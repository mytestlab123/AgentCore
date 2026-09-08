# Specification

Status: draft implementation proof for Issue #31 / Draft PR #33

Owner lifecycle decision (2026-09-08): low-cost resources are retained for
repeatable demos. Do not automatically delete resources estimated below
US$2/month.

Native deployment decision (2026-09-08): use the pinned official AgentCore CLI
and its CDK deployment path. Creating and retaining the `CDKToolkit` bootstrap
stack in the approved profile/Region is authorized. Do not deploy a Harness,
Runtime, or model.

## Problem

The earlier LibreChat demonstration could show approval controls only after a
model emitted a tool call. It did not prove that a deterministic AWS policy
boundary independently blocked an invocation before the backend executed.

## Scope

Build one disposable, model-free Amazon Bedrock AgentCore Gateway proof in
`ap-southeast-1` using the approved `amit` profile:

```text
check_demo_scope(environment=dev)
  -> Gateway Policy ALLOW -> Lambda executes exactly once

check_demo_scope(environment=prod)
  -> Gateway Policy DENY -> Lambda execution delta remains zero
```

The proof uses the AWS-managed Gateway URL with `AWS_IAM` authentication, one
synthetic Lambda tool, one Cedar policy, and bounded Lambda metrics. It does
not use an LLM or mutate application infrastructure.

The AgentCore CLI owns the Gateway, target, Policy Engine, and policy. A small
repo verifier may create/verify the prerequisite synthetic Lambda, enforce the
identity gates, perform signed calls, and collect evidence; it must not
reimplement Gateway Policy decisions.

## MUST

- Fail closed unless profile, region, expected account hash, and expected
  caller hash all match.
- Use only stable, tagged, Issue #31 resources that can be safely reused.
- Prove the dev response, exactly one Lambda invocation, the prod authorization
  denial, and zero additional Lambda invocations.
- Estimate idle and test-run cost before creation and record the estimate.
- Retain Gateway, policy engine, policy, Lambda, IAM roles, and minimal logs
  when their combined projected cost remains below US$2/month.
- Retain the account/Region `CDKToolkit` stack used by the AgentCore CLI while
  its projected idle cost remains below the same threshold.
- On rerun, discover and verify the exact tagged resources before reuse; do not
  create timestamped duplicates.
- Report partial creation or drift and stop. Do not automatically delete a
  low-cost resource merely because a run failed or was interrupted.
- Keep exact identity values and raw responses in private local evidence only;
  committed and PR evidence must be sanitized.
- Provide a default plan mode that makes zero AWS calls.

## MUST NOT

- Use a model, Harness, Runtime, LibreChat, public unauthenticated endpoint, custom
  policy service, or real remediation target.
- Reuse, modify, or delete unrelated or ambiguously owned AWS resources.
- Automatically delete retained Issue #31 resources without a separate,
  explicit cleanup instruction naming this proof.
- Commit credentials, account IDs, caller ARNs, private endpoints, or raw
  evidence.
- Claim PASS if ownership, retained-resource inventory, or backend invocation
  counts are ambiguous.

## Verification

```bash
./scripts/check.sh

AWS_PROFILE=amit AWS_REGION=ap-southeast-1 \
AGENTCORE_EXPECTED_ACCOUNT_SHA256=<approved-hash> \
AGENTCORE_EXPECTED_CALLER_SHA256=<approved-hash> \
python3 scripts/gateway_policy_poc.py --approve-live
```

The pinned upstream CLI dependency graph currently requires this Linux-safe
installation command because its lock metadata includes platform-specific
esbuild packages as non-optional entries:

```bash
npm ci --force --ignore-scripts --no-audit --no-fund \
  --prefix tools/issue31-agentcore
```

The live command converges the retained native stack, validates its deployed
state and ownership, records a bounded CloudWatch metric series, and repeats
the inventory/cost check after the proof before printing PASS.

Expected live result:

```text
DEV_DECISION=ALLOW
DEV_BACKEND_CALLS=1
PROD_DECISION=DENY
PROD_BACKEND_DELTA=0
RESOURCE_RETENTION=PASS
ESTIMATED_MONTHLY_IDLE_COST_USD=<value below 2.00>
GATEWAY_POLICY_RESULT=PASS
```

## Stop Gates

- AWS identity or region mismatch.
- Preflight/API/schema or entitlement failure.
- Any unexpected IAM, network, endpoint, resource, or cost requirement.
- Projected retained cost reaches US$2/month.
- Dev call count differs from one, prod reaches Lambda, or retained ownership
  and inventory cannot be independently verified.
- A proposed change broadens beyond the disposable Issue #31 proof.

## Resource lifecycle

- **Retain by default:** AgentCore Gateway/Policy resources, one small Lambda,
  its least-privilege IAM roles, minimal logs, and the CDK bootstrap stack while
  projected combined idle cost is below US$2/month.
- **Review, do not auto-delete:** tag retained resources with owner, project,
  purpose, a `TTL=08-10-26` review marker, and a review date. The TTL/review
  date triggers an owner review; it is not automatic deletion authority.
- **Clean quickly:** EC2, NAT Gateway, RDS, or other resources with material
  hourly/daily cost, but only when they are inside the approved scope and no
  longer required.
- **Explicit cleanup only:** deleting the retained Issue #31 stack requires a
  new exact owner instruction and an inventory-first check.

Implementation size is a review concern, not an authorization boundary. Keep
the solution compact, but do not remove safety, lifecycle controls, tests, or evidence to
fit an arbitrary file or line count.
