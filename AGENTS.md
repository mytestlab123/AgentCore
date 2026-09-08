# AgentCore Repository Guidance

## Goal

Build a small, understandable internal AI platform POC following `ROADMAP.md`.
Follow KISS and optimize for a 3-5 minute demo.

The active implementation milestone is Issue #46: replace the synthetic
read-only security finding with one real AWS security/compliance signal while
reusing the merged M1-M7 platform and demo path.

## Scope

- Keep local simulation usable without AWS.
- Reuse the existing Project/Home, Playground, Logs, LibreChat, Gateway, Harness
  and validation paths before adding another framework.
- Reuse the merged M1-M7 governed workflow and final demo rather than rebuilding
  approval, Gateway Policy, audit, developer-client, or controlled-action plumbing.
- Issue #46 should choose exactly one already-available read-only AWS security
  source and show a small sanitized result through the existing LibreChat path.
- Keep the controlled remediation harmless/local for this milestone; do not turn
  this into a real remediation engine yet.
- Do not create, update, or delete AWS resources unless Amit separately
  approves the exact mutation.
- Cognito, hosting, many projects/providers, billing, RAG, Kubernetes, complex
  routing, broad observability, and generic AWS-assistant behavior remain out of
  scope unless a later roadmap milestone explicitly requires them.
- Never commit credentials, account IDs, tokens, private endpoints, or real API
  keys.

## AWS test context

- For AgentCore/Bedrock testing, use the `amit` AWS profile by default. This is
  the known tested profile with the required Bedrock and AgentCore access.
- The `dev` profile may be used when a task specifically needs that development
  context.
- Do not use a `prod` AWS profile/account/environment for this POC or for routine
  testing at this stage.
- Historical or synthetic test values named `prod` may remain as deny-test input;
  they do not authorize or select an AWS production profile/account/environment.
- Do not switch to another AWS profile merely because a command is blocked.
  Record the blocker or ask Amit if a different context is genuinely required.
- Bounded AWS changes that are part of an approved POC milestone are acceptable;
  keep them narrow, intentional, and recorded.
- Before any AWS test, confirm the active identity/profile and Region. Do not
  print or commit sensitive identity values as evidence.

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
