# Issue #46 — Real AWS security signal

Purpose: make the existing Security Copilot demo use one real read-only AWS security/compliance signal without expanding the architecture.

## Working plan

1. Pull current `main` and read `AGENTS.md` first.
2. Use `AWS_PROFILE=amit` by default and the approved Region. `dev` only when specifically needed. Never use an AWS prod profile/account/environment; synthetic `prod` remains deny-test data only.
3. Run a very small read-only preflight and choose exactly one already-available source: Inspector2 first, then Security Hub, then AWS Config.
4. If none is available, report BLOCKED and stop. Do not enable a service or create resources for this milestone.
5. Replace only the synthetic read-only finding with one small sanitized real result through the existing LibreChat/thin-adapter path.
6. Keep the current human approval, Gateway ALLOW/DENY, compact audit, and harmless local remediation path intact.

## Acceptance

- one real read-only AWS security/compliance result is visible in LibreChat;
- no sensitive account IDs, ARNs, private endpoints, credentials, or unnecessary raw payloads are exposed;
- focused tests, `./scripts/check.sh`, and `git diff --check` pass;
- one live read-only proof uses profile `amit`;
- one thin authenticated browser proof shows the real result;
- no AWS resource creation/update/delete is needed for acceptance.
