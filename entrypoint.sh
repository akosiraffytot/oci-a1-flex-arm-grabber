#!/usr/bin/env bash
set -uo pipefail

export STATUS_FILE="${STATUS_FILE:-/data/status}"
export LOG_FILE="${LOG_FILE:-/data/catcher.log}"

mkdir -p /data
printf 'running\n' > "$STATUS_FILE"

bash /app/oci-arm-catcher.sh 2>&1 | tee -a "$LOG_FILE" &
catcher_pid=$!

term() {
    kill "$catcher_pid" 2>/dev/null || true
    exit 143
}
trap term TERM INT

# Web server runs in the foreground; when it exits (crash or stop),
# the catcher is killed too. restart:unless-stopped brings both back.
python3 /app/web/server.py &
server_pid=$!
wait "$server_pid"
kill "$catcher_pid" 2>/dev/null || true
