#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
frontend_dir="$repo_dir/frontend"

[[ -s "$frontend_dir/.env.local" ]] || {
  echo 'ERROR: frontend/.env.local is missing. Run the approved deployment first.' >&2
  exit 1
}

cd "$frontend_dir"
[[ -d node_modules ]] || npm ci
echo 'Starting the live Issue #4 portal. Playground requests can incur Bedrock cost.'
export VITE_LOCAL_DEV=false
if [[ -n ${AGENTCORE_PORT:-} ]]; then
  [[ $AGENTCORE_PORT =~ ^[0-9]+$ ]] || {
    echo 'ERROR: AGENTCORE_PORT must be numeric.' >&2
    exit 2
  }
  exec npm run dev -- --port "$AGENTCORE_PORT"
fi
exec npm run dev
