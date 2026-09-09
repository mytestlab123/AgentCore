# AWS Copilot research packet

Status: 2026-09-09

Purpose: decide how to graduate the current `mytestlab123/AgentCore` laboratory into a clean, longer-term AWS security copilot without carrying every experiment into the new product.

This packet is **research and architecture guidance only**. It does not create the future repository or authorize new AWS resources.

## Executive recommendation

The current repo has proved enough plumbing. Keep it as the R&D/reference repository. Create the clean long-term product repository only after the current Kiro deep review closes the remaining architecture questions.

Use **AWS Copilot** as a working/display name if it helps communication. For a short long-term repository name, `aws-secops` remains a strong candidate because AWS already used **AWS Copilot CLI** for ECS/Fargate/App Runner.

The recommended product direction is:

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
exact governed tool
(prefer tiny Lambda MCP targets first)
        |
        v
STS AssumeRole
        |
        +--> AWS account A
        +--> AWS account B
        +--> ... 14-50+ accounts
        |
        v
provider verification + audit
```

The critical architectural improvement over the current POC is that the **actual action tool should sit behind Gateway**. Today the POC asks the retained Gateway for an authorization decision and then the EC2-hosted MCP server independently performs the EC2 API action. In the product architecture, the Gateway invocation itself should invoke the governed tool.

## Latest reviewed decisions

The 2026-09-09 deep-research pass adds these decisions:

1. **Harness is already available in Singapore.** Use `ap-southeast-1` for the live MVP control plane now; do not wait for a future launch.
2. **Registry is optional, not blocking.** AWS Agent Registry is currently GA in five Regions and not Singapore. Keep descriptors/IaC Registry-ready; optionally use Sydney later as a catalog learning lab without moving the live runtime.
3. **Do not host the product workload in the Organizations management account.** Use a member security/tooling or sandbox account; keep management-account access for organization/bootstrap administration.
4. **Use Organizations + STS + StackSets for scale.** Central AgentCore execution assumes fixed read/remediation roles in member accounts; service-managed StackSets can distribute those roles across OUs and future accounts.
5. **Do not build another scanner.** Prefer provider-native findings from Security Hub CSPM, Config, Inspector, Access Analyzer, GuardDuty, and direct AWS APIs; differentiate on explanation, human governance, exact remediation, verification, and audit.
6. **Keep builder tooling separate from runtime authority.** AWS Agent Toolkit / broad AWS MCP can accelerate Kiro/Codex development, but production writes remain narrow Gateway-governed tools.
7. **Temporal approval is later.** Existing LibreChat/native approval is not automatically a Policy-visible historical event. A later milestone must represent trusted human approval explicitly in the temporal policy session.

See [DEEP_RESEARCH_2026-09-09.md](./DEEP_RESEARCH_2026-09-09.md) for the reviewed findings and revised milestone sequence.

## Why Harness-first

AWS positions AgentCore Harness as the managed orchestration layer running inside AgentCore Runtime. Harness supplies the agent loop, session isolation, model selection, Gateway integration, skills, memory, observability and execution limits largely through configuration. Runtime remains available when we need custom orchestration, another framework, A2A servers, non-agent workflows, hooks, or code that Harness configuration cannot express.

Recommended rule:

> Start a specialist agent as a Harness. Export to Strands/Runtime only when a concrete Harness limitation appears.

## What "real MVP" means next

The next product should stop using synthetic display identity where provider truth is available. For an approved private lab/account, the UI should be able to show real AWS values returned by provider APIs, for example:

```text
Account ID / friendly alias
Region
EC2 Name tag + instance ID
Security Group name + sg- ID
VPC / subnet IDs where useful
actual provider finding/control
actual requested AWS action
actual verification result
```

Do not hard-code these values merely to look real. Read them from AWS and display them as provider evidence.

The deployed application must not depend on Amit's interactive SSO session. Development/bootstrap can continue using `AWS_PROFILE=amit`; deployed workloads use IAM execution roles and cross-account STS `AssumeRole`.

## Multi-agent direction

Do not begin with autonomous orchestration. First prove two independent specialists:

```text
Compliance Agent
  -> Security Hub / Config / direct provider APIs
  -> Security Groups
  -> S3 Block Public Access
  -> EC2 IMDSv2

