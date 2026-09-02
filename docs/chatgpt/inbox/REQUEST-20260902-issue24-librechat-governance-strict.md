# STRICT EXECUTION CONTRACT — Issue #24 LibreChat Security Copilot governance

Status: IMPLEMENTATION HANDOFF — HUMAN-APPROVED SCOPE EXPANSION
Owner of architecture/acceptance: ChatGPT + Amit
Implementation worker: Codex
GitHub Issue: #24
Draft PR: #25
Target branch: `feature/issue-24-librechat-governance`

## 0. Human decision supersedes the earlier stop boundary

Keep this work in **PR #25**. Do not create another Issue/branch/PR for the live tool proof.

The earlier blocker correctly proved that the existing custom routes are text-only and drop `tools` / `tool_calls`. Amit explicitly chose to enlarge this PR so it ends with enough successful live evidence rather than stopping at offline configuration proof.

Small directly-related fixes required to complete the live provider validation belong in this PR.

## 1. Milestone objective

Complete one cohesive Security Copilot governance POC with:

```text
OFFLINE GOVERNANCE
CHECK / read-only       -> ALLOW
REMEDIATE / controlled  -> ASK -> Approve or Reject
DELETE / prohibited     -> DENY
HIGH-RISK CONTEXT       -> trusted hook tightens policy

LIVE PROVIDER PROOF
A. Amazon Nova 2 Lite   -> real tool/MCP call through LibreChat native Bedrock path
B. GPT-5.6 Luna         -> real tool/MCP call through a genuinely tool-capable Luna path
```

The POC must finish with at least one real **LibreChat visible approval flow** working end to end. Prefer proving the full governance flow on both providers when credentials/provider support already exist.

No real remediation or cloud-resource mutation is allowed.

## 2. Repository blocker already proven

`api/agentcore_openai_adapter.py` currently:

- extracts only the latest user text;
- sends only text to AgentCore/Codex/GovTechAI;
- does not preserve `tools` or `tool_calls`;
- returns only final assistant text.

Changing the model name on those routes does not make them tool-capable.

Do not claim the existing text-only routes are MCP/tool proof.

## 3. Provider Track A — Nova 2 Lite via native Bedrock

### Required architecture

```text
LibreChat Agent
   -> native `bedrock` provider
   -> Amazon Nova 2 Lite
   -> LibreChat converts selected MCP tools to model tool definitions
   -> model selects tool
   -> LibreChat executes `agentcore_governance` MCP tool
   -> native LibreChat approval policy controls ASK/DENY
```

Use the already-proven model family/region where available. Preferred model:

`global.amazon.nova-2-lite-v1:0`

If LibreChat requires a regional/cross-region model ID instead, use the smallest equivalent Nova 2 Lite identifier that is actually available and record it.

### Authentication

Prefer existing approved AWS authentication already present on the host:

1. `BEDROCK_AWS_PROFILE` / AWS SDK provider chain; or
2. an already-existing Bedrock bearer token/API key.

Do not create/rotate a new AWS credential merely for this test.
Do not commit credentials.

### Nova proof

At minimum prove live:

```text
Prompt: Check the security finding for web-01.
Expected: Nova selects `check_security_finding`; deterministic synthetic finding returns.
```

If that works, run the full governance flow with Nova:

- ALLOW check;
- ASK -> Reject;
- ASK -> Approve;
- DENY delete;
- context DENY / context ASK.

## 4. Provider Track B — GPT-5.6 Luna

GPT-5.6 Luna is known to support tools/MCP. This milestone must prove that capability with the same synthetic governance tool surface rather than assuming it.

Use this preference order.

### B1 — existing GovTechAI Luna capability probe first

The repository already has a protected GovTechAI configuration and `gpt-5.6-luna` route.

Before changing adapter code, make one **sanitized provider capability probe** against the existing Responses-style provider using one harmless synthetic function/tool definition.

Do not log the API key or raw sensitive headers.

If the provider returns a real tool/function call, implement the **smallest protocol translation** needed in the existing adapter so LibreChat `tools` / tool results are preserved for the Luna route.

The adapter may translate protocol only. It must not become a second agent, policy engine, or tool executor.

Required translation boundary if B1 is viable:

```text
LibreChat tools + messages
   -> minimal Chat-Completions/Responses translation
   -> gpt-5.6-luna
   -> tool/function call
   -> LibreChat executes MCP tool under native approval policy
   -> tool result returned to Luna
   -> final assistant response
```

### B2 — official OpenAI API only if already available

If B1 is not tool-capable, and an already-approved `OPENAI_API_KEY` is available, configure LibreChat's native OpenAI provider with:

`gpt-5.6-luna`

and run the same live tool/approval proof.

Do not create a new OpenAI API account, key, or billing commitment automatically.

### B3 — existing Codex subscription as independent model/MCP proof

If neither B1 nor B2 can provide a LibreChat-backed Luna path without new credentials, use the already-authenticated Codex CLI/App Server environment to prove **GPT-5.6 Luna can discover and invoke the same MCP tool**.

This B3 proof validates Luna + MCP/model capability, but it does **not** count as LibreChat approval proof. Record that distinction explicitly.

Do not rewrite LibreChat to imitate Codex approval UX.

