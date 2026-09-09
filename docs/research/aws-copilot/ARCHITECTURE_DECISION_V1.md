# AWS Copilot Architecture Decision v1

Status: **ACCEPTED** — 2026-09-09

Purpose: freeze the architecture direction for the clean long-term AWS security/compliance copilot before implementation begins in a new repository.

This decision incorporates the original research packet, the 2026-09-09 deep-research addendum, and Kiro's independent AWS-native review.

## Product direction

Working/display name: **AWS Copilot**

Recommended short repository name: **`aws-secops`**

The current `mytestlab123/AgentCore` repository remains the R&D/reference laboratory. The clean product should selectively promote proven patterns, not copy the experimental tree.

## Target architecture

```text
thin UI / LibreChat initially
        |
        v
AgentCore Harness
  Compliance Agent
        |
        v
AgentCore Gateway (MCP)
        |
AgentCore Policy
        |
        v
exact read/remediation tools
(prefer small Lambda MCP targets first)
        |
        v
STS AssumeRole
        |
        +--> approved AWS member account A
        +--> approved AWS member account B
        +--> ... later 14-50+ accounts
        |
        v
provider verification + compact audit
```

Critical rule:

> The actual AWS action must be the Gateway-governed tool call. Do not reproduce the POC pattern of asking Gateway for permission and then performing a separate application-side AWS mutation.

## 1. Region and hosting

- Use **Singapore (`ap-southeast-1`)** for the live AgentCore MVP control plane.
- AgentCore Harness and the required core AgentCore services are already available in Singapore; do not wait for a future launch.
- Do **not** host the clean product workload in the AWS Organizations management account.
- For the personal MVP, use an existing non-management **dev/sandbox member account** as the default host candidate, subject to a small deployment/access preflight.
- Introduce a dedicated security-tooling member account only when delegated security administration, stronger isolation, or company environment structure makes it useful.

## 2. Harness first

Start the Compliance Agent on **AgentCore Harness**.

Harness owns the standard agent loop, model integration, session isolation, Gateway integration, skills, memory hooks, limits and native observability.

Move to custom Strands/Runtime orchestration only when a concrete requirement needs it, for example:

- custom hooks/orchestration not expressible in Harness;
- non-agent workflows;
- custom framework/protocol needs;
- A2A supervisor behavior;
- substantial reusable server-side tool logic.

## 3. Tool boundary

For the first 2-3 deterministic controls, prefer **small Lambda targets exposed as MCP tools through AgentCore Gateway**.

Initial tool shape:

```text
check_unrestricted_ssh
remove_unrestricted_ssh
```

Prefer separate read and remediation execution identities.

A Runtime-hosted MCP server becomes justified only when shared libraries, richer state, long-running work, custom protocols, or enough reusable logic make a server materially simpler.

Do not use a generic AWS CLI/API mutation tool as the production boundary.

## 4. Organizations and multi-account access

For 14-50+ accounts:

```text
central AgentCore/tooling member account
        |
        +-- sts:AssumeRole --> AwsCopilotReadRole
        |
        +-- sts:AssumeRole --> AwsCopilotRemediationRole
        |
        v
approved member accounts / OUs
```

Rules:

- keep allowed account/OU/Region/role mappings server-owned or strictly allowlisted;
- never let the model provide arbitrary role ARNs, account IDs, Regions, or AWS actions for execution;
- prefer separate read and remediation roles;
- use exact trust relationships and temporary credentials;
- preserve SCPs and other organization guardrails as outer limits;
- use service-managed CloudFormation StackSets when fixed roles/configuration must be distributed across selected OUs and future accounts;
- do not introduce delegated StackSets administration until its broad organization deployment authority is actually needed.

## 5. Provider truth, not another scanner

AWS Copilot should consume authoritative AWS evidence and differentiate on governance and remediation.

Target lifecycle:

```text
provider finding/state
 -> specialist interpretation
 -> recommendation
 -> trusted human decision when mutating
 -> Gateway + deterministic Policy
 -> exact action
 -> provider re-read
 -> verified result + audit
```

Preferred sources by stage:

### MVP

- direct EC2 provider read for unrestricted SSH Security Group state.

### Near-term compliance breadth

- direct S3 Block Public Access state;
- direct EC2 IMDSv2 state;
- AWS Config where a managed rule/remediation adds value;
- Security Hub CSPM after the organization/delegated-admin pattern is intentionally introduced.

### Vulnerability specialist

- Amazon Inspector findings;
- ECR image/digest/CVE evidence;
- optional Security Hub context.

### Later specialists

- IAM Access Analyzer for access analysis;
- GuardDuty/Security Hub for incident/threat workflows;
- AWS Security Agent / AWS Continuum for application/code-security use cases where they add distinct value.

## 6. Human approval and Policy

### First clean MVP

Use the thin client / LibreChat approval experience or a Harness client-side/inline handoff, then invoke the exact MCP remediation tool through stateless Gateway Policy.

Do not claim this UI approval is automatically historical evidence inside Temporal Policy.

### Later policy-visible approval

A stronger AWS-native sequence may use a trusted workflow/backend plus AgentCore Temporal Policy:

```text
detect
 -> trusted human approval
 -> policy-visible approval event
 -> same-resource remediation
 -> provider verification
```

The approval event must be callable only by the trusted human-facing workflow identity, never by the model's normal execution identity.

Step Functions may orchestrate approval/retry/conditions later, while Harness remains the reasoning component. Prove Temporal Policy in `LOG_ONLY` before `ENFORCE`.

## 7. Registry strategy

AWS Agent Registry is useful for cataloging and governance, but it is **not a Singapore MVP dependency**.

Design now so agents/tools/skills are Registry-ready:

