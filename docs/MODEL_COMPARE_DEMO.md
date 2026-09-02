# Issue #15 Model Compare Demo

## One-minute journey

1. Open `http://localhost:3333/#/playground`.
2. Select **Compare**.
3. Keep the public-safe S3 security prompt.
4. Select **Compare models**.
5. Show the independent Amazon Bedrock Nova 2 Lite and GovTech PlatformAI
   GPT-5.6 Luna responses, latency, tokens when returned, and completion state.

## Configuration boundary

- Nova uses the existing retained model-scoped key.
- PlatformAI reuses `~/.config/gtx/config.env`; the file must be mode `600`.
- The backend permits only the External endpoint and the exact Luna, Claude,
  and Gemini model allowlist used by this POC.
- Provider keys remain server-side and are never returned to the browser.
- Compare accepts text only. It never receives EC2 inventory, Inspector
  findings, AWS identifiers, or SSM data.
- No model or provider fallback is allowed.

## Single-mode models

Single mode offers **Nova 2 Lite**, **GPT-5.6 Luna**, **Claude Haiku 4.5**, and
**Gemini 3.5 Flash**. The exact PlatformAI routes are `gpt-5.6-luna`,
`azure.claude-haiku-4-5`, and `gemini-3.5-flash`. Claude and Gemini requests
omit GPT reasoning settings; Luna uses low reasoning.

EC2 and Inspector are available for these external models only after another
public-safety pass: real EC2 names are replaced by numbered aliases, and no
account IDs, ARNs, or resource IDs are supplied. SSM remains denied and never
invokes a model.

## Honest claim

This is a two-provider response comparison through one developer interface. It
is not a benchmark, gateway, model-quality score, or proof that either model is
better.

## Failure states

The backend fails closed when the PlatformAI configuration is missing, has
unsafe permissions, uses another endpoint/model, lacks model authorization,
times out, is denied, or returns no response text. Gemini receives one bounded
concise retry after an incomplete response; usable partial text is labelled.
