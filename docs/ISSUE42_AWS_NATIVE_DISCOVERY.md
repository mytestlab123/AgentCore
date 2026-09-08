# Issue #42 — AWS-native AgentCore discovery

Purpose: test what AWS already provides before adding more custom integration code.

## Candidates

**Evidence boundary:** Agent Inspector and FAST results below are **source-review evidence only**. Neither was deployed or exercised hands-on for this discovery; do not treat either as a live UX, approval, or trace proof.

| Candidate | Chat/UI | Tool calls | Human approval | Gateway/Policy fit | Trace/observability | Reuse verdict |
| --- | --- | --- | --- | --- | --- | --- |
| Agent Inspector / native AgentCore | **NO** — developer MCP debugger, not end-user chat | **PASS** — interactively tests MCP tools | **NO** — no approval/pause UI | **PASS** — connects to Gateway MCP tools | **PARTIAL** — traces are separate AgentCore/CloudWatch capability | **PARTIAL** — retain only as a debugger |
| FAST | **PASS** — React multi-turn chat baseline | **PASS** — Gateway and Code Interpreter baseline | **PARTIAL** — Cedar policy, no human-approval UX evidenced | **PASS** — native Gateway/Cedar path | **PARTIAL** — telemetry/observability is present in source | **NO** — full stack exceeds this MVP |
| LibreChat + AgentCore | **PASS** — existing operator UI | **PASS** — current MCP/custom-endpoint path | **PASS** — current ASK/Approve/Reject proof | **PASS** — current Gateway Policy direction | **PARTIAL** — existing bounded Harness/Gateway evidence | **PASS** — chosen MVP UI/tooling path |

## What Kiro should do

1. Read Issue #42 and current repo truth. Treat PR #41 as a separate active milestone; do not modify it.
2. Use current AWS-native tooling where practical, including Agent Toolkit for AWS / AgentCore MCP guidance.
3. Hands-on test Agent Inspector enough to understand chat, tools, approval/pause behavior, and traces.
4. Inspect/run FAST only far enough to judge whether its UI can replace custom frontend work.
5. Compare both against the existing LibreChat experience already used by this repo.
6. Optional: inspect Bedrock KB Retrieval MCP only to decide later relevance. Do not add RAG now.
7. Record PASS / PARTIAL / NO evidence in the table and one final recommendation below.

## Final recommendation

- **Chosen MVP UI/tooling path:** **LibreChat + the existing thin server-side AgentCore adapter + LibreChat native ASK/Approve/Reject + retained AgentCore Gateway Policy.** Use the bounded Harness tool/resume and trace path only when a milestone specifically needs it.
- **Keep:** the existing LibreChat conversation shell and approval UX, the thin adapter, Gateway Policy ALLOW/DENY boundary, and the narrow Harness tool/resume contract. Keep Agent Inspector only as a developer debugger, not as a user UI.
- **Remove / simplify:** do not add a custom chat frontend, FAST's Cognito/Amplify/full-stack infrastructure, an AWS Transform pipeline, or RAG/Bedrock KB Retrieval MCP. Keep Agent Toolkit use documentation-first; do not enable broad authenticated AgentCore MCP management tools for this MVP.
- **Next implementation step:** run one separate, approval-gated Agent Inspector check against the retained Gateway: discover its tools, submit only the known denied input, and record the resulting policy/trace evidence; do not deploy FAST or create new AWS resources.

Bounded, reversible lab changes needed for discovery are acceptable. Avoid unrelated hardening, large new frameworks, or multiple experimental repos.