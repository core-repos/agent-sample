# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
BigQuery Analytics AI Agent Platform - Enterprise natural language analytics with 14 visualization types and multi-LLM support (v3.1.0)

## Context Systems (IMPORTANT)

This project has **TWO separate context directories** with different purposes:

### 1. `/context/` - Runtime Agent Context
- **Purpose**: LangChain conversation memory and agent query context
- **Content**: Concise schemas, 10-15 query examples, prompt templates
- **Format**: YAML (262 lines total)
- **Usage**: Loaded by agents during runtime for fast query generation
- **Contains**:
  - `schemas/cost_analysis.yaml` - Complete organizational hierarchy
  - `examples/cost_queries.yaml` - Essential query patterns
  - `prompts/` - Agent prompt templates

### 2. `/data-generator/scripts/context/` - Development Documentation
- **Purpose**: Comprehensive query library and data generation documentation
- **Content**: 90+ query examples, detailed schemas, pipelines, visualization prompts
- **Format**: JSON + YAML (1,539 lines total)
- **Usage**: Development, testing, data generation reference
- **Contains**:
  - `examples/cost_analysis_queries.json` - 40+ cost query examples with metadata
  - `examples/budget_queries.json` - 30+ budget query examples
  - `examples/combined_queries.json` - 20+ multi-table queries
  - `schemas/` - Full schema documentation with constraints
  - `prompts/` - SQL and visualization prompt libraries
  - `pipelines/` - Workflow definitions

**See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed comparison and usage guidelines.**

**Current Status**: Production ready with migrated data
- **Project**: gac-prod-471220
- **Dataset**: agent_bq_dataset
- **Records**: 10,800 cost analytics records (90 days)
- **Total Cost**: $27,506,708.68
- **Service Account**: /Users/gurukallam/.gcp/genai-community/service-account-key.json

## Architecture

```
User → Gradio UI (7860) → FastAPI (8010) → LangChain SQL Agent → BigQuery
         ↓                      ↓                    ↓
    14 Chart Types      3 LLM Providers:      Visualization
    - Bar/Pie/Line      - Anthropic Claude    Processor with
    - Scatter/Heatmap   - Google Gemini       Smart Detection
    - Treemap/Funnel    - OpenAI GPT
    - Gauge/Indicator   ↓
    - Area/Bubble       Cache Manager
    - Waterfall/Sankey  (TTL + Fallback)
    - Radar
```

**Active Configuration**:
- Backend: http://localhost:8010
- Frontend: http://localhost:7860
- BigQuery Project: gac-prod-471220
- Dataset: agent_bq_dataset

## Development Commands

### Quick Start
```bash
# Start both services
./scripts/start_local.sh

# Or manually:
cd genai-agents-backend && python app.py &  # Backend on :8010
cd gradio-chatbot && python app.py &        # Frontend on :7860
```

### Backend Development
```bash
cd genai-agents-backend
pip install -r requirements.txt
python app.py  # Runs on http://localhost:8010

# Run with specific LLM provider
LLM_PROVIDER=anthropic python app.py
LLM_PROVIDER=gemini python app.py
```

### Frontend Development
```bash
cd gradio-chatbot
pip install -r requirements.txt
python app.py  # Runs on http://localhost:7860
```

### Testing
```bash
# Run all API tests
python tests/test_all_queries.py

# Run validation reliability tests (tests each query 10 times)
python tests/test_basic_validation_10_times.py

# Run comprehensive validation tests
python tests/test_validation_10_times.py

# Run UI automation tests (requires npm install puppeteer)
node tests/test_ui_automated.js
```

## Core Architecture Components

### Backend Module Structure (`genai-agents-backend/`)

**Agent Layer (`agents/bigquery/`)**
- `agent.py`: Main BigQueryAgent class with process(), process_with_visualization(), and process_with_validation() methods
  - Handles agent limits (max_iterations=50, max_execution_time=120s)
  - Implements cache checking and fallback mechanisms
  - Contains _parse_result() for SQL extraction from LLM responses
  - New validation pipeline with SQL and graph data validation
