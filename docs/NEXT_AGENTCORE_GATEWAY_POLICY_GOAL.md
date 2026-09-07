# Next AgentCore learning goal — Gateway + Policy on one narrow tool

**Status:** planning handoff for the next ChatGPT thread

**Repository:** `mytestlab123/AgentCore`

**Date:** 2026-09-07

**Purpose:** define exactly one small next learning milestone from the Bedrock / AgentCore evidence already collected. This file is planning only. It does **not** authorize AWS creation, mutation, entitlement changes, IAM changes, model invocation, or implementation by itself.

---

## 1. Current repository truth to read first

The next ChatGPT thread should read these before proposing an Issue or PR:

1. `docs/AMIT_BEDROCK_MODEL_AVAILABILITY.md`
2. `docs/kiro-learning-bedrock-ai-models.md`
3. `docs/HARNESS_MVP_PROOF.md`
4. `docs/LIBRECHAT_TOOL_APPROVAL_LIMITATIONS.md`
5. GitHub Issue #26 — Harness inline tool-use + native observability
6. Draft PR #27 — STRICT contract for Issue #26

Also use the latest Kiro Bedrock/AgentCore Q1-Q12 learning handoff if it has been committed by then.

---

## 2. What we have learned

### Bedrock model access

Repository evidence currently proves:

- `global.amazon.nova-2-lite-v1:0` works with the approved personal `amit` profile in Singapore.
- `apac.anthropic.claude-3-haiku-20240307-v1:0` also has a bounded successful inference proof.
- a model being catalog-visible or having an ACTIVE inference profile does **not** prove it is invokable.
- `global.openai.gpt-5.6-luna` is visible but currently blocked for the tested account by an AWS model-availability/access result.
- Claude Haiku 4.5 is visible but currently requires the Anthropic use-case onboarding step.
- another test profile has an observed zero Nova 2 Lite daily token allocation; this is a quota/account state, not automatically an IAM defect.
- the correct inference **profile** matters. A base model ID may be visible but still not support the caller's requested on-demand route.

### AgentCore

Current learning/proofs establish:

- Amazon Bedrock AgentCore Harness is a real managed AgentCore component.
- this repository already proved a small real Harness create -> invoke -> delete lifecycle with Nova 2 Lite.
- Issue #26 / Draft PR #27 already own the next Harness-specific learning slice:

```text
Harness
 -> model selects one inline function
 -> tool_use
 -> deterministic client returns one synthetic result
 -> same-session resume
 -> final answer
 -> native observability
 -> cleanup
```

- Issue #26 intentionally excludes AgentCore Gateway, remote MCP, Lambda, real AWS tools, LibreChat changes, and remediation.

### Policy / HITL architecture

The current design distinction is important:

```text
LibreChat ASK / Approve / Reject
        = human UX / checkpoint

AgentCore Gateway Policy
        = deterministic server-side ALLOW / DENY on structured tool calls

Narrow tool implementation + IAM
        = final execution / cloud permission boundary
```

LibreChat policy only evaluates a tool call **after the model emits it**. It does not reliably prove a pre-model raw-user-intent DENY.

AgentCore Gateway Policy is therefore interesting because it can become a deterministic authorization layer on the structured tool invocation rather than trusting model prose.

### Tool design

For the future Security / Compliance assistant:

- prefer a few **narrow typed tools** over a broad generic AWS API tool surface;
- skills/prompts may explain what to do, but they must not grant authority;
- known deterministic remediators such as IaC, ASR, SSM Automation, and Patch Manager should be preferred over model-generated arbitrary AWS API mutation;
- real write/remediation remains out of scope until the read-only governance chain is proven.

---

# 3. Selected next goal

## One question only

> **Can Amazon Bedrock AgentCore Gateway + Policy deterministically ALLOW one exact structured tool call, DENY the same tool with a disallowed argument before the target executes, produce useful evidence, and clean up completely?**

This should be the next **Gateway/Policy learning milestone after Issue #26 is complete**.

If Issue #26 / PR #27 is still in HOLD or unfinished when a new ChatGPT thread starts, do not mix this implementation into PR #27. Planning may be prepared separately, but execution should remain sequential unless Amit explicitly changes that decision.

---

## 4. Why this is the right next small test

Issue #26 answers:

> Can Harness perform one tool-use / tool-result / resume cycle?

The missing security question immediately after that is:

> Can AWS enforce a deterministic server-side policy **before the tool target executes**?

Do **not** combine everything yet:

```text
LibreChat + Harness + Gateway + Temporal Policy + SSM + real remediation
```

