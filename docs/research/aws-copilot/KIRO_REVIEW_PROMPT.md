# Kiro independent architecture review prompt

Copy/paste the block below into Kiro after pulling current `main`.

---

You are acting as the **AWS-native architecture reviewer**, not the implementer, for a proposed longer-term product with working name **AWS Copilot**.

This product is intended to evolve from the current `mytestlab123/AgentCore` R&D repository into a clean AWS security/compliance copilot that may eventually serve roughly 14-50+ AWS accounts.

## Read first

Read these files completely:

1. `docs/research/aws-copilot/README.md`
2. `docs/research/aws-copilot/AGENTCORE_ARCHITECTURE.md`
3. `docs/research/aws-copilot/MVP_ROADMAP.md`
4. `docs/research/aws-copilot/SOURCES.md`

Then inspect the existing repo only as evidence/reference for what has already been proven, especially the merged M8 and M9-M13 Security Group / Gateway Policy work. Do **not** assume the old implementation must be preserved.

Also verify the current official AWS AgentCore documentation/release notes as of today. AgentCore is changing quickly; correct any stale statement in this packet.

## Objective

Challenge the proposal. Do not merely endorse it.

We want the smallest correct architecture for a real MVP that:

- uses AWS-native AgentCore capabilities where they remove custom plumbing;
- starts with one real Compliance Agent;
- displays real AWS account/resource identity rather than synthetic presentation aliases;
- makes the actual mutating tool subject to Gateway Policy;
- can later support 14-50+ AWS accounts without personal SSO sessions;
- later adds a Vulnerability Agent and only then a Supervisor/multi-agent flow;
- is practical in `ap-southeast-1`;
- keeps KISS and avoids enterprise/platform work without a demonstrated need.

## Questions to answer

1. **Harness-first vs Runtime-first**
   - Is AgentCore Harness the right starting point for the Compliance Agent?
   - Which requirement would justify exporting Harness to Strands/Runtime?
   - Is any important Harness limitation missing from our packet?

2. **Actual tool behind Gateway**
   - What is the smallest current AWS-native pattern for:
     `Harness -> Gateway + Policy -> exact remediation tool -> AWS API -> verification`?
   - Compare a Gateway Lambda MCP target versus a Runtime-hosted MCP target for our first 2-3 security controls.
   - Confirm whether current Policy enforcement requires the critical action to be an MCP tool.

3. **Multi-account identity**
   - For 14-50+ AWS accounts, is central AgentCore execution identity -> STS `AssumeRole` into fixed member-account roles the right design?
   - Is there a more native AgentCore/Organizations mechanism that is simpler or safer?
   - Should read and remediation use separate roles?

4. **Singapore region constraints**
   - Verify Harness, Runtime, Gateway, Identity, Policy, temporal policy, VPC, Observability and Evaluations in `ap-southeast-1`.
   - Verify AWS Agent Registry region availability.
   - Verify Guardrails-in-Policy availability.
   - Identify any other regional blocker that materially changes the design.

5. **Temporal Policy**
   - Is it a good later mechanism for `detect -> approval -> remediate -> verify`?
   - What exact session/account/Region constraints matter?
   - What should we prove before adopting it?

6. **Skills / native shortcuts**
   - Which curated AWS Agent Skills or Agent Toolkit capabilities can accelerate the Compliance and Vulnerability agents?
   - Clearly separate skills that provide domain knowledge from tools that receive mutation permissions.
   - Identify custom POC code that can be deleted because AgentCore now provides the capability natively.

7. **Two specialists, then supervisor**
   - Validate the proposed sequence: Compliance Agent first, Vulnerability Agent second, manual switching, A2A Supervisor later.
   - If A2A/Runtime offers a much simpler pattern, explain it.
   - Do not recommend a multi-agent swarm merely because AgentCore supports it.

8. **Model plan**
   - Evaluate Nova 2 Lite as a low-cost default candidate, not as an assumed winner.
   - Recommend one comparison model/path available through Harness.
   - Propose a small benchmark based on our actual AWS security tasks.
   - Security enforcement must stay model-independent.

9. **Repository graduation**
   - Should the long-term product start in a clean `amitkarpe/*` repository now?
   - What should be selectively promoted from `mytestlab123/AgentCore`?
   - What should definitely remain behind as R&D history?
   - Working name is `AWS Copilot`, but note any serious naming/product collision and recommend one short repo name if needed.

10. **First 3-6 milestones**
    - Give the highest-value sequence after this review.
    - Prefer a few cohesive milestones over micro-PRs.
    - Identify the **single first implementation milestone** we should open after architecture approval.

## Constraints

- Research/review only. Do not create, update or delete AWS resources.
- Do not create a new repository, Issue or PR.
- Do not use an AWS prod profile/account/environment.
- If an AWS CLI read is genuinely useful, use `AWS_PROFILE=amit` and direct AWS CLI first; keep output sanitized in your response unless the architecture review specifically needs a non-secret identifier.
- No Python/SDK helper for simple CLI inspection.
- Do not assume EKS is needed.
- Do not assume Registry, RAG, SSO/RBAC, billing, a custom frontend, or a new observability platform is needed.
- Prefer native AgentCore features only when they reduce real custom work or strengthen the governance story.

## Required output

Keep the result concise and decision-oriented:

```text
RESULT=PASS|PARTIAL|CHANGE

TOP_DECISIONS=
- ...

NATIVE_SHORTCUTS=
- ...

ARCHITECTURE_CHANGES=
- ...

REGION_BLOCKERS=
- ...

MULTI_ACCOUNT=
- ...

MODEL_PLAN=
- ...

FIRST_MILESTONE=
- ...

NEXT_3_TO_6_MILESTONES=
- ...

REPO_NAME=
- ...

RISKS=
- maximum 5 concrete risks
```

For every material correction, include the current official AWS source URL. If the packet is already correct, say so instead of inventing changes.

---
