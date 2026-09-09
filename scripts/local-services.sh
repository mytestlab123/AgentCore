#!/usr/bin/env bash
# Start and stop the small loopback-only AgentCore demo set after a reboot.
# It owns only the PIDs it starts and never starts or controls remote LibreChat.

set -o errexit -o nounset -o pipefail
umask 077

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
frontend_dir="$repo_dir/frontend"
state_dir=${AGENTCORE_LOCAL_STATE_DIR:-"$HOME/.AGENTS-temp/AgentCore/local-services"}
log_dir="$state_dir/logs"

portal_port=3333
api_port=9019
gateway_port=3334

mode=${1:-}

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/local-services.sh --start
  ./scripts/local-services.sh --start-gateway-visual
  ./scripts/local-services.sh --status
  ./scripts/local-services.sh --stop

--start starts the complete local demo set:
  http://localhost:3333/  Issue 9/15 portal
  http://localhost:9019/  portal API
  http://localhost:3334/  retained Gateway visual proof

--start requires the existing Issue 9 runtime identity/TTL environment gates.
--start-gateway-visual starts only the model-free Gateway visual proof for
local troubleshooting; it never runs a Gateway action until a browser button
is pressed.
USAGE
}

die() {
  echo "NO-GO: $*" >&2
  exit 2
}

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERROR: missing command: $1" >&2
    exit 1
  }
}

pid_file() {
  printf '%s/%s.pid\n' "$state_dir" "$1"
}

read_pid() {
  local file
  file=$(pid_file "$1")
  [[ -r "$file" ]] || return 1
  local value
  value=$(<"$file")
  [[ "$value" =~ ^[0-9]+$ ]] || return 1
  printf '%s\n' "$value"
}

