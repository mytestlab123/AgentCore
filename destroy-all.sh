#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail
umask 077

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
profile=${AWS_PROFILE:-project1}
region=${AWS_REGION:-ap-southeast-1}
expected_account=${EXPECTED_AWS_ACCOUNT:-}
run_id=$(date '+%Y%m%dT%H%M%S%z')
evidence_dir=${EVIDENCE_DIR:-$HOME/.AGENTS-temp/AgentCore/aws-cleanup/$run_id}

if [[ ${1:-} != '--approve-destroy' || -z "$expected_account" ]]; then
  echo 'NO-GO: set EXPECTED_AWS_ACCOUNT and pass --approve-destroy.'
  exit 2
fi

for command_name in aws jq node npm; do
  command -v "$command_name" >/dev/null 2>&1 || { echo "ERROR: missing $command_name" >&2; exit 1; }
done

install -d -m 700 "$evidence_dir"
aws sts get-caller-identity --profile "$profile" --region "$region" \
  >"$evidence_dir/identity.json"
account=$(jq -r .Account "$evidence_dir/identity.json")
[[ $account == "$expected_account" ]] || { echo "NO-GO: unexpected account $account" >&2; exit 2; }

aws cloudformation describe-stacks --stack-name AgentCoreMvp \
  --profile "$profile" --region "$region" \
  >"$evidence_dir/stack-before.json"
aws cloudformation list-stack-resources --stack-name AgentCoreMvp \
  --profile "$profile" --region "$region" \
  >"$evidence_dir/resources-before.json"
target_api_url=$(jq -r '.Stacks[0].Outputs[]? | select(.OutputKey == "ApiUrl") | .OutputValue' \
  "$evidence_dir/stack-before.json")

npm ci --prefix "$repo_dir/cdk"
(
  cd "$repo_dir/cdk"
  npx cdk destroy AgentCoreMvp --profile "$profile" --force
)

if aws cloudformation describe-stacks --stack-name AgentCoreMvp \
  --profile "$profile" --region "$region" \
  >"$evidence_dir/stack-after.json" 2>"$evidence_dir/stack-after.stderr"; then
  echo 'ERROR: AgentCoreMvp still exists after cleanup.' >&2
  exit 1
fi

frontend_config_action=absent
if [[ -f "$repo_dir/frontend/.env.local" ]]; then
  configured_api_url=$(sed -n 's/^VITE_API_BASE_URL=//p' "$repo_dir/frontend/.env.local" | head -n 1)
  if [[ ${configured_api_url%/} == ${target_api_url%/} ]]; then
    rm -f "$repo_dir/frontend/.env.local"
    frontend_config_action=deleted
  else
    frontend_config_action=preserved-other-account
  fi
fi

jq -n \
  --arg timestamp "$(date --iso-8601=seconds)" \
  --arg profile "$profile" \
  --arg account "$account" \
  --arg region "$region" \
  --arg stack "AgentCoreMvp" \
  --arg frontend_config_action "$frontend_config_action" \
  '{timestamp:$timestamp,action:"deleted",profile:$profile,account:$account,region:$region,stack:$stack,frontend_config_action:$frontend_config_action,status:"PASS"}' \
  >"$evidence_dir/result.json"

echo 'PASS: AgentCoreMvp removed and absence verified.'
printf 'Frontend config: %s\nEvidence: %s\n' "$frontend_config_action" "$evidence_dir"
