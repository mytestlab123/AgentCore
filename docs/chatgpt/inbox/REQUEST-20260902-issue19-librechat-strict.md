# STRICT EXECUTION CONTRACT — Issue #19 LibreChat UI over AgentCore

Status: IMPLEMENTATION HANDOFF — V2
Owner of architecture/acceptance: ChatGPT
Implementation worker: Codex
GitHub Issue: #19
Draft PR: #20
Target branch: `feature/issue-19-librechat-agentcore`

## 0. Authority and instruction order

For this milestone, use this order:

1. current collaboration protocol: ChatGPT creates/owns the Issue + Draft PR contract;
2. Issue #19: product decision, scope, architecture and acceptance intent;
3. this file: exact implementation contract;
4. current repository truth and existing code conventions.

If two instructions materially conflict, **do not choose the easier interpretation**. Stop that implementation path and report the conflict/blocker in PR #20.

Codex must not create another issue, branch, or PR for this milestone unless ChatGPT explicitly requests it.

Codex must not edit the architectural contract in this file to make an implementation fit. If the contract must change, report the blocker first and wait for ChatGPT/human review.

---

## 1. Objective — one golden path only

Build the smallest working POC proving:

```text
LibreChat
  -> thin OpenAI-compatible protocol adapter
  -> Amazon Bedrock AgentCore InvokeHarness
  -> AgentCore Harness
  -> Nova 2 Lite
  -> response visible in LibreChat
```

Success requires **one real public-safe prompt** through that exact path.

No tool call is required.

No enterprise platform work is required.

---

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
  | AgentCore InvokeHarness
  v
Amazon Bedrock AgentCore Harness
  |
  v
Nova 2 Lite
```

Roles:

- **LibreChat**: UI/conversation shell only.
- **Adapter**: request/response protocol translation only.
- **AgentCore Harness**: managed agent/runtime execution authority.
- **Nova 2 Lite**: model for this MVP.
- **AWS IAM**: final AWS authorization boundary.

### Important clarification: Python/Node is allowed only as an adapter

The implementation language is not the architecture.

A tiny Python or Node service is acceptable **only** if it performs protocol translation and AgentCore Harness invocation.

It MUST NOT:

- become an LLM backend;
- call Bedrock Runtime directly for the chat path;
- implement the agent/model loop;
- select alternate providers;
- add tools/orchestration/policy logic.

This distinction exists specifically to prevent the type of drift where a required managed runtime is silently replaced by a custom Python LLM implementation.

---

## 3. Technical integration basis

The intended compatibility boundary is deliberately narrow:

### LibreChat side

Use a LibreChat **custom OpenAI-compatible endpoint** configured in `librechat.yaml`.

For the MVP:

- expose only one endpoint/model label such as `AgentCore / Nova 2 Lite`;
- prefer an explicit model list with model fetching disabled if practical;
- do not expose extra providers/models merely because LibreChat supports them;
- do not place AWS credentials in LibreChat configuration;
- streaming is optional for the first proof.

Current LibreChat custom-endpoint documentation:

- https://www.librechat.ai/docs/quick_start/custom_endpoints
- https://www.librechat.ai/docs/configuration/librechat_yaml/object_structure/custom_endpoint

### Adapter side

Expose only the minimum OpenAI-compatible chat-completions surface LibreChat needs.

The adapter must translate that request into the official AgentCore Harness invocation path.

It does not need to emulate the full OpenAI API.

If `models.fetch: false` avoids a `/models` implementation, prefer that smaller shape.

### AgentCore side

The backend operation must be AgentCore **`InvokeHarness`** / the official AgentCore-supported Harness invocation path.

Reference:

- https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/API_InvokeHarness.html

Do not reinterpret “AgentCore-backed” as “call Bedrock Runtime directly.”

---

## 4. Existing proof to reuse — PR #18

Issue #17 / merged PR #18 already proved:

```text
preflight
  -> create temporary execution role
  -> create Harness
  -> READY
  -> invoke Nova 2 Lite
  -> verify answer
  -> delete Harness
  -> delete role
  -> independently verify cleanup
