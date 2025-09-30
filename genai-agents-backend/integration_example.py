"""
Integration example showing how to add the context-aware pipeline to the existing app
"""

import asyncio
import logging
from typing import Dict, Any

# Existing imports (would be in your app.py)
from fastapi import FastAPI
from agents.bigquery.agent import BigQueryAgent
from agents.bigquery.database import BigQueryConnection

# New pipeline imports
from agents.pipeline import PipelineAgent, PipelineConfig
from agents.pipeline.context_loader import ContextConfig
from api.context_pipeline import router as context_pipeline_router

logger = logging.getLogger(__name__)

class IntegratedAgent:
    """
    Integrated agent that combines existing BigQuery agent with new pipeline system
    """

    def __init__(self):
        # Initialize existing components
        self.bigquery_connection = BigQueryConnection()
        self.bigquery_agent = BigQueryAgent(database_connection=self.bigquery_connection)

        # Initialize new pipeline system
        context_config = ContextConfig(
            schema_dir="context/schemas",
            templates_dir="context/templates",
            examples_dir="context/examples",
            cache_enabled=True,
            cache_ttl=3600
        )

        pipeline_config = PipelineConfig(
            context_config=context_config,
            pipeline_timeout=300,
            enable_budget_integration=True,
            enable_caching=True
        )

        self.pipeline_agent = PipelineAgent(
            config=pipeline_config,
            bigquery_agent=self.bigquery_agent,
            database_connection=self.bigquery_connection
        )

        logger.info("Initialized integrated agent with context-aware pipeline")

    async def process_query_legacy(self, query: str) -> Dict[str, Any]:
        """
        Process query using legacy BigQuery agent (for backward compatibility)
        """
        try:
            result = await self.bigquery_agent.process(query)
            return {
                "method": "legacy",
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"Legacy processing failed: {str(e)}")
            return {
                "method": "legacy",
                "success": False,
                "error": str(e)
            }

    async def process_query_pipeline(self, query: str, query_type: str = None) -> Dict[str, Any]:
        """
        Process query using new context-aware pipeline
        """
        try:
            result = await self.pipeline_agent.process_query(
                query=query,
                query_type=query_type,
                use_cache=True
            )
            return {
                "method": "pipeline",
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"Pipeline processing failed: {str(e)}")
            return {
                "method": "pipeline",
                "success": False,
                "error": str(e)
            }

    async def process_query_intelligent(self, query: str) -> Dict[str, Any]:
        """
        Intelligently choose between legacy and pipeline based on query complexity
        """
        # Simple heuristics to determine which method to use
        query_lower = query.lower()

        # Use pipeline for complex queries
        pipeline_indicators = [
            'budget', 'trend', 'compare', 'top', 'bottom', 'rank',
            'over time', 'monthly', 'daily', 'variance', 'vs'
        ]

        use_pipeline = any(indicator in query_lower for indicator in pipeline_indicators)

        if use_pipeline:
            logger.info(f"Using pipeline for complex query: {query[:50]}...")
            result = await self.process_query_pipeline(query)

            # Fallback to legacy if pipeline fails
            if not result['success']:
                logger.warning("Pipeline failed, falling back to legacy agent")
                result = await self.process_query_legacy(query)
                result['fallback'] = True

            return result
        else:
            logger.info(f"Using legacy agent for simple query: {query[:50]}...")
            return await self.process_query_legacy(query)

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get capabilities of the integrated system
        """
        return {
            "legacy_agent": {
                "available": True,
                "description": "Original BigQuery agent with LLM-based SQL generation"
            },
            "pipeline_agent": {
                "available": True,
                "description": "Context-aware pipeline with templates and examples",
                "features": {
                    "query_types": self.pipeline_agent.get_available_query_types(),
                    "templates": len(self.pipeline_agent.sql_agent.get_available_templates()),
                    "schemas": len(self.pipeline_agent.sql_agent.get_schema_info()),
                    "budget_integration": True,
                    "caching": True
                }
            },
            "intelligent_routing": {
                "available": True,
                "description": "Automatically choose best method based on query type"
            }
        }

def add_pipeline_to_existing_app(app: FastAPI):
    """
    Add the context-aware pipeline system to an existing FastAPI app
    """
    # Include the new router
    app.include_router(context_pipeline_router)

    # Add integration endpoint
    @app.post("/api/integrated/query")
    async def integrated_query(request: dict):
        """
        Integrated endpoint that intelligently routes queries
        """
        integrated_agent = IntegratedAgent()
        query = request.get('query', '')

        result = await integrated_agent.process_query_intelligent(query)
        return result

    @app.get("/api/integrated/capabilities")
    async def get_capabilities():
        """
        Get capabilities of the integrated system
        """
        integrated_agent = IntegratedAgent()
        return integrated_agent.get_capabilities()

    logger.info("Added context-aware pipeline integration to existing app")

async def demo_integration():
    """
    Demonstration of the integrated system
    """
    print("🚀 Context-Aware Pipeline Integration Demo")
    print("=" * 50)

    integrated_agent = IntegratedAgent()

    # Test queries
    test_queries = [
        "What is the total cost?",  # Simple - use legacy
        "Show top 5 applications by cost",  # Complex - use pipeline
        "Budget variance by application this month",  # Complex - use pipeline
        "Daily cost trend for the last 30 days",  # Complex - use pipeline
        "SELECT SUM(cost) FROM cost_analysis"  # Simple SQL - use legacy
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 30)

        result = await integrated_agent.process_query_intelligent(query)

        print(f"Method: {result['method']}")
        print(f"Success: {result['success']}")

        if result['success']:
            if result['method'] == 'pipeline':
                pipeline_result = result['result']
                print(f"SQL: {pipeline_result.get('sql_query', 'N/A')[:100]}...")
                print(f"Steps: {pipeline_result.get('steps_completed', 0)}/{pipeline_result.get('total_steps', 0)}")
                print(f"From Cache: {pipeline_result.get('from_cache', False)}")
            else:
                print(f"SQL: {result['result'].get('sql_query', 'N/A')[:100]}...")

        if result.get('fallback'):
            print("⚠️ Used fallback to legacy agent")

        if not result['success']:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")

    # Show capabilities
    print(f"\n📊 System Capabilities")
    print("=" * 30)
    capabilities = integrated_agent.get_capabilities()

    for component, info in capabilities.items():
        print(f"\n{component.replace('_', ' ').title()}:")
        print(f"  Available: {info['available']}")
        print(f"  Description: {info['description']}")

        if 'features' in info:
            features = info['features']
            print(f"  Features:")
            for feature, value in features.items():
                if isinstance(value, list):
                    print(f"    {feature}: {len(value)} items")
                else:
                    print(f"    {feature}: {value}")

if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_integration())