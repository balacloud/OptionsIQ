#!/bin/bash
# OptionsIQ — Stop backend + frontend

ROOT="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$ROOT/.pids" ]; then
  PIDS=$(cat "$ROOT/.pids")
  for PID in $PIDS; do
    if kill -0 "$PID" 2>/dev/null; then
      kill "$PID" && echo "Stopped PID $PID"
    fi
  done
  rm "$ROOT/.pids"
fi

# Belt-and-suspenders: kill by port
lsof -ti:5051 | xargs kill -9 2>/dev/null && echo "Killed port 5051" || true
lsof -ti:3050 | xargs kill -9 2>/dev/null && echo "Killed port 3050" || true

echo "OptionsIQ stopped."
