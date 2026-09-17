# Context

Status: ACTIVE
Updated: 2026-09-17

> Current-only restart state. Completed milestone details belong in Git and closed Issues/PRs.

## Project Identity

- Project: AgentCore internal AI platform POC
- Repository: `mytestlab123/AgentCore`
- Current merged `main`: `6a43779d24c69d90f53d102d4b727d662081c085`
- Context: PERSONAL / LAB

## Current Truth

- The merged platform/demo baseline remains the reusable starting point.
- Issue #46 (real Security Group SSH compliance demo) is completed; it is not an active standing mutation lane.
- Issue #53 (main-only GitHub OIDC STS proof for aws-platform enrollment) is completed; it added proof plumbing without workload authority.
- Historical deployed/demo resources and acceptance evidence must be re-verified before they are treated as current runtime truth.
- Stable implementation/safety/CLI rules stay in `AGENTS.md`; active milestone state belongs here and in the owning Issue/PR.

## Active Work

- Issue #55 — move mutable milestone routing out of `AGENTS.md` and add current-only context.
- No standing product/AWS implementation milestone is authorized by this governance issue.

## Current Boundary

- Documentation/governance only for Issue #55.
- No AgentCore, Bedrock, Security Group, Gateway/Policy, IAM/OIDC, deployment, listener, approval, or AWS mutation.
- Future live work must name an owning Issue/PR and re-verify active AWS identity/profile/Region first.

## Next Action

Review Issue #55 / its PR. After merge, select future work explicitly from a new or reopened authorized milestone; do not resurrect Issue #46 or #53 implicitly.

## Continuation

For a known objective, use the named Issue/PR, latest relevant authorized delta, and current HEAD. Reload broader repository guidance only when a real bootstrap/recovery trigger applies.
