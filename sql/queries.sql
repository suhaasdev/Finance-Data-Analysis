-- Finance analytics — portable SQL (works on SQLite; minor tweaks for Postgres/MySQL)
-- Companion to src/sql_store.py. Table: ledger(month, flow, category, region, amount)

-- 1. Headline KPIs
SELECT
    ROUND(SUM(CASE WHEN flow = 'income'  THEN amount ELSE 0 END), 2)     AS total_revenue,
    ROUND(SUM(CASE WHEN flow = 'expense' THEN amount ELSE 0 END), 2)     AS total_expenses,
    ROUND(SUM(CASE WHEN flow = 'income' THEN amount ELSE -amount END), 2) AS net_profit,
    ROUND(100.0 * SUM(CASE WHEN flow = 'income' THEN amount ELSE -amount END)
        / NULLIF(SUM(CASE WHEN flow = 'income' THEN amount ELSE 0 END), 0), 1) AS margin_pct
FROM ledger;

-- 2. Monthly revenue, expenses, profit
SELECT month,
       SUM(CASE WHEN flow = 'income'  THEN amount ELSE 0 END) AS revenue,
       SUM(CASE WHEN flow = 'expense' THEN amount ELSE 0 END) AS expenses,
       SUM(CASE WHEN flow = 'income' THEN amount ELSE -amount END) AS net_profit
FROM ledger
GROUP BY month
ORDER BY month;

-- 3. Year-over-year revenue growth (window function)
WITH yearly AS (
    SELECT SUBSTR(month, 1, 4) AS yr,
           SUM(CASE WHEN flow = 'income' THEN amount ELSE 0 END) AS revenue
    FROM ledger GROUP BY yr
)
SELECT yr, revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY yr))
             / LAG(revenue) OVER (ORDER BY yr), 1) AS yoy_growth_pct
FROM yearly;

-- 4. Income mix and expense mix
SELECT flow, category,
       ROUND(SUM(amount), 2) AS total,
       ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (PARTITION BY flow), 1) AS share_pct
FROM ledger
GROUP BY flow, category
ORDER BY flow DESC, total DESC;

-- 5. Revenue by region
SELECT region,
       ROUND(SUM(CASE WHEN flow = 'income' THEN amount ELSE 0 END), 2) AS revenue,
       ROUND(100.0 * SUM(CASE WHEN flow = 'income' THEN amount ELSE 0 END)
             / SUM(SUM(CASE WHEN flow = 'income' THEN amount ELSE 0 END)) OVER (), 1) AS share_pct
FROM ledger
GROUP BY region
ORDER BY revenue DESC;

-- 6. Quarter with the highest marketing spend (seasonality check)
SELECT SUBSTR(month, 6, 2) AS month_no,
       ROUND(SUM(amount), 2) AS marketing_spend
FROM ledger
WHERE category = 'Marketing'
GROUP BY month_no
ORDER BY marketing_spend DESC;

-- 7. Months where expenses exceeded 85% of revenue (efficiency watchlist)
WITH m AS (
    SELECT month,
           SUM(CASE WHEN flow = 'income'  THEN amount ELSE 0 END) AS revenue,
           SUM(CASE WHEN flow = 'expense' THEN amount ELSE 0 END) AS expenses
    FROM ledger GROUP BY month
)
SELECT month, ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * expenses / revenue, 1) AS expense_ratio_pct
FROM m
WHERE expenses > 0.85 * revenue
ORDER BY month;
