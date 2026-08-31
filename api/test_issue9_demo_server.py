import json
import tempfile
import unittest
from pathlib import Path

from issue9_demo_server import build_public_status


class Issue9DemoStatusTests(unittest.TestCase):
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
