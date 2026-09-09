# AWS Copilot — AgentCore target architecture research

Status: 2026-09-09

This document separates **AWS-documented capability** from the **recommended architecture** for the next AWS Copilot MVP.

## 1. What the current POC proves

The current `mytestlab123/AgentCore` implementation has real AgentCore involvement:

```text
LibreChat on EC2
      |
      v
repo-owned MCP server
      |
      +--> retained AgentCore Gateway + Policy
      |       exact ALLOW / DENY tuple
      |
      +--> EC2 AWS API
              DescribeSecurityGroups
              RevokeSecurityGroupIngress
```

M8/M9-M13 proved a real Security Group control, native human approval, an exact Gateway/Cedar tuple, hard DENY cases with no backend execution, a real AWS revoke, provider verification, and a safe COMPLIANT no-op.

The remaining architectural weakness is intentional POC plumbing: **Gateway authorizes first, then the EC2-hosted MCP code makes the AWS action separately**. The product architecture should make the actual AWS action the governed Gateway tool.

## 2. AgentCore mental model

### Harness — managed agent loop

AWS documents Harness as a managed agent harness powered by Strands and backed by AgentCore Runtime. You configure the model, system instructions, tools, skills, memory, limits and environment; AgentCore operates the orchestration loop.

Harness already supports, largely by configuration:

- Bedrock, OpenAI, Gemini and LiteLLM-compatible models;
- provider switching between turns;
- AgentCore Gateway;
- remote MCP tools;
- Agent Skills;
- Memory;
- Browser and Code Interpreter;
- session isolation;
- VPC networking;
- observability;
- versioned immutable configurations and endpoints.

Each session runs in an isolated Runtime microVM.

**Recommendation:** use Harness for the first Compliance Agent. Do not begin with a custom agent framework unless a concrete requirement needs it.

### Runtime — managed compute for code we own

AgentCore Runtime is the lower-level hosting service. We bring the agent/tool code and own the orchestration logic. Runtime supports HTTP, MCP, A2A and AG-UI service contracts and works with multiple frameworks/models.

Runtime has two relevant compute choices:

| Choice | Best fit | Session model |
| --- | --- | --- |
| microVM | lightweight API-driven agent/tool, serverless scaling | isolated, up to 8 hours |
| Instances | long-running/stateful/collaborative work, GPUs | AWS-managed EC2 in our account, up to 14 days, multiple agents can share a session |

**Recommendation:** default to Harness/microVM for the MVP. Use Runtime microVM for custom MCP/A2A code when needed. Do not choose Runtime Instances merely because the current POC runs on EC2; Instances solve long-running/stateful/multi-agent compute needs that we do not yet have.

### Gateway — governed front door, not a notification bus

AWS describes Gateway as a managed AI gateway connecting agents to tools, other agents and LLMs. It supports:

- MCP targets: Lambda, API Gateway/OpenAPI/Smithy, MCP servers and connectors;
- HTTP targets: including AgentCore Runtime agents and other HTTP services;
- inference targets for model routing;
- inbound authentication and per-target outbound credentials.

For our security actions, the important category is **MCP tools**. Current AgentCore Policy evaluation applies to MCP tools, so the strongest MVP pattern is to expose exact security operations as MCP tools behind Gateway rather than use an HTTP passthrough path for the critical mutation.

### Policy — deterministic authorization outside the model

Policy in AgentCore evaluates Gateway tool calls independently from agent/model logic. The current POC already proves point-in-time Cedar conditions such as exact environment/action/target.

Temporal policies extend this to session history. They can require previous events, rate/count limits, time windows and ordering. For a later security milestone, this is a good fit for rules such as:

```text
read/detect resource
      -> approval event
      -> exact remediation
      -> verification
```

Temporal policies are supported in Singapore. Important constraint: AgentCore temporal-session propagation does not cross AWS account or Region boundaries between Gateway/Runtime components. Keep the AgentCore policy-visible chain together in one account/Region.

### Identity — workload identity, not Amit's SSO

