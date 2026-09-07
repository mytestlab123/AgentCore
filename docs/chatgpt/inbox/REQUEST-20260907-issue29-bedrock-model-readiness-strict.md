# STRICT implementation contract — Issue #29

Issue:
https://github.com/mytestlab123/AgentCore/issues/29

## Status

**PLANNING ONLY — HOLD ACTIVE.**

This file contains the authoritative implementation contract for Issue #29.
It authorizes no AWS mutation, IAM change, credential copy, public exposure, or feature implementation yet.

Codex must not implement until Amit/ChatGPT explicitly lifts the hold in the linked Draft PR.

## Selected milestone

**One-command Amazon Bedrock verified model readiness gate.**

User question:

> Can this exact Bedrock inference profile work now under this exact AWS identity + Region?

The proof deliberately separates catalog/profile visibility from real bounded inference.

## One problem, one happy path, one command, one proof, one result

Target happy path:

```text
explicit AWS profile + Region
-> validate operator-selected LIVE mode
-> verify caller/Region preflight
-> verify exact allowlisted inference profile is discoverable
-> make one tiny fixed non-sensitive Converse request
-> require real response + Bedrock usage metadata
-> print MODEL_READINESS=LIVE_PASS
-> write sanitized evidence only
```

Supported result labels:

```text
MODEL_READINESS=MOCK
MODEL_READINESS=LIVE_PASS
MODEL_READINESS=LIVE_BLOCKED
```

A blocked result must also include exactly one sanitized blocker category:

```text
BLOCKER_CATEGORY=PROFILE
BLOCKER_CATEGORY=REGION
BLOCKER_CATEGORY=IAM
BLOCKER_CATEGORY=MODEL_ACCESS
BLOCKER_CATEGORY=ROUTING
BLOCKER_CATEGORY=QUOTA
BLOCKER_CATEGORY=PROVIDER
BLOCKER_CATEGORY=UNKNOWN
```

No fallback is permitted.

## Frozen live target

The first implementation supports exactly one approved live target:

```text
AWS profile alias: amit
AWS Region: ap-southeast-1
Inference profile: global.amazon.nova-2-lite-v1:0
Provider: Amazon
Model family: Nova 2 Lite
```

This choice follows current repository evidence:

- `docs/AMIT_BEDROCK_MODEL_AVAILABILITY.md`
- `docs/kiro-learning-bedrock-ai-models.md`

Those records show a bounded successful inference for this exact profile under the local `amit` profile in Singapore.

Do not broaden the allowlist in this milestone.

## Operating modes

### MOCK mode

Purpose: demonstrate contract/output shape without AWS.

Requirements:

- makes zero AWS calls;
- performs no credential lookup that triggers network activity;
- prints `MODEL_READINESS=MOCK`;
- prints the fixed expected profile/Region in sanitized form;
- never claims LIVE availability.

### LIVE mode

Purpose: prove current readiness for the exact allowlisted path.

Requirements:

- must be explicitly selected;
- must require explicit profile and Region input or equivalent explicit environment configuration;
- must reject profile or Region mismatch before paid inference;
- must not silently default to another configured AWS profile;
- performs read-only discovery/preflight followed by at most one tiny billed inference;
- must print exactly `LIVE_PASS` or `LIVE_BLOCKED`.

## Proposed operator command

Codex may refine quoting/flag syntax to fit existing repository conventions, but preserve this contract:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 \
  ./scripts/bedrock-model-readiness.sh --live
