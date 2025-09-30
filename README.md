# 🚀 BigQuery Analytics AI Agent Platform

An enterprise-grade natural language analytics platform that transforms questions into SQL queries and visualizations using BigQuery and advanced AI models.

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

- **Natural Language to SQL**: Convert plain English questions into optimized BigQuery SQL queries
- **14 Visualization Types**: Automatic chart generation (bar, pie, line, scatter, heatmap, treemap, funnel, gauge, indicator, area, bubble, waterfall, sankey, radar)
- **Multi-LLM Support**: Anthropic Claude, Google Gemini, OpenAI GPT
- **Enterprise UI**: Professional Gradio interface with modern design
- **Smart Data Tables**: Automatic table extraction and display for structured data
- **Validation System**: SQL and graph data validation for reliability
- **Smart Caching**: Intelligent response caching for performance
- **Modular Architecture**: Clean, scalable, and maintainable code structure
- **External CSS**: All styles in separate CSS file for maintainability

## 📖 Important: Context Systems

This project has **two separate context directories** with different purposes:

- **`/context/`** (262 lines) - Runtime agent context (LangChain memory) - Essential query patterns, loaded by agents during query processing
- **`/data-generator/scripts/context/`** (1,539+ lines) - Comprehensive documentation - 90+ query examples, detailed schemas, used for development/testing

