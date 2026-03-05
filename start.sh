#!/bin/bash
# OptionsIQ — Start backend + frontend
# Backend: http://localhost:5051
# Frontend: http://localhost:3050
# Requires: IB Gateway or TWS running on 127.0.0.1:4001

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Check .env exists
if [ ! -f "$ROOT/.env" ]; then
  echo "ERROR: .env not found. Copy .env.example to .env and fill in ACCOUNT_SIZE."
  exit 1
fi

# Start backend
echo "Starting OptionsIQ backend on port 5051..."
cd "$ROOT/backend"
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q -r requirements.txt
nohup python app.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Start frontend
echo "Starting OptionsIQ frontend on port 3050..."
cd "$ROOT/frontend"
npm install --silent
PORT=3050 npm start &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "OptionsIQ running:"
echo "  Backend:  http://localhost:5051"
echo "  Frontend: http://localhost:3050"
echo ""
echo "PIDs saved to $ROOT/.pids"
echo "$BACKEND_PID $FRONTEND_PID" > "$ROOT/.pids"
