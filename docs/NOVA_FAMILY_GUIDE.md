# Amazon Nova Family Guide

**For**: Amit's personal AWS development account (account identifier intentionally omitted)
**Purpose**: OpenCode integration testing and future AgentCore experiments
**Last updated**: 2026-09-01

> **Public-safe maintenance rule:** This is a dated POC reference, not a live
> entitlement, pricing, or data-residency guarantee. Recheck the exact model
> ID, inference profile, region, IAM policy, account access, and price before
> every run. External key files and environment files are intentionally not
> part of this repository; never paste their contents into Git, screenshots,
> logs, or chat.

---

## Nova Model Overview

### Current Generation (Nova 1.0)

**Nova Micro** - Fastest text-only model for speed-critical tasks
- Use for: Summarization, translation, classification
- Speed: Lowest latency in family
- Cost: Lowest per-token cost

**Nova Lite** - Fast, cost-effective multimodal (text + images + video input)
- Use for: Customer support, document processing, general automation
- Context: 300K tokens
- Cost: Balanced speed/performance/cost

**Nova Pro** - Balanced multimodal with strong accuracy
- Use for: Complex reasoning, multimodal analysis, agentic workflows
- Context: 300K tokens
- Capabilities: Text + image + video input, text output

---

### Next Generation (Nova 2.0)

**Nova 2 Lite** (GA, December 2025)
- **New**: Extended reasoning with step-by-step decomposition
- **New**: Three thinking intensity levels (low/medium/high)
- **New**: Built-in tools (code interpreter, web grounding)
- **New**: Remote MCP tool support
- **New**: 1M-token context window
- Use for: Business process automation, document workflows, everyday tasks
- Knowledge cutoff: October 2025

**Nova 2 Pro** (Preview - Requires Nova Forge Access)
- **Most capable reasoning model** in Nova family
- Multimodal: Text, image, video, speech input
- Use for: Advanced agentic tasks, multi-document analysis, video reasoning, software migrations
- Context: 1M tokens
- **Access**: Early preview for Nova Forge customers only; contact AWS account team

**Nova 2 Omni** (Preview - Requires Enablement)
- Multimodal reasoning and generation
- Input: Text, image, video, speech
- Output: Text + images
- Use for: Complex multimodal workflows requiring both understanding and generation
- **Access**: Preview requiring account enablement

---

## Choosing the Right Nova Model

### For Text-Only Tasks

| Speed Priority | Cost Priority | Recommended Model |
|----------------|---------------|-------------------|
| Highest | Lowest | Nova Micro |
| Balanced | Balanced | Nova 2 Lite |
| Advanced reasoning | Value for quality | Nova 2 Pro (if access granted) |

### For Multimodal Tasks (Images/Video)

| Complexity | Input Modalities | Output Needs | Recommended Model |
|------------|------------------|--------------|-------------------|
| Simple | Text + images | Text only | Nova Lite |
| Moderate | Text + images + video | Text only | Nova Pro or Nova 2 Lite |
| Complex | Text + images + video | Text only | Nova 2 Pro (preview) |
| Complex + generation | Text + images + video | Text + images | Nova 2 Omni (preview) |

### Cost-Performance Trade-offs

**For everyday development/prototyping**: Nova 2 Lite
- Best balance of reasoning + speed + cost for most tasks
- 1M context window supports long documents
- Built-in tools reduce integration overhead

**For production at scale**: Nova Lite or Nova Micro
- Lower per-token costs for high-volume workloads
- Mature, stable models (GA since 2024)
- Proven performance characteristics

**For advanced research**: Nova Pro v1 (currently available)
- Multimodal capabilities without preview access requirements
- Stable for experimentation
- Lower cost than Nova 2 Pro preview

---

## Pricing Snapshot

**Source**: AWS Console for US East (Ohio) region, captured 2026-09-01
**Service Tier**: Standard (default) unless specified
**Prices per 1M tokens**:

| Model | Input | Output | Cache Write | Cache Read | Notes |
|-------|-------|--------|-------------|------------|-------|
| **Nova 2 Lite** | $0.30 | $2.50 | — | — | Text tokens only |
| **Nova 2 Pro (Preview)** | $1.25 | $10.00 | — | — | Text tokens only; requires preview access |
| **Nova 2 Omni (Preview)** | $0.30 text<br>$0.30 image<br>$0.30 video<br>$1.00 audio | $2.50 text<br>$40.00 image | — | — | Multi-modal pricing; requires preview access |

**⚠️ Pricing Disclaimer**: Rates vary by:
- AWS Region (ap-southeast-1, us-east-2, etc.)
- Service tier (Standard, Priority, Flex)
- Inference profile type (In-Region, Geo, Global)
- Time (AWS adjusts pricing periodically)

**Always verify current pricing** before budgeting:
https://aws.amazon.com/bedrock/pricing/

Nova Lite v1 and Nova Pro v1 pricing not listed above; see AWS Bedrock pricing page for legacy model rates.

---

## Model IDs vs Inference Profile IDs

### Foundation Model IDs (Base IDs)

**Format**: `amazon.nova-{model}-v{version}:0`

Examples:
- `amazon.nova-lite-v1:0` (Nova Lite v1, base model)
- `amazon.nova-pro-v1:0` (Nova Pro v1, base model)
- `amazon.nova-2-lite-v1:0` (Nova 2 Lite, base model)

**Use when**: Calling in-Region inference within a single AWS Region where the model is natively hosted.

### Inference Profile IDs

**Format**: `{scope}.amazon.nova-{model}-v{version}:0`

**Scopes**:
- `apac.` - APAC regional profile (routes within Asia-Pacific regions)
- `us.` - US regional profile (routes within US regions)
- `eu.` - EU regional profile (routes within European regions)
- `jp.` - Japan regional profile (routes within Japanese regions)
- `global.` - Global profile (routes across all available regions worldwide)

Examples:
- `apac.amazon.nova-pro-v1:0` (Nova Pro routed within APAC)
- `global.amazon.nova-2-lite-v1:0` (Nova 2 Lite routed globally)

**Use when**: Cross-region inference is needed or when in-Region deployment is unavailable.

### Why Nova 2 Lite Requires Global Profile in Singapore Test

**Observed behavior (personal development account in `ap-southeast-1`)**:
- Base model ID `amazon.nova-2-lite-v1:0` **not available** for in-Region inference in Singapore
- `global.amazon.nova-2-lite-v1:0` **is available** and works
- `list-foundation-models` shows base model, but `list-inference-profiles` shows only global profile

**AWS Documentation confirms** (from Nova 2 Lite model card):
- In-Region availability: ❌ Not supported in ap-southeast-1
- Global inference: ✅ Supported in ap-southeast-1

**What this means**:
- Requests using `global.amazon.nova-2-lite-v1:0` from Singapore **route to another AWS Region** for processing
- AWS dynamically routes to available capacity (could be us-east-1, us-east-2, or other regions)
- **Data leaves Singapore** for inference processing

### ⚠️ Global Routing ≠ Data Residency Proof

**Critical distinction**:

✅ **What OpenCode/model reports**: "I am running in ap-southeast-1" (from model self-identification)
❌ **What this does NOT prove**: That inference processing stayed in Singapore

**Reality**:
- Model ID resolution happens in requesting region (Singapore)
- Actual inference processing happens in destination region (AWS-determined)
- Model self-report reflects the **profile's regional association**, not actual processing location
- Billing and CloudTrail logs show requesting region, not processing region

**For compliance/data residency**:
- Global profiles **cannot guarantee** data stays in Singapore
- Use APAC geo profile (`apac.`) if available (limits routing to Asia-Pacific regions)
- Use in-Region base model ID if data must stay in specific region (not available for Nova 2 Lite in Singapore)

---

## API Key Authentication vs Model Entitlement

### How Bedrock Authorization Works

**Two independent gates**:

1. **Authentication** (Who you are):
   - Bedrock API key (bearer token)
   - IAM credentials (access key + secret key)
   - IAM role (for EC2/Lambda/etc.)

2. **Entitlement** (What you can access):
   - Account-level model catalog
   - Model agreements/subscriptions
   - Preview/early access programs (Nova Forge, etc.)

