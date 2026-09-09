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
            "Fixed server-owned context: environment=dev, action=remove_unrestricted_ssh, target=demo-security-group",
            "Blank ticket is valid in dev",
            "Reject = no MCP call and no AWS change",
            "GOVERNANCE_AWS_READ_ENABLED: required",
            "GOVERNANCE_AWS_REMEDIATION_ENABLED: required",
            "GOVERNANCE_SECURITY_GROUP_ID:",
            "GOVERNANCE_GATEWAY_POLICY_ENABLED: required",
            "GOVERNANCE_GATEWAY_URL:",
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

    def test_read_only_security_group_result_is_sanitized_and_controls_fail_closed(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps({"SecurityGroups": [{
                "GroupId": "sg-0123456789abcdef0",
                "GroupName": "private-demo-name",
                "Description": "private description",
                "VpcId": "vpc-0123456789abcdef0",
                "OwnerId": "123456789012",
                "IpPermissions": [{
                    "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "private rule description"}],
                    "Ipv6Ranges": [{"CidrIpv6": "::/0"}],
                }],
            }]}),
            stderr="",
        )
        commands: list[list[str]] = []

        def runner(command, **_kwargs):
            commands.append(command)
            return completed

        settings = {
            "GOVERNANCE_AWS_READ_ENABLED": "required",
            "GOVERNANCE_SECURITY_GROUP_ID": "sg-0123456789abcdef0",
        }
        with mock.patch.dict(os.environ, settings, clear=False):
            result = server.read_security_group_ssh(runner=runner)
        public = json.dumps(result)
        self.assertEqual(result["api"], "ec2:DescribeSecurityGroups")
        self.assertEqual(result["compliance"], "NON_COMPLIANT")
        self.assertEqual(result["source"], "0.0.0.0/0, ::/0")
        self.assertEqual(
            commands,
            [[
                "aws", "ec2", "describe-security-groups", "--group-ids", "sg-0123456789abcdef0",
                "--region", "ap-southeast-1", "--output", "json", "--no-cli-pager",
            ]],
        )
        for private_value in ("123456789012", "private-demo-name", "private description", "vpc-", "private rule description"):
            self.assertNotIn(private_value, public)
        with mock.patch.dict(os.environ, {"GOVERNANCE_AWS_READ_ENABLED": ""}, clear=False):
            with self.assertRaises(server.GovernanceBlocked):
                server.read_security_group_ssh(runner=lambda *_args, **_kwargs: completed)
        with mock.patch.dict(
            os.environ,
            {"GOVERNANCE_AWS_READ_ENABLED": "required", "GOVERNANCE_SECURITY_GROUP_ID": ""},
            clear=False,
        ):
            with self.assertRaises(server.GovernanceBlocked):
                server.read_security_group_ssh(runner=lambda *_args, **_kwargs: completed)
        with mock.patch.dict(os.environ, settings, clear=False):
            with self.assertRaises(server.GovernanceBlocked):
                server.read_security_group_ssh(
                    runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError("aws")),
                )

    def test_ssh_compliance_is_compliant_without_unrestricted_tcp_22(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps({"SecurityGroups": [{
                "IpPermissions": [
                    {"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                    {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "10.0.0.0/8"}]},
                ],
            }]}),
            stderr="",
        )
        settings = {
            "GOVERNANCE_AWS_READ_ENABLED": "required",
            "GOVERNANCE_SECURITY_GROUP_ID": "sg-0123456789abcdef0",
        }
        with mock.patch.dict(os.environ, settings, clear=False):
            result = server.read_security_group_ssh(runner=lambda *_args, **_kwargs: completed)
        self.assertEqual(result["compliance"], "COMPLIANT")
        self.assertEqual(result["source"], "none")

    def test_exact_revoke_uses_only_fixed_public_ipv4_ssh_rule(self) -> None:
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="{}", stderr="")
        commands: list[list[str]] = []

        def runner(command, **_kwargs):
            commands.append(command)
            return completed

        settings = {
            "GOVERNANCE_AWS_REMEDIATION_ENABLED": "required",
            "GOVERNANCE_SECURITY_GROUP_ID": "sg-0123456789abcdef0",
        }
        with mock.patch.dict(os.environ, settings, clear=False):
            server.revoke_unrestricted_ssh_ingress(runner=runner)
        self.assertEqual(commands[0][:6], [
            "aws", "ec2", "revoke-security-group-ingress", "--group-id", "sg-0123456789abcdef0",
            "--ip-permissions",
        ])
        self.assertEqual(
            json.loads(commands[0][6]),
            [{"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}],
        )
        self.assertEqual(commands[0][7:], ["--region", "ap-southeast-1", "--output", "json", "--no-cli-pager"])
        with mock.patch.dict(os.environ, {"GOVERNANCE_AWS_REMEDIATION_ENABLED": ""}, clear=False):
            with self.assertRaises(server.GovernanceBlocked):
                server.revoke_unrestricted_ssh_ingress(runner=runner)

    def test_allow_ask_gateway_deny_and_exact_aws_remediation_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp, \
                mock.patch.dict(os.environ, {"GOVERNANCE_STATE_FILE": str(Path(temp) / "state.json")}, clear=False):
            finding = server.call_tool(
                "check_security_finding", {"host": "web-01"},
                security_group_read=lambda: {
                    "api": "ec2:DescribeSecurityGroups",
                    "rule": "TCP/22",
                    "source": "0.0.0.0/0",
                    "compliance": "NON_COMPLIANT",
                    "recommendation": "Remove the unrestricted TCP/22 ingress rule from the dedicated demo Security Group.",
                    "mutation": "none",
                },
            )
            finding_text = finding["content"][0]["text"]
            self.assertIn("ALLOW - Real SSH compliance result returned", finding_text)
            self.assertIn("Compliance: **NON_COMPLIANT**", finding_text)
            self.assertIn("Remove the unrestricted TCP/22 ingress rule", finding_text)
            self.assertIn("### Compact audit", finding_text)
            self.assertIn("Human decision: **not required** (read-only)", finding_text)

            # Native LibreChat Reject never enters this function.  Its only
            # truthful server-side proof is unchanged state.
            rejected_before_call = server.load_state().copy()
            self.assertEqual(rejected_before_call["remediation_calls"], 0)
            self.assertEqual(rejected_before_call["aws_remediation_attempts"], 0)

            reads = iter([
                {
                    "api": "ec2:DescribeSecurityGroups",
                    "rule": "TCP/22",
                    "source": "0.0.0.0/0",
                    "compliance": "NON_COMPLIANT",
                    "recommendation": "Remove the unrestricted TCP/22 ingress rule from the dedicated demo Security Group.",
                    "mutation": "none",
                },
                {
                    "api": "ec2:DescribeSecurityGroups",
                    "rule": "TCP/22",
                    "source": "none",
                    "compliance": "COMPLIANT",
                    "recommendation": "No unrestricted TCP/22 ingress rule is present on the dedicated demo Security Group.",
                    "mutation": "none",
                },
            ])
            revoked: list[bool] = []
            approved = server.call_tool(
                "apply_demo_remediation", {"host": "web-01", "environment": "dev"},
                gateway_check=lambda environment: "ALLOW",
                security_group_read=lambda: next(reads),
                security_group_revoke=lambda: revoked.append(True),
            )
            approved_text = approved["content"][0]["text"]
            self.assertIn("ASK / APPROVE / ALLOW - AWS remediation verified", approved_text)
            self.assertIn("Gateway decision: **ALLOW**", approved_text)
            self.assertIn("Server-owned action: `remove_unrestricted_ssh`", approved_text)
            self.assertIn("Server-owned target: `demo-security-group`", approved_text)
            self.assertIn("Provider verification: **COMPLIANT**", approved_text)
            self.assertEqual(revoked, [True])
            self.assertEqual(server.load_state()["remediation_calls"], 1)
            self.assertEqual(server.load_state()["aws_remediation_attempts"], 1)
            self.assertTrue(server.load_state()["aws_remediation_verified"])
            self.assertTrue(server.load_state()["remediated"])

            denied_calls: list[str] = []
            gateway_denied = server.call_tool(
                "apply_demo_remediation", {"host": "web-01", "environment": "prod", "ticket": "DEMO-123"},
                gateway_check=lambda environment: "DENY",
                security_group_read=lambda: denied_calls.append("read"),
                security_group_revoke=lambda: denied_calls.append("revoke"),
            )
            self.assertTrue(gateway_denied["isError"])
            denied_text = gateway_denied["content"][0]["text"]
            self.assertIn("DENY - Gateway Policy blocked remediation", denied_text)
            self.assertIn("Gateway decision: **DENY**", denied_text)
            self.assertIn("Exact AWS revoke called: **no**", denied_text)
            self.assertIn("Server-owned action: `remove_unrestricted_ssh`", denied_text)
            self.assertIn("Server-owned target: `demo-security-group`", denied_text)
            self.assertEqual(denied_calls, [])
            self.assertEqual(server.load_state()["remediation_calls"], 1)
            self.assertEqual(server.load_state()["aws_remediation_attempts"], 1)

            audit_events = server.load_state()["audit_events"]
            self.assertEqual(len(audit_events), 3)
            self.assertEqual(audit_events[-1]["final_result"], "**DENY** — Gateway blocked remediation")

            deleted = server.call_tool("delete_demo_asset", {"host": "web-01"})
            self.assertTrue(deleted["isError"])
            self.assertEqual(server.load_state()["delete_calls"], 0)
            self.assertEqual(server.state_path().stat().st_mode & 0o777, 0o600)

    def test_compliant_remediation_is_gateway_allowed_no_op(self) -> None:
        with tempfile.TemporaryDirectory() as temp, \
                mock.patch.dict(os.environ, {"GOVERNANCE_STATE_FILE": str(Path(temp) / "state.json")}, clear=False):
            calls: list[str] = []
            result = server.call_tool(
                "apply_demo_remediation", {"host": "web-01", "environment": "dev"},
                gateway_check=lambda environment: "ALLOW",
                security_group_read=lambda: {
                    "api": "ec2:DescribeSecurityGroups", "rule": "TCP/22", "source": "none",
                    "compliance": "COMPLIANT",
                    "recommendation": "No unrestricted TCP/22 ingress rule is present on the dedicated demo Security Group.",
                    "mutation": "none",
                },
                security_group_revoke=lambda: calls.append("revoke"),
            )
            text = result["content"][0]["text"]
            self.assertIn("ASK / APPROVE / ALLOW - NO_REMEDIATION_REQUIRED", text)
            self.assertIn("Server-owned action: `remove_unrestricted_ssh`", text)
            self.assertIn("Server-owned target: `demo-security-group`", text)
            self.assertIn("Exact AWS revoke called: **no**", text)
            self.assertEqual(calls, [])
            state = server.load_state()
            self.assertEqual(state["remediation_calls"], 1)
            self.assertEqual(state["aws_remediation_attempts"], 0)
            self.assertFalse(state["remediated"])

    def test_runtime_gateway_client_uses_host_role_and_exact_decisions(self) -> None:
        requests: list[dict] = []
        def gateway_envelope(environment: str) -> str:
            if environment == "dev":
                nested = {"statusCode": 200, "body": json.dumps({
                    "environment": "dev", "action": "remove_unrestricted_ssh",
                    "target": "demo-security-group", "status": "healthy", "source": "synthetic-demo"})}
                return json.dumps({"jsonrpc": "2.0", "id": "dev", "result": {
                    "isError": False, "content": [{"type": "text", "text": json.dumps(nested)}]}})
            return json.dumps({"jsonrpc": "2.0", "id": "prod", "error": {
                "code": -32002, "message": "Tool Execution Denied: default deny"}})

        def runner(*args, **kwargs):
            command = args[0]
            if command[0] == "aws":
                self.assertNotIn("--profile", command)
                return subprocess.CompletedProcess(command, 0, json.dumps({
                    "AccessKeyId": "test-access", "SecretAccessKey": "test-secret", "SessionToken": "test-token"}), "")
            self.assertEqual(command, ["curl", "--config", "-"])
            config = kwargs["input"]
            response_line = next(line for line in config.splitlines() if line.startswith("output = "))
            response_path = Path(response_line.split('"', 2)[1])
            request_path = Path(next(
                line for line in config.splitlines() if line.startswith("data-binary = ")).split('"', 2)[1][1:])
            request = json.loads(request_path.read_text())
            requests.append(request)
            environment = request["id"]
            response_path.write_text(gateway_envelope(environment), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "200", "")

        settings = {
            "GOVERNANCE_GATEWAY_POLICY_ENABLED": "required",
            "GOVERNANCE_GATEWAY_URL": "https://example.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com",
        }
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ, settings, clear=False):
            self.assertEqual(server.verify_gateway("dev", runner=runner), "ALLOW")
            self.assertEqual(server.verify_gateway("prod", runner=runner), "DENY")
        self.assertEqual(requests[0]["params"]["arguments"], {
            "environment": "dev", "action": "remove_unrestricted_ssh", "target": "demo-security-group",
        })
        self.assertEqual(requests[1]["params"]["arguments"], {
            "environment": "prod", "action": "remove_unrestricted_ssh", "target": "demo-security-group",
        })
        with mock.patch.dict(os.environ, {"GOVERNANCE_GATEWAY_POLICY_ENABLED": ""}, clear=False):
            with self.assertRaises(server.GovernanceBlocked):
                server.verify_gateway("dev", runner=runner)


if __name__ == "__main__":
    unittest.main()
