# AgentCore Test Proof

Last verified: 1 September 2026, 00:09 SGT

## Issue #15 two-provider comparison

Last verified: 1 September 2026, 18:51 SGT

One live synthetic text prompt returned two independent successful responses:

| Provider | Model | Result | Completion |
| --- | --- | --- | --- |
| Amazon Bedrock | Nova 2 Lite | ALLOW; response present | `end_turn` |
| GovTech PlatformAI | GPT-5.6 Luna | ALLOW; response present | `completed` |

The live run used no EC2 inventory, Inspector findings, AWS identifiers, or
other tool data. PlatformAI reused the protected mode-600 GTX configuration;
the capability key was not copied, printed, logged, committed, or returned to
the browser. This proves one bounded provider comparison, not model quality or
a scientific benchmark.

Validation passed: 15 Python tests, frontend lint, 3 frontend tests,
production build, dependency audit, Python compilation, diff check, and one
live comparison. Playwright was not used.

Intermittent-failure correction: `gtx check` confirmed the External endpoint,
capability key, and exact Luna model remain authorized, and the exact GUI API
request subsequently passed. The adapter now validates the model catalogue
once per backend process, retries one transient catalogue failure, preserves
the successful provider lane when the other fails, and reports stable
`DENIED`, `NOT AVAILABLE`, `NOT CONFIGURED`, or `ERROR` states. Sixteen Python
tests plus frontend lint/tests/build pass. Inference POSTs are not retried, to
avoid duplicate usage. No credential was changed.

Claude route check: GTX rejected `bedrock.claude-haiku-4-5` before inference
because the configured provider permits Azure routes only. A single minimal
probe of `azure.claude-haiku-4-5` completed successfully with 11 input tokens
and 5 output tokens. The Single-mode option therefore uses only the proven
Azure route and omits GPT reasoning fields.
The final loopback API proof returned ALLOW, `completed`, a non-empty Markdown
answer, 37 input tokens, 80 output tokens, and zero records.

Gemini route check: the authenticated PlatformAI catalogue contains
`gemini-2.5-flash-lite`; a minimal direct Responses call completed with 4 input
tokens and 1 output token. Single mode now permits Claude or Gemini to summarize
externally sanitized EC2 or Inspector records. Real EC2 names are replaced by
numbered aliases; account IDs, ARNs, and resource IDs remain excluded. SSM is
still denied without model invocation.
The final loopback Gemini plus EC2 proof returned ALLOW, `completed`, one
externally sanitized record, 78 input tokens, 33 output tokens, and a non-empty
answer. The record used a numbered alias rather than the real EC2 name.

## Issue #12 governed AWS playground proof

Last verified: 1 September 2026, 15:29 SGT

The running loopback GUI/API at `http://127.0.0.1:5174/` and
`http://127.0.0.1:9019/` passed a direct HTTP E2E check without Playwright:

| Journey | Live result |
| --- | --- |
| Nova 2 Lite key + EC2 inventory | ALLOW; 2 sanitized records; real model response |
| Nova Pro key + Inspector findings | ALLOW; 20 sanitized records; real model response |
| Nova 2 Lite + SSM Parameter Store | DENY; 0 parameter names or values |

The backend used profile alias `amit` only to assume the dedicated
`agentcore-live-demo-readonly-role-r1` role. The role permits only EC2
`DescribeInstances` and Inspector2 `ListFindings`, and explicitly denies the
four SSM Parameter Store list/get actions. Bedrock inference used the retained
model-scoped keys from the protected local environment file. No key, account
identifier, ARN, instance ID, or SSM value is recorded here.

Validation commands:

```text
PYTHONPATH=api python3 -m unittest discover -s api -p 'test_*.py'
./scripts/check.sh
HTTP calls to /nova-keys and /aws-playground for ec2, inspector, and ssm
```

Result: **PASS**. Browser appearance was not revalidated in this change; the
HTTP journey, AWS authorization boundary, model responses, lint, unit tests,
and production build were validated.

Follow-up correction: the Playground now clears stale results whenever the
model, tool, or prompt changes. The SSM selection replaces the free-form prompt
with a fixed authorization check, skips Bedrock inference, and returns only the
deterministic AWS IAM denial with zero records and zero tokens. The Issue #12
navigation no longer presents the legacy Logs page. This correction was also
validated without Playwright.

