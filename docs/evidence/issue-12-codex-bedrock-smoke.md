# Issue #12 Codex-on-Bedrock E2E result

Date: 2026-09-01 (Asia/Singapore)
Base commit before the Region/key rotation: `449c839`
Change-budget result: 3 product/automation files plus small GUI/docs updates;
no new service, dependency, framework, or parallel runner.

## Result

`BLOCKED - OPENAI MODELS NOT ENABLED FOR THIS AWS ACCOUNT`

The bounded tests ran in temporary tmux session
`agentcore-codex-bedrock-test:smoke` using:

- Codex CLI `0.151.0`;
- provider `amazon-bedrock`;
- low reasoning and read-only sandbox;
- ephemeral isolated `CODEX_HOME` with no OpenAI subscription login;
- the protected `codex1` Bedrock key, never argv or output;
- `us-east-2` and the single `project/default` policy boundary.

## E2E progression

1. Singapore stopped before inference because Codex does not support
   `ap-southeast-1` for this provider.
2. The Singapore-scoped credential was deleted and verified absent.
3. A new 30-day `us-east-2` credential was created and atomically replaced
   only `codex1` in `/home/user/git/awsops/.env`; `nova` was preserved.
4. AWS IAM exposed and then accepted the exact Mantle permissions:
   `bedrock-mantle:CallWithBearerToken` on `*` and
   `bedrock-mantle:CreateInference` on the one default-project resource.
5. Luna and then Terra reached the real Mantle Responses endpoint, but both
   returned HTTP 401: the selected model is not available for this account.

No successful inference or answer was produced. No further model was tried.

## Codex2 token repair

A later manual Codex session used `codex2`, which still contained the deleted
Singapore credential and therefore returned `security token ... invalid`.
The protected `.env` was backed up and repaired so `codex1`, `codex2`, and
`codex_us` reference the one live service-specific credential; `nova` was
preserved. A fresh isolated `codex2` run then passed token authentication and
IAM authorization and reached the Ohio Mantle endpoint. It stopped only at the
same account-level model-unavailable response. This proves the invalid-token
defect is fixed, but successful model output remains blocked externally.

## Account availability discrepancy

The read-only `GetFoundationModelAvailability` API reported Luna and Terra as:

```text
authorizationStatus=AUTHORIZED
entitlementAvailability=AVAILABLE
regionAvailability=AVAILABLE
```

AWS Knowledge MCP research found no official documentation explaining why the
Mantle endpoint can still return this account-level 401. The error explicitly
directs the customer to AWS Sales. AWS Support/Sales is therefore the next
valid action; trying more models is not evidence-driven.

## Proof boundary

DEMO-PROVEN / TEST-PROVEN:

- key rotation, mode-600 `.env`, separate Nova/Codex values, provider routing,
  Region routing, real Mantle authentication, and least-privilege IAM path;
- the E2E failure is account model enablement, not OpenAI subscription auth.

NOT PROVEN:

- successful Codex model output through Bedrock;
- billed model usage or successful CloudTrail inference evidence.
