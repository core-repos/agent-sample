# Data Generator Directory

This directory contains data generation scripts and setup utilities for the BigQuery Analytics AI Agent.

## Directory Structure

```
data-generator/
├── data/                    # Generated datasets
│   └── cost_analysis_new.csv  # Generated cost analysis data (10,800 rows)
├── schema/                  # Database schemas
│   └── cost_analysis_schema.json  # BigQuery table schema
├── scripts/                 # Data generation and setup scripts
│   ├── setup_bigquery.py      # BigQuery setup automation
│   ├── load_data_to_bigquery.py  # Data loading script
│   └── create_cost_views.sql    # Cost analysis views
├── docs/                    # Documentation
│   └── setup_requirements.txt  # Requirements for setup scripts
└── README.md               # This file
```

## Quick Setup

### 1. Prerequisites
```bash
pip install -r docs/setup_requirements.txt
```

### 2. Environment Setup
```bash
# Set your GCP project ID
export GCP_PROJECT_ID=your-project-id

# Authenticate with Google Cloud
gcloud auth application-default login
```

### 3. BigQuery Setup
```bash
cd scripts/
python setup_bigquery.py
```

### 4. Load Sample Data
```bash
python load_data_to_bigquery.py
```

## Sample Data Description

### Cost Analysis Dataset
- **File**: `data/cost_analysis_new.csv`
- **Records**: 10,800 rows
- **Columns**:
  - `date`: Cost record date
  - `cloud`: Cloud provider (AWS/Azure/GCP)
  - `application`: Application name
  - `environment`: Environment (PROD/NON-PROD)
  - `managed_service`: Service name
  - `cost`: Daily cost in USD
  - `tr_product_pillar_team`: Team name
  - `cto`: CTO organization

### Schema Definition
The BigQuery table schema is defined in `schema/cost_analysis_schema.json` with proper data types and descriptions for each field.

## Usage Notes

1. **Data Privacy**: This is generated synthetic data for development/testing only
2. **Scaling**: For production, replace with your actual cost data
3. **Customization**: Modify schemas and scripts to match your data structure
4. **Security**: Ensure proper IAM permissions for BigQuery access

## Supported Query Types

The generated data supports various analytics queries:
- Total cost calculations
- Cost breakdowns by cloud provider, environment, application
- Time-series analysis (daily, monthly trends)
- Top N queries (most expensive applications, services)
- Team-based cost allocation
- Service utilization analysis