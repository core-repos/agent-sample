#!/usr/bin/env python3
"""
Main FastAPI application - Enterprise BigQuery Analytics Backend
Modular architecture with support for multiple LLM providers
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

# Import routers
from api import bigquery, health, visualization, cost_tracking

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
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Default LLM Provider: {settings.default_llm_provider}")
    logger.info(f"BigQuery Project: {settings.gcp_project_id}")
    logger.info(f"BigQuery Dataset: {settings.bq_dataset}")
    logger.info("=" * 80)
    
    # Test database connection
    try:
        from agents.bigquery.database import BigQueryConnection
        conn = BigQueryConnection()
        if conn.test_connection():
            logger.info("✓ Database connection successful")
        else:
            logger.warning("✗ Database connection failed")
    except Exception as e:
        logger.error(f"Database connection error: {e}")
    
    # Check available LLM providers
    try:
        from llm.factory import LLMProviderFactory
        providers = LLMProviderFactory.get_available_providers()
        logger.info(f"Available LLM providers: {[p['name'] for p in providers]}")
    except Exception as e:
        logger.error(f"LLM provider check failed: {e}")
    
    yield
    
    # Shutdown will only happen when the app is stopped
    # logger.info("Shutting down application")

# Create FastAPI app
app = FastAPI(
    title="BigQuery Analytics AI - Enhanced",
    version="3.0.0",
    description="Enterprise BigQuery Analytics with Natural Language Processing and Advanced Visualizations",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(bigquery.router)
app.include_router(visualization.router)
app.include_router(cost_tracking.router)

# Include new pipeline router
from api import pipeline
app.include_router(pipeline.router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "BigQuery Analytics AI - Enhanced",
        "version": "3.0.0",
        "description": "Enterprise BigQuery Analytics with Advanced Visualizations",
        "features": [
            "14 visualization types",
            "Advanced data extraction",
            "Intelligent insights",
            "Modular architecture",
            "Multi-LLM support"
        ],
        "endpoints": {
            "health": "/health",
            "bigquery": {
                "ask": "POST /api/bigquery/ask",
                "examples": "GET /api/bigquery/examples",
                "dataset_info": "GET /api/bigquery/dataset-info",
                "providers": "GET /api/bigquery/providers"
            },
            "visualization": {
                "visualize": "POST /api/visualize",
                "chart_types": "GET /api/chart-types",
                "examples": "GET /api/visualization-examples"
            }
        },
        "documentation": "/docs",
        "openapi": "/openapi.json"
    }

# Backward compatibility endpoints
@app.post("/api/ask")
async def legacy_ask(request: dict):
    """Legacy endpoint for backward compatibility"""
    from api.bigquery import process_query, QueryRequest
    return await process_query(QueryRequest(**request))

@app.get("/api/examples")
async def legacy_examples():
    """Legacy endpoint for backward compatibility"""
    from api.bigquery import get_examples
    return await get_examples()

if __name__ == "__main__":
    import uvicorn
    
    # Ensure logs directory exists
    os.makedirs(settings.log_dir, exist_ok=True)
    
    # Run the application with Docker-aware port configuration
    port = int(os.getenv('PORT', settings.api_port))
    host = os.getenv('HOST', settings.api_host)
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )