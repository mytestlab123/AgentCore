#!/usr/bin/env python3
"""Small stdio MCP server for the governed AgentCore demonstration.

The server deliberately has a narrow surface: one sanitized Security Group
SSH-compliance check, one retained AgentCore Gateway decision check, and one
exact Security Group ingress revoke. It never accepts a caller-selected AWS
resource or generic AWS command.
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
SECURITY_GROUP_ID_PATTERN = re.compile(r"^sg-[0-9a-f]{8}(?:[0-9a-f]{9})?$")


class GovernanceBlocked(RuntimeError):
    """A required independent control was unavailable or rejected the action."""

TOOLS = [
    {
        "name": "check_security_finding",
        "description": (
            "Read-only unrestricted-SSH compliance check for the fixed dedicated "
            "demo Security Group. Returns only sanitized rule, source, compliance, "
            "and recommendation data for web-01."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"host": {"type": "string", "enum": ["web-01"]}},
            "required": ["host"],
        },
    },
    {
        "name": "apply_demo_remediation",
        "description": (
            "For environment=dev, native approval and the retained AgentCore Gateway "
            "must allow this tool before it can revoke only TCP/22 from 0.0.0.0/0 "
            "on the fixed dedicated demo Security Group, then verify compliance. Call this tool "
            "directly with host and environment; ticket is optional. Do not "
            "ask the user to confirm; native LibreChat approval handles the "
            "decision. For environment=prod, ticket must start with DEMO-."
            " After approval, the result begins `ASK / APPROVE`; a native "
            "Reject means this server is not called and no AWS change is made."
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
                    "description": "Use dev for the fixed demo Security Group remediation proof.",
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
        return empty_state()
    state = json.loads(path.read_text(encoding="utf-8"))
    # Older retained demo-state files predate the compact audit.  Preserve the
    # counters rather than forcing an operator to reset a demonstration.
    if not isinstance(state, dict):
        return empty_state()
    for key, value in empty_state().items():
        state.setdefault(key, value)
    if not isinstance(state["audit_events"], list):
        state["audit_events"] = []
    return state


def empty_state() -> dict[str, Any]:
    return {
        "finding_calls": 0,
        "remediation_calls": 0,
        "delete_calls": 0,
        "remediated": False,
        "aws_remediation_attempts": 0,
        "aws_remediation_verified": False,
        "audit_events": [],
    }


def save_state(state: dict[str, Any]) -> None:
    path = state_path()
    path.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)


def record_audit(
    state: dict[str, Any],
    *,
    request: str,
    tool: str,
    human_decision: str,
    gateway_decision: str,
    backend: str,
    final_result: str,
) -> None:
    """Keep a small, safe local summary rather than a second observability system."""
    event = {
        "request": request,
        "tool": tool,
        "human_decision": human_decision,
        "gateway_decision": gateway_decision,
        "backend": backend,
        "final_result": final_result,
    }
    state["audit_events"] = [*state["audit_events"], event][-8:]


def audit_markdown(
    *,
    request: str,
    tool: str,
    human_decision: str,
    gateway_decision: str,
    backend: str,
    final_result: str,
) -> str:
    """Return the six-part audit story that is safe to show in LibreChat."""
    return (
        "### Compact audit\n\n"
        f"1. Request: {request}\n"
        f"2. Tool: `{tool}`\n"
        f"3. Human decision: {human_decision}\n"
        f"4. Gateway decision: {gateway_decision}\n"
        f"5. Backend: {backend}\n"
        f"6. Final result: {final_result}"
    )


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


def security_group_id() -> str:
    value = os.environ.get("GOVERNANCE_SECURITY_GROUP_ID", "")
    if not SECURITY_GROUP_ID_PATTERN.fullmatch(value):
        raise GovernanceBlocked("required demo Security Group setting is absent or invalid")
    return value


def unrestricted_ssh_sources(permissions: Any) -> list[str]:
    """Return only the fixed public CIDRs that make TCP/22 non-compliant."""
    if not isinstance(permissions, list):
        raise GovernanceBlocked("Security Group ingress rules are invalid")
    sources: list[str] = []
    for permission in permissions:
        if not isinstance(permission, dict) or permission.get("IpProtocol") != "tcp":
            continue
        from_port = permission.get("FromPort")
        to_port = permission.get("ToPort")
        if not isinstance(from_port, int) or not isinstance(to_port, int) or not from_port <= 22 <= to_port:
            continue
        for range_value in permission.get("IpRanges", []):
            if isinstance(range_value, dict) and range_value.get("CidrIp") == "0.0.0.0/0":
                sources.append("0.0.0.0/0")
        for range_value in permission.get("Ipv6Ranges", []):
            if isinstance(range_value, dict) and range_value.get("CidrIpv6") == "::/0":
                sources.append("::/0")
    return list(dict.fromkeys(sources))


def read_security_group_ssh(*, runner: Any = subprocess.run) -> dict[str, str]:
    """Read one fixed Security Group and return a deliberately tiny safe result."""
    require_setting("GOVERNANCE_AWS_READ_ENABLED")
    try:
        completed = runner(
            [
                "aws", "ec2", "describe-security-groups", "--group-ids", security_group_id(),
                "--region", aws_region(), "--output", "json", "--no-cli-pager",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GovernanceBlocked("read-only Security Group query could not run") from exc
    if completed.returncode != 0:
        raise GovernanceBlocked("read-only Security Group query failed")
    try:
        payload = json.loads(completed.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise GovernanceBlocked("read-only Security Group query returned invalid JSON") from exc
    groups = payload.get("SecurityGroups") if isinstance(payload, dict) else None
    if not isinstance(groups, list) or len(groups) != 1 or not isinstance(groups[0], dict):
        raise GovernanceBlocked("read-only Security Group query returned an unexpected result")
    sources = unrestricted_ssh_sources(groups[0].get("IpPermissions"))
    if sources:
        return {
            "api": "ec2:DescribeSecurityGroups",
            "rule": "TCP/22",
            "source": ", ".join(sources),
            "compliance": "NON_COMPLIANT",
            "recommendation": "Remove the unrestricted TCP/22 ingress rule from the dedicated demo Security Group.",
            "mutation": "none",
        }
    return {
        "api": "ec2:DescribeSecurityGroups",
        "rule": "TCP/22",
        "source": "none",
        "compliance": "COMPLIANT",
        "recommendation": "No unrestricted TCP/22 ingress rule is present on the dedicated demo Security Group.",
        "mutation": "none",
    }


def revoke_unrestricted_ssh_ingress(*, runner: Any = subprocess.run) -> None:
    """Revoke only the fixed IPv4 SSH rule from the fixed configured Group."""
    require_setting("GOVERNANCE_AWS_REMEDIATION_ENABLED")
    exact_permission = json.dumps([{
        "IpProtocol": "tcp",
        "FromPort": 22,
        "ToPort": 22,
        "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
    }], separators=(",", ":"))
    try:
        completed = runner(
            [
                "aws", "ec2", "revoke-security-group-ingress", "--group-id", security_group_id(),
                "--ip-permissions", exact_permission, "--region", aws_region(),
                "--output", "json", "--no-cli-pager",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GovernanceBlocked("exact Security Group ingress revoke could not run") from exc
    if completed.returncode != 0:
        raise GovernanceBlocked("exact Security Group ingress revoke was not confirmed")


def has_unrestricted_ipv4_ssh(result: dict[str, str]) -> bool:
    return result.get("compliance") == "NON_COMPLIANT" and "0.0.0.0/0" in {
        source.strip() for source in result.get("source", "").split(",")
    }


def verify_gateway(environment: str, *, runner: Any = subprocess.run) -> str:
    """Ask the retained Gateway directly with the LibreChat host's instance role."""
    try:
        return invoke_gateway_runtime(environment, private_dir=state_path().parent, runner=runner)
    except GatewayRuntimeBlocked as exc:
        raise GovernanceBlocked("retained Gateway policy verification failed") from exc


