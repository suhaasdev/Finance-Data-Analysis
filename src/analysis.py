"""EDA engine: KPIs, charts, and a markdown report from the company ledger.

Usage:
    python -m src.analysis [--csv data/company_ledger.csv]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
CHARTS = ROOT / "charts"


def load(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["month"])
    assert df["flow"].isin(["income", "expense"]).all(), "unexpected flow values"
    return df


def monthly_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """Wide month table: revenue, expenses, profit, margin, savings ratio."""
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"])
    monthly = df.pivot_table(index="month", columns="flow", values="amount", aggfunc="sum")
    monthly = monthly.rename(columns={"income": "revenue", "expense": "expenses"})
    monthly["net_profit"] = monthly["revenue"] - monthly["expenses"]
    monthly["margin_pct"] = 100 * monthly["net_profit"] / monthly["revenue"]
    monthly["savings_ratio"] = monthly["net_profit"] / monthly["revenue"]
    return monthly


def kpis(monthly: pd.DataFrame) -> dict:
    total_rev = monthly["revenue"].sum()
    total_exp = monthly["expenses"].sum()
    yearly = monthly.groupby(monthly.index.year)["revenue"].sum()
    yoy = (yearly.pct_change().dropna() * 100).round(1).to_dict()
    mom_chg = monthly["revenue"].pct_change().dropna()
    return {
        "total_revenue": total_rev,
        "total_expenses": total_exp,
        "net_profit": total_rev - total_exp,
        "margin_pct": 100 * (total_rev - total_exp) / total_rev,
        "yoy_revenue_growth_pct": yoy,
        "mom_volatility_pct": float(mom_chg.std() * 100),
        "best_month": monthly["net_profit"].idxmax(),
        "worst_month": monthly["net_profit"].idxmin(),
    }


def spending_patterns(df: pd.DataFrame) -> pd.DataFrame:
    exp = df[df["flow"] == "expense"].groupby("category")["amount"].sum().sort_values(ascending=False)
    return pd.DataFrame({"amount": exp, "share_pct": (100 * exp / exp.sum()).round(1)})


def make_charts(monthly: pd.DataFrame, spend: pd.DataFrame) -> None:
    CHARTS.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(monthly.index, monthly["revenue"] / 1e6, label="Revenue", lw=2)
    ax.plot(monthly.index, monthly["expenses"] / 1e6, label="Expenses", lw=2)
    ax.fill_between(monthly.index, monthly["expenses"] / 1e6, monthly["revenue"] / 1e6,
                    where=monthly["revenue"] >= monthly["expenses"], alpha=0.15, color="green")
    ax.set(title="Revenue vs Expenses", xlabel="Month", ylabel="Millions")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "revenue_vs_expenses.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    colors = ["#2e7d32" if v >= 0 else "#c62828" for v in monthly["net_profit"]]
    ax.bar(monthly.index, monthly["net_profit"] / 1e3, color=colors)
    ax.set(title="Monthly Net Profit", xlabel="Month", ylabel="Thousands")
    fig.tight_layout()
    fig.savefig(CHARTS / "monthly_profit.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    top = spend.head(8)
    ax.barh(top.index[::-1], top["amount"][::-1] / 1e3, color="#455a64")
    ax.set(title="Expense Categories (Pareto)", xlabel="Thousands")
    for i, (share, val) in enumerate(zip(top["share_pct"][::-1], top["amount"][::-1] / 1e3)):
        ax.text(val, i, f" {share:.0f}%", va="center")
    fig.tight_layout()
    fig.savefig(CHARTS / "expense_categories.png", dpi=150)
    plt.close(fig)


def write_report(kpi: dict, spend: pd.DataFrame, monthly: pd.DataFrame) -> Path:
    REPORTS.mkdir(exist_ok=True)
    lines = [
        "# Finance Report (3-Year Ledger)\n",
        "## Headline KPIs\n",
        f"| KPI | Value |\n|---|---|",
        f"| Total revenue | ${kpi['total_revenue']:,.0f} |",
        f"| Total expenses | ${kpi['total_expenses']:,.0f} |",
        f"| Net profit | ${kpi['net_profit']:,.0f} |",
        f"| Profit margin | {kpi['margin_pct']:.1f}% |",
        f"| YoY revenue growth | {kpi['yoy_revenue_growth_pct']} |",
        f"| MoM revenue volatility | {kpi['mom_volatility_pct']:.1f}% |",
        f"| Best month | {kpi['best_month'].strftime('%b %Y')} |",
        f"| Worst month | {kpi['worst_month'].strftime('%b %Y')} |\n",
        "## Spending patterns\n",
        "| Category | Spend | Share |",
        "|---|---|---|",
    ]
    for cat, row in spend.iterrows():
        lines.append(f"| {cat} | ${row['amount']:,.0f} | {row['share_pct']}% |")
    top3 = spend["share_pct"].head(3).sum()
    lines += [
        "",
        f"Top-3 categories concentrate **{top3:.0f}%** of all spending.",
        f"Average monthly savings ratio: **{monthly['savings_ratio'].mean():.1%}**.",
        "",
        "Charts: `charts/revenue_vs_expenses.png`, `charts/monthly_profit.png`, `charts/expense_categories.png`.",
    ]
    out = REPORTS / "finance_report.md"
    out.write_text("\n".join(lines))
    return out


def run(csv_path: Path) -> dict:
    df = load(csv_path)
    monthly = monthly_pivot(df)
    kpi = kpis(monthly)
    spend = spending_patterns(df)
    make_charts(monthly, spend)
    report = write_report(kpi, spend, monthly)
    for k, v in kpi.items():
        print(f"{k:<26} {v if isinstance(v, str) else (f'{v:,.2f}' if isinstance(v, float) else v)}")
    print(f"Report -> {report}")
    return kpi


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=ROOT / "data" / "company_ledger.csv")
    args = parser.parse_args()
    run(args.csv)
