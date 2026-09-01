import json
import os
import stat
import tempfile
import unittest
from unittest.mock import patch

import agentcore_openai_adapter as adapter


class AdapterTests(unittest.TestCase):
    def test_latest_user_text_is_selected(self):
        payload = {
            "messages": [
                {"role": "user", "content": "old"},
                {"role": "assistant", "content": "answer"},
                {"role": "user", "content": "new"},
            ]
        }
        self.assertEqual(adapter._user_prompt(payload), "new")

    def test_invocation_uses_fixed_agentcore_cli_command(self):
        with tempfile.NamedTemporaryFile() as cli:
            os.chmod(cli.name, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            completed = type("Completed", (), {"returncode": 0, "stdout": json.dumps({"type": "contentBlockDelta", "delta": {"text": "ok"}}), "stderr": ""})()
            with patch.object(adapter, "HARNESS_ARN", "arn:aws:bedrock-agentcore:region:account:harness/test"), patch.object(adapter, "AGENTCORE_CLI", cli.name), patch("subprocess.run", return_value=completed) as run:
                self.assertEqual(adapter.invoke_harness("hello"), "ok")
            command = run.call_args.args[0]
            self.assertIn("invoke", command)
            self.assertIn("--harness-arn", command)
            self.assertNotIn("bedrock-runtime", " ".join(command))

    def test_empty_harness_output_fails_closed(self):
        with tempfile.NamedTemporaryFile() as cli:
            os.chmod(cli.name, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            completed = type("Completed", (), {"returncode": 0, "stdout": "{}\n", "stderr": ""})()
            with patch.object(adapter, "HARNESS_ARN", "arn:example"), patch.object(adapter, "AGENTCORE_CLI", cli.name), patch("subprocess.run", return_value=completed):
                with self.assertRaisesRegex(RuntimeError, "no text"):
                    adapter.invoke_harness("hello")


if __name__ == "__main__":
    unittest.main()
