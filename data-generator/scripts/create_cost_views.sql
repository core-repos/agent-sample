-- BigQuery Views for Cost Analytics
-- Run these in BigQuery to create simplified views for the SQL agent

-- 1. Daily Cost Summary View
CREATE OR REPLACE VIEW `gac-prod-471220.agent_bq_dataset.daily_cost_summary` AS
SELECT 
  DATE(date) as cost_date,
  SUM(cost) as total_daily_cost,
  AVG(cost) as avg_cost_per_entry,
  COUNT(DISTINCT application) as active_applications,
  COUNT(DISTINCT cloud) as clouds_used,
  COUNT(DISTINCT tr_product) as products,
  STRING_AGG(DISTINCT environment, ', ' ORDER BY environment) as environments
FROM `gac-prod-471220.agent_bq_dataset.cost_analysis`
GROUP BY cost_date
ORDER BY cost_date DESC;

-- 2. Application Cost Summary View
CREATE OR REPLACE VIEW `gac-prod-471220.agent_bq_dataset.application_cost_summary` AS
WITH current_period AS (
  SELECT 
    application,
    SUM(cost) as current_month_cost,
    AVG(cost) as avg_daily_cost,
    COUNT(DISTINCT DATE(date)) as active_days,
    STRING_AGG(DISTINCT cloud, ', ') as clouds,
    STRING_AGG(DISTINCT environment, ', ') as environments,
    STRING_AGG(DISTINCT managed_service, ', ' LIMIT 5) as top_services
  FROM `gac-prod-471220.agent_bq_dataset.cost_analysis`
  WHERE DATE(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  GROUP BY application
),
previous_period AS (
  SELECT 
    application,
    SUM(cost) as prev_month_cost
  FROM `gac-prod-471220.agent_bq_dataset.cost_analysis`
  WHERE DATE(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
    AND DATE(date) < DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  GROUP BY application
)
SELECT 
  c.application,
  c.current_month_cost,
  COALESCE(p.prev_month_cost, 0) as previous_month_cost,
  c.avg_daily_cost,
  c.active_days,
  c.clouds,
  c.environments,
  c.top_services,
  ROUND(SAFE_DIVIDE(c.current_month_cost - COALESCE(p.prev_month_cost, 0), p.prev_month_cost) * 100, 2) as month_over_month_change,
  CASE 
    WHEN p.prev_month_cost IS NULL THEN 'NEW'
    WHEN c.current_month_cost > p.prev_month_cost * 1.2 THEN 'INCREASING'
    WHEN c.current_month_cost < p.prev_month_cost * 0.8 THEN 'DECREASING'
    ELSE 'STABLE'
  END as trend
FROM current_period c
LEFT JOIN previous_period p ON c.application = p.application
ORDER BY c.current_month_cost DESC;

-- 3. Cloud Provider Cost Breakdown View
CREATE OR REPLACE VIEW `gac-prod-471220.agent_bq_dataset.cloud_cost_breakdown` AS
SELECT 
  cloud,
  environment,
  SUM(cost) as total_cost,
  COUNT(DISTINCT application) as num_applications,
  COUNT(DISTINCT tr_product) as num_products,
  AVG(cost) as avg_cost_per_entry,
  STRING_AGG(DISTINCT tr_product_pillar_team, ', ') as teams
FROM `gac-prod-471220.agent_bq_dataset.cost_analysis`
WHERE DATE(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY cloud, environment
ORDER BY total_cost DESC;

-- 4. Service Cost Analysis View
CREATE OR REPLACE VIEW `gac-prod-471220.agent_bq_dataset.service_cost_analysis` AS
SELECT 
  managed_service,
  cloud,
  SUM(cost) as total_cost,
  COUNT(DISTINCT application) as applications_using,
  AVG(cost) as avg_cost,
  MAX(cost) as max_single_cost,
  COUNT(*) as usage_count
FROM `gac-prod-471220.agent_bq_dataset.cost_analysis`
WHERE DATE(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY managed_service, cloud
ORDER BY total_cost DESC;

-- 5. Team Cost Attribution View
CREATE OR REPLACE VIEW `gac-prod-471220.agent_bq_dataset.team_cost_attribution` AS
SELECT 
  tr_product_pillar_team as team,
  tr_subpillar_name as subpillar,
  COUNT(DISTINCT tr_product) as num_products,
  COUNT(DISTINCT application) as num_applications,
  SUM(cost) as total_cost,
  AVG(cost) as avg_daily_cost,
  STRING_AGG(DISTINCT cloud, ', ') as clouds_used,
  STRING_AGG(DISTINCT environment, ', ') as environments
FROM `gac-prod-471220.agent_bq_dataset.cost_analysis`
WHERE DATE(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY team, subpillar
ORDER BY total_cost DESC;

-- 6. Anomaly Detection View (Day-over-Day)
CREATE OR REPLACE VIEW `gac-prod-471220.agent_bq_dataset.cost_anomalies` AS
WITH daily_app_costs AS (
  SELECT 
    DATE(date) as cost_date,
    application,
    SUM(cost) as daily_cost
  FROM `gac-prod-471220.agent_bq_dataset.cost_analysis`
  WHERE DATE(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 35 DAY)
  GROUP BY cost_date, application
),
rolling_stats AS (
  SELECT 
    cost_date,
    application,
    daily_cost,
    AVG(daily_cost) OVER (
      PARTITION BY application 
      ORDER BY cost_date 
      ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
    ) as avg_7d,
    STDDEV(daily_cost) OVER (
      PARTITION BY application 
      ORDER BY cost_date 
      ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
    ) as stddev_7d,
    LAG(daily_cost, 1) OVER (PARTITION BY application ORDER BY cost_date) as prev_day_cost
  FROM daily_app_costs
)
SELECT 
  cost_date,
  application,
  daily_cost,
  avg_7d as expected_cost,
  ROUND(daily_cost - avg_7d, 2) as deviation_amount,
  ROUND(SAFE_DIVIDE(daily_cost - avg_7d, avg_7d) * 100, 2) as deviation_percent,
  ROUND(SAFE_DIVIDE(daily_cost - avg_7d, NULLIF(stddev_7d, 0)), 2) as z_score,
  ROUND(daily_cost - prev_day_cost, 2) as day_over_day_change,
  CASE 
    WHEN ABS(SAFE_DIVIDE(daily_cost - avg_7d, NULLIF(stddev_7d, 0))) > 3 THEN 'CRITICAL'
    WHEN ABS(SAFE_DIVIDE(daily_cost - avg_7d, NULLIF(stddev_7d, 0))) > 2 THEN 'HIGH'
    WHEN ABS(SAFE_DIVIDE(daily_cost - avg_7d, avg_7d)) > 0.2 THEN 'MEDIUM'
    ELSE 'LOW'
  END as anomaly_severity
FROM rolling_stats
WHERE cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  AND avg_7d IS NOT NULL
ORDER BY cost_date DESC, ABS(deviation_percent) DESC;

-- 7. Cost Forecast View (Simple Linear Trend)
CREATE OR REPLACE VIEW `gac-prod-471220.agent_bq_dataset.cost_forecast` AS
WITH daily_totals AS (
  SELECT 
    DATE(date) as cost_date,
    SUM(cost) as daily_total,
    DATE_DIFF(DATE(date), DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY), DAY) as day_number
  FROM `gac-prod-471220.agent_bq_dataset.cost_analysis`
  WHERE DATE(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  GROUP BY cost_date
),
trend_calc AS (
  SELECT 
    AVG(daily_total) as avg_cost,
    CORR(day_number, daily_total) * (STDDEV_POP(daily_total) / STDDEV_POP(day_number)) as slope,
    AVG(daily_total) - (CORR(day_number, daily_total) * (STDDEV_POP(daily_total) / STDDEV_POP(day_number)) * AVG(day_number)) as intercept
  FROM daily_totals
)
SELECT 
  DATE_ADD(CURRENT_DATE(), INTERVAL day_offset DAY) as forecast_date,
  ROUND(intercept + slope * (30 + day_offset), 2) as forecasted_cost,
  ROUND(avg_cost, 2) as baseline_avg_cost,
  CASE 
    WHEN slope > 0 THEN 'INCREASING'
    WHEN slope < 0 THEN 'DECREASING'
    ELSE 'STABLE'
  END as trend_direction,
  ROUND(slope * 30, 2) as monthly_trend_change
FROM trend_calc
CROSS JOIN UNNEST(GENERATE_ARRAY(1, 7)) as day_offset;