Harness runs with an IAM execution role. Runtime and Gateway also integrate with AgentCore Identity/workload identities. This is the correct production identity model.

Development:

```text
Amit laptop / Codex / Kiro
      -> AWS_PROFILE=amit
      -> SSO session
```

Deployed product:

```text
Harness / tool runtime execution role
      -> AWS IAM / STS
      -> target resource/account
```

The deployed agent should never require Amit's active SSO login.

### Skills — domain knowledge, not authorization

Harness can load AWS Skills from the AWS Agent Toolkit, Git, S3 or the filesystem. AWS's curated skills include core AWS services, operations/troubleshooting, analytics and storage.

**Recommendation:** use curated AWS skills to improve AWS domain understanding and reduce prompt/tool-description reinvention, but do not let broad skills become the mutation boundary. Real changes should still be exposed as narrow Gateway-governed tools with deterministic Policy/IAM controls.

### Registry — useful later, region-sensitive now

AWS Agent Registry is a private governed catalog for agents, MCP servers/tools, skills and custom resources. It adds approvals, semantic/keyword search, CloudTrail, RAM sharing and organization-wide discovery; it can auto-detect AgentCore Runtime agents and Gateways across an organization.

Current GA regions are Oregon, N. Virginia, Ireland, Tokyo and Sydney. Singapore is not listed. It should therefore be a later platform decision, not an MVP dependency.

### Observability and Evaluations

Harness/Runtime integrate with AgentCore observability, and Evaluations can score agent/tool behavior using built-in or custom evaluators. These are useful before broad rollout across many accounts.

**Recommendation:** keep observability from the start because it is native and low-friction. Introduce formal Evaluations after the first agent/tool behavior stabilizes; do not build a new custom observability platform.

## 3. Recommended product architecture

### Phase-one architecture

```text
User
 |
 v
LibreChat (initial UI)
 |
 v
Compliance Agent — AgentCore Harness
 |
 | MCP tool discovery/call
 v
AgentCore Gateway (central security-tooling account, ap-southeast-1)
 |
 +--> AgentCore Policy (Cedar exact action/target)
 |
 v
Exact MCP tool target
  option A: Lambda target for a very small operation
  option B: Runtime-hosted MCP server for richer reusable tooling
 |
 v
STS AssumeRole
 |
 +--> Member account A role
 +--> Member account B role
 +--> Member account C role
      ...
 |
 v
AWS provider API
 |
 v
Provider verification result returned through the same governed path
```

### Why actual tools should be behind Gateway

Current POC:

```text
MCP code -> Gateway "may I?" -> ALLOW -> MCP code separately calls AWS
```

Target:

```text
Harness -> Gateway -> Policy -> governed tool -> AWS
```

Benefits:

- the operation being authorized is the operation being invoked;
- fewer custom trust assumptions;
- one canonical audit path;
- easier to apply exact Cedar/temporal rules;
- fewer ways for application code to bypass the policy path.

For simple, fixed AWS operations, a Lambda Gateway target is attractive because the tool can be tiny and independently permissioned. When the tool set needs shared libraries, richer logic, MCP-native discovery or A2A behavior, Runtime-hosted MCP code becomes more appropriate.

## 4. Multi-account access pattern

For 14-50+ accounts, use a central security-tooling account for AgentCore and narrow roles in each member account.

Example:

```text
Central account
  AwsCopilotComplianceToolRole
        |
        | sts:AssumeRole
        v
Member account
  AwsCopilotReadRole
  AwsCopilotRemediationRole   # only where approved
```

Design rules:

- use separate read and remediation permission sets if that improves approval/governance clarity;
- target roles trust only the central workload role/account as narrowly as practical;
- central role has `sts:AssumeRole` only for approved role names/accounts;
- member-role permissions remain narrow by AWS service/action/resource;
- SCPs and other organization controls continue to bound the effective permissions;
- do not distribute long-lived keys or user SSO credentials.

AWS Organizations recommends account boundaries and centralized security tooling as foundational patterns; cross-account IAM roles are AWS's primary general mechanism when a service/resource does not expose a suitable resource-based policy.

