#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail
umask 077

mode=${1:---plan}
profile=${AWS_PROFILE:-amit}
region=${AWS_REGION:-ap-southeast-1}
expected_account=${EXPECTED_AWS_ACCOUNT:-}
expected_caller_arn=${EXPECTED_AWS_CALLER_ARN:-}
model_id=global.amazon.nova-2-lite-v1:0
harness_name=AgentCoreHarnessMvpR1
role_name=AgentCoreBedrockAgentCoreHarnessMvpR1
policy_name=AgentCoreHarnessMvpPolicy
ttl=${HARNESS_TTL:-$(date -d '+1 day' '+%d-%m-%y')}
run_id=$(date '+%Y%m%dT%H%M%S%z')
evidence_dir=${EVIDENCE_DIR:-$HOME/.AGENTS-temp/AgentCore/harness-mvp/$run_id}
private_dir=$evidence_dir/private
agentcore_cli=${AGENTCORE_CLI:-$HOME/.local/share/agentcore-cli/node_modules/.bin/agentcore}

usage() {
  cat <<'USAGE'
Usage: harness-mvp.sh [--plan|--approve-run|--cleanup]

--plan         Show the fixed MVP scope. No AWS calls.
--approve-run  Create, invoke, prove, delete, and verify cleanup.
--cleanup      Delete the fixed Harness and IAM role if they exist.

Required for AWS modes:
  AWS_PROFILE, EXPECTED_AWS_ACCOUNT, EXPECTED_AWS_CALLER_ARN
USAGE
}

print_plan() {
  cat <<PLAN
Issue #17 AgentCore Harness MVP
Profile alias: $profile
Region: $region
Harness: $harness_name
Model: $model_id
Prompt: What is 2 plus 2? Return only the number.
Tools: none
Memory: disabled
Session ceiling: 600 seconds (current API minimum)
Resource TTL: $ttl
Lifecycle: always delete Harness and IAM execution role
Estimated AWS cost: below USD 0.01 for one bounded invocation
PLAN
}

case "$mode" in
  --plan)
    print_plan
    exit 0
    ;;
  --approve-run|--cleanup) ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

if [[ -z $expected_account || -z $expected_caller_arn ]]; then
  echo 'NO-GO: set EXPECTED_AWS_ACCOUNT and EXPECTED_AWS_CALLER_ARN.' >&2
  exit 2
