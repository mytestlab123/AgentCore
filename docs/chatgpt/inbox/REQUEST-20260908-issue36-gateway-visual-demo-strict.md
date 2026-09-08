# STRICT implementation contract — Issue #36

Issue:
https://github.com/mytestlab123/AgentCore/issues/36

Prepared: 2026-09-08 SGT

## Status

**PLANNING ONLY / HOLD ACTIVE.**

This contract authorizes no implementation and no AWS mutation.

Codex must not start implementation until either Amit or ChatGPT posts the exact text:

```text
HOLD LIFTED
```

on the linked Draft PR, and only after the dependency/rebase gate below is satisfied.

## Selected direction

Build one **Internal Gateway Policy Visual Demo** for the already-retained Issue #31 proof.

This is the smallest useful next POC because the hard authorization proof already exists and passes. The missing operator capability is only a browser-visible replay of that same proof.

It is intentionally distinct from:

- LibreChat approval UI: LibreChat evaluates emitted model tool calls and is useful for `ASK`/human approval; this POC has no model and no LibreChat.
- Issue #15 model UI: Issue #15 compares model/provider responses; this POC has no prompt, model, provider selection, API key, or free-form request.

The string `prod` used below is only the existing synthetic policy input from Issue #31. It does not select or reference any production environment, account, or infrastructure.

## Dependency and review sequence

The implementation depends on final retained verifier behavior from:

1. PR #33 — native AgentCore Gateway Policy proof;
2. PR #35 / Issue #34 — exact proof-integrity and retained-cost hardening.

Required sequence:

```text
review/merge PR #33
-> rebase/review/merge PR #35 onto main
-> rebase this Issue #36 Draft PR onto current main
-> re-read this contract against merged verifier truth
-> only then may HOLD be lifted
-> implementation
-> review
```

PR #35 must not merge before PR #33.

This Issue #36 PR must not be implemented or reviewed as final code while it still carries a pre-#33/#35 base snapshot.

## One question

> Can Amit visually rerun the already-proven retained AgentCore Gateway Policy ALLOW/DENY checks from a loopback-only browser page without exposing AWS secrets/identifiers and without creating, changing, deploying, or deleting AWS resources?

## One command

After HOLD is lifted, expose one repository-owned command that starts the visual verifier, preferably:

```text
python3 scripts/gateway_policy_visual.py --serve
```

The exact filename may be reconciled with merged repository truth after PR #35, but do not add a wrapper merely to preserve this suggested name.

The command must:

- verify the approved local AWS/profile prerequisites;
- bind only to `127.0.0.1:3334`;
- fail if that port is already occupied;
- expose one tiny page with exactly two live actions;
- own listener start/stop and clean local shutdown;
- never create/update/deploy/delete/cleanup/converge AWS resources.

## One happy path

```text
start loopback verifier
-> validate local profile/Region/identity gates
-> validate exact retained Issue #31 Gateway/target/Policy Engine/policy/linkage/status/cost
-> browser opens loopback page
-> click Run DEV allow test
-> server sends fixed signed MCP call for environment=dev
-> Gateway Policy returns ALLOW
-> bounded Lambda metric proof shows backend delta exactly 1
-> browser shows sanitized DEV PASS state
-> click Run PROD deny test
-> server sends fixed signed MCP call for environment=prod
-> Gateway Policy returns DENY
-> bounded Lambda metric proof shows backend delta exactly 0
-> browser shows sanitized PROD PASS state
-> page shows final PASS
-> bounded browser E2E captures sanitized proof
-> listener/browser helper stop cleanly
```

No infrastructure lifecycle operation is part of this path.

## Fixed visible browser behavior

The page must not contain a prompt box, tool selector, environment selector, URL field, headers field, policy editor, AWS text box, or arbitrary request payload.

Exactly two operator controls are allowed.

### Button 1

Visible label:

```text
Run DEV allow test
```

Server-owned request constant:

```text
check_demo_scope(environment=dev)
```

PASS display must clearly contain:

```text
DEV: ALLOW
BACKEND DELTA: 1
NO INFRASTRUCTURE MUTATION
```

### Button 2

Visible label:

```text
Run PROD deny test
```

Server-owned request constant:

```text
check_demo_scope(environment=prod)
```

PASS display must clearly contain:

```text
PROD: DENY
BACKEND DELTA: 0
BACKEND WAS NOT INVOKED
```

### Final visible result

Only after both checks independently pass:

```text
GATEWAY_VISUAL_RESULT=PASS
```

Any failed prerequisite, AWS validation, metric proof, browser proof, or redaction gate must result in a sanitized `BLOCKED` state.

Do not render raw exceptions or AWS responses in the browser.

## Browser versus server trust boundary

### Browser may

- load static loopback page assets;
- call the two fixed local action endpoints;
- display sanitized status/result fields;
- expose no control that changes the fixed AWS request shape.

### Browser must never receive

- AWS access keys, session tokens, bearer tokens, credential-process output, cookies carrying AWS credentials, or credential metadata;
- expected account/caller hashes;
- account IDs or caller identity strings;
- Gateway URL, ARN, ID, target ID, Lambda ARN/name, Policy Engine ARN/ID, policy ID, CloudFormation identifiers, or private endpoint data;
- Cedar statement/policy text;
- raw Gateway/MCP response;
- raw CloudWatch metrics payload;
- raw CloudFormation/IAM/Lambda/AgentCore API response;
- private evidence paths;
- arbitrary user-supplied AWS values.

### Browser must never send

- tool name;
- environment value;
- target/resource ID;
- Gateway URL;
- AWS service/operation;
- SigV4 fields or headers;
- Cedar/policy text;
- profile, Region, identity hash, ARN, account ID;
- free-form request body.

The two buttons must map to immutable server-owned constants.

### Server owns

- AWS profile and Region selection;
- expected identity hash gates;
- retained-resource discovery;
- exact live policy/linkage/status validation;
- retained-cost gate;
- fixed MCP request construction;
- SigV4/AWS_IAM signing;
- bounded metric readback and delta calculation;
- sanitization/redaction;
- all AWS calls.

## Reuse boundary

Reuse merged Issue #31/#34 verifier logic where safe, but do not expose a code path that can create or converge missing resources.

The visual server must use a **read/verify/invoke-only boundary**.

It must not call or make reachable from browser actions any function/path that can:

- create the synthetic Lambda;
- render/deploy the native AgentCore project;
- bootstrap CDK;
- converge Gateway/Policy resources;
- mutate IAM;
- delete or clean up retained resources;
- change tags, retention, policy, target, or Gateway configuration.

If the retained prerequisite is missing or drifted, return `BLOCKED`; never repair it from the visual demo.

If merged verifier structure makes safe reuse awkward, extract only the smallest read-only helpers needed. Do not duplicate the policy engine or Gateway decision logic.

## Loopback listener ownership

- Listener host must be exactly `127.0.0.1`.
- Preferred fixed port is `3334` so it cannot be confused with the existing port `3333` Issue #15 UI.
- Do not auto-select another port if `3334` is occupied; fail closed with a local operator message.
- Do not bind `0.0.0.0`, `::`, LAN interface, WSL externally reachable wildcard, public hostname, or container-published port.
- Do not add Cloudflare Tunnel, ngrok, SSH forwarding, public reverse proxy, API Gateway, EC2 hosting, LibreChat hosting, or another exposure mechanism.
- Server command owns start/stop. Normal exit and interrupt must release the listener.

## Live AWS validation before either button is enabled

The server must fail closed unless it can verify from the merged hardened proof path:

1. approved profile is available and explicitly selected;
2. Region is exactly the reviewed test Region;
3. current caller matches the private expected identity hashes;
4. retained application and bootstrap topology match exact reviewed counts;
5. retained Gateway and target are in the expected active/ready states;
6. retained Policy Engine is the exact linked engine in `ENFORCE` mode;
7. retained policy is active and its exact Cedar statement equals the reviewed expected statement;
8. retained target links to the exact retained synthetic Lambda;
9. retained metric source exists and is sufficient for bounded delta proof;
10. current retained-cost calculation is strictly below US$2/month.

The page may show only coarse sanitized readiness such as:

```text
RETAINED_PROOF=READY
COST_GATE=PASS
```

Do not expose exact identifiers, byte counts, ARNs, URLs, hashes, policy text, or raw inventory in browser output.

## Live action contract

Each button performs exactly one fixed Gateway invocation plus only the bounded read-only AWS calls needed to validate state and compute backend metric delta.