pid_owned_by_repo() {
  local pid=$1 cwd
  kill -0 "$pid" 2>/dev/null || return 1
  cwd=$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)
  [[ "$cwd" == "$repo_dir" || "$cwd" == "$repo_dir"/* ]]
}

listener_pid() {
  local port=$1 listener
  listener=$(ss -ltnpH "sport = :$port" 2>/dev/null || true)
  sed -nE 's/.*pid=([0-9]+).*/\1/p' <<<"$listener" | head -n 1
}

remove_stale_pid_file() {
  local name=$1 file pid
  file=$(pid_file "$name")
  [[ -e "$file" ]] || return 0
  pid=$(read_pid "$name" || true)
  if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
    rm -f -- "$file"
  fi
}

require_free_port() {
  local port=$1 owner
  owner=$(listener_pid "$port")
  [[ -z "$owner" ]] || die "port $port is already in use; do not stop another listener"
}

wait_for_http() {
  local url=$1 pid=$2 label=$3
  local attempt
  for attempt in $(seq 1 50); do
    if curl --fail --silent --max-time 1 "$url" >/dev/null; then
      return 0
    fi
    kill -0 "$pid" 2>/dev/null || die "$label exited before becoming ready; inspect $log_dir"
    sleep 0.2
  done
  die "$label did not become ready; inspect $log_dir"
}

write_pid() {
  printf '%s\n' "$2" >"$(pid_file "$1")"
}

stop_owned() {
  local name=$1 port=$2 file pid live_listener
  file=$(pid_file "$name")
  [[ -e "$file" ]] || return 0
  pid=$(read_pid "$name" || true)
  if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
    rm -f -- "$file"
    return 0
  fi
  pid_owned_by_repo "$pid" || die "refusing to stop $name: tracked PID is not owned by $repo_dir"
  live_listener=$(listener_pid "$port")
  if [[ -n "$live_listener" && "$live_listener" != "$pid" ]]; then
    die "refusing to stop $name: port $port belongs to untracked PID $live_listener"
  fi
  kill -TERM "$pid"
  local attempt
  for attempt in $(seq 1 30); do
    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f -- "$file"
      return 0
    fi
    sleep 0.2
  done
  die "$name did not stop cleanly"
}

rollback_start() {
  set +o errexit
  stop_owned gateway-visual "$gateway_port"
  stop_owned portal "$portal_port"
  stop_owned api "$api_port"
}

require_issue9_runtime_gates() {
  local name
  for name in EXPECTED_AWS_ACCOUNT EXPECTED_AWS_CALLER_ARN ISSUE9_TTL ISSUE9_CREDENTIAL_AGE_DAYS; do
    [[ -n ${!name:-} ]] || die "set $name before --start; no service was started"
  done
  [[ ${AWS_PROFILE:-amit} == amit && ${AWS_REGION:-ap-southeast-1} == ap-southeast-1 ]] || \
    die '--start is fixed to AWS_PROFILE=amit and AWS_REGION=ap-southeast-1'
}

start_api() {
  (
    cd "$repo_dir"
    export AWS_PROFILE=${AWS_PROFILE:-amit}
    export AWS_REGION=${AWS_REGION:-ap-southeast-1}
    export ISSUE9_API_PORT="$api_port"
    export ISSUE9_RETAIN_DEMO=true
    exec setsid /usr/bin/python3 "$repo_dir/api/issue9_demo_server.py"
  ) </dev/null >"$log_dir/api.log" 2>&1 &
  local pid=$!
  write_pid api "$pid"
  wait_for_http "http://localhost:$api_port/health" "$pid" API
}

start_portal() {
  [[ -x "$frontend_dir/node_modules/.bin/vite" ]] || die 'frontend dependencies are absent; run ./scripts/check.sh first'
  (
    cd "$frontend_dir"
    export VITE_DEMO_VARIANT=issue9
    export VITE_ISSUE9_API_BASE_URL="http://localhost:$api_port"
    exec setsid "$frontend_dir/node_modules/.bin/vite" --host 127.0.0.1 --port "$portal_port" --strictPort
  ) </dev/null >"$log_dir/portal.log" 2>&1 &
  local pid=$!
  write_pid portal "$pid"
  wait_for_http "http://localhost:$portal_port/" "$pid" portal
}

start_gateway_visual() {
  (
    cd "$repo_dir"
    exec setsid /usr/bin/python3 "$repo_dir/scripts/gateway_visual_demo.py" --serve
  ) </dev/null >"$log_dir/gateway-visual.log" 2>&1 &
  local pid=$!
  write_pid gateway-visual "$pid"
  wait_for_http "http://localhost:$gateway_port/" "$pid" Gateway-visual
}

status_one() {
  local name=$1 port=$2 url=$3 pid listener
  pid=$(read_pid "$name" || true)
  listener=$(listener_pid "$port")
  if [[ -z "$pid" ]]; then
    if [[ -n "$listener" ]]; then
      printf '%s=UNTRACKED_LISTENER port=%s pid=%s\n' "$name" "$port" "$listener"
    else
      printf '%s=STOPPED\n' "$name"
    fi
    return 1
  fi
  if ! pid_owned_by_repo "$pid"; then
    printf '%s=STALE_OR_UNOWNED pid=%s\n' "$name" "$pid"
    return 1
  fi
  if [[ "$listener" != "$pid" ]]; then
    printf '%s=LISTENER_MISMATCH expected_pid=%s observed_pid=%s\n' "$name" "$pid" "${listener:-none}"
    return 1
  fi
  if ! curl --fail --silent --max-time 2 "$url" >/dev/null; then
    printf '%s=UNHEALTHY pid=%s\n' "$name" "$pid"
    return 1
  fi
  printf '%s=READY url=%s\n' "$name" "$url"
}

for command_name in curl ss sed head readlink kill python3 setsid; do
  need "$command_name"
done
install -d -m 700 "$state_dir" "$log_dir"

case "$mode" in
  --start)
    require_issue9_runtime_gates
    for name in api portal gateway-visual; do remove_stale_pid_file "$name"; done
    for port in "$api_port" "$portal_port" "$gateway_port"; do require_free_port "$port"; done
    trap rollback_start ERR INT TERM
    start_api
    start_portal
    start_gateway_visual
    trap - ERR INT TERM
    echo 'LOCAL_SERVICES=READY'
    echo "PORTAL_URL=http://localhost:$portal_port/"
    echo "API_URL=http://localhost:$api_port/"
    echo "GATEWAY_VISUAL_URL=http://localhost:$gateway_port/"
    ;;
  --start-gateway-visual)
    remove_stale_pid_file gateway-visual
    require_free_port "$gateway_port"
    start_gateway_visual
    echo 'GATEWAY_VISUAL=READY'
    echo "GATEWAY_VISUAL_URL=http://localhost:$gateway_port/"
    ;;
  --status)
    set +o errexit
    result=0
    status_one api "$api_port" "http://localhost:$api_port/health" || result=1
    status_one portal "$portal_port" "http://localhost:$portal_port/" || result=1
    status_one gateway-visual "$gateway_port" "http://localhost:$gateway_port/" || result=1
    exit "$result"
    ;;
  --stop)
    stop_owned gateway-visual "$gateway_port"
    stop_owned portal "$portal_port"
    stop_owned api "$api_port"
    echo 'LOCAL_SERVICES=STOPPED'
    ;;
  -h|--help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
