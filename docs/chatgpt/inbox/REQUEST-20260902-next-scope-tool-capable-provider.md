# ChatGPT decision request: next step after live Nova tool-call failure

## Observed live test

The operator created `AgentCore Governance Demo`, attached the
`agentcore_governance` MCP server with three tools, selected:

```text
agentcore-nova-2-lite
```

and sent:

```text
Check the security finding for web-01.
```

The first ten lines of the saved response in `/tmp/pp2` were a generic guide
about how to use vulnerability scanners. The response did not return the
synthetic `web-01` finding, did not invoke an MCP tool, and did not show a
native approval/policy event.

## Current repository truth

The AgentCore, Codex Subscription, and GovTechAI entries all route through the
same custom OpenAI-compatible adapter. In
`api/agentcore_openai_adapter.py`:

- `_user_prompt(payload)` extracts only the latest user text;
- `invoke_harness`, `invoke_codex`, and `invoke_platform` receive only that
  text;
- no `tools` or `tool_calls` fields are handled or returned;
- each route returns a final assistant text response.

Therefore changing from Codex Luna to AgentCore Nova changes the model route
but does not add tool-calling support.

## PR #25 status

PR #25 remains the native LibreChat governance configuration milestone. It
proves the YAML policy, MCP declarations, trusted hook, and deterministic
offline tool behavior. A live GUI ALLOW/ASK/Reject/Approve/DENY run is not
proven with the current text-only adapters. A blocker has been posted on PR
#25; do not add a custom policy engine or approval UI there.

## ChatGPT questions

1. Recommend the smallest next issue for a real live tool proof:
   - configure one native LibreChat provider/model that supports tool calling;
   - or add OpenAI-compatible tool-call translation to the existing adapter.
2. State the exact provider/model and request/response contract to validate.
3. Keep the solution KISS: one read-only tool, one model, one approval proof.
4. Explain any new credentials, service, cost, or AWS entitlement needed.

## Constraints

- Do not modify PR #25's governance policy or create a parallel policy engine.
- Do not call AWS or change infrastructure while deciding the next scope.
- Do not read or publish the full `/tmp/pp2` response.
- Do not claim that the current Nova response is grounded or tool-backed.
- A new Issue/PR is required if provider/integration architecture changes.

