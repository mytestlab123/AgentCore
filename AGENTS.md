# AgentCore Repository Guidance

## Goal

Build a small, understandable internal AI platform POC following `ROADMAP.md`.
Follow KISS and optimize for a 3-5 minute demo.

The active implementation milestone is Issue #40: combine roadmap M1-M4 into
one governed agent workflow MVP.

## Scope

- Keep local simulation usable without AWS.
- Reuse the existing Project/Home, Playground, Logs, LibreChat, Gateway, Harness
  and validation paths before adding another framework.
- Issue #40 may add one bounded Harness tool-use/resume flow, one real read-only
  AWS lookup, and one harmless demo-owned controlled action behind approval and
  Gateway Policy.
- The real AWS capability for Issue #40 is read-only. Do not create, update, or
  delete AWS resources unless Amit separately approves the exact mutation.
- Cognito, hosting, many projects/providers, billing, RAG, Kubernetes, complex
  routing, broad observability, and generic AWS-assistant behavior remain out of
  scope unless a later roadmap milestone explicitly requires them.
- Never commit credentials, account IDs, tokens, private endpoints, or real API
  keys.

## Local Operations

- The home Linux host is a trusted single-user lab. Do not add local auth,
  proxy, tunnel, network-policy, browser-security, or identity layers unless a
  concrete problem requires them.
- Before starting, stopping, or configuring a listener, read
  `/home/user/.codex/port.md` completely and follow it.
- Bind development services to loopback by default.
- In Amit-facing instructions and handoffs, write local service URLs as
  `http://localhost:<actual-port>/`; reserve the literal `127.0.0.1` form for
  listener binding, internal assertions, and troubleshooting evidence.
- Never stop another repo's listener to reclaim a preferred port.

## Validation

- Use focused tests for changed behavior and `./scripts/check.sh` for the normal
  deterministic check.
- Run one final `./scripts/browser-e2e.sh` proof when the milestone makes a
  browser-visible claim.
- Update `docs/TEST_PROOF.md` only with material live/browser evidence and an
  honest browser-versus-backend proof boundary.
- Prefer proportional proof over new test frameworks or exhaustive matrices.
