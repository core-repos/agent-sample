-- Sample Cost Queries for BigQuery Analytics AI Agent
-- Project: gac-prod-471220, Dataset: agent_bq_dataset, Table: cost_analysis
-- Updated Schema with New Fields

-- =============================================
-- QUERY 1: Total Cost by CTO Organization
-- =============================================
SELECT
  cto,
  SUM(cost) AS total_cost,
  COUNT(*) AS total_records,
  ROUND(AVG(cost), 2) AS avg_cost_per_record
FROM
  `gac-prod-471220`.`agent_bq_dataset`.`cost_analysis`
GROUP BY
  cto
ORDER BY
  total_cost DESC;

-- =============================================
-- QUERY 2: Cost Breakdown by Application and Service
-- =============================================
SELECT
  application,
  service_name,
  managed_service,
  environment,
  SUM(cost) AS total_cost,
  COUNT(*) AS record_count,
  ROUND(SUM(cost) / COUNT(*), 2) AS avg_cost
FROM
  `gac-prod-471220`.`agent_bq_dataset`.`cost_analysis`
GROUP BY
  application, service_name, managed_service, environment
ORDER BY
  total_cost DESC
LIMIT 20;

-- =============================================
-- QUERY 3: Daily Cost Trend Analysis
-- =============================================
SELECT
  date,
  cloud,
  SUM(cost) AS daily_cost,
  COUNT(DISTINCT application) AS unique_applications,
  COUNT(DISTINCT tr_product_id) AS unique_products
FROM
  `gac-prod-471220`.`agent_bq_dataset`.`cost_analysis`
WHERE
  date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY
  date, cloud
ORDER BY
  date DESC, cloud;

-- =============================================
-- QUERY 4: Product Hierarchy Cost Analysis
-- =============================================
SELECT
  cto,
  tr_product_pillar_team,
  tr_subpillar_name,
  tr_product_id,
  tr_product,
  SUM(cost) AS total_product_cost,
  COUNT(DISTINCT application) AS applications_count,
  COUNT(DISTINCT service_name) AS services_count
FROM
  `gac-prod-471220`.`agent_bq_dataset`.`cost_analysis`
GROUP BY
  cto, tr_product_pillar_team, tr_subpillar_name, tr_product_id, tr_product
ORDER BY
  total_product_cost DESC
LIMIT 15;

-- =============================================
-- QUERY 5: Environment vs Cloud Cost Comparison
-- =============================================
SELECT
  environment,
  cloud,
  SUM(cost) AS total_cost,
  ROUND(SUM(cost) * 100.0 / SUM(SUM(cost)) OVER(), 2) AS cost_percentage,
  COUNT(*) AS record_count
FROM
  `gac-prod-471220`.`agent_bq_dataset`.`cost_analysis`
GROUP BY
  environment, cloud
ORDER BY
  total_cost DESC;

-- =============================================
-- QUERY 6: Top Services by Cost
-- =============================================
SELECT
  managed_service,
  service_name,
  COUNT(DISTINCT application) AS applications_using,
  SUM(cost) AS total_service_cost,
  ROUND(AVG(cost), 2) AS avg_cost_per_record,
  MIN(cost) AS min_cost,
  MAX(cost) AS max_cost
FROM
  `gac-prod-471220`.`agent_bq_dataset`.`cost_analysis`
GROUP BY
  managed_service, service_name
HAVING
  SUM(cost) > 10000  -- Filter for services with significant cost
ORDER BY
  total_service_cost DESC
LIMIT 25;

-- =============================================
-- QUERY 7: Application Hierarchy Analysis with APM
-- =============================================
SELECT
  cto,
  tr_product_pillar_team,
  tr_subpillar_name,
  tr_product_id,
  tr_product,
  apm_id,
  application,
  COUNT(*) AS record_count,
  SUM(cost) AS total_cost,
  ROUND(AVG(cost), 2) AS avg_cost
FROM
  `gac-prod-471220`.`agent_bq_dataset`.`cost_analysis`
GROUP BY
  cto, tr_product_pillar_team, tr_subpillar_name, tr_product_id, tr_product, apm_id, application
ORDER BY
  total_cost DESC
LIMIT 20;

-- =============================================
-- QUERY 8: Fiscal Year Average Daily Spend Analysis
-- =============================================
WITH fiscal_year_averages AS (
    SELECT
        environment,
        -- FY24 Average Daily Spend
        ROUND(SUM(CASE WHEN date BETWEEN '2023-02-01' AND '2024-01-31' THEN cost ELSE 0 END) /
              NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2023-02-01' AND '2024-01-31' THEN date ELSE NULL END), 0), 2) AS fy24_avg_daily_spend,
        -- FY25 Average Daily Spend
        ROUND(SUM(CASE WHEN date BETWEEN '2024-02-01' AND '2025-01-31' THEN cost ELSE 0 END) /
              NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2024-02-01' AND '2025-01-31' THEN date ELSE NULL END), 0), 2) AS fy25_avg_daily_spend,
        -- FY26 Average Daily Spend
        ROUND(SUM(CASE WHEN date BETWEEN '2025-02-01' AND '2026-01-31' THEN cost ELSE 0 END) /
              NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2025-02-01' AND '2026-01-31' THEN date ELSE NULL END), 0), 2) AS fy26_avg_daily_spend,
        -- FY26 YTD Daily Spend
        ROUND(SUM(CASE WHEN date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3 THEN cost ELSE 0 END) /
              NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3 THEN date ELSE NULL END), 0), 2) AS fy26_ytd_avg_daily_spend
    FROM
        `gac-prod-471220`.`agent_bq_dataset`.`cost_analysis`
    WHERE
        date BETWEEN '2023-02-01' AND '2026-01-31'
    GROUP BY
        environment
),
daily_costs AS (
    SELECT
        date,
        environment,
        ROUND(SUM(cost), 2) AS daily_cost -- Daily cost for each specific date
    FROM
        `gac-prod-471220`.`agent_bq_dataset`.`cost_analysis`
    WHERE
        date BETWEEN '2023-02-01' AND '2026-01-31'
    GROUP BY
        date, environment
)
SELECT
    d.date,
    d.environment,
    f.fy24_avg_daily_spend,
    f.fy25_avg_daily_spend,
    f.fy26_avg_daily_spend,
    f.fy26_ytd_avg_daily_spend,
    d.daily_cost
FROM
    daily_costs d
LEFT JOIN
    fiscal_year_averages f
ON
    d.environment = f.environment
ORDER BY
    d.date, d.environment;