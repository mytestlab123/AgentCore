# AgentCore AI Model API Key Platform — POC Architecture

Related issue: #1

> Current implementation boundary: GitHub Issue #4. This document is retained
> as future architecture context; it does not define the current MVP scope.

## Goal

Build a polished internal AI developer-platform POC that demonstrates one developer-facing platform interface for governed access to AI models and agent capabilities.

The project is for learning and portfolio demonstration, not production commercialization.

## Demo outcome

A developer should be able to:

1. Sign in to the web portal.
2. Create or open a project/application.
3. Generate a masked platform API key such as `sk-demo-********`.
4. See models available to that project.
5. Run a prompt from the Playground.
6. Receive the model response plus provider/model, latency, token usage, estimated cost, request ID, and status.
7. Switch model/provider while continuing to use the same platform abstraction.
8. Run one agentic workflow where an AgentCore Runtime agent invokes an approved tool.
9. Inspect usage and audit information.

## Visual scope

Keep V1 intentionally small and polished:

- Dashboard
- Projects
- API Keys
- Models
- Playground
- Usage
- Logs

## Reuse-first strategy

Do not start from an empty full-stack application if an official AWS sample already provides the foundations.

Evaluate these official repositories first:

1. `aws-samples/sample-amazon-bedrock-agentcore-fullstack-webapp`
   - Preferred baseline for the React/authentication/AgentCore application skeleton.
2. `aws-samples/sample-multi-agent-orchestration-chat-on-agentcore`
   - Reference for richer AgentCore, gateway, memory, DynamoDB, and agent patterns.
3. `awslabs/amazon-bedrock-agentcore-samples`
   - Reference for focused AgentCore examples and deployment patterns.

Decision rule: reuse the first sample as the base unless current code inspection shows a materially simpler official starter.

## Minimal V1 architecture

```text
Developer Browser
      |
      v
React + TypeScript Portal
      |
      +--> Amazon Cognito (interactive login)
      |
      v
Amazon API Gateway
      |
      v
Thin Platform Lambda
      |
      +--> DynamoDB
      |      - projects
      |      - API-key metadata/hash
      |      - lightweight request metadata
      |
      +--> AgentCore Gateway / inference path
      |        |
      |        +--> Amazon Bedrock
      |        +--> one external provider later
      |
      +--> AgentCore Runtime
               |
               +--> Strands agent
                       |
                       +--> approved Gateway tool

Observability: CloudWatch + AgentCore telemetry
IaC: AWS CDK when compatible with the chosen sample
Hosting: use the hosting pattern already provided by the reused AWS sample; prefer S3 + CloudFront for a simple SPA.
```

## Service responsibilities

### Frontend

**React + TypeScript**

Use the official AWS sample UI as the starting point and reshape it into a developer portal instead of building a design system from scratch.

### Authentication

**Amazon Cognito**

Used for interactive web login. Do not build a custom identity provider.

### Platform API

**Amazon API Gateway + Lambda**

Keep this layer deliberately thin. Its main responsibilities are:

- validate the demo platform API key
- resolve project context and allowed models
- attach audit metadata
- call the configured AgentCore/Bedrock path
- return normalized response metadata to the GUI

This is a platform façade, not a custom LLM orchestration framework.

### Project and API-key metadata

**Amazon DynamoDB**

Store only what the POC needs:

- project ID/name
- API-key identifier and secure hash, never plaintext after creation
- enabled models/providers
- created/last-used timestamps
- small request/audit metadata if needed by the GUI

### Model access

**Amazon Bedrock + AgentCore Gateway where the current supported inference flow fits.**

Do not implement a large custom model router unless required by an actual gap discovered during implementation.

V1 only needs:

- one Bedrock model
- optionally one external provider/model to prove provider abstraction

### Agent demo

**AgentCore Runtime + Strands**

One agent is enough. The demo should visibly show:

User prompt -> AgentCore Runtime -> Agent -> approved tool -> result -> response

The tool can be a safe read-only mock/security-finding lookup. The purpose is to prove governed tool calling, not business complexity.

### Identity and secrets

Use **AgentCore Identity / AWS-managed secret patterns** only where they genuinely simplify external-provider or tool credentials.

