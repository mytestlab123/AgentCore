# Kiro learning handoff: Bedrock models, quotas, and AgentCore boundaries

**Status:** sanitized evidence handoff

**Last updated:** 2026-09-07

**Scope:** Amazon Bedrock and Amazon Bedrock AgentCore learning collected using
locally configured `amit` and `vagent` AWS CLI profiles, primarily in
`ap-southeast-1` (Singapore). This is a durable learning record, not a live
entitlement guarantee, deployment record, security advisory, or pricing quote.

## Safety and evidence rules

- This document intentionally omits AWS account IDs, identity ARNs, API keys,
  credentials, live security findings, private endpoints, and raw terminal
  transcripts.
- `catalog-visible`, `ACTIVE` inference profile, IAM authorization, and
  successful inference are different facts. They must never be treated as
  interchangeable.
- A model response is advisory only. It is not proof of a CVE, Amazon Linux
  advisory, installed package version, patch state, Inspector finding, or
  remediation outcome.
- No AgentCore Runtime was deployed during this work. Direct Bedrock calls do
  not prove AgentCore Runtime, Gateway, Memory, Identity, Browser, Policy, or
  application-level integration.
- No AWS Support case was created and no quota, account, billing, or model
  entitlement setting was changed.

## Executive conclusion

The `amit` profile has working direct Bedrock inference for two bounded,
low-cost model profiles:

| Provider | Inference profile | Evidence state |
|---|---|---|
| Amazon | `global.amazon.nova-2-lite-v1:0` | **Verified successful inference** |
| Anthropic | `apac.anthropic.claude-3-haiku-20240307-v1:0` | **Verified successful inference** |

The `vagent` profile can list Bedrock models and AgentCore control-plane
resources but has a zero Nova 2 Lite daily token allocation; it cannot complete
Nova 2 Lite inference. This is an account/model quota state, not evidence that
its IAM permissions are missing.

OpenAI Luna and current Claude Haiku 4.5 are catalog/profile visible to `amit`
but are currently blocked by explicit AWS availability/provider-access errors.
They must not be described as working.

## Profile and identity-level findings

Read-only AWS checks were used for profile identity and representative IAM
simulation. Both relevant profiles authenticated successfully and matched
broad administrative IAM policy statements for representative actions,
including:

- `bedrock-agentcore:ListGateways`
- `bedrock-agentcore:CreateEvaluator`
- `bedrock:InvokeModel`
- `iam:PassRole`

Both profiles could list Bedrock foundation models and AgentCore Gateways in
Singapore. This shows identity-level authorization, but does **not** override:

- account activation or billing/identity verification;
- model-provider terms or AWS Marketplace/provider onboarding;
- model-specific access allocation;
- Service Quotas;
- inference-profile routing rules;
- resource policies, organization controls, network policy, or future changes.

The `vagent` local profile originally had no configured default Region. Use an
explicit Region for non-interactive calls:

```bash
aws --profile vagent --region ap-southeast-1 <service> <operation>
```

## Nova 2 Lite: catalog ID versus inference profile

Observed base catalog model ID:

```text
amazon.nova-2-lite-v1:0
```

Observed required profile for the successful Singapore test:

```text
global.amazon.nova-2-lite-v1:0
```

The direct base-model call was rejected because on-demand throughput was not
supported for that model ID. The correct inference-profile route was then used.
This demonstrates a key rule: a model appearing in `ListFoundationModels` does
not mean its base model ID can be invoked in the caller's Region.

The global profile can route inference outside Singapore. Treat the Region of
the API call as distinct from a data-residency guarantee. Review AWS
cross-region inference documentation and organizational data-handling rules
before using global profiles with sensitive data.

## Quota comparison: why `vagent` throttles and `amit` works

The same Bedrock Service Quotas code was read in both profiles:

```text
L-AD940EDE
Global cross-region model inference tokens per day for Amazon Nova 2 Lite
```

| Profile | Observed quota | Adjustable | Observed outcome |
|---|---:|---:|---|
| `vagent` | `0` tokens/day | No | Nova 2 Lite profile call returned `ThrottlingException: Too many tokens per day`. |
| `amit` | `11,520,000,000` tokens/day | No | Nova 2 Lite profile call completed successfully. |

This is concrete evidence of an account-level/model-specific quota allocation
difference. The user stated that `vagent` is a free/unregistered account with
no payment card; that might be relevant to account eligibility, but it was not
independently verified in Billing or Account Management and must not be stated
as the proven root cause.

For `vagent`, do not keep retrying the same profile. The appropriate escalation
is account-owner review and AWS Support, using the model/profile, Region, quota
code, zero value, and observed throttling error. The quota is non-adjustable,
so an ordinary Service Quotas increase request is not the route to use.

## Direct model-inference evidence

