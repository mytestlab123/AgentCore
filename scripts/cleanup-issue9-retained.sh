#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail
umask 077

mode=${1:-}
profile=${AWS_PROFILE:-amit}
region=${AWS_REGION:-ap-southeast-1}
expected_account=${EXPECTED_AWS_ACCOUNT:-}
expected_caller_arn=${EXPECTED_AWS_CALLER_ARN:-}
user_name=agentcore-issue9-bedrock-api-key-user-r1
policy_name=AgentCoreIssue9BedrockApiKeyPolicy
retained_dir=${ISSUE9_RETAIN_DIR:-$HOME/.AGENTS-temp/AgentCore/issue9-retained}
credential_file=$retained_dir/credential.json
run_id=$(date '+%Y%m%dT%H%M%S%z')
evidence_dir=$HOME/.AGENTS-temp/AgentCore/issue9-cleanup/$run_id

if [[ $mode != --approve-cleanup ]]; then
  echo 'Usage: cleanup-issue9-retained.sh --approve-cleanup' >&2
  exit 2
fi
if [[ $profile != amit || $region != ap-southeast-1 ]]; then
  echo 'NO-GO: retained Issue #9 cleanup is fixed to amit in ap-southeast-1.' >&2
  exit 2
fi
if [[ -z $expected_account || -z $expected_caller_arn ]]; then
  echo 'NO-GO: set EXPECTED_AWS_ACCOUNT and EXPECTED_AWS_CALLER_ARN.' >&2
  exit 2
fi
for command_name in aws install jq rg; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "ERROR: missing command: $command_name" >&2
    exit 1
  }
done

install -d -m 700 "$evidence_dir"
aws sts get-caller-identity --profile "$profile" --region "$region" \
  >"$evidence_dir/identity.json"
account=$(jq -er '.Account' "$evidence_dir/identity.json")
caller_arn=$(jq -er '.Arn' "$evidence_dir/identity.json")
if [[ $account != "$expected_account" || $caller_arn != "$expected_caller_arn" ]]; then
  echo 'NO-GO: AWS profile resolved to an unexpected account or caller.' >&2
  exit 2
fi

if ! aws iam get-user --profile "$profile" --user-name "$user_name" \
  >"$evidence_dir/user-before.json" 2>"$evidence_dir/user-before.stderr"; then
  if rg -q 'NoSuchEntity' "$evidence_dir/user-before.stderr"; then
    rm -f "$credential_file"
    jq -n '{status:"PASS",credentialDeleted:true,userDeleted:true,alreadyAbsent:true}' \
      >"$evidence_dir/result.json"
    echo 'PASS: retained Issue #9 IAM user is already absent.'
    exit 0
  fi
  echo "ERROR: could not inspect retained Issue #9 IAM user; evidence: $evidence_dir" >&2
  exit 1
fi

aws iam list-service-specific-credentials \
  --profile "$profile" \
  --user-name "$user_name" \
  --service-name bedrock.amazonaws.com \
  >"$evidence_dir/credentials-before.json"
while IFS= read -r credential_id; do
  [[ -n $credential_id ]] || continue
  aws iam delete-service-specific-credential \
    --profile "$profile" \
    --user-name "$user_name" \
    --service-specific-credential-id "$credential_id" \
    >>"$evidence_dir/delete-credentials.stdout"
done < <(jq -r '.ServiceSpecificCredentials[].ServiceSpecificCredentialId' "$evidence_dir/credentials-before.json")

aws iam delete-user-policy \
  --profile "$profile" \
  --user-name "$user_name" \
  --policy-name "$policy_name" \
  >"$evidence_dir/delete-policy.stdout" 2>"$evidence_dir/delete-policy.stderr" || true
aws iam detach-user-policy \
  --profile "$profile" \
  --user-name "$user_name" \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockLimitedAccess \
  >"$evidence_dir/detach-policy.stdout" 2>"$evidence_dir/detach-policy.stderr" || true
aws iam delete-user --profile "$profile" --user-name "$user_name" \
  >"$evidence_dir/delete-user.stdout"

if aws iam get-user --profile "$profile" --user-name "$user_name" \
  >"$evidence_dir/user-after.json" 2>"$evidence_dir/user-after.stderr" ||
  ! rg -q 'NoSuchEntity' "$evidence_dir/user-after.stderr"; then
  echo "ERROR: retained Issue #9 IAM user cleanup is not verified; evidence: $evidence_dir" >&2
  exit 1
fi
rm -f "$credential_file"
jq -n '{status:"PASS",credentialDeleted:true,userDeleted:true}' >"$evidence_dir/result.json"
echo "PASS: retained Issue #9 credential and IAM user deleted. Evidence: $evidence_dir"
