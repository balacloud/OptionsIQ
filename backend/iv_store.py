from __future__ import annotations

import math
import sqlite3
from pathlib import Path
from typing import Iterable

import numpy as np


class IVStore:
    def __init__(self, db_path: str | None = None) -> None:
        base = Path(__file__).resolve().parent
        self.db_path = Path(db_path) if db_path else base / "data" / "iv_history.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS iv_history (
                  ticker TEXT NOT NULL,
                  date TEXT NOT NULL,
                  iv REAL NOT NULL,
                  source TEXT NOT NULL DEFAULT 'ibkr',
                  PRIMARY KEY (ticker, date)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ohlcv_daily (
                  ticker TEXT NOT NULL,
                  date TEXT NOT NULL,
                  open REAL,
                  high REAL,
                  low REAL,
                  close REAL,
                  volume INTEGER,
                  PRIMARY KEY (ticker, date)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_trades (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ticker TEXT NOT NULL,
                  direction TEXT NOT NULL,
                  strategy_rank INTEGER NOT NULL,
                  strike REAL NOT NULL,
                  expiry TEXT NOT NULL,
                  premium REAL NOT NULL,
                  lots REAL NOT NULL,
                  account_size REAL NOT NULL,
                  entry_price REAL,
                  mark_price REAL,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Migrate existing databases
            existing = {row[1] for row in conn.execute("PRAGMA table_info(paper_trades)").fetchall()}
            if "entry_price" not in existing:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN entry_price REAL")
            if "mark_price" not in existing:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN mark_price REAL")
            if "verdict" not in existing:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN verdict TEXT")

    def store_iv(self, ticker: str, date: str, iv: float, source: str = "ibkr") -> None:
        ticker = ticker.upper().strip()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO iv_history (ticker, date, iv, source)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(ticker, date)
                DO UPDATE SET iv=excluded.iv, source=excluded.source
                """,
                (ticker, date, float(iv), source),
            )

    def get_iv_history(self, ticker: str, days: int = 252) -> list[dict]:
        ticker = ticker.upper().strip()
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT date, iv
                FROM iv_history
                WHERE ticker = ?
                ORDER BY date DESC
                LIMIT ?
                """,
                (ticker, int(days)),
            ).fetchall()
        ordered = list(reversed(rows))
        return [{"date": row["date"], "iv": float(row["iv"])} for row in ordered]

    def get_iv_stats(self, ticker: str) -> dict:
        """Row count + date range for data provenance. Returns nulls if empty."""
        ticker = ticker.upper().strip()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as rows, MIN(date) as first_date, MAX(date) as last_date "
                "FROM iv_history WHERE ticker = ?",
                (ticker,),
            ).fetchone()
        rows = int(row["rows"]) if row else 0
        return {
            "rows": rows,
            "first_date": row["first_date"] if rows > 0 else None,
            "last_date": row["last_date"] if rows > 0 else None,
            "status": "ok" if rows >= 30 else ("sparse" if rows > 0 else "empty"),
        }

    def get_ohlcv_stats(self, ticker: str) -> dict:
        """Row count for OHLCV data used in HV computation."""
        ticker = ticker.upper().strip()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as rows, MIN(date) as first_date, MAX(date) as last_date "
                "FROM ohlcv_daily WHERE ticker = ?",
                (ticker,),
            ).fetchone()
        rows = int(row["rows"]) if row else 0
        return {
            "rows": rows,
            "first_date": row["first_date"] if rows > 0 else None,
            "last_date": row["last_date"] if rows > 0 else None,
        }

    def compute_ivr_pct(self, ticker: str, current_iv: float) -> float | None:
        history = self.get_iv_history(ticker, 252)
        if len(history) < 30:
            return None
        vals = np.array([float(x["iv"]) for x in history], dtype=float)
        if vals.size == 0:
            return None
        pct = float((np.sum(vals <= float(current_iv)) / vals.size) * 100.0)
        return round(pct, 2)

    def store_ohlcv(self, ticker: str, bars: Iterable[dict]) -> None:
        ticker = ticker.upper().strip()
        rows = []
        for bar in bars:
            rows.append(
                (
                    ticker,
                    bar["date"],
                    float(bar["open"]),
                    float(bar["high"]),
                    float(bar["low"]),
                    float(bar["close"]),
                    int(bar.get("volume", 0)),
                )
            )
        if not rows:
            return
        with self._conn() as conn:
            conn.executemany(
                """
                INSERT INTO ohlcv_daily (ticker, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker, date)
                DO UPDATE SET
                  open=excluded.open,
                  high=excluded.high,
                  low=excluded.low,
                  close=excluded.close,
                  volume=excluded.volume
                """,
                rows,
            )

    def compute_hv(self, ticker: str, days: int = 20) -> float | None:
        ticker = ticker.upper().strip()
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT close
                FROM ohlcv_daily
                WHERE ticker = ?
                ORDER BY date DESC
                LIMIT ?
                """,
                (ticker, int(days) + 1),
            ).fetchall()

        closes_desc = [float(r["close"]) for r in rows]
        if len(closes_desc) < int(days) + 1:
            return None
        closes = list(reversed(closes_desc))

        returns = []
        for i in range(1, len(closes)):
            prev = closes[i - 1]
            curr = closes[i]
            if prev <= 0 or curr <= 0:
                continue
            returns.append(math.log(curr / prev))

        if len(returns) < 2:
            return None

        hv = float(np.std(np.array(returns), ddof=1) * math.sqrt(252) * 100)
        return round(hv, 2)

    def compute_max_21d_move(self, ticker: str) -> dict:
        """
        McMillan Stress Check: worst 21-day drawdown and best 21-day rally
        in available OHLCV history. Returns percentages as decimals (e.g. 0.08 = 8%).
        Uses rolling window over all available bars (may be < 252 if history is short).
        """
        ticker = ticker.upper().strip()
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT close FROM ohlcv_daily WHERE ticker = ? ORDER BY date ASC",
                (ticker,),
            ).fetchall()
        closes = [float(r["close"]) for r in rows if r["close"] and float(r["close"]) > 0]
        n = len(closes)
        if n < 22:
            return {"max_drawdown_pct": None, "max_rally_pct": None, "bars_available": n}
        worst_dd = 0.0
        best_rally = 0.0
        for i in range(n - 21):
            start = closes[i]
            window = closes[i : i + 22]
            low = min(window)
            high = max(window)
            dd = (start - low) / start  # fraction dropped
            rally = (high - start) / start  # fraction rallied
            worst_dd = max(worst_dd, dd)
            best_rally = max(best_rally, rally)
        return {
            "max_drawdown_pct": round(worst_dd, 4),
            "max_rally_pct": round(best_rally, 4),
            "bars_available": n,
        }

    def save_paper_trade(self, trade: dict) -> int:
        entry_price = trade.get("entry_price") or trade.get("premium")
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO paper_trades
                (ticker, direction, strategy_rank, strike, expiry, premium,
                 lots, account_size, entry_price, mark_price, verdict)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade["ticker"].upper().strip(),
                    trade["direction"],
                    int(trade["strategy_rank"]),
                    float(trade["strike"]),
                    str(trade["expiry"]),
                    float(trade["premium"]),
                    float(trade["lots"]),
                    float(trade["account_size"]),
                    float(entry_price) if entry_price is not None else None,
                    float(trade["mark_price"]) if trade.get("mark_price") is not None else None,
                    trade.get("verdict"),
                ),
            )
            return int(cur.lastrowid)

    def list_paper_trades(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT id, ticker, direction, strategy_rank, strike, expiry,
                       premium, lots, account_size, entry_price, mark_price,
                       verdict, created_at
                FROM paper_trades
                ORDER BY id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_paper_trades_summary(self) -> dict:
        trades = list(reversed(self.list_paper_trades()))  # chronological
        if not trades:
            return {
                "total_trades": 0, "wins": 0, "losses": 0, "win_rate": None,
                "total_pnl": 0.0, "by_direction": {}, "by_ticker": {}, "by_verdict": {},
                "equity_curve": [], "trades": [],
            }

        credit_dirs = {"sell_put", "sell_call"}
        enriched = []
        running_pnl = 0.0
        equity_curve = []

        for t in trades:
            entry = t.get("entry_price")
            mark  = t.get("mark_price")
            lots  = float(t.get("lots", 1))
            direction = t.get("direction", "")

            pnl = None
            if entry is not None and mark is not None:
                if direction in credit_dirs:
                    pnl = (entry - mark) * lots * 100   # credit: want premium to decay
                else:
                    pnl = (mark - entry) * lots * 100   # debit: want premium to rise
                running_pnl += pnl
                equity_curve.append({"date": t["created_at"][:10], "pnl": round(running_pnl, 2)})

            enriched.append({**t, "pnl": round(pnl, 2) if pnl is not None else None})

        wins   = sum(1 for t in enriched if t["pnl"] is not None and t["pnl"] > 0)
        losses = sum(1 for t in enriched if t["pnl"] is not None and t["pnl"] < 0)
        graded = wins + losses
        win_rate = round(wins / graded * 100, 1) if graded > 0 else None

        def group_by(key):
            out = {}
            for t in enriched:
                k = t.get(key) or "unknown"
                if k not in out:
                    out[k] = {"count": 0, "wins": 0, "total_pnl": 0.0}
                out[k]["count"] += 1
                if t["pnl"] is not None:
                    out[k]["total_pnl"] = round(out[k]["total_pnl"] + t["pnl"], 2)
                    if t["pnl"] > 0:
                        out[k]["wins"] += 1
            for k in out:
                c = out[k]["count"]
                w = out[k]["wins"]
                out[k]["win_rate"] = round(w / c * 100, 1) if c > 0 else None
            return out

        return {
            "total_trades": len(trades),
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "total_pnl": round(running_pnl, 2),
            "by_direction": group_by("direction"),
            "by_ticker":    group_by("ticker"),
            "by_verdict":   group_by("verdict"),
            "equity_curve": equity_curve,
            "trades": list(reversed(enriched)),  # most recent first
        }

    def update_paper_trade(self, trade_id: int, mark_price: float | None = None,
                           closed: bool = False) -> bool:
        """Update mark price and/or close a trade. Returns True if row found."""
        with self._conn() as conn:
            if closed and mark_price is not None:
                cur = conn.execute(
                    "UPDATE paper_trades SET mark_price=?, verdict='closed' WHERE id=?",
                    (float(mark_price), int(trade_id)),
                )
            elif closed:
                cur = conn.execute(
                    "UPDATE paper_trades SET verdict='closed' WHERE id=?",
                    (int(trade_id),),
                )
            elif mark_price is not None:
                cur = conn.execute(
                    "UPDATE paper_trades SET mark_price=? WHERE id=?",
                    (float(mark_price), int(trade_id)),
                )
            else:
                return False
        return cur.rowcount > 0

    def delete_paper_trade(self, trade_id: int) -> bool:
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM paper_trades WHERE id=?", (int(trade_id),))
        return cur.rowcount > 0