```

MOCK path:

```bash
./scripts/bedrock-model-readiness.sh --mock
```

No positional model/provider argument is required for this milestone because the allowlist contains exactly one profile.

## Exact implementation scope

Expected product files — maximum three:

1. `scripts/bedrock-model-readiness.sh`
   - owns MOCK/LIVE mode selection;
   - validates exact profile + Region;
   - performs the smallest read-only preflight;
   - performs one bounded inference only in explicit LIVE mode;
   - normalizes errors into one blocker category;
   - emits sanitized terminal/evidence fields.

2. `scripts/test-bedrock-model-readiness.sh`
   - dependency-light offline tests;
   - no AWS/network calls;
   - proves MOCK output, allowlist enforcement, fail-closed input handling, error classification fixtures, and no fallback contract.

3. Optional tiny helper only if unavoidable for parsing a Bedrock response safely.
   - Prefer no third product file.
   - Do not add Python/Node merely for convenience if Bash + existing tools are sufficient.

Documentation/evidence:

- update an existing proof/learning document only after implementation evidence exists;
- avoid a new README or documentation hierarchy;
- the STRICT contract itself is planning metadata, not implementation proof.

Default implementation budget:

```text
<= 3 product files
<= 200 non-generated changed lines across product files
```

If implementation requires more, post BLOCKER and stop before exceeding the budget.

## Deterministic allowlist contract

For Issue #29, the LIVE path must accept only:

```text
profile alias = amit
region        = ap-southeast-1
model profile = global.amazon.nova-2-lite-v1:0
```

If the operator provides or environment resolves to a different profile/Region/model target:

```text
MODEL_READINESS=LIVE_BLOCKED
BLOCKER_CATEGORY=PROFILE|REGION|MODEL_ACCESS
```

as appropriate.

Do not substitute:

- APAC Nova Lite v1;
- Nova Pro;
- Claude 3 Haiku;
- Claude Haiku 4.5;
- GPT-5.6 Luna/Sol/Terra;
- Gemini;
- DeepSeek;
- another Region;
- another local AWS profile.

## Read-only preflight

Before the billed inference, use only the smallest checks necessary to prove the expected path.

At minimum:

1. verify explicit mode is LIVE;
2. verify `AWS_PROFILE` resolves exactly to the approved alias;
3. verify `AWS_REGION` resolves exactly to `ap-southeast-1`;
4. authenticate with STS or equivalent read-only identity check;
5. verify the exact inference profile is discoverable/ACTIVE where the API exposes that state;
6. optionally inspect the exact known Nova 2 Lite quota only if this can be done cheaply/read-only and without adding fragile complexity;
7. stop before inference on any unexpected preflight result.

Do not perform broad inventory scans merely because they are available.

Do not print account IDs or full ARNs in public terminal/evidence output.

## Bounded inference contract

Use one fixed public-safe prompt such as:

```text
Reply with exactly: BEDROCK_READY
```

Requirements:

- prompt is fixed in repository code;
- no user-provided sensitive input;
- use the exact inference profile `global.amazon.nova-2-lite-v1:0`;
- tiny output cap, target <= 8 output tokens unless API semantics require a slightly different minimum;
- SDK/CLI retries disabled for the inference request;
- one inference attempt only for a clean run;
- no model fallback;
- no retry loop for entitlement/quota/provider errors;
- success requires both a real response and returned usage metadata;
- response content may be checked for the fixed marker, but usage metadata is required so catalog visibility cannot be mistaken for execution proof.

If the API/CLI path cannot reliably expose usage metadata with the smallest supported call, post BLOCKER rather than weakening the PASS definition silently.

## Expected terminal output

### MOCK

Example shape:

```text
MODEL_READINESS=MOCK
PROFILE_ALIAS=amit
REGION=ap-southeast-1
MODEL_PROFILE=global.amazon.nova-2-lite-v1:0
AWS_CALLS=0
```

### LIVE PASS

Example shape:

```text
MODEL_READINESS=LIVE_PASS
PROFILE_ALIAS=amit
REGION=ap-southeast-1
MODEL_PROFILE=global.amazon.nova-2-lite-v1:0
INFERENCE=PASS
USAGE_METADATA=PRESENT
FALLBACK_USED=NO
```

### LIVE BLOCKED

Example shape:

```text
MODEL_READINESS=LIVE_BLOCKED
PROFILE_ALIAS=amit
REGION=ap-southeast-1
MODEL_PROFILE=global.amazon.nova-2-lite-v1:0
BLOCKER_CATEGORY=<one approved category>
FALLBACK_USED=NO
```

Do not expose raw AWS exception payloads by default.
A short sanitized message may be printed for operator troubleshooting if it contains no account identifiers, ARNs, request payloads, credentials, or private endpoints.

## Blocker classification guidance

Normalize only enough to make the result operationally useful.

### PROFILE

Examples:

- `AWS_PROFILE` missing in LIVE mode;
- profile is not exactly `amit`;
- profile cannot authenticate because expected local credentials/session are absent.

### REGION

Examples:

- `AWS_REGION` missing;
- Region is not exactly `ap-southeast-1`;
- selected API endpoint is incompatible with the frozen path.

### IAM

Examples:

- explicit AccessDenied for STS/Bedrock read/invoke operation;
- identity policy blocks exact inference-profile invocation.

### MODEL_ACCESS

Examples:

- exact profile unavailable/not entitled for the account;
- profile disappeared or is no longer available.

### ROUTING

Examples:

- direct base-model invocation required an inference profile;
- configured endpoint/model-profile combination is invalid.

### QUOTA

Examples:

- known daily-token quota is zero;
- first bounded request is throttled by model-specific quota/capacity state.

### PROVIDER

Examples:

- provider onboarding/terms prerequisite blocks access.

### UNKNOWN

Use only when the error cannot be safely and deterministically mapped without adding fragile parsing.

Do not build a large error ontology.

## Safety and credential guardrails

Mandatory:

- no AWS credential creation;
- no API-key creation;
- no credential copy to EC2/LibreChat/another host;
- no credential rotation;
- no IAM changes;
- no SCP/Organizations changes;
- no quota mutation/request;
- no provider subscription/onboarding;
- no support case creation;
- no AWS infrastructure/resource creation;
- no public endpoint/network exposure;
- no raw secret or credential logging;
- no account ID or full ARN committed;
- no raw Bedrock response committed if it contains private metadata;
- no shell history command should contain credentials/tokens.

The local profile is an operator-owned credential source and remains outside Git.

## Cost guardrails

LIVE mode is usage-billed.

Therefore:

- run read-only checks before inference;
- one fixed tiny prompt;
- tiny output cap;
- retries disabled;
- no provider/model comparison;
- no second paid attempt after PASS;
- no fallback after BLOCKED;
- do not claim a fixed dollar amount unless current pricing + measured usage are explicitly calculated later;
- one successful bounded request is sufficient evidence.

## Explicit non-goals

Do not add or change:

- LibreChat;
- frontend/UI;
- provider/model dropdown;
- AgentCore Harness;
- AgentCore Runtime;
- AgentCore Gateway;
- AgentCore Policy/Temporal Policy;
- Identity;
- Memory;
- RAG;
- MCP server/tooling;
- AWS Agent Toolkit;
- EC2/Inspector/SSM integration;
- remediation;
- approval workflow;
- CloudFormation/CDK/Terraform resources;
- API Gateway/Lambda;
- public networking;
- new provider credentials;
- model benchmark/quality scoring;
- new external providers.

## Focused regression test

The offline test must prove at minimum:

1. MOCK mode returns `MODEL_READINESS=MOCK`;
2. MOCK mode executes no AWS command (use a fake/stub `aws` executable or equivalent deterministic interception);
3. LIVE mode without explicit approved profile is BLOCKED before inference;
4. LIVE mode with wrong Region is BLOCKED before inference;
5. target profile is exactly `global.amazon.nova-2-lite-v1:0`;
6. no fallback profile/model strings exist in the executable path;
7. representative sanitized fixture errors map to the intended blocker category;
8. existing shell syntax checks remain green.

Then run:

```bash
./scripts/test-bedrock-model-readiness.sh
./scripts/check.sh

