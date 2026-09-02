#!/usr/bin/env python3
"""Offline contract test for the native LibreChat governance configuration."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "librechat.yaml.example"
SERVER = ROOT / "demo_mcp_server.py"
HOOK = ROOT / "approval-hook.cjs"


class GovernanceContractTests(unittest.TestCase):
    def test_native_policy_and_exact_tools_are_declared(self) -> None:
        config = CONFIG.read_text(encoding="utf-8")
        for value in (
            "toolApproval:",
            "enabled: true",
            "disableBuilder: false",
            "interface:",
            "create: true",
            "mcpServers:",
            "mcp:agentcore_governance:check_security_finding",
            "mcp:agentcore_governance:apply_demo_remediation",
            "mcp:agentcore_governance:delete_demo_asset",
            "checkpointer:",
            "type: memory",
            "ASK - Review {tool}.",
            "blank ticket is valid in dev",
            "Reject = no MCP call and no state change",
        ):
            self.assertIn(value, config)
        # The remediation name appears once in `ask` and once in the hook
        # matcher; those are still only three logical tools.
        self.assertEqual(config.count("mcp:agentcore_governance:check_security_finding"), 1)
        self.assertEqual(config.count("mcp:agentcore_governance:apply_demo_remediation"), 2)
        self.assertEqual(config.count("mcp:agentcore_governance:delete_demo_asset"), 1)

    def test_trusted_hook_only_tightens_prod_context(self) -> None:
        script = f"""
const build = require({json.dumps(str(HOOK))});
const factory = build({{}})({{}});
const run = async (toolInput) => await factory({{toolName:'mcp:agentcore_governance:apply_demo_remediation', toolInput}});
Promise.all([run({{environment:'dev'}}), run({{environment:'prod',ticket:''}}), run({{environment:'prod',ticket:'DEMO-123'}})])
  .then((values) => process.stdout.write(JSON.stringify(values)))
  .catch((error) => {{ console.error(error); process.exit(1); }});
"""
        result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
        values = json.loads(result.stdout)
        self.assertEqual(values[0], {})
        self.assertEqual(values[1]["decision"], "deny")
        self.assertEqual(values[2], {})

    def test_mcp_allow_and_approved_effect_without_aws(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "state.json"
            env = {**os.environ, "GOVERNANCE_STATE_FILE": str(state)}
            proc = subprocess.Popen(
                [sys.executable, str(SERVER)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                env=env,
            )

            def request(request_id: int, method: str, params: dict | None = None) -> dict:
                assert proc.stdin is not None and proc.stdout is not None
                proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}) + "\n")
                proc.stdin.flush()
                return json.loads(proc.stdout.readline())

            try:
                request(1, "initialize")
                tools = request(2, "tools/list")["result"]["tools"]
                self.assertEqual([tool["name"] for tool in tools], [
                    "check_security_finding", "apply_demo_remediation", "delete_demo_asset"
                ])
                finding = request(3, "tools/call", {"name": "check_security_finding", "arguments": {"host": "web-01"}})
                self.assertIn("HIGH", finding["result"]["content"][0]["text"])
                self.assertIn("ALLOW - Security finding returned", finding["result"]["content"][0]["text"])
                approved = request(4, "tools/call", {"name": "apply_demo_remediation", "arguments": {"host": "web-01", "environment": "dev"}})
                self.assertIn("ASK / APPROVE - Remediation completed", approved["result"]["content"][0]["text"])
                self.assertIn("MCP tool calls: **1**", approved["result"]["content"][0]["text"])
                denied = request(5, "tools/call", {"name": "delete_demo_asset", "arguments": {"host": "web-01"}})
                self.assertTrue(denied["result"]["isError"])
                self.assertIn("DENY - Deletion blocked", denied["result"]["content"][0]["text"])
                saved = json.loads(state.read_text(encoding="utf-8"))
                self.assertEqual(saved["finding_calls"], 1)
                self.assertEqual(saved["remediation_calls"], 1)
                self.assertEqual(saved["delete_calls"], 0)
                self.assertTrue(saved["remediated"])
                self.assertEqual(state.stat().st_mode & 0o777, 0o600)
            finally:
                if proc.stdin:
                    proc.stdin.close()
                proc.terminate()
                proc.wait(timeout=5)
                if proc.stdout:
                    proc.stdout.close()


if __name__ == "__main__":
    unittest.main()
