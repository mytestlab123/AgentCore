#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
test_dir=$(mktemp -d)
trap 'rm -rf -- "$test_dir"' EXIT INT TERM
fake_codex="$repo_dir/tests/fixtures/fake-codex.sh"
capture="$test_dir/args"
output="$test_dir/output"

printf '%s\n' 'test-bedrock-key' | \
  CODEX_BIN="$fake_codex" CODEX_TEST_CAPTURE="$capture" \
  "$repo_dir/scripts/codex-bedrock-smoke.sh" >"$output"

rg -qx -- '--ephemeral' "$capture"
rg -qx -- 'read-only' "$capture"
rg -qx -- 'model_provider="amazon-bedrock"' "$capture"
rg -qx -- 'model_reasoning_effort="low"' "$capture"
if rg -q 'test-bedrock-key' "$output" "$capture"; then
  echo 'NO-GO: wrapper exposed the key.' >&2
  exit 1
fi
