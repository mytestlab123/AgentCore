#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)

for script in "$repo_dir"/*.sh "$repo_dir"/scripts/*.sh; do
  /usr/bin/bash -n "$script"
done

AWS_PROFILE=profile-that-must-not-exist \
  "$repo_dir/scripts/bedrock-api-key-poc.sh" --plan >/dev/null
AWS_PROFILE=amit ISSUE12_REGION=us-east-2 \
  "$repo_dir/scripts/create-codex-bedrock-key.sh" --plan >/dev/null
"$repo_dir/scripts/codex-bedrock-smoke.sh" --check >/dev/null
"$repo_dir/scripts/test-codex-bedrock-smoke.sh"
if rg -n 'localStorage|sessionStorage|indexedDB' \
  "$repo_dir/frontend/src/issue9-api.ts" "$repo_dir/frontend/src/issue9-pages.tsx"; then
  echo 'NO-GO: credential UI must not use browser persistence.' >&2
  exit 1
fi

npm ci --prefix "$repo_dir/frontend"
npm audit --audit-level=high --prefix "$repo_dir/frontend"
npm run lint --prefix "$repo_dir/frontend"
npm run test --prefix "$repo_dir/frontend"
npm run build --prefix "$repo_dir/frontend"

npm ci --prefix "$repo_dir/cdk"
npm audit --audit-level=high --prefix "$repo_dir/cdk"
npm run build --prefix "$repo_dir/cdk"

PYTHONPATH="$repo_dir/api" python3 -m unittest discover -s "$repo_dir/api" -p 'test_*.py'
python3 -m compileall -q "$repo_dir/api"
git -C "$repo_dir" diff --check

echo "Local POC checks passed. No AWS calls were made."