### Creating Another API Key Cannot Grant Model Access

**Scenario**: The tested account sees Nova 2 Lite and Nova Pro v1, but not Nova 2 Pro or Omni Preview.

**Why creating a new API key won't help**:
- API keys authenticate to the **same AWS account**
- Model catalog is **account-level**, not key-level
- All keys in the same account see the same model catalog
- Keys inherit account's entitlements, they don't create new ones

**What's needed instead**:
- Request preview/early access from AWS account team
- Join Nova Forge program for Nova 2 Pro preview access
- Check account eligibility for preview models

### Verifying Model Entitlement

**Before creating API keys for new models**:

```bash
# Check foundation models available to account
aws bedrock list-foundation-models \
  --region ap-southeast-1 \
  --query 'modelSummaries[?contains(modelId, `nova-2`)].{ID:modelId,Status:modelLifecycle.status}'

# Check inference profiles available
aws bedrock list-inference-profiles \
  --region ap-southeast-1 \
  --query 'inferenceProfileSummaries[?contains(inferenceProfileId, `nova-2`)].inferenceProfileId'
```

If a model/profile doesn't appear in these lists, **creating an API key won't make it accessible**.

### Repeatable refresh sequence

Run these read-only checks with the explicitly approved profile before creating
or reusing a key. Save full output only in private evidence and redact account
IDs before sharing it:

```bash
AWS_PROFILE=amit aws sts get-caller-identity
AWS_PROFILE=amit aws bedrock list-foundation-models \
  --region ap-southeast-1 \
  --query 'modelSummaries[?contains(modelId, `nova`)].{id:modelId,status:modelLifecycle.status}'
AWS_PROFILE=amit aws bedrock list-inference-profiles \
  --region ap-southeast-1 \
  --query 'inferenceProfileSummaries[?contains(inferenceProfileId, `nova`)].inferenceProfileId'
```

Catalog visibility is only a preflight signal. A small, authorized inference
test is the proof of usable access; stop on an entitlement or IAM denial and
do not create more keys as a workaround.

---

## Current Account Evidence

**Account**: Personal development account (identifier omitted from this guide)

### ap-southeast-1 (Singapore) Catalog

**Available models**:
- Nova 2 Lite: `global.amazon.nova-2-lite-v1:0` (global profile only)
- Nova Pro v1: `amazon.nova-pro-v1:0` (base model)
- Nova Pro v1: `apac.amazon.nova-pro-v1:0` (APAC geo profile)

**Not available**:
- Nova 2 Pro Preview (any profile)
- Nova 2 Omni Preview (any profile)
- In-Region Nova 2 Lite base model

### us-east-2 (Ohio) Catalog

**Available models**:
- Nova 2 Lite: Inference profiles available (geo + global)
- Nova Pro v1: Base model + profiles available

**Not available**:
- Nova 2 Pro Preview
- Nova 2 Omni Preview

### API Keys Created

**For Nova 2 Lite + Nova Pro v1 (Singapore)**:
- Credential file: `/home/user/git/awsops/.key` (mode 600; value not documented)
- Region: `ap-southeast-1`
- Verified working with OpenCode

**No separate keys created for Nova 2 Pro/Omni Preview** - account entitlement is absent, so keys would be ineffective.

---

## OpenCode Integration Wrappers

### Wrapper Scripts

**Location**: `/home/user/git/awsops/scripts/opencode/`

**Available wrappers**:
1. `run-nova-2-lite.sh` - Nova 2 Lite via global profile
2. `run-nova-pro-apac.sh` - Nova Pro v1 via APAC profile (verified route)
3. `run-nova-pro.sh` - Legacy alias (points to APAC wrapper)

### Usage Pattern

```bash
# Example: Nova 2 Lite streaming test
cd /home/user/git/awsops/scripts/opencode
./run-nova-2-lite.sh "Explain inference profiles in one sentence"
```

**What the wrappers do**:
1. Source `/home/user/git/awsops/.key` (mode 600; value is never printed)
2. Set `AWS_REGION`, `AWS_BEARER_TOKEN_BEDROCK`
3. Set OpenCode provider configuration
4. Execute `opencode` with model-specific parameters

