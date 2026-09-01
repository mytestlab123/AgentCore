# ChatGPT request: choose the next AgentCore POC milestone

## Protocol

Follow the public collaboration protocol:

<https://gist.github.com/amitkarpe/c8d29ad89cafe3ba178fcae29de3c238>

Create exactly one new standalone GitHub Issue in
<https://github.com/mytestlab123/AgentCore>. Do not implement anything and do
not add the answer only as a PR comment.

## Exact question

Review the current repository truth and tell us what we should do next. Choose
exactly one small, bounded objective. Check existing open Issues first. Return
one Issue and one implementation PR plan. Do not implement anything.

## Current repository truth

- Latest accepted milestone: Issue #12, merged by PR #13.
- The POC has one dark local portal with Project and Playground views.
- Two retained, model-scoped Amazon Nova keys can be explicitly revealed for a
  short in-memory window.
- The live playground uses one fixed read-only AWS role and a fixed tool
  allowlist.
- Nova 2 Lite and Nova Pro can summarize sanitized EC2 inventory or Inspector
  findings.
- SSM Parameter Store list/get access is explicitly denied by IAM. The deny
  path skips model inference and returns no parameter metadata.
- Model responses render as safe GitHub-flavored Markdown and report Complete
  versus Truncated using the provider stop reason.
- Local validation, direct live API proof, dependency audit, and production
  frontend build passed. Browser automation was intentionally not used for the
  final iterations.

Immutable references will be supplied after this packet is committed:

- merged PR #13;
- Issue #12;
- this request packet at its exact commit.

## Existing work records

- Open Issue #3 is a broad full-stack bootstrap and remains intentionally
  larger than the current KISS POC.
- Open Issue #8 is an AgentCore Harness learning spike.
- There are no open pull requests at packet creation time.

## Portfolio context

The operator also runs separate Security Copilot and Compliance Copilot local
demos. A future portfolio experience should make all three demos easy to open
with memorable local URLs rather than remembered ports. This is context, not a
preselected solution: compare whether the next AgentCore milestone should be a
small product capability, the existing Harness spike, or a bounded local
access/routing improvement. Select only one.

## KISS and safety gates

- Target one problem, one happy path, one command, one proof, and one result.
- Optimize for a three-to-five-minute management demo.
- Prefer the existing frontend/backend and deterministic repo automation.
- Do not propose a platform rewrite, hosted control plane, Kubernetes, RAG,
  multi-tenant system, broad observability stack, or enterprise framework.
- Do not require public exposure. Local services remain loopback-only.
- Do not publish credentials, AWS identifiers, private endpoints, resource
  identifiers, host details, or raw cloud payloads.
- Any AWS mutation needs a separately approved exact resource envelope,
  lifecycle tags, cost boundary, validation, and cleanup state.
- Do not require Playwright for the next MVP.
- Reuse an existing open Issue if it already owns the selected objective;
  otherwise create one new standalone Issue.

## Required response issue

Create one new standalone GitHub Issue containing:

1. recommendation and why it is the smallest valuable next step;
2. alternatives rejected, including whether Issues #3 or #8 should remain
   deferred;
3. one bounded Issue title and scope;
4. one bounded implementation PR title, expected files, and non-goals;
5. operator journey and three-to-five-minute demo flow;
6. risks, safety gates, cost and cleanup implications;
7. acceptance criteria and deterministic validation/evidence plan;
8. deferred work;
9. explicit statement that this is planning only and not implementation proof.

## Publication safety

This packet is public-safe. It contains no credentials, account identifiers,
ARNs, resource IDs, private endpoints, internal hostnames, IP addresses, or raw
AWS output.
