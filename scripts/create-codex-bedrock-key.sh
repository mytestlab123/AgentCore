#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail
umask 077

mode=${1:---plan}
profile=${AWS_PROFILE:-amit}
region=${AWS_REGION:-ap-southeast-1}
model=${ISSUE12_CODEX_MODEL:-openai.gpt-5.6-luna}
expected_account=${EXPECTED_AWS_ACCOUNT:-}
expected_caller_arn=${EXPECTED_AWS_CALLER_ARN:-}
ttl=${ISSUE12_TTL:-01-10-26}
credential_age_days=${ISSUE12_CREDENTIAL_AGE_DAYS:-30}
user_name=agentcore-issue12-codex-key-user-r1
policy_name=AgentCoreIssue12CodexKeyPolicy
retained_dir=${ISSUE12_RETAIN_DIR:-$HOME/.AGENTS-temp/AgentCore/issue12-codex-key}
credential_file=$retained_dir/credential.json
metadata_file=$retained_dir/metadata.json
evidence_dir=${EVIDENCE_DIR:-$HOME/.AGENTS-temp/AgentCore/issue12-codex-key-create/$(date '+%Y%m%dT%H%M%S%z')}

print_plan() {
  printf 'Issue #12 Codex Bedrock key\nProfile: %s\nRegion: %s\nModel: %s\nIAM user: %s\nTTL: %s\nCredential lifetime: %s days\nCleanup: review\n' \
    "$profile" "$region" "$model" "$user_name" "$ttl" "$credential_age_days"
}

case "$mode" in
  --plan) print_plan; exit 0 ;;
  --approve-run) ;;
  *) echo 'Usage: create-codex-bedrock-key.sh [--plan|--approve-run]' >&2; exit 2 ;;
esac
if [[ $profile != amit || $region != ap-southeast-1 ]]; then
  echo 'NO-GO: Issue #12 is fixed to amit in ap-southeast-1.' >&2
  exit 2
fi
if [[ -z $expected_account || -z $expected_caller_arn ]]; then
  echo 'NO-GO: expected AWS account and caller gates are required.' >&2
  exit 2
fi
if [[ ! $model =~ ^openai\.[A-Za-z0-9._-]+$ ]]; then
  echo 'NO-GO: model must be an exact openai.* Bedrock model ID.' >&2
  exit 2
fi
if [[ ! $ttl =~ ^[0-9]{2}-[0-9]{2}-[0-9]{2}$ || $credential_age_days != 30 ]]; then
  echo 'NO-GO: Issue #12 requires an uppercase TTL date and 30-day credential.' >&2
  exit 2
fi
for command_name in aws cut install jq sha256sum; do
  command -v "$command_name" >/dev/null 2>&1 || { echo "ERROR: missing command: $command_name" >&2; exit 1; }
done
if [[ -e $credential_file ]]; then
  echo 'NO-GO: a retained Issue #12 Codex key already exists.' >&2
  exit 2
fi

install -d -m 700 "$evidence_dir" "$retained_dir"
aws sts get-caller-identity --profile "$profile" --region "$region" >"$evidence_dir/identity.json"
account=$(jq -er '.Account' "$evidence_dir/identity.json")
caller_arn=$(jq -er '.Arn' "$evidence_dir/identity.json")
if [[ $account != "$expected_account" || $caller_arn != "$expected_caller_arn" ]]; then
  echo 'NO-GO: AWS profile resolved to an unexpected account or caller.' >&2
  exit 2
fi
aws bedrock get-foundation-model --profile "$profile" --region "$region" \
  --model-identifier "$model" >"$evidence_dir/model.json"
jq -e --arg model "$model" '.modelDetails.modelId == $model and .modelDetails.modelLifecycle.status == "ACTIVE"' \
  "$evidence_dir/model.json" >/dev/null || { echo "NO-GO: model is not active: $model" >&2; exit 2; }
if aws iam get-user --profile "$profile" --user-name "$user_name" >"$evidence_dir/existing-user.json" 2>/dev/null; then
  echo "NO-GO: dedicated IAM user already exists: $user_name" >&2
  exit 2
fi

policy_file=$evidence_dir/policy.json
jq -n --arg region "$region" --arg model "$model" '{Version:"2012-10-17",Statement:[
  {Sid:"AllowLongTermBedrockBearerToken",Effect:"Allow",Action:"bedrock:CallWithBearerToken",Resource:"*",Condition:{StringEquals:{"bedrock:bearerTokenType":"LONG_TERM"}}},
  {Sid:"AllowApprovedCodexModelOnly",Effect:"Allow",Action:["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],Resource:["arn:aws:bedrock:\($region)::foundation-model/\($model)"]}
]}' >"$policy_file"

created=false
credential_id=''
cleanup_on_failure() {
  local exit_code=$?
  if ((exit_code != 0)) && [[ $created == true ]]; then
    if [[ -n $credential_id ]]; then
      aws iam delete-service-specific-credential --profile "$profile" --user-name "$user_name" \
        --service-specific-credential-id "$credential_id" >/dev/null 2>&1 || true
    fi
    aws iam delete-user-policy --profile "$profile" --user-name "$user_name" --policy-name "$policy_name" >/dev/null 2>&1 || true
    aws iam delete-user --profile "$profile" --user-name "$user_name" >/dev/null 2>&1 || true
    rm -f "$credential_file" "$metadata_file"
  fi
  exit "$exit_code"
}
trap cleanup_on_failure EXIT

aws iam create-user --profile "$profile" --user-name "$user_name" --tags \
  Key=Name,Value="$user_name" Key=dev,Value=amit Key=project,Value=AgentCore \
  Key=created,Value="$(date '+%Y-%m-%d')" Key=tools,Value=cdx Key=environment,Value=dev \
  Key=owner,Value=amit Key=version,Value=issue-12-r1 Key=TTL,Value="$ttl" \
  Key=purpose,Value=codex-bedrock-key-poc Key=phase,Value=issue-12 Key=cleanup,Value=review \
  >"$evidence_dir/create-user.json"
created=true
aws iam put-user-policy --profile "$profile" --user-name "$user_name" --policy-name "$policy_name" \
  --policy-document "file://$policy_file" >"$evidence_dir/put-policy.json"
aws iam create-service-specific-credential --profile "$profile" --user-name "$user_name" \
  --service-name bedrock.amazonaws.com --credential-age-days "$credential_age_days" >"$evidence_dir/credential.json"
credential_id=$(jq -er '.ServiceSpecificCredential.ServiceSpecificCredentialId' "$evidence_dir/credential.json")
install -m 600 "$evidence_dir/credential.json" "$credential_file"
api_key=$(jq -er '.ServiceSpecificCredential.ServiceApiKeyValue // .ServiceSpecificCredential.ServiceCredentialSecret' "$credential_file")
fingerprint=$(printf '%s' "$api_key" | sha256sum | cut -d' ' -f1)
unset api_key
jq -n --arg model "$model" --arg fingerprint "${fingerprint:0:12}" --arg TTL "$ttl" \
  '{state:"CREATED",model:$model,keyFingerprint:$fingerprint,credentialAgeDays:30,TTL:$TTL,cleanup:"review"}' \
  >"$evidence_dir/metadata.json"
install -m 600 "$evidence_dir/metadata.json" "$metadata_file"
rm -f "$evidence_dir/credential.json"
trap - EXIT
echo "PASS: dedicated Issue #12 Codex key created; protected file: $credential_file"
