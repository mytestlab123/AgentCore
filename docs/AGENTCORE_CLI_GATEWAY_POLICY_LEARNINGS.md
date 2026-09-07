# AgentCore CLI Gateway Policy lessons

This note records reusable, sanitized lessons from Issue #31. It contains no
AWS account IDs, ARNs, endpoint URLs, credentials, or raw deployment output.

## Architecture boundary

- Use the official, pinned AgentCore CLI and its generated CDK stack for the
  Gateway, Gateway target, Policy Engine, Cedar policy, and generated Gateway
  execution role.
- Keep the repository Python verifier thin. It may enforce identity gates,
  create or reuse the synthetic Lambda prerequisite, render private CLI input,
  invoke the managed Gateway, measure Lambda deltas, and produce sanitized
  inventory/cost evidence.
- Do not let the verifier reproduce the AgentCore control plane or policy
  decision logic.
- A Gateway Policy proof does not need a model, Runtime, Harness, Memory,
  LibreChat, API Gateway, VPC, or database.

## Native CLI configuration

- Pin `@aws/agentcore` to an exact reviewed version and commit its lockfile.
- `agentcore.json` can explicitly use empty `runtimes` and `harnesses` arrays.
- A Lambda target uses `targetType: lambdaFunctionArn`, `lambdaArn`, and
  `toolSchemaFile`.
- An IAM-protected Gateway uses `authorizerType: AWS_IAM`; deterministic policy
  enforcement uses `policyEngineConfiguration.mode: ENFORCE`.
- In CLI 0.28.1, `aws-targets.json` is an array of target records containing
  `name`, `account`, and `region`. It is not a map keyed by target name.
- Negotiate or honor the deployed Gateway's advertised MCP version. The live
  Issue #31 Gateway accepted `2025-03-26` and rejected the newer planned value
  before tool execution.
- Resolved configuration and `.cli/deployed-state.json` are private evidence;
  they can contain account-specific identifiers and managed endpoints.

## CDK bootstrap gate

- AgentCore CLI deployment uses CDK and may require the account/Region
  `CDKToolkit` bootstrap stack.
- The standard bootstrap template falls back to `AdministratorAccess` for its
  CloudFormation execution role when no execution policies are supplied.
- Inspect the bootstrap template, execution policies, trust, encryption choice,
  and synthesized application resources before running bootstrap or deploy.
- Stop on broad unreviewed permissions, external trust, unexpected compute or
  network resources, Runtime/Harness/model resources, or projected retained
  cost at or above the approved threshold.

## Evidence and lifecycle

- The proof is `dev` ALLOW with Lambda delta exactly one, followed by `prod`
  DENY with Lambda delta exactly zero.
- Lambda metrics are backend-execution evidence; a policy response alone does
  not prove the backend was untouched.
- Use stable tagged resources. A TTL/review date triggers owner review and does
  not itself authorize deletion.
- Retain approved low-cost resources for repeatable demonstrations. Cleanup is
  a separate, explicit, inventory-first operation.
- Default plan mode must make zero AWS calls.

## Private artifact boundary

Keep resolved account/caller values, ARNs, Gateway URLs, deployed state, CDK
synth output, raw API responses, Lambda bundles, and request/signature material
under the private Issue #31 evidence directory with directories mode 700 and
sensitive files mode 600. Commit only sanitized templates, deterministic code,
tests, and documentation.
