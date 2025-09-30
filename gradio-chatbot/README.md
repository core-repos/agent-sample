# BigQuery Agent Frontend

Professional Gradio UI for BigQuery analytics agent.

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your backend URL
```

3. **Run locally:**
```bash
python app.py
# UI runs on http://localhost:7860
```

## Environment Variables

```bash
# Required
API_BASE_URL=http://localhost:8010

# Optional
ENV=local|stage|prod
UI_PORT=7860
```

## Features

- Natural language query interface
- Automatic data visualization
- Quick insights panel
- Professional white theme

## Deployment

### Docker
```bash
docker build -t bigquery-agent-frontend .
docker run -p 7860:7860 --env-file .env bigquery-agent-frontend
```

### Cloud Run
```bash
gcloud run deploy bigquery-agent-frontend \
  --source . \
  --port 7860 \
  --set-env-vars-from-file .env
```