All tests used non-sensitive fixed prompts, small output limits, and disabled
SDK retries. A failed call that returns no output/usage metadata is not evidence
of successful inference and should not be represented as billable success.

| Model/profile | Result | Evidence and interpretation |
|---|---|---|
| `global.amazon.nova-2-lite-v1:0` with `amit` | **Success** | A bounded security-validation prompt completed. Bedrock returned 169 input, 120 output, 289 total tokens. Output reached its token cap; it is proof of execution only, not proof that all generated security claims were correct. |
| `apac.anthropic.claude-3-haiku-20240307-v1:0` with `amit` | **Success** | A bounded exact-response test matched the expected text. Bedrock returned 18 input, 8 output, 26 total tokens. This is proof for this specific profile only. |
| `global.openai.gpt-5.6-luna` with `amit` | **Blocked** | `AccessDeniedException`: the model is not available for this account. The visible global profile is not an entitlement grant. |
| `global.anthropic.claude-haiku-4-5-20251001-v1:0` with `amit` | **Blocked** | `ResourceNotFoundException`: Anthropic model use-case details have not been submitted. Complete the provider use-case process and wait for propagation before any newly approved preflight. |
| `amazon.nova-2-lite-v1:0` base ID with `vagent` | **Blocked routing** | On-demand throughput was unsupported; an inference profile was required. |
| `global.amazon.nova-2-lite-v1:0` with `vagent` | **Blocked quota** | `ThrottlingException` caused by the observed zero daily Nova 2 Lite token quota. |

## Lower-cost model decision matrix

### Safe current direct Bedrock choices

The only current lower-cost direct Bedrock profiles verified in this account
context are:

```text
global.amazon.nova-2-lite-v1:0
apac.anthropic.claude-3-haiku-20240307-v1:0
```

Each successful request remains usage-billed. “Low-cost” does not mean free.
Always verify current model pricing, profile routing, and token limits before
production or repeated use.

### Explicitly not current direct choices

- **OpenAI GPT-5.6 Luna:** not available for the tested account. Do not assume
  Sol or Terra will work or use them as an automatic fallback; they were not
  tested in this low-cost scope.
- **Claude Haiku 4.5:** visible but requires Anthropic use-case details.
- **Claude Sonnet, Opus, and Fable:** intentionally not tested in the
  low-cost/basic scope. Do not infer availability from catalog visibility.
- **Gemini Flash-Lite:** not in the observed Bedrock foundation-model or
  inference-profile inventory. The existing POC's Gemini route is a separate
  external PlatformAI/provider integration.
- **DeepSeek Flash:** not in the observed Bedrock foundation-model or
  inference-profile inventory. It requires a separate external provider or a
  future Bedrock catalog/profile addition.
- **Cohere Embed models:** embeddings are not interchangeable with text
  generation through `Converse`; no embedding test was performed.
- **TwelveLabs Pegasus and xAI Grok:** profile/catalog visibility observed but
  no inference test was performed.

## Catalog snapshot observed with `amit`

Thirty foundation-model entries were catalog visible in Singapore. Active
system-defined inference profiles were also visible for several providers.
Visibility is recorded here for planning only.

| Provider | Catalog-visible families | Active-profile observation | Interpretation |
|---|---|---|---|
| Amazon | Nova 2 Lite, Nova Micro, Nova Lite, Nova Pro | Global Nova 2 Lite; APAC Nova Micro/Lite/Pro | Nova 2 Lite verified; the remaining Nova profiles untested in this handoff. |
| Anthropic | Claude 3 Haiku; Claude 3/3.5 Sonnet variants; Claude Sonnet 4/4.5/4.6/5; Claude Haiku 4.5; Claude Opus variants; Claude Fable variants | APAC profiles for older Haiku/Sonnet models and global profiles for newer models | Older Claude 3 Haiku verified. Haiku 4.5 has a provider use-case prerequisite. Other Claude profiles untested. |
| OpenAI | GPT-5.6 Luna, Sol, Terra | Global profiles visible | Luna explicitly unavailable to the tested account. Sol/Terra untested. |
| xAI | Grok 4.6 | Global profile visible | Untested. |
| Cohere | Embed v4, English v3, Multilingual v3 | Global Embed v4 profile visible | Untested embedding path. |
| TwelveLabs | Pegasus v1.2 | Global profile visible | Untested. |

## GUI versus direct Bedrock result

The direct CLI/SDK-style Bedrock call to:

```text
apac.anthropic.claude-3-haiku-20240307-v1:0
```

succeeded. Therefore, inability to test that profile from the GUI is not, by
itself, proof of an AWS Bedrock entitlement issue. Check the GUI/application
allowlist, selected provider route, model ID/profile string, Region, backend
credential path, and configured model policy.

The existing POC uses narrow allowlists by design. A frontend model selector or
external PlatformAI route is not a general Bedrock console and must not expose
all catalog-visible models automatically.

