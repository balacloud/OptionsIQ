#!/bin/bash
# OptionsIQ — Graceful stop
# Sends SIGTERM first (allows ib_insync to disconnect cleanly), then SIGKILL if needed.

ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDS_FILE="$ROOT/.pids"

_stop_pid() {
  local pid=$1
  if kill -0 "$pid" 2>/dev/null; then
    kill -TERM "$pid" 2>/dev/null
    local i=0
    while kill -0 "$pid" 2>/dev/null && [ $i -lt 10 ]; do
      sleep 0.5; i=$((i+1))
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null && echo "  Force-killed PID $pid"
    else
      echo "  Stopped PID $pid"
    fi
  fi
}

if [ -f "$PIDS_FILE" ]; then
  for PID in $(cat "$PIDS_FILE"); do
    _stop_pid "$PID"
  done
  rm -f "$PIDS_FILE"
fi

# Belt-and-suspenders: kill any process still LISTENING on our ports.
# Use -sTCP:LISTEN to avoid killing browser connections (Chrome holds the port open
# as a client when connected to the webpack dev server).
for PORT in 5051 3050; do
  PIDS=$(lsof -ti "TCP:$PORT" -sTCP:LISTEN 2>/dev/null)
  if [ -n "$PIDS" ]; then
    for PID in $PIDS; do
      _stop_pid "$PID"
    done
    echo "  Cleared port $PORT"
  fi
done

echo "OptionsIQ stopped."
