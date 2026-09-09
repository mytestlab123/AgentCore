# Kiro deep architecture review result

Status: 2026-09-09

Result: **CHANGE**

This file records the architecture changes accepted from Kiro's independent AWS-native review after the 2026-09-09 deep-research packet.

The full architecture outcome is frozen in [ARCHITECTURE_DECISION_V1.md](./ARCHITECTURE_DECISION_V1.md).

## Accepted corrections and additions

### 1. Personal MVP hosting

Use a non-management dev/sandbox member account for the clean product workload rather than the AWS Organizations management account.

A dedicated security-tooling account is not required for MVP-1; create one later when delegated security administration or stronger separation justifies it.

Reference:
- https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html

### 2. Exact Lambda MCP tools remain the first default

The preferred first vertical slice remains:

```text
Harness
 -> MCP Gateway
 -> Policy
 -> exact Lambda MCP tool
 -> STS AssumeRole
 -> AWS API
 -> provider verification
```

Use separate read/remediation identities where practical.

Reference:
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/use-gateway-with-policy.html

### 3. New native features worth keeping in the roadmap

Kiro identified several current AWS-native capabilities that should replace or avoid custom plumbing when the related requirement appears:

- AgentCore Gateway rate limits;
- direct AWS WAF association with AgentCore Gateway;
- Step Functions optimized `InvokeHarness` integration;
- AgentCore Evaluations / Optimization / A-B testing capabilities;
- API Gateway MCP proxy for existing REST APIs;
- Registry's current `GATEWAY` record type in addition to MCP/AGENT/SKILL/CUSTOM.

These are not all MVP-1 requirements.

References:
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-rate-limits.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-waf.html
- https://docs.aws.amazon.com/step-functions/latest/dg/connect-bedrockagentcore.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html
- https://docs.aws.amazon.com/agent-registry-control/latest/APIReference/API_RegistryRecordSummary.html

### 4. Registry plan tightened

Registry remains out of the Singapore MVP runtime dependency.

Accepted plan:

- source-control portable agent/tool/skill descriptors;
- do not use Sydney Registry as an authoritative catalog for Singapore runtime auto-discovery;
- optional small Sydney Registry experiment later when reuse/discovery is a real problem;
- keep Registry deployment identifiers and Region environment-specific.

Current Registry control/discovery namespaces and record types must follow the current GA APIs.

References:
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry-create-manage.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry-organizations.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry-cloudtrail-integration.html

### 5. Organizations architecture confirmed

Use:

```text
central AgentCore/tooling member account
 -> exact read/remediation tool identities
 -> STS AssumeRole
 -> fixed roles in approved member accounts
```

Use service-managed StackSets when the same narrow roles/configuration need distribution across selected OUs/accounts.

Do not let the model choose arbitrary accounts, role ARNs, Regions or AWS actions.

References:
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-orgs-manage-auto-deployment.html
- https://docs.aws.amazon.com/organizations/latest/userguide/services-that-can-integrate-cloudformation.html

### 6. Provider-native security evidence reinforced

Do not build broad scanning logic.

Use direct provider APIs and AWS findings/services as authoritative inputs:

- direct EC2/S3/IMDSv2 state for fast controls;
- Config where useful;
- Security Hub CSPM for later organization-wide aggregation;
- Inspector/ECR for vulnerability evidence;
- Access Analyzer for future IAM/access specialization;
- GuardDuty for later incident/threat specialization.

AWS Security Agent / Continuum remains complementary application/code-security capability rather than an Inspector replacement.

References:
- https://docs.aws.amazon.com/inspector/latest/user/integrations.html
- https://aws.amazon.com/about-aws/whats-new/2026/06/aws-continuum/

### 7. Builder AWS MCP != product mutation boundary

AWS Agent Toolkit and the broad AWS MCP Server can accelerate Kiro/Codex development and supervised operations.

They must not become the production remediation boundary.

Production writes remain exact, narrow Gateway-governed MCP tools with IAM and Policy enforcement.

References:
- https://aws.amazon.com/products/developer-tools/agent-toolkit-for-aws/
- https://aws.amazon.com/blogs/security/secure-ai-agent-access-patterns-to-aws-resources-using-model-context-protocol/

### 8. Human approval design refined

MVP-1 keeps a simple human approval handoff followed by stateless exact Gateway Policy.

For a later policy-visible sequence, use a trusted approval workflow/backend identity to create the approval event. The model/Harness normal execution identity must not be able to self-authorize.

A later sequence may be:

```text
detect MCP action
 -> trusted approval workflow
 -> policy-visible approval action
 -> Temporal Policy correlation
 -> exact remediation
 -> provider verification
```

Step Functions may provide the workflow state/approval callback while Harness remains the reasoning component.

Reference:
- https://aws.amazon.com/blogs/machine-learning/securing-ai-agents-with-temporal-policies-in-amazon-bedrock-agentcore/

### 9. Model plan refined

Keep Nova 2 Lite as the low-cost baseline.

Compare it with one stronger Bedrock/Harness model whose current Singapore/residency path is explicitly verified before deployment.

Do not infer residency merely from the Harness endpoint Region.

Reference:
- https://docs.aws.amazon.com/bedrock/latest/userguide/models-region-compatibility.html

## Final accepted milestone sequence

1. clean single-account Compliance SG vertical slice;
2. 2-3 account STS/Organizations foundation;
3. S3 BPA + IMDSv2 compliance breadth;
4. organization security sources + Inspector/ECR Vulnerability Agent;
5. trusted policy-visible approval + Temporal Policy;
6. Registry/discovery and A2A Supervisor only when justified.

## R&D code that should remain behind

Do not promote these historical POC mechanisms unless a new requirement proves they are still useful:

- custom agent loop;
- separate Gateway-decision-then-AWS-mutation path;
- EC2-hosted remediation MCP server;
- synthetic resource aliases;
- visual Gateway verifier;
- issue-number-specific compatibility/deployment scripts;
- historical browser proof machinery.

The clean product should reuse the proven behavior/contracts, not the old implementation shape.
