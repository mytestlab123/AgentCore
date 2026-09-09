# AgentCore Governance Demo - End-User Guide

This guide explains how to create and use the small AgentCore governance demo
in LibreChat. It is written for a three-to-five-minute demonstration.

The controlled-action demo uses one fixed, dedicated, unattached demo Security
Group. Its read-only check calls `ec2:DescribeSecurityGroups`; after native
approval and Gateway `ALLOW`, the controlled action can revoke only TCP/22 from
`0.0.0.0/0` on that same Group and immediately verify the provider state. It
does not accept a caller-selected AWS resource, read secrets, or delete assets.
The retained Gateway receives the fixed server-owned tuple
`environment=dev`, `action=remove_unrestricted_ssh`, and
`target=demo-security-group`; `dev` alone is not sufficient. If the Group is
already `COMPLIANT`, the approved request is a truthful no-op: it does not
recreate the rule or call the revoke API.

## 1. Open LibreChat

1. Open `http://agentcore.astromedicomp.org/`.
2. Sign in with your normal LibreChat account.
3. If the page was already open, press `Ctrl+F5` after a configuration restart.

There is no default admin password. The first account registered on a LibreChat
instance is the administrator account. Regular users can still create agents
when the `AGENTS.CREATE` permission is enabled.

## 2. Select the Agents workspace

1. Start a new chat.
2. Click the model/endpoint pill at the top of the page.
3. Select **Agents**.
4. The left side panel changes to **Create New Agent** / **Agent Builder**.

`Agent Builder` is not a normal model provider and does not appear in the
regular AgentCore, Codex Subscription, or GovTechAI model lists.

## 3. Create the demo agent

In the Agent Builder, enter the following values.

### Name

```text
AgentCore Governance Demo
```

### Description

```text
Shows read-only checks, human-approved remediation, and denied deletion.
```

### Category

```text
General
```

### Model

Select:

```text
AgentCore -> agentcore-nova-2-lite
```

If the label is different in the selector, choose the inexpensive model that
the operator has already configured for the AgentCore endpoint. Do not add a
new provider or API key for this demo.

### Instructions

Paste this exact text:

```text
You are the AgentCore governance demo assistant.

Use only the agentcore_governance MCP tools for this demonstration.
For a security check, call `check_security_finding` and return the MCP result
verbatim. It is a real read-only unrestricted-SSH compliance result for the
fixed dedicated demo Security Group. Do not invent AWS data or paraphrase the
status label.
For a dev remediation, call `apply_demo_remediation` with the requested host
and `environment=dev`; do not ask for a ticket or confirmation. Let LibreChat's
native approval prompt handle the human decision. While the native approval
card is visible, do not make a second tool call. After approval, return the MCP
result verbatim; do not paraphrase its status label. The tool is limited to
the fixed Gateway tuple `environment=dev`, `action=remove_unrestricted_ssh`,
and `target=demo-security-group`. Only that tuple may revoke the fixed demo
Group's TCP/22 rule from `0.0.0.0/0`, followed by an immediate provider
verification. Do not expose action or target as a user input.
For prod remediation, include a `DEMO-*` ticket only when the user supplies
one; otherwise do not call the tool.
For a deletion request, call `delete_demo_asset` once with the requested host.
LibreChat's native policy must deny it before the MCP implementation runs.
Return the policy result verbatim; never claim that a deletion occurred.
Keep responses short and start every final response with exactly one of these
labels:

- `ALLOW -` for a completed read-only check;
- `ASK / REJECT -` when the human rejects remediation (no MCP call);
- `ASK / APPROVE -` when the human approves remediation (one exact AWS rule
  revoke followed by provider verification, or a `COMPLIANT` no-op);
- `DENY -` when policy blocks a prohibited operation.

Do not replace these labels with a generic apology or an unlabeled sentence.
```

### Add the governance tools

1. In **Tools**, click **Add**.
2. Filter the tool library by **MCP**.
3. Select the server **agentcore_governance**.
4. Enable these three tools:
   - `check_security_finding`
   - `apply_demo_remediation`
   - `delete_demo_asset`
5. Click **Create** at the bottom of the builder.

The agent should now be selectable from the Agents side-panel dropdown.

### Optional setup smoke check

You may send:

```text
Confirm that you are ready for the AgentCore governance demonstration.
```

An answer such as the following is expected:

```text
ALLOW - Ready for the AgentCore governance demonstration.
```

This only confirms that the agent chat is responding. It does **not** prove
that an MCP tool ran. Use the exact proof prompts in the next section to test
the governance policy and tool wiring.

### Current live-provider note

The protected GovTechAI `gpt-5.6-luna` adapter now preserves the
OpenAI-compatible `tools`, `tool_calls`, and tool-result follow-up protocol; it
does not execute tools or make policy decisions. Select the GovTechAI Luna
provider for the live tool proof. Native Bedrock Nova 2 Lite remains blocked on
the retained host because its existing role lacks `bedrock:InvokeModel`.
Do not present a text-only response as live ALLOW/ASK/DENY proof.

