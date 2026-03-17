#!/bin/bash
# OptionsIQ — Start backend + frontend
# Backend: http://localhost:5051
# Frontend: http://localhost:3050
# Requires: IB Gateway or TWS running on 127.0.0.1:4001

ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Pre-flight checks ─────────────────────────────────────────────────────────

if [ ! -f "$ROOT/backend/.env" ]; then
  echo "ERROR: backend/.env not found. Copy .env.example to backend/.env and fill in ACCOUNT_SIZE."
  exit 1
fi

# ── Stop any existing processes cleanly first ─────────────────────────────────
# This prevents "port already in use" and IB client ID conflicts.
echo "Stopping any running OptionsIQ processes..."
"$ROOT/stop.sh" 2>/dev/null || true

# Give IB Gateway time to release held client IDs after a graceful disconnect.
# (Hard kills leave the connection in IB Gateway for ~30s; graceful exits clear it immediately.)
sleep 2

# ── Confirm ports are free ────────────────────────────────────────────────────
for PORT in 5051 3050; do
  if lsof -ti ":$PORT" >/dev/null 2>&1; then
    echo "ERROR: Port $PORT is still in use after stop. Check for orphaned processes."
    lsof -ti ":$PORT" | xargs ps -p 2>/dev/null || true
    exit 1
  fi
done

# ── IB Gateway reachability check ─────────────────────────────────────────────
if nc -z -w3 127.0.0.1 4001 2>/dev/null; then
  echo "IB Gateway detected on 127.0.0.1:4001 — live data will be available."
else
  echo "WARNING: IB Gateway not reachable on 127.0.0.1:4001 — will run in mock/yfinance mode."
fi

# ── Start backend ─────────────────────────────────────────────────────────────
echo "Starting OptionsIQ backend on port 5051..."
cd "$ROOT/backend"
if [ ! -d "venv" ]; then
  echo "Creating Python venv..."
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

# Rotate log to keep last run's log accessible as backend.log.prev
if [ -f "$ROOT/backend/backend.log" ]; then
  mv "$ROOT/backend/backend.log" "$ROOT/backend/backend.log.prev"
fi

nohup python3 app.py > "$ROOT/backend/backend.log" 2>&1 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# Wait for backend to become healthy (up to 15s)
echo -n "  Waiting for backend..."
READY=0
for i in $(seq 1 15); do
  sleep 1
  STATUS=$(curl -s http://localhost:5051/api/health 2>/dev/null)
  if echo "$STATUS" | grep -q '"status":"ok"'; then
    IBKR=$(echo "$STATUS" | python3 -c "import json,sys; d=json.load(sys.stdin); print('IBKR:' + ('connected' if d['ibkr_connected'] else 'mock'))" 2>/dev/null)
    echo " ready ($IBKR)"
    READY=1
    break
  fi
  echo -n "."
done
if [ $READY -eq 0 ]; then
  echo " TIMEOUT — check backend/backend.log"
fi

# ── Start frontend ────────────────────────────────────────────────────────────
echo "Starting OptionsIQ frontend on port 3050..."
cd "$ROOT/frontend"
npm install --silent
PORT=3050 npm start &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"

# ── Save PIDs ─────────────────────────────────────────────────────────────────
echo "$BACKEND_PID $FRONTEND_PID" > "$ROOT/.pids"

echo ""
echo "OptionsIQ running:"
echo "  Backend:  http://localhost:5051/api/health"
echo "  Frontend: http://localhost:3050"
echo "  Logs:     $ROOT/backend/backend.log"
echo ""
echo "To stop: ./stop.sh"
