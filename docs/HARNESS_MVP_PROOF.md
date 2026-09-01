# AgentCore Harness MVP Proof

Status: PASS on 2026-09-01

Command:

```bash
./scripts/harness-mvp.sh --approve-run
```

Acceptance requires all of the following:

- Harness reached `READY`.
- Nova 2 Lite answered the fixed `2 + 2` prompt with `4`.
- Harness deletion was independently verified.
- IAM execution-role deletion was independently verified.

## Result

- Profile alias: `amit`
- Region: `ap-southeast-1`
- Model: `global.amazon.nova-2-lite-v1:0`
- Harness status before invocation: `READY`
- Model answer confirmed: yes
- Harness absent after deletion: yes
- Execution role absent after deletion: yes
- Private evidence:
  `/home/user/.AGENTS-temp/AgentCore/harness-mvp/20260901T221357+0800`

The verbose stream recorded content deltas, stop reason, token usage, and
latency. CloudWatch Transaction Search was not enabled and a navigable trace
was not queried; this proof does not claim a CloudWatch trace view.

Two earlier implementation attempts failed validation and cleaned up. The
first exposed API response-wrapper differences. The second exposed brittle
exact-output expectations. Neither is counted as the passing E2E result.

Raw account identifiers, ARNs, request metadata, and service output remain in
private local evidence and are not committed.
