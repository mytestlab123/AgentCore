# AWS Copilot deep-research addendum

Status: 2026-09-09

Purpose: update the existing AWS Copilot research packet with the latest AgentCore, AWS Agent Registry, AWS Organizations, and AWS security-service findings before creating the clean long-term product repository.

This is architecture research only. It does not authorize or perform AWS mutations.

## Review verdict

**ACCEPT WITH CHANGES.**

The existing direction remains sound:

```text
thin UI
  -> AgentCore Harness
  -> MCP AgentCore Gateway
  -> AgentCore Policy
  -> exact governed tool
  -> STS AssumeRole
  -> target AWS account
  -> provider verification
```

The new research makes six material improvements:

1. AgentCore Harness is already available in Singapore; do not wait for a future launch.
2. AWS Agent Registry is useful, but it is not currently available in Singapore and must remain optional for the MVP.
3. The product workload should not run in the AWS Organizations management account; use a member security/tooling account.
4. AWS Organizations + delegated administration + StackSets should become part of the multi-account design.
5. AWS Copilot should consume provider-native findings instead of becoming another scanner.
6. Builder-side AWS Agent Toolkit / broad AWS MCP capability must stay separate from the narrow production remediation boundary.

## 1. Region decision: build the live control plane in Singapore now

The current AgentCore region matrix lists Singapore (`ap-southeast-1`) for the core capabilities needed by the MVP, including Harness, Runtime, Gateway, Identity, Policy, Observability, and Evaluations. Temporal Policy is also available in Singapore.

Therefore the clean MVP should use Singapore as its normal live control-plane Region.

Do **not** design around an assumption that Harness will arrive later; it is already present.

### Registry exception

AWS Agent Registry became generally available on 31 August 2026 in five Regions:

- US East (N. Virginia)
- US West (Oregon)
- Europe (Ireland)
- Asia Pacific (Tokyo)
- Asia Pacific (Sydney)

Singapore is not currently listed. No official Singapore launch date was found.

Decision:

> Build Singapore-first and Registry-ready, but do not make Registry a runtime dependency.

If we want Registry learning before Singapore support exists, Sydney is the natural nearby experiment Region. Keep the actual Harness/Gateway/Policy workload in Singapore.

Important: Registry organization auto-detection runs in the current Region. A Sydney organization-scoped Registry does not automatically discover Singapore Runtime/Gateway resources. AWS documentation says a separate Registry with auto-detection is required in each Region to discover that Region's resources.

## 2. Registry-ready, not Registry-dependent

Registry can catalog:

- MCP servers/tools;
- A2A agents;
- Agent Skills;
- custom resources.

It provides approval workflows, hybrid semantic/keyword search, MCP-native discovery, CloudTrail integration, EventBridge events, AWS RAM sharing, and organization-wide auto-detection for supported AgentCore Runtime and Gateway resources.

Recommended future catalog shape:

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

Treat these definitions as source-controlled descriptors so the Registry Region is deployment configuration rather than application architecture.

Do not move the live AgentCore control plane to Sydney just to gain Registry.

### Namespace migration

New Registry automation must use the GA `agent-registry` namespace. AWS states that support for the public-preview `bedrock-agentcore` Registry namespace ends on **17 September 2026**.

Use the new control-plane CLI/API namespace for any new Registry work.

## 3. Organizations architecture: management account is bootstrap/admin only

The personal AWS Organization is a useful miniature of the future company design, but the AWS Organizations management account should not host AWS Copilot workloads.

AWS explicitly recommends:

- use the management account only for tasks that require it;
- avoid deploying workloads there;
- delegate responsibilities to member accounts.

A major reason is that SCPs do not constrain the management account.

Recommended personal-lab topology:

```text
Organizations management account
  -> organization administration only
  -> delegated administration / trusted access / StackSets bootstrap

member security-tooling or sandbox account
  -> AgentCore Harness
  -> Gateway + Policy
  -> exact Lambda/MCP tools
  -> audit/observability
  -> STS AssumeRole into target member accounts
```

The current `amit` profile remains appropriate for human bootstrap/read-only administration while developing. It must not become the deployed application's runtime identity.

## 4. Multi-account scaling: STS + StackSets

For 14-50+ accounts, use fixed member-account roles rather than SSO sessions or stored access keys.

Recommended pattern:

```text
central tool execution role
       |
       +-- sts:AssumeRole --> AwsCopilotReadRole
       |
       +-- sts:AssumeRole --> AwsCopilotRemediationRole
```

Prefer separate read and remediation identities when practical. The model must never provide arbitrary role ARNs, account IDs, Regions, or AWS actions for execution.

Server-side configuration should own the allowed account/OU/Region/role mapping.

For organization-wide provisioning, CloudFormation StackSets with service-managed permissions can deploy to selected OUs and automatically deploy to future accounts that join those OUs.

This is the expected scaling path for member-account roles; do not manually create the same role in dozens of accounts.

A delegated StackSets administrator can be used later, with the important AWS caveat that delegated StackSets administrators have broad organization deployment authority and must therefore be selected carefully.

## 5. Do not build another scanner

The product's differentiator should be governance and verified remediation, not recreating provider-native detection engines.

Target value chain:

```text
AWS provider finding/state
    -> specialist agent understands context
    -> explanation / prioritization
    -> human decision when mutating
    -> Gateway + deterministic Policy
    -> exact remediation
    -> provider verification
    -> audit
```

### Compliance Agent sources

Prioritize:

- Security Hub CSPM findings / controls;
- AWS Config where it already supplies a useful managed rule or conformance pack;
- direct provider APIs when that is simpler and more deterministic.

Security Hub CSPM central configuration is built for Organizations and can manage standards/controls across accounts, OUs, and Regions from a delegated administrator account. The Organizations management account cannot itself be the Security Hub CSPM delegated administrator.

This makes Security Hub a strong organization-scale finding source for the future company deployment.

### Vulnerability specialist sources

Keep a Vulnerability specialist, but source it from provider truth rather than custom scanning logic:

- Amazon Inspector for EC2/ECR/Lambda vulnerability findings;
- existing ECR image digests/findings for live demos;
- Security Hub context where useful;
- AWS Security Agent / AWS Continuum as complementary application/code-security sources.

Do **not** treat AWS Security Agent/Continuum as a replacement for Inspector infrastructure findings. Security Agent is especially relevant to threat modeling, source/code review, penetration testing, and remediation workflows.

AWS Security Agent core capabilities are now available in Singapore.

### Later specialists

Provider-backed specialization may eventually look like:

```text
Compliance Agent
  Security Hub CSPM / Config / direct APIs

Vulnerability Agent
  Inspector / ECR / Security Agent / Continuum

IAM / Access Agent
  IAM Access Analyzer

Incident Agent
  GuardDuty / Security Hub / operations sources
```

Create a specialist only when it has a distinct authoritative data/tool boundary, not merely a different prompt persona.

## 6. Exact production tools, broad builder tools

AWS Agent Toolkit for the AWS CLI now provides the AWS MCP Server with 15,000+ AWS APIs and 40+ skills for coding agents such as Kiro, Codex, Claude Code, and Cursor.

This is valuable for **builders**:

```text
Kiro / Codex
  -> Agent Toolkit
  -> AWS skills
  -> broad AWS MCP for development/research
```

The AWS announcement currently lists the managed AWS MCP Server in US East (N. Virginia) and Europe (Frankfurt). That regional footprint is another reason to treat it as builder tooling rather than a Singapore production-runtime dependency.

It should **not** become the production remediation boundary:

```text
AWS Copilot runtime
  -> Harness
  -> Gateway + Policy
  -> exact narrow MCP tool
```

Do not expose a generic `run_aws_cli`, `call_any_aws_api`, or broad 15,000-API mutation surface to the production agent.

The first tools should remain semantically narrow and independently permissioned.

## 7. First tool target: Lambda MCP pattern remains preferred

For the first 2-3 deterministic controls, the smallest clean pattern remains:

```text
Harness
  -> MCP Gateway
  -> AgentCore Policy
  -> exact Lambda target exposed as MCP tool
  -> STS AssumeRole
  -> AWS API
  -> provider re-read
```

This avoids operating a general MCP server for tiny, fixed operations.

Move to a Runtime-hosted MCP server only when shared libraries, long-running behavior, custom protocols, richer state, or substantial reusable tool logic justify running a server.

Do not confuse a Runtime-hosted MCP server registered as an MCP target with the special AgentCore Runtime target type. Critical actions that need current Gateway Policy enforcement should remain on the MCP tool path.

## 8. Human approval and Temporal Policy

Current application/native UI approval is useful, but it is not automatically a Policy-visible temporal event.

Near term:

```text
human approval UI
  -> exact MCP call
  -> stateless Gateway Policy
  -> exact tool
```

Later, to make Policy itself enforce the safe sequence, represent approval as a trusted policy-visible action in the same authenticated temporal session:

```text
detect resource
  -> trusted human approval event
  -> same-resource remediation
  -> provider verification
```

The trusted approval action must not be callable by the model under its normal tool identity.

Temporal Policy can enforce sequence, argument correlation, freshness, and approval-before-privileged-action. Keep the AgentCore components participating in that temporal session in the same account and Region because current session propagation does not cross AgentCore account/Region boundaries.

## 9. Production-hardening features to keep native

Useful later, not first-milestone requirements:

- AgentCore Gateway rate limiting;
- AWS WAF associated with AgentCore Gateway;
- AgentCore Observability;
- AgentCore Evaluations / Optimization;
- versioned Harness endpoints and rollback;
- CloudTrail;
- Registry approval/discovery when it solves a real reuse problem.

Do not build custom equivalents first.

## 10. Deployment migration path

### Stage A — personal Organization

Use the personal Organization to prove the target shape:

```text
management account
  -> bootstrap only

member tooling account
  -> AgentCore Singapore control plane
  -> exact tools
  -> STS into 2 member accounts
```

Use real provider identities in the private demo: actual account ID/alias, Region, resource name/ID, finding, action, and verification result.

