# STRICT EXECUTION CONTRACT — Issue #24 LibreChat Security Copilot governance

Status: IMPLEMENTATION HANDOFF
Owner of architecture/acceptance: ChatGPT
Implementation worker: Codex
GitHub Issue: #24
Target branch: `feature/issue-24-librechat-governance`

## 0. Instruction priority

This file is authoritative for PR #25.

Codex must implement this contract as written. If current LibreChat behavior or repository reality makes a MUST requirement impossible, stop that implementation path and report a BLOCKER in PR #25 before implementing an alternative.

Do not silently substitute a custom approval system, another UI, another policy engine, or another PR.

## 1. Milestone objective

Build one cohesive local POC proving four related governance behaviors:

```text
CHECK / read-only       -> ALLOW
REMEDIATE / controlled  -> ASK -> Approve or Reject
DELETE / prohibited     -> DENY
HIGH-RISK CONTEXT       -> trusted hook tightens policy
```

This PR is deliberately milestone-sized rather than a micro-PR. Small fixes and directly-related implementation findings should normally stay in PR #25.

No real AWS mutation is required or allowed.

## 2. Frozen architecture

```text
User
  |
  v
LibreChat
  |
  | native tool/MCP approval policy
  |
  +--> ALLOW -> check_security_finding
  |
  +--> ASK   -> apply_demo_remediation
  |              +--> Approve -> one harmless demo effect
  |              +--> Reject  -> no execution / no side effect
  |
  +--> DENY  -> delete_demo_asset never executes
  |
  +--> trusted approval hook -> may tighten ASK/DENY for high-risk context
  |
  v
Tiny local/demo MCP or tool backend
```

LibreChat is the operator-facing governance interaction layer. Future real Security Copilot actions must still be authorized by backend/AgentCore/IAM controls. A GUI approval button alone must never grant AWS authority.

## 3. Required tools — exactly three

### A. `check_security_finding` — ALLOW

- read-only synthetic lookup;
- no approval prompt;
- deterministic public-safe result for `web-01`.

### B. `apply_demo_remediation` — ASK

- pauses before execution;
- native Approve / Reject interaction if current LibreChat supports it;
- Reject: zero side effect;
- Approve: exactly one harmless disposable local effect;
- effect must be easy to reset.

### C. `delete_demo_asset` — DENY

- blocked before implementation executes;
- prove invocation count remains zero;
- do not simulate success after denial.

## 4. Required context-aware policy example

Use LibreChat's trusted tool-approval hook capability if supported by the current installed version.

Preferred synthetic policy:

```text
apply_demo_remediation(environment=dev)
  -> normal ASK

apply_demo_remediation(environment=prod, ticket="")
  -> hook tightens policy -> DENY

apply_demo_remediation(environment=prod, ticket="DEMO-123")
  -> hook permits normal ASK -> still requires Approve / Reject
```

The hook may only tighten policy. It must not become a custom authorization engine.

This test is context-aware policy only. It is not production RBAC and not User-A-request/User-B-approve workflow.

If native hooks cannot support the required behavior cleanly, report:

```text
BLOCKER

Expected behavior:
...

LibreChat/repository reality:
...

Native capability attempted:
...

Smallest options:
1. ...
2. ...

Custom approval code written: NO
Architecture changed: NO
Decision required: ChatGPT / human
```

## 5. Native-first rule

Prefer current native LibreChat capabilities:

- `toolApproval.enabled`;
- static `allow` / `ask` / `deny` rules;
- MCP tool patterns;
- native approval UI;
- native checkpoint/resume behavior;
- trusted approval hooks for context-aware tightening;
- YAML/configuration over custom frontend code.

Do not start by building custom React approval buttons or a custom Python/Node workflow engine.

## 6. MUST

1. Use LibreChat as the operator-facing UI.
2. Implement exactly the three logical tools above.
3. Demonstrate ALLOW without approval.
4. Demonstrate ASK with both Reject and Approve paths.
5. Prove Reject causes no side effect.
6. Prove Approve causes exactly one expected harmless effect.
7. Demonstrate DENY and prove the denied tool implementation never ran.
8. Demonstrate one context-aware tightening example with a native trusted hook if supported; otherwise report a BLOCKER before any alternative.
9. Keep all fixtures/evidence public-safe and synthetic.
10. Add repeatable local/offline checks where practical.
11. Document exact local run steps and sanitized proof.
12. Keep existing repository validation passing.
13. Keep the implementation understandable in a 3-5 minute demo.

