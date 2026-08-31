# AgentCore Internal AI Platform POC

GitHub [Issue #4](https://github.com/mytestlab123/AgentCore/issues/4) implemented
as a deliberately small 3-5 minute demo. Despite the repository name,
AgentCore Runtime is not required for this MVP.

The demo proves two things:

1. `demo-security-app` uses one platform key to call the approved Amazon Nova
   Lite model through one internal API without receiving AWS credentials.
2. The same platform rejects `model-premium` and records both decisions in one
   Logs view.

Only three views exist: Project, Playground, and Logs.

Management demo: [Issue #4 POC presentation](docs/demo.md).

## Local simulation

Prerequisites: Node.js 22+, npm 10+, Bash, and Windows Chrome for browser E2E.

```bash
./dev-local.sh
```

Open the exact URL printed by Vite. It prefers port 5173 and selects the next
available port when needed. Local mode makes no AWS calls and labels its model
response as simulated.

Demo flow:

1. Project: create the demo platform key, then mask it.
2. Playground: run the approved Nova Lite entry.
3. Playground: select Premium model and show `Not allowed for this project`.
4. Logs: show the Allowed and Denied records.

## Validate

```bash
./scripts/check.sh
```

This runs Bash syntax checks, frontend lint/tests/build, Python policy tests,
CDK TypeScript build, npm audits, and whitespace checks. It makes no AWS calls.

## Native Bedrock API key proof

[Issue #9](https://github.com/mytestlab123/AgentCore/issues/9) adds a separate,
GUI-backed proof of governed developer access using an AWS-native Bedrock API
key. It creates a 30-day Bedrock service-specific credential on a dedicated
IAM user, proves Nova Lite ALLOW and Nova Pro DENY through AWS IAM, and shows
sanitized CloudTrail evidence. The successful low-cost setup is retained for
repeat demos with `TTL=30-09-26` and `cleanup=review`; failed runs clean up.

Review the fixed scope without making an AWS call:

```bash
AWS_PROFILE=amit ./scripts/bedrock-api-key-poc.sh --plan
```

The live GUI is deliberately account- and caller-gated and loopback-only:

```bash
export EXPECTED_AWS_ACCOUNT='<exact-target-account-id>'
export EXPECTED_AWS_CALLER_ARN='<exact-target-caller-arn>'
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 \
  ISSUE9_CREDENTIAL_AGE_DAYS=30 ISSUE9_TTL=30-09-26 \
  ./dev-issue9.sh --approve-live
```

Open `http://127.0.0.1:5174/` and use **Generate key and run proof**. The full
secret remains in a mode-600 ignored file. Issue #12 adds an explicit
loopback-only reveal/copy action that holds the secret in page memory for 15
seconds and then masks it. CloudTrail propagation is asynchronous and does
not block the core HTTP 200/403/lifecycle proof. See the
[Issue #9 proof and developer guide](docs/ISSUE_9_BEDROCK_API_KEYS.md).

For the Codex handoff, run `./scripts/codex-bedrock-smoke.sh --check`, then
`./scripts/codex-bedrock-smoke.sh` and paste the copied key at its hidden
prompt. The default model is `openai.gpt-5.6-luna` with low reasoning. Set
`CODEX_BEDROCK_MODEL` to another explicitly verified cheap OpenAI Bedrock model
when needed; there is no automatic fallback. See
[the Issue #12 operator guide](docs/CODEX_BEDROCK_KEY_DEMO.md).

The Issue #12 GUI links directly to the real GitHub issue and includes
**Create Codex AI key**. Clicking it is an explicit AWS mutation: it creates a
separate model-scoped IAM user and 30-day Bedrock service-specific credential
with `TTL=01-10-26` and `cleanup=review`. At-rest IAM/key cost is zero; model
invocations remain usage-billed. The GUI refuses to guess or fall back when the
entered OpenAI model is unavailable in `ap-southeast-1`.

Explicit cleanup is separate and is not part of the repeat-demo path:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 \
  ./scripts/cleanup-issue9-retained.sh --approve-cleanup
```

With the local portal running, use its exact URL:

```bash
APP_URL=http://127.0.0.1:5174/ \
  EXPECTED_API_BASE_URL=http://127.0.0.1:9019 \
  ./scripts/browser-e2e.sh
```

The browser runner uses `playwright-core` with installed Windows Chrome. It
proves the three views, masked key, real HTTP 200 response, real IAM HTTP 403
denial, audit state, local-only browser networking, and exact browser cleanup.
Evidence is written under `~/.AGENTS-temp/AgentCore/browser-e2e/`.

## Minimal AWS architecture

```text
React / TypeScript UI
        |
        v
API Gateway -> Lambda -> APAC Amazon Nova Lite inference profile
                  |
                  +-> one DynamoDB table (key hash + request logs)
```

There is no Cognito, AgentCore Runtime, container build, CloudFront hosting,
second provider, analytics product, or multi-project framework.

## Deploy the live demo

The stack is billable. The script is account- and caller-gated, verifies the
Nova Lite inference profile, applies required tags, and defaults TTL to seven
days. Use a fully activated account with non-zero Bedrock quotas. The small
Lambda is embedded in the CloudFormation template, so no CDK bootstrap bucket
or ECR repository is added.

```bash
export EXPECTED_AWS_ACCOUNT='<exact-target-account-id>'
export EXPECTED_AWS_CALLER_ARN='arn:aws:iam::<exact-target-account-id>:user/amit'
AWS_PROFILE=amit ./deploy-all.sh --approve-deploy
```

The script writes only the API URL to untracked `frontend/.env.local`. Restart
the portal in live mode:

```bash
AGENTCORE_PORT=5174 ./dev-live.sh
```

Then run the same browser proof while allowing only the exact deployed API:

```bash
EXPECTED_API_BASE_URL="$(sed -n 's/^VITE_API_BASE_URL=//p' frontend/.env.local)" \
  APP_URL=http://localhost:5174/ ./scripts/browser-e2e.sh
```

The live API contract also has a secret-safe runner. `--full` requires Bedrock
quota; `--policy-only` proves key validation, denial, and audit logging without
calling the model:

```bash
./scripts/aws-api-e2e.sh --full
```

The first Project-page key creation stores only its SHA-256 hash in DynamoDB;
the full platform key is returned once and kept only in browser session
storage. The key-creation endpoint is intentionally single-use for this short,
TTL-bound demo. This is not a production credential lifecycle.

For a repeat demo, reset only that key record:

```bash
EXPECTED_AWS_ACCOUNT='<exact-target-account-id>' \
  AWS_PROFILE=amit ./scripts/reset-demo-key.sh --approve-reset
```

If Bedrock returns `Too many tokens per day`, stop retries and inspect the
account plan and applied quotas. A zero quota can be an account limitation; a
daily reset time is not documented. A tiny preflight for an activated account
is:

```bash
aws bedrock-runtime converse --profile amit --region ap-southeast-1 \
  --model-id apac.amazon.nova-lite-v1:0 \
  --messages '[{"role":"user","content":[{"text":"Reply: ok"}]}]' \
  --inference-config '{"maxTokens":8,"temperature":0}'
```

## Cleanup

```bash
export EXPECTED_AWS_ACCOUNT='<exact-target-account-id>'
AWS_PROFILE=amit ./destroy-all.sh --approve-destroy
```

Cleanup targets only `AgentCoreMvp`, verifies the stack is gone, and removes
the generated live frontend config.

## Security and cost boundary

- Never commit credentials, account IDs, API URLs, keys, or private endpoints.
- The Lambda limits prompt length and output tokens; API Gateway throttles the
  public demo endpoint to one request per second with a burst of two.
- Method-level API Gateway detailed metrics are disabled for this short POC;
  Lambda logs retain enough failure evidence for seven days.
- A screenshot proves UI state, not AWS execution. Live proof also requires the
  API result, DynamoDB log records, and stack evidence.
- Destroy the stack at the end of the demo or before its TTL.

See [Issue #4 reuse decision](docs/ISSUE_4_REUSE_DECISION.md) and the broader
[future architecture](docs/POC_ARCHITECTURE.md). AWS lifecycle actions are
tracked in [the resource record](docs/aws-resource-record.csv).