fi
if [[ ! $ttl =~ ^[0-9]{2}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo 'NO-GO: HARNESS_TTL must use DD-MM-YY.' >&2
  exit 2
fi
for command_name in aws date install jq rg seq sleep uuidgen; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "ERROR: missing command: $command_name" >&2
    exit 1
  }
done
if [[ ! -x $agentcore_cli ]]; then
  echo "NO-GO: AgentCore CLI not executable: $agentcore_cli" >&2
  exit 2
fi

install -d -m 700 "$private_dir"
export AWS_PROFILE=$profile AWS_REGION=$region AWS_DEFAULT_REGION=$region
identity_file=$private_dir/identity.json
aws sts get-caller-identity --output json >"$identity_file"
actual_account=$(jq -r '.Account' "$identity_file")
actual_caller_arn=$(jq -r '.Arn' "$identity_file")
if [[ $actual_account != "$expected_account" || $actual_caller_arn != "$expected_caller_arn" ]]; then
  echo 'NO-GO: live AWS identity does not match the approved identity.' >&2
  exit 2
fi

role_arn="arn:aws:iam::$actual_account:role/$role_name"
harness_id=''
harness_arn=''
role_created=false
harness_created=false
cleanup_failed=false

find_harness() {
  aws bedrock-agentcore-control list-harnesses --max-results 100 --output json \
    >"$private_dir/list-harnesses.json"
  jq -r --arg name "$harness_name" \
    '.harnesses[]? | select(.harnessName == $name) | .harnessId' \
    "$private_dir/list-harnesses.json" | head -n 1
}

cleanup_resources() {
  local found_id role_absent=false harness_absent=false
  set +o errexit
  found_id=${harness_id:-$(find_harness)}
  if [[ -n $found_id ]]; then
    aws bedrock-agentcore-control delete-harness \
      --harness-id "$found_id" --delete-managed-memory \
      >"$private_dir/delete-harness.json" 2>"$private_dir/delete-harness.err"
    for _ in $(seq 1 60); do
      sleep 5
      if [[ -z $(find_harness) ]]; then
        harness_absent=true
        break
      fi
    done
  else
    harness_absent=true
  fi
  aws iam delete-role-policy --role-name "$role_name" --policy-name "$policy_name" \
    >"$private_dir/delete-role-policy.out" 2>"$private_dir/delete-role-policy.err" || true
  if aws iam get-role --role-name "$role_name" \
    >"$private_dir/role-before-delete.json" 2>"$private_dir/role-before-delete.err"; then
    aws iam delete-role --role-name "$role_name" \
      >"$private_dir/delete-role.out" 2>"$private_dir/delete-role.err" || cleanup_failed=true
  fi
  if aws iam get-role --role-name "$role_name" \
    >"$private_dir/role-after-delete.json" 2>"$private_dir/role-after-delete.err"; then
    cleanup_failed=true
  elif rg -q 'NoSuchEntity' "$private_dir/role-after-delete.err"; then
    role_absent=true
  else
    cleanup_failed=true
  fi
  [[ $harness_absent == true ]] || cleanup_failed=true
  jq -n --argjson harnessDeleted "$harness_absent" \
    --argjson roleDeleted "$role_absent" --argjson cleanupFailed "$cleanup_failed" \
    '{harnessDeleted:$harnessDeleted,roleDeleted:$roleDeleted,cleanupFailed:$cleanupFailed}' \
    >"$evidence_dir/CLEANUP.json"
  set -o errexit
  [[ $cleanup_failed == false ]]
}

on_exit() {
  local exit_code=$?
  trap - EXIT INT TERM
  if [[ $mode == --approve-run && ($role_created == true || $harness_created == true) ]]; then
    cleanup_resources || exit_code=1
  fi
  chmod -R go-rwx "$evidence_dir"
  exit "$exit_code"
}
trap on_exit EXIT INT TERM

if [[ $mode == --cleanup ]]; then
  cleanup_resources
  jq -e '.cleanupFailed == false' "$evidence_dir/CLEANUP.json" >/dev/null
  echo "Cleanup verified. Evidence: $evidence_dir"
  exit 0
fi

if [[ -n $(find_harness) ]] || aws iam get-role --role-name "$role_name" >/dev/null 2>&1; then
  echo 'NO-GO: fixed-name Harness or role already exists; run --cleanup first.' >&2
  exit 2
fi

trust_file=$private_dir/trust.json
policy_file=$private_dir/policy.json
create_file=$private_dir/create-harness-input.json
jq -n --arg account "$actual_account" --arg region "$region" \
  '{Version:"2012-10-17",Statement:[{Effect:"Allow",Principal:{Service:"bedrock-agentcore.amazonaws.com"},Action:"sts:AssumeRole",Condition:{StringEquals:{"aws:SourceAccount":$account},ArnLike:{"aws:SourceArn":("arn:aws:bedrock-agentcore:"+$region+":"+$account+":*")}}}]}' \
  >"$trust_file"
jq -n --arg account "$actual_account" --arg region "$region" --arg model "$model_id" \
  '{Version:"2012-10-17",Statement:[
    {Sid:"BedrockModelInvocation",Effect:"Allow",Action:["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],Resource:[("arn:aws:bedrock:"+$region+":"+$account+":inference-profile/"+$model),"arn:aws:bedrock:*::foundation-model/amazon.nova-2-lite-v1:0"]},
    {Sid:"EcrPublicTokenAccess",Effect:"Allow",Action:"ecr-public:GetAuthorizationToken",Resource:"*"},
    {Sid:"StsForEcrPublicPull",Effect:"Allow",Action:"sts:GetServiceBearerToken",Resource:"*"},
    {Sid:"XRayTracingAccess",Effect:"Allow",Action:["xray:PutTraceSegments","xray:PutTelemetryRecords","xray:GetSamplingRules","xray:GetSamplingTargets"],Resource:"*"},
    {Sid:"CloudWatchLogs",Effect:"Allow",Action:["logs:CreateLogGroup","logs:DescribeLogStreams","logs:CreateLogStream","logs:PutLogEvents"],Resource:("arn:aws:logs:"+$region+":"+$account+":log-group:/aws/bedrock-agentcore/runtimes/*")},
    {Sid:"CloudWatchLogsAccount",Effect:"Allow",Action:["logs:DescribeLogGroups","logs:PutResourcePolicy"],Resource:"*"},
    {Sid:"CloudWatchMetrics",Effect:"Allow",Action:"cloudwatch:PutMetricData",Resource:"*",Condition:{StringEquals:{"cloudwatch:namespace":"bedrock-agentcore"}}},
    {Sid:"AgentCoreWorkloadIdentity",Effect:"Allow",Action:["bedrock-agentcore:GetWorkloadAccessToken","bedrock-agentcore:GetWorkloadAccessTokenForJWT"],Resource:[("arn:aws:bedrock-agentcore:"+$region+":"+$account+":workload-identity-directory/default"),("arn:aws:bedrock-agentcore:"+$region+":"+$account+":workload-identity-directory/default/workload-identity/harness_*")]}
  ]}' >"$policy_file"

aws iam create-role --role-name "$role_name" \
  --assume-role-policy-document "file://$trust_file" \
  --tags \
    Key=Name,Value="$role_name" Key=dev,Value=amit Key=project,Value=AgentCore \
    Key=created,Value=2026-09-01 Key=tools,Value=cdx Key=environment,Value=dev \
    Key=owner,Value=amit Key=version,Value=r1 Key=TTL,Value="$ttl" \
    Key=purpose,Value=harness-mvp Key=phase,Value=harness-mvp Key=cleanup,Value=delete \
  >"$private_dir/create-role.json"
role_created=true
aws iam put-role-policy --role-name "$role_name" --policy-name "$policy_name" \
  --policy-document "file://$policy_file"
sleep 10

jq -n --arg name "$harness_name" --arg role "$role_arn" --arg model "$model_id" \
  --arg ttl "$ttl" \
  '{harnessName:$name,executionRoleArn:$role,
    environment:{agentCoreRuntimeEnvironment:{lifecycleConfiguration:{idleRuntimeSessionTimeout:600,maxLifetime:600},networkConfiguration:{networkMode:"PUBLIC"}}},
    model:{bedrockModelConfig:{modelId:$model,maxTokens:128,temperature:0,topP:1,apiFormat:"converse_stream",additionalParams:{}}},
    systemPrompt:[{text:"Follow the user instruction exactly. Do not use tools."}],
    memory:{disabled:{}},maxIterations:1,maxTokens:128,timeoutSeconds:120,
    tags:{Name:$name,dev:"amit",project:"AgentCore",created:"2026-09-01",tools:"cdx",environment:"dev",owner:"amit",version:"r1",TTL:$ttl,purpose:"harness-mvp",phase:"harness-mvp",cleanup:"delete"}}' \
  >"$create_file"
