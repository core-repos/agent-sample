#!/usr/bin/env python3
"""
BigQuery Setup Script - Creates sample agent_bq_dataset dataset and tables
Now includes budget table creation and integration with fiscal year structure
Updated with apm_id field in application hierarchy
"""

import os
import sys
from datetime import datetime, timedelta, date
import random
from google.cloud import bigquery
from google.cloud.exceptions import Conflict
import pandas as pd
import numpy as np
import json
from dateutil.relativedelta import relativedelta

# Configuration - Use environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'gac-prod-471220')
DATASET_ID = os.getenv('BQ_DATASET', 'agent_bq_dataset')
COST_TABLE_ID = "cost_analysis"
BUDGET_TABLE_ID = "budget_analysis"

# Set credentials - use service account key from environment or default location
service_account_key = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/Users/gurukallam/.gcp/genai-community/service-account-key.json')
if os.path.exists(service_account_key):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_key
    print(f"🔑 Using service account: {service_account_key}")
elif os.path.exists(os.path.expanduser("~/.config/gcloud/application_default_credentials.json")):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expanduser(
        "~/.config/gcloud/application_default_credentials.json"
    )
    print("🔑 Using default gcloud credentials")

def create_dataset(client, dataset_id):
    """Create BigQuery dataset if it doesn't exist"""
    dataset_ref = f"{client.project}.{dataset_id}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "US"
    dataset.description = "Cost analytics and budget management data for cloud infrastructure"

    try:
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"✅ Created dataset {client.project}.{dataset_id}")
        return True
    except Conflict:
        print(f"ℹ️  Dataset {client.project}.{dataset_id} already exists")
        return False

def delete_table_if_exists(client, dataset_id, table_id):
    """Delete table if it exists"""
    table_ref = f"{client.project}.{dataset_id}.{table_id}"
    try:
        client.get_table(table_ref)
        client.delete_table(table_ref)
        print(f"🗑️  Deleted existing table {table_ref}")
        return True
    except:
        print(f"ℹ️  Table {table_ref} doesn't exist, will create new")
        return False

