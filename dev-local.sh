#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
frontend_dir="$repo_dir/frontend"

command -v node >/dev/null 2>&1 || { echo "ERROR: Node.js is required." >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "ERROR: npm is required." >&2; exit 1; }

cd "$frontend_dir"
if [[ ! -d node_modules ]]; then
  npm ci
fi

echo "Starting the local Issue #4 simulation (preferred port: http://localhost:5173)"
echo "If port 5173 is busy, Vite will print the next available local port."
echo "No AWS calls or cloud resources are used."
export VITE_LOCAL_DEV=true
exec npm run dev
