#!/usr/bin/env python3
"""Offline tests for the narrow Issue #40 LibreChat MCP configurator."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import issue40_configure_librechat as configure


GATEWAY_URL = "https://example.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com"
SECURITY_GROUP_ID = "sg-0123456789abcdef0"
SOURCE = """version: 1.2.1\nmcpServers:\n  agentcore_governance:\n    command: /usr/bin/python3\n    args:\n      - /old/demo_mcp_server.py\n    env:\n      GOVERNANCE_STATE_FILE: /old/state.json\n    chatMenu: false\nendpoints:\n  agents:\n    disableBuilder: false\n"""
SOURCE_WITH_LEGACY_APPROVAL = SOURCE + """interface:\n  agents:\n    toolApproval:\n      enabled: true\n      ask:\n        - apply_demo_remediation_mcp_agentcore_governance\n      reason: \"ASK - Review {tool}. Approve = one harmless local marker, no AWS or secret access.\"\n"""


class Issue40ConfigureLibreChatTests(unittest.TestCase):
    def test_replaces_only_known_server_block_and_retains_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / "librechat.yaml"
            config.write_text(SOURCE, encoding="utf-8")
            server_dir = root / "agentcore-governance"
            server_dir.mkdir()
            (server_dir / "demo_mcp_server.py").write_text("# test\n", encoding="utf-8")
            configure.configure(
                config=config, server_dir=server_dir, state_file=root / "state.json",
                gateway_url=GATEWAY_URL, security_group_id=SECURITY_GROUP_ID)
            updated = config.read_text(encoding="utf-8")
            self.assertIn("GOVERNANCE_GATEWAY_POLICY_ENABLED: required", updated)
            self.assertIn("GOVERNANCE_GATEWAY_URL: " + GATEWAY_URL, updated)
            self.assertIn("GOVERNANCE_SECURITY_GROUP_ID: " + SECURITY_GROUP_ID, updated)
            self.assertIn("GOVERNANCE_AWS_REMEDIATION_ENABLED: required", updated)
            self.assertIn("endpoints:\n  agents:", updated)
            self.assertEqual(config.with_name("librechat.yaml.issue40-before-gateway.bak").read_text(), SOURCE)

    def test_refuses_unknown_governance_block_field(self):
        lines = ("mcpServers:\n  agentcore_governance:\n    command: /usr/bin/python3\n"
                 "    unexpected: true\n")
        with self.assertRaises(configure.ConfigureBlocked):
            configure.known_top_level_fields(lines.splitlines(keepends=True), 1, 4, 2)

    def test_replaces_only_existing_governance_approval_reason(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / "librechat.yaml"
            config.write_text(SOURCE_WITH_LEGACY_APPROVAL, encoding="utf-8")
            server_dir = root / "agentcore-governance"
            server_dir.mkdir()
            (server_dir / "demo_mcp_server.py").write_text("# test\n", encoding="utf-8")
            configure.configure(
                config=config, server_dir=server_dir, state_file=root / "state.json",
                gateway_url=GATEWAY_URL, security_group_id=SECURITY_GROUP_ID)
            updated = config.read_text(encoding="utf-8")
            self.assertIn(configure.APPROVAL_REASON, updated)
            self.assertIn("action=remove_unrestricted_ssh", updated)
            self.assertIn("target=demo-security-group", updated)
            self.assertNotIn("harmless local marker", updated)
            self.assertIn("- apply_demo_remediation_mcp_agentcore_governance", updated)

    def test_rejects_non_managed_gateway_url(self):
        with self.assertRaises(configure.ConfigureBlocked):
            configure.require_gateway_url("https://example.invalid/mcp")

    def test_rejects_invalid_security_group_id(self):
        with self.assertRaises(configure.ConfigureBlocked):
            configure.require_security_group_id("sg-not-a-real-id")


if __name__ == "__main__":
    unittest.main()
