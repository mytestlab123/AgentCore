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
            self.assertIn("--max-tokens", command)
            self.assertIn("6000", command)
            self.assertNotIn("bedrock-runtime", " ".join(command))

    def test_empty_harness_output_fails_closed(self):
        with tempfile.NamedTemporaryFile() as cli:
            os.chmod(cli.name, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            completed = type("Completed", (), {"returncode": 0, "stdout": "{}\n", "stderr": ""})()
            with patch.object(adapter, "HARNESS_ARN", "arn:example"), patch.object(adapter, "AGENTCORE_CLI", cli.name), patch("subprocess.run", return_value=completed):
                with self.assertRaisesRegex(RuntimeError, "no text"):
                    adapter.invoke_harness("hello")

    def test_stream_events_use_openai_chunk_shape(self):
        events = adapter._stream_events("chatcmpl-test", "hello")
        self.assertEqual(events[0]["object"], "chat.completion.chunk")
        self.assertEqual(events[0]["choices"][0]["delta"]["content"], "hello")
        self.assertEqual(events[1]["choices"][0]["finish_reason"], "stop")

    def test_platform_requires_user_provided_key(self):
        with self.assertRaisesRegex(adapter.ProviderAuthError, "protected config is not available"):
            adapter.invoke_platform("hello", "gpt-5.6-luna", None)

    def test_platform_response_translation(self):
        response_body = {
            "output": [{"content": [{"type": "output_text", "text": "ok"}]}]
        }

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps(response_body).encode("utf-8")

        with patch.object(adapter.urllib.request, "urlopen", return_value=Response()) as opened:
            self.assertEqual(
                adapter.invoke_platform("hello", "gpt-5.6-luna", "Bearer demo-key"),
                "ok",
            )
        request = opened.call_args.args[0]
        self.assertIn("/platform/models/v1/responses", request.full_url)
        self.assertEqual(request.get_header("X-api-key"), "demo-key")

    def test_platform_uses_protected_config_when_placeholder_is_supplied(self):
        response_body = {"output": [{"content": [{"type": "output_text", "text": "ok"}]}]}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps(response_body).encode("utf-8")

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as config:
            config.write('PLATFORM_API_KEY="protected-key"\n')
            config.write('PLATFORM_API_BASE_URL="https://example.invalid"\n')
            config.write('PLATFORM_AI_MODEL="gpt-5.6-luna"\n')
            config_path = config.name
        os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
        try:
            with patch.object(adapter, "PLATFORM_CONFIG", config_path), patch.object(adapter.urllib.request, "urlopen", return_value=Response()) as opened:
                self.assertEqual(adapter.invoke_platform("hello", "gpt-5.6-luna", "Bearer local-poc-placeholder"), "ok")
            request = opened.call_args.args[0]
            self.assertEqual(request.get_header("X-api-key"), "protected-key")
            self.assertTrue(request.full_url.startswith("https://example.invalid/"))
        finally:
            os.unlink(config_path)

    def test_codex_subscription_invocation_is_read_only_and_parses_message(self):
        with tempfile.TemporaryDirectory() as home:
            auth_path = os.path.join(home, "auth.json")
            open(auth_path, "w", encoding="utf-8").close()
            completed = type(
                "Completed",
                (),
                {
                    "returncode": 0,
                    "stdout": json.dumps({
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": "ok"},
                    }),
                    "stderr": "",
                },
            )()
            with patch.object(adapter, "CODEX_CLI", "/opt/codex"), patch.object(adapter, "CODEX_HOME", home), patch("os.path.isfile", side_effect=lambda path: path in {"/opt/codex", auth_path}), patch("os.access", return_value=True), patch("subprocess.run", return_value=completed) as run:
                self.assertEqual(adapter.invoke_codex("hello"), "ok")
            command = run.call_args.args[0]
            self.assertIn("--sandbox", command)
            self.assertIn("read-only", command)
            self.assertIn("--ephemeral", command)
            self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)


if __name__ == "__main__":
    unittest.main()
