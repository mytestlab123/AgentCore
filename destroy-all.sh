#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
profile=${AWS_PROFILE:-project1}
region=${AWS_REGION:-ap-southeast-1}
expected_account=${EXPECTED_AWS_ACCOUNT:-}

if [[ ${1:-} != '--approve-destroy' || -z "$expected_account" ]]; then
  echo 'NO-GO: set EXPECTED_AWS_ACCOUNT and pass --approve-destroy.'
  exit 2
fi
account=$(aws sts get-caller-identity --profile "$profile" --region "$region" --query Account --output text)
[[ $account == "$expected_account" ]] || { echo "NO-GO: unexpected account $account" >&2; exit 2; }

npm ci --prefix "$repo_dir/cdk"
(
  cd "$repo_dir/cdk"
  npx cdk destroy AgentCoreMvp --profile "$profile" --force
)

if aws cloudformation describe-stacks --stack-name AgentCoreMvp --profile "$profile" --region "$region" >/dev/null 2>&1; then
  echo 'ERROR: AgentCoreMvp still exists after cleanup.' >&2
  exit 1
fi
rm -f "$repo_dir/frontend/.env.local"
echo 'PASS: AgentCoreMvp removed and live frontend config deleted.'
