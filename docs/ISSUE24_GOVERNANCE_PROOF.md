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
- **READ-ONLY PROVEN:** the synthetic check has no mutation and the test makes
  no network or AWS call.
- **PLANNED:** run the same config in a disposable LibreChat instance and
  capture the native approval UI/checkpoint interaction.
- **NOT PROVEN:** live LibreChat rendering in this worktree, real AWS/Inspector
  authorization, production RBAC, multi-user approval, ticketing, or durable
  production persistence.

No screenshot is treated as proof of AWS state. A future live run must retain
the MCP state file and LibreChat decision evidence separately.
