# STRICT implementation contract — Issue #31

Issue:
https://github.com/mytestlab123/AgentCore/issues/31

## Status

**PLANNING ONLY / HOLD ACTIVE.**

This contract authorizes no AWS mutation and contains no feature implementation.
Codex must not start implementation until Amit/ChatGPT explicitly lifts the hold in the linked Draft PR.

## One question

> Can Amazon Bedrock AgentCore Gateway Policy deterministically ALLOW one structured tool call and DENY the equivalent higher-risk call before the backend executes?

This milestone isolates the hard authorization boundary. It intentionally uses no LLM, no LibreChat, and no real workload data.

## Selected proof

Use one Gateway-exposed tool:

```text
check_demo_scope(environment)
```

Use exactly two structured calls:

```text
environment=dev   -> ALLOW -> backend executes once
environment=prod  -> DENY  -> backend execution delta remains zero
```

The same tool is used for both calls so the proof exercises argument-based policy rather than two different backends.

## One command

After HOLD is explicitly lifted, the implementation should expose one live command:

```bash
python3 scripts/gateway_policy_poc.py --approve-live
```

A zero-AWS local plan/test path may also exist, but the live proof above is the only acceptance path.

## One happy path

```text
exact profile + Region preflight
-> create temporary least-privilege IAM roles
-> create one disposable Lambda backend
-> create one disposable AgentCore Gateway + target
-> create/attach one deny-by-default AgentCore Policy
-> call check_demo_scope(environment=dev)
-> prove ALLOW and backend call count = 1
-> call check_demo_scope(environment=prod)
-> prove DENY and backend call delta = 0
-> capture sanitized evidence
-> delete all dedicated resources
-> independently verify absence
```

## Expected final result

The public-safe summary must finish with exactly one of:

```text
GATEWAY_POLICY_RESULT=PASS
GATEWAY_POLICY_RESULT=BLOCKED
```

PASS requires all of:

```text
DEV_DECISION=ALLOW
DEV_BACKEND_CALLS=1
PROD_DECISION=DENY
PROD_BACKEND_DELTA=0
CLEANUP=PASS
```

If the policy engine, Gateway, IAM, Region, target schema, service availability, or cleanup differs from the reviewed contract, the result is BLOCKED. Do not substitute another architecture.

## Frozen AWS boundary

Use only:

```text
AWS_PROFILE=amit
AWS_REGION=ap-southeast-1
```

The implementation must also require operator-provided expected account/caller gates privately before any create call. Never commit the real account ID or caller ARN.

No fallback to another profile, account, Region, or service is permitted.

## Exact policy intent

The policy must be deterministic and deny-by-default.

Conceptual rule:

```text
permit check_demo_scope only when environment == "dev"
deny / no permit for environment == "prod"
```

Use the current AWS-supported AgentCore Policy representation/API (Cedar/Dogwood as appropriate to the current service contract). Codex must verify current official APIs before implementing syntax.

The authorization input must come from the structured Gateway tool arguments. Do not inspect or classify natural-language prompt text.

## Backend contract

The backend is one disposable Lambda function with a fixed synthetic response.

It must:

- accept only the narrow test payload required by the Gateway target;
- return a fixed non-sensitive result;
- perform no EC2, SSM, Inspector, S3, Config, Security Hub, IAM, networking, or other workload API call;
- create no child resource;
- store no data;
- use no secret;
- emit only minimal evidence needed to prove invocation count.

The backend exists only to answer: "did execution happen?"

## Evidence contract

Private evidence may contain exact AWS identifiers but must remain outside Git under a mode-700/600 local directory such as:

```text
/home/user/.AGENTS-temp/AgentCore/issue-31-gateway-policy/<timestamp>/
```

Public repository/PR evidence may contain only sanitized fields such as:

```text
profile_alias=amit
region=ap-southeast-1
tool=check_demo_scope
dev_decision=ALLOW
dev_backend_calls=1
prod_decision=DENY
prod_backend_delta=0
cleanup=PASS
```