That would make failure analysis difficult and would teach too many concepts at once.

Instead isolate the policy layer first.

---

# 5. Frozen architecture for this milestone

```text
Small deterministic test client
          |
          | MCP tools/call
          v
AgentCore Gateway
          |
          v
AgentCore Policy (Cedar / current supported policy engine)
      /              \
   ALLOW              DENY
     |                  X
     v             target must not run
One Lambda target
     |
     v
Fixed synthetic result

Evidence -> Gateway/Policy/CloudWatch logs or traces
Cleanup  -> delete every dedicated resource
```

### Important simplification

**No LLM is required for this milestone.**

That is intentional.

We already have separate model and Harness proofs. Removing the model makes this experiment cheaper, more deterministic, and easier to explain:

> same exact structured request -> policy decision -> target execution or no execution.

A later milestone can connect Harness to the already-proven Gateway/Policy path.

---

# 6. Exact test tool

Use exactly one tiny tool, suggested contract:

```text
check_demo_scope(environment)
```

Allowed input values:

```text
environment = "dev" | "prod"
```

The Lambda returns only a fixed public-safe synthetic result, for example:

```json
{
  "environment": "dev",
  "status": "healthy",
  "source": "synthetic-demo"
}
```

The Lambda must make **zero AWS data-plane calls** for this first policy proof.

It exists only to prove whether Gateway actually reached the target.

---

# 7. Policy behavior to prove

Use deny-by-default behavior with one explicit narrow permit.

Required outcomes:

```text
check_demo_scope(environment="dev")
    -> ALLOW
    -> Lambda invoked exactly once
    -> fixed result returned

check_demo_scope(environment="prod")
    -> DENY
    -> Lambda NOT invoked
    -> deterministic policy denial recorded
```

The exact Cedar/current AgentCore policy syntax must come from current AWS documentation and actual implementation. Do not invent policy fields.

This milestone should prove **argument-level authorization**, not merely a tool-name allowlist.

That learning maps directly to future rules such as:

```text
read-only operation                 -> ALLOW
controlled dev remediation          -> ASK / approval workflow later
production mutation without ticket  -> DENY
```

Only the first deterministic ALLOW/DENY foundation is in scope now.

---

# 8. Acceptance criteria

PASS requires all of the following:

- [ ] current official AgentCore Gateway + Policy documentation reviewed;
- [ ] approved personal/test profile and `ap-southeast-1` identity preflight passes;
- [ ] Gateway and Policy are confirmed available for the selected account/Region before creation;
- [ ] one temporary Gateway exists;
- [ ] exactly one narrow Lambda-backed tool exists;
- [ ] one explicit policy permit allows `environment=dev`;
- [ ] unmatched / `environment=prod` request is denied by policy;
- [ ] ALLOW path invokes Lambda and returns the fixed synthetic result;
- [ ] DENY path proves the Lambda was not invoked for that request;
- [ ] at least one useful sanitized Gateway/Policy/CloudWatch evidence reference is captured;
- [ ] no model invocation is required;
- [ ] no real EC2/S3/Inspector/SSM data is read;
- [ ] no AWS workload mutation/remediation occurs;
- [ ] all dedicated Gateway/Policy/Lambda/IAM/log resources are deleted or the exact retained log boundary is documented;
- [ ] cleanup is independently verified;
- [ ] repository checks and secret/identifier scans pass;
- [ ] public evidence contains no account ID, ARN, credential, private endpoint, or raw sensitive payload.

---

# 9. MUST NOT

Do not add in this milestone:

- LibreChat changes;
- human approval UI;
- Temporal Policy / approval-event history;
- AgentCore Harness integration;
- custom AgentCore Runtime container;
- Bedrock model invocation;
- OpenAI / Claude / Gemini / second provider;
- remote third-party MCP server;
- AWS Agent Toolkit as the runtime tool surface;
- EC2, Inspector, SSM, Config, Security Hub, Prowler, or real security findings;
- real remediation;
- Patch Manager execution;
- ASR execution;
- Cloud Custodian;
- S3/EC2/security-group mutation;
- RAG, Memory, Browser, Code Interpreter, Evaluations, Registry;
- broad AWS IAM permissions;
- production/office/customer account or data;
- new GUI.

Do not broaden the milestone merely because AgentCore exposes more capabilities.

---

# 10. Security boundaries

The test must demonstrate this separation clearly:

```text
Client request
    |
    v
Gateway authentication
    |
    v
Policy authorization
    |
  ALLOW only
    v
Narrow Lambda implementation
    |
    v
Lambda execution role
```

