#!/usr/bin/env bash
# Start the persistent LOCAL demo. Ctrl+C stops only processes this script owns.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .local
owned_pids=()
cleanup() {
  for pid in "${owned_pids[@]:-}"; do
    if [ -n "$pid" ]; then
      pkill -TERM -P "$pid" 2>/dev/null || true
      kill "$pid" 2>/dev/null || true
    fi
  done
}
trap cleanup EXIT
trap 'exit 130' INT TERM

.venv/bin/python - <<'PY'
import socket
for port in (8000,5173):
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',port)) == 0:
            raise SystemExit(f'Port {port} is already in use. Stop that development server first.')
PY

if ! .venv/bin/python - <<'PY'
import socket
with socket.socket() as s:
    raise SystemExit(s.connect_ex(('127.0.0.1',8001)))
PY
then
  bash scripts/start_dynamodb.sh > .local/dynamodb.log 2>&1 &
  owned_pids+=("$!")
  ready=false
  for attempt in $(seq 1 30); do
    if .venv/bin/python - <<'PY'
import socket
with socket.socket() as s:
    raise SystemExit(s.connect_ex(('127.0.0.1',8001)))
PY
    then ready=true; break; fi
    sleep 1
  done
  if [ "$ready" != true ]; then
    echo 'DynamoDB Local did not start. Check .local/dynamodb.log and Java 17+.'
    exit 1
  fi
fi

.venv/bin/python -m scripts.setup_local_db
SKILLPILOT_REPOSITORY=dynamodb-local SKILLPILOT_DYNAMODB_ENDPOINT=http://127.0.0.1:8001 \
  .venv/bin/uvicorn backend.api:app --host 127.0.0.1 --port 8000 &
owned_pids+=("$!")
npm run dev --prefix frontend &
owned_pids+=("$!")
echo 'SkillPilot: http://127.0.0.1:5173 · Ctrl+C stops this local demo.'
wait
