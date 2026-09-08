# Issue #44 — platform experience + final demo

This is the second roadmap delivery milestone and combines M5-M7.

## Chosen MVP stack

LibreChat + the existing thin AgentCore adapter + native ASK/Approve/Reject +
retained AgentCore Gateway Policy.

Do not add FAST, a new custom chat frontend, or RAG for this milestone.

## Workstreams

### M5 — developer clients

- keep the already-proven governed Codex path;
- use current Agent Toolkit for AWS guidance/tooling for Codex AWS work where practical;
- prove one equivalent bounded Kiro developer task;
- run one small Agent Inspector check against the retained Gateway using only the
  known denied synthetic input and record the result honestly.

Agent Inspector is a developer/debug surface, not the final user interface.

Current bounded Inspector result: **BLOCKED without an AWS call**. The retained
artifact is an IAM-protected MCP Gateway, while Agent Inspector is the local
web UI launched by `agentcore dev`; attaching it would require new local
agent/client and SigV4 scaffolding, which this milestone excludes. The concise
sanitized evidence is the [PR #45 Inspector
comment](https://github.com/mytestlab123/AgentCore/pull/45#issuecomment-5581509043).
The already-proven Codex Bedrock wrapper remains the governed developer-client
path; `scripts/codex-bedrock-smoke.sh --check` verifies its installed CLI and
read-only invocation contract without requesting a credential.

### M6 — compact audit story

Reuse existing evidence and logging. Present one small sequence for a governed
request:

`request -> tool -> human decision -> Gateway decision -> backend effect/blocked -> final result`

Do not build a new observability platform.

Implementation: each completed read-only or remediation MCP result renders this
safe six-part sequence and retains at most eight similarly sanitized local
events:

`request -> tool -> human decision -> Gateway decision -> backend -> final result`

A LibreChat **Reject** deliberately has no MCP event: the visible native
`Cancelled` card is the evidence that the server was not called. A `prod`
request with `DEMO-*` can be approved at the UI and still produces the separate
Gateway **DENY** result with no local effect.

### M7 — five-minute Security Copilot demo

Use the existing `web-01` flow:

1. read-only security check proceeds automatically with sanitized AWS read evidence;
2. controlled remediation pauses at native LibreChat approval;
3. allowed approval reaches Gateway ALLOW and exactly one harmless effect;
4. reject or the existing denied case produces no additional effect;
5. show the compact audit/evidence sequence.

The final operator script and exact expected results are in
`docs/LIBRECHAT_END_USER_GUIDE.md`. This preserves the native LibreChat UI: no
custom approval panel, dashboard, or replacement chat surface is added.

## Validation

Use focused tests while iterating, then `./scripts/check.sh`, `git diff --check`,
one thin final browser proof, and one bounded developer-client proof for Codex and
Kiro. Prefer evidence economy over another framework or large test matrix.

Bounded, intentional lab/AWS changes directly required for this milestone are
acceptable when narrow and recorded. If a native AWS developer surface is
blocked, record the limitation and continue the usable MVP rather than redesigning
it.
