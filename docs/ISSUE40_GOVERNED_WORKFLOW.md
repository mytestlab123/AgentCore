# Issue #40 governed workflow

This document states the proof boundary for PR #41. It is intentionally small:
one governed MCP server, one retained AgentCore Gateway, and one future bounded
Harness tool protocol. The one approved AWS control-plane change is a separately
named Cedar permit for the existing LibreChat EC2 role; it does not create or
modify an application, Gateway, target, Lambda, IAM role, or credential.

## Flow

```text
LibreChat Agent
  -> native ALLOW or ASK policy
  -> agentcore_governance MCP server
  -> fixed retained Gateway MCP client (controlled action only)
  -> local demo-state marker (only after Gateway ALLOW)
```

- `check_security_finding(web-01)` is **ALLOW**. It reads only the fixed,
  dedicated Issue #46 demo Security Group with `ec2:DescribeSecurityGroups`
  and evaluates unrestricted TCP/22 ingress. The public result contains only
  rule, public source, compliance state, and exact recommendation; it excludes
  group/VPC/account identifiers, ARNs, credential material, and raw AWS error
  text.
- `apply_demo_remediation(web-01, dev)` is **ASK**. Native LibreChat **Reject**
  means the MCP server is never called. After **Approve**, the server requires
  the retained Gateway verifier to report `ALLOW` before it writes exactly one
  local marker.
- `apply_demo_remediation(web-01, prod, DEMO-123)` may pass the UI ticket hook,
  but the retained Gateway must return `DENY`; no marker is written.
- `delete_demo_asset(web-01)` remains **DENY** in LibreChat and has no local
  delete implementation.

## Harness tool/resume contract

`scripts/harness_inline_tool.py` validates the one allowed inline function:
`check_demo_health({"service":"demo"})`. It creates the exact assistant
`toolUse` / user `toolResult` messages required to resume the same Harness
session. Its trace contains only the fixed tool name, `healthy` result, resume
readiness, and `AWS_CALLS=0`; it excludes session and request identifiers.
The config shape and resume pair follow the [AgentCore Harness tools
documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-tools.html).

Run the local contract proof:

```bash
PYTHONPATH=scripts python3 scripts/test_harness_inline_tool.py
python3 scripts/harness_inline_tool.py --self-test
```

A live Harness tool invocation needs a separately approved Harness resource
run. This PR does not make that claim or create that resource.

## Runtime prerequisites and result meaning

The LibreChat MCP process must receive these non-secret settings from its
private deployment configuration:

```text
GOVERNANCE_AWS_READ_ENABLED=required
GOVERNANCE_AWS_REGION=ap-southeast-1
GOVERNANCE_SECURITY_GROUP_ID=sg-<dedicated-demo-group>
GOVERNANCE_GATEWAY_POLICY_ENABLED=required
GOVERNANCE_GATEWAY_URL=https://<existing-gateway>.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com
```

The MCP runtime uses the LibreChat EC2 instance role; it never receives or
copies the `amit` profile. That role needs only the read-only
`ec2:DescribeSecurityGroups` permission required for the fixed demo Security
Group. The existing Gateway Cedar policy must grant that
specific role only the fixed `check_demo_scope` action in `dev`; `prod` remains
default-deny. If any prerequisite, role authorization, retained resource, or
expected response is missing, the MCP response is **BLOCKED** and records no
local effect. `BLOCKED` is a safe operational result, not an AWS success.

The EC2 role also needs the single IAM transport permission
`bedrock-agentcore:InvokeGateway` on that retained Gateway. This grants no
target action by itself: the Gateway's active Cedar policy still admits only
the fixed `dev` tool call and remains default-deny for `prod`.

The authorization is named `Issue40LibreChatDevPermit`. Its deployment helper
first verifies the pre-existing human permit byte-for-byte, permits only the
EC2 role / fixed tool / retained Gateway / `dev` combination, and reads the
human permit unchanged again after the new policy is active. It never accepts
an extra policy in that retained engine.

`scripts/issue40_configure_librechat.py` is the corresponding host-side YAML
updater. It replaces only the known `agentcore_governance` MCP block, retains a
mode-600 private backup, and refuses unknown top-level fields in that block.
The managed Gateway URL is supplied only at deployment time and is never
committed or printed.

## Validation commands

```bash
python3 integration/librechat-governance/test_governance.py
PYTHONPATH=scripts python3 scripts/test_gateway_policy_poc.py
PYTHONPATH=scripts python3 scripts/test_issue40_gateway_authorize.py
PYTHONPATH=scripts python3 scripts/test_issue40_configure_librechat.py
./scripts/check.sh
```

To perform a real sanitized AWS read on a configured private runtime, use the
LibreChat ALLOW tool flow. Do not treat the offline test as that live proof.