```

Review before coding:

- Issue #19;
- Draft PR #20;
- merged PR #18;
- `docs/HARNESS_MVP_GUIDE.md`;
- `scripts/harness-mvp.sh`;
- repository `AGENTS.md`;
- existing check/test conventions.

Do not duplicate the entire Harness lifecycle if reuse is possible.

### Explicitly authorized lifecycle variation

Interactive LibreChat needs the Harness to remain available briefly. That is **not** an architecture deviation for this milestone.

The approved temporary demo lifecycle is:

```text
preflight
  -> create temporary Harness/role using proven pattern
  -> wait for READY
  -> start adapter + LibreChat
  -> ONE real LibreChat prompt
  -> capture sanitized proof
  -> stop local services
  -> delete Harness/role
  -> verify cleanup
```

Do not turn this into a persistent service or always-on AWS deployment.

---

## 5. MUST requirements

1. Use LibreChat as the reusable UI.
2. Use one fixed AgentCore-backed custom endpoint/model label.
3. Use AgentCore Harness for the actual managed execution path.
4. Use AgentCore `InvokeHarness` / official Harness invocation path from the adapter.
5. Reuse the proven Harness pattern from #17 / PR #18 where practical.
6. Use Nova 2 Lite unless ChatGPT explicitly approves a documented substitution.
7. Keep the adapter protocol-only.
8. One LibreChat prompt must result in one real Harness-backed Nova 2 Lite response rendered in LibreChat.
9. Keep AWS credentials/identifiers out of LibreChat and Git.
10. Use server-side/local AWS credential-chain/profile access only where the adapter/Harness lifecycle requires it.
11. Failure must be explicit and must not silently fall back to another provider/model.
12. Add focused local/offline tests for request/response translation where practical.
13. Add an anti-drift check over new runtime code.
14. Add sanitized proof and exact run/cleanup steps.
15. Delete disposable AWS resources and independently verify cleanup.

---

## 6. MUST NOT requirements

The implementation MUST NOT:

- call Bedrock Runtime `Converse`, `ConverseStream`, `InvokeModel`, or `InvokeModelWithResponseStream` directly for the LibreChat chat path;
- create a custom Python/Node LLM or agent loop;
- replace Harness with Strands, LangChain, custom orchestration, or another framework;
- introduce LiteLLM;
- add AgentCore Gateway or MCP;
- add EC2, Inspector, SSM, remediation, or AWS mutation workflows;
- add RAG/vector DB;
- add AgentCore/LibreChat memory work;
- add browser/code interpreter;
- add multi-agent behavior;
- give LibreChat AWS credentials;
- silently switch provider/model;
- expose a broad model catalog;
- fork LibreChat unless a documented blocker proves configuration/adapter integration impossible;
- build production SSO, multi-tenancy, billing, chargeback, EKS, or enterprise deployment;
- redesign the existing AgentCore platform;
- create a second implementation PR for the same milestone.

---

## 7. Exact MVP demo

The complete proof should remain approximately:

```text
1. Preflight identity/config.
2. Create temporary Harness/role using PR #18 pattern.
3. Wait for Harness READY.
4. Start minimal adapter locally.
5. Start LibreChat locally.
6. LibreChat shows one endpoint: AgentCore / Nova 2 Lite.
7. Send one public-safe prompt.
8. Adapter translates the request and invokes AgentCore Harness.
9. Harness/Nova 2 Lite returns the answer.
10. LibreChat renders the answer.
11. Capture sanitized evidence.
12. Stop local services.
13. Delete Harness/role.
14. Independently verify cleanup.
```

Suggested prompt:

> Explain in five bullets what Amazon Bedrock AgentCore Harness manages for an AI agent.

A correct non-streaming response is sufficient. Do not spend the milestone implementing streaming unless it is trivial and does not broaden scope.

---

## 8. Expected implementation shape

Prefer fewer files and configuration over new framework code.

Approximate shape only:

```text
integration/librechat/
  librechat.yaml.example       # one custom endpoint, no secrets
  README.md                    # exact local run steps

adapter/ or integration/librechat/adapter/
  minimal handler/server       # chat-completions translation only
  focused tests

scripts/
  small demo lifecycle helper  # only if it genuinely reduces operator error

docs/
  ISSUE19_LIBRECHAT_PROOF.md   # sanitized end-to-end evidence
