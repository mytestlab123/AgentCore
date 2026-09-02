# ChatGPT research request: Agents endpoint hidden in live LibreChat

## Context

Repository: `/home/user/git/AgentCore`
PR: #25, branch `feature/issue-24-librechat-governance`
Live host: `http://agentcore.astromedicomp.org/`
LibreChat: `v0.8.8-rc1`, direct Node deployment on the existing EC2 host

The live UI shows only these endpoint groups:

- AgentCore
- Codex Subscription (EC2)
- GovTechAI

The built-in `Agents` endpoint is absent, so the user cannot reach Agent
Builder. The screenshots show a normal model endpoint selector, not the Agents
workspace.

## Evidence collected

Read-only SSM check using the approved `amit` profile, Singapore region, and
the existing demo instance (identifier intentionally omitted):

```text
ENDPOINTS=custom
librechat.yaml contains:
  endpoints.agents.disableBuilder: false
  interface.agents.use: true
  interface.agents.create: true
  interface.mcpServers.use: true
```

The live backend log also shows the governance MCP server initialized with
three tools. Public HTTP health returned `200`.

The repository guide currently documents:

```dotenv
ENDPOINTS=custom
```

That setting was intended to hide the built-in OpenAI endpoint, but it also
appears to hide the built-in `agents` endpoint. LibreChat's current dotenv
documentation defines `ENDPOINTS` as a comma-separated endpoint allow-list and
uses `ENDPOINTS=openAI,agents,...` as the example.

## Research question

Confirm whether the smallest correct fix is:

```dotenv
ENDPOINTS=custom,agents
```

while keeping the existing custom endpoints and `endpoints.agents` block.
Confirm whether this preserves the custom model providers and removes only the
OpenAI endpoint from the selector.

Also confirm the expected UI path:

1. Click the top endpoint/model pill.
2. Select `Agents`.
3. Open the Side Panel's `Agent Builder`.

## Constraints

- Keep PR #25 scope; do not create another Issue or PR.
- Prefer native LibreChat configuration; no custom Agent Builder UI.
- Do not change Mongo roles or passwords.
- Do not expose credentials or AWS identifiers in public output.
- Do not call AWS model inference or mutate AWS infrastructure.
- If `ENDPOINTS=custom,agents` is not sufficient, stop and identify the exact
  configuration or version incompatibility before implementing alternatives.

## Official references

- https://www.librechat.ai/docs/features/agents
- https://www.librechat.ai/docs/configuration/dotenv#endpoints
- https://www.librechat.ai/docs/configuration/librechat_yaml/object_structure/agents
- https://www.librechat.ai/docs/features/access_control

## Resolution applied for review

The live `.env` was changed from `ENDPOINTS=custom` to
`ENDPOINTS=custom,agents` after the read-only confirmation above. The existing
LibreChat process was restarted cleanly after stopping its exact Node process
tree; port 80 is listening with one backend and HTTP health returned `200`.
The startup log shows one configured `agentcore_governance` MCP server with
three tools and the native approval hook registered. No AWS resource or model
inference call was made.

The durable guide updates in this branch document the same setting. ChatGPT
should review whether this is sufficient for PR #25 and whether any additional
version-specific UI issue remains after a fresh browser login.
