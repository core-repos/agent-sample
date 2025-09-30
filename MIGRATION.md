# BigQuery Analytics AI Agent - Migration Guide

This guide covers connecting the BigQuery Analytics AI Agent system to existing Google Cloud projects and BigQuery datasets using service account authentication.

## 📋 Migration Overview

**Important**: This system connects to **existing** BigQuery resources. You will need:
1. Existing Google Cloud Project with BigQuery enabled
2. Existing BigQuery dataset and tables
3. Service account with appropriate permissions
4. Application environment configuration

**We do not create**: Projects, datasets, or tables. You provide existing resource names and service account credentials.

## 🔑 Step 1: Service Account Setup

### 1.1 Use Existing or Create Service Account
```bash
# Set your existing project
gcloud config set project YOUR-EXISTING-PROJECT-ID

# Create service account (if you don't have one)
gcloud iam service-accounts create bigquery-agent-sa \
    --display-name="BigQuery Analytics Agent Service Account" \
    --description="Service account for BigQuery Analytics AI Agent"

# Grant required BigQuery permissions
gcloud projects add-iam-policy-binding YOUR-EXISTING-PROJECT-ID \
    --member="serviceAccount:bigquery-agent-sa@YOUR-EXISTING-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding YOUR-EXISTING-PROJECT-ID \
    --member="serviceAccount:bigquery-agent-sa@YOUR-EXISTING-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

# Export service account key
gcloud iam service-accounts keys create ./service-account-key.json \
    --iam-account=bigquery-agent-sa@YOUR-EXISTING-PROJECT-ID.iam.gserviceaccount.com
```

### 1.2 Required Permissions
Your service account needs:
- `roles/bigquery.dataViewer` - Read data from tables
- `roles/bigquery.jobUser` - Run queries
- Dataset-level access to your specific dataset (if using dataset-level permissions)

## 🔧 Step 2: Application Configuration

### 2.1 Identify Your Existing BigQuery Resources

Before configuring, identify your existing resources:

```bash
# List your projects
gcloud projects list

# List datasets in your project
bq ls --project_id=YOUR-EXISTING-PROJECT-ID

# List tables in your dataset
bq ls --project_id=YOUR-EXISTING-PROJECT-ID YOUR-EXISTING-DATASET

# View table schema
bq show --project_id=YOUR-EXISTING-PROJECT-ID YOUR-EXISTING-DATASET.YOUR-TABLE
```

### 2.2 Environment Variables Setup
Copy the environment template and configure:

```bash
# Copy environment template
cp .env.example .env
```

Edit `.env` file with your **existing** resource details:

```bash
# ============================
# REQUIRED: BIGQUERY SETTINGS
# ============================

# Your EXISTING Google Cloud Project ID (REQUIRED)
GCP_PROJECT_ID=your-existing-project-id

# Your EXISTING BigQuery Dataset name (REQUIRED)
BQ_DATASET=your_existing_dataset_name

# Path to your exported service account key (REQUIRED)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json

# ============================
# REQUIRED: LLM PROVIDERS
# ============================

# Anthropic Claude (recommended)
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Google Gemini (optional)
# GEMINI_API_KEY=AIza-your-key-here

# OpenAI GPT (optional)
# OPENAI_API_KEY=sk-proj-your-key-here

# Default LLM Provider
DEFAULT_LLM_PROVIDER=anthropic

# ============================
# SERVER CONFIGURATION
# ============================

# Backend API Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8010

# Frontend Gradio Server
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=7860

# ============================
# PERFORMANCE SETTINGS
# ============================

# Agent Configuration (prevents timeouts)
AGENT_MAX_ITERATIONS=50
AGENT_MAX_EXECUTION_TIME=120.0

# API Request timeout in seconds
API_TIMEOUT=120

# Cache Settings
ENABLE_CACHE=true
CACHE_TTL=3600
```

### 2.3 Configuration Validation

