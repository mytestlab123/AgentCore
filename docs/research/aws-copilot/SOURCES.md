# AWS Copilot research sources

Research date: 2026-09-09

The architecture packet intentionally prefers current official AWS/Amazon and official GitHub/GitLab documentation. AgentCore is changing quickly; re-check these sources before a major implementation decision.

## AgentCore core

- AgentCore overview: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html
- AgentCore supported regions: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html
- AgentCore Harness: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html
- Harness vs Runtime: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-vs-runtime.html
- Harness security/execution role: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-security.html
- Harness models: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-models.html
- Harness skills: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-skills.html
- Harness versioning/endpoints: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-versioning.html
- Export Harness to Strands code: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-export.html

Key finding: Harness is a managed Strands-powered orchestration layer backed by Runtime; it can configure models, Gateway, skills, memory, observability and other primitives without owning the loop code. Export provides an escape hatch when custom code is needed.

## Runtime and protocols

- Runtime overview: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html
- Runtime microVM model: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html
- Runtime service contract: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-service-contract.html
- Runtime Instances: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-instances-how-it-works.html
- Runtime A2A: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-a2a.html
- Runtime VPC configuration: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-vpc.html

Key finding: Runtime supports HTTP, MCP, A2A and AG-UI. Default microVMs are the simpler serverless choice for lightweight API-driven agents/tools; Instances are managed EC2 in the customer account for long-lived/stateful/GPU/multi-agent sessions.

## Gateway and Policy

- AgentCore Gateway: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html
- Gateway concepts: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-core-concepts.html
- Supported Gateway targets: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-supported-targets.html
- MCP targets: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-targets-mcp.html
- Runtime HTTP target: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-http-runtime.html
- Gateway outbound authentication: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-outbound-auth.html
- Gateway with Policy: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/use-gateway-with-policy.html
- Temporal policies: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-temporal.html
- Policy sessions / identity propagation: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-session-based-temporal.html
- Guardrails in Policy: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-guardrails-in-policies.html

Key findings:

- Gateway is the governed front door for tools/agents/models, not primarily a Slack/email delivery channel.
- MCP targets include Lambda, API/OpenAPI/Smithy and MCP servers.
- Current Policy evaluation is documented for MCP tools, which makes MCP the preferred path for the first critical mutating tool.
- Temporal policies are supported in Singapore and can enforce session-history conditions.
- Temporal propagation between AgentCore Gateway/Runtime components does not cross AWS account or Region boundaries.
- Guardrails inside AgentCore Policy are currently not supported in Singapore.

## Identity and multi-account AWS

- AgentCore Identity: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html
- Agent identity directory: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agent-identity-directory.html
- IAM cross-account resource access: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies-cross-account-resource-access.html
- IAM roles: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html
- Organizations OU best practices: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_ous_best_practices.html
- IAM multi-account guardrail best practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

Key finding: AWS cross-account roles remain the standard mechanism for a central workload to receive temporary, scoped access to member accounts. AWS Organizations recommends centralized security/infrastructure account structures and SCP/RCP guardrails; those guardrails do not themselves grant permissions.

## Registry

- AWS Agent Registry management docs: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry-create-manage.html
- GA announcement and regions: https://aws.amazon.com/about-aws/whats-new/2026/08/aws-agent-registry-generally-available/

Key findings:

- Registry catalogs agents, MCP servers/tools, skills and custom resources with governance/search/sharing.
- GA regions as of the research date: N. Virginia, Oregon, Ireland, Tokyo and Sydney.
- Singapore is not currently a Registry region, so Registry should not block the Singapore MVP.
- The new `agent-registry` namespace replaces the preview namespace; preview namespace support is scheduled to end on 17 September 2026.

## Observability and Evaluations

- Harness operations / observability and cost controls: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-operations.html
- AgentCore Evaluations: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/evaluations.html

Key finding: use native tracing/CloudTrail/evaluation capabilities before creating a custom operations/LLM-observability stack.

## Models

- Harness model providers/switching: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-models.html
- Nova 2 Lite model card: https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-2-lite.html
- Nova model overview, including Nova Premier positioning: https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards-amazon.html
- Nova 2 extended thinking: https://docs.aws.amazon.com/nova/latest/nova2-userguide/extended-thinking.html

Key finding: Nova 2 Lite is positioned as a cost-efficient model for simpler automation/document/support tasks; Nova Premier is positioned for complex reasoning/agentic workflows. Harness model flexibility means the security architecture should not depend on either model winning.

## CI/CD OIDC

- GitHub Actions OIDC with AWS: https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws
- GitLab OIDC with AWS: https://docs.gitlab.com/ci/cloud_services/aws/

Key finding: use short-lived OIDC-federated AWS deployment credentials for CI rather than storing long-lived AWS access keys. This is separate from the deployed agent's runtime cross-account STS role assumption.

## Naming note

- Existing AWS Copilot CLI documentation / end-of-support notice: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/copilot-install.html

The historical AWS Copilot CLI reached end of support on 12 June 2026. `AWS Copilot` can still be used as an internal working name, but a future public/long-term repository named `aws-copilot` can be confused with that established product name.
