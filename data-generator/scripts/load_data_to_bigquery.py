#!/usr/bin/env python3
"""
Load cost analysis data to BigQuery
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "langchain-backend" / ".env")

def create_dataset_and_tables():
    """Create BigQuery dataset and load data"""
    
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET", "agent_bq_dataset")
    
    print(f"Project ID: {project_id}")
    print(f"Dataset ID: {dataset_id}")
    
    # Initialize BigQuery client
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        credentials_path = os.path.expanduser(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
        if os.path.exists(credentials_path):
            print(f"Using service account from: {credentials_path}")
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
        else:
            print("Using service account from environment variable")
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(os.getenv("GCP_SERVICE_ACCOUNT_KEY"))
            )
    else:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(os.getenv("GCP_SERVICE_ACCOUNT_KEY"))
        )
    
    client = bigquery.Client(credentials=credentials, project=project_id)
    
    # Create dataset if it doesn't exist
    dataset_ref = client.dataset(dataset_id)
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "US"
    dataset.description = "Cloud cost analytics data"
    
    try:
        dataset = client.create_dataset(dataset, exists_ok=True)
        print(f"✅ Dataset {dataset_id} created/verified")
    except Exception as e:
        print(f"❌ Error creating dataset: {e}")
        return False
    
    # Load cost_analysis data
    csv_file = Path(__file__).parent / "cost_analysis_new.csv"
    
    if not csv_file.exists():
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    print(f"Loading data from: {csv_file}")
    
    # Read CSV
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} rows from CSV")
    
    # Convert date column to datetime and then to date only
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    # Define table schema - Updated with apm_id field (13 total fields)
    # Application Hierarchy: cto -> tr_product_pillar_team -> tr_subpillar_name -> tr_product_id -> apm_id -> application
    schema = [
        bigquery.SchemaField("date", "DATE"),
        bigquery.SchemaField("cto", "STRING"),
        bigquery.SchemaField("cloud", "STRING"),
        bigquery.SchemaField("tr_product_pillar_team", "STRING"),
        bigquery.SchemaField("tr_subpillar_name", "STRING"),
        bigquery.SchemaField("tr_product_id", "STRING"),
        bigquery.SchemaField("tr_product", "STRING"),
        bigquery.SchemaField("apm_id", "STRING"),  # NEW: Application Performance Management identifier
        bigquery.SchemaField("application", "STRING"),
        bigquery.SchemaField("service_name", "STRING"),
        bigquery.SchemaField("managed_service", "STRING"),
        bigquery.SchemaField("environment", "STRING"),
        bigquery.SchemaField("cost", "FLOAT64"),
    ]
    
    # Create table and load data
    table_id = f"{project_id}.{dataset_id}.cost_analysis"
    
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_TRUNCATE",  # Replace table if exists
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,  # Skip header row
    )
    
    try:
        # Load data from DataFrame
        job = client.load_table_from_dataframe(
            df, table_id, job_config=job_config
        )
        job.result()  # Wait for job to complete
        
        print(f"✅ Loaded {job.output_rows} rows to {table_id}")
        
        # Verify the data
        query = f"SELECT COUNT(*) as count FROM `{table_id}`"
        result = list(client.query(query).result())
        print(f"✅ Verified: Table contains {result[0].count} rows")
        
        # Show sample data
        query = f"SELECT * FROM `{table_id}` LIMIT 5"
        results = client.query(query).result()
        
        print("\nSample data:")
        for row in results:
            print(f"  {row.date}, {row.application}, ${row.cost:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False

def create_views():
    """Create BigQuery views for easier querying"""
    
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET", "agent_bq_dataset")
    
    # Initialize BigQuery client
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        credentials_path = os.path.expanduser(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
        if os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
        else:
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(os.getenv("GCP_SERVICE_ACCOUNT_KEY"))
            )
    else:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(os.getenv("GCP_SERVICE_ACCOUNT_KEY"))
        )
    
    client = bigquery.Client(credentials=credentials, project=project_id)
    
    # Create daily summary view
    view_id = f"{project_id}.{dataset_id}.daily_cost_summary"
    view_query = f"""
    SELECT 
      DATE(date) as cost_date,
      SUM(cost) as total_daily_cost,
      AVG(cost) as avg_cost_per_entry,
      COUNT(DISTINCT application) as active_applications,
      COUNT(DISTINCT cloud) as clouds_used,
      STRING_AGG(DISTINCT environment, ', ' ORDER BY environment) as environments
    FROM `{project_id}.{dataset_id}.cost_analysis`
    GROUP BY cost_date
    ORDER BY cost_date DESC
    """
    
    view = bigquery.Table(view_id)
    view.view_query = view_query
    
    try:
        view = client.create_table(view, exists_ok=True)
        print(f"✅ Created view: daily_cost_summary")
    except Exception as e:
        print(f"⚠️  Error creating view: {e}")
    
    # Create application summary view
    view_id = f"{project_id}.{dataset_id}.application_cost_summary"
    view_query = f"""
    WITH current_period AS (
      SELECT 
        application,
        SUM(cost) as current_month_cost,
        AVG(cost) as avg_daily_cost,
        COUNT(DISTINCT DATE(date)) as active_days
      FROM `{project_id}.{dataset_id}.cost_analysis`
      WHERE DATE(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
      GROUP BY application
    )
    SELECT 
      application,
      current_month_cost,
      avg_daily_cost,
      active_days
    FROM current_period
    ORDER BY current_month_cost DESC
    """
    
    view = bigquery.Table(f"{project_id}.{dataset_id}.application_cost_summary")
    view.view_query = view_query
    
    try:
        view = client.create_table(view, exists_ok=True)
        print(f"✅ Created view: application_cost_summary")
    except Exception as e:
        print(f"⚠️  Error creating view: {e}")
    
    return True

def main():
    """Main function"""
    print("\n🚀 Loading Cost Analysis Data to BigQuery\n")
    print("=" * 60)
    
    # Create dataset and load data
    success = create_dataset_and_tables()
    
    if success:
        print("\n" + "=" * 60)
        print("Creating views...")
        create_views()
        
        print("\n" + "=" * 60)
        print("✅ Data loaded successfully!")
        print("\nYou can now:")
        print("1. Run the backend: cd langchain-backend && python main.py")
        print("2. Test queries with: python test_connection.py")
        print("3. Access the chatbot at: http://localhost:3000")
    else:
        print("\n❌ Failed to load data. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()