Rules:

- policy is not a substitute for least-privilege IAM;
- Lambda must not accept arbitrary operation names or code;
- no model-generated string may become code, shell, AWS CLI, or arbitrary API input;
- policy input must come from the typed tool schema;
- default result for uncertainty/malformed input is DENY/failure;
- public evidence uses aliases only.

---

# 11. Cost / lifecycle guardrails

This should be a very small temporary AWS experiment.

Expected billable surfaces are limited to tiny Gateway/Policy/Lambda/CloudWatch usage. There is intentionally **no model-token spend** for this milestone.

Before creation:

- verify the exact resources to be created;
- verify expected permissions;
- verify Region availability;
- define cleanup before apply;
- use explicit tags/TTL/cleanup metadata consistent with repository practice where supported;
- stop if successful proof requires broad IAM or persistent infrastructure.

One successful ALLOW and one successful DENY proof are enough. Do not loop requests for cosmetic evidence.

---

# 12. NO-GO / hard stop conditions

Stop and report a blocker if:

1. the intended account/profile/Region is unclear;
2. Gateway or Policy is unavailable in the approved account/Region;
3. policy requires a preview/entitlement not already approved;
4. the required policy cannot deterministically inspect the intended structured argument;
5. success requires broad IAM or wildcard AWS workload authority;
6. proving DENY cannot distinguish "policy blocked" from "target failed";
7. the target would need real security/workload data;
8. cleanup cannot be independently verified;
9. implementation starts requiring Harness, LibreChat, Temporal Policy, remote MCP, or another architecture layer;
10. any secret/private AWS identifier would need to be committed.

Do not substitute a different architecture on NO-GO.

---

# 13. What this milestone proves — and does not prove

### After PASS we may claim

> AgentCore Gateway accepted one typed MCP tool surface, AgentCore Policy deterministically allowed one exact argument case and denied another before target execution, the allowed request reached only the narrow Lambda target, the denied request did not, and the dedicated AWS resources were cleaned up.

### Still NOT proven

- Harness -> Gateway integration;
- LibreChat -> Gateway integration;
- human approval / Approve Once;
- Temporal Policy;
- user/RBAC/tenant claims;
- real AWS security findings;
- Inspector / SSM / Config / Security Hub integration;
- remediation;
- production authorization design;
- scale, HA, or enterprise platform behavior.

---

# 14. Logical milestone after this one — not part of this task

Only after both of these are independently proven:

```text
A. Harness tool-use/resume            [Issue #26]
B. Gateway + Policy ALLOW/DENY        [this proposed milestone]
```

consider the next integration:

```text
Harness
 -> AgentCore Gateway
 -> Policy
 -> one narrow read-only tool
```

After that, a later separate milestone may evaluate:

```text
LibreChat ASK
 -> trusted approval event
 -> Temporal Policy
 -> one approved action
```

Real SSM/ASR/Patch remediation comes later.

---

# 15. Instructions for the next ChatGPT thread

Use this file as the planning handoff.

### First action

Read:

- this file;
- `docs/AMIT_BEDROCK_MODEL_AVAILABILITY.md`;
- `docs/kiro-learning-bedrock-ai-models.md`;
- Issue #26;
- Draft PR #27;
- latest repository `AGENTS.md` / README / relevant AgentCore docs.

### Then

1. verify whether Issue #26 / PR #27 is completed, still HOLD, or active;
2. confirm this Gateway/Policy goal does not duplicate another existing Issue;
3. review current official AWS Gateway + Policy docs for any changed names/contracts;
4. keep **exactly one goal**: one tool, one argument-level ALLOW, one argument-level DENY, one evidence path, cleanup;
5. create **one standalone GitHub Issue** containing the bounded implementation contract only when Amit asks to proceed;
6. create **one Draft PR / STRICT planning contract** only if that is still the repository's current collaboration workflow;
7. do not implement until the human HOLD/approval gate is explicit;
8. do not modify Issue #26 / PR #27 to absorb this milestone.

### Suggested Issue title

`POC: prove AgentCore Gateway + Policy ALLOW/DENY on one narrow tool`

### Suggested management/learning sentence

> **The agent model is not the authorization boundary. Gateway Policy decides whether a structured tool request may reach a narrowly permissioned backend.**

---

## Final recommendation

**Do this Gateway + Policy isolation test next, after the Harness inline-tool milestone.**

It is small, cheap, directly relevant to the future Security/Compliance Copilot, and teaches the most important missing control before adding human approval or real remediation.
