#!/usr/bin/env python3
"""Offline protocol helper for the retained AgentCore Harness tool-use demo.

The Harness service emits a tool-use event.  The caller validates that event,
executes this one fixed inline function, and submits the corresponding
tool-result in a follow-up invocation.  This file performs no AWS call and
does not create a Harness; it keeps the resume contract testable before a
separately authorized live Harness run.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Iterable


TOOL_NAME = "check_demo_health"
TOOL_INPUT = {"service": "demo"}
TOOL_RESULT = {"service": "demo", "status": "healthy"}


class ToolProtocolError(ValueError):
    """The model event is not the one bounded tool protocol this demo accepts."""


def tool_definition() -> dict[str, Any]:
    return {
        "type": "inline_function",
        "name": TOOL_NAME,
        "config": {
            "inlineFunction": {
                "description": "Return the fixed health state of the demo service.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"service": {"type": "string", "enum": ["demo"]}},
                    "required": ["service"],
                    "additionalProperties": False,
                },
            },
        },
    }


def harness_tool_config() -> dict[str, Any]:
    """The minimal config fragment for a future explicitly-approved run."""
    return {"tools": [tool_definition()], "allowedTools": [TOOL_NAME], "maxIterations": 2}


def parse_tool_use(events: Iterable[dict[str, Any]]) -> dict[str, str]:
    tool_id: str | None = None
    name: str | None = None
    fragments: list[str] = []
    stopped_for_tool = False
    for event in events:
        start = event.get("contentBlockStart", {}).get("start", event.get("start", {})).get("toolUse")
        if start is not None:
            if tool_id is not None:
                raise ToolProtocolError("multiple tool calls are not allowed")
            tool_id = start.get("toolUseId")
            name = start.get("name")
        delta = event.get("contentBlockDelta", {}).get("delta", event.get("delta", {})).get("toolUse")
        if delta is not None:
            fragments.append(delta.get("input", ""))
        if (event.get("type") == "messageStop" or "messageStop" in event) and event.get("stopReason", event.get("messageStop", {}).get("stopReason")) == "tool_use":
            stopped_for_tool = True
    if not isinstance(tool_id, str) or not tool_id or name != TOOL_NAME or not stopped_for_tool:
        raise ToolProtocolError("expected exactly one check_demo_health tool-use stop")
    try:
        received_input = json.loads("".join(fragments))
    except (TypeError, json.JSONDecodeError) as exc:
        raise ToolProtocolError("tool input was not valid JSON") from exc
    if received_input != TOOL_INPUT:
        raise ToolProtocolError("tool input is outside the fixed demo contract")
    return {"toolUseId": tool_id, "name": TOOL_NAME}


def resume_messages(tool_use: dict[str, str]) -> list[dict[str, Any]]:
    if tool_use.get("name") != TOOL_NAME or not tool_use.get("toolUseId"):
        raise ToolProtocolError("cannot resume an unrecognized tool")
    return [
        {"role": "assistant", "content": [{"toolUse": {
            "toolUseId": tool_use["toolUseId"], "name": TOOL_NAME, "input": TOOL_INPUT,
        }}]},
        {"role": "user", "content": [{"toolResult": {
            "toolUseId": tool_use["toolUseId"],
            "content": [{"text": json.dumps(TOOL_RESULT, separators=(",", ":"))}],
            "status": "success",
        }}]},
    ]


def trace_summary(tool_use: dict[str, str]) -> dict[str, str]:
    """Safe, useful trace labels; deliberately excludes sessions and request IDs."""
    return {
        "tool_use": tool_use["name"],
        "tool_result": TOOL_RESULT["status"],
        "resume": "ready",
        "aws_calls": "0",
    }


def fixture_events() -> list[dict[str, Any]]:
    return [
        {"contentBlockStart": {"start": {"toolUse": {"toolUseId": "demo-tool-1", "name": TOOL_NAME}}}},
        {"contentBlockDelta": {"delta": {"toolUse": {"input": '{"service":"demo"}'}}}},
        {"messageStop": {"stopReason": "tool_use"}},
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="validate the fixed offline event fixture")
    parser.add_argument("--events", help="JSON Lines Harness event trace to turn into safe resume messages")
    args = parser.parse_args()
    if args.self_test == bool(args.events):
        parser.error("select exactly one of --self-test or --events")
    events = fixture_events() if args.self_test else [
        json.loads(line) for line in open(args.events, encoding="utf-8") if line.strip()
    ]
    tool_use = parse_tool_use(events)
    result = {"trace": trace_summary(tool_use), "resume_messages": resume_messages(tool_use)}
    print(json.dumps(result, separators=(",", ":")))
    if args.self_test:
        print("HARNESS_INLINE_TOOL_OFFLINE_PASS")
        print("AWS_CALLS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
