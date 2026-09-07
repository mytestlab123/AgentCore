# AgentCore — ChatGPT Session Bootstrap

Use this file to start a **new, short ChatGPT session** for this repository.

## Repository

https://github.com/mytestlab123/AgentCore

## Working principle

Follow **KISS**:

> one problem, one happy path, one command, one proof, one result

Do not rebuild context from the full chat history. Read only the current owning Issue, PR, and contract unless more context is required.

## Collaboration protocol

Read first:

https://github.com/amitkarpe/work/blob/main/docs/chatgpt/CHATGPT_COLLABORATION_PROTOCOL.md

Core rules:

- keep changes small and reviewable;
- reuse the current Issue/PR instead of creating parallel work;
- distinguish planning from implementation;
- do not widen AWS/IAM/deployment authority implicitly;
- never place credentials, account IDs, ARNs, tokens, private endpoints, or sensitive evidence in Git.

## Current active milestone

### Issue #31

https://github.com/mytestlab123/AgentCore/issues/31

Question:

> Can AgentCore Gateway Policy deterministically ALLOW one structured tool call and DENY another before the backend executes?

Target proof:

```text
check_demo_scope(environment=dev)
  -> AgentCore Gateway Policy -> ALLOW -> backend executes once

check_demo_scope(environment=prod)
  -> AgentCore Gateway Policy -> DENY -> backend execution delta = 0
```

No LLM and no LibreChat are involved in this proof.

### Draft PR #33

https://github.com/mytestlab123/AgentCore/pull/33

STRICT contract:

https://github.com/mytestlab123/AgentCore/blob/feature/issue-31-agentcore-gateway-policy/docs/chatgpt/inbox/REQUEST-20260907-issue31-agentcore-gateway-policy-strict.md

Current state:

- Draft PR is open.
- **HOLD is active.**
- No implementation or AWS mutation is authorized yet.

## Frozen scope

After HOLD is explicitly lifted, expected implementation is limited to:

1. `scripts/gateway_policy_poc.py`
2. `scripts/test_gateway_policy_poc.py`
3. minimal `scripts/check.sh` wiring only if needed

Target:

```text
<= 3 product files
<= 200 non-generated changed lines
```

Live proof must use only:

```text
AWS profile: amit
Region: ap-southeast-1
```

The test may create only disposable Gateway / Policy / Lambda / temporary least-privilege IAM resources required for this isolated proof, then delete and independently verify cleanup.

## Explicit non-goals

Do not add:

- LibreChat changes;
- LLM/model inference;
- AgentCore Harness or Runtime;
- Temporal Policy / human approval sequencing;
- EC2, Inspector, SSM, Security Hub, Config, S3 remediation;
- production/customer/office data;
- provider subscriptions, API keys, quota changes, or copied credentials;
- VPC/network architecture;
- persistent deployment;
- multi-agent, RAG, or UI work.

## Required PASS result

```text
DEV_DECISION=ALLOW
DEV_BACKEND_CALLS=1
PROD_DECISION=DENY
PROD_BACKEND_DELTA=0
CLEANUP=PASS
GATEWAY_POLICY_RESULT=PASS
```

Any IAM, Gateway, Policy, Region, schema, unexpected backend execution, or cleanup problem must fail closed as `BLOCKED` / failure.

## New-chat instruction

Paste this into the new ChatGPT session:

> Read `docs/chatgpt/SESSION_BOOTSTRAP.md`, then Issue #31, Draft PR #33, and the STRICT contract. Follow the collaboration protocol and KISS. Work only on this one milestone. Do not create another Issue/PR unless the current one cannot own the work. HOLD remains active until Amit explicitly lifts it.
