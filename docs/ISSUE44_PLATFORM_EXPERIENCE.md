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

### M6 — compact audit story

Reuse existing evidence and logging. Present one small sequence for a governed
request:

`request -> tool -> human decision -> Gateway decision -> backend effect/blocked -> final result`

Do not build a new observability platform.

### M7 — five-minute Security Copilot demo

Use the existing `web-01` flow:

1. read-only security check proceeds automatically with sanitized AWS read evidence;
2. controlled remediation pauses at native LibreChat approval;
3. allowed approval reaches Gateway ALLOW and exactly one harmless effect;
4. reject or the existing denied case produces no additional effect;
5. show the compact audit/evidence sequence.

## Validation

Use focused tests while iterating, then `./scripts/check.sh`, `git diff --check`,
one thin final browser proof, and one bounded developer-client proof for Codex and
Kiro. Prefer evidence economy over another framework or large test matrix.

Bounded, intentional lab/AWS changes directly required for this milestone are
acceptable when narrow and recorded. If a native AWS developer surface is
blocked, record the limitation and continue the usable MVP rather than redesigning
it.