### Stage B — company non-production

Deploy the same architecture into a dedicated non-production security/tooling member account.

Use Organizations/StackSets to establish target roles in approved non-production OUs/accounts.

The application configuration changes account/OU mappings; the core agent/tool architecture does not change.

### Stage C — company production

Deploy a separately controlled production security/tooling stack, narrow target-account roles, production CI/CD controls, approval policy, audit, and least privilege.

Do not treat the personal account as something to "lift and shift". Migrate source-controlled architecture/configuration and redeploy cleanly.

## 11. Revised product milestones

### Milestone 1 — clean Compliance vertical slice

- create the clean long-term repository;
- deploy Compliance Agent on AgentCore Harness in Singapore;
- use a member tooling/sandbox account, not the Organizations management account;
- show real account/resource identity;
- put actual Security Group read/remediation tools behind MCP Gateway + Policy;
- use workload IAM identity;
- provider verification + compact audit.

One real SG lifecycle only.

### Milestone 2 — Organizations / cross-account foundation

- prove 2-3 approved member accounts;
- separate read/remediation target roles;
- server-owned account/role routing;
- StackSet design for OU deployment;
- account-aware audit.

### Milestone 3 — native compliance breadth

- make Security Hub CSPM a first-class finding source;
- add S3 Block Public Access;
- add EC2 IMDSv2;
- use Config/SSM managed remediation where simpler than custom Lambda;
- retain direct provider verification.

### Milestone 4 — second specialist

- add Vulnerability Agent;
- real Inspector/ECR findings;
- optionally integrate Security Agent/Continuum context;
- manual agent switching first.

### Milestone 5 — policy-visible human governance

- model trusted approval as a Policy-visible event;
- prove Temporal Policy in `LOG_ONLY` first;
- same-resource/freshness/sequence tests;
- then `ENFORCE`.

### Milestone 6 — reuse/discovery/orchestration

- add Registry only when multiple agents/tools/skills justify discovery;
- if Singapore Registry still does not exist, optionally use Sydney for a catalog-only experiment;
- keep descriptors/IaC portable;
- add A2A Supervisor only if manual specialist selection becomes a real usability problem.

## 12. KISS / cost defaults

For the personal MVP:

- Singapore Harness + one narrow Gateway/Policy path;
- one or two tiny Lambda tools before Runtime MCP servers;
- no EKS;
- no custom scanner;
- no custom observability platform;
- no Registry dependency;
- no autonomous supervisor;
- no broad production AWS MCP mutation access;
- use existing provider findings where possible;
- use temporary credentials only;
- enable cost-heavy services only when the milestone needs them.

AWS Security Agent penetration testing is task-hour billed; use budget controls if/when tested. Registry, Security Hub, Config, Inspector, WAF, logging, and cross-Region experiments can all create recurring cost or operational overhead, so add them only when they prove the next product outcome.

## Reviewed caveats

The deep-research findings were reviewed against current official AWS documentation. These caveats are intentionally retained:

1. **No Singapore Registry date:** design for portability, not an assumed roadmap date.
2. **Management account:** administrative access is useful for bootstrap, but workload deployment there is contrary to AWS Organizations best practice.
3. **Security Agent/Continuum:** complementary to, not a replacement for, Inspector and Security Hub infrastructure findings.
4. **Agent Toolkit:** excellent builder accelerator; broad AWS MCP is not the product's write boundary, and the managed MCP Server currently has a smaller Region footprint than AgentCore Singapore.
5. **Temporal approval:** current LibreChat/native approval does not automatically become Policy history.
6. **Registry auto-detection:** organization-wide does not mean cross-Region; it is Region-scoped.
7. **Real identifiers:** the future private demo may display real provider identifiers, but credentials, tokens, private keys, and secrets remain prohibited.

## Official sources reviewed

AgentCore:

- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/use-gateway-with-policy.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-temporal.html
- https://aws.amazon.com/about-aws/whats-new/2026/08/temporal-policies-agentcore/
- https://aws.amazon.com/about-aws/whats-new/2026/06/aws-waf-amazon-bedrock-agentcore/

Registry:

- https://aws.amazon.com/about-aws/whats-new/2026/08/aws-agent-registry-generally-available/
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry-get-started.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry-key-capabilities.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry-organizations.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry-supported-record-types.html

Organizations / security services:

- https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-orgs-associate-stackset-with-org.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-orgs-manage-auto-deployment.html
- https://docs.aws.amazon.com/securityhub/latest/userguide/central-configuration-intro.html
- https://docs.aws.amazon.com/securityhub/latest/userguide/start-central-configuration.html
- https://docs.aws.amazon.com/inspector/latest/user/what-is-inspector.html

Agent development / security:

- https://aws.amazon.com/about-aws/whats-new/2026/06/aws-cli-agent-toolkit/
- https://aws.amazon.com/about-aws/whats-new/2026/07/aws-security-agent-asia-pacific/
- https://aws.amazon.com/about-aws/whats-new/2026/06/aws-continuum/
