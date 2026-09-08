# Issue #40 governed workflow

This document states the proof boundary for PR #41. It is intentionally small:
one governed MCP server, one retained AgentCore Gateway, and one future bounded
Harness tool protocol. No AWS resource creation or mutation is part of this
milestone.

## Flow

```text
LibreChat Agent
  -> native ALLOW or ASK policy
  -> agentcore_governance MCP server
  -> retained Gateway verifier (controlled action only)
  -> local demo-state marker (only after Gateway ALLOW)
```

- `check_security_finding(web-01)` is **ALLOW**. It returns the fixed synthetic
  finding and calls the fixed read-only `sts:GetCallerIdentity` AWS API. The
  public result says only that identity was verified; it does not expose account
  ID, ARN, user ID, credential material, or AWS error text.
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
GOVERNANCE_GATEWAY_POLICY_ENABLED=required
```

The existing private Gateway identity-hash settings remain outside source
control. If any prerequisite, credential, retained resource, cost gate, or
expected response is missing, the MCP response is **BLOCKED** and records no
local effect. `BLOCKED` is a safe operational result, not an AWS success.

## Validation commands

```bash
python3 integration/librechat-governance/test_governance.py
PYTHONPATH=scripts python3 scripts/test_gateway_policy_poc.py
./scripts/check.sh
```

To perform a real sanitized AWS read on a configured private runtime, use the
LibreChat ALLOW tool flow. Do not treat the offline test as that live proof.
