# Issue #19 LibreChat POC

This is a single-path demo:

`LibreChat -> OpenAI-compatible adapter -> AgentCore Harness -> Nova 2 Lite`

The adapter is protocol translation only. It invokes the official AgentCore
CLI Harness command and never receives AWS credentials from LibreChat.

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

It accepts the latest user text, invokes one fixed Harness, and returns one
OpenAI-compatible completion. When LibreChat requests `stream: true`, it
returns minimal OpenAI-compatible SSE chunks and closes the stream after
`[DONE]`. Errors are explicit; no provider or model fallback exists.

## LibreChat configuration

Copy `librechat.yaml.example` to LibreChat's `librechat.yaml` and mount it
using the normal LibreChat configuration path. Set a local placeholder API key
in LibreChat; it is not an AWS key. Keep the adapter reachable only on the
private host or SSM tunnel.

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
