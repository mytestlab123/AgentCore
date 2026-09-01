#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
script=$repo_dir/scripts/harness-mvp.sh

/usr/bin/bash -n "$script"
plan=$(AWS_PROFILE=amit "$script" --plan)
rg -q 'Issue #17 AgentCore Harness MVP' <<<"$plan"
rg -q 'Tools: none' <<<"$plan"
rg -q 'Memory: disabled' <<<"$plan"
rg -q 'Lifecycle: always delete' <<<"$plan"

if AWS_PROFILE=amit "$script" --approve-run >/dev/null 2>&1; then
  echo 'ERROR: live mode must reject missing identity gates.' >&2
  exit 1
fi

echo 'Harness MVP offline checks passed. No AWS calls were made.'
