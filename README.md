# 💰 Finance Data Analysis

Exploratory data analysis on a 3-year company ledger that surfaces revenue trends, spending patterns, and key performance indicators — combining Python (Pandas/NumPy/Matplotlib) with a SQLite warehouse and SQL analytics.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Pandas](https://img.shields.io/badge/Pandas-EDA-150458)
![SQL](https://img.shields.io/badge/SQLite-Warehouse-blue)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## ✨ What it does

- **Generates a realistic 3-year ledger** (~21,600 monthly transactions: income & expense flows with seasonality and growth trends)
- **Computes core KPIs** — revenue, expenses, net profit, profit margin, MoM/YoY growth, expense ratios, best/worst months
- **Surfaces spending patterns** — category breakdowns, expense concentration (top-3 share), month-over-month volatility
- **SQL warehouse layer** — loads the ledger into SQLite and answers the same business questions in SQL (`sql/queries.sql`)
- **Exports deliverables** — `reports/finance_report.md` + 3 charts (revenue vs expenses trend, monthly profit, expense Pareto)

## 🚀 Quickstart

```bash
pip install -r requirements.txt

python data/generate_financials.py   # → data/company_ledger.csv
python -m src.analysis               # KPIs + reports/ + charts/
python -m src.sql_store              # SQLite warehouse + SQL KPIs
```

Or run the SQL queries against any SQLite/Postgres/MySQL database directly — see `sql/queries.sql`.

## 📊 KPIs computed

| KPI | Definition |
|---|---|
| Revenue / Expenses / Net Profit | Aggregated by flow type |
| Profit margin | Net profit ÷ revenue |
| YoY growth | Revenue year vs prior year |
| MoM volatility | Std-dev of monthly revenue change |
| Expense concentration | Share of spend in top-3 categories |
| Savings ratio | (Revenue − expenses) ÷ revenue, per month |

## 📁 Structure

```
├── data/generate_financials.py   # Reproducible ledger generator (fixed seed)
├── src/analysis.py               # EDA engine → KPIs, charts, markdown report
├── src/sql_store.py              # SQLite loader + SQL aggregations
├── sql/queries.sql               # Portable SQL analytics
├── tests/test_finance.py
├── reports/ · charts/            # Generated outputs (gitignored)
└── requirements.txt
```

## 📄 License

MIT — see [LICENSE](LICENSE).