## 7. MUST NOT

Do not add:

- real EC2, SSM, Inspector, IAM, WAF, or other AWS mutation;
- AWS credentials inside LibreChat;
- real remediation;
- replacement of AgentCore/SecCop architecture;
- separate approver queue;
- User A requests / User B approves workflow;
- production RBAC or SSO;
- ServiceNow/ticketing integration;
- RAG/vector database;
- LiteLLM unless ChatGPT explicitly approves a documented blocker;
- Kubernetes/EKS;
- large LibreChat fork;
- custom enterprise policy engine;
- replacement Issue/branch/PR.

## 8. Expected implementation shape

Exact paths may change after repository inspection. Prefer a compact shape such as:

```text
integration/librechat-governance/
  librechat.yaml.example
  README.md
  demo-tools.*
  approval-hook.*
  fixture.*
  test/check script

docs/
  ISSUE24_GOVERNANCE_PROOF.md
```

Fewer files are preferable when clear. Do not add layers merely to match this example.

## 9. Acceptance tests

### Test 1 — ALLOW

```text
Prompt: Check the security finding for web-01.
Expected: tool executes directly; no approval prompt; deterministic result returned.
```

### Test 2 — ASK / Reject

```text
Prompt: Apply the remediation for web-01.
Decision: Reject.
Expected: tool does not execute; demo state unchanged.
```

### Test 3 — ASK / Approve

```text
Prompt: Apply the remediation for web-01.
Decision: Approve.
Expected: tool executes once; exactly one expected harmless state change.
```

### Test 4 — DENY

```text
Prompt: Delete web-01.
Expected: blocked before execution; denied tool invocation count remains zero.
```

### Test 5 — context DENY

```text
Prompt/tool args: remediation for environment=prod without demo ticket.
Expected: trusted hook tightens policy to DENY; tool does not execute.
```

### Test 6 — context ASK

```text
Prompt/tool args: remediation for environment=prod with ticket=DEMO-123.
Expected: context hook does not bypass approval; normal ASK remains and user must Approve/Reject.
```

## 10. Evidence

Final PR must include sanitized proof showing:

- ALLOW executed;
- ASK visibly paused;
- Reject did not execute;
- Approve executed exactly once;
- DENY did not execute;
- context hook tightened high-risk request;
- context hook never bypassed ASK;
- no AWS credentials/calls were required;
- no custom approval UI was introduced unless explicitly approved after a BLOCKER.

## 11. Milestone sizing / PR reuse rule

During PR #25, keep directly-related work in this PR when it is required to complete, test, document, or safely operate the frozen governance milestone.

Do **not** create a new Issue/PR for every small fix.

Create a new Issue/PR only when work materially changes one of these boundaries:

1. architecture;
2. security/authorization model;
3. user workflow (for example second-user approval);
4. external system integration (real AWS, ServiceNow, etc.);
5. unrelated product capability.

When uncertain, report the proposed extension in PR #25 and let ChatGPT/human decide whether it remains in-scope.

## 12. Codex working protocol

Codex must:

1. read Issue #24, PR #25, and this contract before coding;
2. inspect current repository truth;
3. work only on `feature/issue-24-librechat-governance`;
4. continue existing Draft PR #25 only;
5. keep implementation coherent with the frozen milestone;
6. run repeatable tests and repository validation;
7. post sanitized proof and one implementation-summary comment;
8. report blockers before architecture changes.

Codex must not:

- create a replacement PR;
- weaken this contract to fit an easier implementation;
- silently replace native LibreChat approval with a custom workflow;
- mark PR #25 ready;
- merge PR #25;
- close Issue #24.

## 13. Definition of done

A reviewer can reproduce all required paths and conclude:

> LibreChat can present a useful Security Copilot governance interaction: safe reads execute automatically, controlled actions require explicit human approval, rejected actions do not execute, prohibited actions are blocked before execution, and higher-risk context can tighten policy without bypassing approval.

Real AWS mutation, cross-user approval, production RBAC/SSO, or a different architecture requires a later milestone.