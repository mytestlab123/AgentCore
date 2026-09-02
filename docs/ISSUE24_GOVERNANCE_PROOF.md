# Issue #24 governance proof

## Scope

This PR is a local, synthetic POC. LibreChat is the operator-facing layer;
its native MCP tool-approval policy, approval UI, checkpoint/resume, and trusted
hook provide the governance path. The demo MCP server is dependency-free and
stdio-only. It never calls AWS and never contains credentials.

## Policy contract

| Operation | Native policy | Expected result |
| --- | --- | --- |
| `check_security_finding` | `allow` | executes directly; deterministic HIGH finding |
| `apply_demo_remediation` | `ask` | Reject: no call; Approve: one harmless local state effect |
| `delete_demo_asset` | `deny` | blocked before the implementation runs |
| remediation in `prod` without `DEMO-*` ticket | trusted hook tightens | deny |
| remediation in `prod` with `DEMO-123` | hook abstains | normal ask remains |

The static policy and hook are in
`integration/librechat-governance/librechat.yaml.example` and
`integration/librechat-governance/approval-hook.cjs`.

## Dual-provider live preflight

The existing protected GovTechAI Responses provider was probed with the same
harmless `check_security_finding` function definition used by the adapter.
The provider returned HTTP 200 with an actual `function_call` named
`check_security_finding`. The adapter now translates Chat Completions
`tools`, assistant `tool_calls`, and tool-result follow-up messages to/from
the provider Responses shape. It only translates protocol data; it never
executes an MCP tool and never makes an approval decision.

The live loopback adapter round trip passed with the protected Luna provider:

```text
LUNA_TOOL_CALL_STATUS=PASS
TOOL_NAME=check_security_finding
LUNA_TOOL_RESULT_STATUS=PASS
FINAL_TEXT_PRESENT=yes
ADAPTER_EXECUTION_STATUS=PASS
```

This proves Luna provider tool-call and tool-result protocol compatibility,
not LibreChat's visible approval UI. The adapter deployment retained the
existing loopback listener and made no AWS resource or IAM change.

Native Bedrock Nova 2 Lite was also probed with the same tool schema using the
EC2 default role chain. AWS returned an identity-policy `AccessDenied` for
`bedrock:InvokeModel` on the Nova inference profile. No credential, policy, or
resource was created or changed; Nova live inference is therefore an
account-role blocker for this milestone, not a claimed PASS.

## Repeatable evidence

Run from `/home/user/.AGENTS-temp/AgentCore/issue-24-librechat-governance`:

```bash
python3 integration/librechat-governance/test_governance.py
```

Expected result:

```text
Ran 3 tests ...
OK
```

The test proves the exact three MCP tools, native allow/ask/deny declarations,
hook decisions, the ALLOW lookup, and the approved harmless effect. The effect
increments `remediation_calls` once and sets `remediated=true` in a temporary
mode-600 file. A fresh server starts with `delete_calls=0`; the denied path is
therefore never executed in the governed flow.

The repository-wide check also runs this test:

```bash
./scripts/check.sh
```

## Claim boundary

- **DEMO-PROVEN:** the native configuration contract and local MCP behavior
  above are repeatable offline.
- **TEST-PROVEN:** the focused test and `scripts/check.sh` pass without AWS.
- **TEST-PROVEN:** the adapter's Luna tool-call translation and tool-result
  follow-up pass in a sanitized live loopback round trip.
- **LIVE PROVIDER-PROVEN:** protected GovTechAI Luna returned a real function
  call; the adapter preserved it without execution or policy logic.
- **BLOCKED:** native Bedrock Nova 2 Lite tool calling is not available to the
  existing EC2 role because `bedrock:InvokeModel` is denied by identity policy.
- **READ-ONLY PROVEN:** the synthetic check has no mutation and the test makes
  no network or AWS call.
- **PLANNED:** run the same config in a disposable LibreChat instance and
  capture the native approval UI/checkpoint interaction.
- **NOT PROVEN:** a visible LibreChat MCP tool call and native ASK Reject /
  Approve screenshots in this run; real AWS/Inspector authorization;
  production RBAC; multi-user approval; ticketing; or durable production
  persistence.

No screenshot is treated as proof of AWS state. A future live run must retain
the MCP state file and LibreChat decision evidence separately.
