#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail
umask 077

region=${AWS_REGION:-ap-southeast-1}
model=${CODEX_BEDROCK_MODEL:-openai.gpt-5.6-luna}
reasoning=${CODEX_REASONING_EFFORT:-low}
codex_bin=${CODEX_BIN:-codex}
fixture_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../fixtures/codex-smoke" && pwd)

cleanup() {
  unset AWS_BEARER_TOKEN_BEDROCK
}
trap cleanup EXIT INT TERM

if [[ ${1:-} == --check ]]; then
  command -v "$codex_bin" >/dev/null 2>&1 || { echo 'NO-GO: Codex CLI is not installed.' >&2; exit 2; }
  "$codex_bin" --version
  "$codex_bin" exec --help | grep -q -- '--ephemeral' || { echo 'NO-GO: installed Codex lacks ephemeral exec.' >&2; exit 2; }
  printf 'Ready: provider=amazon-bedrock model=%s reasoning=%s region=%s sandbox=read-only\n' "$model" "$reasoning" "$region"
  exit 0
fi
if (($# != 0)); then
  echo 'Usage: codex-bedrock-smoke.sh [--check]' >&2
  echo 'The Bedrock key is accepted only through hidden input.' >&2
  exit 2
fi
if [[ -z $region || ! $model =~ ^openai\.[A-Za-z0-9._-]+$ || $reasoning != low ]]; then
  echo 'NO-GO: set a Region, an explicit openai.* Bedrock model, and low reasoning.' >&2
  exit 2
fi
command -v "$codex_bin" >/dev/null 2>&1 || { echo 'NO-GO: Codex CLI is not installed.' >&2; exit 2; }

read -r -s -p 'Paste governed Bedrock key: ' AWS_BEARER_TOKEN_BEDROCK
printf '\n'
if [[ -z $AWS_BEARER_TOKEN_BEDROCK ]]; then
  echo 'NO-GO: no Bedrock key was supplied.' >&2
  exit 2
fi
export AWS_BEARER_TOKEN_BEDROCK AWS_REGION="$region"

printf '%s\n' 'Starting one read-only Codex smoke. No model or Region fallback is enabled.'
exec "$codex_bin" --ask-for-approval never exec --ephemeral --ignore-user-config --strict-config \
  --sandbox read-only -C "$fixture_dir" \
  -m "$model" -c 'model_provider="amazon-bedrock"' \
  -c "model_reasoning_effort=\"$reasoning\"" \
  -c "model_providers.amazon-bedrock.aws.region=\"$region\"" \
  'Read demo.py. In at most five lines, explain what the function does and identify one obvious edge case. Do not modify files or run commands.'
