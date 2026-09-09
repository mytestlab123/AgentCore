#!/usr/bin/env python3
"""Replace the known governance MCP block and its approval explanation.

This deployment helper receives all host-specific paths and the retained
Gateway endpoint at runtime. It does not print those values or write them into
the repository. Before the first change it creates a mode-600 sibling backup;
the replacement is atomic and refuses an MCP entry with unknown top-level
settings rather than risk deleting deployment-owned configuration. If the
governed approval block is present, it replaces only its `reason` line.
"""

from __future__ import annotations

import argparse
import os
import re
import stat
import tempfile
from pathlib import Path
from urllib.parse import urlparse


REGION = "ap-southeast-1"
URL_SUFFIX = f".gateway.bedrock-agentcore.{REGION}.amazonaws.com"
SECURITY_GROUP_ID_PATTERN = re.compile(r"^sg-[0-9a-f]{8}(?:[0-9a-f]{9})?$")
ALLOWED_TOP_LEVEL = {"command", "args", "env", "chatMenu"}
APPROVAL_REASON = (
    "ASK - Review {tool}. The parameters below target one fixed unattached demo Security Group: "
    "blank ticket is valid in dev. Reject = no MCP call and no AWS change. Approve checks the "
    "retained AgentCore Gateway first; only Gateway ALLOW revokes exact TCP/22 from 0.0.0.0/0 "
    "and verifies COMPLIANT. No generic AWS mutation or secret access."
)


class ConfigureBlocked(RuntimeError):
    """The config does not match the intentionally narrow deployment shape."""


