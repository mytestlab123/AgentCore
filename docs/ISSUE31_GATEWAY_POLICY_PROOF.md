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

The live verifier reached `GATEWAY_POLICY_RESULT=PASS`. Raw identifiers,
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

The prod denial is a JSON-RPC error inside HTTP 200, which is valid MCP
transport behavior. Acceptance is based on the policy-denial body plus the
stable zero Lambda delta, not HTTP status alone.

The deployed Gateway advertised MCP protocol `2025-03-26`; requests using the
newer planned value were rejected before tool execution. The verifier now uses
the service-supported version.

## Approved permission exception

The retained standard `CDKToolkit` bootstrap uses its default broad
CloudFormation execution policy. This was initially a STOP finding and was
then explicitly accepted by the owner for this personal study POC. It must not
be represented as a least-privilege production design.

## Retention and estimated cost

Resources are retained for repeatable demonstrations. The estimate is roughly
US$1.01/month: approximately US$1/month for the retained customer-managed KMS
key in the bootstrap stack, plus negligible idle storage/indexing and tiny
bounded Gateway, policy, and Lambda test traffic. Actual usage can vary.

TTL and review-date tags are owner review markers, not automatic deletion
authority. Cleanup requires a separate inventory-first instruction.

## Commands

Offline validation:

```bash
./scripts/check.sh
```

Live proof after identity hashes are supplied privately:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 \
AGENTCORE_EXPECTED_ACCOUNT_SHA256=<approved-hash> \
AGENTCORE_EXPECTED_CALLER_SHA256=<approved-hash> \
python3 scripts/gateway_policy_poc.py --prove-live
```