The backend automatically loads configuration from environment variables. No code changes needed:

```python
# genai-agents-backend/config/settings.py
# Already configured to use existing resources
gcp_project_id: str = Field(env="GCP_PROJECT_ID")
bq_dataset: str = Field(env="BQ_DATASET")
```

### 2.4 Verify Configuration
```bash
# Test service account access
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json

# Test connection
python -c "
from google.cloud import bigquery
client = bigquery.Client(project='your-existing-project-id')
datasets = list(client.list_datasets())
print(f'Found {len(datasets)} datasets')
for dataset in datasets:
    print(f'  - {dataset.dataset_id}')
"
```

## 📊 Step 3: Optional Sample Data (For Testing)

### 3.1 Understanding the Data Generator System

**Important**: The data generator scripts are **optional** and only for testing purposes. They will:
- Connect to your existing project and dataset (from `.env`)
- Create a `cost_analysis` table if it doesn't exist
- Populate it with synthetic data for testing

**You can skip this step if**:
- You already have data in your BigQuery tables
- You want to use your own existing tables and data

### 3.2 Deploy Sample Data (Optional)
```bash
# Only run this if you need sample data for testing
cd data-generator/scripts
python setup_bigquery.py
```

This script uses your existing project/dataset from `.env` and creates sample tables.

### 3.3 Expected Sample Data Structure (Reference Only)
```sql
-- Example schema the sample data uses
-- Your existing tables can have any schema
CREATE TABLE `your-project.your-dataset.cost_analysis` (
  date DATE NOT NULL,
  cloud STRING NOT NULL,
  application STRING NOT NULL,
  environment STRING NOT NULL,
  managed_service STRING NOT NULL,
  cost FLOAT64 NOT NULL,
  tr_product_pillar_team STRING,
  cto STRING
);
```

## 🚀 Step 4: Application Deployment

### 4.1 Install Dependencies
```bash
# Backend dependencies
cd genai-agents-backend
pip install -r requirements.txt

# Frontend dependencies
cd ../gradio-chatbot
pip install -r requirements.txt
```

### 4.2 Start Services
```bash
# Terminal 1: Backend API
cd genai-agents-backend
python app.py

# Terminal 2: Frontend UI
cd gradio-chatbot
python app.py
```

### 4.3 Verify Deployment
```bash
# Test backend health
curl http://localhost:8010/health

# Test sample query
curl -X POST http://localhost:8010/api/bigquery/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the total cost?"}'

# Access frontend
open http://localhost:7860
```

## 🔄 Step 5: Connection Checklist

### Pre-Connection Setup
- [ ] Identify existing Google Cloud Project ID
- [ ] Identify existing BigQuery Dataset name
- [ ] Identify existing BigQuery Table names
- [ ] Obtain service account credentials (or create new one)
- [ ] Export service account key JSON file
- [ ] Obtain required LLM API keys

### Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Set `GCP_PROJECT_ID` to your existing project
- [ ] Set `BQ_DATASET` to your existing dataset
- [ ] Set `GOOGLE_APPLICATION_CREDENTIALS` path to your service account key
- [ ] Configure LLM provider API keys
- [ ] Verify service account has required permissions

### Deployment
- [ ] Install backend dependencies
- [ ] Install frontend dependencies
- [ ] Start backend service (port 8010)
- [ ] Start frontend service (port 7860)

### Verification
- [ ] Backend health check succeeds
- [ ] BigQuery connection established
- [ ] Can query existing tables
- [ ] Frontend loads correctly
- [ ] End-to-end query processing works
- [ ] Visualizations generate from your data

## 🛠️ Troubleshooting Common Issues

### Permission Errors
```bash
# Common error: "User does not have bigquery.jobs.create permission"
# Solution: Ensure service account has required roles
gcloud projects add-iam-policy-binding YOUR-EXISTING-PROJECT-ID \
    --member="serviceAccount:your-sa@YOUR-EXISTING-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding YOUR-EXISTING-PROJECT-ID \
    --member="serviceAccount:your-sa@YOUR-EXISTING-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"
```

