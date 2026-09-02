"""Minimal OpenAI-compatible adapter for the Issue #19 LibreChat proof.

The adapter translates chat-completions requests into the official AgentCore
CLI Harness, Codex CLI, or protected GovTechAI Responses invocation. Its
GovTechAI path preserves function-call protocol data but never executes tools
or makes policy decisions; LibreChat remains the MCP and approval owner.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


HARNESS_ARN = os.environ.get("AGENTCORE_HARNESS_ARN", "")
REGION = os.environ.get("AWS_REGION", "ap-southeast-1")
AGENTCORE_CLI = os.environ.get(
    "AGENTCORE_CLI",
    "/home/user/.local/share/agentcore-cli/node_modules/.bin/agentcore",
)
CODEX_CLI = os.environ.get("CODEX_CLI", "/opt/agentcore-codex/node_modules/.bin/codex")
CODEX_HOME = os.environ.get("CODEX_HOME", "/root/.codex")
CODEX_WORKDIR = os.environ.get("CODEX_WORKDIR", "/opt/agentcore-codex")
CODEX_FAMILY_MODELS = ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol")
CODEX_REASONING_EFFORTS = ("low", "medium", "high")
CODEX_DEFAULT_MODEL = os.environ.get("CODEX_MODEL", "gpt-5.6-luna")
if CODEX_DEFAULT_MODEL not in CODEX_FAMILY_MODELS:
    CODEX_DEFAULT_MODEL = "gpt-5.6-luna"
CODEX_DEFAULT_EFFORT = os.environ.get("CODEX_REASONING_EFFORT", "low")
if CODEX_DEFAULT_EFFORT not in CODEX_REASONING_EFFORTS:
    CODEX_DEFAULT_EFFORT = "low"
CODEX_MODEL_OPTIONS = tuple(
    f"{model}-{effort}"
    for model in CODEX_FAMILY_MODELS
    for effort in CODEX_REASONING_EFFORTS
)
MODEL_ID = "global.amazon.nova-2-lite-v1:0"
HARNESS_MAX_TOKENS = os.environ.get("AGENTCORE_MAX_TOKENS", "6000")
PLATFORM_BASE_URL = os.environ.get("PLATFORM_API_BASE_URL", "https://api-public.ai.tech.gov.sg")
PLATFORM_CONFIG = os.environ.get("PLATFORM_CONFIG", "/etc/agentcore-issue19/platformai.env")
PLATFORM_MODELS = {
    "gpt-5.6-luna",
    "azure.claude-haiku-4-5",
    "gemini-3.5-flash",
}


def _response(
    request_id: str,
    text: str | None,
    model: str = "agentcore-nova-2-lite",
    tool_calls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    message: dict[str, Any] = {"role": "assistant", "content": text}
    finish_reason = "stop"
    if tool_calls:
        message["tool_calls"] = tool_calls
        finish_reason = "tool_calls"
    return {
        "id": request_id,
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": finish_reason,
            }
        ],
    }


def _stream_events(request_id: str, text: str, model: str = "agentcore-nova-2-lite") -> list[dict[str, Any]]:
    """Return the two minimal chunks LibreChat expects for stream=true."""
    return [
        {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": 0,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": text},
                    "finish_reason": None,
                }
            ],
        },
        {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": 0,
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        },
    ]


def _stream_tool_events(
    request_id: str, tool_calls: list[dict[str, Any]], model: str
) -> list[dict[str, Any]]:
    """Return OpenAI SSE chunks for a provider function call."""
    return [
        {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": 0,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "tool_calls": tool_calls},
                    "finish_reason": None,
                }
            ],
        },
        {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": 0,
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}],
        },
    ]


def _error(message: str) -> dict[str, Any]:
    return {"error": {"message": message, "type": "agentcore_adapter_error"}}


class ProviderAuthError(RuntimeError):
    """Raised when no protected GovTech provider key is available."""


def _platform_config() -> dict[str, str]:
    try:
        mode = os.stat(PLATFORM_CONFIG).st_mode & 0o777
        if mode != 0o600:
            raise ProviderAuthError("GovTechAI protected config must be mode 600")
        values: dict[str, str] = {}
        with open(PLATFORM_CONFIG, encoding="utf-8") as handle:
            for line in handle:
                if "=" not in line or line.lstrip().startswith("#"):
                    continue
                name, value = line.rstrip("\n").split("=", 1)
                if name in {"PLATFORM_API_KEY", "PLATFORM_API_BASE_URL", "PLATFORM_AI_MODEL"}:
                    values[name] = value.strip().strip('"').strip("'")
        return values
    except FileNotFoundError:
        return {}


def _platform_credentials(authorization: str | None) -> tuple[str, str]:
    if authorization and authorization.lower().startswith("bearer "):
        key = authorization[7:].strip()
        if key and key != "local-poc-placeholder":
            return key, PLATFORM_BASE_URL
    config = _platform_config()
    key = config.get("PLATFORM_API_KEY", "")
    if not key:
        raise ProviderAuthError("GovTechAI protected config is not available")
    return key, config.get("PLATFORM_API_BASE_URL", PLATFORM_BASE_URL)


def _codex_model_selection(selection: str) -> tuple[str, str, str]:
    if selection in CODEX_MODEL_OPTIONS:
        base_model, effort = selection.rsplit("-", 1)
        return base_model, effort, selection
    if selection in CODEX_FAMILY_MODELS:
        canonical = f"{selection}-{CODEX_DEFAULT_EFFORT}"
        return selection, CODEX_DEFAULT_EFFORT, canonical
    raise RuntimeError("Codex subscription model is not available")


def invoke_codex(prompt: str, model: str = CODEX_DEFAULT_MODEL) -> str:
    base_model, effort, _ = _codex_model_selection(model)
    if not os.path.isfile(CODEX_CLI) or not os.access(CODEX_CLI, os.X_OK):
        raise RuntimeError("Codex CLI is not installed")
    if not os.path.isfile(os.path.join(CODEX_HOME, "auth.json")):
        raise ProviderAuthError("Codex subscription is not authenticated")
    environment = os.environ.copy()
    environment.update({"HOME": "/root", "CODEX_HOME": CODEX_HOME})
    completed = subprocess.run(
        [
            CODEX_CLI,
            "exec",
            "--json",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "-C",
            CODEX_WORKDIR,
            "-m",
            base_model,
            "-c",
            f'model_reasoning_effort="{effort}"',
            prompt,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
        env=environment,
    )
    if completed.returncode != 0:
        raise RuntimeError("Codex subscription invocation failed")
    messages: list[str] = []
    for line in completed.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item")
        if event.get("type") == "item.completed" and isinstance(item, dict):
            text = item.get("text")
            if item.get("type") == "agent_message" and isinstance(text, str) and text.strip():
                messages.append(text)
    if messages:
        return messages[-1]
    raise RuntimeError("Codex subscription returned no text")


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        )
    return ""


def _responses_input(messages: list[Any]) -> list[dict[str, Any]]:
    """Translate Chat Completions messages into Responses input items."""
    translated: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        if role in {"system", "user"}:
            content = _message_text(message.get("content"))
            if content:
                translated.append({"role": role, "content": content})
            continue
        if role == "assistant":
            content = _message_text(message.get("content"))
            if content:
                translated.append({"role": "assistant", "content": content})
            for call in message.get("tool_calls", []):
                if not isinstance(call, dict):
                    continue
                function = call.get("function", {})
                if not isinstance(function, dict):
                    function = {}
                name = function.get("name") or call.get("name")
                arguments = function.get("arguments", call.get("arguments", "{}"))
                call_id = call.get("id") or call.get("call_id")
                if isinstance(name, str) and isinstance(call_id, str):
                    if not isinstance(arguments, str):
                        arguments = json.dumps(arguments, separators=(",", ":"))
                    translated.append(
                        {
                            "type": "function_call",
                            "call_id": call_id,
                            "name": name,
                            "arguments": arguments,
                        }
                    )
            continue
        if role == "tool":
            call_id = message.get("tool_call_id") or message.get("call_id")
            output = _message_text(message.get("content"))
            if isinstance(call_id, str):
                translated.append(
                    {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": output,
                    }
                )
    if not translated:
        raise ValueError("messages must contain supported text")
    return translated


def _responses_tools(tools: Any) -> list[dict[str, Any]]:
    translated: list[dict[str, Any]] = []
    if not isinstance(tools, list):
        return translated
    for tool in tools:
        if not isinstance(tool, dict) or tool.get("type") != "function":
            continue
        function = tool.get("function", {})
        if not isinstance(function, dict) or not isinstance(function.get("name"), str):
            continue
        item: dict[str, Any] = {
            "type": "function",
            "name": function["name"],
        }
        for key in ("description", "parameters", "strict"):
            if key in function:
                item[key] = function[key]
        translated.append(item)
    return translated


def _platform_request_payload(payload: dict[str, Any], model: str) -> dict[str, Any]:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise ValueError("messages must be a list")
    request_payload: dict[str, Any] = {
        "model": model,
        "input": _responses_input(messages),
        "max_output_tokens": 700,
    }
    tools = _responses_tools(payload.get("tools"))
    if tools:
        request_payload["tools"] = tools
    for key in ("tool_choice", "parallel_tool_calls"):
        if key in payload:
            request_payload[key] = payload[key]
    if model == "gpt-5.6-luna":
        request_payload["reasoning"] = {"effort": "low"}
    return request_payload


def _platform_text(response: dict[str, Any], *, required: bool = True) -> str:
    text = "".join(
        content.get("text", "")
        for item in response.get("output", [])
        for content in item.get("content", [])
        if content.get("type") == "output_text"
    )
    if not text and required:
        raise RuntimeError("GovTechAI returned no response text")
    return text


def _platform_tool_calls(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Translate Responses function_call items; never executes or authorizes them."""
    calls: list[dict[str, Any]] = []
    for item in response.get("output", []):
        if not isinstance(item, dict):
            continue
        if item.get("type") not in {"function_call", "tool_call"}:
            continue
        function = item.get("function", {})
        if not isinstance(function, dict):
            function = {}
        name = item.get("name") or function.get("name")
        arguments = item.get("arguments", function.get("arguments", "{}"))
        call_id = item.get("call_id") or item.get("id")
        if isinstance(name, str) and isinstance(call_id, str):
            if not isinstance(arguments, str):
                arguments = json.dumps(arguments, separators=(",", ":"))
            calls.append(
                {
                    "id": call_id,
                    "type": "function",
                    "function": {"name": name, "arguments": arguments},
                }
            )
    return calls


