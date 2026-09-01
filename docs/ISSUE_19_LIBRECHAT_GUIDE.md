# Issue #19 LibreChat POC

This is a small demo with two fixed provider paths:

`LibreChat -> OpenAI-compatible adapter -> AgentCore Harness -> Nova 2 Lite`

or

`LibreChat -> OpenAI-compatible adapter -> GovTech PlatformAI`

or

`LibreChat -> OpenAI-compatible adapter -> EC2 Codex CLI -> ChatGPT subscription`

The adapter is protocol translation only. It invokes the official AgentCore
CLI Harness or the authenticated Codex CLI and never receives credentials from
LibreChat.

## Adapter

Run from the repository root after setting the temporary Harness ARN:

```bash
export AGENTCORE_HARNESS_ARN='temporary-harness-arn'
export AWS_REGION=ap-southeast-1
export PORT=3081
python3 -m api.agentcore_openai_adapter
```

The adapter exposes only:

- `GET /v1/models`
- `POST /v1/chat/completions`
- `GET /govtech/v1/models`
- `POST /govtech/v1/chat/completions`
- `GET /codex/v1/models`
- `POST /codex/v1/chat/completions`

Codex may emit progress messages before a tool call and a final answer. The
adapter returns the last completed assistant message so the GUI receives the
answer rather than progress text such as “I’ll verify…”.

It accepts the latest user text, invokes one fixed Harness, and returns one
OpenAI-compatible completion. When LibreChat requests `stream: true`, it
returns minimal OpenAI-compatible SSE chunks and closes the stream after
`[DONE]`. GovTechAI exposes only GPT-5.6 Luna, Azure Claude Haiku 4.5, and
Gemini 3.5 Flash. Errors are explicit; no provider or model fallback exists.
The experimental `Codex Subscription (EC2)` endpoint invokes the authenticated
EC2 Codex CLI with `--sandbox read-only` and `--ephemeral`; it is not an
OpenAI API endpoint and does not use `OPENAI_API_KEY`.
The subscription selector exposes nine explicit choices: each of
`gpt-5.6-luna`, `gpt-5.6-terra`, and `gpt-5.6-sol` at `low`, `medium`, and
`high` reasoning effort. For example, `gpt-5.6-luna-high` maps to the Codex
CLI model `gpt-5.6-luna` with `model_reasoning_effort="high"`. Luna is the
cost-saving default; Terra is the balanced option; Sol is the quality-first
option. These labels are adapter-owned selector IDs, not separate model
providers.

To authenticate the EC2 CLI interactively, use `codex login --device-auth` in
the dedicated remote tmux session. LibreChat only receives the CLI response;
the ChatGPT session file stays on the EC2 host and is never sent to the GUI.

## LibreChat configuration

Copy `librechat.yaml.example` to LibreChat's `librechat.yaml` and mount it
using the normal LibreChat configuration path. Set a local placeholder API key
in LibreChat; it is not an AWS or GovTech key. The live EC2 adapter reads the
GovTech key only from `/etc/agentcore-issue19/platformai.env`, owned by root
with mode `600`; it is never committed, logged, or returned to the browser.
Keep the adapter reachable only on the private host or SSM tunnel.

For this POC, set `ENDPOINTS=custom` in LibreChat's `.env` before restarting.
This keeps the built-in OpenAI endpoint out of the selector, so a new chat
opens on AgentCore instead of asking for an OpenAI subscription key. The
custom endpoint key is only the local placeholder consumed by the adapter; it
is not an AWS or OpenAI credential. After restart, refresh the browser and
start a new chat.

```dotenv
ENDPOINTS=custom
```

```yaml
version: 1.2.1
endpoints:
  custom:
    - name: AgentCore
      apiKey: local-poc-placeholder
      baseURL: http://127.0.0.1:3081/v1
      models:
        default:
          - agentcore-nova-2-lite
      fetch: false
```

## One proof

1. Create one temporary Harness with `scripts/harness-mvp.sh`'s proven
   pattern, leaving it available briefly for the interactive prompt.
2. Start the adapter and LibreChat.
3. Send one prompt from LibreChat and save the adapter/Harness response.
4. Stop local services.
5. Delete the temporary Harness and execution role and independently verify
   both are absent.

The proof must state which boundary it covers. A browser response alone does
not prove AWS execution; the adapter invocation output and cleanup evidence
are required.
