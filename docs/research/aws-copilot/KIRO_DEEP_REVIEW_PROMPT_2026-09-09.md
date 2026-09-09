# Kiro deep architecture review prompt — AWS Copilot

Copy/paste the block below into Kiro after pulling current `main`.

---

You are the **AWS-native independent architecture reviewer** for the next phase of a project currently developed in `mytestlab123/AgentCore`.

The working product name is **AWS Copilot**. The likely future long-term repository is a clean `amitkarpe/*` repository such as `aws-secops`; do not create it yet.

## Objective

Challenge the latest AWS Copilot architecture research using current AWS documentation, release notes, blogs, service behavior, and—where useful—**read-only discovery** of Amit's personal AWS Organization.

Do not implement anything.

## Read first

Read these files completely from current `main`:

1. `docs/research/aws-copilot/README.md`
2. `docs/research/aws-copilot/AGENTCORE_ARCHITECTURE.md`
3. `docs/research/aws-copilot/MVP_ROADMAP.md`
4. `docs/research/aws-copilot/DEEP_RESEARCH_2026-09-09.md`
5. `docs/research/aws-copilot/SOURCES.md`

Treat the old repo as R&D evidence, not as an implementation that must be preserved.

## Current project assumptions

- Personal AWS access uses `AWS_PROFILE=amit`.
- This profile is in Amit's AWS Organizations management account and currently has broad administrative access.
- Registry permissions that were previously missing are now expected to be fixed.
- Amit's personal AWS Organization has management/member accounts and dev/prod/test OU structure suitable for learning the future multi-account pattern.
- The clean MVP should not deploy its product workload in the Organizations management account unless current AWS guidance gives a compelling exception.
- The future private product/demo is allowed to show real provider identity: AWS account ID/alias, Region, EC2 instance name/ID, Security Group name/ID, finding ID, and other non-secret resource identifiers.
- Never expose or commit credentials, tokens, passwords, private keys, session credentials, or secrets.
- Production/company account details are not available in this personal lab; design for later clean redeployment into company non-production and production Organizations.

## Read-only AWS discovery allowed

You MAY run direct read-only AWS CLI commands using `AWS_PROFILE=amit` where they materially improve the review.

Examples of useful read-only checks:

- STS caller identity;
- Organizations roots, OUs, accounts, delegated administrators, and trusted access;
- CloudFormation StackSets inventory/status;
- current AgentCore Harness/Runtime/Gateway/Policy resources;
- AWS Agent Registry access/current registries in supported Regions;
- Security Hub / Inspector / IAM Access Analyzer / Config organization/delegated-admin state;
- current Region/service availability where the CLI can prove it safely.

Use direct AWS CLI first. No Python/SDK wrapper for simple inspection.

Do not create, update, delete, enable, disable, deploy, register, delegate, assume a mutation role, reset a resource, or change AWS configuration.

Do not create/update GitHub repositories, Issues, PRs, branches, or files.

## Questions to answer

### 1. Singapore reality

Verify current official support in `ap-southeast-1` for:

- AgentCore Harness;
- Runtime;
- Gateway;
- Identity;
- Policy;
- Temporal Policy;
- Observability;
- Evaluations / Optimization;
- built-in tools;
- AWS WAF integration with Gateway where relevant;
- AWS Agent Registry.

Confirm the research claim that Harness is already available in Singapore.

If Registry is still unavailable in Singapore, state that clearly. Do not predict a Singapore launch date unless AWS has officially announced one.

### 2. Registry plan

Review the proposed **Singapore live control plane + optional Sydney Registry learning lab**.

Check:

- current Registry GA Regions;
- new `agent-registry` namespace and the 17 September 2026 preview-namespace retirement;
- record types: MCP, Agent/A2A, Agent Skill, custom;
- approval/search/MCP endpoint/RAM/EventBridge/CloudTrail capabilities;
- organization-scoped auto-detection;
- exactly which AgentCore resources auto-detection currently discovers;
- whether auto-detection is Region-scoped;
- whether Singapore Runtime/Gateway resources can or cannot be auto-detected by a Sydney Registry;
- best way to keep record/descriptors/IaC portable so Registry Region can change later.

