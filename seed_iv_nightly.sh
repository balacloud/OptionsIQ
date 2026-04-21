#!/bin/bash
# Nightly IV seeding — call after market close (4:30pm ET recommended)
# Loops all 16 ETFs via IBWorker, stores daily IV into iv_store.db
# Cron setup: crontab -e
#   30 21 * * 1-5 /path/to/options-iq/seed_iv_nightly.sh >> /tmp/seed_iv.log 2>&1
#   (21:30 UTC = 4:30pm ET, weekdays only)

BACKEND_URL="http://localhost:5051"
LOG_PREFIX="[seed_iv_nightly $(date '+%Y-%m-%d %H:%M:%S')]"

echo "$LOG_PREFIX Starting IV seed for all ETFs..."

RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/admin/seed-iv/all" \
    -H "Content-Type: application/json" \
    --max-time 300)

if [ $? -ne 0 ]; then
    echo "$LOG_PREFIX ERROR: curl failed — is the backend running on port 5051?"
    exit 1
fi

TICKERS=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tickers_seeded',0))" 2>/dev/null)
ROWS=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_iv_rows',0))" 2>/dev/null)
ERRORS=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('errors',[])))" 2>/dev/null)

echo "$LOG_PREFIX Done — $TICKERS ETFs seeded, $ROWS IV rows stored, $ERRORS errors"

if [ "$ERRORS" -gt "0" ]; then
    echo "$LOG_PREFIX Errors:"
    echo "$RESPONSE" | python3 -c "import sys,json; [print('  ',e) for e in json.load(sys.stdin).get('errors',[])]"
fi
