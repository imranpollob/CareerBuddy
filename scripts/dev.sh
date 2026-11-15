#!/usr/bin/env bash
# Start the persistent LOCAL demo. Ctrl+C stops only processes this script owns.
set -euo pipefail
restart=true
case "${1:-}" in
  --restart) restart=true; shift ;;
  -h|--help)
    echo 'Usage: bash scripts/dev.sh [--restart]'
    echo 'Stops listeners on ports 8000 and 5173 before starting (default).'
    echo '  --restart  Explicit alias for the default behavior.'
    exit 0 ;;
esac
if [ "$#" -ne 0 ]; then
  echo 'Usage: bash scripts/dev.sh [--restart]' >&2
  exit 2
fi
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

.venv/bin/python - "$restart" <<'PY'
import os
import shutil
import signal
import socket
import subprocess
import sys
import time

ports = (8000, 5173)
if sys.argv[1] == 'true':
    if not shutil.which('lsof'):
        raise SystemExit('Restarting development servers requires lsof. Install it and try again.')

    def listeners():
        pids = set()
        for port in ports:
            result = subprocess.run(
                ['lsof', '-t', f'-iTCP:{port}', '-sTCP:LISTEN'],
                capture_output=True, text=True,
            )
            if result.returncode not in (0, 1) or result.stderr:
                raise SystemExit(f'Could not inspect port {port}: {result.stderr.strip()}')
            pids.update(int(pid) for pid in result.stdout.split())
        return pids

    pending = listeners()
    for sig, timeout in ((signal.SIGTERM, 5), (signal.SIGKILL, 2)):
        for pid in pending:
            print(f'Stopping PID {pid} with {sig.name} (development ports).', flush=True)
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
            except PermissionError:
                raise SystemExit(f'Permission denied stopping PID {pid}.')
        deadline = time.monotonic() + timeout
        while pending and time.monotonic() < deadline:
            time.sleep(0.1)
            pending &= listeners()
        if not pending:
            break
    if pending:
        raise SystemExit(f'Could not stop listeners: {sorted(pending)}')

for port in ports:
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',port)) == 0:
            raise SystemExit(f'Port {port} is still in use after stopping existing listeners.')
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
