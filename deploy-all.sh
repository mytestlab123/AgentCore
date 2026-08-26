#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail
umask 077

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
profile=${AWS_PROFILE:-project1}
region=${AWS_REGION:-ap-southeast-1}
expected_account=${EXPECTED_AWS_ACCOUNT:-}
expected_caller_arn=${EXPECTED_AWS_CALLER_ARN:-}
ttl=${AGENTCORE_TTL:-$(date -d '+7 days' '+%d-%m-%y')}

if [[ ${1:-} != '--approve-deploy' ]]; then
  echo 'NO-GO: this creates a small billable AWS POC.'
  echo 'Rerun with --approve-deploy after reviewing the account, region, TTL, and cleanup.'
  exit 2
fi
if [[ -z "$expected_account" || -z "$expected_caller_arn" ]]; then
  echo 'NO-GO: set EXPECTED_AWS_ACCOUNT and EXPECTED_AWS_CALLER_ARN exactly.'
  exit 2
fi
if [[ ! $ttl =~ ^[0-9]{2}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo 'NO-GO: AGENTCORE_TTL must use DD-MM-YY.'
  exit 2
fi

for command_name in aws jq node npm; do
  command -v "$command_name" >/dev/null 2>&1 || { echo "ERROR: missing $command_name" >&2; exit 1; }
done

identity=$(aws sts get-caller-identity --profile "$profile" --region "$region" --output json)
account=$(jq -r .Account <<<"$identity")
arn=$(jq -r .Arn <<<"$identity")
[[ $account == "$expected_account" ]] || { echo "NO-GO: profile $profile resolved to unexpected account $account" >&2; exit 2; }
[[ $arn == "$expected_caller_arn" ]] || { echo "NO-GO: profile $profile resolved to unexpected caller $arn" >&2; exit 2; }

aws bedrock list-inference-profiles --profile "$profile" --region "$region" \
  --type-equals SYSTEM_DEFINED --output json |
  jq -e '.inferenceProfileSummaries[] | select(.inferenceProfileId == "apac.amazon.nova-lite-v1:0" and .status == "ACTIVE")' >/dev/null

run_id=$(date '+%Y%m%dT%H%M%S%z')
evidence_dir=${EVIDENCE_DIR:-$HOME/.AGENTS-temp/AgentCore/aws/$run_id}
install -d -m 700 "$evidence_dir"

npm ci --prefix "$repo_dir/cdk"
npm run build --prefix "$repo_dir/cdk"
(
  cd "$repo_dir/cdk"
  npx cdk deploy AgentCoreMvp \
    --profile "$profile" \
    --require-approval never \
    --outputs-file "$evidence_dir/outputs.json" \
    -c "ttl=$ttl" \
    -c "created=$(date '+%Y-%m-%d')"
)

api_url=$(jq -r '.AgentCoreMvp.ApiUrl' "$evidence_dir/outputs.json")
[[ $api_url == https://* ]] || { echo 'ERROR: deployment did not return an HTTPS API URL' >&2; exit 1; }
printf 'VITE_API_BASE_URL=%s\n' "${api_url%/}" >"$repo_dir/frontend/.env.local"
chmod 600 "$repo_dir/frontend/.env.local"

printf 'PASS: AgentCore Issue #4 MVP deployed\n'
printf 'Profile: %s\nRegion: %s\nTTL: %s\nAPI URL: %s\nEvidence: %s\n' \
  "$profile" "$region" "$ttl" "$api_url" "$evidence_dir"
printf 'Next: restart with ./dev-live.sh\n'
