# ChatGPT request: choose the smallest AWS Bedrock key-to-coding-tool demo

## Required collaboration protocol

Follow this public protocol:

<https://gist.github.com/amitkarpe/c8d29ad89cafe3ba178fcae29de3c238>

Repository: <https://github.com/mytestlab123/AgentCore>

Do not implement anything. Review current repository truth, check existing open
Issues first, and create one new standalone GitHub Issue containing your
response.

## Objective

Amit wants a 3-5 minute management demo showing that an operator can generate
a governed Amazon Bedrock API key in the AgentCore GUI, copy it, and use it
immediately for local AI coding through:

1. Codex CLI with a low-cost supported OpenAI model on Amazon Bedrock; and
2. Claude Code with Claude Haiku 4.5 or, when unavailable, Claude Sonnet 4.5.

Choose exactly one small next milestone. Decide whether both coding tools fit
responsibly in one KISS issue. If not, select the stronger first tool and defer
the other explicitly.

## Current repository truth

Latest merged work:

- [PR #10: native Bedrock API-key governance POC](https://github.com/mytestlab123/AgentCore/pull/10)
- [Issue #9: native Amazon Bedrock API keys](https://github.com/mytestlab123/AgentCore/issues/9)
- [Merged repository commit](https://github.com/mytestlab123/AgentCore/commit/1bf4ca6677458bd0d601b9e5eacb04750af2999a)
- [Public-safe test and AWS proof](https://github.com/mytestlab123/AgentCore/blob/1bf4ca6677458bd0d601b9e5eacb04750af2999a/docs/TEST_PROOF.md)

Issue #9 already proves:

- one native Bedrock service-specific credential;
- real approved-model HTTP 200;
- real restricted-model HTTP 403 enforced by AWS IAM;
- sanitized CloudTrail success and AccessDenied evidence;
- no general AWS access key or console login;
- a retained 30-day credential with an explicit TTL and cleanup path;
- a loopback-only GUI that exposes only a masked fingerprint.

The current GUI does **not** reveal or copy the full key and has not tested a
coding client.

Existing open Issues are [#3](https://github.com/mytestlab123/AgentCore/issues/3)
and [#8](https://github.com/mytestlab123/AgentCore/issues/8). Neither currently
owns this key-to-coding-tool demo. Confirm that before proposing a new Issue.

## Current documentation facts

Official OpenAI documentation now describes a built-in `amazon-bedrock`
provider for local Codex surfaces. It accepts a Bedrock API key through
`AWS_BEARER_TOKEN_BEDROCK`, requires an AWS Region, and lists supported Bedrock
model IDs including `openai.gpt-5.6-luna`:

<https://learn.chatgpt.com/docs/amazon-bedrock>

`luna-low` is not a model ID. The candidate is
`openai.gpt-5.6-luna` with low reasoning effort, subject to actual account and
Region availability.

Official Claude Code documentation supports Amazon Bedrock API keys through
`AWS_BEARER_TOKEN_BEDROCK` with `CLAUDE_CODE_USE_BEDROCK=1` and explicit model
pinning:

<https://code.claude.com/docs/en/amazon-bedrock>

Amazon Bedrock API-key usage documentation:

<https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys-use.html>

## Honest proof states

### PROVEN

- Native Bedrock API-key creation, ALLOW, DENY, audit, retention, and cleanup.
- The GUI can safely show a masked key fingerprint and sanitized results.
- Official client documentation supports Bedrock API-key authentication for
  local Codex and Claude Code.

### NOT PROVEN

- An OpenAI Bedrock model is enabled and invokable in the target account and
  Region.
- `openai.gpt-5.6-luna` works with the retained key and current Codex version.
- Claude Haiku 4.5 or Claude Sonnet 4.5 is invokable with the retained key.
- One IAM policy and one key can safely support both coding clients.
- The GUI reveal/copy workflow is safe and usable.
- Any coding-client invocation, cost, quota, or CloudTrail evidence.

Do not convert documentation support or catalogue visibility into a proven
account-level result.

## Preferred operator journey

```text
Project GUI
  -> choose a coding-demo policy preset
  -> generate or reuse a 30-day Bedrock key
  -> explicitly reveal and copy the key
  -> key auto-masks after a short interval
  -> paste through a hidden-input repo wrapper
  -> run one tiny Codex task using an allowed OpenAI Bedrock model
  -> run one tiny Claude Code task using an allowed Claude Bedrock model
  -> show sanitized success and CloudTrail evidence in the GUI
```

The demo should clearly prove that AWS supplies and governs the credential and
model access. It must not imply that Codex models and Claude models are the
same service or provider.

## Model candidates

Codex candidate:

- `openai.gpt-5.6-luna` with low reasoning effort, only if read-only discovery
  and one bounded invocation prove availability.

Claude candidates, in preference order:

1. Claude Haiku 4.5, if the exact active inference profile is invokable.
2. Claude Sonnet 4.5 as the higher-cost fallback.

Do not invent Claude Haiku 4.0, 4.3, 4.4, or 4.6 model IDs. Do not call Sonnet
a cheap model without current pricing evidence.

## Security and KISS constraints

- The secret may appear only after an explicit loopback-only user action.
- Never place it in Git, screenshots, URLs, browser storage, logs, evidence,
  command arguments, shell history, or PR/Issue text.
- Prefer the existing protected mode-600 local file outside Git for this POC.
- Do not add Secrets Manager or SSM Parameter Store unless the selected issue
  proves they are necessary. They are optional future hardening.
- Provide repo-owned wrappers that accept the pasted key through hidden input
  rather than an `export KEY=...` command saved in shell history.
- Auto-mask the GUI value and make the one-time/repeat-reveal tradeoff explicit.
- Use exact model-scoped IAM permissions and deny unintended model access.
- Keep the successful low-cost demo setup retained with a 30-day expiry,
  explicit TTL, `cleanup=review`, and targeted cleanup automation.
- Bound each smoke prompt and output to minimize inference cost.
- Do not run Playwright Core. Amit will perform the small GUI journey manually.
- No AWS mutation occurs until Amit separately approves the implementation
  issue, exact account, Region, resources, IAM policy, and models.

## Explicit non-goals

- production secret distribution or multi-user credential brokering;
- SSO, Cognito, hosted portal, public endpoint, HA, billing, quotas dashboard,
  RAG, Kubernetes, LiteLLM, Open WebUI, or broad multi-provider routing;
- saving a secret in browser local/session storage;
- Codex cloud, hosted ChatGPT, or Claude web integration;
- more than one tiny prompt per selected coding client;
- broad model comparison or benchmark work.

## Required ChatGPT response

Create exactly one new standalone GitHub Issue in this repository. Do not use
an existing Issue or PR comment. The Issue must include:

1. recommendation and why it is the smallest useful management demo;
2. alternatives rejected, including whether one or two keys are preferable;
3. one bounded Issue title and exact scope;
4. one implementation PR title, expected files, and non-goals;
5. exact Codex and Claude model-selection/preflight rules;
6. secure GUI reveal/copy behavior and secret-handling gates;
7. one operator journey suitable for a 3-5 minute demo;
8. acceptance criteria;
9. deterministic validation plus Amit's short manual smoke test, with no
   Playwright requirement;
10. public-safe evidence plan, cost guardrails, retention, and cleanup;
11. risks, no-go gates, and deferred work.

If both Codex and Claude Code make the issue too large, choose exactly one for
the next Issue and state that the other is deferred. Do not implement anything.

## Publication safety

This packet intentionally contains no credentials, account identifiers, ARNs,
resource identifiers, private endpoints, hostnames, IP addresses, raw logs, or
private payloads. All links are public documentation or public repository
records.
