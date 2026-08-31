# AgentCore Test Proof

Last verified: 1 September 2026, 00:09 SGT

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

CloudTrail event history is asynchronous. The GUI reports the core proof PASS
as soon as HTTP 200 ALLOW, HTTP 403 IAM DENY, and credential lifecycle are
verified. Audit is shown separately as PENDING or VERIFIED. The latest browser
run saw VERIFIED with both events.

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
| Codex wrapper is ephemeral, hidden-input, and read-only | Bash syntax/capability check and Codex 0.151.0 help | TEST-PROVEN |
| A governed key successfully invokes Codex through Bedrock | Requires one separately approved live smoke | NOT PROVEN |
| Claude model selection and Claude Code usage | Separate future issue | NOT IMPLEMENTED |

Screenshots support the GUI claim but do not independently prove AWS
execution. The correlated HTTP results, sanitized CloudTrail events, lifecycle
record, and protected local evidence are required for the AWS claims.
