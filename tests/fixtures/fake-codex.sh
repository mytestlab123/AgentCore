#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

if [[ ${1:-} == --version ]]; then
  echo 'codex-cli test'
  exit 0
fi
if [[ ${1:-} == exec && ${2:-} == --help ]]; then
  echo '--ephemeral'
  exit 0
fi
[[ ${AWS_BEARER_TOKEN_BEDROCK:-} == test-bedrock-key ]] || exit 3
printf '%s\n' "$@" >"$CODEX_TEST_CAPTURE"