Vulnerability Agent
  -> Inspector / ECR
  -> optional Security Agent / Continuum context
  -> real CVE / digest / severity / fix evidence
```

Use manual agent selection/switching first. Introduce a Supervisor using Runtime/A2A only after automatic routing adds clear value.

## Multi-account direction

For 14-50+ accounts, prefer one central Security Copilot / security-tooling member account for the AgentCore control plane rather than deploying the whole agent stack into every member account.

Likely pattern:

```text
central Harness / tool execution role
        |
        | sts:AssumeRole
        v
member-account AwsCopilotReadRole
or narrow AwsCopilotRemediationRole
```

Use Organizations/StackSets to distribute fixed member-account roles to selected OUs. Account/Region/role routing must remain server-owned or allowlisted rather than model-selected.

## Region decision

Singapore (`ap-southeast-1`) is the default live MVP Region because the current AgentCore matrix includes Harness and the core AgentCore capabilities needed by the design.

Current Registry reality:

- AWS Agent Registry is GA in N. Virginia, Oregon, Ireland, Tokyo, and Sydney;
- Singapore is not currently listed;
- organization auto-detection is Region-scoped;
- new Registry automation should use the GA `agent-registry` namespace, not the preview Registry namespace scheduled for retirement on 17 September 2026.

Registry therefore remains a portable discovery/governance layer, not a first-MVP runtime dependency.

## Model decision

Do not make Nova versus another provider an architecture choice. Harness keeps model choice replaceable.

Nova 2 Lite is a sensible low-cost candidate to benchmark. Compare it with one stronger Bedrock/Harness model on actual AWS Copilot tasks:

- correct control interpretation;
- correct tool choice;
- bounded recommendation;
- refusal when evidence is missing;
- correct DENY interpretation;
- correct provider-verification interpretation;
- latency and cost.

Security enforcement remains Gateway Policy + exact tools + IAM regardless of which model performs best.

## Research files

- [AGENTCORE_ARCHITECTURE.md](./AGENTCORE_ARCHITECTURE.md) — original target architecture and native AgentCore components.
- [MVP_ROADMAP.md](./MVP_ROADMAP.md) — original proposed product phases and boundaries.
- [DEEP_RESEARCH_2026-09-09.md](./DEEP_RESEARCH_2026-09-09.md) — reviewed latest AgentCore/Registry/Organizations/security-service addendum and revised milestones.
- [KIRO_REVIEW_PROMPT.md](./KIRO_REVIEW_PROMPT.md) — first independent AWS-native review prompt.
- [KIRO_DEEP_REVIEW_PROMPT_2026-09-09.md](./KIRO_DEEP_REVIEW_PROMPT_2026-09-09.md) — current deep review prompt with read-only Organizations/Registry discovery.
- [SOURCES.md](./SOURCES.md) — original official source inventory; the deep-research addendum contains the additional sources reviewed.

## Current decision gate before creating the new repo

Give Kiro the **deep review prompt** and close these final questions:

1. Which current member account is the best personal MVP security/tooling host, or is a dedicated member account materially better?
2. Is Singapore Harness + MCP Gateway + Policy + exact Lambda tools still the smallest correct vertical slice?
3. Is central AgentCore + STS + StackSets the right 14-50+ account pattern?
4. Should Registry remain deferred, or is a small Sydney catalog experiment worth doing before Singapore Registry exists?
5. Which provider-native security sources should enter milestones 2-4, and which custom scanner logic should never be built?
6. Is there any newer AgentCore/AWS native capability that removes more custom code from the proposed MVP?

After that review, freeze Architecture Decision v1 and create the clean long-term repository.