## Security-analysis learning boundary

One successful Nova 2 Lite prompt was asked to provide cautious guidance about
user-supplied ALAS/CVE/package data. The output correctly emphasized validation
and did not recommend immediate production patching, but it was truncated and
included details that require fact checking. In particular:

- Amazon Linux advisory/package repositories are authoritative sources for
  Amazon Linux advisory and fixed-package claims.
- Security Hub may aggregate findings but is not the canonical publisher of an
  Amazon Linux advisory.
- State Manager association logs are conditional evidence, not universal
  package inventory.
- Do not assume a particular local security-log path exists on every Amazon
  Linux 2 host.
- `yum check-update` can be useful discovery evidence but must run under an
  approved read-only process; it is not advisory proof.

For a real vulnerability, retain authoritative evidence in this order:

1. Official advisory/CVE and package repository metadata.
2. Target inventory, for example `rpm -q <package>`, collected under an
   approved SSM read-only execution process.
3. SSM Patch Manager compliance state.
4. Amazon Inspector package/resource finding details, when Inspector is
   enabled.
5. Development/canary patch test, approved change control, production
   maintenance, and post-change re-scan.

## AgentCore security posture demo: source versus deployment

A self-contained read-only AgentCore Runtime demo was created in the separate
AWSOps knowledge repository under:

```text
../awsops/docs/agentcore-security-posture-demo/
```

It is **not deployed**. The source implements AgentCore-compatible `/ping` and
`/invocations` HTTP endpoints and only permits bounded read operations:

- `ssm:DescribeInstanceInformation`
- `ssm:DescribeInstancePatchStates`
- `inspector2:BatchGetAccountStatus`
- `inspector2:ListFindings`
- `sts:GetCallerIdentity`

It cannot install patches, enable or scan Inspector, suppress findings, change
instances, create reports, persist memory, or invoke a model. The packaged
runtime policy is deliberately narrow and has a separate restrictive AgentCore
trust-policy template.

Local demo validation passed: Python unit tests, Python compilation, shell
syntax, IAM JSON parsing, sensitive-material scan, and whitespace check. No
AgentCore Runtime endpoint, IAM role, S3 artifact, CloudWatch resource, or
model-backed AgentCore request was created by this demo work.

## AgentCore cost learning

Published AgentCore Runtime microVM pricing observed during this work:

- active CPU: `$0.0895` per vCPU-hour;
- peak memory: `$0.00945` per GB-hour;
- per-second billing with a one-second minimum;
- inactive CPU I/O wait is not charged when no background work consumes CPU;
- 128 MB minimum memory billing.

Illustrative five-second session at one active vCPU and 0.25 GB peak memory:

```text
5 / 3600 × (1 × $0.0895 + 0.25 × $0.00945) ≈ $0.000128/request
100 requests/month   ≈ $0.013
10,000 requests/month ≈ $1.28
```

This excludes model tokens, CloudWatch logs/traces, S3 artifact storage,
network transfer, and existing Inspector assessment charges. It is an example,
not a cost commitment.

## Repository operating guidance

This repository's `AGENTS.md` remains authoritative:

- keep the POC small and preserve local simulation;
- do not deploy or mutate AWS without explicit approval for exact resources;
- never commit credentials, account IDs, tokens, real API keys, private
  endpoints, or raw sensitive evidence;
- use `./scripts/check.sh` for deterministic local validation;
- describe mock/live and browser/backend evidence boundaries honestly.

When future work targets another repository, inspect that repository's local
`AGENTS.md`, README, and documentation first. Use the repository as the tool
working directory or use absolute file paths; do not assume this repository's
rules apply elsewhere.

## Related AgentCore documents

- [AMIT_BEDROCK_MODEL_AVAILABILITY.md](AMIT_BEDROCK_MODEL_AVAILABILITY.md) —
  concise current model/profile matrix and direct test evidence.
- [NOVA_FAMILY_GUIDE.md](NOVA_FAMILY_GUIDE.md) — Nova profile routing,
  regionality, pricing, and data-residency cautions.
- [MODEL_COMPARE_DEMO.md](MODEL_COMPARE_DEMO.md) — POC comparison scope and
  external-provider boundary.
- [CODEX_BEDROCK_KEY_DEMO.md](CODEX_BEDROCK_KEY_DEMO.md) — a separate,
  model-scoped API-key proof with a different caller and evidence boundary.

## Revalidation commands

These commands read the current catalog and profiles without model-token spend:

```bash
aws --profile amit --region ap-southeast-1 bedrock list-foundation-models
aws --profile amit --region ap-southeast-1 bedrock list-inference-profiles
```

A model call is usage-billed. Any future preflight should have explicit owner
approval, a profile-specific allowlist, a fixed non-sensitive prompt, a small
output cap, no automatic fallback, and a recorded evidence/cost boundary.