- `visualization.py`: VisualizationProcessor with 14 chart type extractors
  - Pattern-based detection in _init_visualization_patterns()
  - Data extraction methods like _extract_bar_data() with float conversion error handling
  - extract_insights() for generating chart-specific insights
- `sql_toolkit.py`: SQLAgentBuilder wrapping LangChain's create_sql_agent
  - Configurable agent limits via create_agent() parameters
  - Custom prompt templates for BigQuery-specific SQL
- `database.py`: BigQueryConnection using sqlalchemy-bigquery
  - Connection pooling and retry logic
  - Dataset: agent_bq_dataset.cost_analysis (10,800 rows)
- `validators/`: Validation agents for SQL and graph data
  - `sql_validator.py`: SQLValidationAgent for syntax, execution, and performance validation
  - `graph_validator.py`: GraphDataValidationAgent for chart data validation
  - `validation_coordinator.py`: Coordinates complete validation pipeline

**LLM Factory Pattern (`llm/`)**
- `factory.py`: LLMProviderFactory with provider registration
  - Dynamic provider selection based on environment variables
  - Automatic fallback chain: primary → secondary → cached response
- Provider implementations:
  - `anthropic_provider.py`: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
  - `gemini_provider.py`: Google Gemini Pro
  - `openai_provider.py`: GPT-4

**API Layer (`api/`)**
- `bigquery.py`: /api/bigquery/ask endpoint with async processing
- `visualization.py`: /api/visualize, /api/chart-types, /api/visualization-examples
- `health.py`: /health endpoint with BigQuery connection status

**Configuration (`config/settings.py`)**
- Pydantic v2 settings with environment variable loading
- Key settings: agent_max_iterations, agent_max_execution_time, cache_ttl
- Multi-provider API key management

### Frontend Architecture (`gradio-chatbot/`)

**Main Application (`app.py`)**
- Chart creation: `create_chart_from_response()` with regex patterns for data extraction
- Table extraction: `extract_table_data()` for structured data detection
- Response handling: `chat_response()` with error wrapping for chart/table creation
- External CSS from `styles/app.css`

**Components (`components/`)**
- `charts.py`: Plotly chart generators for all 14 types
- `chat_interface.py`: Gradio chat UI with message history
- `modern_ui.py`: Enterprise theme configuration
- `quick_insights.py`: Pre-defined query buttons
- `visualization.py`: Chart type selection logic

**Utils (`utils/`)**
- `api_client.py`: Async HTTP client for backend communication
- `error_handler.py`: User-friendly error message formatting

**UI Layout**
- Left Column (scale=2): Chat interface with input area, conditional data table below
- Right Sidebar: Data visualization (expandable) and example queries
- Responsive design with 99% fluid width

## Critical Implementation Details

### Float Conversion Error Handling
Fixed in `gradio-chatbot/app.py` with bullet point handling:
```python
pattern = r'•\s*([A-Z][A-Za-z\s-]+?):\s*\$?([\d,]+(?:\.\d{2})?)'  # Handles • bullets
if label and value_str and value_str != '':
    value = float(value_str)  # Safe after validation
```

### Agent Limits (IMPORTANT)
Must use these settings to prevent timeouts:
```env
AGENT_MAX_ITERATIONS=50        # Increased from default 30
AGENT_MAX_EXECUTION_TIME=120.0  # Increased from default 60
API_TIMEOUT=120
ENABLE_VALIDATION=true         # Enable SQL and graph validation
```

### Cache Strategy
- Primary key: question text
- TTL: 3600 seconds (configurable)
- Fallback: Returns stale cache on LLM failure
- Semantic similarity for near-match queries
- Validated results cached separately

### Validation System
- **SQL Validation**: Syntax, BigQuery compatibility, execution, performance
- **Graph Data Validation**: Structure, types, quality, consistency
- **Testing**: Each validation component tested 10 times for reliability
- **Endpoints**: `/validation/health`, `/validation/examples`

### BigQuery Schema
**Project**: gac-prod-471220
**Dataset**: agent_bq_dataset
**Table**: cost_analysis (10,800 records)