def blocked_result(title: str, *, aws_mutation: str = "none") -> dict[str, Any]:
    return text_result(
        f"## BLOCKED - {title}\n\n"
        "- No local demo effect was recorded\n"
        f"- AWS or infrastructure mutation: **{aws_mutation}**\n"
        "- Check the private runtime prerequisites; details are intentionally not exposed.",
        error=True,
    )


def call_tool(
    name: str,
    args: dict[str, Any],
    *,
    security_group_read: Any | None = None,
    security_group_revoke: Any | None = None,
    gateway_check: Any | None = None,
) -> dict[str, Any]:
    state = load_state()
    host = args.get("host")
    if host != "web-01":
        return text_result("Only synthetic host web-01 is supported.", error=True)

    if name == "check_security_finding":
        try:
            security_result = (security_group_read or read_security_group_ssh)()
        except GovernanceBlocked:
            return blocked_result("read-only Security Group compliance check unavailable")
        state["finding_calls"] += 1
        record_audit(
            state,
            request="read-only unrestricted-SSH compliance check for `web-01`",
            tool=name,
            human_decision="**not required** (read-only)",
            gateway_decision="**not required** (no controlled action)",
            backend="sanitized `ec2:DescribeSecurityGroups`; mutation **none**",
            final_result=f"**ALLOW** — {security_result['compliance']} result returned",
        )
        save_state(state)
        return text_result(
            "## ALLOW - Real SSH compliance result returned\n\n"
            "- Host: `web-01`\n"
            f"- Rule: `{security_result['rule']}`\n"
            f"- Source: `{security_result['source']}`\n"
            f"- Compliance: **{security_result['compliance']}**\n"
            f"- Recommended action: {security_result['recommendation']}\n"
            f"- AWS API: `{security_result['api']}`\n"
            "- MCP tool calls: **1**\n"
            "- AWS or infrastructure mutation: **none**\n\n"
            + audit_markdown(
                request="read-only unrestricted-SSH compliance check for `web-01`",
                tool=name,
                human_decision="**not required** (read-only)",
                gateway_decision="**not required** (no controlled action)",
                backend="sanitized `ec2:DescribeSecurityGroups`; mutation **none**",
                final_result=f"**ALLOW** — {security_result['compliance']} result returned",
            )
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
            record_audit(
                state,
                request=f"controlled remediation for `{host}` in `{environment}`",
                tool=name,
                human_decision="tool reached the server; native Reject would stop before this point",
                gateway_decision="**DENY**",
                backend="AWS action **not called**",
                final_result="**DENY** — Gateway blocked remediation",
            )
            save_state(state)
            return text_result(
                "## DENY - Gateway Policy blocked remediation\n\n"
                f"- Host: `{host}`\n"
                f"- Environment: `{environment}`\n"
                "- Gateway decision: **DENY**\n"
                "- Exact AWS revoke called: **no**\n"
                "- AWS or infrastructure mutation: **none**\n\n"
                + audit_markdown(
                    request=f"controlled remediation for `{host}` in `{environment}`",
                    tool=name,
                    human_decision="tool reached the server; native Reject would stop before this point",
                    gateway_decision="**DENY**",
                    backend="AWS action **not called**",
                    final_result="**DENY** — Gateway blocked remediation",
                ),
                error=True,
            )
        reader = security_group_read or read_security_group_ssh
        revoker = security_group_revoke or revoke_unrestricted_ssh_ingress
        try:
            before = reader()
        except GovernanceBlocked:
            return blocked_result("provider pre-check unavailable")
        if not has_unrestricted_ipv4_ssh(before):
            return blocked_result("exact unrestricted TCP/22 rule is not present")

        # Persist the attempted controlled action before the AWS call, so a
        # later provider-verification failure can never be misreported as no call.
        state["remediation_calls"] += 1
        state["aws_remediation_attempts"] += 1
        save_state(state)
        try:
            revoker()
        except GovernanceBlocked:
            record_audit(
                state,
                request=f"exact TCP/22 revoke for `{host}` in `{environment}`",
                tool=name,
                human_decision="tool reached the server; native Reject would stop before this point",
                gateway_decision="**ALLOW**",
                backend="exact AWS revoke attempted; provider verification unavailable",
                final_result="**BLOCKED** — AWS action status could not be verified",
            )
            save_state(state)
            return blocked_result(
                "exact AWS revoke could not be verified",
                aws_mutation="exact revoke attempted; provider verification unavailable",
            )
        try:
            after = reader()
        except GovernanceBlocked:
            record_audit(
                state,
                request=f"exact TCP/22 revoke for `{host}` in `{environment}`",
                tool=name,
                human_decision="tool reached the server; native Reject would stop before this point",
                gateway_decision="**ALLOW**",
                backend="exact AWS revoke completed; provider re-read unavailable",
                final_result="**BLOCKED** — provider verification unavailable",
            )
            save_state(state)
            return blocked_result(
                "provider verification unavailable after exact AWS revoke",
                aws_mutation="exact TCP/22 revoke completed; final provider state unavailable",
            )
        if after.get("compliance") != "COMPLIANT":
            record_audit(
                state,
                request=f"exact TCP/22 revoke for `{host}` in `{environment}`",
                tool=name,
                human_decision="tool reached the server; native Reject would stop before this point",
                gateway_decision="**ALLOW**",
                backend="exact AWS revoke completed; provider still reports NON_COMPLIANT",
                final_result="**BLOCKED** — final provider verification is not compliant",
            )
            save_state(state)
            return blocked_result(
                "provider verification is not compliant after exact AWS revoke",
                aws_mutation="exact TCP/22 revoke completed; provider still reports NON_COMPLIANT",
            )

        state["remediated"] = True
        state["aws_remediation_verified"] = True
        record_audit(
            state,
            request=f"exact TCP/22 revoke for `{host}` in `{environment}`",
            tool=name,
            human_decision="tool reached the server; native Reject would stop before this point",
            gateway_decision="**ALLOW**",
            backend="revoked exact TCP/22 from 0.0.0.0/0; provider re-read COMPLIANT",
            final_result="**ASK / APPROVE / ALLOW** — AWS remediation verified COMPLIANT",
        )
        save_state(state)
        return text_result(
            "## ASK / APPROVE / ALLOW - AWS remediation verified\n\n"
            f"- Host: `{host}`\n"
            f"- Environment: `{environment}`\n"
            "- Exact AWS action: **revoked TCP/22 from `0.0.0.0/0` on the fixed dedicated demo Security Group**\n"
            "- Gateway decision: **ALLOW**\n"
            "- MCP tool calls: **1** (after approval)\n"
            "- Provider verification: **COMPLIANT** (unrestricted TCP/22 absent)\n"
            "- AWS or infrastructure mutation: **one exact dedicated Security Group ingress revoke**\n"
            "- ENI, instance, route, public IP, and workload changes: **none**\n"
            "- Secrets accessed: **none**\n\n"
            + audit_markdown(
                request=f"exact TCP/22 revoke for `{host}` in `{environment}`",
                tool=name,
                human_decision="tool reached the server; native Reject would stop before this point",
                gateway_decision="**ALLOW**",
                backend="revoked exact TCP/22 from 0.0.0.0/0; provider re-read COMPLIANT",
                final_result="**ASK / APPROVE / ALLOW** — AWS remediation verified COMPLIANT",
            )
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
