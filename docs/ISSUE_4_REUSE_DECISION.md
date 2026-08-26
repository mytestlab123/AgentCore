# Issue 4 Reuse Decision

Date: 2026-08-27

## Decision

Keep only the useful React layout and CDK conventions learned from the official
AWS samples. Do not retain their AgentCore Runtime, Cognito, container build,
multi-agent, Gateway, Memory, CloudFront, or orchestration layers for Issue #4.

The current implementation is intentionally smaller:

```text
Local React UI -> API Gateway -> Lambda policy facade -> Amazon Bedrock
                                      |
                                      +-> one DynamoDB table for key hash and logs
```

## Samples inspected

- `aws-samples/sample-amazon-bedrock-agentcore-fullstack-webapp` at commit
  `7a9e70f3abc879b736f0011657462023746f0c36`: useful React, Bash, and CDK
  conventions; the Cognito and AgentCore deployment shape is too large here.
- `aws-samples/sample-multi-agent-orchestration-chat-on-agentcore` at commit
  `b48bcb476d08383f9d9b65a5df046555d7ba0fbb`: useful API Gateway, Lambda, and
  DynamoDB reference; multi-agent components are deliberately omitted.
- `awslabs/agentcore-samples` at commit
  `cff4a1e3345da936f0a19c121ffaaccf233d082a`: retained only as future learning
  reference because AgentCore is not required by Issue #4.

## Kept and omitted

Kept: a compact React shell, local/live modes, CDK, deterministic Bash checks,
and explicit cleanup. Omitted: every service and product area not needed to
show one allowed model call, one denied model call, and central logs.