## 5. Required governance tools — exactly three

### `check_security_finding` — ALLOW
- read-only synthetic lookup;
- deterministic public-safe result for `web-01`;
- no side effect.

### `apply_demo_remediation` — ASK
- native LibreChat Approve / Reject interaction;
- Reject: zero effect;
- Approve: exactly one harmless disposable local effect;
- easy reset.

### `delete_demo_asset` — DENY
- blocked before tool implementation executes;
- invocation count remains zero.

## 6. Context-aware tightening

Keep the existing trusted hook policy:

```text
remediation(environment=dev)
  -> ASK

remediation(environment=prod, ticket="")
  -> DENY

remediation(environment=prod, ticket="DEMO-123")
  -> ASK -> Approve / Reject
```

The hook may only tighten policy. It must never bypass ASK or become an authorization engine.

## 7. MUST

1. Keep LibreChat as the operator-facing governance UI.
2. Keep exactly the three logical demo tools.
3. Preserve native `toolApproval` ALLOW / ASK / DENY and trusted hook behavior.
4. Preserve all existing offline governance tests.
5. Run a real Nova 2 Lite tool/MCP validation through native Bedrock if current AWS access permits it.
6. Run a real GPT-5.6 Luna tool/MCP validation using B1, B2, or B3 above.
7. At least one provider must produce a real visible LibreChat MCP/tool call; a text-only answer is not success.
8. At least one provider must prove the live LibreChat ASK interaction with Reject and Approve.
9. Prefer full ALLOW/ASK/DENY/context live proof for both providers when practical with existing credentials.
10. Keep model/provider calls minimal and low-cost.
11. Keep evidence sanitized and state exactly which provider/path produced it.
12. Run repository validation after implementation.

## 8. MUST NOT

Do not add:

- real EC2/SSM/Inspector/IAM/WAF remediation or mutation;
- creation/rotation of new AWS credentials;
- automatic creation of a new OpenAI API account/key/billing setup;
- credentials committed to Git;
- custom React approval buttons;
- a second policy/approval engine;
- User A requests / User B approves workflow;
- production RBAC/SSO;
- ServiceNow/ticketing;
- RAG/vector DB;
- LiteLLM;
- Kubernetes/EKS;
- a large LibreChat fork;
- replacement Issue/branch/PR.

## 9. Adapter-change rule

A small protocol translation change is allowed in PR #25 **only for Track B1** if the live GovTechAI Luna capability probe proves the upstream provider can return tool/function calls.

Allowed:
- preserve `tools` from LibreChat;
- translate supported tool schemas to the provider request;
- translate provider tool calls back to the OpenAI-compatible shape LibreChat expects;
- preserve tool-result follow-up messages;
- add focused tests.

Not allowed:
- tool execution inside the adapter;
- policy decisions inside the adapter;
- model-side fake tool responses;
- replacing LibreChat MCP/approval with custom orchestration.

If the provider itself rejects tool definitions, do not build fake adapter behavior around it.

## 10. Acceptance matrix

Record PASS / BLOCKED with evidence for each row:

| Path | Tool call | LibreChat ALLOW | ASK Reject | ASK Approve | DENY | Context | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nova 2 Lite / native Bedrock | | | | | | | |
| GPT-5.6 Luna / B1 or B2 | | | | | | | |
| GPT-5.6 Luna / B3 subscription | model/MCP proof only | N/A | N/A | N/A | N/A | N/A | |

Success minimum:

```text
existing offline governance = PASS
Nova tool-capability validation = PASS or evidence-backed provider/access BLOCKED
Luna tool-capability validation = PASS
at least one real LibreChat tool call = PASS
at least one full live ASK Reject + Approve flow = PASS
```

The preferred result is both Nova and Luna passing the live LibreChat matrix.

## 11. Evidence

Update `docs/ISSUE24_GOVERNANCE_PROOF.md` with:

- provider/model actually selected;
- exact sanitized prompt;
- tool selected;
- approval event observed;
- tool invocation counter/state before and after;
- final synthetic result;
- which credentials path was used by category only (profile, bearer token, protected API key), never secret values;
- cost-impact note (model inference only; no infrastructure mutation);
- any provider limitation/blocker.

Do not publish raw private responses or secrets.

## 12. Codex working protocol

Codex must:

1. read Issue #24, PR #25, this contract, and the latest blocker/follow-up comments;
2. work only on `feature/issue-24-librechat-governance`;
3. continue Draft PR #25 only;
4. keep directly-related provider/tool fixes in this PR;
5. prefer native LibreChat provider/tool behavior;
6. test provider capability before adding translation code;
7. run repeatable tests and repository validation;
8. post one updated implementation-summary comment with the acceptance matrix.

Codex must not:
- create another Issue/branch/PR;
- mark PR #25 Ready;
- merge PR #25;
- close Issue #24.

## 13. Definition of done

A reviewer can conclude, from live and offline evidence:

> LibreChat can govern synthetic Security Copilot tools with ALLOW / ASK / DENY and context-aware tightening; at least one real tool-capable model completes the visible approval flow; Nova 2 Lite and GPT-5.6 Luna have both been actually validated rather than assumed; and no real remediation or infrastructure mutation occurred.
