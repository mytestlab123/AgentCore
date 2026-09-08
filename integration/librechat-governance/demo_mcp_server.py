#!/usr/bin/env python3
"""Small stdio MCP server for the governed AgentCore demonstration.

The server deliberately has a narrow surface: one sanitized read-only AWS STS
check, one retained AgentCore Gateway decision check, and one local demo-state
marker.  It never creates or mutates AWS resources.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from gateway_runtime_client import GatewayRuntimeBlocked, verify_gateway as invoke_gateway_runtime

REGION_PATTERN = re.compile(r"^[a-z]{2}(?:-gov)?-[a-z]+-\d$")


class GovernanceBlocked(RuntimeError):
    """A required independent control was unavailable or rejected the action."""

TOOLS = [
    {
        "name": "check_security_finding",
        "description": "Read-only finding lookup plus a sanitized AWS STS identity check for web-01.",
        "inputSchema": {
            "type": "object",
            "properties": {"host": {"type": "string", "enum": ["web-01"]}},
            "required": ["host"],
        },
    },
    {
        "name": "apply_demo_remediation",
        "description": (
            "Harmless local demo effect. For environment=dev, native approval and "
            "the retained AgentCore Gateway must allow this tool before it can "
            "record one local marker. Call this tool "
            "directly with host and environment; ticket is optional. Do not "
            "ask the user to confirm; native LibreChat approval handles the "
            "decision. For environment=prod, ticket must start with DEMO-."
            " After approval, the result begins `ASK / APPROVE`; a native "
            "Reject means this server is not called and no effect is recorded."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "enum": ["web-01"],
                    "description": "Synthetic demo host; use web-01.",
                },
                "environment": {
                    "type": "string",
                    "enum": ["dev", "prod"],
                    "description": "Use dev for the harmless default proof.",
                },
                "ticket": {
                    "type": "string",
                    "description": "Optional in dev; required with DEMO-* prefix in prod.",
                },
            },
            "required": ["host", "environment"],
        },
    },
    {
        "name": "delete_demo_asset",
        "description": "Prohibited demo operation; static policy must deny before call.",
        "inputSchema": {
            "type": "object",
            "properties": {"host": {"type": "string", "enum": ["web-01"]}},
            "required": ["host"],
        },
    },
]


def state_path() -> Path:
    configured = os.environ.get("GOVERNANCE_STATE_FILE")
    if configured:
        path = Path(configured).expanduser()
    else:
        path = Path.home() / ".cache" / "agentcore-governance" / "state.json"
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    return path


def load_state() -> dict[str, Any]:
    path = state_path()
    if not path.exists():
        return {"finding_calls": 0, "remediation_calls": 0, "delete_calls": 0, "remediated": False}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    path = state_path()
    path.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)


def text_result(text: str, *, error: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if error:
        result["isError"] = True
    return result


def require_setting(name: str) -> None:
    if os.environ.get(name) != "required":
        raise GovernanceBlocked("required runtime setting is absent")


def aws_region() -> str:
    region = os.environ.get("GOVERNANCE_AWS_REGION", "ap-southeast-1")
    if not REGION_PATTERN.fullmatch(region):
        raise GovernanceBlocked("invalid AWS region setting")
    return region


def read_aws_identity(*, runner: Any = subprocess.run) -> dict[str, str]:
    """Run a fixed read-only identity query and discard all identity values."""
    require_setting("GOVERNANCE_AWS_READ_ENABLED")
    completed = runner(
        ["aws", "sts", "get-caller-identity", "--region", aws_region(), "--output", "json", "--no-cli-pager"],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if completed.returncode != 0:
        raise GovernanceBlocked("read-only AWS identity query failed")
    try:
        identity = json.loads(completed.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise GovernanceBlocked("read-only AWS identity query returned invalid JSON") from exc
    if not all(isinstance(identity.get(key), str) and identity[key] for key in ("Account", "Arn", "UserId")):
        raise GovernanceBlocked("read-only AWS identity query returned an incomplete identity")
    return {"api": "sts:GetCallerIdentity", "result": "identity verified", "mutation": "none"}


def verify_gateway(environment: str, *, runner: Any = subprocess.run) -> str:
    """Ask the retained Gateway directly with the LibreChat host's instance role."""
    try:
        return invoke_gateway_runtime(environment, private_dir=state_path().parent, runner=runner)
    except GatewayRuntimeBlocked as exc:
        raise GovernanceBlocked("retained Gateway policy verification failed") from exc


