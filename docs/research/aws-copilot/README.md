# AWS Copilot research packet

Status: **Architecture Decision v1 accepted — 2026-09-09**

Purpose: preserve the research that graduates the current `mytestlab123/AgentCore` laboratory into a clean, longer-term AWS security copilot without carrying every experiment into the new product.

The research gate is now closed. The current repo remains the R&D/reference repository; the next implementation should begin in a clean long-term repository.

## Current decision

Working/display name: **AWS Copilot**

Recommended short repository name: **`aws-secops`**

Accepted architecture:

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
(prefer tiny Lambda MCP targets first)
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

Read the frozen decision first:

- [ARCHITECTURE_DECISION_V1.md](./ARCHITECTURE_DECISION_V1.md)

Kiro's final deep-review result and accepted corrections are summarized here:

- [KIRO_DEEP_REVIEW_RESULT_2026-09-09.md](./KIRO_DEEP_REVIEW_RESULT_2026-09-09.md)

## Key decisions

1. **Use AgentCore Harness in Singapore now.** Do not wait for a future Harness launch.
2. **Run the clean product in a member dev/sandbox or security-tooling account, not the Organizations management account.**
3. **Put the actual AWS read/remediation operation behind MCP Gateway + Policy.** Prefer small Lambda MCP targets for the first deterministic controls.
4. **Use Organizations + STS + StackSets for scale.** Keep account/OU/Region/role routing server-owned or strictly allowlisted.
5. **Do not build another scanner.** Prefer direct provider state plus Security Hub CSPM, Config, Inspector, Access Analyzer, GuardDuty and other AWS-native evidence as the product grows.
6. **Keep broad AWS Agent Toolkit / AWS MCP as builder tooling.** Production writes remain exact narrow tools behind Gateway Policy + IAM.
7. **Registry-ready, not Registry-dependent.** Singapore Registry is not a first-MVP requirement; an optional Sydney learning catalog may come later when discovery/reuse becomes useful.
8. **Human approval is simple first, policy-visible later.** Existing UI approval is not automatically Temporal Policy history; a later trusted workflow must create the approval event under a non-model identity.
9. **Specialists before Supervisor.** Compliance Agent first, Vulnerability Agent second, manual switching first, A2A Supervisor only when it solves a real usability problem.
10. **Model choice stays replaceable.** Benchmark Nova 2 Lite against one stronger Bedrock/Harness model; Policy + exact tools + IAM remain the security boundary.

## First implementation milestone

Create one cohesive milestone in the future clean repository:

```text
MVP-1 — Clean Compliance SG vertical slice

thin approval UI
 -> Singapore AgentCore Harness
 -> MCP Gateway + stateless exact Policy
 -> exact read Lambda / read identity
 -> exact remediation Lambda / remediation identity
 -> one fixed real Security Group
 -> provider verification
 -> compact audit
```

Use real non-secret provider identity in the private demo. Do not include Registry, StackSets, Temporal Policy, WAF, Memory, Supervisor, Security Hub rollout, or multiple controls in MVP-1.

## Accepted next milestones

1. **MVP-1:** clean single-account Security Group vertical slice.
2. **MVP-2:** 2-3 account STS/Organizations foundation and narrowly scoped StackSet design.
3. **MVP-3:** S3 Block Public Access + EC2 IMDSv2 compliance breadth.
4. **MVP-4:** organization security sources + Inspector/ECR Vulnerability Agent, manual switching.
5. **MVP-5:** trusted policy-visible approval + Temporal Policy `LOG_ONLY` -> `ENFORCE`.
6. **MVP-6:** Registry/discovery and A2A Supervisor only when justified.

## Research history

- [AGENTCORE_ARCHITECTURE.md](./AGENTCORE_ARCHITECTURE.md) — original target architecture research.
- [MVP_ROADMAP.md](./MVP_ROADMAP.md) — original proposed roadmap.
- [DEEP_RESEARCH_2026-09-09.md](./DEEP_RESEARCH_2026-09-09.md) — deep AgentCore/Registry/Organizations/security-services research.
- [KIRO_REVIEW_PROMPT.md](./KIRO_REVIEW_PROMPT.md) — first Kiro review prompt.
- [KIRO_DEEP_REVIEW_PROMPT_2026-09-09.md](./KIRO_DEEP_REVIEW_PROMPT_2026-09-09.md) — final deep-review prompt.
- [KIRO_DEEP_REVIEW_RESULT_2026-09-09.md](./KIRO_DEEP_REVIEW_RESULT_2026-09-09.md) — final accepted Kiro corrections.
- [SOURCES.md](./SOURCES.md) — source inventory.

## R&D -> product rule

Promote the proven **contracts and architecture**, not the historical implementation shape.

Do not automatically migrate:

- custom agent loop;
- separate Gateway-decision-then-AWS-mutation path;
- EC2-hosted remediation MCP server;
- synthetic resource aliases;
- old visual portals/verifiers;
- issue-number-specific compatibility/deployment scripts;
- historical browser proof machinery.

The next durable product artifact is the clean `aws-secops` repository and its MVP-1 Issue/PR.
