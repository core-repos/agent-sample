-- Sample Budget Queries for BigQuery Analytics AI Agent
-- Project: gac-prod-471220, Dataset: agent_bq_dataset, Table: budget_analysis

-- =============================================
-- QUERY 1: Budget Summary by Product ID
-- =============================================
SELECT
  tr_product_id,
  tr_product,
  tr_product_pillar_team,
  cto,
  SUM(fy_24_budget) AS total_fy_24_budget,
  SUM(fy_25_budget) AS total_fy_25_budget,
  SUM(fy_26_budget) AS total_fy_26_budget,
  SUM(fy26_ytd_spend) AS total_fy26_ytd_spend,
  SUM(fy26_projected_spend) AS total_fy26_projected_spend,
  ROUND(SUM(fy26_ytd_spend) / SUM(fy_26_budget) * 100, 2) AS fy26_utilization_pct,
  ROUND(SUM(fy26_projected_spend) - SUM(fy_26_budget), 2) AS fy26_projected_variance
FROM
  `gac-prod-471220`.`agent_bq_dataset`.`budget_analysis`
GROUP BY
  tr_product_id, tr_product, tr_product_pillar_team, cto
ORDER BY
  tr_product_id;

-- =============================================
-- QUERY 2: Budget Summary by Organization/CTO
-- =============================================
SELECT
  cto,
  tr_product_pillar_team,
  COUNT(DISTINCT tr_product_id) AS num_products,
  SUM(fy_24_budget) AS total_fy_24_budget,
  SUM(fy_25_budget) AS total_fy_25_budget,
  SUM(fy_26_budget) AS total_fy_26_budget,
  SUM(fy26_ytd_spend) AS total_fy26_ytd_spend,
  SUM(fy26_projected_spend) AS total_fy26_projected_spend,
  ROUND(SUM(fy26_ytd_spend) / SUM(fy_26_budget) * 100, 2) AS fy26_utilization_pct,
  ROUND((SUM(fy26_projected_spend) - SUM(fy_26_budget)) / SUM(fy_26_budget) * 100, 2) AS fy26_variance_pct,
  CASE
    WHEN SUM(fy26_projected_spend) > SUM(fy_26_budget) * 1.1 THEN 'OVER_BUDGET'
    WHEN SUM(fy26_projected_spend) > SUM(fy_26_budget) * 0.95 THEN 'AT_RISK'
    WHEN SUM(fy26_ytd_spend) / SUM(fy_26_budget) < 0.3 THEN 'UNDER_UTILIZED'
    ELSE 'ON_TRACK'
  END AS budget_status
FROM
  `gac-prod-471220`.`agent_bq_dataset`.`budget_analysis`
GROUP BY
  cto, tr_product_pillar_team
ORDER BY
  cto, total_fy_26_budget DESC;

-- =============================================
-- QUERY 3: Products Over Budget (Bonus Query)
-- =============================================
SELECT
  tr_product_id,
  tr_product,
  tr_product_pillar_team,
  cto,
  fy_26_budget,
  fy26_ytd_spend,
  fy26_projected_spend,
  ROUND(fy26_projected_spend - fy_26_budget, 2) AS projected_overspend,
  ROUND(fy26_projected_spend / fy_26_budget * 100, 2) AS projected_utilization_pct,
  ROUND(fy26_ytd_spend / fy_26_budget * 100, 2) AS ytd_utilization_pct
FROM
  `gac-prod-471220`.`agent_bq_dataset`.`budget_analysis`
WHERE
  fy26_projected_spend > fy_26_budget
ORDER BY
  projected_overspend DESC;

-- =============================================
-- QUERY 4: Fiscal Year Budget Comparison
-- =============================================
SELECT
  tr_product_pillar_team,
  cto,
  SUM(fy_24_budget) AS fy24_budget,
  SUM(fy_25_budget) AS fy25_budget,
  SUM(fy_26_budget) AS fy26_budget,
  ROUND((SUM(fy_25_budget) - SUM(fy_24_budget)) / SUM(fy_24_budget) * 100, 2) AS fy24_to_fy25_growth_pct,
  ROUND((SUM(fy_26_budget) - SUM(fy_25_budget)) / SUM(fy_25_budget) * 100, 2) AS fy25_to_fy26_growth_pct,
  ROUND((SUM(fy_26_budget) - SUM(fy_24_budget)) / SUM(fy_24_budget) * 100, 2) AS total_2yr_growth_pct
FROM
  `gac-prod-471220`.`agent_bq_dataset`.`budget_analysis`
GROUP BY
  tr_product_pillar_team, cto
ORDER BY
  total_2yr_growth_pct DESC;