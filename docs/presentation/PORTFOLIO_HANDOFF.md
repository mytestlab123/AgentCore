# AI API Platform Portfolio Handoff

Status: READY FOR PORTFOLIO ASSEMBLY

This handoff contributes only the AI API Platform story to a combined
management presentation covering Security Copilot, Compliance Copilot, and the
AI API Platform. It does not assert implementation or evidence for the other
two products.

## Current baseline

- Repository: `mytestlab123/AgentCore`
- Current commit: `81c8e8b4e8ed4a554c5fcf8bd0a24c93bdc05cbd`
- Latest merged PR: [#7 - Add AWS resource lifecycle audit and cleanup controls](https://github.com/mytestlab123/AgentCore/pull/7)
- Implemented MVP: [Issue #4 - one project, one API key, one Bedrock model](https://github.com/mytestlab123/AgentCore/issues/4), delivered by [PR #5](https://github.com/mytestlab123/AgentCore/pull/5)
- Scope: one project, one platform key, one approved model, one denied model,
  and one combined audit view

## Management problem

Application teams want useful AI access, but giving each application direct
cloud credentials and unrestricted model choice weakens central governance and
makes usage harder to review consistently.

## Proposed solution

Provide an internal platform credential in front of Amazon Bedrock. The
platform validates the key, applies a project-to-model allowlist, invokes or
denies the request, and records the result in one audit view. The developer
uses the platform interface without receiving the underlying AWS credential.

Portfolio positioning must remain explicit:

- **PLANNED:** the AI API Platform could become a shared governed model-access
  layer for Security Copilot and Compliance Copilot.
- **NOT PROVEN:** neither copilot is integrated with this repository today.

## One operator journey

1. The developer opens `demo-security-app` and creates the single-use demo
   platform key; the UI masks it after initial display.
2. The developer selects the approved Amazon Nova Lite model and submits a
   security prompt.
3. The platform returns the response with model, latency, token counts,
   request label, and allowed status.
4. The same developer selects `model-premium`; the platform rejects it as not
   allowed for the project.
5. The developer opens Logs and sees the allowed and denied decisions together.

Management takeaway: one developer experience can provide model access,
central policy enforcement, and visible evidence without exposing provider
credentials to the application team.

## Evidence claims

### DEMO-PROVEN

- The captured live UI shows an approved Amazon Nova Lite response with model,
  latency, token, request, status, and provider-credential-isolation metadata.
- The captured live UI shows the same project being denied access to
  `model-premium`.
- The captured Logs view shows allowed and denied requests together.
- The Project flow creates the demo platform key once and then masks it.

### TEST-PROVEN

- The deterministic browser runner checks all three routes, key creation and
  masking, approved response, denied policy, combined logs, zero unexpected
  console errors, local-only networking, and browser cleanup.
- Unit tests cover the narrow platform policy and frontend behavior.
- The repository check command validates Bash syntax, lint, tests, production
  builds, dependency audits, Python compilation, and whitespace.

### READ-ONLY PROVEN

- Recorded AWS inspection evidence confirmed that the deployed key record held
  a SHA-256 hash rather than the raw platform key.
- Recorded stack inventory and lifecycle evidence supports the bounded,
  discoverable, TTL-tagged demo-resource claim.
- This handoff task made no AWS call and does not claim current runtime or stack
  availability.

### PLANNED

- Evaluate whether this governed API layer should be reused by Security
  Copilot and Compliance Copilot.
- Evaluate a smaller reusable governance gateway only if it reduces custom
  code without weakening the visible policy and audit story.
- Define production identity, key lifecycle, private connectivity, and
  operational ownership only after management accepts the direction.

### NOT PROVEN

- Production authentication, enterprise key rotation, multi-tenancy, billing,
  resilience, private networking, and service-level objectives.
- Integration with Security Copilot or Compliance Copilot.
- AgentCore Runtime, AgentCore Gateway, AgentCore Identity, Memory, multiple
  agents, or MCP integration.
- Production cost savings, compliance improvement, incident reduction, or
  security-outcome guarantees.

## Public-safe screenshots

The following repository images were visually reviewed for this handoff. They
contain demo project/model/request labels but no AWS account ID, ARN, endpoint,
credential, real platform key, or private host.

1. `docs/demo-proof/playground-allowed.png`
   - Caption: **Approved access - the governed platform returns a live Nova
     Lite response with status, latency, tokens, and no provider credential
     exposed.**
2. `docs/demo-proof/playground-denied.png`
   - Caption: **Policy boundary - the same project receives a clear denial for
     a model outside its allowlist.**
3. `docs/demo-proof/logs-allowed-denied.png`
   - Caption: **Central evidence - allowed and denied decisions appear together
     with project, model, status, latency, and token metadata.**

For the combined deck, use one large screenshot per proof panel. Do not shrink
all three full-screen images onto one slide.

## Management value

- Gives application teams one simple, governed model-access pattern.
- Keeps the underlying AWS credential outside the developer experience.
- Makes project/model policy visible before an invocation is allowed.
- Places allowed and denied decisions in one reviewable history.
- Provides a small foundation for evaluating shared AI access across the two
  copilots without claiming that integration already exists.

## Limitations and prohibited claims

Limitations:

- This is a three-view POC, not a production platform.
- The public, TTL-bound demo architecture is not a production deployment model.
- The single-use demo key is not an enterprise credential lifecycle.
- Evidence is bounded to one project, one approved model, one denied model, and
  the recorded test/demo runs.

Do not claim:

- that the AI API Platform currently powers either copilot;
- that the POC is production-ready, enterprise-ready, secure by default, or
  compliant;
- that developers or operators receive unrestricted AWS or infrastructure
  access;
- that screenshots alone prove current AWS execution or cloud state;
- that all model misuse, data leakage, or policy bypass is prevented;
- that AgentCore services are used in the implemented MVP;
- quantified savings, risk reduction, compliance improvement, or performance
  beyond the recorded evidence.

## Recommended portfolio content - maximum three slides

### Slide 1 - Governed AI access for both copilots

- Problem: teams need AI capabilities without distributing cloud credentials
  or allowing unrestricted model choice.
- Solution: one platform credential, one policy gate, one approved Bedrock
  path, and one audit trail.
- Portfolio note: shared use by Security Copilot and Compliance Copilot is
  **PLANNED**, not implemented.
- Suggested headline: **Access. Govern. Prove.**

### Slide 2 - One request proves the policy boundary

- Flow: create key -> approved model succeeds -> restricted model is denied ->
  both decisions are recorded.
- Use `playground-allowed.png` and `playground-denied.png` as separate large
  proof panels or reveal them sequentially.
- Label the visible behavior **DEMO-PROVEN** and the deterministic policy/browser
  checks **TEST-PROVEN**.

### Slide 3 - Management value and next decision

- Use `logs-allowed-denied.png` as the main proof image.
- Value: a simpler developer interface, central model policy, and common audit
  visibility.
- Limitation: no production identity, multi-tenancy, resilience, private
  networking, or copilot integration is proven.
- Decision request: approve a bounded evaluation of this platform pattern as a
  shared service; do not approve production deployment from this POC.

## Validation and evidence references

Current-truth sources:

- `README.md` - scope, architecture, local/live boundaries, and cleanup
- `docs/demo.md` - management story and evidence labels
- `docs/ISSUE_4_REUSE_DECISION.md` - deliberately omitted services and sample
  reuse decision
- `docs/aws-resource-record.csv` - redacted lifecycle record
- `scripts/check.sh` - deterministic local validation entrypoint
- `scripts/browser-e2e.sh` - bounded Playwright Core browser proof and cleanup
- `frontend/e2e/browser-e2e.mjs` - browser assertions and screenshot capture
- `frontend/src/portal.test.ts` - frontend behavior tests
- `api/test_handler.py` - backend policy tests

Handoff validation:

- Current commit and merged PR were read from the repository and GitHub.
- Screenshot files exist at 1920 x 1080 and were visually inspected.
- Screenshot captions describe only visible or independently tested behavior.
- Proof labels follow the management presentation protocol.
- Public-safety scanning covers credentials, AWS account IDs, ARNs, API
  endpoints, private hosts, and real platform keys.
- No AWS call, infrastructure mutation, PPTX creation, commit, push, or GitHub
  mutation is part of this handoff.
