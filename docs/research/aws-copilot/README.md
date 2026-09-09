# AWS Copilot research packet

Status: 2026-09-09

Purpose: decide how to graduate the current `mytestlab123/AgentCore` laboratory into a clean, longer-term AWS security copilot without carrying every experiment into the new product.

This packet is **research and architecture guidance only**. It does not create the future repository or authorize new AWS resources.

## Executive recommendation

The current repo has proved enough plumbing. Keep it as the R&D/reference repository. For the next product phase, create a clean repo under `amitkarpe/*` only after Kiro independently reviews this packet.

Use **AWS Copilot** as a working product name if it helps communication, but be aware that AWS already used the name **AWS Copilot CLI** for ECS/Fargate/App Runner; that CLI reached end of support on 12 June 2026. A public or long-lived repository may therefore eventually benefit from a less ambiguous name such as `aws-secops`, `aws-secops-copilot`, or `secops-copilot`. Naming should not block architecture work.

The recommended product direction is:

```text
LibreChat or another thin UI
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
exact governed tool target
(Lambda or Runtime-hosted MCP tool)
        |
        v
STS AssumeRole
        |
        +--> AWS account A
        +--> AWS account B
        +--> ... 14-50+ accounts
```

The critical architectural improvement over the current POC is that the **actual action tool should sit behind Gateway**. Today the POC asks the retained Gateway for an authorization decision and then the EC2-hosted MCP server independently performs the EC2 API action. In the product architecture, the Gateway invocation itself should invoke the governed tool. This removes the split between "check policy" and "do AWS action".

## Why Harness-first

AWS now positions AgentCore Harness as the managed orchestration layer running inside AgentCore Runtime. The harness supplies the agent loop, session isolation, model selection, Gateway integration, skills, memory, observability and execution limits largely through configuration. Runtime remains available when we need custom orchestration, a custom framework, A2A servers, non-agent workflows, hooks, or code that Harness configuration cannot express.

Recommended rule:

> Start a specialist agent as a Harness. Export to Strands/Runtime only when a concrete Harness limitation appears.

AWS supports exporting a working Harness to editable Strands Python code, so starting managed does not lock the project into configuration forever.

## What "real MVP" means next

The next product should stop using synthetic display identity where provider truth is available. For an approved lab/account, the UI should be able to show the real AWS values returned by provider APIs, for example:

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

The deployed application should also stop depending on Amit's interactive SSO session. Development can continue using `AWS_PROFILE=amit`; the deployed solution should use workload IAM roles and, for other AWS accounts, narrow cross-account STS `AssumeRole` roles.

## Multi-agent direction

Do not begin with autonomous orchestration. First prove two independent specialists:

```text
Compliance Agent
  -> Security Groups
  -> S3 Block Public Access
  -> EC2 IMDSv2
  -> Config corroboration / WAF later

Vulnerability Agent
  -> ECR
  -> existing Inspector findings
  -> image digest / CVE / fix evidence
```

Use manual agent selection/switching first. After both specialists work independently with the same governance layer, introduce a Supervisor using AgentCore Runtime/A2A if automatic routing adds clear value.

## Multi-account direction

For 14-50+ accounts, prefer one central Security Copilot / security-tooling account for the AgentCore control plane rather than deploying the whole agent stack into every member account.

A likely pattern is:

```text
central Harness / tool execution role
        |
        | sts:AssumeRole
        v
member-account AwsCopilotReadRole
or narrow AwsCopilotRemediationRole
```

The member account role remains subject to its own IAM policies, SCPs and other organization guardrails. This is standard AWS cross-account role delegation and does not require a human SSO session at runtime.

## Region decision

Singapore (`ap-southeast-1`) is a good default for this MVP because AgentCore Harness, Runtime, Gateway, Identity, Policy, Observability, Evaluations and temporal policies are supported there, and VPC connectivity is supported in documented Singapore Availability Zones.

Two current regional limitations matter:

- AWS Agent Registry is GA in five regions only (Oregon, N. Virginia, Ireland, Tokyo and Sydney), not Singapore. Defer it or make a deliberate regional design later.
- Guardrails inside AgentCore Policy are currently not supported in Singapore. Do not make that feature an MVP dependency.

Temporal Policy is supported in Singapore, but its policy-session propagation does not cross AgentCore account/Region boundaries. This favors keeping the Harness/Gateway/Runtime policy chain together in the same central account and region, while the governed tool uses normal STS to operate on target AWS accounts.

## Model decision

Do not make Nova versus OpenAI an architecture choice. Harness can use Bedrock, OpenAI, Gemini and LiteLLM-compatible providers and can switch provider between turns.

Nova 2 Lite is a sensible low-cost candidate to benchmark, but AWS describes it as a cost-efficient model for simpler automation/document/support work. Nova Premier is positioned for more complex reasoning and agentic workflows. Therefore, do not assume an Amazon model is automatically better at AWS operations.

Use a small benchmark of our actual tasks: identify a control, select the correct tool, explain the risk, produce the bounded recommendation, and interpret the AWS response. Security enforcement must remain in Gateway Policy + IAM regardless of which model wins.

## Research files

- [AGENTCORE_ARCHITECTURE.md](./AGENTCORE_ARCHITECTURE.md) — target architecture and native AgentCore components.
- [MVP_ROADMAP.md](./MVP_ROADMAP.md) — recommended product phases and boundaries.
- [KIRO_REVIEW_PROMPT.md](./KIRO_REVIEW_PROMPT.md) — copy-friendly independent AWS-native review prompt.
- [SOURCES.md](./SOURCES.md) — official sources used for this research.

## Decision gate before creating the new repo

Ask Kiro to challenge this packet. Create the clean long-term repository only after we have answers to these four questions:

1. Is Harness-first the fastest correct path for the first Compliance Agent?
2. What is the smallest AgentCore-native way to put the **actual** remediation tool behind Gateway Policy?
3. Is central-account AgentCore + member-account STS roles the right design for our 14-50+ account environment?
4. Which AgentCore features should be deliberately deferred because of Singapore support, complexity or lack of demonstrated need?
