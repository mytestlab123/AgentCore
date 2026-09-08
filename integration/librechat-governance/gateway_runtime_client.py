"""Narrow runtime client for the retained AgentCore Gateway policy decision.

Unlike the retained-resource proof script, this module is shipped beside the
MCP server and uses the LibreChat host's instance role. It performs one fixed
MCP tools/call request and has no create, update, delete, or generic-command
path.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REGION = "ap-southeast-1"
MCP_PROTOCOL_VERSION = "2025-03-26"
FULL_TOOL_NAME = "Issue31Target___check_demo_scope"
URL_SUFFIX = f".gateway.bedrock-agentcore.{REGION}.amazonaws.com"


class GatewayRuntimeBlocked(RuntimeError):
    """The fixed runtime Gateway request cannot be made or was not authorized."""


def require_gateway_url() -> str:
    if os.environ.get("GOVERNANCE_GATEWAY_POLICY_ENABLED") != "required":
        raise GatewayRuntimeBlocked("Gateway policy runtime setting is absent")
    value = os.environ.get("GOVERNANCE_GATEWAY_URL", "")
    parsed = urlparse(value)
    if (parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(URL_SUFFIX)
            or parsed.username or parsed.password or parsed.port not in {None, 443}
            or parsed.query or parsed.fragment):
        raise GatewayRuntimeBlocked("Gateway URL is not the expected managed endpoint")
    return value.rstrip("/") + ("" if value.rstrip("/").endswith("/mcp") else "/mcp")


def private_write(path: Path, value: str) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_text(value, encoding="utf-8")
    path.chmod(0o600)


def parse_decision(environment: str, http_code: int, body: str) -> str:
    try:
        envelope = json.loads(body)
    except (TypeError, json.JSONDecodeError) as exc:
        raise GatewayRuntimeBlocked("Gateway returned malformed JSON") from exc
    if environment == "dev":
        content = envelope.get("result", {}).get("content", [])
        if (http_code == 200 and envelope.get("jsonrpc") == "2.0"
                and envelope.get("id") == "dev" and not envelope.get("error")
                and len(content) == 1 and isinstance(content[0], dict)):
            try:
                payload = json.loads(content[0].get("text", ""))
                result = json.loads(payload.get("body", ""))
            except (AttributeError, TypeError, json.JSONDecodeError) as exc:
                raise GatewayRuntimeBlocked("Gateway dev result was malformed") from exc
            if result == {"environment": "dev", "status": "healthy", "source": "synthetic-demo"}:
                return "ALLOW"
        raise GatewayRuntimeBlocked("Gateway did not return the required dev ALLOW result")
    error = envelope.get("error")
    if (http_code == 200 and envelope.get("jsonrpc") == "2.0" and envelope.get("id") == "prod"
            and isinstance(error, dict) and error.get("code") == -32002
            and "Tool Execution Denied" in str(error.get("message", ""))):
        return "DENY"
    raise GatewayRuntimeBlocked("Gateway did not return the required prod DENY result")


def verify_gateway(
    environment: str,
    *,
    private_dir: Path,
    runner: Any = subprocess.run,
) -> str:
    if environment not in {"dev", "prod"}:
        raise GatewayRuntimeBlocked("unexpected Gateway environment")
    endpoint = require_gateway_url()
    exported = runner(
        ["aws", "--region", REGION, "configure", "export-credentials"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if exported.returncode != 0:
        raise GatewayRuntimeBlocked("host instance-role credentials are unavailable")
    try:
        credentials = json.loads(exported.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise GatewayRuntimeBlocked("host credential response was malformed") from exc
    if any(not isinstance(credentials.get(key), str) or not credentials[key]
           for key in ("AccessKeyId", "SecretAccessKey")):
        raise GatewayRuntimeBlocked("host credential response was incomplete")
    request = Path(private_dir) / f"gateway-runtime-{environment}-request.json"
    response = Path(private_dir) / f"gateway-runtime-{environment}-response.json"
    private_write(request, json.dumps({
        "jsonrpc": "2.0", "id": environment, "method": "tools/call",
        "params": {"name": FULL_TOOL_NAME, "arguments": {"environment": environment}},
    }, separators=(",", ":")))
    private_write(response, "")
    config = [
        f'url = "{endpoint}"', 'request = "POST"',
        f'aws-sigv4 = "aws:amz:{REGION}:bedrock-agentcore"',
        f'user = "{credentials["AccessKeyId"]}:{credentials["SecretAccessKey"]}"',
        'header = "Accept: application/json, text/event-stream"',
        'header = "Content-Type: application/json"',
        f'header = "MCP-Protocol-Version: {MCP_PROTOCOL_VERSION}"',
        f'data-binary = "@{request}"', f'output = "{response}"',
        'write-out = "%{http_code}"', 'silent', 'show-error',
        'connect-timeout = 15', 'max-time = 60',
    ]
    if credentials.get("SessionToken"):
        config.append(f'header = "X-Amz-Security-Token: {credentials["SessionToken"]}"')
    try:
        invoked = runner(
            ["curl", "--config", "-"], input="\n".join(config) + "\n", check=False,
            capture_output=True, text=True, timeout=75,
        )
    finally:
        credentials.clear()
    if invoked.returncode != 0:
        raise GatewayRuntimeBlocked("Gateway request failed")
    try:
        http_code = int(invoked.stdout[-3:])
    except (TypeError, ValueError) as exc:
        raise GatewayRuntimeBlocked("Gateway returned no HTTP status") from exc
    try:
        body = response.read_text(encoding="utf-8")
    except OSError as exc:
        raise GatewayRuntimeBlocked("Gateway response was unavailable") from exc
    return parse_decision(environment, http_code, body)