aws bedrock-agentcore-control create-harness --cli-input-json "file://$create_file" \
  --output json >"$private_dir/create-harness.json"
harness_id=$(jq -er '.harness.harnessId | select(type == "string" and length > 0)' \
  "$private_dir/create-harness.json")
harness_arn=$(jq -er '.harness.arn | select(type == "string" and length > 0)' \
  "$private_dir/create-harness.json")
harness_created=true

status=''
for _ in $(seq 1 60); do
  aws bedrock-agentcore-control get-harness --harness-id "$harness_id" \
    --output json >"$private_dir/get-harness.json"
  status=$(jq -r '.harness.status // .status // "UNKNOWN"' \
    "$private_dir/get-harness.json")
  [[ $status == READY ]] && break
  [[ $status == CREATE_FAILED ]] && break
  sleep 5
done
if [[ $status != READY ]]; then
  echo "ERROR: Harness did not become READY; status=$status" >&2
  exit 1
fi

session_id=$(uuidgen)
"$agentcore_cli" invoke --harness-arn "$harness_arn" --region "$region" \
  --session-id "$session_id" --json --verbose \
  'What is 2 plus 2? Return only the number.' \
  >"$private_dir/invoke.jsonl" 2>"$private_dir/invoke.err"
model_text=$(jq -rs \
  '[.[] | select(.type == "contentBlockDelta") | .delta.text // ""] | join("")' \
  "$private_dir/invoke.jsonl")
if ! rg -q '(^|[^0-9])4([^0-9]|$)' <<<"$model_text"; then
  echo 'ERROR: invocation did not return the expected answer.' >&2
  exit 1
fi

jq -n --arg result HARNESS_MVP_PASS --arg model "$model_id" \
  '{status:"PASS",result:$result,answerConfirmed:true,model:$model,tools:"none",memory:"disabled",cleanup:"pending"}' \
  >"$evidence_dir/RESULT.json"
cleanup_resources
role_created=false
harness_created=false
jq -e '.cleanupFailed == false and .harnessDeleted and .roleDeleted' \
  "$evidence_dir/CLEANUP.json" >/dev/null
jq '.cleanup="verified"' "$evidence_dir/RESULT.json" >"$evidence_dir/RESULT.tmp"
mv "$evidence_dir/RESULT.tmp" "$evidence_dir/RESULT.json"
chmod -R go-rwx "$evidence_dir"
echo "HARNESS_MVP_PASS"
echo "Cleanup verified. Evidence: $evidence_dir"