```text
AGENTS
  compliance-agent
  vulnerability-agent
  later: security-supervisor

TOOLS
  check-unrestricted-ssh
  remove-unrestricted-ssh
  check-s3-block-public-access
  enforce-s3-block-public-access
  check-imdsv2
  require-imdsv2

SKILLS
  compliance-evidence
  security-hub-triage
  remediation-explanation
  provider-verification
```

Keep descriptors and schemas source-controlled.

Registry Region/IDs/endpoints/bindings remain deployment configuration.

Current decision:

- no Registry dependency in MVP-1;
- optionally run a **small Sydney learning experiment later** when enough agents/tools/skills exist to make catalog discovery useful;
- do not move the Singapore live control plane merely to gain Registry;
- organization auto-detection is Region-scoped, so a Sydney Registry is not an authoritative auto-discovery source for Singapore Runtime/Gateway resources.

## 8. Native AgentCore features to reuse

Prefer native features before custom equivalents:

- Harness agent loop/session isolation;
- Gateway MCP tool aggregation/targeting;
- stateless and later Temporal Policy;
- Gateway rate limiting as a quota control, not an authorization boundary;
- direct AWS WAF association with AgentCore Gateway when a later hardening milestone needs it;
- Observability;
- Evaluations / Optimization after a stable evaluation dataset exists;
- Memory only when the product has a clear durable-context requirement;
- Browser/Code Interpreter only when a use case needs them and the narrow tool boundary remains intact;
- Step Functions `InvokeHarness` only when explicit workflow orchestration/approval adds value;
- A2A only after specialist agents are independently useful.

Broad AWS Agent Toolkit / AWS MCP capability is **builder tooling** for Kiro/Codex and supervised development, not the runtime production write boundary.

## 9. Agent structure

Start with real specialization, not prompt personas.

### Agent 1 — Compliance Agent

Owns compliance configuration/state and exact remediation tools.

Initial controls:

1. Security Group unrestricted SSH;
2. S3 Block Public Access;
3. EC2 IMDSv2.

### Agent 2 — Vulnerability Agent

Owns Inspector/ECR vulnerability evidence and bounded recommendations/actions.

Use manual agent switching first.

Introduce a Supervisor/A2A layer only when manual switching creates a demonstrated usability problem.

Additional specialists are justified only when they have a distinct authoritative data/tool/security boundary.

## 10. Model strategy

Keep the model replaceable.

Benchmark:

- Nova 2 Lite as the low-cost baseline;
- one stronger Bedrock/Harness model with a verified acceptable Singapore/residency path.

Use 10-20 representative AWS Copilot cases and score:

- control interpretation;
- correct tool choice;
- refusal when evidence is absent;
- bounded recommendation;
- DENY interpretation;
- provider-verification interpretation;
- unsafe tool attempts;
- hallucination/evidence fidelity;
- latency and cost.

The model never becomes the authorization boundary.

## 11. Migration strategy

Treat environments as clean deployments, not copies of the personal lab.

```text
personal Organization lab
  -> company non-production Organization
  -> company production Organization
```

Promote:

- source code;
- IaC;
- tool schemas;
- policies;
- skills;
- deterministic tests/evaluations;
- architecture decisions;
- audit contracts.

Recreate per environment:

- workload/execution identities;
- trust policies;
- KMS/logging resources;
- delegated-admin assignments;
- target-account roles;
- Registry records/configuration;
- Security Hub/Inspector/GuardDuty organization configuration;
- endpoints and demo/test resources.

Parameterize Region, organization/OU/account mappings, role names, logical resource selectors, model/routing, Registry Region, audit/log destinations, approval windows and StackSet targets.

## 12. Accepted milestone sequence

### MVP-1 — clean Compliance SG vertical slice

```text
thin approval UI
 -> Singapore Harness
 -> MCP Gateway + stateless exact Policy
 -> exact read Lambda / read identity
 -> exact remediation Lambda / remediation identity
 -> one fixed real Security Group
 -> provider verification
 -> compact audit
```

Show real non-secret provider identity in the private demo.

Do not include Registry, StackSets, Temporal Policy, WAF, Memory, Supervisor or multiple controls in MVP-1.

### MVP-2 — multi-account foundation

- 2-3 approved dev/test accounts;
- fixed STS read/remediation roles;
- server-owned routing;
- account-aware audit;
- narrowly scoped StackSet design.

### MVP-3 — compliance breadth

- S3 Block Public Access;
- EC2 IMDSv2;
- Config where useful;
- provider verification remains mandatory.

### MVP-4 — organization security sources + Vulnerability Agent

- member security-tooling/delegated-admin pattern where needed;
- Security Hub CSPM;
- Inspector/ECR-backed Vulnerability Agent;
- manual agent switching.

### MVP-5 — policy-visible human governance

- trusted approval workflow/event;
- Temporal Policy `LOG_ONLY`;
- wrong/stale/reused/mismatched approval tests;
- then `ENFORCE`.

### MVP-6 — discovery/orchestration only when justified

- Registry learning/catalog if reuse/discovery is now a real problem;
- A2A Supervisor only if manual specialist selection creates measured friction.

## 13. Explicit non-goals for MVP-1

Do not add:

- EKS;
- generic AWS write shell/API tool;
- autonomous multi-agent supervisor;
- Registry dependency;
- custom scanner;
- custom observability platform;
- organization-wide Security Hub/Inspector rollout;
- Temporal Policy;
- WAF hardening;
- many controls;
- migration of historical POC portals/scripts/browser proof machinery.

## Decision consequence

Architecture research is now sufficient to begin the clean product repository.

The next implementation artifact should be one Issue + one PR in the new repository for **MVP-1 — Clean Compliance SG vertical slice**.
