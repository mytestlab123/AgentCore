# AgentCore POC Roadmap

Purpose: keep future work moving toward a useful AgentCore platform demo without
turning each idea into a separate micro-POC.

## Working rules

- Follow KISS: one useful milestone, normally 2-3 related improvements, one
  demonstrable outcome.
- Group related milestones when they naturally form one usable outcome; the M1-M7
  labels are capability checkpoints, not mandatory PR boundaries.
- Build the MVP first; add only proportional validation for changed behavior.
- Reuse current code, retained POC resources, LibreChat, Gateway, Harness and
  existing browser/test helpers before adding another framework.
- The home Linux host is a trusted single-user lab. Do not add more local auth,
  proxy, tunnel, network-policy, browser-security, or identity machinery unless
  a concrete problem requires it.
- No automatic fallback to another model/provider/architecture when a proof is
  blocked. Record the blocker and keep the design simple.

## Foundation already proven

The repository already has enough building blocks to stop doing isolated
plumbing experiments:

- governed Bedrock model/API-key access;
- Codex using a governed Bedrock credential;
- two-provider model comparison;
- LibreChat MCP tool governance with ALLOW / ASK / DENY;
- AgentCore Harness lifecycle proof;
- native AgentCore Gateway Policy ALLOW / DENY proof;
- loopback visual Gateway Policy proof with backend execution evidence.

Future milestones should combine these pieces rather than re-prove them.

## Delivery plan

Use two implementation PRs unless a real blocker makes that split impractical:

1. **PR 1 - Governed agent workflow MVP:** M1-M4. Human approval + Gateway
   Policy + Harness tool-use + one real read-only AWS lookup + one harmless
   demo-owned controlled action.
2. **PR 2 - Platform experience + final demo:** M5-M7. Codex/Kiro developer
   clients + one useful audit timeline + polished five-minute Security Copilot
   story.

Do not create separate micro-PRs for each roadmap checkpoint.

## Milestones

### M1 - One governed chat-to-tool path

**Goal:** connect the existing human approval UX to the existing hard Gateway
policy boundary.

- LibreChat emits one synthetic controlled tool call.
- `ASK` provides Approve / Reject before execution.
- Approved execution still passes through AgentCore Gateway Policy; a blocked
  structured input is denied before the backend runs.

**Demo result:** one browser conversation visibly proves human approval **and**
deterministic server-side authorization in the same path.

---

### M2 - Harness tool-use + native trace

**Goal:** move beyond the already-proven Harness create/invoke lifecycle.

- one model selects one read-only synthetic tool;
- client returns the fixed tool result and Harness resumes to the final answer;
- show one useful native trace/log reference using existing observability.

**Demo result:** explain clearly what Harness manages versus what the client,
Gateway and IAM control.

---

### M3 - One real read-only AWS capability

**Goal:** replace one synthetic lookup with one safe, bounded AWS read.

- choose exactly one useful read-only operation;
- expose it through the already-selected governed tool path;
- show sanitized result + audit evidence in the UI.

Good candidates are a small security/compliance status lookup or model-readiness
check. Do not create a generic AWS assistant.

**Demo result:** the platform is no longer only synthetic; it can safely answer
one real AWS operational question.

---

### M4 - One controlled action with human approval

**Goal:** prove the full human-in-the-middle loop on one dedicated demo-owned
action.

- one harmless reversible action only;
- LibreChat `ASK` -> Approve / Reject;
- Gateway Policy remains the hard authorization boundary and the result is
  audited.

Reject must cause no action. Approval must cause exactly one expected effect.

**Demo result:** show `recommend -> approve -> execute -> verify` without
building a general remediation engine.

---

### M5 - Developer clients: Codex + Kiro

**Goal:** show that governed model access is useful outside the web portal.

- keep the existing Codex path;
- prove one equivalent bounded Kiro developer task using the same governance
  idea where current Kiro support permits it;
- document only material client differences.

Do not build a custom client abstraction unless the two real clients expose a
clear gap.

**Demo result:** one governed AI access model can serve both application and
coding-agent workflows.

---

### M6 - Unified audit timeline

**Goal:** make the governance story easy to explain in one screen.

Show only the useful fields needed to follow one request:

- model/provider request;
- tool selected;
- human decision when applicable;
- Gateway Policy decision;
- backend executed or blocked;
- final status / latency / request ID where already available.

Reuse existing logs and evidence. Do not build a new observability platform.

**Demo result:** a reviewer can answer "what happened and why?" without opening
several terminals or pages.

---

### M7 - One polished end-to-end Security Copilot demo

**Goal:** combine the strongest proven pieces into the final 5-minute story.

1. Developer/user enters one security question.
2. Model uses one governed tool.
3. Read-only work proceeds automatically; controlled work pauses for approval.
4. Gateway Policy independently enforces the allowed boundary.
5. Result and audit timeline are visible.

Keep one happy path and one denied/rejected path. Prefer polishing and removing
confusion over adding another service.

**Demo result:** a manager or engineer can understand the value of the platform
within five minutes.

## Deliberately deferred

Do not add these merely because they are common platform features:

- Kubernetes/EKS;
- large multi-agent orchestration;
- RAG/vector database;
- many providers/models;
- LiteLLM or another model router unless native paths show a real gap;
- enterprise multi-user/RBAC/SSO work;
- billing/subscription systems;
- custom approval or policy engine when LibreChat + AgentCore already provide
  the required boundary;
- new local security layers for the trusted home lab.

## How to use this roadmap

1. Use one Issue per useful implementation milestone, not per checkpoint.
2. Keep related implementation and corrections in the same PR.
3. Use focused tests while iterating and one final browser/live proof when the
   milestone makes that claim.
4. Merge when the complete milestone is reviewable and its important path works.
5. Update this file only when the direction materially changes.
