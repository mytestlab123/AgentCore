# AgentCore Repository Guidance

## Goal

Build GitHub Issue #4 as a small, understandable internal AI platform POC.
Follow KISS and optimize for a 3-5 minute demo.

## Scope

- Keep local simulation usable without AWS.
- Use only Project/Home, Playground, and Logs views.
- Use one project, one platform key, one allowed Bedrock model, and one denied
  catalogue model.
- AgentCore Runtime, Cognito, hosting, multiple projects/providers, billing,
  RAG, Kubernetes, complex routing, and broad observability are out of scope.
- Never deploy or mutate AWS without explicit approval for the exact resources.
- Never commit credentials, account IDs, tokens, private endpoints, or real API
  keys.

## Local Operations

- Before starting, stopping, or configuring a listener, read
  `/home/user/.codex/port.md` completely and follow it.
- Bind development services to loopback by default.
- Never stop another repo's listener to reclaim a preferred port.

## Validation

- Use `./scripts/check.sh` for deterministic local checks.
- Use `./scripts/browser-e2e.sh` for the bounded browser proof.
- After a browser run, create or update `docs/TEST_PROOF.md` with the command,
  result, evidence paths, and an honest browser-versus-backend proof boundary.
- Keep tests focused on distinct POC behavior and honest mock/live labels.
- Browser screenshots are supporting evidence, not proof of AWS or backend state.