Schema:
- date (DATE): Cost record date
- cloud (STRING): Provider (AWS/Azure/GCP)
- application (STRING): App name
- environment (STRING): PROD/NON-PROD
- managed_service (STRING): Service name
- cost (FLOAT): Daily USD cost
- tr_product_pillar_team (STRING): Team
- cto (STRING): Tech organization

**Data Coverage**: 90 days of cost analytics data
**Total Cost Value**: $27,506,708.68

## Environment Configuration

### Required Environment Variables (.env)
```env
# BigQuery (Required - Updated Configuration)
GCP_PROJECT_ID=gac-prod-471220
BQ_DATASET=agent_bq_dataset
GOOGLE_APPLICATION_CREDENTIALS=/Users/gurukallam/.gcp/genai-community/service-account-key.json

# LLM Providers (At least one required)
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
OPENAI_API_KEY=sk-...

# Configuration (REQUIRED to prevent timeouts)
LLM_PROVIDER=anthropic  # Active provider
DEFAULT_LLM_PROVIDER=anthropic  # Fallback
AGENT_MAX_ITERATIONS=50  # Increased to prevent timeouts
AGENT_MAX_EXECUTION_TIME=120.0  # 2 minutes timeout
API_TIMEOUT=120  # API request timeout
ENABLE_CACHE=true
CACHE_TTL=3600
ENABLE_VALIDATION=true  # Enable SQL and graph validation
```

## Testing

### Test Suite Location
All tests are in `/tests` directory:
- `test_all_queries.py` - API integration tests for all 7 example queries
- `test_ui_automated.js` - Puppeteer-based UI automation tests
- `README.md` - Complete testing documentation

### Example Queries for Testing
1. "What is the total cost?" → KPI Indicator
2. "Show top 5 applications by cost" → Bar Chart
3. "Cost breakdown by environment" → Pie Chart
4. "Daily cost trend last 30 days" → Line Chart
5. "Cost vs usage correlation" → Scatter Plot

## Common Issues & Solutions

### "Agent stopped due to iteration limit"
- Use recommended settings: AGENT_MAX_ITERATIONS=50, AGENT_MAX_EXECUTION_TIME=120.0
- Simplify complex queries
- Check for SQL syntax issues in agent prompt

### "Could not convert string to float"
- Fixed in visualization.py with empty value validation
- Check data format in BigQuery response
- Review regex patterns in extraction methods

### "Model not found" errors
- Update to latest model versions:
  - Claude: claude-3-5-sonnet-20241022
  - Gemini: gemini-pro
  - GPT: gpt-4

### BigQuery Connection Issues
- Verify service account path: /Users/gurukallam/.gcp/genai-community/service-account-key.json
- Confirm project ID: gac-prod-471220
- Check dataset access: agent_bq_dataset

## Performance Optimization Points

1. **Cache Hit Optimization**: Implement semantic similarity for near-match queries
2. **Agent Prompt Engineering**: Enhanced prompts in _get_enhanced_prompt() for better SQL generation
3. **Visualization Detection**: Pattern-based detection reduces LLM calls
4. **Async Processing**: FastAPI async endpoints for concurrent requests
5. **Connection Pooling**: SQLAlchemy connection pool for BigQuery

## Deployment Considerations

- **Ports**: Backend (8010), Frontend (7860)
- **Memory**: Minimum 8GB RAM for LLM operations
- **CPU**: 4+ cores recommended for concurrent requests
- **Network**: Stable connection for LLM API calls
- **BigQuery**: Service account with BigQuery Data Viewer role

## Migration Notes

**Recent Migration**: Data successfully migrated to production environment
- **Source**: Data generator scripts
- **Target**: gac-prod-471220.agent_bq_dataset.cost_analysis
- **Records**: 10,800 rows (90 days of data)
- **Verification**: Full data integrity confirmed
- **Performance**: Optimized for analytics queries

**Service Account Configuration**:
- Location: /Users/gurukallam/.gcp/genai-community/service-account-key.json
- Permissions: BigQuery Data Viewer, BigQuery Job User
- Project Access: gac-prod-471220
