# BigQuery Agent Backend

FastAPI backend service for natural language SQL queries using Claude AI.

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Run locally:**
```bash
python bigquery_agent.py
# API runs on http://localhost:8010
```

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your-key-here
GOOGLE_CLOUD_PROJECT=gac-prod-471220

# Optional
ENV=local|stage|prod
API_PORT=8010
```

## API Endpoints

- `POST /api/ask` - Process natural language query
- `GET /api/health` - Health check
- `GET /api/examples` - Sample queries

## Deployment

### Docker
```bash
docker build -t bigquery-agent-backend .
docker run -p 8010:8010 --env-file .env bigquery-agent-backend
```

### Cloud Run
```bash
gcloud run deploy bigquery-agent-backend \
  --source . \
  --port 8010 \
  --set-env-vars-from-file .env
```