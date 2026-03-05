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
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
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
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

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

    def save_paper_trade(self, trade: dict) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO paper_trades
                (ticker, direction, strategy_rank, strike, expiry, premium, lots, account_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )
            return int(cur.lastrowid)

    def list_paper_trades(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT id, ticker, direction, strategy_rank, strike, expiry,
                       premium, lots, account_size, created_at
                FROM paper_trades
                ORDER BY id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]
