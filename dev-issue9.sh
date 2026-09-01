#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
frontend_dir="$repo_dir/frontend"
mode=${1:-}
profile=${AWS_PROFILE:-amit}
region=${AWS_REGION:-ap-southeast-1}
frontend_port=${AGENTCORE_PORT:-3333}
api_port=${ISSUE9_API_PORT:-9019}
ttl=${ISSUE9_TTL:-}
credential_age_days=${ISSUE9_CREDENTIAL_AGE_DAYS:-}
backend_pid=''

if [[ $mode != --approve-live ]]; then
  echo 'Usage: dev-issue9.sh --approve-live' >&2
  echo 'Starts the loopback GUI; AWS calls begin only after the GUI proof button is pressed.' >&2
  exit 2
fi
if [[ $profile != amit || $region != ap-southeast-1 ]]; then
  echo 'NO-GO: Issue #9 GUI is fixed to profile amit in ap-southeast-1.' >&2
  exit 2
fi
if [[ -z ${EXPECTED_AWS_ACCOUNT:-} || -z ${EXPECTED_AWS_CALLER_ARN:-} ]]; then
  echo 'NO-GO: set EXPECTED_AWS_ACCOUNT and EXPECTED_AWS_CALLER_ARN.' >&2
  exit 2
fi
if [[ ! $ttl =~ ^[0-9]{2}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo 'NO-GO: set ISSUE9_TTL using DD-MM-YY for the retained demo.' >&2
  exit 2
fi
if [[ ! $credential_age_days =~ ^[0-9]+$ ]]; then
  echo 'NO-GO: set ISSUE9_CREDENTIAL_AGE_DAYS for the retained demo.' >&2
  exit 2
fi
if [[ ! $frontend_port =~ ^[0-9]+$ || ! $api_port =~ ^[0-9]+$ ]]; then
  echo 'NO-GO: frontend and API ports must be numeric.' >&2
  exit 2
fi

for command_name in curl node npm python3 rg ss; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "ERROR: missing command: $command_name" >&2
    exit 1
  }
done
[[ -r $HOME/.codex/port.md ]] || {
  echo 'ERROR: shared port protocol is missing.' >&2
  exit 1
}
for port in "$frontend_port" "$api_port"; do
  if ss -ltnH "sport = :$port" | rg -q .; then
    echo "NO-GO: port $port is already in use; do not stop another listener." >&2
    exit 2
  fi
done

cleanup() {
  if [[ $backend_pid =~ ^[0-9]+$ ]] && kill -0 "$backend_pid" 2>/dev/null; then
    kill -TERM "$backend_pid"
    wait "$backend_pid" || true
  fi
}
trap cleanup EXIT INT TERM

export AWS_PROFILE="$profile"
export AWS_REGION="$region"
export ISSUE9_API_PORT="$api_port"
export ISSUE9_RETAIN_DEMO=true
export ISSUE9_TTL="$ttl"
export ISSUE9_CREDENTIAL_AGE_DAYS="$credential_age_days"
python3 "$repo_dir/api/issue9_demo_server.py" &
backend_pid=$!

for ((attempt = 1; attempt <= 50; attempt++)); do
  if curl --fail --silent --max-time 1 "http://127.0.0.1:$api_port/health" >/dev/null; then
    break
  fi
  kill -0 "$backend_pid" 2>/dev/null || {
    echo 'ERROR: Issue #9 backend exited before becoming ready.' >&2
    exit 1
  }
  sleep 0.1
done
curl --fail --silent --max-time 2 "http://127.0.0.1:$api_port/health" >/dev/null || {
  echo 'ERROR: Issue #9 backend did not become ready.' >&2
  exit 1
}

cd "$frontend_dir"
[[ -d node_modules ]] || npm ci
export VITE_DEMO_VARIANT=issue9
export VITE_ISSUE9_API_BASE_URL="http://127.0.0.1:$api_port"
echo "Starting Issue #15 model comparison demo at http://127.0.0.1:$frontend_port"
echo 'The AWS profile remains server-side. Use the GUI button to start the bounded proof.'
npm run dev -- --host 127.0.0.1 --port "$frontend_port" --strictPort
