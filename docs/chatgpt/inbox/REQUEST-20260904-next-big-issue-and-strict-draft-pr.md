# ChatGPT decision request: choose the next big AgentCore milestone

## Action requested

Review the current `main` branch and choose exactly one next substantial
milestone for this repository. Then create:

1. one GitHub Issue; and
2. one linked STRICT Draft PR.

Do not create competing Issues or PRs. Do not merge or mark the Draft PR
ready. Codex will implement only after the Issue and strict contract are
reviewed and approved.

## Current merged baseline

The following work is complete on `main`:

- bounded AgentCore POC and deterministic repository checks;
- native Bedrock API-key governance proof;
- LibreChat deployment with selected model providers;
- Issue #24 / PR #25 governance POC:
  - synthetic read-only MCP check is ALLOW;
  - synthetic remediation is native ASK;
  - native Reject causes no MCP call or state change;
  - native Approve/Submit causes exactly one harmless local effect;
  - delete policy resolves to DENY and `delete_calls=0`;
  - GovTechAI GPT-5.6 Luna function-call and tool-result protocol passed;
  - no real AWS or infrastructure mutation occurred.

Read these first:

1. `README.md`
2. `docs/TEST_PROOF.md`
3. `docs/ISSUE24_GOVERNANCE_PROOF.md`
4. `docs/LIBRECHAT_END_USER_GUIDE.md`
5. `docs/HARNESS_MVP_PLAN.md`
6. Issue #24 and merged PR #25.

## Important accepted boundaries

- The native Bedrock Nova 2 Lite tool-call probe is blocked because the
  existing EC2 role lacks `bedrock:InvokeModel` permission for the inference
  profile. Do not claim Nova tool calling is proven.
- Luna safely refused the DELETE request before emitting a tool call. The
  native policy still resolves the concrete delete key to DENY; do not add a
  mechanism that forces a model to issue a destructive tool call merely for a
  screenshot.
- The current governance MCP tools are synthetic and local. They must not be
  extended into real EC2, Inspector, SSM, ticketing, production data, or AWS
  mutation as part of the next milestone without a separately reviewed
  authorization model.
- The existing LibreChat EC2 host is a protected demo service, not a general
  Docker/Java/Nextflow builder. Do not redesign it or use its protected
  configuration as the next milestone.

## Candidate directions to assess

### A. Real, disposable AgentCore Harness learning MVP

Issue #8 and `docs/HARNESS_MVP_PLAN.md` define the deferred design:
one Harness, one entitlement-proven model, one synthetic read-only capability,
one invocation/trace/configuration proof, and verified cleanup. This is the
preferred direction if it remains supported by the current AWS account and
provides a clear learning outcome beyond the existing LibreChat POC.

### B. One tool-capable provider integration hardening

Use one provider/model to prove one live LibreChat MCP flow beyond the current
Luna adapter, but only if this can be completed without broadening the policy
engine, storing credentials, or changing the current demo host's
authorization model. Nova entitlement/IAM gaps must be treated as a preflight
gate, not as an invitation to add broad permissions.

### C. A better option

You may recommend a different direction only when it is more valuable,
demonstrable in five minutes, and materially advances the internal AI platform
without introducing a new product, deployment platform, or broad cloud scope.

## Selection rules

Choose one direction using this order:

1. clear user-visible learning or product value;
2. one problem, one happy path, one command, one proof, one result;
3. meaningful reuse of the merged POC rather than another UI polish pass;
4. no new production, office, or customer-data dependency;
5. a small, reversible cost and security envelope.

The expected default code budget is at most three product files and 200 net
new non-generated lines. Explain any justified variance before implementation.

## Required Issue and STRICT Draft PR content

The Issue must state:

- problem and intended demo outcome;
- one acceptance path and measurable proof;
- in-scope and explicitly excluded work;
- AWS account/region/entitlement preflight, if AWS is involved;
- lifecycle, cost, cleanup, and rollback boundary;
- security/credential boundary;
- no-go gates and the exact condition that stops implementation.

The STRICT Draft PR must contain a compact authoritative execution contract:

- target branch and base branch;
- exact files expected to change;
- implementation sequence;
- tests and live-validation boundary;
- evidence artifacts;
- explicit statement of what remains unproven;
- no merge/no Ready instruction until actual diff and proof are reviewed.

## Response requested

In the Issue and Draft PR, include a brief comparison of A, B, and C, then
name the one selected milestone and why it wins. Do not implement code or make
AWS changes while deciding.