Inspector positive-result proof: selecting Inspector now supplies a matching
default question and public-safe fields only: title, severity, status,
resource type, CVE or vulnerability ID, Inspector score, exploit availability,
and fix availability. A direct live call through Nova 2 Lite returned ALLOW,
20 sanitized findings, and a non-empty top-10 summary. Finding ARNs, account
identifiers, and resource IDs were not supplied to the model or response.

Markdown readability follow-up: Nova responses are rendered as safe
GitHub-flavored Markdown without raw HTML support. Headings, lists, code, and
tables are styled inside the existing dark result panel. The backend now asks
for grounded Markdown, limits output to 900 tokens, and returns Bedrock's real
stop reason so the GUI labels a response Complete or Truncated. A live Nova 2
Inspector run returned a Markdown table, 439 output tokens, and `end_turn`
(Complete). Dependency audit, unit tests, lint, frontend tests, and production
build passed. Playwright was not used.

## Bottom line

Issue #9 passed the dark-mode GUI journey at `http://127.0.0.1:5174/` using
Playwright Core and installed Windows Chrome. The browser reused the retained
30-day Bedrock credential and showed real Nova Lite ALLOW 200, Nova Pro IAM
DENY 403, and two sanitized CloudTrail events. No AWS secret entered the
browser.

## Playwright Core browser proof

Command:

```bash
APP_URL=http://127.0.0.1:5174/ \
  EXPECTED_API_BASE_URL=http://127.0.0.1:9019 \
  ./scripts/browser-e2e.sh
```

Result: **PASS**

| Browser contract | Evidence |
| --- | --- |
| Project, Playground, and Logs load | 3 routes checked |
| Retained key is safe in GUI | SHA-256 fingerprint only; AWS secret absent |
| Approved model | Amazon Nova Lite, ALLOW HTTP 200, real response visible |
| Restricted model | Amazon Nova Pro, DENY HTTP 403, AWS IAM visible |
| Audit view | Success and AccessDenied CloudTrail rows together |
| Browser network boundary | 0 external requests; only loopback GUI/API |
| Browser quality | 0 unexpected console or page errors |
| Browser cleanup | Chrome stopped, temporary profile removed, debug port released |

Evidence directory:

`/home/user/.AGENTS-temp/AgentCore/browser-e2e/20260901T000923+0800/`

Key files:

- `result.json`
- `cleanup.json`
- `routes.json`
- `network.json`
- `unexpected-console-errors.json`
- `playground-allowed.png`
- `playground-denied.png`
- `logs-allowed-denied.png`

Windows review copies:

- `C:\Users\ISSUser\Downloads\output\AgentCore\playground-allowed.png`
- `C:\Users\ISSUser\Downloads\output\AgentCore\playground-denied.png`
- `C:\Users\ISSUser\Downloads\output\AgentCore\logs-allowed-denied.png`
- `C:\Users\ISSUser\Downloads\output\AgentCore\browser-e2e-result.json`

## Issue #9 AWS proof

```text
retained Bedrock-specific key
  -> Nova Lite             ALLOW / HTTP 200
  -> Nova Pro              DENY / HTTP 403 from AWS IAM
  -> lifecycle             30 days / TTL=30-09-26 / cleanup=review
  -> CloudTrail            success plus AccessDenied events
```

AWS environment used:

- profile alias: `amit`;
- Region: `ap-southeast-1`;
- `project1` profile: not used;
- credential: 30-day long-term Bedrock service-specific credential;
- normal AWS access key issued to client: no;
- console login issued: no;
- retained Issue #9 resources: one dedicated IAM user and one model-restricted
  service-specific credential;
- cleanup: explicit repo-owned cleanup script; not run after successful proof.

Public-safe AWS evidence:
[issue-9-live-proof.json](evidence/issue-9-live-proof.json)

Private local AWS evidence:
`/home/user/.AGENTS-temp/AgentCore/issue9-gui/20260831T233242+0800/`

## CloudTrail propagation behavior

## ChatGPT subscription GUI bridge