### DEV action acceptance

PASS requires all of:

```text
DEV_DECISION=ALLOW
DEV_BACKEND_DELTA=1
```

The successful Gateway result must correspond to the fixed synthetic Lambda response through the retained Gateway path.

Direct Lambda invocation does not count as acceptance proof.

### PROD action acceptance

PASS requires all of:

```text
PROD_DECISION=DENY
PROD_BACKEND_DELTA=0
```

A denial string by itself is insufficient. The independent backend metric delta must remain zero.

If the denied request reaches Lambda, the action fails even if an upstream component reports DENY.

## Final acceptance result

The complete browser proof may print/record only sanitized fields such as:

```text
DEV_DECISION=ALLOW
DEV_BACKEND_DELTA=1
PROD_DECISION=DENY
PROD_BACKEND_DELTA=0
RETAINED_COST_GATE=PASS
BROWSER_SECRET_EXPOSURE=0
INFRASTRUCTURE_MUTATION=0
GATEWAY_VISUAL_RESULT=PASS
```

No exact cost number is required in browser-visible output. Detailed current cost evidence remains in the hardened private/server-side proof path.

## Explicit non-goals

Do not add or change:

- LLM/model invocation;
- prompt input or chat behavior;
- LibreChat;
- AgentCore Harness;
- AgentCore Runtime;
- AgentCore Memory;
- custom policy engine;
- Temporal Policy or approval sequencing;
- human approval cards;
- new Gateway, target, Policy Engine, policy, Lambda, IAM resource, API Gateway, database, CDK stack, or endpoint;
- CDK bootstrap/deploy/converge/cleanup;
- real infrastructure remediation or mutation;
- EC2, SSM, Inspector, Security Hub, Config, S3 workload integrations;
- arbitrary MCP tools or user-supplied arguments;
- public networking or hosted UI;
- RAG/vector DB, multi-agent, SSO/RBAC, provider routing;
- Issue #15 model-comparison behavior;
- replacement of the existing retained proof verifier.

## Smallest implementation shape

Prefer a small standalone loopback surface rather than modifying the Issue #15 React application.

Expected product changes after HOLD is lifted:

1. one small Python visual-server file, ideally with inline static HTML/JS;
2. one focused Python test file;
3. update the existing bounded browser E2E implementation to explicitly recognize and test this visual page;
4. minimal `scripts/check.sh` wiring only if needed.

Do not create a second frontend build, new framework, dependency, database, router, or generic API layer.

Implementation size is a review concern, not permission to omit safety gates. If the implementation becomes materially larger than a small visual adapter over the merged verifier, stop and report a BLOCKER before broadening scope.

## Backend/offline regression tests

Add only the smallest tests required to prove the new boundary.

At minimum prove:

- bind address is fixed to `127.0.0.1`;
- occupied port fails closed and no alternate port is chosen;
- only the expected local GET/readiness and two fixed POST action routes exist;
- POST requests with a body, query string, unexpected header-driven behavior, unknown action, or free-form field cannot alter tool/environment/AWS inputs;
- DEV action maps only to the immutable `dev` request;
- PROD action maps only to the immutable `prod` request;
- browser response schema is a fixed sanitized allowlist;
- sanitization excludes credential-like values, expected identity hashes, account IDs, ARNs, AWS URLs/endpoints, Cedar text, private evidence paths, and raw response fragments;
- failed profile/identity/status/linkage/policy/metric/cost validation returns sanitized `BLOCKED`;
- no create/update/deploy/delete/bootstrap/cleanup/converge function is reachable from server routes;
- DEV requires ALLOW plus backend delta exactly 1;
- PROD requires DENY plus backend delta exactly 0;
- any unexpected backend delta prevents PASS;
- no AWS call occurs in unit/offline tests.

Do not add a new test framework.

## Repository validation

Required after implementation:

```text
./scripts/check.sh
```

Also run the focused server regression tests and normal syntax/whitespace checks already expected by the repository.

## Bounded browser E2E

The existing browser helper currently carries stale Issue #9 expectations against the newer Issue #15 page. This milestone must update the bounded browser path so it understands the current UI under test rather than relying on those stale selectors.

The Issue #36 browser E2E must:

- run only against the exact loopback URL for this visual server;
- assert the listener belongs to this repository/process;
- use selectors/data-testid values owned by Issue #36;
- verify both exact button labels;
- click DEV once and wait for exact visible `ALLOW`, `BACKEND DELTA: 1`, and `NO INFRASTRUCTURE MUTATION` labels;
- click PROD once and wait for exact visible `DENY`, `BACKEND DELTA: 0`, and `BACKEND WAS NOT INVOKED` labels;
- verify final `GATEWAY_VISUAL_RESULT=PASS`;
- verify zero browser requests to non-loopback hosts;
- verify browser request payloads contain no AWS credentials, identity hashes, Gateway URL/ID, ARNs, policy text, or arbitrary AWS values;
- scan visible page text and captured local response bodies for forbidden identifier/secret patterns;
- record zero browser secret exposure;
- capture only sanitized screenshots;
- verify console/page errors are absent except any exact explicitly-reviewed benign browser behavior;
- verify Chrome stopped, temporary browser profile removed, and debug port released.

Do not make the Issue #15 model UI pass by weakening assertions. The helper should explicitly distinguish the UI it is testing.

## Public/private evidence boundary

Public Git/PR evidence may contain only sanitized result labels and test summaries.

Do not commit or place in Issue/PR/comments/screenshots:

- account IDs;
- ARNs/resource IDs;
- Gateway URL or endpoint;
- exact caller identity;
- identity hashes;
- credentials/tokens;
- raw Gateway/MCP result;
- raw CloudWatch metric payload;
- raw AWS inventory/API response;
- Cedar statement;
- private evidence filesystem paths containing sensitive context.

Exact live evidence stays private under the existing Issue #31/approved local evidence pattern with restrictive permissions.

## Stop / BLOCKER conditions

Stop without substituting architecture if any of these occurs:

- approved AWS profile is unavailable;
- expected identity does not match;
- retained Gateway/target/Policy Engine/policy is missing or not in reviewed state;
- exact Gateway-to-Policy-Engine or target-to-Lambda linkage differs;
- exact Cedar statement differs from the merged hardened proof;
- retained topology/resource-count validation fails;
- retained metric evidence cannot independently prove backend delta;
- retained-cost estimate is at or above US$2/month;
- port `3334` is already occupied;
- safe read-only helper reuse is impossible without exposing a mutation path;
- browser requires direct AWS access or any AWS identifier/secret;
- browser E2E cannot complete or detects a non-loopback request/secret/private identifier;
- implementation requires a model, LibreChat, Harness/Runtime, public host, new AWS resource, deployment, cleanup, custom policy engine, or another architecture;
- this PR is not rebased onto `main` after PR #33 and PR #35 merge.

BLOCKER format:

```text
BLOCKER
Expected: <reviewed behavior>
Actual: <current merged repository/AWS truth>
Why blocked: <evidence-based reason>
Smallest options: 1. <option>  2. <option>
Architecture changed: NO
Alternative implementation started: NO
Decision required: ChatGPT / Amit
```

## Codex handoff after HOLD is lifted

Codex must work only in this Issue #36 Draft PR after it has been rebased onto current `main`.

Before implementation, Codex must re-read:

- Issue #36;
- this STRICT contract;
- merged Issue #31 proof documentation;
- merged Issue #34 verifier hardening;
- current browser E2E files.

Then implement the smallest read/verify/invoke-only loopback visual adapter and stop after posting one concise PR handoff containing:

- changed files/size;
- exact local command;
- focused/offline test result;
- `./scripts/check.sh` result;
- bounded browser E2E result;
- sanitized DEV/PROD decision/delta labels;
- retained-cost gate PASS/BLOCKED;
- `BROWSER_SECRET_EXPOSURE` value;
- `INFRASTRUCTURE_MUTATION=0` statement;
- confirmation that no model, LibreChat, Harness/Runtime, public endpoint, deployment, cleanup, credential copy, or new AWS resource was added.

Then stop. Do not mark Ready or merge.

## Review / merge gate

Until HOLD is explicitly lifted, Codex must not:

- implement;
- change product/test/browser code;
- make live AWS calls for this Issue;
- mark Ready;
- merge;
- close Issue #36;
- create a replacement Issue, branch, or PR;
- broaden architecture.

After implementation, ChatGPT must review the complete rebased diff and sanitized evidence against Issue #36 and this contract before any Ready/merge decision.
