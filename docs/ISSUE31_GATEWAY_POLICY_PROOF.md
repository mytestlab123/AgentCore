# Issue #31 AgentCore Gateway Policy proof

Date: 2026-09-08

Region: `ap-southeast-1`

Provider path: native AgentCore CLI 0.28.1 and generated CDK
Model use: none

## Result

```text
check_demo_scope(environment=dev)
  -> Gateway Policy ALLOW
  -> synthetic Lambda execution delta = 1

check_demo_scope(environment=prod)
  -> Gateway Policy DENY by default
  -> synthetic Lambda execution delta = 0
```

The corrected live verifier reached `GATEWAY_POLICY_RESULT=PASS` on
2026-09-08 from 09:16 through 09:19 SGT. Raw identifiers,
managed endpoint details, requests, responses, CLI logs, and deployed state are
retained only in the private Issue #31 evidence directory.

## Architecture deployed

- One AWS_IAM-protected AgentCore MCP Gateway.
- One Lambda ARN Gateway target exposing `check_demo_scope`.
- One AgentCore Policy Engine in `ENFORCE` mode.
- One active Cedar `INITIATE` policy permitting the approved caller only when
  `context.input.environment == "dev"`.
- One fixed synthetic Lambda backend and its logging-only execution role.
- No model, AgentCore Runtime, Harness, Memory, API Gateway, VPC, database, or
  application-infrastructure mutation.

Deployment required two native CLI phases because the Cedar statement binds to
the deployed Gateway ARN. Phase 1 created the Gateway, target, and Policy
Engine; phase 2 inserted the private Gateway ARN and created the policy.

## Validation evidence

```text
DEV_DECISION=ALLOW
DEV_BACKEND_CALLS=1
PROD_DECISION=DENY
PROD_BACKEND_DELTA=0
RESOURCE_RETENTION=PASS
ESTIMATED_MONTHLY_IDLE_COST_USD=1.01
GATEWAY_POLICY_RESULT=PASS
```

The dev and prod requests both returned HTTP 200. The dev response was parsed
as an exact successful MCP JSON-RPC result containing the fixed synthetic
Lambda payload. The prod response was parsed as JSON-RPC error `-32002` with
the expected Gateway Policy deny-by-default message. Authentication errors,
generic errors containing "denied", and successful results mentioning that
word now fail closed.

The bounded CloudWatch proof used a quiet minute, recorded eight timestamped
samples whose only values were zero and one, and continued observation for two
minutes after the prod request. The count rose exactly once for dev and did not
rise for prod. Raw samples and responses remain private with file mode 600.

Final repository validation also passed: `./scripts/check.sh` ran the 12
focused Issue #31 tests, three offline governance tests, three frontend tests,
32 API tests, frontend/CDK builds, dependency audits, and diff checks without
making AWS calls. The standalone Python compile and full `git diff --check`
also passed.

The deployed Gateway advertised MCP protocol `2025-03-26`; requests using the
newer planned value were rejected before tool execution. The verifier now uses
the service-supported version.

## Approved permission exception

The retained standard `CDKToolkit` bootstrap uses its default broad
CloudFormation execution policy. This was initially a STOP finding and was
then explicitly accepted by the owner for this personal study POC. It must not
be represented as a least-privilege production design.

## Retention and estimated cost

Resources are retained for repeatable demonstrations. The post-proof inventory
verified the application stack `UPDATE_COMPLETE`, the bootstrap stack
`CREATE_COMPLETE`, Gateway and target `READY`, Policy Engine and policy
`ACTIVE`, required ownership tags, one retained bootstrap KMS key, and the
expected CloudFormation resource-type sets. The resulting estimate is roughly
US$1.01/month: approximately US$1/month for that customer-managed KMS key plus
a US$0.01 conservative buffer for tiny retained storage and bounded calls.
Actual usage can vary.

The current tagging API returns tag maps for the Gateway and Policy Engine.
The policy and Gateway target are instead proven as members of the dedicated
native CloudFormation stack; this service tag-surface gap is recorded in the
private retained inventory.

TTL and review-date tags are owner review markers, not automatic deletion
authority. Cleanup requires a separate inventory-first instruction.

## Commands

Offline validation:

```bash
./scripts/check.sh
```

Pinned CLI install on Linux:

```bash
npm ci --force --ignore-scripts --no-audit --no-fund \
  --prefix tools/issue31-agentcore
```

Live proof after identity hashes are supplied privately:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 \
AGENTCORE_EXPECTED_ACCOUNT_SHA256=<approved-hash> \
AGENTCORE_EXPECTED_CALLER_SHA256=<approved-hash> \
python3 scripts/gateway_policy_poc.py --prove-live
```

## Issue #34 integrity follow-up

The stacked Issue #34 verifier hardening repeated the retained live proof on
2026-09-08 from 09:36 through 09:39 SGT and reached the same PASS result.

The stronger verifier additionally proved:

- the native CLI deployment environment removes ambient static, web-identity,
  container, and role credential overrides before selecting profile `amit`;
- the live Cedar statement exactly equals the permit derived from the approved
  caller, Gateway ARN, tool action, and `environment == "dev"` condition;
- the Gateway is linked to the exact Policy Engine in `ENFORCE` mode and the
  target is linked to the exact retained Lambda;
- the application stack has exactly one Gateway, target, policy, Policy Engine,
  CDK metadata object, IAM policy, and IAM role;
- the bootstrap stack has exactly one S3 bucket, ECR repository, KMS key/alias,
  S3 policy, SSM parameter, two IAM policies, and five IAM roles;
- retained storage measured 65,884 S3 bytes, zero ECR image bytes, and 849 log
  bytes; together with one KMS key and the conservative small-use buffer, the
  calculated monthly estimate was US$1.0100023152, displayed as US$1.01;
- seven timestamped metric samples contained only zero and one, with dev delta
  one and prod delta zero.

The follow-up focused suite contains 16 offline regression tests covering the
new identity-environment, exact-linkage, exact-policy, duplicate-topology, and
measured-cost gates. Exact identifiers and raw evidence remain private.