**See [CONTEXT_SYSTEMS_EXPLAINED.md](./CONTEXT_SYSTEMS_EXPLAINED.md) for quick reference or [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture.**

## 🏗️ Production Ready Status

This codebase is **fully operational and production-ready**:
- ✅ Service Account: Configured with secure GCP authentication
- ✅ Project: `gac-prod-471220` with BigQuery enabled
- ✅ Dataset: `agent_bq_dataset` with 10,800 sample records
- ✅ Data Range: 90 days of cost analytics ($27,506,708.68 total)
- ✅ Backend: Running on http://localhost:8010
- ✅ Frontend: Running on http://localhost:7860
- ✅ SQL and graph data validation system
- ✅ Comprehensive testing framework (tested 10 times for reliability)
- ✅ Docker support with health checks
- ✅ Production configuration templates
- ✅ Complete migration documentation

See [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md) for deployment instructions.
For new project setup, see [MIGRATION.md](./MIGRATION.md) for the complete configuration guide.

## 📁 Project Structure

```
ADK-Agents/
├── context/                   # Runtime agent context (LangChain memory)
│   ├── examples/             # Essential query patterns
│   ├── prompts/              # Agent prompt templates
│   └── schemas/              # Concise schema definitions
│
├── genai-agents-backend/       # Backend API (FastAPI)
│   ├── app.py                 # Main application entry point
│   ├── agents/                # Agent implementations
│   │   └── bigquery/         # BigQuery-specific logic
│   │       ├── agent.py      # Main BigQuery agent
│   │       ├── database.py   # Database connections
│   │       ├── sql_toolkit.py # SQL agent builder
│   │       └── visualization.py # Chart data extraction
│   ├── api/                  # API endpoints
│   │   ├── bigquery.py      # BigQuery endpoints
│   │   ├── health.py        # Health checks
│   │   └── visualization.py # Visualization endpoints
│   ├── llm/                  # LLM providers
│   │   ├── base.py          # Abstract base class
│   │   ├── factory.py       # Provider factory
│   │   ├── anthropic_provider.py
│   │   ├── gemini_provider.py
│   │   └── openai_provider.py
│   ├── config/               # Configuration
│   │   └── settings.py      # Application settings
│   └── utils/                # Utilities
│       └── cache.py         # Cache management
│
├── gradio-chatbot/            # Frontend UI (Gradio)
│   ├── app.py                # Main UI application
│   ├── styles/               # External CSS
│   │   └── app.css          # All application styles
│   ├── components/           # UI components
│   │   ├── charts.py        # Chart generation
│   │   ├── chat_interface.py # Chat UI
│   │   ├── modern_ui.py     # Modern UI theme
│   │   ├── quick_insights.py # Quick insights panel
│   │   └── visualization.py # Visualization logic
│   └── utils/                # Frontend utilities
│       ├── api_client.py    # API client
│       └── error_handler.py # Error handling
│
├── data-generator/            # Data generation and setup
│   ├── data/                 # Generated datasets
│   │   └── cost_analysis_new.csv # 10,800 records, 90 days
│   ├── schema/               # BigQuery schema JSONs
│   ├── queries/              # Sample SQL queries
│   └── scripts/              # Data generation scripts
│       └── context/          # Comprehensive documentation (90+ query examples)
│
└── scripts/                   # Utility scripts
    └── start_local.sh        # Start all services
```

**Note**: See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed explanation of the two context systems.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud Project with BigQuery enabled
- API Keys (at least one):
  - Anthropic Claude API key
  - Google Gemini API key
  - OpenAI API key

### Current Configuration

The system is currently configured with:
- **Project ID**: `gac-prod-471220`
- **Dataset**: `agent_bq_dataset`
- **Service Account**: `/Users/gurukallam/.gcp/genai-community/service-account-key.json`
- **Sample Data**: 10,800 records covering 90 days of cost analytics
- **Total Cost Value**: $27,506,708.68

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ADK-Agents.git
cd ADK-Agents
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
# Backend
cd genai-agents-backend
pip install -r requirements.txt

# Frontend
cd ../gradio-chatbot
pip install -r requirements.txt
```

4. **Configure environment variables**

For the current working setup, create `.env` file in `genai-agents-backend/`:
```env
# Google Cloud Configuration (Production Ready)
GCP_PROJECT_ID=gac-prod-471220
BQ_DATASET=agent_bq_dataset
GOOGLE_APPLICATION_CREDENTIALS=/Users/gurukallam/.gcp/genai-community/service-account-key.json

# LLM Providers (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
OPENAI_API_KEY=sk-...

# Default provider (anthropic, gemini, or openai)
DEFAULT_LLM_PROVIDER=anthropic

# IMPORTANT: Recommended Agent Configuration (Prevents timeouts)
AGENT_MAX_ITERATIONS=50
AGENT_MAX_EXECUTION_TIME=120.0
API_TIMEOUT=120

# Cache Configuration
ENABLE_CACHE=true
CACHE_TTL=3600
```

**Note**: For setting up a new project from scratch, refer to [MIGRATION.md](./MIGRATION.md) for the complete setup guide.

### Running the Application

#### Option 1: Using the start script
```bash
./scripts/start_local.sh
```

#### Option 2: Manual start
```bash
# Terminal 1: Start Backend
cd genai-agents-backend
python app.py  # Runs on http://localhost:8010

# Terminal 2: Start Frontend
cd gradio-chatbot
python app.py  # Runs on http://localhost:7860
```

## 🎨 Frontend Design

The frontend follows a strict design specification documented in [FRONTEND_DESIGN_SPEC.md](./FRONTEND_DESIGN_SPEC.md).

### Key UI Components:
- **Chat Interface**: Clean chat with message history
- **Data Visualization**: 14 chart types with expand functionality
- **Data Tables**: Auto-displays when response contains tabular data
- **Example Queries**: Quick-start buttons for common questions

### Layout:
- **Left Column (2/3 width)**: Chat interface + Data table (conditional)
- **Right Sidebar (400px)**: Visualizations + Example queries
- **Responsive**: 99% fluid width for optimal screen usage

**Note**: UI layout is locked per design spec. Any modifications require explicit override.

## 📊 Sample Data Overview

The current dataset contains:
- **Records**: 10,800 cost analytics entries
- **Time Range**: 90 days of historical data
- **Total Cost**: $27,506,708.68
- **Data Points**: Date, cloud provider, application, environment, managed service, cost, team, CTO organization
- **Applications**: 15 different applications across AWS, Azure, and GCP
- **Environments**: Production and Non-Production
- **Teams**: Multiple product pillar teams

## 🚨 Troubleshooting

### "Agent stopped due to iteration limit or time limit"
**Solution**: Update your `.env` file with recommended settings:
```env
AGENT_MAX_ITERATIONS=50
AGENT_MAX_EXECUTION_TIME=120.0
API_TIMEOUT=120
```

### "HTTPConnectionPool timeout" errors
**Solution**: This usually happens with Arctic/Ollama. Switch to a cloud LLM provider:
```env
DEFAULT_LLM_PROVIDER=anthropic  # or gemini, openai
```

## 📡 API Documentation

### Base URL
```
http://localhost:8010
```

### Endpoints

#### Health Check
```http
GET /health
```

#### Process Query
```http
POST /api/bigquery/ask
Content-Type: application/json

{
  "question": "What is the total cost?"
}
```

#### Visualize Query
```http
POST /api/visualize
Content-Type: application/json

{
  "question": "Show top 5 applications by cost",
  "visualization_hint": "bar"
}
```

#### Get Chart Types
```http
GET /api/chart-types
```

#### Get Examples
```http
GET /api/visualization-examples
```

### Response Format
```json
{
  "success": true,
  "answer": "The total cost is $27,506,708.68",
  "visualization_type": "indicator",
  "chart_data": {
    "type": "indicator",
    "data": {
      "value": 27506708.68,
      "title": "Total Cost",
      "format": "currency"
    }
  },
  "insights": [
    "Total cost represents all applications over 90 days",
    "Data covers production and non-production environments"
  ],
  "metadata": {
    "llm_provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "cached": false
  }
}
```

## 🎨 Visualization Types

| Type | Use Case | Example Query |
|------|----------|---------------|
| Bar Chart | Rankings, comparisons | "Show top 5 applications by cost" |
| Pie Chart | Distribution, proportions | "Cost breakdown by environment" |
| Line Chart | Trends over time | "Daily cost trend for last 30 days" |
| Scatter Plot | Correlations | "Cost vs usage correlation" |
| Heatmap | Matrix visualization | "Cost by day and service" |
| Treemap | Hierarchical data | "Nested cost breakdown" |
| Funnel | Process stages | "Conversion from dev to prod" |
| Gauge | Performance metrics | "Current utilization rate" |
| Indicator | Single KPIs | "Total cost" |
| Area Chart | Cumulative trends | "Cumulative cost over time" |
| Bubble | 3D relationships | "Cost, usage, and efficiency" |
| Waterfall | Incremental changes | "Monthly cost changes" |
| Sankey | Flow visualization | "Resource allocation flow" |
| Radar | Multi-dimensional | "Service performance metrics" |

## 🔧 Configuration

### Backend Configuration (`genai-agents-backend/config/settings.py`)

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `gcp_project_id` | `GCP_PROJECT_ID` | `gac-prod-471220` | Google Cloud Project ID |
| `bq_dataset` | `BQ_DATASET` | `agent_bq_dataset` | BigQuery dataset name |
| `default_llm_provider` | `DEFAULT_LLM_PROVIDER` | `anthropic` | Default LLM provider |
| `agent_max_iterations` | `AGENT_MAX_ITERATIONS` | `50` | Max reasoning steps |
| `agent_max_execution_time` | `AGENT_MAX_EXECUTION_TIME` | `120.0` | Max execution time (seconds) |
| `enable_cache` | `ENABLE_CACHE` | `true` | Enable response caching |
| `cache_ttl` | `CACHE_TTL` | `3600` | Cache time-to-live (seconds) |

### Frontend Configuration (`gradio-chatbot/config/settings.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `api_base_url` | `http://localhost:8010` | Backend API URL |
| `theme` | `professional` | UI theme |
| `max_messages` | `50` | Chat history limit |
| `auto_refresh` | `false` | Auto-refresh charts |

## 🧪 Testing

### API Tests
```bash
# Run all API tests
python tests/test_all_queries.py

# Test validation reliability (tests each query 10 times)
python tests/test_basic_validation_10_times.py

# Comprehensive validation testing
python tests/test_validation_10_times.py
```

### Backend Tests
```bash
cd genai-agents-backend
pytest tests/
```

### Frontend Tests
```bash
cd gradio-chatbot
python test_visualizations.py
python test_ui_queries.py
```

### Validation Health Check
```bash
curl http://localhost:8010/api/bigquery/validation/health
```

## 🛠️ Development

### Adding a New LLM Provider

1. Create provider class in `llm/`:
```python
# llm/custom_provider.py
from .base import LLMProvider

class CustomProvider(LLMProvider):
    def get_model(self, **kwargs):
        # Implementation
        pass
```

2. Register in factory:
```python
# llm/factory.py
from .custom_provider import CustomProvider
LLMProviderFactory.register_provider("custom", CustomProvider)
```

### Adding a New Visualization Type

1. Add pattern detection in `agents/bigquery/visualization.py`:
```python
def _init_visualization_patterns(self):
    return {
        "custom": ["pattern1", "pattern2"],
        # ...
    }
```

2. Add data extraction method:
```python
def _extract_custom_data(self, answer: str):
    # Extract and return structured data
    pass
```

## 📊 Sample Queries

Test the system with these example queries using the current dataset:

- **Basic Metrics**: "What is the total cost?" → $27,506,708.68
- **Rankings**: "Show me the top 5 applications by cost"
- **Distributions**: "What's the cost breakdown by environment?"
- **Trends**: "Display the daily cost trend for the last 30 days"
- **Comparisons**: "Compare costs between production and development"
- **Aggregations**: "What's the average cost per application?"
- **Filtering**: "Show costs greater than $10,000"
- **Complex**: "What percentage of total cost is from production environment?"

## 🐛 Troubleshooting

### Common Issues

1. **"Agent stopped due to iteration limit"**
   - Increase `AGENT_MAX_ITERATIONS` in `.env`
   - Simplify your query

2. **"Could not convert string to float"**
   - Fixed in latest version
   - Check data format in responses

3. **"Model not found" errors**
   - Ensure using latest model versions
   - Check API key validity

4. **Connection errors**
   - Verify BigQuery credentials
   - Check network connectivity

## 📚 Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Context systems and architecture overview
- [MIGRATION.md](./MIGRATION.md) - Complete setup guide for new projects
- [FRONTEND_DESIGN_SPEC.md](./FRONTEND_DESIGN_SPEC.md) - UI design specifications
- [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md) - Deployment instructions
- [data-generator/scripts/context/README.md](./data-generator/scripts/context/README.md) - Comprehensive query documentation

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📧 Support

For issues and questions:
- Create an issue on GitHub
- Email: support@example.com

## 🏆 Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Backend API framework
- [Gradio](https://gradio.app/) - Frontend UI framework
- [LangChain](https://langchain.com/) - LLM orchestration
- [Google BigQuery](https://cloud.google.com/bigquery) - Data warehouse
- [Anthropic Claude](https://anthropic.com/) - AI model

---

**Version**: 3.0.0 | **Status**: Production Ready | **Last Updated**: January 2025