Do not commit:

- AWS account ID;
- real ARN/resource ID;
- credentials/tokens/session data;
- private endpoint;
- raw CloudTrail/CloudWatch payload;
- raw Gateway/Policy response containing private identifiers.

## How DENY must be proven

A policy error string by itself is not enough.

The proof must combine:

1. a Gateway/Policy result showing the `prod` call was denied; and
2. independent backend evidence showing no new Lambda execution occurred for that denied call.

The key acceptance invariant is:

```text
PROD_BACKEND_DELTA=0
```

If the denied call reaches Lambda, the milestone fails even if some upstream component later reports DENY.

## How ALLOW must be proven

The `dev` call must:

1. reach the same Gateway/tool path;
2. be permitted by policy;
3. invoke Lambda exactly once; and
4. return the fixed synthetic result through the Gateway path.

Do not invoke Lambda directly as acceptance proof.

## Cost and lifecycle guardrails

No LLM/model inference is part of this milestone.

Live work is limited to:

- one small Lambda function;
- temporary least-privilege IAM roles/policies required for this isolated proof;
- one AgentCore Gateway + one target;
- one AgentCore policy engine/policy or the minimum current AWS equivalent;
- exactly one allowed and one denied test call;
- minimal native logging/evidence reads;
- cleanup.

Do not enable CloudWatch Transaction Search, account-wide observability, VPC resources, public networking, databases, or another managed service just for evidence.

Prewrite cleanup before create. Cleanup must run on success and failure. PASS is impossible until every dedicated resource is independently verified absent.

## Credential guardrails

- use the existing local `amit` AWS profile only;
- do not create/copy/rotate Bedrock API keys or AWS long-term credentials;
- do not copy local credentials to EC2, LibreChat, containers, or another host;
- do not print credentials or environment secrets;
- do not place identifiers or credentials in argv, Git, Issues, PR text, screenshots, or logs;
- use temporary service roles only where the POC itself requires them, with least privilege and explicit cleanup.

## Expected implementation files

Maximum three product files:

1. `scripts/gateway_policy_poc.py`
   - plan/preflight/live lifecycle;
   - create only the reviewed disposable resources;
   - invoke the two structured calls;
   - calculate backend execution delta;
   - sanitize result;
   - cleanup/final verification.

2. `scripts/test_gateway_policy_poc.py`
   - offline tests only;
   - no AWS calls.

3. `scripts/check.sh`
   - only the smallest wiring needed to run the focused test.

Target:

```text
<= 3 product files
<= 200 non-generated changed lines total
```

If current AgentCore APIs make this budget unrealistic, Codex must post BLOCKER before exceeding it.

The script may generate a tiny Lambda handler and ZIP in a private temporary directory at runtime instead of adding a fourth product file.

## Required offline tests

The focused test must prove at minimum:

- plan/offline mode performs no AWS calls;
- wrong/missing profile gate fails before create;
- wrong/missing Region gate fails before create;
- only `check_demo_scope` is accepted by the local contract;
- only `dev` and `prod` are accepted test inputs;
- expected ALLOW/DENY result parsing is fail-closed;
- backend delta calculation treats any `prod` increment as failure;
- cleanup failure prevents PASS;
- sanitization excludes account IDs/ARNs/private identifiers.

Required validation before review:

```bash
python3 -m py_compile scripts/gateway_policy_poc.py
python3 scripts/test_gateway_policy_poc.py
./scripts/check.sh
git diff --check
```

Do not add a new test framework.

## Mandatory live preflight

After HOLD is lifted but before creating anything, Codex must privately verify:

