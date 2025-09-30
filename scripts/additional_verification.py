#!/usr/bin/env python3
"""
Additional BigQuery verification queries
"""

import os
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv('/Users/gurukallam/projects/ADK-Agents/.env')

# Connect to BigQuery
project_id = os.getenv('GCP_PROJECT_ID')
dataset_id = os.getenv('BQ_DATASET')
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

credentials = service_account.Credentials.from_service_account_file(credentials_path)
client = bigquery.Client(credentials=credentials, project=project_id)

print('=== ADDITIONAL VERIFICATION QUERIES ===')

# Check for specific fields mentioned in the requirements
print('\n1. COST_ANALYSIS FIELD ANALYSIS:')
query = f'''
SELECT column_name, data_type, is_nullable
FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'cost_analysis'
ORDER BY ordinal_position
'''
result = client.query(query).result()
for row in result:
    print(f'   {row.column_name:<25} {row.data_type:<15} {row.is_nullable}')

print('\n2. BUDGET_ANALYSIS FIELD ANALYSIS:')
query = f'''
SELECT column_name, data_type, is_nullable
FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'budget_analysis'
ORDER BY ordinal_position
'''
result = client.query(query).result()
for row in result:
    print(f'   {row.column_name:<25} {row.data_type:<15} {row.is_nullable}')

print('\n3. DATA QUALITY CHECKS:')

# Check for NULL apm_id values
query = f'''
SELECT
  COUNT(*) as total_rows,
  COUNT(apm_id) as apm_id_populated,
  COUNT(*) - COUNT(apm_id) as apm_id_null
FROM `{project_id}.{dataset_id}.cost_analysis`
'''
result = client.query(query).result()
for row in result:
    print(f'   Cost Analysis - Total: {row.total_rows}, APM_ID populated: {row.apm_id_populated}, APM_ID null: {row.apm_id_null}')

# Check unique values in key dimensions
print('\n4. KEY DIMENSION ANALYSIS:')
query = f'''
SELECT
  COUNT(DISTINCT cloud) as unique_clouds,
  COUNT(DISTINCT environment) as unique_environments,
  COUNT(DISTINCT application) as unique_applications,
  COUNT(DISTINCT apm_id) as unique_apm_ids,
  MIN(date) as earliest_date,
  MAX(date) as latest_date
FROM `{project_id}.{dataset_id}.cost_analysis`
'''
result = client.query(query).result()
for row in result:
    print(f'   Clouds: {row.unique_clouds}, Environments: {row.unique_environments}')
    print(f'   Applications: {row.unique_applications}, APM IDs: {row.unique_apm_ids}')
    print(f'   Date range: {row.earliest_date} to {row.latest_date}')

print('\n5. BUDGET TABLE ANALYSIS:')
query = f'''
SELECT
  COUNT(DISTINCT cto) as unique_ctos,
  COUNT(DISTINCT tr_product_pillar_team) as unique_teams,
  COUNT(DISTINCT tr_product_id) as unique_products,
  MIN(fy_24_budget) as min_fy24_budget,
  MAX(fy_26_budget) as max_fy26_budget
FROM `{project_id}.{dataset_id}.budget_analysis`
'''
result = client.query(query).result()
for row in result:
    print(f'   CTOs: {row.unique_ctos}, Teams: {row.unique_teams}, Products: {row.unique_products}')
    print(f'   Budget range (FY24): ${row.min_fy24_budget:,.2f} to (FY26): ${row.max_fy26_budget:,.2f}')

print('\n6. JOIN COMPATIBILITY TEST:')
query = f'''
SELECT
  c.tr_product_id,
  c.tr_product,
  COUNT(DISTINCT c.application) as applications,
  SUM(c.cost) as total_cost,
  b.fy_26_budget,
  b.fy26_projected_spend
FROM `{project_id}.{dataset_id}.cost_analysis` c
LEFT JOIN `{project_id}.{dataset_id}.budget_analysis` b
  ON c.tr_product_id = b.tr_product_id
WHERE c.tr_product_id IS NOT NULL
GROUP BY c.tr_product_id, c.tr_product, b.fy_26_budget, b.fy26_projected_spend
ORDER BY total_cost DESC
LIMIT 5
'''
result = client.query(query).result()
print(f'   Join test results (cost vs budget by product):')
for row in result:
    budget = row.fy_26_budget or 0
    print(f'   Product {row.tr_product_id}: {row.tr_product} - Cost: ${row.total_cost:,.2f}, Budget: ${budget:,.2f}')