# Issue #15 Model Compare Demo

## One-minute journey

1. Open `http://localhost:5174/#/playground`.
2. Select **Compare**.
3. Keep the public-safe S3 security prompt.
4. Select **Compare models**.
5. Show the independent Amazon Bedrock Nova 2 Lite and GovTech PlatformAI
   GPT-5.6 Luna responses, latency, tokens when returned, and completion state.

## Configuration boundary

- Nova uses the existing retained model-scoped key.
- PlatformAI reuses `~/.config/gtx/config.env`; the file must be mode `600`.
- The backend permits only the External endpoint and exact `gpt-5.6-luna`
  model.
- Provider keys remain server-side and are never returned to the browser.
- Compare accepts text only. It never receives EC2 inventory, Inspector
  findings, AWS identifiers, or SSM data.
- No model or provider fallback is allowed.

## Optional Single PlatformAI models

Single mode also offers **PlatformAI Claude Haiku 4.5** and **PlatformAI Gemini
2.5 Flash Lite** using the proven exact routes `azure.claude-haiku-4-5` and
`gemini-2.5-flash-lite`. The rejected `bedrock.claude-haiku-4-5` identifier is
not used. Claude and Gemini requests omit GPT reasoning settings.

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
times out, is denied, or returns an incomplete response.
