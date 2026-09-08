#!/usr/bin/env python3
"""Focused offline regression tests for the bounded Harness inline tool contract."""

import unittest

import harness_inline_tool as harness


class HarnessInlineToolTests(unittest.TestCase):
    def test_fixed_tool_use_resumes_with_fixed_result(self):
        tool_use = harness.parse_tool_use(harness.fixture_events())
        messages = harness.resume_messages(tool_use)
        self.assertEqual(tool_use, {"toolUseId": "demo-tool-1", "name": "check_demo_health"})
        self.assertEqual(messages[1]["content"][0]["toolResult"]["status"], "success")
        self.assertEqual(harness.trace_summary(tool_use)["aws_calls"], "0")

    def test_any_other_tool_or_input_is_rejected(self):
        wrong_tool = harness.fixture_events()
        wrong_tool[0]["contentBlockStart"]["start"]["toolUse"]["name"] = "shell"
        with self.assertRaises(harness.ToolProtocolError):
            harness.parse_tool_use(wrong_tool)
        wrong_input = harness.fixture_events()
        wrong_input[1]["contentBlockDelta"]["delta"]["toolUse"]["input"] = '{"service":"prod"}'
        with self.assertRaises(harness.ToolProtocolError):
            harness.parse_tool_use(wrong_input)

    def test_harness_config_exposes_only_the_fixed_tool(self):
        config = harness.harness_tool_config()
        self.assertEqual(config["allowedTools"], [harness.TOOL_NAME])
        self.assertEqual([tool["name"] for tool in config["tools"]], [harness.TOOL_NAME])
        self.assertEqual(config["tools"][0]["type"], "inline_function")
        self.assertEqual(config["tools"][0]["config"]["inlineFunction"]["inputSchema"]["type"], "object")
        self.assertEqual(config["maxIterations"], 2)


if __name__ == "__main__":
    unittest.main()