git diff --check
```

Do not add a new test framework.

## Validation evidence Codex must post before review

After HOLD is explicitly lifted and implementation is complete, Codex must post one concise PR comment containing:

```text
IMPLEMENTATION SUMMARY
Changed product files: <list>
Non-generated changed lines: <count>
Mock test: PASS/BLOCKED
Focused regression test: PASS/BLOCKED
Repository check: PASS/BLOCKED
Live execution approved by Amit: YES/NO
Live result: LIVE_PASS / LIVE_BLOCKED / NOT_RUN
Profile alias: amit
Region: ap-southeast-1
Inference profile: global.amazon.nova-2-lite-v1:0
Usage metadata: PRESENT / ABSENT / NOT_RUN
Blocker category: <category or N/A>
Fallback used: NO
AWS mutation performed: NO
IAM change performed: NO
Credential copied/created: NO
Public exposure created: NO
Secrets/account IDs/ARNs committed: NO
```

If LIVE was not separately approved by Amit, `Live result` must be `NOT_RUN`.
Implementation/tests may still be reviewed without pretending live readiness is proven.

## NO-GO conditions

Stop and post BLOCKER if any of the following occurs:

1. current `main`/branch does not match the named Issue/PR;
2. implementation requires more than the approved file/line budget without review;
3. explicit `amit` profile cannot be used locally;
4. exact Region cannot remain `ap-southeast-1`;
5. exact Nova 2 Lite profile is no longer discoverable/usable;
6. success requires IAM mutation;
7. success requires quota/support/provider changes;
8. success requires copying credentials/keys/tokens to another host;
9. success requires a second model/provider/Region;
10. success requires AWS infrastructure creation;
11. retries/fallback are required to manufacture a PASS;
12. output cannot be sanitized without losing the PASS/BLOCKED evidence;
13. implementation would confuse MOCK with LIVE;
14. secret/account-specific material would need to enter Git.

BLOCKER format:

```text
BLOCKER
Expected: <contract expectation>
Actual: <observed repository/AWS reality>
Category: <PROFILE|REGION|IAM|MODEL_ACCESS|ROUTING|QUOTA|PROVIDER|UNKNOWN>
Why blocked: <short sanitized reason>
Fallback attempted: NO
AWS mutation performed: NO
Decision required: ChatGPT / Amit
```

Do not substitute architecture after a NO-GO.

## Review and merge gate

Codex must not:

- implement before HOLD LIFTED;
- mark the Draft PR Ready;
- merge the PR;
- close Issue #29;
- create another Issue/branch/PR for the same milestone;
- change AWS/IAM/credentials to make the test pass.

When implementation is complete, Codex posts the required evidence summary and stops.

ChatGPT/Amit will review the full diff and decide Ready/merge/closure separately.

## Definition of done

A reviewer can run one repository-owned command and truthfully distinguish:

```text
MOCK
LIVE_PASS
LIVE_BLOCKED
```

for exactly `global.amazon.nova-2-lite-v1:0` under the approved local `amit` profile in `ap-southeast-1`, with no fallback, no secret copying, and no AWS mutation.