**Security**: Bearer token values are **never exposed in command line or logs**. Users should not paste secrets into terminal; wrappers handle secure credential loading.

### Observed OpenCode Routing Caveat

**Issue**: Base model ID with OpenCode streaming produces IAM policy denial

**Scenario tested**:
- Direct Bedrock Converse API call to base `amazon.nova-pro-v1:0` in `ap-southeast-2` (Sydney): ✅ Works
- OpenCode streaming call to same base model ID from Singapore: ❌ Denied by IAM policy

**Root cause**: OpenCode resolved base model ID to APAC inference profile, but current API key policy doesn't grant `apac.*` profile ARNs.

**Verified working route**: Use APAC profile explicitly:
- Model ID: `apac.amazon.nova-pro-v1:0`
- Region: `ap-southeast-1`
- OpenCode provider: `amazon-bedrock`
- Result: ✅ Streaming works, IAM policy accepts profile ARN

**Recommendation**: For OpenCode integration, always use explicit inference profile IDs, not base model IDs, to avoid IAM policy mismatches.

---

## Standard Comparison Prompt

**Use this prompt to verify model identity and capabilities**:

```
Which model are you using? What can you do? Reply with the model ID, region, and three capabilities in five short lines.
```

**Expected response pattern**:
```
Model: amazon.nova-2-lite-v1:0 (or profile ID)
Region: ap-southeast-1 (or processing region)
1. Multimodal understanding (text, images, video)
2. Extended reasoning with step-by-step logic
3. Built-in code interpreter and web grounding
```

### ⚠️ Self-Reported Region is Not Proof

**What the model reports**: Often the **requesting region** or **profile's regional scope**, not the actual processing location.

**Why this matters**:
- Global profiles can process in any region
- Geo profiles can process in any region within the geography
- Model doesn't have visibility into AWS's internal routing decisions

**For compliance verification**, use:
- CloudTrail logs (show requesting region, not processing region)
- AWS Bedrock console metrics (show profile usage, not physical location)
- **In-Region base model IDs** if data residency is required (not available for all models in all regions)

---

## Enablement Checklist for Nova 2 Pro/Omni Preview

### Step 1: Request Preview Access

**For Nova 2 Pro Preview**:
1. Contact AWS account team via AWS Support case
2. Category: Amazon Bedrock → Model Access
3. Request: "Early access to Nova 2 Pro Preview via Nova Forge program"
4. Include the target account ID in the private support form (do not commit it here)
5. Justification: Personal development/POC for AgentCore experimentation

**For Nova 2 Omni Preview**:
1. Same process as Nova 2 Pro
2. Request: "Preview access to Amazon Nova 2 Omni"
3. Expected timeline: 3-5 business days for review

### Step 2: Verify Model Availability

**After approval notification**:

```bash
# Recheck foundation models
aws bedrock list-foundation-models \
  --region us-east-2 \
  --query 'modelSummaries[?contains(modelId, `nova-2-pro`) || contains(modelId, `nova-2-omni`)].{ID:modelId,Status:modelLifecycle.status}' \
  --output table

# Recheck inference profiles
aws bedrock list-inference-profiles \
  --region us-east-2 \
  --query 'inferenceProfileSummaries[?contains(inferenceProfileId, `nova-2-pro`) || contains(inferenceProfileId, `nova-2-omni`)].{ID:inferenceProfileId,Type:type}' \
  --output table
```

**If models don't appear**: Wait 24 hours for account catalog refresh, then contact AWS Support if still unavailable.

### Step 3: Create Specific API Key (Only After Confirmation)

**DO NOT create keys before confirming model availability**

The repository's authoritative workflow uses an IAM service-specific
credential. The one-time response contains secret material, so create the
directory with a restrictive umask, write only to a private per-user path,
and never print or commit the response:

```bash
umask 077
private_dir="${XDG_STATE_HOME:-$HOME/.local/state}/agentcore/bedrock"
install -d -m 700 "$private_dir"
credential_file="$private_dir/nova-2-pro-credential.json"

aws iam create-service-specific-credential \
  --profile "${AWS_PROFILE:?set the approved profile}" \
  --user-name "${BEDROCK_KEY_USER:?set the dedicated IAM user}" \
  --service-name bedrock.amazonaws.com \
  --credential-age-days 30 \
  >"$credential_file"
chmod 600 "$credential_file"

# Use the secret once, then remove the response file when no longer needed.
rm -f -- "$credential_file"
```

Prefer the repeatable repository wrapper, which applies the same private
evidence and cleanup controls:

```bash
./scripts/bedrock-api-key-poc.sh --plan
```

The credential response and any bearer token must never be logged, placed in
`/tmp`, added to shell history, or committed. Keep only sanitized metadata
(for example, a short fingerprint) in private evidence. Removing the local
file does not revoke the AWS credential; use the IAM
`delete-service-specific-credential` operation through the owning cleanup
workflow when the credential itself must be revoked.

### Step 4: Update IAM Policy for New Profiles

**If new inference profile ARNs are needed**:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "bedrock:InvokeModel",
    "Resource": [
      "arn:aws:bedrock:*::foundation-model/amazon.nova-2-pro-*",
      "arn:aws:bedrock:*:<ACCOUNT_ID>:inference-profile/*nova-2-pro*",
      "arn:aws:bedrock:*:<ACCOUNT_ID>:inference-profile/*nova-2-omni*"
    ]
  }]
}
```

### Step 5: Create OpenCode Wrapper (Only After Verification)

**Template** (`run-nova-2-pro-preview.sh`):

```bash
#!/bin/bash
set -euo pipefail

# Source Nova 2 Pro preview key (after creation)
source /home/user/git/awsops/.key

# Set region and profile
export AWS_REGION=us-east-2
export OPENCODE_MODEL="amazon.nova-2-pro-preview-v1:0"  # or actual model ID
export OPENCODE_PROVIDER="amazon-bedrock"

# Execute OpenCode with Nova 2 Pro
opencode "$@"
```

**DO NOT create this wrapper until**:
1. AWS confirms preview access
2. `list-foundation-models` shows Nova 2 Pro
3. API key is created and verified working

---

## Official AWS Resources

### Model Cards and Documentation

- **Nova 2 Announcement**: https://aws.amazon.com/about-aws/whats-new/2025/12/nova-2-foundation-models-amazon-bedrock
- **Nova 2 Lite Model Card**: https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-2-lite.html
- **Nova Pro v1 Model Card**: https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-pro.html
- **Nova 2 Omni Preview Announcement**: https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-nova-2-omni-preview/

### Bedrock Platform Documentation

- **Bedrock Pricing**: https://aws.amazon.com/bedrock/pricing/
- **Inference Profiles Guide**: https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html
- **Using Inference Profiles**: https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-use.html

### OpenCode Provider Configuration

- **Amazon Bedrock Provider** (OpenCode docs): https://opencode.ai/docs/providers/
- **Authentication Guide** (AWS Bedrock API keys): https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html

---

## Appendix: Model Selection Decision Tree

```
START: What's your use case?

├─ Text-only, speed-critical
│  └─ Nova Micro
│
├─ Text-only, everyday tasks
│  └─ Nova 2 Lite (current account route: global profile)
│     └─ Fallback: Nova Lite v1
│
├─ Text + images, simple workflows
│  └─ Nova Lite v1
│
├─ Text + images/video, moderate complexity
│  ├─ Prototype/dev: Nova Pro v1
│  └─ Production: Nova 2 Lite (if access granted)
│
├─ Complex reasoning, agentic tasks
│  ├─ If preview access: Nova 2 Pro
│  └─ If no preview: Nova Pro v1
│
└─ Multimodal generation (text + images output)
   └─ Nova 2 Omni Preview (requires enablement)
      └─ Fallback: Use Nova Pro + external image generation
```

---

**Guide version**: 1.1 (2026-09-02)
**Account context**: Personal development account (identifier omitted)
**Repository**: `/home/user/git/AgentCore/docs/NOVA_FAMILY_GUIDE.md`
**Maintenance**: Verify pricing and model availability after AWS announcements
or before a new demo; keep credentials and raw account evidence outside Git.
