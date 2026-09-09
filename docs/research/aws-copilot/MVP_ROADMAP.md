# AWS Copilot — proposed MVP roadmap

Status: 2026-09-09

This is a **proposed sequence**, not an approved implementation plan. Kiro should challenge it before the new long-term repository is created.

## Working principle

The experimental repo has already proved the governance mechanism. The next product should prove that the same mechanism can govern **real specialist agents operating on real AWS resources across multiple accounts**.

Do not re-prove every old experiment. Promote only the patterns that survived:

- native human approval for controlled actions;
- Gateway + Policy as a hard authorization boundary;
- exact action/target policy context;
- real provider reads and verification;
- DENY/Reject = no backend mutation;
- AWS CLI first for simple operator work;
- repeatable lifecycle helpers only when repetition is real;
- one compact audit story.

## Phase 0 — architecture decision packet

Outcome: decide the clean product architecture before creating another repository.

Work:

- review this packet with Kiro;
- confirm AgentCore Harness/Runtime/Gateway/Policy regional support in Singapore;
- confirm the smallest supported target for one exact AWS remediation tool;
- confirm multi-account STS role pattern;
- choose a short working repo name;
- identify what **not** to migrate from `mytestlab123/AgentCore`.

No AWS mutation required.

## Phase 1 — clean real-resource Compliance MVP

Goal: one clean end-to-end real AWS control in the future product repository.

Target flow:

```text
LibreChat
  -> Compliance Agent on AgentCore Harness
  -> Gateway + Policy
  -> exact MCP tool target
  -> one real AWS account/resource
  -> provider verification
```

Required product truth:

- show actual AWS account ID and friendly alias where available;
- show actual Region;
- show actual EC2 Name/instance ID when the control is tied to an instance;
- show actual Security Group name/ID;
- no `web-01` or `demo-security-group` presentation alias unless it is genuinely the provider resource name;
- no personal SSO dependency in the deployed path.

First control remains unrestricted SSH because it is fast, deterministic and already understood.

Architecture checkpoint:

> The actual `remove_unrestricted_ssh` action must be a Gateway-governed MCP tool, not an application-side AWS call performed after a separate Gateway permission check.

Done when one real resource can be detected, approved, policy-authorized, changed exactly once and verified using the clean architecture.

## Phase 2 — cross-account foundation

Goal: prove the same Compliance Agent against more than one AWS account without human SSO switching.

Start with 2-3 approved lab/member accounts, not all 50.

Add:

- central Harness/tool execution identity;
- fixed member-account read role;
- narrow remediation role where required;
- account inventory/display with real account ID + alias;
- explicit target-account selection or server-owned routing;
- account-aware audit evidence.

Use STS `AssumeRole`. Do not distribute access keys.

Done when the same agent/tool contract works against at least two accounts with clear identity/audit and no code fork per account.

## Phase 3 — Compliance Agent breadth

Goal: show that the architecture is reusable across several controls.

Recommended order:

1. Security Group unrestricted SSH;
2. S3 Block Public Access;
3. EC2 IMDSv2;
4. AWS Config corroboration where it adds evidence;
5. WAF control only after the first three are stable.

Every control should implement the same contract:

```text
provider read
 -> deterministic finding
 -> explanation/recommendation
 -> ASK for mutation
 -> Gateway/Policy exact action
 -> exact tool action
 -> provider re-read
 -> final state/audit
```

Avoid building a generic unrestricted AWS command tool.

Done when a user can ask the Compliance Agent about 2-3 distinct controls and the governance behavior stays consistent.

## Phase 4 — Vulnerability Agent

Goal: introduce the second specialist without supervisor complexity.

Use:

- real ECR repository/image digest;
- existing Inspector finding data;
- real CVE/severity/fix evidence;
- bounded recommended action.

Do not make the live presentation wait for a fresh Inspector scan. Prepare or retain an image with already-available findings.

