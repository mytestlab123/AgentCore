# STRICT implementation contract — Issue #26

Issue:
https://github.com/mytestlab123/AgentCore/issues/26

Decision request:
https://github.com/mytestlab123/AgentCore/blob/main/docs/chatgpt/inbox/REQUEST-20260904-next-big-issue-and-strict-draft-pr.md

## Status

**PLANNING ONLY.**

This file authorizes no AWS mutation and contains no implementation.
Codex must not start implementation until Amit/ChatGPT explicitly lifts the hold in the linked Draft PR.

## Selected milestone

**AgentCore Harness inline tool-use + native observability proof.**

This extends the already-merged PR #18 Harness lifecycle. It must not repeat or replace that implementation.

Target learning path:

```text
one command
-> exact AWS/model/SDK/observability preflight
-> one disposable Harness
-> one exact inline function: check_demo_health
-> Harness emits tool_use
-> deterministic client validates tool + args
-> client returns one synthetic read-only result
-> Harness resumes with toolResult
-> final HEALTHY result
-> native observability evidence
-> delete Harness + role
-> independently verify cleanup
```

## A / B / C decision

| Direction | Assessment | Decision |
| --- | --- | --- |
| A. Harness learning | PR #18 proved lifecycle but no tools and no navigable trace; this closes the highest-value missing AgentCore learning gap | **SELECTED** |
| B. Provider hardening | PR #25 already proves Luna function/tool protocol and LibreChat native approval; Nova remains role-blocked on the protected demo host | Defer |
| C. Other platform feature | Adds breadth before the Harness tool/observability boundary is understood | Defer |

## Git boundary

Base branch:

```text
main
```

Base commit used to create this branch:

```text
0ad3ce258cb9ccd3038f150be58a7f3e90fca6a2
```

Implementation branch:

```text
feature/issue-26-harness-inline-tool-trace
```

Codex must work only on this branch and the linked Draft PR.
Do not create a replacement Issue, branch, or PR.

## Exact expected file scope

Product files — maximum three:

1. `scripts/harness-mvp.sh`
   - add one explicit `--approve-tool-run` path;
   - reuse existing identity, create, lifecycle, cleanup, and fail-closed gates;
   - do not weaken the existing `--approve-run` path.

2. `scripts/harness-inline-tool.py`
   - minimal client-side helper for the Harness inline-function pause/resume contract;
   - accept only `check_demo_health`;
   - validate bounded arguments;
   - return only the fixed synthetic read-only result;
   - no shell, subprocess, AWS mutation, network service, arbitrary dispatch, or model-controlled function name.

3. `scripts/test-harness-mvp.sh`
   - retain existing checks;
   - add offline contract tests for the new mode/tool allowlist/helper fail-closed behavior;
   - tests must make no AWS calls.

Documentation/evidence file — not a product file:

4. `docs/TEST_PROOF.md`
   - append sanitized PASS/BLOCKED evidence only after actual validation;
   - state exactly what is and is not proven.

Do not edit LibreChat/GovTechAI integration files, frontend files, CDK stacks, API-key scripts, or unrelated documentation in this milestone.

Default code budget:

```text
<= 3 product files
<= 200 net new non-generated lines across product files
```

If implementation needs more, post BLOCKER before exceeding the budget.

## Frozen architecture

### Model

Use exactly one model:

```text
global.amazon.nova-2-lite-v1:0
```

Only after live preflight proves the exact current account/Region entitlement.
No automatic model fallback and no benchmark.

### Tool

Use exactly one Harness `inline_function`:

```text
check_demo_health
```

Conceptual schema:

```json
{
  "type": "object",
  "properties": {
    "service": {"type": "string", "enum": ["demo"]}
  },
  "required": ["service"],
  "additionalProperties": false
}
```

Fixed client result:

```json
{"service":"demo","status":"healthy"}
```

The function executes client-side and performs no AWS call.

### Tool authority

The Harness invocation must restrict `allowedTools` to the exact inline function.
Default `shell` and `file_operations` must not be available to this proof.

The model may request the tool; the client remains the execution/validation boundary.
Any unknown tool name, malformed arguments, additional fields, or unexpected tool-use shape must fail closed.

### Observability

Use native AgentCore observability already available in the approved test account.
Capture one sanitized trace/log reference sufficient to correlate:

```text
Harness invocation
-> model step
-> inline tool_use / resume
-> final result
```

Do not enable CloudWatch Transaction Search or another account-wide observability feature automatically.
If the required native observability proof is unavailable without enabling a new account-level feature, post BLOCKER and stop.

## Mandatory preflight — read-only first

Before creating a Harness:

1. confirm current branch is the named milestone branch;
2. confirm Issue #26 and this contract are current;
3. confirm no conflicting open implementation PR exists;
4. validate shell/Python syntax and installed CLI/SDK versions;
5. verify `AWS_PROFILE`, account, caller, and Region against explicit operator-provided gates;
6. verify exact Nova 2 Lite inference-profile entitlement;
7. verify current AgentCore SDK/API supports `inline_function`, `tool_use`, and matching `toolResult` resume;
8. verify existing native observability/trace access is usable without enabling a new account-wide setting;
9. verify the disposable execution-role policy is no broader than the existing Harness MVP role plus permissions already required for native observability;
10. verify the cleanup path before mutation.

No fallback to another account, Region, profile, provider, model, or tool architecture.

## Implementation sequence

After explicit HOLD LIFTED only:

1. Add the offline helper/contract tests first.
2. Extend `harness-mvp.sh --plan` to show the new fixed tool proof without AWS calls.
3. Add `--approve-tool-run` while preserving the existing lifecycle/cleanup trap.
4. Create the Harness with:
   - memory disabled;
   - one model;
   - one inline function;
   - exact `allowedTools` restriction;
   - bounded iterations/tokens/timeouts;
   - no shell/file tools.