1. current branch/PR/Issue match this contract;
2. explicit `amit` profile is authenticated;
3. current caller matches operator-provided expected identity gates;
4. Region is exactly `ap-southeast-1`;
5. AgentCore Gateway and Policy APIs required by this design are available in Singapore;
6. current AWS CLI/SDK exposes the required create/list/get/delete/invoke operations;
7. the minimum temporary IAM permissions are understood before creation;
8. the Gateway target type needed for one Lambda tool is currently supported;
9. policy can inspect the structured `environment` argument in the current service contract;
10. cleanup commands/API calls are known before mutation.

Do not make a billable model invocation as part of this preflight.

## NO-GO / BLOCKER conditions

Stop without substituting architecture if any of these occurs:

- wrong/unclear profile, account, caller, or Region;
- AgentCore Gateway or Policy is unavailable in the approved Region/account;
- current policy cannot deterministically inspect the tool argument needed for this proof;
- Gateway cannot expose the single narrow Lambda tool without adding another hosted layer;
- implementation requires Runtime, Harness, remote MCP hosting, API Gateway, a VPC, database, or public endpoint;
- success would require broad IAM, AdministratorAccess, or PowerUserAccess;
- evidence would require enabling an account-wide logging/observability feature;
- denied call cannot be independently proven to have zero backend execution;
- code exceeds the approved budget without review;
- secret/private identifiers would need to enter Git;
- any dedicated resource cannot be deleted and independently verified absent.

BLOCKER format:

```text
BLOCKER
Expected: <reviewed behavior>
Actual: <current AWS/repository reality>
Why blocked: <evidence-based reason>
Smallest options: 1. <option>  2. <option>
Architecture changed: NO
Alternative implementation started: NO
Decision required: ChatGPT / Amit
```

## Explicitly out of scope

Do not add or change:

- LibreChat;
- GPT/OpenAI/Nova/Claude model inference;
- AgentCore Harness;
- AgentCore Runtime;
- AgentCore Memory;
- Temporal Policy;
- human approval/Approve Once;
- custom approval UI;
- pre-model raw-prompt firewall;
- real remote MCP server hosting;
- EC2/Inspector/SSM/S3/Security Hub/Config workload integrations;
- ASR, Cloud Custodian, patching, remediation, or IaC changes;
- production/customer/office data;
- provider subscriptions, quotas, or entitlement changes;
- persistent AWS deployment;
- multi-agent/RAG;
- frontend changes.

## What this milestone proves

If PASS, it proves only:

> AgentCore Gateway Policy can deterministically permit one structured tool call based on its argument and deny the equivalent disallowed call before the Lambda backend executes.

It does **not** prove:

- LibreChat integration;
- human approval sequencing;
- Temporal Policy / one-time approval;
- production RBAC/SSO;
- real remediation safety;
- multi-user isolation;
- broad MCP security;
- production observability or HA.

## Next logical milestone after PASS

Do not implement this now, but the next candidate would be:

```text
LibreChat ASK
-> trusted approval event
-> Gateway/Temporal Policy
-> one bounded synthetic action
-> Approve Once semantics
```

That later milestone must remain separate.

## Codex review handoff

Before ChatGPT review, Codex must post one concise PR comment containing:

- changed files and line budget;
- exact AWS profile alias + Region used;
- current Gateway/Policy API path used;
- `DEV_DECISION` and `DEV_BACKEND_CALLS`;
- `PROD_DECISION` and `PROD_BACKEND_DELTA`;
- focused test result;
- `./scripts/check.sh` result;
- cleanup verification;
- statement that no model, LibreChat, workload data, credential copy, public endpoint, or unrelated AWS service was added;
- sanitized private-evidence location only, never its sensitive contents.

Then stop. Do not mark Ready or merge.

## Review / merge gate

Codex must not:

- implement until HOLD is explicitly lifted;
- create a replacement Issue, branch, or PR;
- mark the Draft PR Ready;
- merge;
- close Issue #31;
- broaden architecture on BLOCKER;
- perform any AWS change outside the exact approved live lifecycle.

ChatGPT must review the actual final diff and evidence against Issue #31 and this contract before any Ready/merge decision.