Decide whether we should:

A. ignore Registry until Singapore support;
B. create a small Sydney Registry learning experiment later;
C. use Sydney Registry as an active catalog while the runtime stays Singapore;
D. use another pattern.

Do not create a Registry during this review.

### 3. AWS Organizations architecture

Inspect the current personal Organization read-only if useful.

Challenge this target pattern:

```text
Organizations management account
  -> organization/bootstrap/delegation only

member security-tooling account
  -> AgentCore Harness
  -> Gateway / Policy
  -> exact tools
  -> STS AssumeRole
  -> target member accounts
```

Answer:

- Should AWS Copilot run in a dedicated member account rather than the management account?
- For Amit's current personal Organization, should the first MVP reuse an existing member/sandbox account or would a dedicated tooling account be materially better?
- Which AWS services should use delegated administrator accounts later?
- Is central AgentCore + target-account STS still the simplest 14–50+ account design?
- Should read and remediation use separate execution roles and separate member-account roles?
- How should we prevent confused-deputy / arbitrary-account / arbitrary-role routing?
- Which Organizations metadata should be server-owned versus model-selected?

### 4. StackSets / account onboarding

Verify whether service-managed CloudFormation StackSets with Organizations are the right KISS mechanism to deploy fixed roles/config to OUs and future accounts automatically.

Review:

- delegated StackSets administrator tradeoffs;
- auto-deployment to accounts entering OUs;
- appropriate scope for `AwsCopilotReadRole` and `AwsCopilotRemediationRole`;
- whether a simpler Organizations-native mechanism now exists.

### 5. Do not rebuild AWS scanners

Challenge the proposal that AWS Copilot should consume authoritative provider findings rather than build its own broad compliance/vulnerability scanning engine.

Assess these sources:

- Security Hub CSPM central configuration/findings;
- AWS Config managed rules/conformance packs/remediation;
- Amazon Inspector ECR/EC2/Lambda findings;
- IAM Access Analyzer;
- GuardDuty;
- AWS Security Agent / AWS Continuum;
- direct AWS provider APIs for fast deterministic controls.

For each, say whether it belongs in:

- MVP;
- next 1–3 milestones;
- later;
- defer.

Important: determine whether AWS Security Agent/Continuum complements or replaces any planned Vulnerability specialist functions. Do not overclaim overlap with Inspector infrastructure findings.

### 6. Latest AgentCore-native shortcuts

Search current AWS AgentCore release notes, AWS What's New, AWS blogs, official examples, and AWS GitHub repositories for features that could delete custom code or improve the governance design.

Specifically check:

- Harness additions;
- Gateway target types;
- Lambda MCP targets;
- Runtime-hosted MCP;
- special Runtime target behavior;
- Policy/stateless/Temporal Policy;
- Gateway rate limiting;
- WAF on Gateway;
- Memory;
- Browser / Code Interpreter / built-in tools;
- Observability;
- Evaluations / Optimization;
- Step Functions + AgentCore agentic workflows / human approval if now relevant in Singapore;
- A2A / multi-agent support;
- Registry;
- any capability launched after the existing research packet.

Identify exact POC plumbing that should **not** be promoted because AgentCore now supplies the capability natively.

### 7. Agent Toolkit, skills, and MCP

Review the current Agent Toolkit for AWS:

- AWS MCP Server;
- 15,000+ AWS APIs claim;
- 40+ skills;
- Kiro/Codex/Claude Code/Cursor integration;
- security/DevSecOps skills/plugins relevant to this project.

Decide which should accelerate **development** versus which should be part of the **runtime product**.

Treat a broad AWS MCP mutation surface as suspect for production. The proposed product boundary is exact narrow MCP tools behind Gateway Policy.

### 8. Tool target architecture

Re-evaluate:

```text
Harness
  -> MCP Gateway
  -> Policy
  -> exact Lambda MCP tool
  -> STS AssumeRole
  -> AWS API
  -> provider verification
```

For the first controls, compare:

