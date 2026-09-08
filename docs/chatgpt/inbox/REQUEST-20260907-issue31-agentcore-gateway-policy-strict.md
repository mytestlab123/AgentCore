# STRICT implementation contract — Issue #31

Issue:
https://github.com/mytestlab123/AgentCore/issues/31

## Status

**HOLD LIFTED by Amit on 2026-09-07.**

Approved live boundary: `AWS_PROFILE=amit` and
`AWS_REGION=ap-southeast-1`.

Lifecycle amendment approved by Amit on 2026-09-08 supersedes every older
mandatory-cleanup or deletion-TTL statement in this contract: retain the
dedicated low-cost Issue #31 resources when projected combined cost is below
US$2/month. Do not auto-delete them on success, failure, or interruption.
Tag a review date instead of an automatic cleanup TTL. Cleanup requires a new,
explicit instruction for this exact stack. Material hourly/day resources such
as EC2 or NAT Gateway remain cleanup-first, but are not part of this milestone.

Native CLI amendment approved by Amit on 2026-09-08: use pinned official
AgentCore CLI `0.28.1` for Gateway, target, Policy Engine, and policy deployment.
Creating and retaining the account/Region `CDKToolkit` bootstrap stack is
explicitly authorized. The stack remains subject to the US$2/month cost gate.
Harness, Runtime, and model deployment remain prohibited.

### Practical implementation amendment

Amit approved the following correction after the mandatory preflight exposed
the original budget and endpoint mismatch:

- aim for roughly five changed files and 500 non-generated changed lines as a
  review target, but do not omit safety, lifecycle controls, tests, or durable evidence to
  force that estimate;
- the AWS-managed Gateway URL is permitted only with `AWS_IAM` authentication;
- expected account and caller SHA-256 environment gates are mandatory;
- bounded AWS/Lambda invocation metrics may prove backend execution count;
- the original no-public-endpoint rule means no unauthenticated or separately
  created public endpoint; it does not prohibit the IAM-protected managed URL.

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

For the isolated pinned CLI 0.28.1 toolchain on Linux, install with
`npm ci --force --ignore-scripts --no-audit --no-fund --prefix
tools/issue31-agentcore`; the force flag is a documented workaround for
upstream non-optional platform-specific esbuild lock metadata, not permission
to relax any deployment or proof gate.

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
-> retain the tagged low-cost stack for repeatable demos
-> independently verify retained inventory and projected monthly cost
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
RESOURCE_RETENTION=PASS
ESTIMATED_MONTHLY_IDLE_COST_USD=<value below 2.00>
```

If the policy engine, Gateway, IAM, Region, target schema, service availability,
ownership, retention inventory, or cost differs from the reviewed contract,
the result is BLOCKED. Do not substitute another architecture.

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
resource_retention=PASS
estimated_monthly_idle_cost_usd=<value below 2.00>
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
- retained-resource inventory and cost verification.

Do not enable CloudWatch Transaction Search, account-wide observability, VPC resources, public networking, databases, or another managed service just for evidence.

Prewrite exact cleanup commands before create for future owner-directed use,
but do not execute them automatically. PASS requires every retained resource to
be independently inventoried, tagged, unambiguously owned, and projected below
US$2/month.

## Credential guardrails

- use the existing local `amit` AWS profile only;
- do not create/copy/rotate Bedrock API keys or AWS long-term credentials;
- do not copy local credentials to EC2, LibreChat, containers, or another host;
- do not print credentials or environment secrets;
- do not place identifiers or credentials in argv, Git, Issues, PR text, screenshots, or logs;
- use dedicated service roles only where the POC itself requires them, with
  least privilege and explicit ownership tags.

## Expected implementation files

Expected compact implementation:

1. `scripts/gateway_policy_poc.py`
   - plan/preflight/live lifecycle;
   - create only the reviewed disposable resources;
   - invoke the two structured calls;
   - calculate backend execution delta;
   - sanitize result;
   - retained-resource inventory and final cost verification.

2. `scripts/test_gateway_policy_poc.py`
   - offline tests only;
   - no AWS calls.

3. `scripts/check.sh`
   - only the smallest wiring needed to run the focused test.

Target:

```text
approximately 5 changed files
approximately 500 non-generated changed lines total
```

This is a review target, not a hard limit or safety gate. Explain material
growth in the PR, and never remove safety, lifecycle controls, validation, or evidence only
to fit the estimate.

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
- ambiguous ownership, duplicate resources, or cost above the threshold
  prevents PASS;
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
10. future cleanup commands/API calls are known before mutation, while the
    approved default for this stack remains retention.

Do not make a billable model invocation as part of this preflight.

## NO-GO / BLOCKER conditions

Stop without substituting architecture if any of these occurs:

- wrong/unclear profile, account, caller, or Region;
- AgentCore Gateway or Policy is unavailable in the approved Region/account;
- current policy cannot deterministically inspect the tool argument needed for this proof;
- Gateway cannot expose the single narrow Lambda tool without adding another hosted layer;
- implementation requires Runtime, Harness, remote MCP hosting, API Gateway, a VPC, database, or public endpoint;
- success would require broad IAM beyond the owner's explicitly approved
  standard CDK bootstrap exception, or any unreviewed PowerUserAccess;
- evidence would require enabling an account-wide logging/observability feature;
- denied call cannot be independently proven to have zero backend execution;
- code grows materially beyond the review target without explanation;
- secret/private identifiers would need to enter Git;
- retained resources cannot be independently identified, tagged, or kept below
  the US$2/month threshold.

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
- persistent AWS deployment other than the explicitly approved retained,
  tagged, sub-US$2 Issue #31 and CDK bootstrap resources;
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
- retained-resource inventory and monthly cost estimate;
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
