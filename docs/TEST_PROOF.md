# AgentCore Test Proof

Last verified: 31 August 2026, 21:49 SGT

## Bottom line

The existing Issue #4 dark-mode local portal passed its Playwright Core browser
regression test at `http://localhost:5174/`. Issue #9 did not change the GUI;
its native Bedrock API-key flow was tested separately against AWS.

## Screenshot review

The supplied Project-page screenshot is consistent with the intended local
demo:

- dark mode is applied across the full portal;
- the visible scope is correctly labelled `ISSUE #4 MVP`;
- `Local POC`, `No AWS calls`, `LOCAL MOCK`, and `Clearly marked local
  simulation` make the environment boundary visible;
- Project, Playground, and Logs are the only navigation views;
- Nova Lite is shown as allowed and Premium model as not allowed.

The screenshot was taken while the simulated platform key was visible. This is
not a native Bedrock API key. The automated browser test presses `Mask key` and
verifies that the full simulated value is no longer displayed.

## Playwright Core browser proof

Command:

```bash
APP_URL=http://localhost:5174/ ./scripts/browser-e2e.sh
```

Tested version: `playwright-core 1.62.1`, connected to installed Windows Chrome
through the Chrome DevTools Protocol.

Result: **PASS**

| Browser contract | Evidence |
| --- | --- |
| Project, Playground, and Logs load | 3 routes checked |
| Demo key lifecycle | key created and then masked |
| Approved catalogue entry | Amazon Nova Lite shown as Allowed |
| Restricted catalogue entry | Premium model shown as Denied |
| Audit view | Allowed and Denied decisions shown together |
| Local-only boundary | 0 external requests |
| Browser quality | 0 console or page errors |
| Browser cleanup | Chrome stopped, temporary profile removed, debug port released |

Evidence directory:

`/home/user/.AGENTS-temp/AgentCore/browser-e2e/20260831T214913+0800/`

Key files:

- `result.json`
- `cleanup.json`
- `routes.json`
- `network.json`
- `playground-allowed.png`
- `playground-denied.png`
- `logs-allowed-denied.png`

Windows review copies:

- `C:\Users\ISSUser\Downloads\output\AgentCore\playground-allowed.png`
- `C:\Users\ISSUser\Downloads\output\AgentCore\playground-denied.png`
- `C:\Users\ISSUser\Downloads\output\AgentCore\logs-allowed-denied.png`
- `C:\Users\ISSUser\Downloads\output\AgentCore\browser-e2e-result.json`

## Issue #9 AWS proof

Issue #9 introduced a CLI-only flow, not a new browser flow:

```text
temporary Bedrock-specific key
  -> Nova Lite             ALLOW / HTTP 200
  -> Nova Pro              DENY / HTTP 403 from AWS IAM
  -> CloudTrail            success plus AccessDenied events
  -> targeted cleanup      credential and IAM user deleted
```

AWS environment used:

- profile alias: `amit`;
- Region: `ap-southeast-1`;
- `project1` profile: not used;
- credential: one-day long-term Bedrock service-specific credential;
- normal AWS access key issued to client: no;
- console login issued: no;
- retained Issue #9 AWS resources: none.

Public-safe AWS evidence:
[issue-9-live-proof.json](evidence/issue-9-live-proof.json)

Private local evidence:
`/home/user/.AGENTS-temp/AgentCore/bedrock-api-key/20260831T212021+0800/`

## Proof boundary

| Claim | Proof source | Status |
| --- | --- | --- |
| Existing local GUI works in dark mode | Playwright Core and screenshots | TEST-PROVEN |
| Local GUI performs no external requests | Playwright network capture | TEST-PROVEN |
| Native Bedrock key invokes Nova Lite | HTTP client response and CloudTrail | AWS-PROVEN |
| AWS IAM denies Nova Pro | HTTP 403 and CloudTrail AccessDenied | AWS-PROVEN |
| Temporary Issue #9 resources were deleted | IAM cleanup result and post-check | AWS-PROVEN |
| Issue #9 has a new GUI flow | No GUI was added by design | NOT IMPLEMENTED |

Browser screenshots do not prove AWS execution. The AWS client, IAM denial,
CloudTrail events, and cleanup evidence are required for the Issue #9 claims.
