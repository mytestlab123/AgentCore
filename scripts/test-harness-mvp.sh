#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
script=$repo_dir/scripts/harness-mvp.sh
inline_tool=$repo_dir/scripts/harness_inline_tool.py

/usr/bin/bash -n "$script"
plan=$(AWS_PROFILE=amit "$script" --plan)
rg -q 'Issue #19 AgentCore Harness MVP' <<<"$plan"
rg -q 'Tools: none' <<<"$plan"
rg -q 'Memory: disabled' <<<"$plan"
rg -q 'Lifecycle: always delete' <<<"$plan"
python3 "$inline_tool" --self-test | rg -q 'HARNESS_INLINE_TOOL_OFFLINE_PASS'
PYTHONPATH="$repo_dir/scripts" python3 "$repo_dir/scripts/test_harness_inline_tool.py"

if AWS_PROFILE=amit "$script" --approve-run >/dev/null 2>&1; then
  echo 'ERROR: live mode must reject missing identity gates.' >&2
  exit 1
fi

echo 'Harness MVP offline checks passed. No AWS calls were made.'
