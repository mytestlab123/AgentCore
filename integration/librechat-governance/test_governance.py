#!/usr/bin/env python3
"""Offline contract test for the native LibreChat governance configuration."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "librechat.yaml.example"
SERVER = ROOT / "demo_mcp_server.py"
HOOK = ROOT / "approval-hook.cjs"

sys.path.insert(0, str(ROOT))
import demo_mcp_server as server  # noqa: E402


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
            "type: mongo",
            "ASK - Review {tool}.",
            "blank ticket is valid in dev",
            "Reject = no MCP call and no state change",
            "GOVERNANCE_AWS_READ_ENABLED: required",
            "GOVERNANCE_GATEWAY_POLICY_ENABLED: required",
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

    def test_stdio_lists_the_exact_governed_tool_surface(self) -> None:
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
            finally:
                if proc.stdin:
                    proc.stdin.close()
                proc.terminate()
                proc.wait(timeout=5)
                if proc.stdout:
                    proc.stdout.close()

    def test_read_only_aws_result_is_sanitized_and_controls_fail_closed(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps({"Account": "123456789012", "Arn": "arn:aws:sts::123456789012:assumed-role/demo/x", "UserId": "sensitive-id"}),
            stderr="",
        )
        with mock.patch.dict(os.environ, {"GOVERNANCE_AWS_READ_ENABLED": "required"}, clear=False):
            result = server.read_aws_identity(runner=lambda *_args, **_kwargs: completed)
        public = json.dumps(result)
        self.assertEqual(result["api"], "sts:GetCallerIdentity")
        for private_value in ("123456789012", "arn:aws", "sensitive-id"):
            self.assertNotIn(private_value, public)
        with mock.patch.dict(os.environ, {"GOVERNANCE_AWS_READ_ENABLED": ""}, clear=False):
            with self.assertRaises(server.GovernanceBlocked):
                server.read_aws_identity(runner=lambda *_args, **_kwargs: completed)

    def test_allow_ask_gateway_deny_and_local_effect_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp, \
                mock.patch.dict(os.environ, {"GOVERNANCE_STATE_FILE": str(Path(temp) / "state.json")}, clear=False):
            finding = server.call_tool(
                "check_security_finding", {"host": "web-01"},
                aws_read=lambda: {"api": "sts:GetCallerIdentity", "result": "identity verified", "mutation": "none"},
            )
            self.assertIn("ALLOW - Security finding and AWS read returned", finding["content"][0]["text"])

            rejected_before_call = server.load_state().copy()
            self.assertEqual(rejected_before_call["remediation_calls"], 0)

            approved = server.call_tool(
                "apply_demo_remediation", {"host": "web-01", "environment": "dev"},
                gateway_check=lambda environment: "ALLOW",
            )
            self.assertIn("ASK / APPROVE / ALLOW - Remediation completed", approved["content"][0]["text"])
            self.assertEqual(server.load_state()["remediation_calls"], 1)
            self.assertTrue(server.load_state()["remediated"])

            gateway_denied = server.call_tool(
                "apply_demo_remediation", {"host": "web-01", "environment": "prod", "ticket": "DEMO-123"},
                gateway_check=lambda environment: "DENY",
            )
            self.assertTrue(gateway_denied["isError"])
            self.assertIn("DENY - Gateway Policy blocked remediation", gateway_denied["content"][0]["text"])
            self.assertEqual(server.load_state()["remediation_calls"], 1)

            deleted = server.call_tool("delete_demo_asset", {"host": "web-01"})
            self.assertTrue(deleted["isError"])
            self.assertEqual(server.load_state()["delete_calls"], 0)
            self.assertEqual(server.state_path().stat().st_mode & 0o777, 0o600)

    def test_gateway_verifier_requires_exact_safe_output(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout="GATEWAY_DECISION=ALLOW\nRETAINED_COST_GATE=PASS\nGATEWAY_ACTION_VERIFIED=PASS\n",
            stderr="",
        )
        with mock.patch.dict(os.environ, {"GOVERNANCE_GATEWAY_POLICY_ENABLED": "required"}, clear=False):
            self.assertEqual(server.verify_gateway("dev", runner=lambda *_args, **_kwargs: completed), "ALLOW")
        incomplete = subprocess.CompletedProcess(args=[], returncode=0, stdout="GATEWAY_DECISION=ALLOW\n", stderr="")
        with mock.patch.dict(os.environ, {"GOVERNANCE_GATEWAY_POLICY_ENABLED": "required"}, clear=False):
            with self.assertRaises(server.GovernanceBlocked):
                server.verify_gateway("dev", runner=lambda *_args, **_kwargs: incomplete)


if __name__ == "__main__":
    unittest.main()