```

Do not add layers merely to match this example.

---

## 9. Required anti-drift validation

Before implementation is considered complete, inspect all new runtime/adapter code and prove that the LibreChat execution path does not directly invoke Bedrock models.

Prohibited runtime concepts for the LibreChat path include equivalents of:

```text
bedrock-runtime
converse
converse_stream
invoke_model
invoke_model_with_response_stream
custom LLM loop
provider fallback
```

These words may appear in this contract, documentation, or tests that assert prohibition. They must not represent the actual chat execution path.

Expected positive boundary:

```text
LibreChat request
  -> adapter
  -> InvokeHarness
```

Also test one negative case:

```text
Harness unavailable / invocation fails
  -> adapter returns explicit error
  -> LibreChat shows failure
  -> NO direct Bedrock/provider fallback
```

---

## 10. Evidence required

Add sanitized public-safe proof showing enough evidence to conclude, without inference:

1. LibreChat sent the test prompt to the configured custom endpoint.
2. The adapter received the request.
3. The backend operation used AgentCore Harness invocation.
4. The Harness used the intended Nova 2 Lite configuration.
5. The real model response returned to LibreChat.
6. The negative no-fallback test behaved correctly.
7. Disposable Harness/IAM resources were absent after cleanup.

Do not commit:

- account IDs;
- ARNs;
- credentials/tokens;
- private endpoints;
- raw AWS service responses containing identifiers;
- sensitive local paths beyond already-established public-safe conventions.

Private/raw evidence may remain outside Git following the PR #18 evidence pattern.

---

## 11. Blocker / architecture-deviation protocol

If any MUST requirement appears impossible or materially wrong, Codex must **stop that implementation path before coding an alternative** and add this to PR #20:

```text
BLOCKER

Expected contract:
<required architecture/technology>

Repository/AWS reality:
<what was actually discovered>

Why the contract cannot currently be met:
<short evidence-based explanation>

Smallest options:
1. <option>
2. <option>

Architecture changed: NO
Alternative implementation started: NO
Decision required: ChatGPT / human
```

A workaround is not permission to change architecture.

No new branch or replacement PR should be created for the blocker.

---

## 12. PR execution rules for Codex

Codex must:

1. read Issue #19, PR #20 and this contract before editing code;
2. inspect repository truth;
3. push only to `feature/issue-19-librechat-agentcore`;
4. continue the existing Draft PR #20;
5. keep the diff bounded to the one golden path;
6. run focused validation and repository checks;
7. add sanitized implementation/proof notes to the existing PR/branch;
8. report blockers rather than substituting architecture.

Codex must **not**:

- rewrite the Issue scope;
- weaken this contract;
- create another Issue/branch/PR for this milestone;
- mark PR #20 ready for review;
- merge PR #20;
- close Issue #19.

**ChatGPT/human review is the gate that changes the PR from Draft/implementation to ready/mergeable work.**

---

## 13. Acceptance checklist

- [ ] LibreChat runs separately as the UI/service.
- [ ] Exactly one focused AgentCore-backed custom endpoint/model is configured for the proof.
- [ ] One real prompt travels from LibreChat to the thin adapter.
- [ ] Adapter is protocol-only.
- [ ] Adapter invokes AgentCore Harness, not Bedrock Runtime directly.
- [ ] Harness invokes Nova 2 Lite, or a substitution was explicitly approved before implementation.
- [ ] The real response renders in LibreChat.
- [ ] Streaming was not made a blocker.
- [ ] No custom agent/model orchestration loop was added.
- [ ] No LiteLLM/Gateway/MCP/tool/RAG/memory/enterprise scope was introduced.
- [ ] LibreChat contains no AWS credentials.
- [ ] No secrets/private AWS identifiers are committed.
- [ ] Harness failure produces an explicit error with no provider/model fallback.
- [ ] Focused tests/checks pass.
- [ ] Sanitized proof demonstrates the exact path.
- [ ] Disposable AWS resources are cleaned up and absence is verified.
- [ ] PR remains Draft pending ChatGPT/human architecture review.

---

## 14. Definition of done

A reviewer can inspect the final diff plus proof and conclude, without inference:

> LibreChat is the user experience only. A thin compatibility adapter translates LibreChat's OpenAI-compatible chat request into Amazon Bedrock AgentCore `InvokeHarness`. AgentCore Harness remains the managed runtime/agent authority, Nova 2 Lite provides the model response, AWS IAM remains the authorization boundary, and no alternate model path is silently used.

Anything materially broader requires a new ChatGPT-created Issue + Draft PR milestone.