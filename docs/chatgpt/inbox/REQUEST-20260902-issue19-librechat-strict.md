# STRICT EXECUTION CONTRACT — Issue #19 LibreChat UI over AgentCore

Status: IMPLEMENTATION HANDOFF
Owner of architecture/acceptance: ChatGPT
Implementation worker: Codex
GitHub Issue: #19
Target branch: `feature/issue-19-librechat-agentcore`

## 0. Instruction priority

This file is the implementation contract for Issue #19.

Codex must implement this contract as written. If repository reality makes any MUST requirement impossible, stop implementation for that part and document the blocker in the existing PR. Do not silently substitute another architecture.

Do not create another issue, another implementation branch, or another PR for this milestone unless ChatGPT explicitly requests it.

## 1. Objective

Build the smallest working POC proving:

```text
LibreChat
  -> thin compatibility adapter
  -> Amazon Bedrock AgentCore Harness
  -> Nova 2 Lite
  -> response visible in LibreChat
```

LibreChat is only the UI/conversation shell.

AgentCore Harness remains the managed agent/runtime authority.

AWS IAM remains the authorization boundary.

## 2. Architecture invariant — MUST NOT DRIFT

Approved architecture:

```text
User
  |
  v
LibreChat
  |
  | OpenAI-compatible chat request
  v
Thin protocol adapter
  |
  | InvokeHarness / official AgentCore-supported invocation path
  v
Amazon Bedrock AgentCore Harness
  |
  v
Nova 2 Lite
```

The compatibility adapter exists only because LibreChat and AgentCore Harness expose different interfaces.

The adapter MUST NOT become an agent, orchestration framework, model router, policy engine, or alternate backend.

## 3. MUST requirements

1. Use LibreChat as the reusable chat UI.
2. Use Amazon Bedrock AgentCore Harness for the actual managed agent/model execution path.
3. Reuse the proven Harness knowledge/pattern from Issue #17 / PR #18 rather than replacing it.
4. Use Nova 2 Lite for the MVP unless a current AWS/account limitation makes this impossible; any substitution must be explicitly documented in the PR before implementation proceeds.
5. Keep the adapter minimal: translate LibreChat/OpenAI-compatible request and response semantics to/from the official AgentCore Harness invocation path.
6. One user prompt from LibreChat must result in one real AgentCore Harness-backed response rendered in LibreChat.
7. Preserve server-side/AWS authorization. UI model selection must never grant model permission.
8. Keep credentials and AWS identifiers out of Git.
9. Add deterministic local/offline validation where practical for adapter request/response mapping.
10. Document exact run steps and exact proof collected.

## 4. MUST NOT requirements

The implementation MUST NOT:

- call Bedrock Runtime `Converse`, `ConverseStream`, `InvokeModel`, or `InvokeModelWithResponseStream` directly for the LibreChat chat path;
- create a custom Python or Node agent loop;
- replace AgentCore Harness with Strands, LangChain, custom orchestration, or another framework;
- introduce LiteLLM for this MVP;
- add AgentCore Gateway, MCP tools, EC2, Inspector, SSM, remediation, RAG, memory, browser, code interpreter, multi-agent logic, or autonomous AWS writes;
- give LibreChat broad AWS credentials;
- fork LibreChat unless a small, documented blocker proves configuration/adapter integration is impossible;
- redesign the existing AgentCore platform/UI architecture;
- build production SSO, multi-tenancy, billing, chargeback, EKS, or enterprise deployment;
- silently fall back to a different provider/model when AgentCore invocation fails.

## 5. Explicit anti-drift check

Before declaring implementation complete, inspect all newly added adapter/runtime code.

The new LibreChat integration must not contain a direct model invocation path using concepts/functions equivalent to:

```text
bedrock-runtime
converse
converse_stream
invoke_model
invoke_model_with_response_stream
custom LLM loop
```

