#!/usr/bin/env python3
"""Focused offline checks for the Issue #31 native CLI verifier."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import gateway_policy_poc as poc

SCRIPT = Path(__file__).with_name("gateway_policy_poc.py")


def allow_response(case_name="exact-allow", status="healthy", source="synthetic-demo"):
    context = poc.case_context(case_name)
    payload = {"environment": context["environment"], "action": context["action"],
               "target": context["target"], "status": status, "source": source}
    lambda_result = {"statusCode": 200, "body": json.dumps(payload)}
    return json.dumps({"jsonrpc": "2.0", "id": case_name, "result": {
        "isError": False, "content": [{"type": "text", "text": json.dumps(lambda_result)}]}})


def deny_response(case_name="synthetic-prod", code=-32002, message=None):
    message = message or (
        "Tool Execution Denied: Tool call not allowed due to policy enforcement "
        "[No policy applies to the request (denied by default).]")
    return json.dumps({"jsonrpc": "2.0", "id": case_name,
                       "error": {"code": code, "message": message}})


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
        self.assertIn("PRECREATE_ESTIMATED_MONTHLY_IDLE_COST_USD=1.01", result.stdout)

    def test_live_command_is_present(self):
        result = subprocess.run([sys.executable, SCRIPT, "--help"], text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--approve-live", result.stdout)

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

    def test_identity_hash_mismatch_blocks(self):
        fake = mock.Mock()
        fake.call.return_value = {"Account": "111122223333", "Arn": "arn:example"}
        env = {"AWS_PROFILE": poc.PROFILE, "AWS_REGION": poc.REGION,
               "AGENTCORE_EXPECTED_ACCOUNT_SHA256": poc.digest("wrong"),
               "AGENTCORE_EXPECTED_CALLER_SHA256": poc.digest("wrong")}
        with mock.patch.dict(os.environ, env, clear=False), self.assertRaises(poc.Blocked):
            poc.require_live_gates(fake)
        fake.call.assert_called_once()

    def test_scoped_aws_environment_removes_ambient_credentials(self):
        source = {"AWS_ACCESS_KEY_ID": "ambient", "AWS_SECRET_ACCESS_KEY": "ambient",
                  "AWS_SESSION_TOKEN": "ambient", "AWS_WEB_IDENTITY_TOKEN_FILE": "/tmp/x",
                  "AWS_ROLE_ARN": "ambient", "KEEP_ME": "yes"}
        env = poc.scoped_aws_env(source)
        for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
                     "AWS_WEB_IDENTITY_TOKEN_FILE", "AWS_ROLE_ARN"):
            self.assertNotIn(name, env)
        self.assertEqual(env["AWS_PROFILE"], poc.PROFILE)
        self.assertEqual(env["AWS_REGION"], poc.REGION)
        self.assertEqual(env["KEEP_ME"], "yes")

    def test_exact_tuple_allow_and_all_bounded_denials_pass(self):
        poc.parse_allow_response(200, allow_response(), "exact-allow")
        for case_name in ("wrong-action", "wrong-target", "synthetic-prod"):
            with self.subTest(case_name=case_name):
                poc.parse_deny_response(200, deny_response(case_name), case_name)

    def test_false_positive_responses_are_rejected(self):
        bad_cases = (
            (200, "synthetic-demo healthy", 200, "Authorization denied"),
            (200, json.dumps({"jsonrpc": "2.0", "id": "exact-allow", "error": {
                "code": -32603, "message": "synthetic-demo healthy"}}), 200, deny_response()),
            (200, allow_response(), 401, json.dumps({"message": "Authorization token expired"})),
            (200, allow_response(), 200, json.dumps({"jsonrpc": "2.0", "id": "synthetic-prod",
                "result": {"isError": False, "content": [{"type": "text", "text": "denied"}]}})),
            (200, allow_response(status="unhealthy"), 200, deny_response()),
            (200, allow_response(), 200, deny_response(code=-32001)),
        )
        for dev_code, dev_body, prod_code, prod_body in bad_cases:
            with self.subTest(prod_code=prod_code), self.assertRaises(poc.Blocked):
                poc.parse_allow_response(dev_code, dev_body, "exact-allow")
                poc.parse_deny_response(prod_code, prod_body, "synthetic-prod")
        with self.assertRaises(poc.Blocked):
            poc.parse_deny_response(200, deny_response("exact-allow"), "exact-allow")

    def test_case_cost_and_endpoint_contracts(self):
        poc.validate_case(poc.TOOL_NAME, "exact-allow")
        self.assertEqual(poc.case_context("exact-allow"), {
            "environment": "dev", "action": "remove_unrestricted_ssh",
            "target": "demo-security-group", "decision": "ALLOW",
        })
        for case_name in ("wrong-action", "wrong-target", "synthetic-prod"):
            self.assertEqual(poc.case_context(case_name)["decision"], "DENY")
        self.assertEqual(poc.validate_cost("1.01"), 1.01)
        good_url = "https://example.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com"
        self.assertEqual(poc.validate_gateway_url(good_url), good_url)
        for value in ("bad", -1, 2, float("inf")):
            with self.subTest(value=value), self.assertRaises(poc.Blocked):
                poc.validate_cost(value)
        for tool, case_name in (("other", "exact-allow"), (poc.TOOL_NAME, "stage")):
            with self.assertRaises(poc.Blocked):
                poc.validate_case(tool, case_name)
        for url in ("http://example.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com",
                    "https://example.invalid/mcp",
                    "https://user:pass@example.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com"):
            with self.assertRaises(poc.Blocked):
                poc.validate_gateway_url(url)

    def test_exact_cedar_schema_and_lambda_context_are_bound(self):
        statement = poc.cedar_statement(
            "arn:aws:sts::111122223333:assumed-role/Demo/session",
            "arn:aws:bedrock-agentcore:ap-southeast-1:111122223333:gateway/demo",
        )
        for fragment in (
            'context.input.environment == "dev"',
            'context.input.action == "remove_unrestricted_ssh"',
            'context.input.target == "demo-security-group"',
        ):
            self.assertIn(fragment, statement)
        schema = json.loads(poc.TOOL_SCHEMA.read_text())
        self.assertEqual(schema[0]["inputSchema"]["required"], ["environment", "action", "target"])
        for definition in schema[0]["inputSchema"]["properties"].values():
            self.assertEqual(set(definition), {"type", "description"})
        self.assertIn("action = event.get('action')", poc.lambda_source())
        self.assertIn("target = event.get('target')", poc.lambda_source())

    def test_each_fixed_deny_case_has_zero_backend_delta(self):
        gateway = {"gatewayUrl": "https://demo.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com"}
        for case_name in ("wrong-action", "wrong-target", "synthetic-prod"):
            with self.subTest(case_name=case_name):
                with tempfile.TemporaryDirectory() as directory:
                    aws = mock.Mock()
                    aws.private_dir = Path(directory)
                    with mock.patch.object(poc, "PRIVATE_ROOT", Path(directory)), \
                            mock.patch.object(poc, "quiet_metric_boundary", return_value=datetime.now(timezone.utc)), \
                            mock.patch.object(poc, "invoke_gateway", return_value=(200, deny_response(case_name))), \
                            mock.patch.object(poc, "wait_for_metric", return_value=0) as metric_wait:
                        evidence = poc.prove_fixed_action(
                            aws, gateway, case_name, deny_observation_seconds=0)
                self.assertEqual(evidence["backend_delta"], 0)
                metric_wait.assert_called_once()

    def test_metric_wait_rejects_extra_invocation(self):
        with mock.patch.object(poc, "metric_sum", return_value=2):
            with self.assertRaises(poc.Blocked):
                poc.wait_for_metric(mock.Mock(), mock.Mock(), 1, [], timeout=1)

    def test_exact_topology_counts_reject_duplicates(self):
        items = [{"ResourceType": key} for key, count in poc.EXPECTED_APP_COUNTS.items()
                 for _ in range(count)]
        self.assertEqual(poc.assert_resource_counts(
            items, poc.EXPECTED_APP_COUNTS, "app"), poc.EXPECTED_APP_COUNTS)
        with self.assertRaises(poc.Blocked):
            poc.assert_resource_counts(items + [items[0]], poc.EXPECTED_APP_COUNTS, "app")

    def test_measured_storage_is_included_in_cost(self):
        empty = {"s3_bytes": 0, "ecr_bytes": 0, "log_bytes": 0}
        one_gib_each = {"s3_bytes": 1024 ** 3, "ecr_bytes": 1024 ** 3,
                        "log_bytes": 1024 ** 3}
        self.assertEqual(poc.retained_cost(1, empty), 1.01)
        self.assertAlmostEqual(poc.retained_cost(1, one_gib_each), 1.76)
        with self.assertRaises(poc.Blocked):
            poc.retained_cost(2, empty)

    def test_live_linkage_and_exact_cedar_statement(self):
        gateway_arn = "arn:aws:bedrock-agentcore:ap-southeast-1:111122223333:gateway/demo"
        engine_arn = "arn:aws:bedrock-agentcore:ap-southeast-1:111122223333:policy-engine/demo"
        lambda_arn = "arn:aws:lambda:ap-southeast-1:111122223333:function:demo"
        identity = {"Arn": "arn:aws:sts::111122223333:assumed-role/Demo/session"}
        gateway_state = {"gatewayArn": gateway_arn}
        gateway = {"status": "READY", "authorizerType": "AWS_IAM", "protocolType": "MCP",
                   "gatewayUrl": "https://demo.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com",
                   "policyEngineConfiguration": {"arn": engine_arn, "mode": "ENFORCE"}}
        target = {"status": "READY", "name": poc.TARGET_NAME, "gatewayArn": gateway_arn,
                  "targetConfiguration": {"mcp": {"lambda": {"lambdaArn": lambda_arn}}}}
        engine = {"status": "ACTIVE", "policyEngineArn": engine_arn}
        policy = {"status": "ACTIVE", "enforcementMode": "ACTIVE", "definition": {
            "policy": {"statement": poc.cedar_statement(identity["Arn"], gateway_arn)}}}
        poc.validate_live_links(gateway, target, engine, policy, gateway_state,
                                lambda_arn, identity)
        policy["definition"]["policy"]["statement"] += " permit(principal);"
        with self.assertRaises(poc.Blocked):
            poc.validate_live_links(gateway, target, engine, policy, gateway_state,
                                    lambda_arn, identity)
        policy["definition"]["policy"]["statement"] = poc.cedar_statement(
            identity["Arn"], gateway_arn)
        target["targetConfiguration"]["mcp"]["lambda"]["lambdaArn"] += "-other"
        with self.assertRaises(poc.Blocked):
            poc.validate_live_links(gateway, target, engine, policy, gateway_state,
                                    lambda_arn, identity)

    def test_private_native_project_shape_and_permissions(self):
        identity = {"Account": "111122223333",
                    "Arn": "arn:aws:sts::111122223333:assumed-role/Demo/session"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "Issue31Policy" / "agentcore"
            project.mkdir(parents=True)
            with mock.patch.object(poc, "PRIVATE_ROOT", root):
                rendered = poc.render_private_project(
                    root,
                    "arn:aws:lambda:ap-southeast-1:111122223333:function:demo",
                    identity,
                    "arn:aws:bedrock-agentcore:ap-southeast-1:111122223333:gateway/demo")
                data = poc.validate_rendered_project(rendered)
            self.assertEqual((project / "agentcore.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual((project / "aws-targets.json").stat().st_mode & 0o777, 0o600)
        gateway = data["agentCoreGateways"][0]
        self.assertEqual(data["runtimes"], [])
        self.assertEqual(data["harnesses"], [])
        self.assertEqual(gateway["authorizerType"], "AWS_IAM")
        self.assertEqual(gateway["policyEngineConfiguration"]["mode"], "ENFORCE")
        self.assertEqual(gateway["targets"][0]["targetType"], "lambdaFunctionArn")
        self.assertNotIn("prod", data["policyEngines"][0]["policies"][0]["statement"])

    def test_native_state_rejects_duplicate_or_missing_policy(self):
        state = {"targets": {"default": {"resources": {
            "mcp": {"gateways": {poc.GATEWAY_NAME: {"gatewayId": "g",
                "gatewayArn": "a", "gatewayUrl": "u",
                "targets": {poc.TARGET_NAME: {"targetId": "t"}}}}},
            "policyEngines": {poc.ENGINE_NAME: {"policyEngineId": "e"}},
            "policies": {f"{poc.ENGINE_NAME}/{poc.POLICY_NAME}": {"policyId": "p"}},
            "stackName": poc.STACK_NAME}}}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".cli" / "deployed-state.json"
            path.parent.mkdir()
            path.write_text(json.dumps(state))
            poc.native_resources(Path(directory), complete=True)
            state["targets"]["default"]["resources"]["policies"] = {}
            path.write_text(json.dumps(state))
            with self.assertRaises(poc.Blocked):
                poc.native_resources(Path(directory), complete=True)

    def test_retained_target_schema_converges_only_the_known_lambda_target(self):
        lambda_arn = "arn:aws:lambda:ap-southeast-1:111122223333:function:demo"
        schema_uri = "s3://bucket/" + "a" * 64 + ".json"
        gateway_state = {"gatewayId": "gateway", "targets": {poc.TARGET_NAME: {"targetId": "target"}}}
        expected = poc.expected_lambda_target_configuration(lambda_arn, schema_uri)
        retained_fields = {
            "name": poc.TARGET_NAME,
            "description": f"Lambda function target: {poc.TARGET_NAME}",
            "credentialProviderConfigurations": poc.expected_gateway_target_credentials(),
            "metadataConfiguration": poc.expected_gateway_target_metadata(),
        }
        ready = {"status": "READY", **retained_fields, "targetConfiguration": expected}
        aws = mock.Mock()
        with mock.patch.object(poc, "wait_gateway_target_ready", return_value=ready):
            self.assertFalse(poc.converge_gateway_tool_schema(aws, gateway_state, lambda_arn, schema_uri))
        aws.call.assert_not_called()

        old = {"status": "READY", **retained_fields, "targetConfiguration": {
            "mcp": {"lambda": {"lambdaArn": lambda_arn, "toolSchema": {"inlinePayload": []}}}}}
        aws = mock.Mock()
        with mock.patch.object(poc, "wait_gateway_target_ready", side_effect=[old, ready]):
            self.assertTrue(poc.converge_gateway_tool_schema(aws, gateway_state, lambda_arn, schema_uri))
        self.assertEqual(aws.call.call_args.args[:2], ("bedrock-agentcore-control", "update-gateway-target"))
        self.assertEqual(aws.call.call_args.args[2]["name"], poc.TARGET_NAME)
        self.assertEqual(aws.call.call_args.args[2]["credentialProviderConfigurations"],
                         poc.expected_gateway_target_credentials())
        self.assertNotIn("metadataConfiguration", aws.call.call_args.args[2])
        self.assertEqual(aws.call.call_args.args[2]["targetConfiguration"], expected)

        drifted = {"status": "READY", "targetConfiguration": {
            "mcp": {"lambda": {"lambdaArn": lambda_arn + "-other", "toolSchema": {"inlinePayload": []}}}}}
        with mock.patch.object(poc, "wait_gateway_target_ready", return_value=drifted), self.assertRaises(poc.Blocked):
            poc.converge_gateway_tool_schema(mock.Mock(), gateway_state, lambda_arn, schema_uri)

    def test_native_schema_uri_must_reference_the_rendered_reviewed_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            output = project / "cdk" / "cdk.out"
            output.mkdir(parents=True)
            digest = "b" * 64
            uri = f"s3://bucket/{digest}.json"
            template = {"Resources": {"Target": {
                "Type": "AWS::BedrockAgentCore::GatewayTarget",
                "Properties": {"TargetConfiguration": {"Mcp": {"Lambda": {
                    "ToolSchema": {"S3": {"Uri": uri}}}}}},
            }}}
            (output / f"{poc.STACK_NAME}.template.json").write_text(json.dumps(template))
            (output / f"asset.{digest}.json").write_text(poc.TOOL_SCHEMA.read_text())
            self.assertEqual(poc.rendered_tool_schema_uri(project), uri)
            (output / f"asset.{digest}.json").write_text("[]")
            with self.assertRaises(poc.Blocked):
                poc.rendered_tool_schema_uri(project)

    def test_schema_asset_staging_is_exact_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            output = project / "cdk" / "cdk.out"
            output.mkdir(parents=True)
            digest = "c" * 64
            uri = f"s3://bucket/{digest}.json"
            asset = output / f"asset.{digest}.json"
            asset.write_text("[]")
            aws = mock.Mock()
            aws.env = {}
            aws.call.return_value = {"ContentLength": asset.stat().st_size}
            self.assertFalse(poc.ensure_rendered_tool_schema_asset(aws, project, uri))
            aws.call.assert_called_once_with("s3api", "head-object", {"Bucket": "bucket", "Key": f"{digest}.json"})

            aws = mock.Mock()
            aws.env = {}
            aws.call.side_effect = [poc.Blocked("NoSuchKey"), {"ContentLength": asset.stat().st_size}]
            runner = mock.Mock(return_value=subprocess.CompletedProcess([], 0, "", ""))
            self.assertTrue(poc.ensure_rendered_tool_schema_asset(aws, project, uri, runner=runner))
            self.assertEqual(runner.call_args.args[0][0:3], ["aws", "s3", "cp"])
            self.assertEqual(runner.call_args.args[0][3], str(asset))
            self.assertEqual(runner.call_args.args[0][4], uri)

    def test_sanitization_covers_real_credential_field_names(self):
        raw = ('123456789012 arn:aws:iam::123456789012:role/x '
               'https://example.invalid/mcp "AccessKeyId":"AKIAEXAMPLE", '
               '"SecretAccessKey":"secret", "SessionToken":"token" /home/user/private')
        clean = poc.sanitize(raw)
        for forbidden in ("123456789012", "arn:aws", "https://", "AKIAEXAMPLE",
                          '"secret"', '"token"', "/home/user"):
            self.assertNotIn(forbidden, clean)

    def test_pass_is_not_reported_when_inventory_blocks(self):
        with mock.patch.object(poc, "live_context", return_value=(Path("/private"), mock.Mock(), {})), \
                mock.patch.object(poc, "ensure_lambda_prerequisite", return_value="lambda"), \
                mock.patch.object(poc, "inventory_and_cost", side_effect=poc.Blocked("inventory")), \
                mock.patch.object(poc, "prove_deltas") as proof:
            with self.assertRaises(poc.Blocked):
                poc.prove_live()
        proof.assert_not_called()

    def test_one_retained_action_validates_only_its_gateway_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            aws = mock.Mock()
            aws.private_dir = Path(directory)
            gateway = {"gatewayUrl": "https://demo.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com"}
            with mock.patch.object(poc, "PRIVATE_ROOT", Path(directory)), \
                    mock.patch.object(poc, "retained_live_context", return_value=(aws, gateway, 1.01)), \
                    mock.patch.object(poc, "invoke_gateway", return_value=(200, allow_response())), \
                    mock.patch.object(poc, "parse_allow_response") as parse_allow, \
                    mock.patch.object(poc, "wait_for_metric") as metric_wait:
                result = poc.verify_retained_action("exact-allow")
        self.assertEqual(result, {"case": "exact-allow", "context": {
            "environment": "dev", "action": "remove_unrestricted_ssh", "target": "demo-security-group"},
            "decision": "ALLOW", "retained_cost_gate": "PASS"})
        parse_allow.assert_called_once()
        metric_wait.assert_not_called()


if __name__ == "__main__":
    unittest.main()
