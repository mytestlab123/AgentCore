#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

profile=${AWS_PROFILE:-project1}
region=${AWS_REGION:-ap-southeast-1}
expected_account=${EXPECTED_AWS_ACCOUNT:-}

if [[ ${1:-} != '--approve-reset' || -z "$expected_account" ]]; then
  echo 'NO-GO: set EXPECTED_AWS_ACCOUNT and pass --approve-reset.'
  exit 2
fi
account=$(aws sts get-caller-identity --profile "$profile" --region "$region" --query Account --output text)
[[ $account == "$expected_account" ]] || { echo "NO-GO: unexpected account $account" >&2; exit 2; }

aws dynamodb delete-item \
  --table-name agentcore-issue4-mvp \
  --key '{"pk":{"S":"KEY#demo-security-app"}}' \
  --profile "$profile" \
  --region "$region" \
  --return-values ALL_OLD \
  --output json >/dev/null

echo 'PASS: removed only the demo project key record; request logs were preserved.'