def invoke_platform_request(
    payload: dict[str, Any], model: str, authorization: str | None
) -> dict[str, Any]:
    if model not in PLATFORM_MODELS:
        raise RuntimeError("GovTechAI model is not in the approved allowlist")
    key, base_url = _platform_credentials(authorization)
    request_payload = _platform_request_payload(payload, model)
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/platform/models/v1/responses",
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "x-api-key": key,
            "content-type": "application/json",
            "accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read())
            if not isinstance(body, dict):
                raise RuntimeError("GovTechAI returned an invalid response")
            return body
    except urllib.error.HTTPError as error:
        if error.code in {401, 403}:
            raise RuntimeError("GovTechAI rejected the key or model") from error
        if error.code == 404:
            raise RuntimeError("GovTechAI model is unavailable") from error
        raise RuntimeError("GovTechAI request failed") from error
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError("GovTechAI request failed") from error


def invoke_platform(prompt: str, model: str, authorization: str | None) -> str:
    """Compatibility helper for the original text-only callers and tests."""
    response = invoke_platform_request(
        {"messages": [{"role": "user", "content": prompt}]}, model, authorization
    )
    return _platform_text(response)


def _user_prompt(payload: dict[str, Any]) -> str:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise ValueError("messages must be a list")
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
            raise ValueError("the latest user message must contain text")
    raise ValueError("a user message is required")


