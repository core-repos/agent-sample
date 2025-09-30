#!/usr/bin/env python3
"""
BigQuery Table Verification Script
Connects to BigQuery and verifies the actual current state of both tables:
- cost_analysis table
- budget_analysis table
"""

import os
import sys
import json
from typing import Dict, Any, List
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv

# Add parent directory to path to import from genai-agents-backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'genai-agents-backend'))

# Load environment variables
load_dotenv('/Users/gurukallam/projects/ADK-Agents/.env')

def get_bigquery_client() -> bigquery.Client:
    """Get BigQuery client with service account credentials"""
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    project_id = os.getenv('GCP_PROJECT_ID')

    if not project_id:
        raise ValueError("GCP_PROJECT_ID environment variable is required")

    if credentials_path and os.path.exists(credentials_path):
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        client = bigquery.Client(credentials=credentials, project=project_id)
    else:
        # Try to use default credentials
        client = bigquery.Client(project=project_id)

    print(f"✓ Connected to BigQuery project: {project_id}")
    return client

def get_table_schema(client: bigquery.Client, dataset_id: str, table_id: str) -> Dict[str, Any]:
    """Get detailed schema information for a table"""
    table_ref = client.dataset(dataset_id).table(table_id)

    try:
        table = client.get_table(table_ref)
        schema_info = {
            'table_id': table.table_id,
            'num_rows': table.num_rows,
            'num_bytes': table.num_bytes,
            'created': table.created.isoformat() if table.created else None,
            'modified': table.modified.isoformat() if table.modified else None,
            'fields': []
        }

        for field in table.schema:
            field_info = {
                'name': field.name,
                'field_type': field.field_type,
                'mode': field.mode,
                'description': field.description
            }
            schema_info['fields'].append(field_info)

        return schema_info
    except Exception as e:
        return {'error': str(e)}

