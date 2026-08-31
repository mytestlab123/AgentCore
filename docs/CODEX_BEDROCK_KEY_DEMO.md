# Governed Bedrock key to Codex CLI

Issue #12 extends the retained Issue #9 demo with one explicit credential
handoff to Codex CLI. It remains a loopback-only POC.

## Demo flow

1. Start the retained demo with `./dev-issue9.sh --approve-live` using the
   existing Issue #9 environment gates.
2. Open the Project view and confirm the sidebar links to Issue #12.
3. Enter one exact, verified `openai.*` Bedrock model ID and select
   **Create Codex AI key**. This is the explicit AWS mutation action. It creates
   a separate 30-day IAM user credential; it does not broaden the Nova key.
4. Select **Reveal Codex key**, then **Copy for another Codex**. The GUI masks and discards
   its in-memory copy after 15 seconds.
5. Run `./scripts/codex-bedrock-smoke.sh` and paste at the hidden prompt.
6. Codex reads `fixtures/codex-smoke/demo.py` in an ephemeral, read-only
   session and returns at most five lines.

The operating-system clipboard may retain the copied value after the GUI masks
it. Clear the clipboard manually after the demo.

## Model selection

The default candidate is `openai.gpt-5.6-luna` with low reasoning. A different
cheap OpenAI model can be chosen explicitly after account and Region preflight:

```bash
CODEX_BEDROCK_MODEL='<verified-openai-model-id>' \
  ./scripts/codex-bedrock-smoke.sh
```

There is no automatic model or Region fallback. An unavailable or denied model
stops the demo. The wrapper uses the built-in `amazon-bedrock` provider and
passes the credential only through `AWS_BEARER_TOKEN_BEDROCK`.

## Configure another Codex checkout

The simplest safe route is to copy only the key from the GUI and run this
repository's wrapper. It does not change normal Codex login or persistent
configuration:

```bash
cd /home/user/git/AgentCore
CODEX_BEDROCK_MODEL='openai.gpt-5.6-luna' \
  ./scripts/codex-bedrock-smoke.sh
```

Paste at the hidden prompt. Change the model value only when the GUI-created
policy used that exact model. To test a different checkout, replace the
fixture directory after first reviewing the wrapper and keep Codex in
`read-only` sandbox mode.

Prompt for another Codex assistant:

> Configure one ephemeral read-only Codex CLI smoke using the built-in
> amazon-bedrock provider. Prompt for AWS_BEARER_TOKEN_BEDROCK using hidden
> input, set AWS_REGION=ap-southeast-1, use the exact model shown in the
> AgentCore GUI with low reasoning, do not persist the key or change my normal
> login, and do not enable model or Region fallback.

After the demo, clear the clipboard and close the shell. Do not put the key in
`~/.codex/config.toml`, `.env`, argv, screenshots, chat, or shell history.

Targeted cleanup, only when explicitly approved:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 \
  ./scripts/cleanup-issue12-codex-key.sh --approve-cleanup
```

## Proof boundary

DEMO-PROVEN after local validation:

- explicit reveal/copy UI with a 15-second mask timer;
- no browser persistence API in the credential flow;
- mode-600 retained-file gate;
- hidden-input, ephemeral, read-only Codex wrapper configuration.

NOT PROVEN until a separately approved live run:

- selected model availability in the Amit account and Region;
- successful Codex inference through Amazon Bedrock;
- exact invocation cost and resulting AWS audit event.

Never put the revealed key in Git, screenshots, logs, command arguments, shell
history, or persistent Codex configuration. No Playwright test is required.

Official setup reference:
https://learn.chatgpt.com/docs/amazon-bedrock