The EC2 Codex CLI was authenticated with ChatGPT device authorization. The
adapter exposes `gpt-5.6-luna` at `/codex/v1/models` and runs each
request with `--sandbox read-only`, `--ephemeral`, and a non-repository working
directory. A direct E2E request returned `CODEX_GUI_E2E_PASS`, and the LibreChat
startup log loaded `Codex Subscription (EC2)`. This is a custom CLI bridge, not
an OpenAI API-key integration; the subscription auth file remains root-only on
EC2.

## Issue #19 LibreChat + GovTechAI proof

The EC2 adapter was deployed with a root-owned mode-600 GovTech configuration
at `/etc/agentcore-issue19/platformai.env`. A temporary encrypted SSM handoff
was checksum-verified against `/home/user/.config/gtx/config.env`; the transfer
parameter and temporary IAM policy were deleted afterward. Direct local adapter
requests returned HTTP 200 and `MODEL_PROOF_OK` for GPT-5.6 Luna, Azure Claude
Haiku 4.5, and Gemini 3.5 Flash. The adapter exposes these three models at
`/govtech/v1/models` and never returns the key to LibreChat.

CloudTrail event history is asynchronous. The GUI reports the core proof PASS
as soon as HTTP 200 ALLOW, HTTP 403 IAM DENY, and credential lifecycle are
verified. Audit is shown separately as PENDING or VERIFIED. The latest browser
run saw VERIFIED with both events.

## Issue #24 dual-provider governance milestone

The existing protected GovTechAI `gpt-5.6-luna` Responses provider returned a
real `function_call` for the harmless `check_security_finding` definition.
PR #25's adapter now preserves function tools, tool calls, and tool-result
follow-up messages without executing a tool or making a policy decision. The
sanitized live loopback round trip reported:

```text
LUNA_TOOL_CALL_STATUS=PASS
TOOL_NAME=check_security_finding
LUNA_TOOL_RESULT_STATUS=PASS
FINAL_TEXT_PRESENT=yes
ADAPTER_EXECUTION_STATUS=PASS
```

The same native Bedrock Nova 2 Lite probe was denied by the existing EC2 role
because `bedrock:InvokeModel` is not allowed. No IAM, credential, or AWS
resource mutation was performed. A visible LibreChat MCP call and native ASK
Reject/Approve UI proof remain pending manual browser validation.

## Proof boundary

| Claim | Proof source | Status |
| --- | --- | --- |
| Issue #9 dark-mode GUI works | Playwright Core and screenshots | TEST-PROVEN |
| Browser receives no AWS secret | Sanitized API contract and browser assertions | TEST-PROVEN |
| Browser makes no external request | Playwright network capture | TEST-PROVEN |
| Native Bedrock key invokes Nova Lite | HTTP 200 client record and CloudTrail | AWS-PROVEN |
| AWS IAM denies Nova Pro | HTTP 403 client record and CloudTrail AccessDenied | AWS-PROVEN |
| Successful setup is retained safely | AWS lifecycle evidence and protected mode-600 file | AWS-PROVEN |
| Issue #12 reveal is explicit, loopback-origin gated, and no-store | Python HTTP/unit tests | TEST-PROVEN |
| Issue #12 GUI masks after a fixed 15-second in-memory window | TypeScript state-transition test and implementation review | TEST-PROVEN |
| Issue #12 GUI labels and links the active version | TypeScript build and source review | TEST-PROVEN |
| Dedicated Codex key creation validates profile, caller, model, TTL, and exact model policy | Bash plan/syntax and Python control tests | TEST-PROVEN; AWS NOT RUN |
| Codex wrapper is ephemeral, hidden-input, and read-only | Bash syntax/capability check and Codex 0.151.0 help | TEST-PROVEN |
| A governed key successfully invokes Codex through Bedrock | Requires one separately approved live smoke | NOT PROVEN |
| Codex key reaches the real Ohio Mantle endpoint with exact IAM | `docs/evidence/issue-12-codex-bedrock-smoke.md` | LIVE TEST-PROVEN |
| Luna and Terra produce Codex output in this account | Real Mantle HTTP 401 account-unavailable responses | NOT PROVEN; AWS ACCOUNT BLOCKER |
| Claude model selection and Claude Code usage | Separate future issue | NOT IMPLEMENTED |

Screenshots support the GUI claim but do not independently prove AWS
execution. The correlated HTTP results, sanitized CloudTrail events, lifecycle
record, and protected local evidence are required for the AWS claims.