## 5. Real resource identity

The next product phase may show exact provider identity rather than synthetic aliases, because Amit has explicitly allowed it for the real demo.

Read these values at runtime rather than store them as presentation constants:

- STS account ID;
- account alias when configured and available;
- Region;
- EC2 Name tag + instance ID;
- Security Group GroupName + GroupId;
- VPC/Subnet IDs where useful;
- ECR repository + image digest;
- real finding/control ID.

Treat account alias as convenience metadata; account ID remains the authoritative account identifier.

## 6. Specialist agents before supervisor orchestration

### Compliance Agent

Good early deterministic controls:

1. unrestricted SSH Security Group;
2. S3 Block Public Access;
3. EC2 IMDSv2;
4. AWS Config as corroboration where useful;
5. WAF control later.

Each control should reuse one lifecycle contract:

```text
detect -> explain -> human decision when mutating -> Gateway Policy -> exact tool -> verify
```

### Vulnerability Agent

Use real ECR and existing Inspector findings. Do not make the presentation wait for a fresh Inspector scan.

```text
existing ECR image
    -> existing Inspector finding
    -> actual digest/CVE/severity/fix evidence
    -> bounded recommendation/action
```

### Supervisor later

After both agents work independently, consider a Runtime-hosted A2A Supervisor. Runtime supports A2A and agent cards for discovery. Gateway can front Runtime agents as HTTP targets for centralized access, but remember the current Policy hard-enforcement path is centered on MCP tools; keep actual mutating tools behind the governed MCP Gateway path.

## 7. Singapore constraints that affect architecture

Use `ap-southeast-1` as the MVP control-plane region unless an organizational requirement says otherwise.

Supported there today:

- Harness;
- Runtime;
- Gateway;
- Identity;
- Policy;
- Observability;
- Evaluations;
- VPC connectivity;
- temporal policies.

Important exceptions:

- AWS Agent Registry is not currently GA in Singapore;
- Guardrails in AgentCore Policy are not currently supported in Singapore;
- temporal policy propagation cannot span AgentCore resources across accounts/Regions.

This is another reason to centralize Harness/Gateway/tool Runtime in Singapore and use STS for business-account access rather than placing AgentCore policy hops in every AWS account.

## 8. CI/CD identity

Deployment identity and runtime identity are separate concerns.

### GitHub Actions

Use GitHub OIDC -> AWS STS role. GitHub documents this as a way to avoid storing long-lived AWS credentials in repository secrets and recommends trust-policy conditions such as the repository/branch `sub`.

### GitLab

GitLab supports OIDC ID tokens -> `sts:AssumeRoleWithWebIdentity`, including GitLab Dedicated. Pin the trust policy to appropriate project/group/branch claims. For a non-public GitLab issuer, follow GitLab's documented issuer/JWKS requirements rather than inventing a custom credential bridge.

### Runtime

Runtime/tool access to member AWS accounts should use normal IAM role assumption, not CI OIDC.

## 9. Model strategy

Harness makes model choice replaceable, so keep it out of the core security architecture.

Candidate experiment:

- Nova 2 Lite as an inexpensive default candidate, optionally with extended thinking for harder prompts;
- one stronger comparison model available through Harness/Bedrock;
- run the same security task set through both.

Score only product-relevant behavior:

- correct control interpretation;
- correct tool selection;
- bounded recommendation;
- no invented AWS state;
- correct interpretation of provider response;
- latency/cost.

The model may be wrong. Policy/IAM must still make an unsafe action impossible.

## 10. Explicit non-goals for the clean MVP

Do not initially add:

- EKS merely as an agent hosting platform;
- custom Kubernetes identity machinery;
- a generic AWS shell/CLI agent with write permissions;
- autonomous supervisor routing before two specialists work independently;
- Registry as a Singapore dependency;
- a custom observability stack;
- dozens of AWS controls in the first milestone;
- an assumption that one model vendor is a permanent architecture dependency.
