# AgentCore Repository Guidance

## Goal

Build a small, understandable internal AI platform POC following `ROADMAP.md`.
Follow KISS and optimize for a 3-5 minute demo.

The active implementation milestone is Issue #46: complete one real AWS
Security Group governance lifecycle while reusing the merged M1-M7 platform
and demo path.

## Scope

- Keep local simulation usable without AWS.
- Reuse the existing Project/Home, Playground, Logs, LibreChat, Gateway, Harness
  and validation paths before adding another framework.
- Reuse the merged M1-M7 governed workflow and final demo rather than rebuilding
  approval, Gateway Policy, audit, developer-client, or controlled-action plumbing.
- Issue #46 uses one fixed, dedicated, unattached demo Security Group. It may
  read that Group and, only after native approval plus Gateway ALLOW, revoke
  the single exact TCP/22-from-0.0.0.0/0 ingress rule and verify the result.
- Do not turn this into a generic Security Group mutation capability, accept a
  caller-selected resource/rule, or change any instance, ENI, route, public IP,
  or workload.
- An active Amit-approved Issue, PR, goal, task, or milestone authorizes the
  normal scoped AWS, IAM, configuration, deployment, service-restart, and
  validation changes needed to complete it. Do not request a second approval
  for those implementation steps.
- Stop and surface a decision only when a proposed action materially expands
  the approved scope, changes the authorization/security model, needs a
  different AWS profile/account/Region, creates an unrelated resource, or
  would cause an unapproved external impact.
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
- Bounded AWS changes that are part of an approved POC milestone are authorized;
  keep them narrow, intentional, and recorded without asking Amit again.
- Before any AWS test, confirm the active identity/profile and Region. Do not
  print or commit sensitive identity values as evidence.

## AWS CLI first / KISS execution

- For simple AWS reads, setup, verification, or one-off mutations, use the AWS
  CLI directly. Do not create Python, shell, SDK, MCP, or helper wrappers around
  work that is clearer as a few `aws ...` commands.
- Prefer native AWS CLI features first: `--query`, `--output text|json`, command
  substitution, and normal shell variables. Use `jq` only when the CLI query is
  genuinely insufficient.
- Do not use Python merely to extract IDs, build trivial JSON, count rules, hide
  identifiers, or validate a small AWS CLI result. Keep sensitive values in an
  unprinted shell variable or a private mode-600 temporary file when needed.
- Do not add a reusable script for a one-time or very short AWS operation. Prove
  the direct commands first; automate only when repetition or real complexity
  justifies it.
- Python/SDK code remains appropriate for application runtime logic, tests,
  non-trivial data processing, or reusable behavior that the AWS CLI cannot
  express cleanly. The burden is on the worker to keep the simpler CLI path when
  both approaches are equivalent.
- Prefer one provider read and one exact action over multiple discovery layers.
  Do not add service enablement, scanners, or orchestration when a direct API/CLI
  read already proves the demo requirement.
- In handoffs, report the exact AWS CLI action/result and the useful evidence;
  avoid long implementation narratives for simple cloud operations.

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
