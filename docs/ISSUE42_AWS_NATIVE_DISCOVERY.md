# Issue #42 — AWS-native AgentCore discovery

Purpose: test what AWS already provides before adding more custom integration code.

## Candidates

| Candidate | Chat/UI | Tool calls | Human approval | Gateway/Policy fit | Trace/observability | Reuse verdict |
| --- | --- | --- | --- | --- | --- | --- |
| Agent Inspector / native AgentCore | TBD | TBD | TBD | TBD | TBD | TBD |
| FAST | TBD | TBD | TBD | TBD | TBD | TBD |
| LibreChat + AgentCore | known strong UI | known MCP path | known ASK/Approve/Reject | current PR #41 path | partial/current evidence | TBD |

## What Kiro should do

1. Read Issue #42 and current repo truth. Treat PR #41 as a separate active milestone; do not modify it.
2. Use current AWS-native tooling where practical, including Agent Toolkit for AWS / AgentCore MCP guidance.
3. Hands-on test Agent Inspector enough to understand chat, tools, approval/pause behavior, and traces.
4. Inspect/run FAST only far enough to judge whether its UI can replace custom frontend work.
5. Compare both against the existing LibreChat experience already used by this repo.
6. Optional: inspect Bedrock KB Retrieval MCP only to decide later relevance. Do not add RAG now.
7. Replace the TBD cells above with PASS / PARTIAL / NO plus a few words, then add one final recommendation below.

## Final recommendation

TBD.

Include only:

- chosen MVP UI/tooling path;
- what existing AgentCore code we should keep;
- what custom glue can be removed/simplified;
- one next implementation step.

Bounded, reversible lab changes needed for discovery are acceptable. Avoid unrelated hardening, large new frameworks, or multiple experimental repos.