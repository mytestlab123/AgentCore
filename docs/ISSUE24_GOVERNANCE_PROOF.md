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
The policy carries both the documented `mcp:server:tool` spelling and
LibreChat's persisted `tool_mcp_server` spelling. This is required for agents
whose saved tool list uses the latter form.

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

## GUI mismatch diagnosis (2 September 2026)

The first manual screenshots were not evidence of a model or AWS failure. The
retained agent stored these concrete MCP keys:

```text
check_security_finding_mcp_agentcore_governance
apply_demo_remediation_mcp_agentcore_governance
delete_demo_asset_mcp_agentcore_governance
```

The running YAML initially listed only the colon-form patterns. A direct
LibreChat SDK policy probe reproduced the observed behavior: the read-only
check fell through to `ask`, remediation fell through to `ask`, and deletion
also fell through to `ask` instead of `deny`. The deployment was corrected to
include both spellings, and a second hook matcher was added for the concrete
remediation key. A fresh service start loaded both hook registrations and all
three MCP tools.

The saved agent instructions also asked the model to describe remediation and
wait. They were updated so the model must emit `apply_demo_remediation` for a
dev request and let native LibreChat approval handle the human decision. A
backup of the prior instructions remains on the private host; no secret was
changed.

The remediation MCP schema now states the same rule at the tool boundary:
`ticket` is optional in `dev`, while `prod` requires a `DEMO-*` ticket. This
reduces model ambiguity without moving approval or authorization into the MCP
server.

The policy decision probe after the correction returned:

```text
check_security_finding_mcp_agentcore_governance => allow
apply_demo_remediation_mcp_agentcore_governance => ask
delete_demo_asset_mcp_agentcore_governance => deny
```

The deployed process uses LibreChat's durable MongoDB checkpointer. A prior
restart left an old Node child on port 80; that process was stopped and a new
backend was verified healthy before the successful native approval run.

### Native UI interpretation

The live GUI proof is retained under `docs/presentation/issue24-governance/`:

- `03-ask-native-prompt.png` shows native ASK before execution.
- `04-ask-approve-result.png` shows Approve/Submit resumed the run and returned
  `ASK / APPROVE - Remediation completed`, one MCP call, one harmless local
  effect, no AWS/infrastructure mutation, and no secrets accessed.
- `05-ask-reject-then-approve.png` records the separate Reject then Approve
  exercise. LibreChat may label a rejected pending call **Cancelled**; that is
  the native ASK/Reject representation and causes no MCP call.

The state file after the separate approved exercises reports `remediated=true`
and `remediation_calls=2`; this is an aggregate counter. Each completed UI
result reports exactly one call for its own approval run.

### Accepted DELETE boundary

For `Delete web-01.`, Luna safely refuses before emitting
`delete_demo_asset`. Consequently, the visible native LibreChat deny
interception is not exercised. This is accepted for this POC because the
static/native policy probe resolves the concrete delete key to `deny`, and the
synthetic state retains `delete_calls=0`.

No forcing mechanism was added: tool approval evaluates a model-emitted call;
it does not compel the model to issue one. The generic model refusal is kept as
`nonfinal-delete-model-refusal.png` to document the boundary, not as a native
DENY success claim.

The saved Agent instructions also require the assistant to begin final text
with `ALLOW`, `ASK / REJECT`, `ASK / APPROVE`, or `DENY`. This keeps a model's
paraphrase aligned with the native policy result; the native button labels
remain LibreChat's fixed **Approve**, **Reject**, and **Submit** controls.

### Clarity-fix plan and implementation

The bounded fix was:

1. require exact status prefixes in the saved Agent instructions;
2. make the native ASK reason state the Approve/Reject effects explicitly;
3. keep the existing native buttons and policy engine;
4. retain Markdown status output from the synthetic MCP server;
5. restart LibreChat and verify the saved Agent and HTTP health.

The saved `AgentCore Governance Demo` instructions are versioned in the
retained deployment and the previous text is backed up privately. The current
version requires the exact prefixes and prevents a duplicate call while an
approval card is pending. Even after it was updated to request the delete tool,
Luna safely chose a model-level refusal; the accepted DELETE boundary above
records that live behavior honestly.

No custom approval UI was added: LibreChat's fixed **Approve**, **Reject**, and
**Submit** labels and native styling remain the source of truth.

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
- **LIVE GUI-PROVEN:** native ASK prompt, Reject/Cancelled with no MCP call,
  and Approve/Submit with exactly one MCP call and one harmless local effect
  for that run; no AWS/infrastructure mutation and no secret access.
- **ACCEPTED BOUNDARY:** DELETE is a safe model-level refusal before tool
  emission; static policy resolves `delete_demo_asset` to `deny`, and
  `delete_calls=0`. A visible native DENY interception is not claimed.
- **NOT PROVEN:** real AWS/Inspector authorization; production RBAC;
  multi-user approval; ticketing; or durable production persistence.

No screenshot is treated as proof of AWS state. A future live run must retain
the MCP state file and LibreChat decision evidence separately.