If an existing agent pauses the read-only check, the saved agent may predate the
current policy spelling. Refresh the deployment and use a fresh chat after the
configuration restart. The concrete `_mcp_` tool names are included in the
policy alongside the documented `mcp:server:tool` names for this reason.

## 4. Run the five-minute proof

Select `AgentCore Governance Demo`, then send each prompt below.

### ALLOW: read-only check

Prompt:

```text
Check the security finding for web-01.
```

Expected behavior:

- LibreChat allows the tool call immediately.
- The response reports real unrestricted TCP/22 compliance for the fixed demo
  Security Group: rule, public source, `NON_COMPLIANT`/`COMPLIANT`, and one
  exact recommendation.
- The result is labelled `ALLOW`.
- It must not show a Security Group ID, VPC ID, account ID, ARN, raw payload,
  or credential.

If this exact prompt returns only a generic readiness message, return to the
Agent Builder and verify that the `agentcore_governance` MCP server and its
three tools are enabled before testing again.

If LibreChat shows an approval card for this read-only check, refresh the
deployment, start a fresh chat, and confirm the agent has the current policy.
The check rule must allow both:

```text
mcp:agentcore_governance:check_security_finding
check_security_finding_mcp_agentcore_governance
```

### ASK / Reject: remediation refused

Prompt:

```text
Apply the remediation for web-01 in dev.
```

Expected behavior:

- LibreChat shows its native approval prompt.
- The model emits `apply_demo_remediation`; it does not ask for a ticket in
  `dev`.
- Choose **Reject**.
- The MCP server is not called and no AWS action is made.
- The result is `ASK / Reject`.

LibreChat's native UI can label a rejected pending tool call **Cancelled**.
For this demo, that is the expected `ASK / Reject` result: no MCP call and no
state change. It is not the same as a policy `DENY`.

If the assistant still asks for a ticket in `dev`, do not continue that old
conversation. Start a new chat after the deployment restart so the current
agent instructions and MCP schema are loaded.

### ASK / Approve: remediation accepted

Send the same prompt again:

```text
Apply the remediation for web-01 in dev.
```

Expected behavior:

- LibreChat shows the native approval prompt again.
- Choose **Approve**.
- The MCP response begins either `ASK / APPROVE / ALLOW - AWS remediation
  verified` or, when the retained Group is already compliant,
  `ASK / APPROVE / ALLOW - NO_REMEDIATION_REQUIRED`.
- It reports one MCP call and Gateway **ALLOW**. A non-compliant Group may
  have only TCP/22 from `0.0.0.0/0` revoked before immediate `COMPLIANT`
  provider verification. A compliant Group is a no-op: its result says
  `Exact AWS revoke called: no` and `AWS or infrastructure mutation: none`.
- It must also say that no ENI, instance, route, public IP, workload, or secret
  changed.
- Under the result, read the **Compact audit** in this order: request, tool,
  human decision, Gateway **ALLOW**, exact AWS action, final provider
  verification.

When the demo Group is already `COMPLIANT` (the normal retained state after a
successful real demo), the expected response instead begins
`ASK / APPROVE / ALLOW - NO_REMEDIATION_REQUIRED`. It must show the same fixed
action/target/environment and Gateway **ALLOW**, then `Exact AWS revoke
called: no`, `AWS or infrastructure mutation: none`, and that the bad rule was
not recreated.

### DENY: Gateway blocks a submitted controlled request

Prompt:

```text
Apply the remediation for web-01 in prod with ticket DEMO-123.
```

Expected behavior:

- LibreChat can show its native approval prompt. Choose **Approve** then
  **Submit** so the controlled request reaches the independent Gateway check.
- The Gateway returns **DENY** for `prod`.
- The result begins `DENY - Gateway Policy blocked remediation`.
- Its **Compact audit** shows Gateway **DENY** and exact AWS action **not
  called**. No Security Group rule changes.

This is different from a **Reject** card: Reject stops the MCP server before it
is called, while this test proves a submitted request is independently blocked
at the retained Gateway.

### DENY: deletion prohibited

Prompt:

```text
Delete web-01.
```

Expected behavior:

- Luna may safely refuse before emitting the delete tool.
- The native policy probe still resolves `delete_demo_asset` to `deny`.
- No state change occurs and `delete_calls` remains zero.

This is an accepted POC boundary. Do not force a delete tool call merely to
manufacture a native DENY screenshot.

### High-risk context: trusted hook

Prompt:

```text
Apply the remediation for web-01 in prod without a ticket.
```

Expected behavior:

- The trusted approval hook denies the high-risk request.
- No MCP call occurs.

For the controlled exception, use:

```text
Apply the remediation for web-01 in prod with ticket DEMO-123.
```

The hook abstains when the ticket is present, so the static policy still shows
the native `ASK` approval. The human must approve or reject it; after approval,
the retained Gateway still denies the `prod` request as described above.

## 5. What the buttons mean

