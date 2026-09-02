# Issue #24: native LibreChat governance demo

This integration is a small, local-only proof of a governed MCP tool flow.
LibreChat owns the approval UI, checkpoint/resume, static allow/ask/deny policy,
and trusted approval hook. The dependency-free MCP server uses synthetic data
and one harmless local state file. It never calls AWS.

## Configure

1. Copy `librechat.yaml.example` into the LibreChat configuration.
2. Replace both `/absolute/path/to/...` placeholders.
3. Set `ENDPOINTS=custom,agents` in LibreChat's `.env` when custom endpoints
   are also configured; `agents` must be listed or the native Agents endpoint
   is hidden from the endpoint selector.
4. Ensure the state directory is private (`700`) and restart LibreChat so the
   MCP server and trusted hook load.
5. Select `Agents`, open the native Agent Builder, and create an Agent with the
   `agentcore_governance` MCP server selected.

The example policy includes both the documented `mcp:server:tool` patterns and
the concrete `tool_mcp_server` keys LibreChat persists for existing agents.
Keep both forms when upgrading a retained deployment so allow/ask/deny rules
do not fall through on older saved agents.

## Five-minute flow

1. Ask `Check the security finding for web-01.` The check tool is **ALLOW**.
2. Ask `Apply the remediation for web-01 in dev.` Select **Reject**. The MCP
   server is not called and the state remains unchanged (**ASK / Reject**).
   LibreChat may render this native rejection as **Cancelled**; that is the
   expected visual proof that the pending tool call was stopped before MCP
   execution, not a failed remediation.
3. Repeat and select **Approve**. One harmless local effect is recorded
   (**ASK / Approve**). The MCP response starts with a clear Markdown
   `ASK / APPROVE` result and reports one tool call, no AWS mutation, and no
   secret access.
4. Ask `Delete web-01.` LibreChat blocks the call before the server runs
   (**DENY**).
5. Remediation with `environment=prod` and no ticket is denied by the trusted
   hook. With `ticket=DEMO-123`, the hook abstains and static policy remains
   **ASK**.

## Offline proof

From the repository root:

```bash
python3 integration/librechat-governance/test_governance.py
```

The test checks the exact three tools, native policy patterns, hook decisions,
ALLOW execution, approved harmless effect, and mode-600 state handling. It does
not claim that a screenshot proves a running LibreChat deployment.

This is synthetic policy education, not production RBAC, AWS authorization, or
a multi-user approval queue.

The `apply_demo_remediation` schema marks `ticket` optional for `dev`; the
native LibreChat approval prompt, not the model or MCP server, is the human
confirmation boundary. `prod` remains guarded by the trusted hook and a
`DEMO-*` ticket.

### Provider boundary

For the expanded PR #25 milestone, the protected GovTechAI Luna route is
tool-capable. The repository adapter translates OpenAI-compatible function
tool requests and follow-up results to the provider Responses protocol and
translates function calls back; it does not execute tools or authorize them.
LibreChat's native MCP approval path remains responsible for ALLOW, ASK, and
DENY. Native Bedrock Nova 2 Lite remains blocked until the existing EC2 role
has approved `bedrock:InvokeModel`; this POC does not change that role.
