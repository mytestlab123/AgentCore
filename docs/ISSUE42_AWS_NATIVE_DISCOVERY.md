# Issue #42 — AWS-native AgentCore discovery

Purpose: test what AWS already provides before adding more custom integration code.

## Candidates

**Evidence boundary:** Agent Inspector and FAST results below are **source-review evidence only**. Neither was deployed or exercised hands-on for this discovery; do not treat either as a live UX, approval, or trace proof.

| Candidate | Chat/UI | Tool calls | Human approval | Gateway/Policy fit | Trace/observability | Reuse verdict |
| --- | --- | --- | --- | --- | --- | --- |
| Agent Inspector / native AgentCore | **PASS** — developer chat/inspection surface, not chosen end-user UX | **PASS** — interactively tests agent/tool behavior | **NO** — no native LibreChat-style approval UX evidenced here | **PASS** — fits AgentCore/Gateway development workflows | **PARTIAL** — useful developer traces/inspection; not live-proven in this discovery | **PARTIAL** — retain as a developer/debug surface |
| FAST | **PASS** — React multi-turn chat baseline | **PASS** — Gateway and Code Interpreter baseline | **PARTIAL** — Cedar policy, no human-approval UX evidenced | **PASS** — native Gateway/Cedar path | **PARTIAL** — telemetry/observability is present in source | **NO** — full stack exceeds this MVP |
| LibreChat + AgentCore | **PASS** — existing operator UI | **PASS** — current MCP/custom-endpoint path | **PASS** — current ASK/Approve/Reject proof | **PASS** — current Gateway Policy direction | **PARTIAL** — existing bounded Harness/Gateway evidence | **PASS** — chosen MVP UI/tooling path |

## Discovery scope reviewed

- Reviewed current Agent Toolkit for AWS / AgentCore MCP guidance for Kiro and Codex.
- Reviewed Agent Inspector/native AgentCore capabilities from current sources; no hands-on deployment claim is made here.
- Reviewed FAST far enough from source/docs to judge MVP fit; no hands-on deployment claim is made here.
- Compared both against the existing LibreChat experience already proven by this repo.
- Bedrock KB Retrieval MCP remains deferred; do not add RAG to the MVP now.

## Final recommendation

- **Chosen MVP UI/tooling path:** **LibreChat + the existing thin server-side AgentCore adapter + LibreChat native ASK/Approve/Reject + retained AgentCore Gateway Policy.** Use the bounded Harness tool/resume and trace path only when a milestone specifically needs it.
- **Keep:** the existing LibreChat conversation shell and approval UX, the thin adapter, Gateway Policy ALLOW/DENY boundary, and the narrow Harness tool/resume contract. Keep Agent Inspector only as a developer/debug surface, not as the user-facing MVP UI.
- **Remove / simplify:** do not add a custom chat frontend, FAST's Cognito/Amplify/full-stack infrastructure, an AWS Transform pipeline, or RAG/Bedrock KB Retrieval MCP. Keep Agent Toolkit use documentation-first; do not enable broad authenticated AgentCore MCP management tools for this MVP.
- **Next implementation step:** run one separate, approval-gated Agent Inspector check against the retained Gateway: discover its tools, submit only the known denied input, and record the resulting policy/trace evidence; do not deploy FAST or create new AWS resources.

Bounded, reversible lab changes needed for discovery are acceptable. Avoid unrelated hardening, large new frameworks, or multiple experimental repos.
