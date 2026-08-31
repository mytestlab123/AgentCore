#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail
umask 077

[[ ${1:-} == --approve-cleanup ]] || { echo 'Usage: cleanup-issue12-codex-key.sh --approve-cleanup' >&2; exit 2; }
profile=${AWS_PROFILE:-amit}
region=${ISSUE12_REGION:-us-east-2}
expected_account=${EXPECTED_AWS_ACCOUNT:-}
expected_caller_arn=${EXPECTED_AWS_CALLER_ARN:-}
user_name=agentcore-issue12-codex-key-user-r1
policy_name=AgentCoreIssue12CodexKeyPolicy
retained_dir=${ISSUE12_RETAIN_DIR:-$HOME/.AGENTS-temp/AgentCore/issue12-codex-key}
evidence_dir=$HOME/.AGENTS-temp/AgentCore/issue12-codex-key-cleanup/$(date '+%Y%m%dT%H%M%S%z')

if [[ $profile != amit || $region != us-east-2 || -z $expected_account || -z $expected_caller_arn ]]; then
  echo 'NO-GO: cleanup requires the exact amit/us-east-2 account and caller gates.' >&2
  exit 2
fi
install -d -m 700 "$evidence_dir"
aws sts get-caller-identity --profile "$profile" --region "$region" >"$evidence_dir/identity.json"
[[ $(jq -er '.Account' "$evidence_dir/identity.json") == "$expected_account" ]] || { echo 'NO-GO: unexpected account.' >&2; exit 2; }
[[ $(jq -er '.Arn' "$evidence_dir/identity.json") == "$expected_caller_arn" ]] || { echo 'NO-GO: unexpected caller.' >&2; exit 2; }
aws iam list-service-specific-credentials --profile "$profile" --user-name "$user_name" \
  --service-name bedrock.amazonaws.com >"$evidence_dir/credentials.json"
while IFS= read -r credential_id; do
  [[ -n $credential_id ]] || continue
  aws iam delete-service-specific-credential --profile "$profile" --user-name "$user_name" \
    --service-specific-credential-id "$credential_id" >>"$evidence_dir/delete-credentials.stdout"
done < <(jq -r '.ServiceSpecificCredentials[].ServiceSpecificCredentialId' "$evidence_dir/credentials.json")
aws iam delete-user-policy --profile "$profile" --user-name "$user_name" --policy-name "$policy_name" >"$evidence_dir/delete-policy.stdout"
aws iam delete-user --profile "$profile" --user-name "$user_name" >"$evidence_dir/delete-user.stdout"
rm -f "$retained_dir/credential.json" "$retained_dir/metadata.json"
echo "PASS: Issue #12 Codex key resources deleted. Evidence: $evidence_dir"
