# AgentCore Harness MVP Guide

## Outcome

This POC proves one managed AgentCore Harness lifecycle:

`preflight -> create role -> create Harness -> invoke Nova 2 Lite -> verify marker -> delete -> verify absence`

The trusted entry point is:

```bash
./scripts/harness-mvp.sh --approve-run
```

It uses the `amit` profile and `ap-southeast-1` by default. The script refuses
AWS work unless the operator supplies the expected account and caller ARN. It
never writes those identifiers into the repository.

## Install the official CLI

The AWS CLI currently provides Harness control-plane commands, but this POC
uses the official AgentCore CLI for invocation.

```bash
npm install \
  --prefix /home/user/.local/share/agentcore-cli \
  @aws/agentcore@0.28.1
```

Verify it:

```bash
/home/user/.local/share/agentcore-cli/node_modules/.bin/agentcore --version
```

## Learn without AWS changes

Show the exact plan:

```bash
cd /home/user/git/AgentCore
./scripts/harness-mvp.sh --plan
```

Run only offline script checks:

```bash
./scripts/test-harness-mvp.sh
```

Run all repository checks:

```bash
./scripts/check.sh
```

## Run the real proof

Read the expected values without printing secrets, then export them for the
identity gate:

```bash
export AWS_PROFILE=amit
export AWS_REGION=ap-southeast-1
export EXPECTED_AWS_ACCOUNT='approved-account-id'
export EXPECTED_AWS_CALLER_ARN='approved-caller-arn'
./scripts/harness-mvp.sh --approve-run
```

Expected terminal result:

```text
HARNESS_MVP_PASS
Cleanup verified. Evidence: /home/user/.AGENTS-temp/AgentCore/harness-mvp/...
```

The input is a fixed `2 + 2` prompt, and the script requires the streamed model
text to contain the standalone answer `4`. A successful run prints
`HARNESS_MVP_PASS`. The model is `global.amazon.nova-2-lite-v1:0`, capped at
128 tokens and one iteration. No
tool, skill, browser, code interpreter, Gateway, or memory is configured.

## What the command does

1. Confirms the live account and caller match the explicit gate.
2. Rejects a pre-existing fixed-name Harness or role.
3. Creates one tagged least-purpose IAM execution role.
4. Creates one public-network Harness with a 600-second lifecycle ceiling.
5. Waits for `READY` and invokes it through the official AgentCore CLI.
6. Requires the exact response marker.
7. Deletes the Harness, inline policy, and role.
8. Independently verifies that both resources are absent.

The public network mode is an AWS-managed runtime setting; this POC creates no
VPC, subnet, security group, public IP, load balancer, or endpoint.

## Failure recovery

The EXIT trap attempts cleanup after any failure that occurs after role or
Harness creation. If a terminal was killed before the trap ran, use:

```bash
export AWS_PROFILE=amit
export AWS_REGION=ap-southeast-1
export EXPECTED_AWS_ACCOUNT='approved-account-id'
export EXPECTED_AWS_CALLER_ARN='approved-caller-arn'
./scripts/harness-mvp.sh --cleanup
```

Do not recreate until cleanup says it is verified.

## Evidence and proof boundary

Private evidence is stored with mode `700/600` under:

`/home/user/.AGENTS-temp/AgentCore/harness-mvp/<run-id>/`

`RESULT.json` proves the expected model answer was observed. `CLEANUP.json`
proves the fixed Harness and role were absent after deletion. Files under
`private/` contain raw AWS responses and must not be committed or shared.

This proves one short managed Harness invocation and cleanup. It does not prove
production readiness, multi-user authorization, tools, memory, private VPC
connectivity, long sessions, scale, reliability, or a persistent deployment.

The raw invocation stream includes content deltas, stop reason, token usage,
and latency. The run did not enable CloudWatch Transaction Search or query a
CloudWatch trace, so a navigable distributed trace is not proven by this MVP.

## Files and inputs

- `/home/user/git/AgentCore/scripts/harness-mvp.sh`: lifecycle operator.
- `/home/user/git/AgentCore/scripts/test-harness-mvp.sh`: offline contract test.
- `/home/user/git/AgentCore/docs/HARNESS_MVP_GUIDE.md`: operator and learning guide.
- `/home/user/git/AgentCore/docs/HARNESS_MVP_PROOF.md`: sanitized live result.
- `/home/user/git/AgentCore/docs/aws-resource-record.csv`: public-safe create and delete audit.

The generated private run directory contains `create-role.json`,
`create-harness.json`, `get-harness.json`, `invoke.jsonl`, `RESULT.json`, and
`CLEANUP.json`. The create payload fixes the model, system prompt, public
network mode, disabled memory, one iteration, token limit, timeout, and tags.

## Debugging lessons from the first implementation run

The current APIs wrap a create response under `harness` and return list entries
under `harnesses`. Parsing guessed field names caused the first create to stop;
the recovery check found and deleted the Harness before retrying. The parser
now rejects missing IDs and cleanup reads the real list collection.

Nova 2 Lite also declined the first all-caps synthetic marker and added prose
around the arithmetic answer. The trusted assertion therefore checks the
semantic answer `4`, while keeping the task fixed and deterministic. These were
failed validation attempts, not successful proof runs; both cleaned up.

## Cost and retention

Harness itself has no separate fee. Runtime consumption, model tokens, and
observability can incur charges. This run uses one small prompt and deletes the
resource immediately; its expected cost is below USD 0.01. Tags use
`TTL=DD-MM-YY` and `cleanup=delete` as a recovery signal, not as a substitute
for immediate cleanup.

## Source references

- AWS Harness get started: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-get-started.html
- AWS Harness security and execution role: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-security.html
- AWS Harness operations and cost controls: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-operations.html
