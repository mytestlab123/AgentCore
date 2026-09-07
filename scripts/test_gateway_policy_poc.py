#!/usr/bin/env python3
"""Focused offline checks for the Issue 31 native CLI verifier."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import gateway_policy_poc as poc

SCRIPT = Path(__file__).with_name("gateway_policy_poc.py")


class GatewayPolicyPocTest(unittest.TestCase):
    def test_plan_makes_no_external_call(self):
        with tempfile.TemporaryDirectory() as directory:
            blocker = Path(directory) / "aws"
            blocker.write_text("#!/bin/sh\nexit 99\n")
            blocker.chmod(0o755)
            env = os.environ | {"PATH": f"{directory}:{os.environ['PATH']}"}
            result = subprocess.run([sys.executable, SCRIPT], env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(result.returncode, 0)
        self.assertIn("AWS_CALLS=0", result.stdout)
        self.assertIn("NATIVE_AGENTCORE_CLI=0.28.1", result.stdout)

    def test_scope_and_hash_gates_fail_before_aws(self):
        fake = mock.Mock()
        cases = (("wrong", poc.REGION, "x", "y"),
                 (poc.PROFILE, "us-east-1", "x", "y"),
                 (poc.PROFILE, poc.REGION, "", ""))
        for profile, region, account_hash, caller_hash in cases:
            env = {"AWS_PROFILE": profile, "AWS_REGION": region,
                   "AGENTCORE_EXPECTED_ACCOUNT_SHA256": account_hash,
                   "AGENTCORE_EXPECTED_CALLER_SHA256": caller_hash}
            with self.subTest(profile=profile, region=region), \
                    mock.patch.dict(os.environ, env, clear=False), \
                    self.assertRaises(poc.Blocked):
                poc.require_live_gates(fake)
        fake.call.assert_not_called()

    def test_decision_and_cost_validation_are_fail_closed(self):
        poc.validate_case(poc.TOOL_NAME, "dev")
        poc.validate_results(200, "synthetic-demo healthy", 1,
                             200, "Authorization denied", 0)
        self.assertEqual(poc.validate_cost("0.01"), 0.01)
        for value in ("bad", -1, 2, float("inf")):
            with self.subTest(value=value), self.assertRaises(poc.Blocked):
                poc.validate_cost(value)
        with self.assertRaises(poc.Blocked):
            poc.validate_case("other", "dev")
        with self.assertRaises(poc.Blocked):
            poc.validate_case(poc.TOOL_NAME, "stage")
        with self.assertRaises(poc.Blocked):
            poc.validate_results(200, "synthetic-demo healthy", 1,
                                 403, "Authorization denied", 1)

    def test_private_native_project_shape(self):
        identity = {"Account": "111122223333",
                    "Arn": "arn:aws:sts::111122223333:assumed-role/Demo/session"}
        with tempfile.TemporaryDirectory() as directory:
            project = poc.render_private_project(
                Path(directory),
                "arn:aws:lambda:ap-southeast-1:111122223333:function:demo",
                identity)
            data = poc.validate_rendered_project(project)
            self.assertEqual((project / "agentcore.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual((project / "aws-targets.json").stat().st_mode & 0o777, 0o600)
        gateway = data["agentCoreGateways"][0]
        self.assertEqual(data["runtimes"], [])
        self.assertEqual(data["harnesses"], [])
        self.assertEqual(gateway["authorizerType"], "AWS_IAM")
        self.assertEqual(gateway["policyEngineConfiguration"]["mode"], "ENFORCE")
        self.assertEqual(gateway["targets"][0]["targetType"], "lambdaFunctionArn")

    def test_sanitization_and_committed_placeholders(self):
        raw = ("123456789012 arn:aws:iam::123456789012:role/x "
               "https://example.invalid/mcp secret_key=abc /home/user/private")
        clean = poc.sanitize(raw)
        for forbidden in ("123456789012", "arn:aws", "https://", "abc", "/home/user"):
            self.assertNotIn(forbidden, clean)
        data = json.loads(poc.TEMPLATE.read_text())
        text = json.dumps(data)
        self.assertIn("__PRIVATE_LAMBDA_ARN__", text)
        self.assertIn("__PRIVATE_CEDAR_STATEMENT__", text)
        self.assertNotRegex(text, r"\b\d{12}\b")
        self.assertNotIn("arn:aws:", text)


if __name__ == "__main__":
    unittest.main()