5. Invoke with a fixed prompt that requires the synthetic health result.
6. Require first terminal reason `tool_use` and exact tool name.
7. Validate input locally.
8. Return the matching assistant `toolUse` + user `toolResult` pair required by the Harness API.
9. Resume the same session and require a normal final answer containing `HEALTHY`.
10. Capture sanitized native observability evidence.
11. Delete the Harness and temporary role.
12. Independently verify both are absent.
13. Run focused tests and `./scripts/check.sh`.
14. Update `docs/TEST_PROOF.md` with honest proof boundaries.
15. Post one concise implementation/evidence summary on the Draft PR.

## Tests

Required before final review:

```bash
/usr/bin/bash -n scripts/harness-mvp.sh
python3 -m py_compile scripts/harness-inline-tool.py
./scripts/test-harness-mvp.sh
./scripts/check.sh
git diff --check
```

Offline tests must prove at least:

- plan mode makes no AWS calls;
- missing identity gates fail before live work;
- exact tool name is allowlisted;
- unknown tool fails closed;
- malformed/additional arguments fail closed;
- fixed synthetic result is deterministic;
- default shell/file tools are excluded by configuration;
- existing bare Harness MVP regression remains intact.

## Live validation boundary

One approved live run only unless a failure has a clearly fixed local cause.
Do not repeatedly recreate resources to discover the same entitlement/IAM/observability blocker.

The live run may:

- create one Harness;
- create one temporary Harness execution role;
- make the minimum Nova 2 Lite model calls required by the two-turn tool cycle;
- read native AgentCore observability evidence;
- delete the Harness and role.

The live run may not:

- create Gateway/MCP/Lambda/API Gateway/network/database resources;
- enable account-wide observability settings;
- mutate LibreChat or its EC2 role;
- call EC2/Inspector/SSM;
- create persistent credentials;
- use office/customer/production data.

## Evidence contract

Private evidence root:

```text
/home/user/.AGENTS-temp/AgentCore/harness-tool-mvp/<timestamp>/
```

Private evidence must remain mode 700/600 and must not be committed.

Expected private artifacts:

```text
RESULT.json
TOOL_CALL.json
TOOL_RESULT.json
OBSERVABILITY.json
CLEANUP.json
private/*
```

Public repository evidence in `docs/TEST_PROOF.md` may contain only:

- PASS/BLOCKED;
- profile alias, not account identity;
- Region;
- model ID;
- tool name;
- stop reasons;
- HEALTHY result marker;
- sanitized observability status/reference type;
- cleanup booleans;
- test command/results.

No account ID, ARN, runtime/harness identifier, credential, private URL, raw trace payload, or secret-bearing environment value may be committed.

## Cost and lifecycle boundary

Expected resources:

```text
1 disposable Harness
1 temporary execution role
0 tool-side AWS resources
```

Expected usage is one tiny two-turn inference proof and existing native observability.
No separate Harness fee is assumed; underlying model/AgentCore capability usage remains billable.
Target cost remains below USD 0.01 under the existing small-token assumptions.

Cleanup is mandatory even on failure after resource creation.
PASS is impossible unless independent cleanup verification succeeds.

## BLOCKER conditions

Post the standard BLOCKER in this Draft PR and stop if any of the following occurs:

- wrong or unclear AWS identity/Region;
- exact model is not entitled/invokable;
- inline-function tool-use/resume is unsupported by the installed/current SDK path;
- implementation requires Gateway, remote MCP, Lambda, another hosted service, a second provider, or a new UI;
- implementation requires shell/file tools or broad IAM;
- native observability proof requires enabling a new account-wide feature;
- tool arguments cannot be constrained deterministically;
- code budget would exceed the approved limit;
- secret/private identifiers would enter Git;
- cleanup is incomplete or cannot be independently verified;
- repository truth conflicts with this contract.

BLOCKER format:

```text
BLOCKER
Expected: <required behavior / architecture>
Actual: <repository/AWS reality>
Why blocked: <short evidence-based reason>
Options: 1. <smallest option>  2. <smallest option>
Architecture changed: NO
Alternative implementation started: NO
Decision required: ChatGPT / Amit
```

## Explicitly out of scope

- LibreChat changes;
- GovTechAI/GPT-5.6 Luna adapter changes;
- protected EC2 role/IAM changes;
- AgentCore Gateway;
- remote MCP;
- Browser / Code Interpreter;
- shell / file-operation tools;
- memory / RAG / skills;
- multi-agent;
- model/provider comparison;
- real AWS workload data;
- mutation/remediation tools;
- persistent deployment;
- new frontend;
- production architecture.

## What remains unproven even after PASS

A successful milestone will **not** prove:

- AgentCore Gateway or remote MCP authorization;
- production RBAC/SSO or multi-user approval;
- real EC2/Inspector/SSM access;
- write/remediation authority;
- model quality or provider comparison;
- performance, scale, HA, or cost benchmark;
- production-ready observability retention/alerting;
- that the protected LibreChat Nova role is fixed.

## Review / merge gate

Codex must not:

- mark this PR Ready;
- merge it;
- close Issue #26;
- create another implementation PR;
- silently substitute architecture.

When implementation is complete, Codex posts one concise summary with:

- changed files;
- exact path used;
- test results;
- live PASS/BLOCKED evidence;
- tool-use/resume proof;
- native observability proof boundary;
- cleanup verification;
- confirmation that no prohibited scope was added.

Then stop.

ChatGPT must review the **actual final diff and evidence** against Issue #26 and this contract.
Only after PASS may Amit/ChatGPT mark Ready and squash-merge.