- Lambda target transformed to MCP;
- Runtime-hosted MCP server;
- special AgentCore Runtime target;
- SSM Automation / managed remediation where applicable;
- any newer native target.

Recommend the smallest correct default.

### 9. Human approval / Temporal Policy

The current R&D LibreChat ASK/Approve event is **not assumed to be automatically visible to AgentCore Temporal Policy**.

Find the most AWS-native design now for:

```text
detect
  -> trusted human approval
  -> same-resource remediation
  -> verify
```

Clarify:

- Harness client-side/inline tool support;
- how approval becomes a Policy-visible event;
- how to prevent the model from self-issuing the approval event;
- authenticated principal/session design;
- same-resource correlation;
- freshness/expiry;
- same-account/same-Region requirements;
- `LOG_ONLY` -> `ENFORCE` rollout.

### 10. Agent structure

Review this sequence:

1. Compliance Agent;
2. Vulnerability Agent;
3. manual agent switching;
4. A2A Supervisor only later.

Recommend additional specialists only if they have a distinct data/tool/security boundary, for example:

- IAM/Access specialist;
- Network/WAF specialist;
- Data/S3 specialist;
- Incident/operations specialist.

Do not recommend a multi-agent swarm merely because AWS supports it.

### 11. Model strategy

Review Nova 2 Lite as a low-cost baseline candidate, not an assumed winner.

Recommend one stronger comparison model/path available through Harness/Bedrock with attention to Singapore/cross-Region inference/data-residency implications.

Propose a small benchmark using the actual AWS Copilot tasks.

The model must never become the security boundary.

### 12. Personal -> company migration

Recommend a clean migration pattern:

```text
personal Organization lab
  -> company non-production Organization
  -> company production Organization
```

We want to promote:

- source code;
- IaC;
- policies;
- tool schemas;
- skills;
- tests/evaluations;
- architecture decisions.

We do not want to copy personal AWS identities/resources into company environments.

Explain what must be parameterized and what should be recreated cleanly in each environment.

### 13. First 3–6 milestones

Challenge the proposed sequence:

1. clean single-account Compliance SG vertical slice;
2. Organizations / 2–3 account STS foundation;
3. Security Hub + S3 BPA + IMDSv2;
4. Vulnerability specialist using Inspector/ECR + optional Security Agent/Continuum context;
5. Policy-visible human approval + Temporal Policy;
6. Registry/discovery and A2A Supervisor only when justified.

Recommend the best order and identify the **single first implementation milestone** for the future clean repository.

## KISS constraints

- Research/review only.
- No AWS writes.
- No GitHub writes.
- No EKS unless a concrete requirement makes it clearly simpler.
- No generic AWS write shell/API tool.
- No custom scanner when AWS provider truth is adequate.
- No custom observability platform before native AgentCore observability is insufficient.
- No Registry dependency for the first Singapore MVP.
- No Supervisor before two specialists are independently useful.
- Direct AWS CLI first for any allowed read-only discovery.

## Required output

Return exactly this decision-oriented structure:

```text
RESULT=ACCEPT|CHANGE

TOP_DECISIONS=
- ...

NEW_NATIVE_FEATURES=
- ...

REGION_REALITY=
- ...

REGISTRY_PLAN=
- ...

ORGANIZATIONS_ARCHITECTURE=
- ...

AGENT_TOOL_SKILL_CATALOG=
- ...

HUMAN_APPROVAL_POLICY=
- ...

MODEL_PLAN=
- ...

MIGRATION_PLAN=
- ...

FIRST_MILESTONE=
- ...

NEXT_3_TO_6_MILESTONES=
- ...

RISKS=
- maximum 7 concrete risks
```

For every material correction or new feature, include the current official AWS source URL.

If you perform read-only AWS discovery, add a final compact section:

```text
AWS_READ_ONLY_EVIDENCE=
- profile/Region used
- Organizations facts materially relevant to architecture
- Registry access/result by Region
- delegated-admin/service state that changes a decision
```

Do not paste credentials or secrets. Real non-secret AWS identifiers may be reported in this private review when they materially support the architecture decision, but do not commit them to the public R&D repository.

---