def invoke_harness(prompt: str) -> str:
    if not HARNESS_ARN:
        raise RuntimeError("AGENTCORE_HARNESS_ARN is not configured")
    if not os.path.isfile(AGENTCORE_CLI) or not os.access(AGENTCORE_CLI, os.X_OK):
        raise RuntimeError("AgentCore CLI is not executable")
    completed = subprocess.run(
        [
            AGENTCORE_CLI,
            "invoke",
            "--harness-arn",
            HARNESS_ARN,
            "--region",
            REGION,
            "--session-id",
            str(uuid.uuid4()),
            "--json",
            "--verbose",
            "--max-tokens",
            HARNESS_MAX_TOKENS,
            prompt,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
        env=os.environ.copy(),
    )
    if completed.returncode != 0:
        raise RuntimeError("AgentCore Harness invocation failed")
    chunks: list[str] = []
    for line in completed.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        delta = event.get("delta")
        if event.get("type") == "contentBlockDelta" and isinstance(delta, dict):
            text = delta.get("text")
            if isinstance(text, str):
                chunks.append(text)
    if not chunks:
        raise RuntimeError("AgentCore Harness returned no text")
    return "".join(chunks)


class Handler(BaseHTTPRequestHandler):
    server_version = "AgentCoreIssue19Adapter/1.0"

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_stream(
        self,
        request_id: str,
        text: str | None,
        model: str,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> None:
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("cache-control", "no-cache")
        self.send_header("connection", "close")
        self.end_headers()
        events = (
            _stream_tool_events(request_id, tool_calls, model)
            if tool_calls
            else _stream_events(request_id, text or "", model)
        )
        for event in events:
            body = f"data: {json.dumps(event)}\n\n".encode("utf-8")
            self.wfile.write(body)
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()
        self.close_connection = True

    def _models(self, models: list[dict[str, str]]) -> None:
        self._send(200, {"object": "list", "data": models})

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            self._models(
                [
                    {
                        "id": "agentcore-nova-2-lite",
                        "object": "model",
                        "owned_by": "agentcore",
                    }
                ]
            )
            return
        if self.path == "/govtech/v1/models":
            self._models(
                [
                    {"id": model, "object": "model", "owned_by": "govtechai"}
                    for model in sorted(PLATFORM_MODELS)
                ]
            )
            return
        if self.path == "/codex/v1/models":
            self._models(
                [
                    {"id": model, "object": "model", "owned_by": "openai-chatgpt"}
                    for model in CODEX_MODEL_OPTIONS
                ]
            )
            return
        self._send(404, _error("route not found"))

    def do_POST(self) -> None:  # noqa: N802
        is_platform = self.path == "/govtech/v1/chat/completions"
        is_codex = self.path == "/codex/v1/chat/completions"
        if self.path not in {"/v1/chat/completions", "/govtech/v1/chat/completions", "/codex/v1/chat/completions"}:
            self._send(404, _error("route not found"))
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length))
            if is_platform:
                response = invoke_platform_request(
                    payload,
                    str(payload.get("model", "")),
                    self.headers.get("authorization"),
                )
                text = _platform_text(response, required=False)
                tool_calls = _platform_tool_calls(response)
                if not text and not tool_calls:
                    raise RuntimeError("GovTechAI returned no text or tool call")
            elif is_codex:
                requested_model = str(payload.get("model", CODEX_DEFAULT_MODEL))
                _, _, codex_response_model = _codex_model_selection(requested_model)
                text = invoke_codex(_user_prompt(payload), requested_model)
                tool_calls = []
            else:
                text = invoke_harness(_user_prompt(payload))
                tool_calls = []
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(400, _error(str(exc)))
            return
        except ProviderAuthError as exc:
            self._send(401, _error(str(exc)))
            return
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            self._send(502, _error(str(exc)))
            return
        request_id = f"chatcmpl-{uuid.uuid4().hex}"
        response_model = (
            codex_response_model
            if is_codex
            else (str(payload.get("model", "")) if is_platform else "agentcore-nova-2-lite")
        )
        if payload.get("stream") is True:
            self._send_stream(request_id, text, response_model, tool_calls)
            return
        self._send(200, _response(request_id, text, response_model, tool_calls))

    def log_message(self, *_args: Any) -> None:
        return


def main() -> None:
    port = int(os.environ.get("PORT", "3081"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"AgentCore adapter listening on 127.0.0.1:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
