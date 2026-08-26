#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail
umask 077

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
mode=${1:---full}
api_base=$(sed -n 's/^VITE_API_BASE_URL=//p' "$repo_dir/frontend/.env.local")
[[ $mode == '--full' || $mode == '--policy-only' ]] || { echo 'Usage: aws-api-e2e.sh [--full|--policy-only]' >&2; exit 2; }
[[ $api_base == https://* ]] || { echo 'ERROR: live API URL is missing' >&2; exit 1; }

evidence_root=${EVIDENCE_ROOT:-$HOME/.AGENTS-temp/AgentCore/aws-api-e2e}
run_id=$(date '+%Y%m%dT%H%M%S%z')
evidence_dir="$evidence_root/$run_id"
install -d -m 700 "$evidence_dir"
header_config=$(mktemp "$evidence_dir/curl-header.XXXXXX")
cleanup() { rm -f "$header_config"; }
trap cleanup EXIT INT TERM

key_response=$(curl --fail --silent --show-error --max-time 15 -X POST "${api_base}/key")
platform_key=$(jq -er '.apiKey | select(startswith("sk-demo-"))' <<<"$key_response")
printf 'header = "x-api-key: %s"\n' "$platform_key" >"$header_config"
jq -n --arg project demo-security-app '{keyCreated:true,keyStored:false,project:$project}' >"$evidence_dir/key-summary.json"

if [[ $mode == '--full' ]]; then
  curl --fail --silent --show-error --max-time 40 --config "$header_config" \
    -H 'content-type: application/json' -X POST "${api_base}/invoke" \
    --data '{"modelId":"apac.amazon.nova-lite-v1:0","prompt":"Explain why a public S3 bucket is a security risk and recommend remediation."}' \
    >"$evidence_dir/allowed.json"
  jq -e '.status == "Allowed" and .model == "Amazon Nova Lite" and .requestId != null and .inputTokens > 0 and .outputTokens > 0' \
    "$evidence_dir/allowed.json" >/dev/null
fi

denied_status=$(curl --silent --show-error --max-time 15 --config "$header_config" \
  -H 'content-type: application/json' -X POST "${api_base}/invoke" \
  --data '{"modelId":"model-premium","prompt":"test governed access"}' \
  -o "$evidence_dir/denied.json" -w '%{http_code}')
[[ $denied_status == 403 ]]
jq -e '.status == "Denied" and .message == "Not allowed for this project" and .requestId != null' \
  "$evidence_dir/denied.json" >/dev/null

curl --fail --silent --show-error --max-time 15 --config "$header_config" "${api_base}/logs" \
  >"$evidence_dir/logs.json"
jq -e '.items | any(.status == "Denied" and .modelId == "model-premium")' "$evidence_dir/logs.json" >/dev/null

jq -n --arg mode "$mode" '{status:"PASS",mode:$mode,keyCreatedAndNotSaved:true,deniedRecorded:true}' \
  >"$evidence_dir/result.json"
printf 'PASS: live platform API E2E (%s)\nEvidence: %s\n' "$mode" "$evidence_dir"
