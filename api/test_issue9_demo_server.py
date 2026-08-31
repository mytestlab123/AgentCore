import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from issue9_demo_server import Issue9Handler, ProofController, build_public_status


class Issue9DemoStatusTests(unittest.TestCase):
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
