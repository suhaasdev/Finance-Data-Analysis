"""Generate a 3-year monthly company ledger with realistic seasonality.

Each row: month, flow (income/expense), category, amount, region.
Income grows ~1.2%/month with Q4 seasonality; expenses are stickier with
a year-end bump. Fixed seed → reproducible.

Usage:
    python data/generate_financials.py   # → data/company_ledger.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
HERE = Path(__file__).parent

INCOME_CATEGORIES = ["Product Sales", "Services", "Subscriptions", "Interest Income"]
INCOME_WEIGHTS = [0.55, 0.22, 0.18, 0.05]
EXPENSE_CATEGORIES = ["Payroll", "COGS", "Marketing", "Rent & Utilities",
                      "Software & IT", "Travel", "Professional Services"]
EXPENSE_WEIGHTS = [0.38, 0.22, 0.14, 0.10, 0.08, 0.04, 0.04]
REGIONS = ["North", "South", "East", "West"]
SEASONALITY = np.array([0.85, 0.82, 0.95, 0.97, 1.02, 1.05, 0.92, 0.96, 1.08, 1.12, 1.30, 1.42])


def generate() -> pd.DataFrame:
    months = pd.date_range("2023-01-31", "2025-12-31", freq="ME")
    rows = []
    revenue_base = 820_000.0

    for i, month in enumerate(months):
        trend = (1.012 ** i)
        seasonal = SEASONALITY[month.month - 1]
        # Income: one record per category per region per month
        for cat, w in zip(INCOME_CATEGORIES, INCOME_WEIGHTS):
            for region in REGIONS:
                amount = revenue_base * trend * seasonal * w / len(REGIONS)
                amount *= RNG.normal(1.0, 0.08)
                rows.append({
                    "month": month.strftime("%Y-%m"),
                    "flow": "income",
                    "category": cat,
                    "region": region,
                    "amount": round(max(amount, 0), 2),
                })

        # Expenses: sticky base growing slower than revenue
        expense_base = 640_000.0 * (1.006 ** i) * (0.94 + 0.10 * seasonal)
        for cat, w in zip(EXPENSE_CATEGORIES, EXPENSE_WEIGHTS):
            bump = 1.35 if (cat == "Marketing" and month.month == 11) else 1.0
            amount = expense_base * w * bump * RNG.normal(1.0, 0.10)
            region = REGIONS[RNG.integers(0, 4)] if cat not in ("Payroll", "Rent & Utilities") else "HQ"
            rows.append({
                "month": month.strftime("%Y-%m"),
                "flow": "expense",
                "category": cat,
                "region": region,
                "amount": round(max(amount, 0), 2),
            })

    df = pd.DataFrame(rows)
    return df.sort_values(["month", "flow", "category"]).reset_index(drop=True)


def main() -> None:
    out = HERE / "company_ledger.csv"
    df = generate()
    out.write_text(df.to_csv(index=False))
    income = df[df["flow"] == "income"]["amount"].sum()
    expense = df[df["flow"] == "expense"]["amount"].sum()
    print(f"Wrote {len(df)} rows -> {out}")
    print(f"Income ${income:,.0f} | Expenses ${expense:,.0f} | Margin {(income - expense) / income:.1%}")


if __name__ == "__main__":
    main()