The Vulnerability Agent may initially be read/recommend only if the clean remediation path would add disproportionate complexity. If a mutation is added, it must use the same Gateway/Policy/exact-tool pattern.

Done when LibreChat can manually switch between:

- **Compliance Agent**;
- **Vulnerability Agent**;

and each has a clearly different tool/skill scope while sharing the same governance philosophy.

## Phase 5 — temporal governance

Goal: move from "this individual action is allowed" to "this safe sequence occurred before the action".

Evaluate AgentCore temporal policies for a session-aware rule such as:

```text
real detect
 -> recorded human approval
 -> same-resource remediation
 -> verification
```

Also consider:

- approval freshness window;
- maximum remediation count per session;
- matching the remediation target to the earlier finding/approval target.

Keep the Gateway and AgentCore targets participating in the temporal chain in the same central account and Singapore Region because current temporal-session propagation does not cross AgentCore account/Region boundaries.

Done when an out-of-order or mismatched sequence is denied by Policy rather than by application conventions alone.

## Phase 6 — Supervisor / A2A orchestration

Goal: automate specialist selection only after specialists are independently useful.

Potential architecture:

```text
User
  -> Security Supervisor
       -> Compliance Agent
       -> Vulnerability Agent
```

Use AgentCore Runtime/A2A when the Supervisor genuinely needs agent-to-agent discovery/delegation. Keep actual AWS mutations behind the MCP Gateway/Policy path.

Initial supervisor responsibility should be small:

- classify request;
- route to exactly one specialist;
- optionally combine read-only summaries.

Do not begin with a large autonomous swarm.

Done when routing adds user value without weakening specialist tool boundaries or governance evidence.

## Phase 7 — operational maturity before broader rollout

Goal: make behavior measurable before expanding to many users/accounts.

Use native AgentCore features first:

- Harness/Runtime observability and traces;
- CloudTrail;
- AgentCore Evaluations for representative tasks and failure cases;
- versioned Harness endpoints and rollback;
- cost/iteration/token limits;
- CI deployment through GitHub/GitLab OIDC rather than static AWS credentials.

Then gradually expand account onboarding.

AWS Agent Registry becomes relevant when enough approved agents/tools/skills exist that discovery and reuse are a real problem. Because Registry is not currently GA in Singapore, decide deliberately whether a cross-region registry is worth the operational/data-governance tradeoff.

## Model benchmark track

Run this in parallel with Phase 1 rather than block architecture on model preference.

Candidate baseline:

- Nova 2 Lite for cost-efficient operation;
- one stronger comparison model through Harness.

Use 10-20 fixed test cases drawn from real product tasks:

- identify unrestricted SSH from provider data;
- distinguish compliant/non-compliant state;
- select the correct read versus remediation tool;
- refuse/infer nothing when AWS evidence is missing;
- explain a Config/S3/IMDSv2 control;
- summarize an existing ECR/Inspector finding;
- produce the exact bounded recommendation;
- interpret DENY and provider verification correctly.

Measure correctness, tool selection, hallucination rate, latency and cost. Do not grant a model broader IAM because it performs better in the benchmark.

## What should not enter the first clean repo

Do not automatically migrate:

- issue-number-specific compatibility code from the R&D repo;
- old synthetic portals kept only for earlier proofs;
- multiple overlapping browser frameworks;
- FAST deployment experiments;
- RAG/vector database;
- EKS merely to host the agent;
- generic AWS CLI/shell write capability;
- dozens of controls;
- autonomous multi-agent routing;
- Registry integration before it solves a real discovery problem;
- historical proof scripts that no longer support the clean architecture.

## Suggested first implementation milestone after Kiro review

One Issue + one PR in the future product repo:

> **Clean Compliance Agent: Harness -> Gateway Policy -> real SG tool -> provider verification**

Keep the milestone to one useful outcome, but include the related architecture pieces needed for it to be genuinely clean: Harness deployment, exact Gateway target, workload IAM identity, real resource display and one provider-verified SG lifecycle.