Those strings may appear in documentation explaining prohibited paths, tests, or comments, but not as the execution path for the LibreChat POC.

The expected backend execution boundary is AgentCore Harness invocation.

## 6. MVP scope — intentionally tiny

The complete demo should be approximately:

```text
1. Start LibreChat locally.
2. Start the minimal adapter locally.
3. Configure one LibreChat endpoint: "AgentCore / Nova 2 Lite".
4. Send one simple public-safe prompt.
5. Adapter invokes the existing/proven AgentCore Harness path.
6. Response is returned to LibreChat and rendered normally.
7. Capture sanitized proof.
8. Cleanup any disposable AgentCore resources if this implementation creates them.
```

Suggested prompt:

> Explain in five bullets what Amazon Bedrock AgentCore Harness manages for an AI agent.

No tool call is required in this milestone.

## 7. Prefer reuse over invention

Review before coding:

- Issue #19
- merged PR #18
- `docs/HARNESS_MVP_GUIDE.md`
- `scripts/harness-mvp.sh`
- repository `AGENTS.md`
- existing project check/test conventions

Do not duplicate the complete Harness lifecycle implementation if a smaller reusable integration boundary is possible.

If persistent Harness availability is required for interactive LibreChat use, document that as a deliberate deviation from PR #18's disposable lifecycle and implement only the smallest safe lifecycle needed for this POC.

## 8. Expected implementation shape

Exact filenames may change based on repository truth, but the implementation should remain approximately this small:

```text
librechat/ or integration/librechat/
  librechat.yaml.example       # endpoint configuration, no secrets
  README.md                    # local run instructions

adapter/
  minimal server/handler       # protocol translation only
  focused tests                # request/response mapping

scripts/
  one start/demo helper        # only if useful

docs/
  ISSUE19_LIBRECHAT_PROOF.md   # sanitized evidence and final result
```

Do not add layers merely to match this example structure. Fewer files are preferable if clear.

## 9. PR execution rules for Codex

Codex must continue the existing Draft PR created for this issue.

During implementation:

1. Read this contract before editing code.
2. Inspect repository truth before deciding filenames.
3. Keep changes bounded to Issue #19.
4. Push commits only to `feature/issue-19-librechat-agentcore`.
5. Update the existing Draft PR description/checklist as evidence becomes available.
6. Do not mark the PR ready for review until all MUST and MUST-NOT checks have been verified.
7. Do not merge the PR.
8. Do not close Issue #19 merely because a response appeared in the UI.
9. If architecture must change, stop and request ChatGPT review in the PR instead of improvising.

## 10. Acceptance criteria

The PR is implementation-complete only when all are true:

- [ ] LibreChat runs as a separate UI/service.
- [ ] A single configured LibreChat endpoint represents the AgentCore-backed path.
- [ ] One real prompt travels from LibreChat to the thin adapter.
- [ ] The adapter invokes AgentCore Harness, not Bedrock Runtime directly.
- [ ] AgentCore Harness invokes Nova 2 Lite (or an explicitly reviewed substitute).
- [ ] The real response is rendered in LibreChat.
- [ ] No custom agent/model orchestration loop was added.
- [ ] No LiteLLM/Gateway/MCP/tooling/RAG/memory scope was introduced.
- [ ] No AWS credentials or private identifiers are committed.
- [ ] Failure does not silently fall back to another model/provider.
- [ ] Focused tests/checks pass.
- [ ] Sanitized proof documents the exact tested path.
- [ ] Disposable resources are cleaned up or their deliberate retention is explicitly documented.

## 11. Definition of done

A reviewer can inspect code plus proof and conclude, without inference:

> LibreChat is only the user experience. The implementation crosses a thin compatibility boundary into Amazon Bedrock AgentCore Harness. AgentCore remains the runtime/agent authority, Nova 2 Lite is the model, and AWS IAM remains the authorization boundary.

Anything materially broader is outside Issue #19 and requires a new ChatGPT-approved milestone.
