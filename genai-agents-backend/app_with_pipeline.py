#!/usr/bin/env python3
"""
Enhanced FastAPI application with context-aware pipeline integration
This shows how to add the new pipeline system to the existing app
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Import settings
from config.settings import settings

# Import existing routers
from api import bigquery, health, visualization

# Import new pipeline router
from api.context_pipeline import router as context_pipeline_router

# Import pipeline integration
from integration_example import add_pipeline_to_existing_app

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{settings.log_dir}/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("=" * 80)
    logger.info(f"Starting {settings.app_name} v{settings.app_version} WITH PIPELINE SYSTEM")
    logger.info(f"Default LLM Provider: {settings.default_llm_provider}")
    logger.info(f"BigQuery Project: {settings.gcp_project_id}")
    logger.info(f"BigQuery Dataset: {settings.bq_dataset}")
    logger.info("Context Pipeline: ENABLED")
    logger.info("=" * 80)

    # Test database connection
    try:
        from agents.bigquery.database import BigQueryConnection
        conn = BigQueryConnection()
        if conn.test_connection():
            logger.info("✅ BigQuery connection successful")
        else:
            logger.warning("⚠️ BigQuery connection test failed")
    except Exception as e:
        logger.error(f"❌ BigQuery connection error: {e}")

    # Test pipeline system
    try:
        from agents.pipeline.context_loader import ContextLoader
        context_loader = ContextLoader()
        schemas = context_loader.load_table_schemas()
        templates = context_loader.load_query_templates()
        logger.info(f"✅ Pipeline system initialized: {len(schemas)} schemas, {len(templates)} templates")
    except Exception as e:
        logger.error(f"❌ Pipeline system initialization error: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application")

# Create FastAPI app
app = FastAPI(
    title=f"{settings.app_name} with Context Pipeline",
    description="""
    Enterprise BigQuery Analytics AI Agent Platform with Context-Aware Pipeline System

    ## Features
    - 🤖 Multi-LLM Support (Anthropic Claude, Google Gemini, OpenAI GPT)
    - 📊 14+ Visualization Types
    - 🔄 Context-Aware SQL Generation Pipeline
    - 📋 Template-Based Query Processing
    - 💾 Intelligent Caching System
    - 📈 Budget Integration and Variance Analysis
    - 🎯 Smart Query Routing

    ## API Groups
    - `/api/bigquery/` - Original BigQuery agent endpoints
    - `/api/context-pipeline/` - New context-aware pipeline endpoints
    - `/api/integrated/` - Intelligent routing between systems
    - `/api/visualization/` - Chart generation and processing
    """,
    version=f"{settings.app_version}+pipeline",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include existing routers
app.include_router(bigquery.router)
app.include_router(health.router)
app.include_router(visualization.router)

# Include new pipeline router
app.include_router(context_pipeline_router)

# Add pipeline integration (includes integrated endpoints)
add_pipeline_to_existing_app(app)

# Enhanced root endpoint
@app.get("/")
async def root():
    """Enhanced root endpoint with pipeline information"""
    return {
        "message": f"Welcome to {settings.app_name} with Context-Aware Pipeline System",
        "version": f"{settings.app_version}+pipeline",
        "status": "running",
        "features": {
            "original_bigquery_agent": True,
            "context_aware_pipeline": True,
            "intelligent_routing": True,
            "template_system": True,
            "budget_integration": True,
            "multi_llm_support": True,
            "visualization_engine": True
        },
        "endpoints": {
            "legacy": "/api/bigquery/ask",
            "pipeline": "/api/context-pipeline/query",
            "integrated": "/api/integrated/query",
            "templates": "/api/context-pipeline/templates",
            "schemas": "/api/context-pipeline/schemas",
            "health": "/health",
            "docs": "/docs"
        },
        "documentation": "/docs"
    }

# Health check with pipeline status
@app.get("/health/extended")
async def extended_health_check():
    """Extended health check including pipeline system"""
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # Would be actual timestamp
        "components": {}
    }

    # Check BigQuery connection
    try:
        from agents.bigquery.database import BigQueryConnection
        conn = BigQueryConnection()
        health_status["components"]["bigquery"] = {
            "status": "healthy" if conn.test_connection() else "unhealthy"
        }
    except Exception as e:
        health_status["components"]["bigquery"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Check pipeline system
    try:
        from agents.pipeline.context_loader import ContextLoader
        context_loader = ContextLoader()
        schemas = context_loader.load_table_schemas()
        templates = context_loader.load_query_templates()

        health_status["components"]["pipeline_system"] = {
            "status": "healthy",
            "schemas_loaded": len(schemas),
            "templates_loaded": len(templates)
        }
    except Exception as e:
        health_status["components"]["pipeline_system"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Overall status
    all_healthy = all(
        comp.get("status") == "healthy"
        for comp in health_status["components"].values()
    )
    health_status["status"] = "healthy" if all_healthy else "degraded"

    return health_status

# Run the application
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting application with context-aware pipeline system...")
    logger.info("Available endpoints:")
    logger.info("  - Legacy BigQuery: http://localhost:8010/api/bigquery/ask")
    logger.info("  - Context Pipeline: http://localhost:8010/api/context-pipeline/query")
    logger.info("  - Integrated: http://localhost:8010/api/integrated/query")
    logger.info("  - API Documentation: http://localhost:8010/docs")
    logger.info("  - Health Check: http://localhost:8010/health/extended")

    uvicorn.run(
        "app_with_pipeline:app",
        host="0.0.0.0",
        port=8010,
        reload=True,
        log_level="info"
    )