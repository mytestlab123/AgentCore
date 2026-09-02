# STRICT EXECUTION CONTRACT — Issue #24 LibreChat Security Copilot governance

Status: IMPLEMENTATION HANDOFF
Owner of architecture/acceptance: ChatGPT
Implementation worker: Codex
GitHub Issue: #24
Target branch: `feature/issue-24-librechat-governance`

## 0. Instruction priority

This file is the implementation contract for Issue #24.

Codex must implement this contract as written. If current LibreChat behavior, repository reality, or tool integration makes a MUST requirement impossible, stop that implementation path and report the blocker in the existing Draft PR.

Do not silently substitute a custom approval system, another UI, another policy engine, or another PR.

## 1. Objective

Build the smallest local POC proving three Security Copilot governance outcomes in LibreChat:

```text
CHECK / read-only      -> ALLOW
REMEDIATE / controlled -> ASK -> Approve or Reject
DELETE / prohibited    -> DENY
```

This milestone tests governance UX only.

No real AWS mutation is required or allowed.

## 2. Frozen architecture

Preferred shape:

```text
User
  |
  v
LibreChat
  |
  | native tool/MCP approval policy if available
  |
  +--> ALLOW -> check_security_finding
  |
  +--> ASK   -> apply_demo_remediation
  |              |
  |              +--> Approve -> execute one harmless demo effect
  |              +--> Reject  -> no execution / no side effect
  |
  +--> DENY  -> delete_demo_asset never executes
  |
  v
Tiny local/demo tool backend
```

The backend should remain intentionally harmless and deterministic.

For this milestone, LibreChat is the policy/approval interaction layer. A future real Security Copilot would still require backend/AgentCore/IAM authorization; this POC must not imply that a GUI approval button grants AWS authority.

## 3. Required tools — exactly three

### A. `check_security_finding` — ALLOW

- Read-only.
- May read a committed synthetic fixture.
- Must execute without an approval prompt.
- Must return a deterministic public-safe result for `web-01`.

### B. `apply_demo_remediation` — ASK

- Must pause before execution.
- LibreChat must visibly offer the native approval/rejection interaction if supported.
- Reject path: zero side effect.
- Approve path: exactly one harmless disposable effect, e.g. a marker/state file outside the repository or an equally safe in-memory/local state change.
- The effect must be easy to reset.

### C. `delete_demo_asset` — DENY

- Must be blocked before tool implementation executes.
- Add a simple counter/marker/log assertion proving invocation count remains zero.
- Do not simulate success after policy denial.

## 4. Native-first rule

Prefer native LibreChat configuration and policy capabilities first:

- LibreChat YAML/configuration;
- native tool/MCP integration;
- native approval policy behavior;
- native approval UI.

Do not start by building custom React approval buttons or a custom Python/Node workflow engine.

If native LibreChat cannot provide one of the required behaviors, report:

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

## 5. MUST

1. Use LibreChat as the operator-facing UI.
2. Implement exactly the three logical tools above.
3. Demonstrate ALLOW without an approval prompt.
4. Demonstrate ASK with both Reject and Approve paths.
5. Prove Reject causes no side effect.
6. Prove Approve causes exactly one expected harmless effect.
7. Demonstrate DENY and prove the denied tool implementation never ran.
8. Prefer native LibreChat policy/configuration over custom approval code.
9. Keep all fixtures and evidence public-safe.
10. Add repeatable local/offline checks where practical.
11. Document exact local run steps and sanitized proof.
12. Keep the implementation small enough for a 3-minute demo.

## 6. MUST NOT

Do not add:

- real EC2, SSM, Inspector, IAM, WAF, or other AWS mutation;
- AWS credentials inside LibreChat;
- real remediation;
- AgentCore architecture replacement;
- SecCop implementation in this repository;
- separate approver queue;
- User A requests / User B approves workflow;
- production RBAC or SSO;
- ServiceNow/ticketing workflow;
- RAG/vector database;
- LiteLLM unless ChatGPT explicitly approves a documented blocker;
- Kubernetes/EKS;
- large LibreChat fork;
- a custom enterprise policy engine;
- replacement Issue/branch/PR.

## 7. Expected implementation shape

Keep it small. Exact paths may change after repository inspection, but a reasonable shape is:

```text
integration/librechat-governance/
  librechat.yaml.example       # ALLOW / ASK / DENY configuration
  README.md                    # local run + demo instructions
  demo-tools.*                 # three tiny synthetic tools only
  fixture.*                    # public-safe web-01 finding
  test/check script            # deterministic assertions if useful

docs/
  ISSUE24_GOVERNANCE_PROOF.md  # sanitized evidence
```

Fewer files are preferable if clear.

Do not add layers just to match this example.

## 8. Acceptance tests

At minimum prove:

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

## 9. Evidence

The final PR must include sanitized proof sufficient to show:

- ALLOW actually executed;
- ASK visibly paused;
- Reject did not execute;
- Approve did execute once;
- DENY did not execute;
- no AWS credentials/calls were required;
- no custom approval UI was introduced unless explicitly approved after a blocker.

Screenshots may be referenced locally if useful, but do not commit secrets/private data.

## 10. Codex working protocol

Codex must:

1. read Issue #24, this contract, and the Draft PR before coding;
2. inspect repository truth;
3. push only to `feature/issue-24-librechat-governance`;
4. continue the existing Draft PR only;
5. keep the implementation MVP-sized;
6. update the PR with validation/proof;
7. report blockers before architecture changes.

Codex must not:

- create a replacement PR;
- weaken this contract to fit an easier implementation;
- silently replace native LibreChat approval with a custom workflow;
- mark the PR ready;
- merge the PR;
- close Issue #24.

## 11. Explicit next milestone — not this PR

After this POC succeeds, a separate milestone may test role/context-aware governance:

```text
DEV read        -> ALLOW
PROD remediation -> ASK for authorized Ops role
unauthorized user -> DENY
```

A later milestone may then evaluate cross-user approval:

```text
Requester A -> submits
Approver B  -> independently approves/rejects
```

Do not implement either in Issue #24.

## 12. Definition of done

A reviewer can reproduce all four test paths and conclude:

> LibreChat can present a useful Security Copilot governance interaction: safe reads execute automatically, controlled actions require explicit human approval, rejected actions do not execute, and prohibited actions are blocked before execution.

Anything broader requires a new ChatGPT-approved milestone.