import json
import unittest
from unittest.mock import patch

import handler


class HandlerPolicyTests(unittest.TestCase):
    def test_denied_model_is_logged_without_bedrock_call(self):
        with patch.object(handler, "_validate_key", return_value=True), patch.object(
            handler, "_write_log"
        ) as write_log, patch.object(handler, "_invoke_model") as invoke_model:
            response = handler.handler({
                "httpMethod": "POST", "path": "/invoke", "headers": {},
                "body": json.dumps({"prompt": "test", "modelId": "model-premium"}),
            }, None)
        self.assertEqual(response["statusCode"], 403)
        self.assertEqual(json.loads(response["body"])["status"], "Denied")
        invoke_model.assert_not_called()
        write_log.assert_called_once()

    def test_allowed_model_returns_normalized_metadata(self):
        with patch.object(handler, "_validate_key", return_value=True), patch.object(
            handler, "_write_log"
        ), patch.object(handler, "_invoke_model", return_value=("Safe response", 321, 12, 34)):
            response = handler.handler({
                "httpMethod": "POST", "path": "/invoke", "headers": {},
                "body": json.dumps({"prompt": "test", "modelId": handler.ALLOWED_MODEL_ID}),
            }, None)
        body = json.loads(response["body"])
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body["status"], "Allowed")
        self.assertEqual(body["inputTokens"], 12)
        self.assertEqual(body["outputTokens"], 34)


if __name__ == "__main__":
    unittest.main()
