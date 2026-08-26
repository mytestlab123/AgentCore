#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail
umask 077

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
frontend_dir="$repo_dir/frontend"
app_url=${APP_URL:-}
chrome_pid=''
debug_port=''
profile_dir=''
cleanup_done=false

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

for command_name in curl jq node npm rg ss wslpath; do
  command -v "$command_name" >/dev/null 2>&1 || fail "missing command: $command_name"
done

[[ -n "$app_url" ]] || fail 'set APP_URL to the exact loopback URL printed by Vite'
if [[ $app_url =~ ^http://(localhost|127\.0\.0\.1):([0-9]+)(/.*)?$ ]]; then
  app_port=${BASH_REMATCH[2]}
else
  fail 'APP_URL must use http://localhost:PORT or http://127.0.0.1:PORT'
fi

[[ -r "$HOME/.codex/port.md" ]] || fail 'shared port protocol is missing'

listener=$(ss -ltnpH "sport = :$app_port" 2>/dev/null || true)
[[ -n "$listener" ]] || fail "no listener found on port $app_port"
app_pid=$(sed -nE 's/.*pid=([0-9]+).*/\1/p' <<<"$listener" | head -1)
[[ $app_pid =~ ^[0-9]+$ ]] || fail "could not resolve the listener PID for port $app_port"
app_cwd=$(readlink -f "/proc/$app_pid/cwd" 2>/dev/null || true)
[[ $app_cwd == "$repo_dir"* ]] || fail "port $app_port belongs to another repo: ${app_cwd:-unknown}"

evidence_root=${EVIDENCE_ROOT:-$HOME/.AGENTS-temp/AgentCore/browser-e2e}
run_id=$(date '+%Y%m%dT%H%M%S%z')
evidence_dir="$evidence_root/$run_id"
install -d -m 700 "$evidence_dir"

printf '%s\n' "$listener" >"$evidence_dir/app-listener.txt"
ps -o pid,ppid,lstart,cmd -p "$app_pid" >"$evidence_dir/app-process.txt"
printf '%s\n' "$app_cwd" >"$evidence_dir/app-cwd.txt"
curl --fail --silent --show-error --max-time 10 \
  -D "$evidence_dir/readiness.headers" \
  "$app_url" \
  -o "$evidence_dir/readiness.html"

chrome_bin=${CHROME_WSL:-}
if [[ -z "$chrome_bin" ]]; then
  for candidate in \
    '/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' \
    '/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe'; do
    if [[ -x "$candidate" ]]; then
      chrome_bin=$candidate
      break
    fi
  done
fi
[[ -x "$chrome_bin" ]] || fail 'Windows Chrome was not found; set CHROME_WSL'

powershell_bin='/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
[[ -x "$powershell_bin" ]] || fail 'Windows PowerShell was not found'
windows_node='/mnt/c/Program Files/nodejs/node.exe'
[[ -x "$windows_node" ]] || fail 'Windows Node.js was not found'
windows_helper="$repo_dir/scripts/browser-e2e-windows.ps1"
[[ -r "$windows_helper" ]] || fail 'Windows browser helper was not found'
windows_temp_native=$(
  "$powershell_bin" -NoProfile -NonInteractive \
    -Command '[System.IO.Path]::GetTempPath()' | tr -d '\r\n'
)
windows_user_native=$(
  "$powershell_bin" -NoProfile -NonInteractive \
    -Command '$env:USERPROFILE' | tr -d '\r\n'
)
windows_temp_wsl=$(wslpath -u "$windows_temp_native")
windows_user_wsl=$(wslpath -u "$windows_user_native")
profile_dir=$(mktemp -d "$windows_temp_wsl/agentcore-e2e.XXXXXX")
profile_windows=$(wslpath -w "$profile_dir")

cleanup() {
  local cleanup_json cleanup_status helper_windows

  if [[ $cleanup_done == true ]]; then
    return
  fi
  cleanup_done=true

  if [[ -z "$profile_dir" ]]; then
    jq -n '{chrome_stopped:true, profile_removed:true, debug_port_released:true, debug_port:""}' \
      >"$evidence_dir/cleanup.json"
    return
  fi

  case "$profile_dir" in
    "$windows_temp_wsl"/agentcore-e2e.*) ;;
    *)
      jq -n --arg path "$profile_dir" \
        '{chrome_stopped:false, profile_removed:false, debug_port_released:false, error:("unexpected profile path: " + $path)}' \
        >"$evidence_dir/cleanup.json"
      return
      ;;
  esac

  helper_windows=$(wslpath -w "$windows_helper")
  set +o errexit
  cleanup_json=$(
    "$powershell_bin" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$helper_windows" \
      -Action Cleanup \
      -ProfilePath "$profile_windows" \
      -DebugPort "$debug_port" 2>"$evidence_dir/cleanup.stderr" | tr -d '\r'
  )
  cleanup_status=$?
  if [[ $cleanup_status -eq 0 ]] && \
    jq -e '.chrome_stopped and .profile_removed and .debug_port_released' \
      >/dev/null 2>&1 <<<"$cleanup_json"; then
    :
  else
    sleep 2
    cleanup_json=$(
      "$powershell_bin" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$helper_windows" \
        -Action Cleanup \
        -ProfilePath "$profile_windows" \
        -DebugPort "$debug_port" 2>>"$evidence_dir/cleanup.stderr" | tr -d '\r'
    )
    cleanup_status=$?
  fi
  set -o errexit

  if [[ $cleanup_status -eq 0 ]] && jq -e . >/dev/null 2>&1 <<<"$cleanup_json"; then
    printf '%s\n' "$cleanup_json" | jq . >"$evidence_dir/cleanup.json"
  else
    jq -n --arg error "Windows cleanup helper failed with status $cleanup_status" \
      '{chrome_stopped:false, profile_removed:false, debug_port_released:false, error:$error}' \
      >"$evidence_dir/cleanup.json"
  fi

  if [[ -n "$chrome_pid" ]] && kill -0 "$chrome_pid" 2>/dev/null; then
    kill "$chrome_pid" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

"$chrome_bin" \
  --headless=new \
  --disable-gpu \
  --disable-background-networking \
  --disable-component-update \
  --hide-scrollbars \
  --no-first-run \
  --no-default-browser-check \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=0 \
  "--user-data-dir=$profile_windows" \
  --window-size=1920,1080 \
  about:blank \
  >"$evidence_dir/chrome.log" 2>&1 &
chrome_pid=$!

devtools_file="$profile_dir/DevToolsActivePort"
for ((attempt = 1; attempt <= 100; attempt++)); do
  [[ -s "$devtools_file" ]] && break
  kill -0 "$chrome_pid" 2>/dev/null || fail 'Windows Chrome exited before becoming ready'
  sleep 0.1
done
[[ -s "$devtools_file" ]] || fail 'Chrome DevTools endpoint was not ready in time'
debug_port=$(sed -n '1p' "$devtools_file" | tr -d '\r')
[[ $debug_port =~ ^[0-9]+$ ]] || fail 'Chrome reported an invalid debugging port'
cdp_url="http://127.0.0.1:$debug_port"
printf '%s\n' "$debug_port" >"$evidence_dir/debug-port.txt"

cdp_version_windows=$(wslpath -w "$evidence_dir/chrome-version.json")
helper_windows=$(wslpath -w "$windows_helper")
"$powershell_bin" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$helper_windows" \
  -Action GetVersion \
  -CdpUrl "$cdp_url/json/version" \
  -OutputPath "$cdp_version_windows"
[[ -s "$evidence_dir/chrome-version.json" ]] || fail 'Windows could not reach the Chrome DevTools endpoint'

script_windows=$(wslpath -w "$frontend_dir/e2e/browser-e2e.mjs")
evidence_windows=$(wslpath -w "$evidence_dir")
expected_api_base_url=${EXPECTED_API_BASE_URL:-}
"$windows_node" "$script_windows" "$app_url" "$cdp_url" "$evidence_windows" "$expected_api_base_url"

cleanup
trap - EXIT INT TERM

jq -e '.status == "PASS" and .routesChecked == 3 and .keyCreatedThenMasked and .externalRequests == 0 and .consoleErrors == 0' \
  "$evidence_dir/result.json" >/dev/null
jq -e '.chrome_stopped and .profile_removed and .debug_port_released' \
  "$evidence_dir/cleanup.json" >/dev/null
test -s "$evidence_dir/playground-allowed.png"
test -s "$evidence_dir/playground-denied.png"
test -s "$evidence_dir/logs-allowed-denied.png"

review_dir=${REVIEW_DIR:-$windows_user_wsl/Downloads/output/AgentCore}
install -d "$review_dir"
install -m 644 "$evidence_dir/playground-allowed.png" "$review_dir/playground-allowed.png"
install -m 644 "$evidence_dir/playground-denied.png" "$review_dir/playground-denied.png"
install -m 644 "$evidence_dir/logs-allowed-denied.png" "$review_dir/logs-allowed-denied.png"
install -m 644 "$evidence_dir/result.json" "$review_dir/browser-e2e-result.json"

printf 'PASS: AgentCore browser E2E\n'
printf 'Evidence: %s\n' "$evidence_dir"
printf 'Review: %s\n' "$review_dir"
