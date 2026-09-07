# Amit Bedrock model availability — verified snapshot

**Status:** validated snapshot, 2026-09-07

**Scope:** Amazon Bedrock access using the locally configured `amit` profile in
`ap-southeast-1` (Singapore). This document intentionally omits the AWS account
identifier, credentials, raw model transcripts, and exact per-run timestamps.

> **Claim boundary:** catalog visibility and an `ACTIVE` inference profile do
> **not** prove successful inference. Only rows labelled **Verified inference**
> were invoked successfully in this snapshot. Re-check model access, profile,
> Region, quota, price, and provider terms before every use.

## Bottom line

Only these lower-cost text-generation profiles are directly verified as working
with the `amit` profile:

| Provider | Model / inference profile used | Status | Evidence |
|---|---|---|---|
| Amazon | `global.amazon.nova-2-lite-v1:0` | **Verified inference** | A bounded `Converse` request completed successfully through the required global profile. Bedrock returned usage metadata. |
| Anthropic | `apac.anthropic.claude-3-haiku-20240307-v1:0` | **Verified inference** | A bounded `Converse` request returned the expected fixed response exactly; Bedrock reported 18 input, 8 output, 26 total tokens. |

These are not provider-wide approvals. The current/latest low-cost provider
profiles below show why a catalog entry or active profile must never be called
“supported” before an actual inference result.

## Latest lower-cost profile preflights

Each call used an exact fixed non-sensitive prompt, `maxTokens=8`, and retries
disabled. Neither failed call returned output or usage metadata.

| Provider | Profile tested | Result | Meaning |
|---|---|---|---|
| OpenAI | `global.openai.gpt-5.6-luna` | **Blocked** — `AccessDeniedException`: model is not available for this account | The profile is visible but not entitled/available to this account. Do not retry or substitute Sol/Terra without a separate approval. |
| Anthropic | `global.anthropic.claude-haiku-4-5-20251001-v1:0` | **Blocked** — `ResourceNotFoundException`: Anthropic model use-case details have not been submitted | Complete the Anthropic use-case-details form, wait for propagation, then run a new approved preflight. This is an AWS provider-access prerequisite, not a GUI defect. |

**Current answer to “low-cost models without a further entitlement process”:**
Nova 2 Lite and the older Claude 3 Haiku profile are verified. OpenAI Luna and
current Claude Haiku 4.5 are not currently usable by this account.

## Important model-ID rule

Use the inference profile rather than assuming the base catalog model ID is
invocable in Singapore. For example, the base Nova 2 Lite ID
`amazon.nova-2-lite-v1:0` was catalog-visible but rejected for on-demand
throughput. The corresponding global profile above completed successfully.

See [NOVA_FAMILY_GUIDE.md](NOVA_FAMILY_GUIDE.md) for the existing explanation
of Nova profile routing and its data-residency boundary.

## Catalog-visible model inventory

The following 30 foundation-model entries were visible. This is **catalog
availability**, not a grant of successful inference access.

| Provider | Catalog-visible models | Active inference-profile situation | Snapshot conclusion |
|---|---|---|---|
| Amazon | Nova 2 Lite; Nova Micro; Nova Lite; Nova Pro | Global Nova 2 Lite; APAC Nova Micro/Lite/Pro | Nova 2 Lite verified; other Nova profiles active but untested here. |
| Anthropic | Claude Opus 5; Opus 4.8/4.7/4.6/4.5; Claude Haiku 4.5; Claude 3 Haiku; Claude Sonnet 5/4.6/4.5/4; Claude 3.5 Sonnet (v1/v2); Claude 3 Sonnet (base, 28K, 200K); Claude Fable 5/5.1 | APAC profiles for Claude 3 Haiku, Claude 3/3.5 Sonnet, and Claude Sonnet 4; global profiles for newer Claude models | Claude 3 Haiku verified. Haiku 4.5 currently requires Anthropic use-case details; all other Claude models remain untested. |
| OpenAI | GPT-5.6 Luna, Sol, Terra | Global profiles visible for all three | Luna is explicitly unavailable to this account. Sol/Terra were intentionally not tested because they are not low-cost scope. |
| xAI | Grok 4.6 | Global profile visible | Untested. |
| Cohere | Embed v4, Embed English v3, Embed Multilingual v3 | Global Embed v4 profile visible | Untested. Embedding APIs are not interchangeable with `Converse` text-generation tests. |
| TwelveLabs | Pegasus v1.2 | Global profile visible | Untested. |

## External-provider boundary: Gemini and DeepSeek

- **Gemini Flash-Lite:** no Gemini model or inference profile was returned by
  this Bedrock catalog/profile inventory. The existing POC's Gemini path is an
  external PlatformAI/provider integration with its own endpoint, credentials,
  governance, price, and proof. It is not a direct Bedrock entitlement.
- **DeepSeek Flash:** no DeepSeek model or inference profile was returned by
  this Bedrock catalog/profile inventory. It likewise needs a separately
  configured external provider or a future Bedrock catalog/profile addition;
  neither was tested here.
- **AgentCore Runtime:** these are direct Bedrock inference checks. They do not
  prove an AgentCore Runtime deployment, Gateway, Memory, or application-level
  integration.
- **Security correctness:** a model response is advice, not proof of CVE,
  patch, Inspector, or SSM state. Verify with official advisories and live
  read-only AWS evidence before remediation.

## Verification method

All direct Bedrock preflights used:

- explicit `amit` profile and `ap-southeast-1` Region;
- the stated system-defined inference profile ID;
- a fixed non-sensitive prompt;
- a small output-token cap;
- SDK retries disabled;
- success recorded only when Bedrock returned a response and usage metadata.

The successful Claude 3 Haiku test is deliberately low cost and bounded. It is
proof for that specific older Haiku profile only, not provider-wide approval or
production readiness.

## Operational selection guidance

1. For an existing low-cost verified text-generation path, use the verified
   **Claude 3 Haiku APAC profile** or the verified **Nova 2 Lite global
   profile**, subject to current pricing and data-routing review.
2. For Claude Haiku 4.5, first complete the Anthropic use-case-details process;
   wait for propagation and perform a newly approved bounded preflight.
3. For OpenAI Luna, access must be enabled for the account; the visible profile
   alone is insufficient. Do not automatically fall back to a more expensive
   OpenAI profile.
4. Gemini and DeepSeek need an external-provider integration. Keep provider
   credentials out of this repository and apply separate allowlist, egress,
   cost, and data-handling controls.
5. Use a profile-specific allowlist. Stop on `AccessDenied`,
   `ResourceNotFoundException`, `ValidationException`, or
   `ThrottlingException` and inspect the exact model/profile, quota, provider
   terms, and account state instead of blind retries.

## Related repository material

- [NOVA_FAMILY_GUIDE.md](NOVA_FAMILY_GUIDE.md) — Nova routing, model IDs, and
  cost/residency cautions.
- [MODEL_COMPARE_DEMO.md](MODEL_COMPARE_DEMO.md) — POC comparison boundary.
- [CODEX_BEDROCK_KEY_DEMO.md](CODEX_BEDROCK_KEY_DEMO.md) — separate
  model-scoped API-key proof; do not assume its result applies to the direct
  `amit` CLI identity above.

## Revalidation commands

These read-only commands re-check inventory without spending model tokens:

```bash
aws --profile amit --region ap-southeast-1 bedrock list-foundation-models
aws --profile amit --region ap-southeast-1 bedrock list-inference-profiles
```

A model invocation is usage-billed. Run one only with explicit approval and a
small fixed prompt/output cap.
