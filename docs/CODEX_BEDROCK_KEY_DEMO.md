# Governed Bedrock key to Codex CLI

Issue #12 extends the retained Issue #9 demo with one explicit credential
handoff to Codex CLI. It remains a loopback-only POC.

## Demo flow

1. Start the retained demo with `./dev-issue9.sh --approve-live` using the
   existing Issue #9 environment gates.
2. Open the Project view. The key is masked by default.
3. Select **Reveal key**, then **Copy for Codex**. The GUI masks and discards
   its in-memory copy after 15 seconds.
4. Run `./scripts/codex-bedrock-smoke.sh` and paste at the hidden prompt.
5. Codex reads `fixtures/codex-smoke/demo.py` in an ephemeral, read-only
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