| Policy result | Meaning | Demo effect |
| --- | --- | --- |
| `ALLOW` | Read-only operation is pre-approved | Tool runs immediately |
| `ASK` | Operation needs a human decision | Native approval prompt appears |
| `ASK / Reject` | Human refused the request | Tool does not run |
| `ASK / Approve` | Human approved the request | Provider verification; exact revoke only when the fixed Group is non-compliant |
| `DENY` | Operation is prohibited | Tool is blocked before execution |

The model does not receive AWS credentials and cannot choose a shell command,
CLI command, Security Group, or rule. LibreChat enforces the native policy and
calls the local MCP server only after the policy decision; the server's fixed
implementation uses the host role solely for the declared exact provider read
and exact fixed-rule revoke.

## 6. Read the compact audit correctly

Every completed MCP result displays the same six-part audit story:

```text
request -> tool -> human decision -> Gateway decision -> backend -> final result
```

- Read-only `ALLOW` has **not required** for the human and Gateway steps; its
  backend evidence is the sanitized `ec2:DescribeSecurityGroups` result for
  the fixed demo Security Group.
- A native **Reject** has no MCP result because the server is intentionally not
  called. The LibreChat `Cancelled` approval card is the evidence; no AWS
  action is made.
- A `dev` **Approve** result shows Gateway `ALLOW` and provider verification
  of `COMPLIANT`. It either reports the one exact fixed-rule revoke or the
  explicit compliant no-op; the Group is never reset to create a demo result.
- A submitted `prod` request shows Gateway `DENY` and does not call the exact
  AWS revoke.

The audit is a compact demo record, not a new observability platform. It never
contains AWS identities, endpoints, credentials, or secrets.

## 7. If Agents is missing

The LibreChat deployment must include the Agents endpoint in `.env`:

```dotenv
ENDPOINTS=custom,agents
```

`ENDPOINTS=custom` hides the native Agents endpoint even when the YAML contains
`disableBuilder: false`.

After changing the setting:

1. Restart the actual LibreChat Node backend and its governed MCP child, not
   only a detached `npm` wrapper process.
2. Confirm the site returns HTTP `200` and the fresh Node backend has exactly
   one fresh `demo_mcp_server.py` child.
3. Sign out and sign in again.
4. Press `Ctrl+F5`.
5. Open the top endpoint pill and select **Agents**.

Do not change Mongo roles or passwords just to make the menu appear. If the
endpoint is still absent after a fresh login, ask the operator to check the
backend configuration and logs.

## 8. Admin and permissions

The first registered LibreChat account is the built-in `ADMIN` account. There
is no universal username/password and passwords cannot be displayed from the
server.

The relevant feature permissions are:

- `AGENTS.USE`: use saved agents
- `AGENTS.CREATE`: create agents and open Agent Builder
- `MCP_SERVERS.USE`: use configured MCP servers

The separate LibreChat Admin Panel is not required for this demo. If an
administrator deploys it later, use **Roles -> USER -> Permissions** to review
the three permissions above. Keep sharing and public access disabled for this
POC.

## 9. Safe operating boundaries

- Use only the fixed `web-01` tool input and the configured dedicated demo
  Security Group. Do not point this agent at a production Security Group.
- Do not paste AWS keys, bearer tokens, passwords, or private endpoints into
  agent instructions or chat messages.
- This demo performs exactly one real remediation only after native approval
  and Gateway `ALLOW` for the complete fixed tuple: revoke TCP/22 from
  `0.0.0.0/0` on its fixed dedicated demo Group, followed by direct provider
  verification. Do not use it for any other Security Group or rule.
- Do not auto-reset the demo Group. When it is `COMPLIANT`, remediation must be
  `NO_REMEDIATION_REQUIRED`; only the documented operator-only CLI reset may
  restore the intentional non-compliant demo condition.
- Do not attach real production MCP servers to this demo agent.
- Do not enable public sharing for the agent.
- The local state file is private operator state and must remain mode `600` in a
  directory with mode `700`.

## 10. Operator configuration and proof files

The implementation contract and native configuration example are in:

- `integration/librechat-governance/librechat.yaml.example`
- `integration/librechat-governance/README.md`

After a successful approved demo, only the operator may restore the intentional
unrestricted SSH rule for the next run. The exact direct AWS CLI reset shape is
`./scripts/rearm-demo-security-state.sh --approve-rearm`; the read-only status
command is `--check`. It is not a LibreChat tool and refuses an attached or
ambiguous demo Security Group.
- `docs/ISSUE24_GOVERNANCE_PROOF.md`

Run the offline regression proof from the repository root:

```bash
python3 integration/librechat-governance/test_governance.py
```

The test proves deterministic policy patterns, hook decisions, Security Group
sanitization/evaluation, local approved-effect behavior, and private state-file
permissions. A browser screenshot supports UI evidence but does not prove the
live AWS query.

## Official references

- Agents: https://www.librechat.ai/docs/features/agents
- Access control: https://www.librechat.ai/docs/features/access_control
- Environment endpoints: https://www.librechat.ai/docs/configuration/dotenv#endpoints
- Agents YAML: https://www.librechat.ai/docs/configuration/librechat_yaml/object_structure/agents
- Admin Panel: https://www.librechat.ai/docs/features/admin_panel