def blocked_result(title: str) -> dict[str, Any]:
    return text_result(
        f"## BLOCKED - {title}\n\n"
        "- No local demo effect was recorded\n"
        "- No AWS or infrastructure mutation was made\n"
        "- Check the private runtime prerequisites; details are intentionally not exposed.",
        error=True,
    )


def call_tool(
    name: str,
    args: dict[str, Any],
    *,
    aws_read: Any | None = None,
    gateway_check: Any | None = None,
) -> dict[str, Any]:
    state = load_state()
    host = args.get("host")
    if host != "web-01":
        return text_result("Only synthetic host web-01 is supported.", error=True)

    if name == "check_security_finding":
        try:
            aws_result = (aws_read or read_aws_identity)()
        except GovernanceBlocked:
            return blocked_result("read-only AWS identity check unavailable")
        state["finding_calls"] += 1
        save_state(state)
        return text_result(
            "## ALLOW - Security finding and AWS read returned\n\n"
            "- Host: `web-01`\n"
            "- Severity: **HIGH**\n"
            "- Finding: `demo-cve-2026-0001`\n"
            "- Recommended action: patch package `demo-lib`\n"
            f"- AWS API: `{aws_result['api']}` ({aws_result['result']})\n"
            "- MCP tool calls: **1**\n"
            "- AWS or infrastructure mutation: **none**"
        )

    if name == "apply_demo_remediation":
        environment = args.get("environment")
        ticket = str(args.get("ticket") or "").strip()
        if environment == "prod" and not ticket.startswith("DEMO-"):
            return text_result("Backend guard: prod remediation requires a DEMO-* ticket.", error=True)
        if environment not in {"dev", "prod"}:
            return text_result("Environment must be dev or prod.", error=True)
        try:
            decision = (gateway_check or verify_gateway)(environment)
        except GovernanceBlocked:
            return blocked_result("independent Gateway Policy verification unavailable")
        if decision != "ALLOW":
            return text_result(
                "## DENY - Gateway Policy blocked remediation\n\n"
                f"- Host: `{host}`\n"
                f"- Environment: `{environment}`\n"
                "- Gateway decision: **DENY**\n"
                "- Local demo effect recorded: **no**\n"
                "- AWS or infrastructure mutation: **none**",
                error=True,
            )
        state["remediation_calls"] += 1
        state["remediated"] = True
        save_state(state)
        return text_result(
            "## ASK / APPROVE / ALLOW - Remediation completed\n\n"
            f"- Host: `{host}`\n"
            f"- Environment: `{environment}`\n"
            "- Result: **one harmless local demo effect recorded**\n"
            "- Gateway decision: **ALLOW**\n"
            "- MCP tool calls: **1** (after approval)\n"
            "- AWS or infrastructure mutation: **none**\n"
            "- Secrets accessed: **none**"
        )

    if name == "delete_demo_asset":
        return text_result(
            "## DENY - Deletion blocked\n\n"
            "- This operation is prohibited by the native LibreChat policy.\n"
            "- MCP tool calls: **0 expected**\n"
            "- Demo asset deleted: **no**",
            error=True,
        )

    return text_result(f"Unknown tool: {name}", error=True)


def handle(message: dict[str, Any]) -> dict[str, Any] | None:
    if message.get("method") == "notifications/initialized":
        return None
    method = message.get("method")
    request_id = message.get("id")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "agentcore-governance", "version": "0.1.0"},
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params") or {}
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": call_tool(str(params.get("name")), params.get("arguments") or {}),
        }
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Unsupported method: {method}"},
    }


def main() -> int:
    for line in sys.stdin:
        try:
            message = json.loads(line)
            response = handle(message)
            if response is not None:
                sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
                sys.stdout.flush()
        except (json.JSONDecodeError, TypeError) as exc:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
