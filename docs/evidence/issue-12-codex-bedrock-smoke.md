# Issue #12 Codex-on-Bedrock smoke result

Date: 2026-09-01 (Asia/Singapore)

## Result

`FAIL - REGION NOT SUPPORTED BY CODEX CLIENT`

One bounded smoke ran in the temporary tmux session
`agentcore-codex-bedrock-test:smoke`.

Verified configuration:

- Codex CLI: `0.151.0`
- provider: `amazon-bedrock`
- model: `openai.gpt-5.6-luna`
- reasoning: `low`
- sandbox: `read-only`
- approval: `never`
- session persistence: disabled (`--ephemeral`)
- normal OpenAI login/config: isolated with a temporary `CODEX_HOME`
- authentication variable: `AWS_BEARER_TOKEN_BEDROCK`
- Region: `ap-southeast-1`

Codex stopped with:

```text
Fatal error: Amazon Bedrock does not support region `ap-southeast-1`
```

The fixture was not answered and no successful model inference was recorded.
No model or Region fallback and no second request were attempted.

## Proof boundary

PROVEN:

- the protected Codex key can be injected without argv, chat, or output;
- Codex selects the built-in Amazon Bedrock provider and exact Luna model;
- the smoke is isolated, ephemeral, and read-only;
- Codex 0.151.0 rejects the selected Singapore Region before completion.

NOT PROVEN:

- successful Codex inference through Amazon Bedrock;
- key policy correctness in a Codex-supported Region;
- billed model usage or CloudTrail inference evidence.

## Required next decision

Select and approve one Codex-supported AWS Region, update the dedicated Issue
#12 model policy to that exact Region, and run one retry. Do not silently fall
back or broaden the policy to multiple Regions.