def require_absolute_file(value: str, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or not path.name:
        raise ConfigureBlocked(f"{label} must be an absolute path")
    return path


def require_gateway_url(value: str) -> str:
    parsed = urlparse(value)
    if (parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(URL_SUFFIX)
            or parsed.username or parsed.password or parsed.port not in {None, 443}
            or parsed.query or parsed.fragment):
        raise ConfigureBlocked("Gateway URL is not the expected managed endpoint")
    return value.rstrip("/")


def require_security_group_id(value: str) -> str:
    if not SECURITY_GROUP_ID_PATTERN.fullmatch(value):
        raise ConfigureBlocked("demo Security Group ID is invalid")
    return value


def indent_width(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def find_governance_block(lines: list[str]) -> tuple[int, int, int]:
    mcp_start = next((index for index, line in enumerate(lines)
                      if line.strip() == "mcpServers:" and indent_width(line) == 0), None)
    if mcp_start is None:
        raise ConfigureBlocked("top-level mcpServers section is absent")
    server_start = None
    server_indent = 0
    for index in range(mcp_start + 1, len(lines)):
        line = lines[index]
        if line and indent_width(line) == 0:
            break
        if line.strip() == "agentcore_governance:":
            server_start = index
            server_indent = indent_width(line)
            break
    if server_start is None:
        raise ConfigureBlocked("agentcore_governance MCP entry is absent")
    server_end = next((index for index in range(server_start + 1, len(lines))
                       if lines[index] and indent_width(lines[index]) <= server_indent), len(lines))
    return server_start, server_end, server_indent


def known_top_level_fields(lines: list[str], start: int, end: int, server_indent: int) -> set[str]:
    fields: set[str] = set()
    field_pattern = re.compile(r"^" + re.escape(" " * (server_indent + 2)) + r"([A-Za-z][A-Za-z0-9_-]*):")
    for line in lines[start + 1:end]:
        match = field_pattern.match(line)
        if match:
            fields.add(match.group(1))
    unknown = fields - ALLOWED_TOP_LEVEL
    if unknown:
        raise ConfigureBlocked("agentcore_governance contains unknown top-level fields")
    return fields


def replace_governance_approval_reason(lines: list[str]) -> list[str]:
    """Replace the sole supported toolApproval reason, preserving its location."""
    tool_approval_indexes = [
        index for index, line in enumerate(lines)
        if indent_width(line) == 4 and line.strip() == "toolApproval:"
    ]
    if not tool_approval_indexes:
        return lines
    if len(tool_approval_indexes) != 1:
        raise ConfigureBlocked("governed toolApproval block is ambiguous")
    tool_approval_start = tool_approval_indexes[0]
    tool_approval_end = next(
        (index for index in range(tool_approval_start + 1, len(lines))
         if lines[index] and indent_width(lines[index]) <= 4),
        len(lines),
    )
    reason_indexes = [
        index for index in range(tool_approval_start + 1, tool_approval_end)
        if indent_width(lines[index]) == 6 and lines[index].lstrip().startswith("reason:")
    ]
    if len(reason_indexes) != 1:
        raise ConfigureBlocked("governed toolApproval reason is missing or ambiguous")
    reason_index = reason_indexes[0]
    return lines[:reason_index] + [f'      reason: "{APPROVAL_REASON}"\n'] + lines[reason_index + 1:]


def render_block(
    *, indent: int, server_dir: Path, state_file: Path, gateway_url: str, security_group_id: str,
) -> list[str]:
    base = " " * indent
    nested = " " * (indent + 2)
    value = " " * (indent + 4)
    return [
        f"{base}agentcore_governance:\n",
        f"{nested}command: /usr/bin/python3\n",
        f"{nested}args:\n",
        f"{value}- {server_dir / 'demo_mcp_server.py'}\n",
        f"{nested}env:\n",
        f"{value}GOVERNANCE_STATE_FILE: {state_file}\n",
        f"{value}GOVERNANCE_AWS_READ_ENABLED: required\n",
        f"{value}GOVERNANCE_AWS_REMEDIATION_ENABLED: required\n",
        f"{value}GOVERNANCE_AWS_REGION: {REGION}\n",
        f"{value}GOVERNANCE_SECURITY_GROUP_ID: {security_group_id}\n",
        f"{value}GOVERNANCE_GATEWAY_POLICY_ENABLED: required\n",
        f"{value}GOVERNANCE_GATEWAY_URL: {gateway_url}\n",
        f"{nested}chatMenu: false\n",
    ]


def backup_once(config: Path, original: str) -> Path:
    backup = config.with_name(config.name + ".issue40-before-gateway.bak")
    if backup.exists():
        return backup
    descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(original)
    backup.chmod(0o600)
    return backup


def atomic_write(config: Path, value: str) -> None:
    mode = stat.S_IMODE(config.stat().st_mode)
    descriptor, temporary = tempfile.mkstemp(prefix=config.name + ".issue40-", dir=config.parent, text=True)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
        os.chmod(temporary, mode)
        os.replace(temporary, config)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def configure(*, config: Path, server_dir: Path, state_file: Path, gateway_url: str, security_group_id: str) -> None:
    original = config.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    start, end, indent = find_governance_block(lines)
    known_top_level_fields(lines, start, end, indent)
    replacement = render_block(
        indent=indent, server_dir=server_dir, state_file=state_file, gateway_url=gateway_url,
        security_group_id=security_group_id,
    )
    updated_lines = lines[:start] + replacement + lines[end:]
    updated = "".join(replace_governance_approval_reason(updated_lines))
    if updated == original:
        return
    backup_once(config, original)
    atomic_write(config, updated)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve", action="store_true", help="perform the reviewed single-block update")
    parser.add_argument("--config", required=True)
    parser.add_argument("--server-dir", required=True)
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--gateway-url", required=True)
    parser.add_argument("--security-group-id", required=True)
    args = parser.parse_args(argv)
    if not args.approve:
        print("PLAN=replace only the known agentcore_governance MCP YAML block")
        print("CONFIG_WRITES=0")
        return 0
    try:
        config = require_absolute_file(args.config, "config")
        server_dir = require_absolute_file(args.server_dir, "server directory")
        state_file = require_absolute_file(args.state_file, "state file")
        gateway_url = require_gateway_url(args.gateway_url)
        security_group_id = require_security_group_id(args.security_group_id)
        if not config.is_file() or not (server_dir / "demo_mcp_server.py").is_file():
            raise ConfigureBlocked("required deployment files are absent")
        configure(
            config=config, server_dir=server_dir, state_file=state_file, gateway_url=gateway_url,
            security_group_id=security_group_id,
        )
    except (ConfigureBlocked, OSError) as error:
        print(f"BLOCKED={error}")
        return 2
    print("LIBRECHAT_MCP_CONFIG=UPDATED")
    print("PRIVATE_BACKUP=retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