### Connection Issues
```bash
# Verify service account key path
echo $GOOGLE_APPLICATION_CREDENTIALS
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Test BigQuery connection to existing project
python -c "
from google.cloud import bigquery
client = bigquery.Client(project='YOUR-EXISTING-PROJECT-ID')
print(f'Connected to: {client.project}')

# List your existing datasets
datasets = list(client.list_datasets())
print(f'Found {len(datasets)} datasets:')
for dataset in datasets:
    print(f'  - {dataset.dataset_id}')
"
```

### Environment Loading Issues
```python
# In your application, verify environment loading:
from dotenv import load_dotenv
load_dotenv()
import os
print(f"Project: {os.getenv('GCP_PROJECT_ID')}")
print(f"Dataset: {os.getenv('BQ_DATASET')}")
```

## 📁 Files That Need Configuration (No Code Changes)

### Configuration Files Only
- `.env` - Main environment configuration (point to your existing resources)
- `.env.example` - Template reference

### No Code Changes Required
The application is already designed to work with existing BigQuery resources:
- `genai-agents-backend/config/settings.py` - Loads from environment variables
- `genai-agents-backend/agents/bigquery/database.py` - Uses env config
- `gradio-chatbot/utils/api_client.py` - Uses env config

## 🎯 Example: Connecting to Existing Production Resources

### Scenario: Connect to Existing Production BigQuery

You have:
- Project ID: `gac-prod-471220`
- Dataset: `agent_bq_dataset`
- Table: `cost_analysis`
- Service account: Already created with exported key

### Configuration Steps
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your existing resources
cat > .env << EOF
# Your existing BigQuery resources
GCP_PROJECT_ID=gac-prod-471220
BQ_DATASET=agent_bq_dataset
GOOGLE_APPLICATION_CREDENTIALS=/Users/username/.gcp/service-account-key.json

# LLM provider
ANTHROPIC_API_KEY=sk-ant-...
DEFAULT_LLM_PROVIDER=anthropic

# Server settings (defaults work fine)
BACKEND_PORT=8010
FRONTEND_PORT=7860
AGENT_MAX_ITERATIONS=50
AGENT_MAX_EXECUTION_TIME=120.0
EOF

# 3. Start application - it connects to your existing resources
cd genai-agents-backend && python app.py &
cd gradio-chatbot && python app.py &
```

### What Happens
- Application connects to `gac-prod-471220.agent_bq_dataset`
- Uses your existing `cost_analysis` table
- No data creation or modification
- Service account authenticates with existing permissions

## 📞 Support and Resources

### Documentation
- [Main README](./README.md) - Complete system overview
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment
- [Data Generator Guide](./data-generator/README.md) - Optional testing data

### Quick Reference
- **Backend Port**: 8010
- **Frontend Port**: 7860
- **Service Account Roles**: `bigquery.dataViewer`, `bigquery.jobUser`
- **No Resource Creation**: Uses existing projects, datasets, and tables

### Health Check Commands
```bash
# Backend health
curl http://localhost:8010/health

# Test with your existing data
curl -X POST http://localhost:8010/api/bigquery/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me a sample of the data"}'
```

### Key Points to Remember

✅ **This system connects to existing BigQuery resources**
- Provide existing Project ID, Dataset name, and Table names
- Service account needs read permissions only
- No tables or datasets are created by the application

✅ **Configuration via environment variables only**
- All settings in `.env` file
- No code changes required
- Service account key exported to local file

✅ **Data generator scripts are optional**
- Only for testing purposes
- Can be completely skipped if you have existing data
- They use your configured project/dataset from `.env`

---

**Setup Complete!** Your BigQuery Analytics AI Agent is now connected to your existing BigQuery resources using service account authentication.