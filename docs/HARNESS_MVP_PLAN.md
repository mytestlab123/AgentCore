# AgentCore Harness MVP

**Status:** Deferred future task

**Repository owner:** `~/git/AgentCore`

**Public repository decision:** Do not create a separate `harness` repository.

**Environment:** Personal/test AWS account only. This plan is not approved for
office, Synapxe, GovTech, or production accounts.

**Reference:** [AgentCore learning issue #8](https://github.com/mytestlab123/AgentCore/issues/8)

**Maintenance note (2026-09-02):** This remains a future-only design. The
current AgentCore POC work is complete on the existing local/live demo paths;
this document does not authorize a Harness build, a new service, or a new
repository. When the work is approved, start from the current `main` branch
and re-run the preflight below rather than assuming that this plan is live
account evidence.

## 1. Purpose

Build the smallest real Amazon Bedrock AgentCore Harness proof so the operator
can explain what the managed Harness provides beyond a hand-built agent loop.
This is a learning MVP and a portfolio-quality demonstration, not a production
platform.

The final demonstration must answer one question clearly:

> Which runtime, session, tool, identity, and observability responsibilities
> are managed by Harness, and which permissions remain controlled by the
> customer?

## 2. Learning outcome

At the end of this task the operator must be able to:

1. Create one disposable Harness configuration.
2. Invoke it with one intentionally selected model.
3. Demonstrate one safe read-only capability.
4. Show the invocation/session and automatic trace evidence.
5. Change one configuration value without redesigning the application.
6. Delete the Harness resources and prove cleanup.
7. Explain the execution role as the real AWS permission boundary.
8. Compare managed Harness plumbing with the existing AgentCore approach.

## 3. Current truth and constraints

- The work stays in `~/git/AgentCore`.
- The proposed `~/git/harness` repository is cancelled.
- Existing unrelated dirty files must be preserved.
- No production or office AWS account may be used.
- No credentials, account IDs, ARNs, private endpoints, tokens, or raw runtime
  payloads may be committed.
- Amazon Nova 2 Pro access must not be assumed. A model is usable only after
  live account and region entitlement is proven.
- The retired Bedrock model-access page is not an enablement mechanism.
- A model visible in documentation, pricing, or another account is not proof
  that this account can invoke it.
- Repository-owned operator scripts belong under `scripts/` and must remain
  deterministic, reviewable, and placeholder-only. One-off helpers under
  `~/.AGENTS-temp/` are evidence, not the supported implementation path.
- Credentials, bearer tokens, and environment files stay outside Git in
  mode-600 files. A public document may name an external path, but never copy
  its contents.

## 4. Scope

### Included

- One Harness.
- One supported Bedrock model.
- One concise system instruction.
- One safe, read-only built-in capability or one narrow read-only Gateway/MCP
  tool.
- One real invocation.
- One automatic trace or observability proof.
- One small configuration experiment.
- Create, invoke, observe, delete, and cleanup verification.
- Concise public documentation and a repeatable operator path.

### Explicitly excluded

- Production, office, or customer data.
- Broad AWS API access or unrestricted shell access.
- Multiple Harnesses or a model benchmark.
- Multiple tools, multiple MCP servers, or multi-agent orchestration.
- RAG, vector databases, long-term memory design, or enterprise SSO.
- Custom containers unless the default runtime is proven insufficient.
- High-availability, scaling, performance, or cost benchmarking.
- A new frontend or a permanent service.
- LiteLLM or unrelated API-key experiments.

## 5. Architecture for the MVP

```text
Operator
   |
   v
Harness invocation
   |
   +--> selected Bedrock model
   |
   +--> one read-only capability
   |
   +--> isolated managed runtime/session
   |
   +--> execution role (AWS permission boundary)
   |
   +--> automatic trace and status evidence
   |
   v
Result -> evidence packet -> cleanup verification
```

The diagram is intentionally small. It must show the managed execution path,
the tool boundary, the identity boundary, and the evidence path without
introducing unrelated AWS services.

## 6. Phase 0: Read-only preflight

Do this before creating any resource or invoking any model.

### Local preflight

Read, in order:

1. `AGENTS.md` in the repository.
2. `CONTEXT.md` if present.
3. `SPEC.md` if present.
4. `docs/POC_ARCHITECTURE.md`.
5. `docs/ISSUE_9_BEDROCK_API_KEYS.md`.
6. This plan.

Check:

- current branch and dirty state;
- existing AgentCore scripts and ownership boundaries;
- available CLI versions;
- that no secret-bearing file will be staged;
- that the local output directory is under `/home/user`.

### AWS preflight

Use the approved personal/test profile and explicitly record the account and
region in private evidence only. Do not silently fall back to another profile,
region, or account.

Verify:

- caller identity;
- selected region;
- AgentCore Harness service availability;
- exact model ID and inference profile availability;
- model entitlement for this account;
- service quotas if the API exposes them;
- execution-role trust and required permissions;
- network prerequisites for the chosen tool path;
- expected cost and automatic cleanup path.

### Entitlement gate

The gate is binary:

- **PASS:** the exact model is visible and invokable for this account/region,
  and the execution role is authorized.
- **STOP:** model absent, early-access approval missing, IAM/SCP denial,
  unsupported region, or unclear account identity.

Do not invoke an unavailable model merely to discover that it is unavailable.
If the gate fails, write a blocker note and stop before resource creation.

## 7. Phase 1: Minimal design

Choose the simplest supported path documented by AWS.

### Model selection

1. Prefer the first model that passes the live entitlement gate.
2. Record the exact model ID and inference profile.
3. Do not substitute Nova 2 Pro, Nova 2 Lite, or another model by name alone.
4. Do not create a benchmark or compare several models in this MVP.

### Tool selection

Use exactly one capability:

1. A built-in read-only capability if it provides the clearest learning value.
2. Otherwise one narrow Gateway/MCP read-only tool.

The tool must return synthetic or non-sensitive data. It must not modify AWS,
read secrets, access private office systems, or write to production.

### Identity design

Use one dedicated execution role with only the actions needed for the chosen
Harness and tool path. Record the exact actions from the successful run. Do not
grant broad administrator, power-user, unrestricted IAM, or unrestricted
Bedrock permissions.

Document the distinction between:

- control-plane permissions used to create/invoke/delete the Harness; and
- execution-role permissions used by the running Harness.

## 8. Phase 2: Implementation

Keep implementation deterministic and small. The repository owner should add
only the files required for the create/invoke/delete proof, for example:

- one configuration file with placeholders only;
- one Bash or Python operator wrapper;
- one read-only tool definition or adapter;
- one concise README section;
- one evidence template.

The implementation must:

- use `/usr/bin/bash` for shell wrappers;
- validate shell syntax before execution;
- fail closed on missing account, region, model, role, or credential inputs;
- avoid printing credentials or complete environment dumps;
- write raw logs to a private evidence directory;
- return a compact terminal result with a stable status;
- make cleanup explicit and idempotent.

Do not add a large test framework. One syntax check, one local configuration
check, and one real E2E acceptance run are sufficient for this learning MVP.

## 9. Phase 3: Create and invoke

Run the following sequence once:

1. Create the disposable Harness.
2. Capture the returned identifier in private evidence.
3. Invoke the Harness with a fixed prompt and the one read-only capability.
4. Wait on the deterministic command until a terminal state.
5. Capture status, model step, tool step, result, and trace reference.
6. Redact credentials, IDs, private URLs, and sensitive payloads before any
   public documentation.

The invocation should answer a small deterministic prompt such as:

```text
Return the synthetic service-health value and explain which read-only tool was used.
```

The expected result is a stable marker plus enough trace information to prove
that the managed Harness path was used.

## 10. Phase 4: Small configuration experiment

Perform exactly one bounded change, such as:

- change the system instruction; or
- change the selected model to another model that independently passes the
  entitlement gate; or
- change the read-only tool description.

Invoke again once and record what changed. Do not turn this into a model
benchmark or redesign the runtime.

## 11. Phase 5: Cleanup and recovery

Cleanup is mandatory unless a resource is deliberately retained and documented.

1. Delete the Harness and any temporary endpoint, tool, or role created only
   for this test.
2. Remove temporary credentials from the shell and local files.
3. Confirm the resource is deleted or in a terminal deleted state.
4. Confirm no unexpected compute, storage, log, or networking resource remains.
5. Record cleanup evidence before declaring success.

If invocation fails, do not repeatedly recreate resources. Save the failure,
identify whether it is entitlement, IAM, network, tool, or runtime related,
then stop at the written boundary.

## 12. Evidence contract

Private evidence belongs under:

```text
/home/user/.AGENTS-temp/AgentCore/harness-mvp/<timestamp>/
```

The evidence packet should contain:

| Artifact | Required content |
|---|---|
| `RESULT.md` | PASS/BLOCKED, scope, exact model, region, result, blocker, next action |
| `RUN.log` | Sanitized command and status output; no secrets |
| `TRACE.md` | Invocation/session/tool/trace explanation |
| `CLEANUP.md` | Deleted resources and independent verification |
| `PUBLIC_SUMMARY.md` | Alias-only explanation safe for the public repository |

Do not commit the private evidence packet. Only the sanitized summary and
generic diagrams may be committed.

## 13. Acceptance criteria

The MVP is complete only when all are true:

- official Harness documentation was reviewed;
- the personal/test account and region were proven;
- the exact model passed the entitlement gate;
- one Harness was created successfully;
- one real invocation succeeded;
- one read-only capability was demonstrated;
- the execution-role boundary was documented;
- automatic trace/observability evidence was captured;
- one configuration experiment was completed;
- create -> invoke -> observe -> delete is repeatable;
- cleanup was independently verified;
- the managed-versus-hand-built comparison is written;
- no secret or private infrastructure detail is public.

## 14. Hard stop conditions

Stop immediately for:

- wrong AWS account or region;
- missing model entitlement or early-access approval;
- IAM, SCP, permissions-boundary, or service-control denial;
- request to add broad permissions;
- request to use office or production data;
- unexpected public networking or public IP requirement;
- tool requiring write access when read-only was specified;
- unredacted secret, token, account ID, ARN, or private endpoint in an output;
- cleanup failure or unexplained residual resource;
- conflicting current truth in the repository.

## 15. Public demonstration outline

The final README/demo should take five minutes:

1. State the learning question.
2. Show the four-part architecture: invocation, model, tool, managed runtime.
3. Show the execution-role boundary.
4. Run one invocation and show the trace/result.
5. Show the one configuration change.
6. Show cleanup verification.
7. Explain what Harness removes from the hand-built implementation and what it
   does not solve, especially IAM and tool authorization.

Avoid claims about production readiness, scale, cost, or model quality unless
those claims are separately measured and documented.

## 16. Future extensions, not part of this MVP

Only after this MVP is accepted may a separate issue consider:

- a second model;
- a governed Gateway/MCP tool;
- memory or session persistence;
- identity/policy integration;
- a controlled AWS read-only assistant;
- cost and latency measurement;
- a production architecture.

Each extension must have its own scope, entitlement preflight, permissions
review, evidence contract, and cleanup plan.

## Definition of done

The operator can truthfully say:

> I created one disposable AgentCore Harness in a personal test account,
> invoked one entitlement-verified model through one safe read-only capability,
> observed the managed execution and trace path, changed one configuration
> value, and removed the test resources. I can explain which responsibilities
> Harness manages and which remain controlled by IAM and tool policy.

## Refresh checklist before future implementation

Reconfirm the following immediately before starting this deferred task:

1. Read `AGENTS.md`, `~/.codex/AWS.md`, and the current issue/PR scope.
2. Check the branch, dirty files, and existing `scripts/` ownership.
3. Verify the intended AWS profile, account, region, model entitlement, and
   execution-role boundary in private evidence.
4. Set a small change budget before coding; stop if the design needs a new
   framework, service, broad permission, or public network path.
5. Keep raw output under `/home/user/.AGENTS-temp/AgentCore/`; publish only
   alias-only summaries and generic diagrams.