def create_cost_table_schema():
    """Define the updated schema for cost_analysis table with apm_id field"""
    schema = [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("cto", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("cloud", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tr_product_pillar_team", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("tr_subpillar_name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("tr_product_id", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("tr_product", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("apm_id", "STRING", mode="NULLABLE"),  # NEW FIELD
        bigquery.SchemaField("application", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("service_name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("managed_service", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("environment", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("cost", "FLOAT", mode="REQUIRED"),
    ]
    return schema

def create_budget_table_schema():
    """Define the schema for budget_analysis table"""
    schema_file = os.path.join(os.path.dirname(__file__), '..', 'schema', 'budget_schema.json')

    with open(schema_file, 'r') as f:
        schema_data = json.load(f)

    schema = []
    for field in schema_data:
        mode = field.get('mode', 'NULLABLE')
        schema.append(bigquery.SchemaField(field['name'], field['type'], mode=mode, description=field.get('description', '')))

    return schema

def generate_apm_hierarchy(teams, ctos):
    """Generate APM hierarchy mapping for consistent relationships"""
    apm_hierarchy = {}

    # Define APM ID patterns by team category
    apm_patterns = {
        "ENTERPRISE FINANCE TECH": ["APM-FIN", "APM-EXP", "APM-INV", "APM-BUD", "APM-CST"],
        "PLATFORM ENGINEERING": ["APM-PLT", "APM-DEP", "APM-MON", "APM-LOG", "APM-CNT"],
        "DATA ANALYTICS": ["APM-DAT", "APM-ANL", "APM-RPT", "APM-MLT", "APM-DWH"],
        "SECURITY OPERATIONS": ["APM-SEC", "APM-THR", "APM-CMP", "APM-IDM", "APM-SCN"],
        "CUSTOMER PLATFORM": ["APM-CUS", "APM-USR", "APM-NOT", "APM-CAL", "APM-SUP"],
        "PAYMENT SYSTEMS": ["APM-PAY", "APM-FRD", "APM-TXN", "APM-GTW", "APM-BIL"],
        "ML PLATFORM": ["APM-ML", "APM-INF", "APM-FST", "APM-OPS", "APM-EXP"],
        "INFRASTRUCTURE SERVICES": ["APM-INF", "APM-STO", "APM-NET", "APM-BAK", "APM-DR"]
    }

    # Applications grouped by APM category
    apm_applications = {
        "FIN": ["financial-portal", "expense-tracker", "invoice-processor", "budget-planner"],
        "EXP": ["expense-management", "receipt-scanner", "approval-workflow", "cost-tracker"],
        "INV": ["invoice-service", "billing-automation", "payment-processor", "vendor-portal"],
        "BUD": ["budget-service", "forecasting-engine", "cost-analytics", "planning-tool"],
        "CST": ["cost-analyzer", "spend-optimizer", "budget-alerts", "cost-dashboard"],
        "PLT": ["platform-core", "infrastructure-api", "resource-manager", "deployment-service"],
        "DEP": ["ci-cd-pipeline", "deployment-automation", "release-manager", "artifact-store"],
        "MON": ["monitoring-stack", "alerting-service", "metrics-collector", "dashboard-service"],
        "LOG": ["logging-service", "log-aggregator", "search-service", "audit-logger"],
        "CNT": ["container-registry", "orchestration-service", "image-scanner", "runtime-service"],
        "DAT": ["data-pipeline", "etl-service", "data-lake", "streaming-processor"],
        "ANL": ["analytics-engine", "query-processor", "data-explorer", "insight-generator"],
        "RPT": ["reporting-platform", "dashboard-builder", "export-service", "scheduler"],
        "MLT": ["ml-platform", "model-training", "inference-engine", "feature-store"],
        "DWH": ["data-warehouse", "olap-service", "cube-processor", "metadata-service"],
        "SEC": ["security-scanner", "vulnerability-service", "compliance-checker", "audit-service"],
        "THR": ["threat-detector", "anomaly-service", "incident-responder", "forensics-tool"],
        "CMP": ["compliance-platform", "policy-engine", "assessment-tool", "reporting-service"],
        "IDM": ["identity-service", "auth-gateway", "user-manager", "token-service"],
        "SCN": ["security-analytics", "log-analyzer", "behavior-monitor", "risk-assessor"],
        "CUS": ["customer-portal", "profile-service", "preference-manager", "activity-tracker"],
        "USR": ["user-service", "registration-service", "profile-api", "authentication-service"],
        "NOT": ["notification-service", "email-service", "sms-gateway", "push-service"],
        "CAL": ["customer-analytics", "behavior-tracker", "segmentation-service", "insights-engine"],
        "SUP": ["support-platform", "ticket-system", "knowledge-base", "chat-service"],
        "PAY": ["payment-gateway", "transaction-processor", "settlement-service", "reconciliation-tool"],
        "FRD": ["fraud-detector", "risk-analyzer", "pattern-matcher", "score-calculator"],
        "TXN": ["transaction-monitor", "audit-trail", "compliance-checker", "reporting-service"],
        "GTW": ["api-gateway", "payment-router", "protocol-adapter", "rate-limiter"],
        "BIL": ["billing-service", "invoice-generator", "subscription-manager", "pricing-engine"],
        "ML": ["model-service", "training-pipeline", "experiment-tracker", "version-manager"],
        "INF": ["inference-service", "prediction-api", "batch-processor", "real-time-scorer"],
        "FST": ["feature-store", "feature-pipeline", "serving-layer", "metadata-manager"],
        "OPS": ["mlops-platform", "model-monitor", "drift-detector", "performance-tracker"],
        "EXP": ["experiment-platform", "ab-testing", "variant-manager", "results-analyzer"],
        "STO": ["storage-service", "backup-manager", "archive-service", "replication-tool"],
        "NET": ["network-service", "load-balancer", "proxy-service", "dns-manager"],
        "BAK": ["backup-service", "restore-manager", "snapshot-service", "recovery-tool"],
        "DR": ["disaster-recovery", "failover-service", "replication-manager", "backup-orchestrator"]
    }

    product_id_counter = 700

    for team in teams:
        if team not in apm_patterns:
            continue

        patterns = apm_patterns[team]

        # Generate 3-5 products per team
        num_products = random.randint(3, 5)

        for i in range(num_products):
            pattern = random.choice(patterns)

            # Extract category from pattern (e.g., "APM-FIN" -> "FIN")
            category = pattern.split('-')[1]

            # Generate 2-4 APM IDs per product
            num_apm_ids = random.randint(2, 4)

            for j in range(num_apm_ids):
                apm_id = f"{pattern}-{j+1:03d}"

                # Get applications for this APM category
                apps = apm_applications.get(category, ["web-app", "api-service", "worker-service", "data-processor"])

                # Select 2-3 applications per APM ID
                num_apps = random.randint(2, 3)
                selected_apps = random.sample(apps, min(num_apps, len(apps)))

                if product_id_counter not in apm_hierarchy:
                    apm_hierarchy[product_id_counter] = {}

                apm_hierarchy[product_id_counter][apm_id] = selected_apps

            product_id_counter += 1

    return apm_hierarchy

def generate_sample_data(num_days=90, records_per_day=120):
    """Generate sample cost data with updated schema including apm_id"""
    print(f"📊 Generating sample data: {num_days} days × {records_per_day} records/day...")

    # Sample data pools
    clouds = ["AWS", "Azure", "GCP"]
    cloud_weights = [0.5, 0.3, 0.2]  # AWS has more usage

    environments = ["PROD", "NON-PROD"]
    env_weights = [0.7, 0.3]  # More production costs

    services = {
        "AWS": ["EC2", "RDS", "S3", "Lambda", "EKS", "CloudFront", "DynamoDB", "ElastiCache", "Redshift", "SQS"],
        "Azure": ["Virtual Machines", "SQL Database", "Blob Storage", "Functions", "AKS", "CDN", "Cosmos DB", "Redis Cache"],
        "GCP": ["Compute Engine", "Cloud SQL", "Cloud Storage", "Cloud Functions", "GKE", "Cloud CDN", "Firestore", "Memorystore"]
    }

    # Service name variations based on managed service
    service_names = {
        "EC2": ["web-server", "app-server", "worker-node", "database-server", "cache-server"],
        "RDS": ["primary-db", "replica-db", "analytics-db", "backup-db"],
        "S3": ["data-lake", "backup-storage", "static-assets", "log-storage"],
        "Lambda": ["data-processor", "webhook-handler", "scheduler", "api-function"],
        "EKS": ["prod-cluster", "staging-cluster", "dev-cluster"],
        "Virtual Machines": ["web-vm", "app-vm", "db-vm", "cache-vm"],
        "SQL Database": ["primary-sql", "replica-sql", "analytics-sql"],
        "Blob Storage": ["data-blob", "backup-blob", "media-blob"],
        "Functions": ["trigger-func", "processor-func", "api-func"],
        "Compute Engine": ["web-instance", "app-instance", "worker-instance"],
        "Cloud SQL": ["main-sql", "read-replica", "analytics-sql"],
        "Cloud Storage": ["data-bucket", "backup-bucket", "static-bucket"],
        "Cloud Functions": ["event-handler", "data-processor", "api-endpoint"]
    }

    teams = ["ENTERPRISE FINANCE TECH", "PLATFORM ENGINEERING", "DATA ANALYTICS", "SECURITY OPERATIONS",
             "CUSTOMER PLATFORM", "PAYMENT SYSTEMS", "ML PLATFORM", "INFRASTRUCTURE SERVICES"]
    ctos = ["Engineering", "Data & Analytics", "Security & Compliance", "Operations"]

    # Sub-pillars for each team
    sub_pillars = {
        "ENTERPRISE FINANCE TECH": ["ENTERPRISE FINANCE TECH", "FINANCIAL REPORTING", "EXPENSE MANAGEMENT"],
        "PLATFORM ENGINEERING": ["PLATFORM CORE", "DEPLOYMENT SERVICES", "MONITORING PLATFORM"],
        "DATA ANALYTICS": ["DATA PLATFORM", "ANALYTICS SERVICES", "ML INFRASTRUCTURE"],
        "SECURITY OPERATIONS": ["SECURITY CORE", "COMPLIANCE PLATFORM", "THREAT MANAGEMENT"],
        "CUSTOMER PLATFORM": ["CUSTOMER SERVICES", "USER EXPERIENCE", "SUPPORT PLATFORM"],
        "PAYMENT SYSTEMS": ["PAYMENT CORE", "FRAUD PREVENTION", "BILLING SERVICES"],
        "ML PLATFORM": ["ML CORE", "MODEL SERVICES", "EXPERIMENTATION"],
        "INFRASTRUCTURE SERVICES": ["COMPUTE PLATFORM", "STORAGE SERVICES", "NETWORK PLATFORM"]
    }

    # Products for each team
    products = {
        "ENTERPRISE FINANCE TECH": ["financial reporting", "expense management", "invoice processing", "budget planning", "cost analytics"],
        "PLATFORM ENGINEERING": ["infrastructure platform", "deployment automation", "monitoring services", "logging platform", "container platform"],
        "DATA ANALYTICS": ["data pipeline", "analytics engine", "reporting platform", "ml platform", "data warehouse"],
        "SECURITY OPERATIONS": ["security monitoring", "threat detection", "compliance platform", "identity management", "security analytics"],
        "CUSTOMER PLATFORM": ["customer portal", "user management", "notification service", "customer analytics", "support platform"],
        "PAYMENT SYSTEMS": ["payment processing", "fraud detection", "transaction monitoring", "payment gateway", "billing system"],
        "ML PLATFORM": ["model training", "inference engine", "feature store", "ml ops platform", "experimentation platform"],
        "INFRASTRUCTURE SERVICES": ["compute services", "storage platform", "network services", "backup services", "disaster recovery"]
    }

    # Generate APM hierarchy
    print("🔗 Generating APM hierarchy...")
    apm_hierarchy = generate_apm_hierarchy(teams, ctos)

    # Flatten hierarchy for easier access during data generation
    product_apm_mapping = {}
    for product_id, apm_dict in apm_hierarchy.items():
        product_apm_mapping[product_id] = []
        for apm_id, apps in apm_dict.items():
            for app in apps:
                product_apm_mapping[product_id].append((apm_id, app))

    # Generate data
    data = []
    end_date = datetime.now().date()

    for day_offset in range(num_days):
        current_date = end_date - timedelta(days=day_offset)

        for _ in range(records_per_day):
            cloud = np.random.choice(clouds, p=cloud_weights)
            environment = np.random.choice(environments, p=env_weights)
            team = random.choice(teams)
            cto = random.choice(ctos)
            sub_pillar = random.choice(sub_pillars[team])
            product = random.choice(products[team])
            managed_service = random.choice(services[cloud])

            # Generate service name based on managed service
            service_name_options = service_names.get(managed_service, ["service-instance"])
            service_name = random.choice(service_name_options)

            # Select a product_id that has APM mapping
            available_product_ids = list(product_apm_mapping.keys())
            if available_product_ids:
                product_id = random.choice(available_product_ids)

                # Select an APM ID and application from the hierarchy
                apm_app_pairs = product_apm_mapping[product_id]
                if apm_app_pairs:
                    apm_id, application = random.choice(apm_app_pairs)
                else:
                    apm_id = "APM-GEN-001"
                    application = "default-application"
            else:
                product_id = 700 + random.randint(0, 50)
                apm_id = "APM-GEN-001"
                application = "default-application"

            # Cost varies by environment and service
            if environment == "PROD":
                base_cost = random.uniform(10, 5000)
            else:
                base_cost = random.uniform(5, 1000)

            # Add some realistic patterns
            # Higher costs during business hours (simplified)
            hour_factor = 1.0 + (0.3 * abs(random.gauss(0, 1)))

            # Weekly pattern - weekends are cheaper
            if current_date.weekday() >= 5:
                weekend_factor = 0.7
            else:
                weekend_factor = 1.0

            # Monthly pattern - end of month higher (reports, processing)
            if current_date.day > 25:
                month_end_factor = 1.2
            else:
                month_end_factor = 1.0

            final_cost = base_cost * hour_factor * weekend_factor * month_end_factor

            # Add some outliers (5% chance of spike)
            if random.random() < 0.05:
                final_cost *= random.uniform(2, 5)

            record = {
                "date": current_date,
                "cto": cto,
                "cloud": cloud,
                "tr_product_pillar_team": team,
                "tr_subpillar_name": sub_pillar,
                "tr_product_id": product_id,
                "tr_product": product,
                "apm_id": apm_id,  # NEW FIELD
                "application": application,
                "service_name": service_name,
                "managed_service": managed_service,
                "environment": environment,
                "cost": round(final_cost, 2),
            }
            data.append(record)

    df = pd.DataFrame(data)
    print(f"✅ Generated {len(df)} records")

    # Show sample statistics
    print("\n📈 Sample Data Statistics:")
    print(f"  • Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  • Total cost: ${df['cost'].sum():,.2f}")
    print(f"  • Average daily cost: ${df.groupby('date')['cost'].sum().mean():,.2f}")
    print(f"  • Cost by cloud:")
    for cloud in clouds:
        cloud_cost = df[df['cloud'] == cloud]['cost'].sum()
        print(f"    - {cloud}: ${cloud_cost:,.2f} ({cloud_cost/df['cost'].sum()*100:.1f}%)")
    print(f"  • Teams represented: {df['tr_product_pillar_team'].nunique()}")
    print(f"  • CTOs represented: {df['cto'].nunique()}")
    print(f"  • Products represented: {df['tr_product'].nunique()}")
    print(f"  • APM IDs represented: {df['apm_id'].nunique()}")
    print(f"  • Applications represented: {df['application'].nunique()}")

    # Show APM hierarchy sample
    print(f"\n🔗 APM Hierarchy Sample:")
    sample_hierarchy = df.groupby(['tr_product_id', 'apm_id', 'application']).size().reset_index(name='record_count').head(10)
    for _, row in sample_hierarchy.iterrows():
        print(f"    • Product {row['tr_product_id']} → {row['apm_id']} → {row['application']} ({row['record_count']} records)")

    return df

def generate_budget_data(cost_df):
    """Generate realistic budget data based on fiscal year structure"""
    print("\n💰 Generating budget data with fiscal year structure...")

    # Get teams from cost data
    teams = cost_df['tr_product_pillar_team'].unique()
    ctos = cost_df['cto'].unique()

    # Product types and services for each team
    product_categories = {
        "ENTERPRISE FINANCE TECH": ["financial reporting", "expense management", "invoice processing", "budget planning", "cost analytics"],
        "PLATFORM ENGINEERING": ["infrastructure platform", "deployment automation", "monitoring services", "logging platform", "container platform"],
        "DATA ANALYTICS": ["data pipeline", "analytics engine", "reporting platform", "ml platform", "data warehouse"],
        "SECURITY OPERATIONS": ["security monitoring", "threat detection", "compliance platform", "identity management", "security analytics"],
        "CUSTOMER PLATFORM": ["customer portal", "user management", "notification service", "customer analytics", "support platform"],
        "PAYMENT SYSTEMS": ["payment processing", "fraud detection", "transaction monitoring", "payment gateway", "billing system"],
        "ML PLATFORM": ["model training", "inference engine", "feature store", "ml ops platform", "experimentation platform"],
        "INFRASTRUCTURE SERVICES": ["compute services", "storage platform", "network services", "backup services", "disaster recovery"]
    }

    sub_pillars = {
        "ENTERPRISE FINANCE TECH": ["ENTERPRISE FINANCE TECH", "FINANCIAL REPORTING", "EXPENSE MANAGEMENT"],
        "PLATFORM ENGINEERING": ["PLATFORM CORE", "DEPLOYMENT SERVICES", "MONITORING PLATFORM"],
        "DATA ANALYTICS": ["DATA PLATFORM", "ANALYTICS SERVICES", "ML INFRASTRUCTURE"],
        "SECURITY OPERATIONS": ["SECURITY CORE", "COMPLIANCE PLATFORM", "THREAT MANAGEMENT"],
        "CUSTOMER PLATFORM": ["CUSTOMER SERVICES", "USER EXPERIENCE", "SUPPORT PLATFORM"],
        "PAYMENT SYSTEMS": ["PAYMENT CORE", "FRAUD PREVENTION", "BILLING SERVICES"],
        "ML PLATFORM": ["ML CORE", "MODEL SERVICES", "EXPERIMENTATION"],
        "INFRASTRUCTURE SERVICES": ["COMPUTE PLATFORM", "STORAGE SERVICES", "NETWORK PLATFORM"]
    }

    budget_data = []
    product_id_counter = 700  # Starting from 700 to match sample data

    for team in teams:
        team_costs = cost_df[cost_df['tr_product_pillar_team'] == team]
        if len(team_costs) == 0:
            continue

        # Calculate team's spending patterns
        monthly_avg_cost = team_costs['cost'].sum() / 3  # Roughly 3 months of data
        annual_cost_base = monthly_avg_cost * 12

        # Generate 3-5 products per team
        num_products = random.randint(3, 5)
        products = random.sample(product_categories.get(team, ["service", "platform", "tool"]),
                                min(num_products, len(product_categories.get(team, ["service"]))))

        team_cto = team_costs['cto'].iloc[0] if len(team_costs) > 0 else random.choice(ctos)

        for i, product in enumerate(products):
            # Distribute costs across products (some products are more expensive)
            if i == 0:  # Primary product gets more budget
                product_cost_ratio = random.uniform(0.3, 0.5)
            else:
                product_cost_ratio = random.uniform(0.1, 0.3)

            base_annual_cost = annual_cost_base * product_cost_ratio

            # Generate budgets with some growth/decline patterns
            fy24_budget = base_annual_cost * random.uniform(0.8, 1.2)
            fy25_budget = fy24_budget * random.uniform(0.9, 1.3)  # Some growth/decline
            fy26_budget = fy25_budget * random.uniform(0.95, 1.25)  # Continued evolution

            # FY26 YTD spend (assuming we're partway through FY26)
            # Assume FY26 started 4 months ago (random progress)
            fy26_progress = random.uniform(0.25, 0.75)  # 25-75% through the year
            fy26_ytd_spend = fy26_budget * fy26_progress * random.uniform(0.7, 1.1)  # Some variance

            # FY26 projected spend based on current burn rate
            if fy26_progress > 0:
                monthly_burn = fy26_ytd_spend / (fy26_progress * 12)
                fy26_projected_spend = monthly_burn * 12 * random.uniform(0.9, 1.15)
            else:
                fy26_projected_spend = fy26_budget * random.uniform(0.85, 1.05)

            # Select sub-pillar
            sub_pillar = random.choice(sub_pillars.get(team, [team]))

            budget_record = {
                "cto": team_cto,
                "tr_product_pillar_team": team,
                "tr_subpillar_name": sub_pillar,
                "tr_product_id": product_id_counter,
                "tr_product": product,
                "fy_24_budget": round(fy24_budget, 2),
                "fy_25_budget": round(fy25_budget, 2),
                "fy_26_budget": round(fy26_budget, 2),
                "fy26_ytd_spend": round(fy26_ytd_spend, 2),
                "fy26_projected_spend": round(fy26_projected_spend, 2)
            }
            budget_data.append(budget_record)
            product_id_counter += 1

    budget_df = pd.DataFrame(budget_data)
    print(f"✅ Generated {len(budget_df)} budget records")

    # Show budget statistics
    print("\n💰 Budget Data Statistics:")
    print(f"  • Total FY24 budget: ${budget_df['fy_24_budget'].sum():,.2f}")
    print(f"  • Total FY25 budget: ${budget_df['fy_25_budget'].sum():,.2f}")
    print(f"  • Total FY26 budget: ${budget_df['fy_26_budget'].sum():,.2f}")
    print(f"  • Total FY26 YTD spend: ${budget_df['fy26_ytd_spend'].sum():,.2f}")
    print(f"  • Total FY26 projected spend: ${budget_df['fy26_projected_spend'].sum():,.2f}")
    print(f"  • Average FY26 utilization: {(budget_df['fy26_ytd_spend'].sum() / budget_df['fy_26_budget'].sum() * 100):.1f}%")
    print(f"  • CTOs represented: {budget_df['cto'].nunique()}")
    print(f"  • Teams represented: {budget_df['tr_product_pillar_team'].nunique()}")

    return budget_df

def upload_to_bigquery(client, dataset_id, table_id, df, schema):
    """Upload DataFrame to BigQuery"""
    table_ref = f"{client.project}.{dataset_id}.{table_id}"

    # Configure job
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_TRUNCATE",  # Replace table if exists
    )

    try:
        print(f"\n📤 Uploading data to {table_ref}...")
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()  # Wait for job to complete

        # Verify upload
        table = client.get_table(table_ref)
        print(f"✅ Uploaded {table.num_rows} rows to {table_ref}")
        return True
    except Exception as e:
        print(f"❌ Error uploading data: {e}")
        return False

def verify_data(client, dataset_id):
    """Run sample queries to verify data including apm_id field"""
    print("\n🔍 Verifying data with sample queries...")

    queries = [
        ("Cost Analysis - Total cost", f"SELECT SUM(cost) as total FROM `{client.project}.{dataset_id}.{COST_TABLE_ID}`"),
        ("Cost Analysis - Record count", f"SELECT COUNT(*) as count FROM `{client.project}.{dataset_id}.{COST_TABLE_ID}`"),
        ("Budget Analysis - Total FY26 budget", f"SELECT SUM(fy_26_budget) as total FROM `{client.project}.{dataset_id}.{BUDGET_TABLE_ID}`"),
        ("Budget Analysis - Record count", f"SELECT COUNT(*) as count FROM `{client.project}.{dataset_id}.{BUDGET_TABLE_ID}`"),
        ("Cost Analysis - APM hierarchy verification", f"""
            SELECT
                cto,
                tr_product_pillar_team,
                tr_subpillar_name,
                tr_product_id,
                tr_product,
                apm_id,
                application,
                COUNT(*) as record_count,
                SUM(cost) as total_cost
            FROM `{client.project}.{dataset_id}.{COST_TABLE_ID}`
            GROUP BY cto, tr_product_pillar_team, tr_subpillar_name, tr_product_id, tr_product, apm_id, application
            ORDER BY total_cost DESC
            LIMIT 5
        """),
        ("APM ID statistics", f"""
            SELECT
                apm_id,
                COUNT(DISTINCT application) as app_count,
                COUNT(DISTINCT tr_product_id) as product_count,
                SUM(cost) as total_cost
            FROM `{client.project}.{dataset_id}.{COST_TABLE_ID}`
            GROUP BY apm_id
            ORDER BY total_cost DESC
            LIMIT 10
        """),
        ("Application hierarchy by APM", f"""
            SELECT
                tr_product_id,
                apm_id,
                application,
                COUNT(*) as record_count,
                SUM(cost) as total_cost
            FROM `{client.project}.{dataset_id}.{COST_TABLE_ID}`
            GROUP BY tr_product_id, apm_id, application
            ORDER BY tr_product_id, apm_id, total_cost DESC
            LIMIT 10
        """),
        ("Budget vs Cost - Team comparison", f"""
            SELECT
                b.tr_product_pillar_team,
                b.cto,
                SUM(b.fy_26_budget) as fy26_budget,
                SUM(b.fy26_ytd_spend) as ytd_spend,
                SUM(b.fy26_projected_spend) as projected_spend,
                ROUND(SUM(b.fy26_ytd_spend) / SUM(b.fy_26_budget) * 100, 2) as ytd_utilization_pct,
                COALESCE(c.actual_cost, 0) as recent_cost_data
            FROM `{client.project}.{dataset_id}.{BUDGET_TABLE_ID}` b
            LEFT JOIN (
                SELECT
                    tr_product_pillar_team,
                    SUM(cost) as actual_cost
                FROM `{client.project}.{dataset_id}.{COST_TABLE_ID}`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY tr_product_pillar_team
            ) c ON b.tr_product_pillar_team = c.tr_product_pillar_team
            GROUP BY b.tr_product_pillar_team, b.cto, c.actual_cost
            ORDER BY ytd_utilization_pct DESC
            LIMIT 5
        """),
        ("Over-budget products (FY26)", f"""
            SELECT
                tr_product_pillar_team,
                tr_product,
                fy_26_budget,
                fy26_projected_spend,
                ROUND((fy26_projected_spend - fy_26_budget), 2) as projected_overspend,
                ROUND((fy26_projected_spend / fy_26_budget * 100), 2) as projected_utilization_pct
            FROM `{client.project}.{dataset_id}.{BUDGET_TABLE_ID}`
            WHERE fy26_projected_spend > fy_26_budget
            ORDER BY projected_overspend DESC
            LIMIT 5
        """)
    ]

    for name, query in queries:
        try:
            result = client.query(query).result()
            print(f"\n  ✅ {name}:")
            for row in result:
                print(f"     {dict(row)}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 BigQuery Setup Script for ADK-Agents")
    print("📊 Cost Analytics + Fiscal Year Budget Management")
    print("🔄 Updated Cost Schema with APM ID Field")
    print("🔗 Application Hierarchy: CTO → Team → Sub-pillar → Product → APM → App")
    print("=" * 60)

    try:
        # Initialize client
        print(f"\n📌 Project: {PROJECT_ID}")
        client = bigquery.Client(project=PROJECT_ID)
        print("✅ Connected to BigQuery")

        # Create dataset
        create_dataset(client, DATASET_ID)

        # Delete existing cost table to ensure clean schema update
        print("\n" + "="*40)
        print("🗑️  STEP 1: Cleaning Existing Tables")
        print("="*40)
        delete_table_if_exists(client, DATASET_ID, COST_TABLE_ID)

        # Check if budget table exists
        budget_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{BUDGET_TABLE_ID}"
        budget_exists = False

        try:
            budget_table = client.get_table(budget_table_ref)
            budget_exists = True
            print(f"ℹ️  Budget table {budget_table_ref} exists with {budget_table.num_rows} rows")
        except:
            print(f"ℹ️  Budget table {budget_table_ref} doesn't exist, will create it")

        if budget_exists:
            response = input("\n❓ Do you want to replace existing budget data? (y/n): ").lower()
            if response != 'y':
                print("ℹ️  Keeping existing budget data")

        # Generate sample data
        print("\n" + "="*40)
        print("📊 STEP 2: Generating Cost Data (Updated Schema with APM ID)")
        print("="*40)
        cost_df = generate_sample_data(num_days=90, records_per_day=120)

        print("\n" + "="*40)
        print("💰 STEP 3: Generating Fiscal Year Budget Data")
        print("="*40)
        budget_df = generate_budget_data(cost_df)

        # Upload cost data
        print("\n" + "="*40)
        print("📤 STEP 4: Uploading to BigQuery")
        print("="*40)

        cost_success = upload_to_bigquery(
            client, DATASET_ID, COST_TABLE_ID, cost_df, create_cost_table_schema()
        )

        budget_success = True
        if not budget_exists or response == 'y':
            budget_success = upload_to_bigquery(
                client, DATASET_ID, BUDGET_TABLE_ID, budget_df, create_budget_table_schema()
            )
        else:
            print("ℹ️  Skipping budget table upload (keeping existing data)")

        if cost_success and budget_success:
            verify_data(client, DATASET_ID)

            print("\n" + "=" * 60)
            print("✅ Setup Complete!")
            print("=" * 60)
            print(f"\n📊 Your BigQuery dataset is ready:")
            print(f"   • Project: {PROJECT_ID}")
            print(f"   • Dataset: {DATASET_ID}")
            print(f"   • Cost Table: {COST_TABLE_ID} ({len(cost_df):,} records) - UPDATED SCHEMA WITH APM_ID")
            print(f"   • Budget Table: {BUDGET_TABLE_ID}")

            print(f"\n🔄 Updated Cost Schema Fields (13 total):")
            print("    • date (DATE)")
            print("    • cto (STRING)")
            print("    • cloud (STRING)")
            print("    • tr_product_pillar_team (STRING)")
            print("    • tr_subpillar_name (STRING)")
            print("    • tr_product_id (INTEGER)")
            print("    • tr_product (STRING)")
            print("    • apm_id (STRING) ⭐ NEW FIELD")
            print("    • application (STRING)")
            print("    • service_name (STRING)")
            print("    • managed_service (STRING)")
            print("    • environment (STRING)")
            print("    • cost (FLOAT)")

            print(f"\n🔗 Application Hierarchy:")
            print("    cto → tr_product_pillar_team → tr_subpillar_name → tr_product_id → apm_id → application")
            print("    • Each tr_product_id has multiple apm_id values")
            print("    • Each apm_id has multiple applications")
            print("    • APM IDs follow pattern: APM-[CATEGORY]-[NUMBER] (e.g., APM-FIN-001, APM-ML-002)")

            print(f"\n🎯 Example questions to try:")
            print("  💸 Cost Analysis:")
            print("    • What is the total cost?")
            print("    • Show me the top 10 applications by cost")
            print("    • What's the cost breakdown by environment?")
            print("    • Display the daily cost trend for last 30 days")
            print("    • Show cost by APM ID")
            print("    • What applications are under APM-FIN-001?")
            print("    • What's the cost breakdown by tr_subpillar_name?")

            print("  💰 Budget Analysis:")
            print("    • Show FY26 budget vs YTD spending by team")
            print("    • Which products are projected to go over budget?")
            print("    • What's the budget utilization by CTO organization?")
            print("    • Compare FY25 vs FY26 budget allocation")

            print("  📈 Combined Analysis:")
            print("    • Compare actual spending vs budget by team")
            print("    • Show teams with highest budget variance")
            print("    • What's the projected vs budgeted spending for FY26?")
            print("    • Join cost and budget data by tr_product_id")
            print("    • Show cost by APM ID and join with budget data")

            print("  🔗 APM Hierarchy Analysis:")
            print("    • Show applications grouped by APM ID")
            print("    • What's the cost distribution across APM categories?")
            print("    • Which APM IDs have the highest costs?")
            print("    • Show the full hierarchy from CTO to application")
        else:
            print("\n❌ Setup failed. Please check the errors above.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure you have:")
        print("  1. Google Cloud SDK installed")
        print("  2. Authenticated with: gcloud auth application-default login")
        print("  3. Proper permissions for BigQuery in your project")
        print("  4. dateutil package installed: pip install python-dateutil")
        sys.exit(1)

if __name__ == "__main__":
    main()