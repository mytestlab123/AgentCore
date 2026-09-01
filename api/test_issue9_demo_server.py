import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from issue9_demo_server import CodexKeyController, Issue9Handler, LiveAwsPlayground, ProofController, _read_platform_config, build_public_status


class Issue9DemoStatusTests(unittest.TestCase):
    def test_inspector_sample_contains_exactly_fifty_public_safe_rows(self):
        records = LiveAwsPlayground()._source("inspector", {})

        self.assertEqual(len(records), 50)
        self.assertEqual(
            set(records[0]),
            {"cve_id", "severity", "package_name", "installed_version", "fixed_version", "status"},
        )
        self.assertNotIn("instance_id", records[0])

    def test_platform_config_requires_mode_600_and_exact_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.env"
            config.write_text(
                'PLATFORM_API_KEY="secret"\nPLATFORM_API_BASE_URL="https://api-public.ai.tech.gov.sg"\nPLATFORM_AI_MODEL="gpt-5.6-luna"\n',
                encoding="utf-8",
            )
            config.chmod(0o600)
            values = _read_platform_config(config)
            self.assertEqual(values["PLATFORM_AI_MODEL"], "gpt-5.6-luna")
            config.chmod(0o644)
            with self.assertRaisesRegex(RuntimeError, "mode 600"):
                _read_platform_config(config)

    def test_compare_uses_only_fixed_two_provider_lanes(self):
        class ComparePlayground(LiveAwsPlayground):
            def _invoke(self, key_name, prompt):
                self.nova_input = (key_name, prompt)
                return "Nova answer", {"inputTokens": 10, "outputTokens": 5}, "end_turn"

            def _invoke_platform(self, prompt):
                self.platform_input = prompt
                return "Luna answer", {"input_tokens": 11, "output_tokens": 6}, "completed"

        controller = ComparePlayground()
        result = controller.compare({"prompt": "Explain one synthetic security risk."})

        self.assertEqual([item["provider"] for item in result["results"]], ["Amazon Bedrock", "GovTech PlatformAI"])
        self.assertEqual(result["results"][0]["model"], "global.amazon.nova-2-lite-v1:0")
        self.assertEqual(result["results"][1]["model"], "gpt-5.6-luna")
        self.assertEqual(controller.nova_input[0], "nova2")
        self.assertNotIn("EC2", controller.platform_input)

    def test_compare_preserves_nova_when_platform_is_unavailable(self):
        class PartialPlayground(LiveAwsPlayground):
            def _invoke(self, key_name, prompt):
                return "Nova answer", {"inputTokens": 10, "outputTokens": 5}, "end_turn"

            def _invoke_platform(self, prompt):
                raise RuntimeError("NOT AVAILABLE: PlatformAI GPT-5.6 Luna is unavailable.")

        result = PartialPlayground().compare({"prompt": "Explain one synthetic security risk."})

        self.assertEqual(result["results"][0]["status"], "ALLOW")
        self.assertEqual(result["results"][1]["status"], "NOT AVAILABLE")
        self.assertEqual(result["results"][1]["inputTokens"], None)

    def test_platform_models_use_sanitized_tools_and_omit_gpt_reasoning(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.env"
            config.write_text(
                'PLATFORM_API_KEY="secret"\nPLATFORM_API_BASE_URL="https://api-public.ai.tech.gov.sg"\nPLATFORM_AI_MODEL="gpt-5.6-luna"\n',
                encoding="utf-8",
            )
            config.chmod(0o600)

            class ClaudePlayground(LiveAwsPlayground):
                def _role_env(self):
                    return {}

                def _source(self, tool, env):
                    return [{"instanceAlias": "real-name-must-not-leave", "state": "running", "instanceType": "small"}]

                def _platform_request(self, path, key, payload=None):
                    if path == "models":
                        return {"data": [{"id": "azure.claude-haiku-4-5"}, {"id": "gemini-2.5-flash"}]}
                    self.payload = payload
                    return {"status": "completed", "output": [{"content": [{"type": "output_text", "text": "Safe answer"}]}],
                            "usage": {"input_tokens": 9, "output_tokens": 4}}

            controller = ClaudePlayground(platform_config=config)
            result = controller.platform_tool({"model": "gemini-2.5-flash", "tool": "ec2", "prompt": "Summarize."})

        self.assertEqual(result["model"], "gemini-2.5-flash")
        self.assertEqual(result["tool"], "ec2")
        self.assertEqual(result["records"][0]["instanceAlias"], "instance-1")
        self.assertNotIn("real-name-must-not-leave", json.dumps(controller.payload))
        self.assertNotIn("reasoning", controller.payload)

    def test_nova_key_status_uses_fingerprint_not_secret_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("nova2=secret-nova-two\nnova_pro=secret-nova-pro\n", encoding="utf-8")
            env_file.chmod(0o600)

            status = LiveAwsPlayground(key_env=env_file).key_status()

        self.assertTrue(status["keys"]["nova2"]["available"])
        self.assertTrue(status["keys"]["nova2"]["masked"].startswith("bedrock-"))
        self.assertNotIn("secret-nova", json.dumps(status))

    def test_nova_key_reveal_rejects_unknown_name(self):
        with self.assertRaisesRegex(RuntimeError, "Unknown Nova"):
            LiveAwsPlayground().reveal_key("unknown")

    def test_ssm_deny_never_invokes_model_or_returns_records(self):
        class DeniedPlayground(LiveAwsPlayground):
            def _role_env(self):
                return {}

            def _source(self, tool, env):
                self.assert_tool = tool
                return []

            def _invoke(self, key_name, prompt):
                raise AssertionError("The model must not run for the SSM deny proof")

        result = DeniedPlayground().run({"model": "nova2", "tool": "ssm", "prompt": "list secrets"})

        self.assertEqual(result["decision"], "DENY")
        self.assertEqual(result["records"], [])
        self.assertEqual(result["inputTokens"], 0)
        self.assertEqual(result["stopReason"], "policy_denied")
        self.assertIn("No parameter names or values", result["answer"])

    def test_codex_key_status_is_masked_and_model_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            retained = Path(directory)
            (retained / "credential.json").write_text("{}", encoding="utf-8")
            (retained / "metadata.json").write_text(json.dumps({
                "model": "openai.gpt-5.6-luna", "keyFingerprint": "abcdef123456",
            }), encoding="utf-8")
            controller = CodexKeyController(retained)

            status = controller.status()

        self.assertEqual(status["state"], "CREATED")
        self.assertEqual(status["model"], "openai.gpt-5.6-luna")
        self.assertEqual(status["masked"], "bedrock-abcdef123456********")

    def test_codex_key_rejects_non_openai_model_before_aws(self):
        with tempfile.TemporaryDirectory() as directory:
            controller = CodexKeyController(directory)
            with self.assertRaisesRegex(RuntimeError, "exact openai"):
                controller.start("amazon.nova-lite-v1:0")

    def test_reveal_endpoint_requires_allowed_origin_and_disables_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            credential = Path(directory) / "credential.json"
            credential.write_text(json.dumps({
                "ServiceSpecificCredential": {"ServiceApiKeyValue": "bedrock-secret-demo"},
            }), encoding="utf-8")
            credential.chmod(0o600)
            Issue9Handler.controller = ProofController(Path(directory) / "evidence", credential)
            server = ThreadingHTTPServer(("127.0.0.1", 0), Issue9Handler)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            url = f"http://127.0.0.1:{server.server_port}/key/reveal"
            try:
                request = urllib.request.Request(
                    url, method="POST", headers={"Origin": "http://127.0.0.1:5174"}
                )
                with urllib.request.urlopen(request) as response:
                    body = json.loads(response.read())
                    self.assertEqual(response.headers["Cache-Control"], "no-store")
                    self.assertEqual(body["key"], "bedrock-secret-demo")
                with self.assertRaises(urllib.error.HTTPError) as rejected:
                    urllib.request.urlopen(urllib.request.Request(url, method="POST"))
                self.assertEqual(rejected.exception.code, 403)
            finally:
                server.shutdown()
                server.server_close()
                worker.join()

    def test_reveal_reads_only_mode_600_retained_key(self):
        with tempfile.TemporaryDirectory() as directory:
            credential = Path(directory) / "credential.json"
            credential.write_text(json.dumps({
                "ServiceSpecificCredential": {"ServiceApiKeyValue": "bedrock-secret-demo"},
            }), encoding="utf-8")
            credential.chmod(0o600)
            controller = ProofController(Path(directory) / "evidence", credential)

            revealed = controller.reveal_key()

        self.assertEqual(revealed, {"key": "bedrock-secret-demo", "expiresInSeconds": 15})

    def test_reveal_rejects_unsafe_file_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            credential = Path(directory) / "credential.json"
            credential.write_text("{}", encoding="utf-8")
            credential.chmod(0o644)
            controller = ProofController(Path(directory) / "evidence", credential)

            with self.assertRaisesRegex(RuntimeError, "mode 600"):
                controller.reveal_key()

    def test_completed_status_is_sanitized(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory)
            private = evidence / "private"
            private.mkdir()
            (evidence / "key-metadata.json").write_text(json.dumps({
                "keyType": "long-term", "credentialAgeDays": 1,
                "keyFingerprint": "123456789abc",
            }), encoding="utf-8")
            (evidence / "allow.json").write_text(json.dumps({
                "result": "ALLOW", "model": "allowed", "httpStatus": 200,
                "requestId": "allow-request", "inputTokens": 7, "outputTokens": 6,
            }), encoding="utf-8")
            (evidence / "deny.json").write_text(json.dumps({
                "result": "DENY", "model": "denied", "httpStatus": 403,
                "requestId": "deny-request", "enforcedBy": "AWS IAM",
            }), encoding="utf-8")
            (evidence / "cleanup.json").write_text(json.dumps({
                "credentialDeleted": False, "userDeleted": False, "cleanupFailed": False,
                "intentionallyRetained": True,
            }), encoding="utf-8")
            (evidence / "cloudtrail.json").write_text(json.dumps([{
                "eventName": "Converse", "requestId": "allow-request",
                "actorName": "must-not-leak", "actorType": "IAMUser",
            }]), encoding="utf-8")
            (evidence / "result.json").write_text(json.dumps({
                "status": "PASS", "cloudTrail": {"successEvents": 1, "deniedEvents": 1},
            }), encoding="utf-8")
            (private / "allowed-response.json").write_text(json.dumps({
                "output": {"message": {"content": [{"text": "governed access works"}]}},
            }), encoding="utf-8")

            status = build_public_status(evidence, process_running=False, return_code=0)
            encoded = json.dumps(status)

        self.assertEqual(status["state"], "PASS")
        self.assertEqual(status["auditState"], "VERIFIED")
        self.assertEqual(status["key"]["masked"], "bedrock-123456789abc********")
        self.assertEqual(status["allowed"]["response"], "governed access works")
        self.assertTrue(status["steps"]["cleanupVerified"])
        self.assertNotIn("allow-request", encoded)
        self.assertNotIn("must-not-leak", encoded)

    def test_running_status_reports_current_phase(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory)
            (evidence / "key-metadata.json").write_text(json.dumps({
                "keyType": "long-term", "credentialAgeDays": 1,
                "keyFingerprint": "abcdef123456",
            }), encoding="utf-8")
            status = build_public_status(evidence, process_running=True)

        self.assertEqual(status["state"], "RUNNING")
        self.assertEqual(status["phase"], "Invoking approved model")

    def test_core_proof_passes_while_cloudtrail_is_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory)
            (evidence / "key-metadata.json").write_text(json.dumps({
                "keyType": "long-term", "credentialAgeDays": 30,
                "keyFingerprint": "abcdef123456",
            }), encoding="utf-8")
            (evidence / "allow.json").write_text(json.dumps({
                "result": "ALLOW", "model": "allowed", "httpStatus": 200,
            }), encoding="utf-8")
            (evidence / "deny.json").write_text(json.dumps({
                "result": "DENY", "model": "denied", "httpStatus": 403,
            }), encoding="utf-8")
            (evidence / "cleanup.json").write_text(json.dumps({
                "credentialDeleted": False, "userDeleted": False, "cleanupFailed": False,
                "intentionallyRetained": True,
            }), encoding="utf-8")

            status = build_public_status(evidence, process_running=True)

        self.assertEqual(status["state"], "PASS")
        self.assertEqual(status["phase"], "Core proof complete; CloudTrail pending")
        self.assertEqual(status["auditState"], "PENDING")
        self.assertFalse(status["steps"]["cloudTrailCaptured"])


if __name__ == "__main__":
    unittest.main()
