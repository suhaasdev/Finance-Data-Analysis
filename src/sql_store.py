"""Load the ledger into SQLite and answer business questions with SQL.

Usage:
    python -m src.sql_store [--csv data/company_ledger.csv] [--db finance.db]
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

SCHEMA = """
CREATE TABLE IF NOT EXISTS ledger (
    month    TEXT NOT NULL,
    flow     TEXT NOT NULL CHECK (flow IN ('income', 'expense')),
    category TEXT NOT NULL,
    region   TEXT NOT NULL,
    amount   REAL NOT NULL CHECK (amount >= 0)
);
CREATE INDEX IF NOT EXISTS idx_ledger_month ON ledger (month);
CREATE INDEX IF NOT EXISTS idx_ledger_cat   ON ledger (category);
"""

QUERY_KPI = """
SELECT
    ROUND(SUM(CASE WHEN flow = 'income'  THEN amount ELSE 0 END), 2) AS total_revenue,
    ROUND(SUM(CASE WHEN flow = 'expense' THEN amount ELSE 0 END), 2) AS total_expenses,
    ROUND(SUM(CASE WHEN flow = 'income' THEN amount ELSE -amount END), 2) AS net_profit
FROM ledger
"""

QUERY_YEARLY = """
SELECT SUBSTR(month, 1, 4) AS year,
       ROUND(SUM(CASE WHEN flow = 'income' THEN amount ELSE -amount END), 2) AS net_profit
FROM ledger GROUP BY year ORDER BY year
"""

QUERY_CATEGORY = """
SELECT flow, category,
       ROUND(SUM(amount), 2) AS total,
       ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (PARTITION BY flow), 1) AS share_pct
FROM ledger
GROUP BY flow, category
ORDER BY flow DESC, total DESC
"""

QUERY_REGION = """
SELECT region, flow, ROUND(SUM(amount), 2) AS total
FROM ledger
GROUP BY region, flow
ORDER BY region, flow
"""


def load_to_sqlite(csv_path: Path, db_path: Path) -> sqlite3.Connection:
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    df = pd.read_csv(csv_path)
    conn.executemany(
        "INSERT INTO ledger (month, flow, category, region, amount) VALUES (?, ?, ?, ?, ?)",
        df[["month", "flow", "category", "region", "amount"]].itertuples(index=False, name=None),
    )
    conn.commit()
    return conn


def run(csv_path: Path = ROOT / "data" / "company_ledger.csv",
        db_path: Path = ROOT / "finance.db") -> None:
    conn = load_to_sqlite(csv_path, db_path)
    try:
        kpi = pd.read_sql_query(QUERY_KPI, conn).iloc[0]
        print("KPIs (via SQL):")
        print(kpi.to_string(), "\n")
        print("Net profit by year:")
        print(pd.read_sql_query(QUERY_YEARLY, conn).to_string(index=False), "\n")
        print("Category breakdown (top 8):")
        print(pd.read_sql_query(QUERY_CATEGORY, conn).head(8).to_string(index=False), "\n")
        print("Region breakdown:")
        print(pd.read_sql_query(QUERY_REGION, conn).to_string(index=False))
    finally:
        conn.close()
    print(f"\nWarehouse -> {db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=ROOT / "data" / "company_ledger.csv")
    parser.add_argument("--db", type=Path, default=ROOT / "finance.db")
    args = parser.parse_args()
    run(args.csv, args.db)
