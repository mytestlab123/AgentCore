"""Minimal OpenAI-compatible adapter for the Issue #19 LibreChat proof.

The adapter only translates chat-completions requests into the official
AgentCore CLI Harness invocation. It never calls Bedrock Runtime directly and
does not implement model, tool, or provider selection.
"""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


HARNESS_ARN = os.environ.get("AGENTCORE_HARNESS_ARN", "")
REGION = os.environ.get("AWS_REGION", "ap-southeast-1")
AGENTCORE_CLI = os.environ.get(
    "AGENTCORE_CLI",
    "/home/user/.local/share/agentcore-cli/node_modules/.bin/agentcore",
)
MODEL_ID = "global.amazon.nova-2-lite-v1:0"


def _response(request_id: str, text: str) -> dict[str, Any]:
    return {
        "id": request_id,
        "object": "chat.completion",
        "created": 0,
        "model": "agentcore-nova-2-lite",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
    }


def _error(message: str) -> dict[str, Any]:
    return {"error": {"message": message, "type": "agentcore_adapter_error"}}


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

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            self._send(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": "agentcore-nova-2-lite",
                            "object": "model",
                            "owned_by": "agentcore",
                        }
                    ],
                },
            )
            return
        self._send(404, _error("route not found"))

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self._send(404, _error("route not found"))
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length))
            text = invoke_harness(_user_prompt(payload))
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(400, _error(str(exc)))
            return
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            self._send(502, _error(str(exc)))
            return
        self._send(200, _response(f"chatcmpl-{uuid.uuid4().hex}", text))

    def log_message(self, *_args: Any) -> None:
        return


def main() -> None:
    port = int(os.environ.get("PORT", "3081"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"AgentCore adapter listening on 127.0.0.1:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