Do not add credential infrastructure just to increase the number of AWS services in the diagram.

### Observability

Reuse **CloudWatch and AgentCore telemetry** for request traces, errors, latency, and agent/tool activity wherever possible.

The portal can present a simplified developer-facing Usage/Logs view based on those signals plus lightweight request metadata.

## Suggested API abstraction

The developer should conceptually see one endpoint and one platform credential:

```text
Developer App
    |
    |  Platform API key
    v
AgentCore POC Platform API
    |
    +--> project/policy validation
    +--> normalized model request
    |
    v
AWS AI / AgentCore layer
    |
    +--> Bedrock model
    +--> optional external model
```

The API-key format is a demo UX abstraction such as `sk-demo-*`; it does not need to become a production key-management product.

## Playground response metadata

For each request display:

```text
Provider
Model
Latency
Input tokens
Output tokens
Estimated cost
Request ID
Project
Status
Tool calls (when applicable)
```

## Security controls to make visible

Keep security visible but understandable:

- masked API keys
- API key shown only once at creation
- hashed key storage
- project-to-model allow list
- authenticated portal access
- request/audit identifier
- read-only approved tool for the first agent demo
- no provider secrets exposed to developer applications

A human-approval step is optional for V1. Add it only if it improves the five-minute demo rather than creating workflow complexity.

## Explicit non-goals

Do not build in V1:

- EKS/Kubernetes
- production SaaS multi-tenancy
- billing/subscription engine
- RAG/vector database
- many agents
- many providers
- custom OAuth server
- custom observability stack
- enterprise-grade key rotation lifecycle
- complex policy engine
- custom LLM router when AgentCore/AWS already provides the needed path
- mobile application

## Implementation phases

### Phase 0 — reuse validation

- inspect the official AWS full-stack sample
- confirm deploy/local-development path
- identify the minimum files/components to retain
- document any AgentCore Gateway inference limitations discovered from current AWS APIs/docs

### Phase 1 — visual portal

- adapt navigation and branding
- create Dashboard, Projects, API Keys, Models, Playground, Usage, Logs
- use mock data where needed so the visual story is complete early

### Phase 2 — real Bedrock path

- Cognito login
- thin platform API
- DynamoDB project/key metadata
- Bedrock model invocation
- normalized metadata shown in Playground

### Phase 3 — agentic capability

- deploy one AgentCore Runtime agent
- expose one controlled tool through the appropriate Gateway pattern
- show tool call + trace in the GUI

### Phase 4 — optional multi-provider proof

- add one external model/provider only if it can be done cleanly
- preserve the same platform-facing request abstraction

## Five-minute demo story

### 0:00–0:45 — Problem

Application teams should not individually manage model credentials, SDK differences, and AI governance.

Show the Dashboard and explain that this POC represents an internal developer AI platform.

### 0:45–1:30 — Developer onboarding

Open `demo-security-app`, show its allowed models, and create/reveal a masked `sk-demo-*` API key.

### 1:30–2:30 — Unified model access

Use Playground to ask:

> Explain this security finding and recommend remediation.

Show the answer plus provider/model, latency, tokens, cost estimate, and request ID.

### 2:30–4:00 — Agentic capability

Switch to the security agent. Show the agent calling a safe approved tool through the AgentCore path and returning a grounded result.

### 4:00–5:00 — Trust and operations

Open Usage/Logs and show project, model, request ID, latency, token usage, tool call, and status.

Close with the message:

> This demonstrates not only an AI application, but a secure AWS developer platform that governs how applications and agents consume models and tools.

## Success criteria

V1 is successful when a reviewer can understand within five minutes that the project demonstrates:

- full-stack AI application development
- Amazon Bedrock invocation
- AgentCore Runtime
- AgentCore Gateway/tool integration
- model/provider abstraction
- API authentication/key concepts
- tool calling
- auditability/observability
- secure AI-platform thinking

without needing a production-scale architecture.

## Cost and cleanup

This is a personal learning POC.

- prefer serverless/pay-per-use services
- avoid permanently running compute where possible
- document deployed resources
- provide a one-command or clearly documented CDK cleanup path
- delete learning resources after testing when they are not needed
