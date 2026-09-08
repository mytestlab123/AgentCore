# Issue #24: native LibreChat governance demo

This integration is a small governed MCP tool flow for the AgentCore POC.
LibreChat owns the approval UI, checkpoint/resume, static allow/ask/deny policy,
and trusted approval hook. The dependency-free MCP server reads one fixed
dedicated demo Security Group with `ec2:DescribeSecurityGroups`, evaluates only
unrestricted TCP/22 ingress, uses the retained Gateway verifier, and records a
harmless local state marker. It never creates or mutates AWS resources.

## Configure

1. Copy `librechat.yaml.example` into the LibreChat configuration.
2. Replace both `/absolute/path/to/...` placeholders.
3. Set `ENDPOINTS=custom,agents` in LibreChat's `.env` when custom endpoints
   are also configured; `agents` must be listed or the native Agents endpoint
   is hidden from the endpoint selector.
4. In the private LibreChat runtime, use the host instance role for the
   read-only `ec2:DescribeSecurityGroups` query and the fixed retained-Gateway
   MCP call. Set the dedicated demo Security Group ID in
   `GOVERNANCE_SECURITY_GROUP_ID` and the existing managed Gateway URL in
   `GOVERNANCE_GATEWAY_URL`.
   The Gateway Cedar policy, not a copied local credential, must authorize that
   instance role for the narrow `dev` tool call.
5. Ensure the state directory is private (`700`) and restart LibreChat so the
   MCP server and trusted hook load.
6. Select `Agents`, open the native Agent Builder, and create an Agent with the
   `agentcore_governance` MCP server selected.

The example policy includes both the documented `mcp:server:tool` patterns and
the concrete `tool_mcp_server` keys LibreChat persists for existing agents.
Keep both forms when upgrading a retained deployment so allow/ask/deny rules
do not fall through on older saved agents.

## Five-minute flow

1. Ask `Check the security finding for web-01.` The check tool is **ALLOW** and
   reports only the fixed rule, public source, compliance state, and exact
   recommendation from the dedicated demo Security Group. No group ID, VPC ID,
   account value, ARN, raw payload, or credential is displayed.
2. Ask `Apply the remediation for web-01 in dev.` Select **Reject**. The MCP
   server is not called and the state remains unchanged (**ASK / Reject**).
   LibreChat may render this native rejection as **Cancelled**; that is the
   expected visual proof that the pending tool call was stopped before MCP
   execution, not a failed remediation. If the model receives control after
   the rejection, its final text should begin `ASK / REJECT`.
3. Repeat and select **Approve**. The MCP server asks the already-retained
   AgentCore Gateway for the `dev` decision with the host instance role. Only
   **ALLOW** records one harmless local effect (**ASK / Approve / ALLOW**). The
   response reports one tool call, no AWS mutation, and no secret access. If
   the Gateway role/URL/response gate is unavailable, the server returns
   **BLOCKED** and records no effect.
4. Ask `Delete web-01.` LibreChat blocks the call before the server runs
   (**DENY**).
5. Remediation with `environment=prod` and no ticket is denied by the trusted
   hook. With `ticket=DEMO-123`, the hook abstains and static policy remains
   **ASK**, but the retained Gateway returns **DENY** and the local effect is
   still not recorded. This demonstrates the independent boundary after the UI
   approval path.

## Offline proof

From the repository root:

```bash
python3 integration/librechat-governance/test_governance.py
```

The test checks the exact three tools, native policy patterns, hook decisions,
sanitized AWS-result handling, Gateway allow/deny behavior, approved harmless
effect, and mode-600 state handling. It injects deterministic fakes for the
AWS and Gateway boundaries; it does not claim a screenshot proves a running
LibreChat deployment or a real AWS read.

This is POC policy education, not production RBAC, AWS authorization, or a
multi-user approval queue.

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
