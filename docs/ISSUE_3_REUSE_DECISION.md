# Issue 3 Reuse Decision

Date: 2026-08-26

## Decision

Use `aws-samples/sample-amazon-bedrock-agentcore-fullstack-webapp` as the V1
baseline. Selectively adapt its frontend, Cognito authentication, AgentCore
Runtime agent, CDK stacks, and Bash automation instead of recreating those
foundations.

Pinned source commit:

```text
7a9e70f3abc879b736f0011657462023746f0c36
```

## Samples inspected

1. `aws-samples/sample-amazon-bedrock-agentcore-fullstack-webapp`
   - selected because it is the smallest complete React, Cognito, AgentCore
     Runtime, CloudFront/S3, and CDK example
   - its frontend calls AgentCore Runtime directly with a Cognito JWT
   - it provides separate local-development and deployment paths
2. `aws-samples/sample-multi-agent-orchestration-chat-on-agentcore`
   - inspected at commit `b48bcb476d08383f9d9b65a5df046555d7ba0fbb`
   - demonstrates API Gateway, Lambda, DynamoDB, Gateway, Memory, scheduling,
     AppSync, and multi-agent patterns
   - rejected as the baseline because that scope is much larger than issue #3
3. `awslabs/agentcore-samples`
   - the issue's older repository name now resolves to this repository
   - inspected at commit `cff4a1e3345da936f0a19c121ffaaccf233d082a`
   - retained as a focused reference catalog for future Runtime, Gateway,
     Identity, and observability work, not as an application scaffold

## Reused foundation

- `frontend/src/auth.ts` and `frontend/src/AuthModal.tsx` for Cognito
- `frontend/src/agentcore.ts` for the Runtime invocation and streaming boundary
- `agent/` for the Bedrock AgentCore and Strands runtime shape
- `cdk/` for Cognito, build, Runtime, CloudFront, and S3 infrastructure
- Bash build and deployment automation

## MVP adaptations

- replaced the generic chatbot screen with a seven-route developer portal
- made local mock mode the default, so a reviewer needs no AWS deployment
- added normalized mock response metadata and explicit mock labels
- changed the sample tool to one synthetic, read-only security finding lookup
- added local lint, focused tests, build checks, and script syntax checks
- added deployment approval, TTL, tagging, and cleanup gates

## Material deviations and deferrals

The approved architecture includes a thin API Gateway and Lambda platform
facade plus DynamoDB project and key metadata. The selected baseline does not:
it invokes AgentCore Runtime directly from the browser after Cognito login.

Issue #3 preserves that working boundary but does not add the facade or
DynamoDB. The portal's projects, keys, usage, logs, and cost values are clearly
mocked. Building the persistence and API-key lifecycle now would violate the
issue's bootstrap scope.

The inspected official examples use AgentCore Gateway for controlled tool
targets, while model execution remains in the Runtime and Bedrock path. Gateway
tool integration is therefore retained as a later agentic-capability phase, not
presented as a completed model-routing service.

## Human learning checkpoint

1. The full-stack sample was chosen because it provides the smallest official
   end-to-end React, Cognito, Runtime, and CDK foundation.
2. Authentication, Runtime invocation, the Strands agent shape, hosting stacks,
   and deployment plumbing were reused.
3. Cognito authenticates the deployed web user and supplies the JWT accepted by
   AgentCore Runtime. Local mock mode bypasses Cognito intentionally.
4. AgentCore Runtime hosts the retained Strands agent, which can invoke Bedrock
   and one synthetic read-only tool when live mode is deliberately enabled.
5. Project persistence, real keys, model policy, usage, logs, cost, Gateway
   integration, and cloud validation remain mocked or deferred.