def run_sample_query(client: bigquery.Client, query: str, description: str) -> Dict[str, Any]:
    """Run a sample query and return results"""
    print(f"\n📊 {description}")
    print(f"Query: {query}")

    try:
        query_job = client.query(query)
        results = query_job.result()

        rows = []
        for row in results:
            rows.append(dict(row))

        return {
            'success': True,
            'row_count': len(rows),
            'rows': rows,
            'job_id': query_job.job_id
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def verify_tables():
    """Main verification function"""
    dataset_id = os.getenv('BQ_DATASET', 'agent_bq_dataset')

    print("=" * 80)
    print("🔍 BIGQUERY TABLE VERIFICATION")
    print("=" * 80)

    try:
        client = get_bigquery_client()

        # List all tables in the dataset
        print(f"\n📋 Dataset: {dataset_id}")
        dataset_ref = client.dataset(dataset_id)
        tables = list(client.list_tables(dataset_ref))
        table_names = [table.table_id for table in tables]
        print(f"Available tables: {table_names}")

        # Expected tables
        expected_tables = ['cost_analysis', 'budget_analysis']

        for table_name in expected_tables:
            print(f"\n" + "="*60)
            print(f"🔎 VERIFYING TABLE: {table_name}")
            print(f"="*60)

            if table_name not in table_names:
                print(f"❌ Table {table_name} does not exist!")
                continue

            # Get schema information
            schema = get_table_schema(client, dataset_id, table_name)

            if 'error' in schema:
                print(f"❌ Error getting schema: {schema['error']}")
                continue

            print(f"✓ Table exists")
            print(f"✓ Rows: {schema['num_rows']:,}")
            print(f"✓ Size: {schema['num_bytes']:,} bytes")
            print(f"✓ Created: {schema['created']}")
            print(f"✓ Modified: {schema['modified']}")
            print(f"✓ Fields: {len(schema['fields'])}")

            # Print schema details
            print(f"\n📋 SCHEMA DETAILS:")
            for i, field in enumerate(schema['fields'], 1):
                print(f"  {i:2d}. {field['name']:<25} {field['field_type']:<15} {field['mode']:<10}")

            # Run verification queries
            print(f"\n🧪 VERIFICATION QUERIES:")

            # Count query
            count_result = run_sample_query(
                client,
                f"SELECT COUNT(*) as total_rows FROM `{client.project}.{dataset_id}.{table_name}`",
                f"Total row count for {table_name}"
            )

            if count_result['success']:
                print(f"✓ Total rows: {count_result['rows'][0]['total_rows']:,}")
            else:
                print(f"❌ Count query failed: {count_result['error']}")

            # Sample data query
            sample_result = run_sample_query(
                client,
                f"SELECT * FROM `{client.project}.{dataset_id}.{table_name}` LIMIT 3",
                f"Sample data from {table_name}"
            )

            if sample_result['success']:
                print(f"✓ Sample data retrieved ({sample_result['row_count']} rows)")
                for i, row in enumerate(sample_result['rows'], 1):
                    print(f"  Row {i}: {row}")
            else:
                print(f"❌ Sample query failed: {sample_result['error']}")

        # Test table compatibility with joins
        if 'cost_analysis' in table_names and 'budget_analysis' in table_names:
            print(f"\n" + "="*60)
            print(f"🔗 TESTING TABLE COMPATIBILITY")
            print(f"="*60)

            # Test join query
            join_query = f"""
            SELECT
                c.application,
                c.environment,
                COUNT(*) as cost_records,
                COUNT(DISTINCT c.date) as cost_days,
                SUM(c.cost) as total_cost
            FROM `{client.project}.{dataset_id}.cost_analysis` c
            GROUP BY c.application, c.environment
            ORDER BY total_cost DESC
            LIMIT 5
            """

            join_result = run_sample_query(
                client,
                join_query,
                "Testing cost_analysis aggregation"
            )

            if join_result['success']:
                print(f"✓ Cost analysis aggregation successful")
                for row in join_result['rows']:
                    print(f"  {row}")
            else:
                print(f"❌ Join test failed: {join_result['error']}")

        # Expected vs Actual State Summary
        print(f"\n" + "="*80)
        print(f"📊 EXPECTED vs ACTUAL STATE SUMMARY")
        print(f"="*80)

        print(f"\n🎯 COST_ANALYSIS TABLE:")
        if 'cost_analysis' in table_names:
            cost_schema = get_table_schema(client, dataset_id, 'cost_analysis')
            if 'fields' in cost_schema:
                print(f"✓ Expected: 13 fields | Actual: {len(cost_schema['fields'])} fields")

                expected_cost_fields = [
                    'date', 'cloud', 'application', 'environment', 'managed_service',
                    'cost', 'tr_product_pillar_team', 'cto', 'apm_id'
                ]

                actual_fields = [f['name'] for f in cost_schema['fields']]
                print(f"✓ Field names: {actual_fields}")

                # Check for apm_id field
                if 'apm_id' in actual_fields:
                    print(f"✓ apm_id field exists")
                else:
                    print(f"❌ apm_id field missing")

                print(f"✓ Total rows: {cost_schema['num_rows']:,}")
        else:
            print(f"❌ cost_analysis table does not exist")

        print(f"\n🎯 BUDGET_ANALYSIS TABLE:")
        if 'budget_analysis' in table_names:
            budget_schema = get_table_schema(client, dataset_id, 'budget_analysis')
            if 'fields' in budget_schema:
                print(f"✓ Expected: 10 fields | Actual: {len(budget_schema['fields'])} fields")

                actual_fields = [f['name'] for f in budget_schema['fields']]
                print(f"✓ Field names: {actual_fields}")

                # Check for incorrect fields
                incorrect_fields = ['budget_id', 'budget_name']
                has_incorrect = any(field in actual_fields for field in incorrect_fields)

                if has_incorrect:
                    print(f"❌ Found incorrect fields: {[f for f in incorrect_fields if f in actual_fields]}")
                else:
                    print(f"✓ No incorrect budget_id/budget_name fields found")

                print(f"✓ Total rows: {budget_schema['num_rows']:,}")
        else:
            print(f"❌ budget_analysis table does not exist")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

    print(f"\n✅ Verification completed successfully!")
    return True

if __name__ == "__main__":
    verify_tables()