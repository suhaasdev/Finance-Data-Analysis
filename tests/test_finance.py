"""Tests for the finance EDA pipeline."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.generate_financials import generate  # noqa: E402


@pytest.fixture(scope="module")
def ledger(tmp_path_factory) -> pd.DataFrame:
    df = generate()
    csv = tmp_path_factory.mktemp("data") / "ledger.csv"
    csv.write_text(df.to_csv(index=False))
    return df


def test_generation(ledger):
    assert {"month", "flow", "category", "region", "amount"} == set(ledger.columns)
    assert ledger["flow"].isin(["income", "expense"]).all()
    assert (ledger["amount"] >= 0).all()
    assert ledger["month"].str.match(r"^\d{4}-\d{2}$").all()


def test_monthly_pivot(ledger):
    from src.analysis import monthly_pivot

    monthly = monthly_pivot(ledger)
    assert len(monthly) == 36  # 3 years of months
    assert (monthly["net_profit"] > 0).all()
    assert (monthly["margin_pct"] > 0).all()


def test_kpis(ledger):
    from src.analysis import kpis, monthly_pivot

    kpi = kpis(monthly_pivot(ledger))
    assert kpi["total_revenue"] > kpi["total_expenses"]
    assert 0 < kpi["margin_pct"] < 60
    assert len(kpi["yoy_revenue_growth_pct"]) == 2
    assert set(kpi["yoy_revenue_growth_pct"].values()) and all(v > 0 for v in kpi["yoy_revenue_growth_pct"].values())


def test_spending_patterns(ledger):
    from src.analysis import spending_patterns

    spend = spending_patterns(ledger)
    assert spend.index[0] == "Payroll"
    assert spend["share_pct"].sum() == pytest.approx(100.0, abs=0.2)


def test_sql_store(tmp_path, ledger):
    from src.sql_store import QUERY_KPI, QUERY_YEARLY, load_to_sqlite

    db = tmp_path / "test.db"
    csv = tmp_path / "ledger.csv"
    csv.write_text(ledger.to_csv(index=False))
    con = load_to_sqlite(csv, db)
    try:
        kpi = pd.read_sql_query(QUERY_KPI, con).iloc[0]
        assert kpi["total_revenue"] > 0
        yearly = pd.read_sql_query(QUERY_YEARLY, con)
        assert len(yearly) == 3
    finally:
        con.close()
