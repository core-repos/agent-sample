"""
API endpoints for context-aware pipeline-based SQL generation
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.pipeline import PipelineAgent, PipelineConfig
    from agents.pipeline.context_loader import ContextConfig
    from agents.pipeline.step_executor import StepConfig, StepType
except ImportError:
    # Fallback imports
    from agents.pipeline.pipeline_agent import PipelineAgent, PipelineConfig
    from agents.pipeline.context_loader import ContextConfig
    from agents.pipeline.step_executor import StepConfig, StepType

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    query_type: Optional[str] = Field(None, description="Query type (aggregation, time_series, etc.)")
    use_cache: bool = Field(True, description="Whether to use cached results")
    enable_budget_integration: bool = Field(False, description="Enable budget data integration")

class TemplateQueryRequest(BaseModel):
    template_name: str = Field(..., description="Template name to use")
    parameters: Dict[str, Any] = Field(..., description="Template parameters")
    query_description: str = Field(..., description="Description of what the query does")

class PipelineStepConfig(BaseModel):
    step_type: str = Field(..., description="Type of step")
    name: str = Field(..., description="Step name")
    description: str = Field(..., description="Step description")
    enabled: bool = Field(True, description="Whether step is enabled")
    timeout: int = Field(30, description="Step timeout in seconds")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Step parameters")

class CustomPipelineRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    steps: List[PipelineStepConfig] = Field(..., description="Custom pipeline steps")
    query_type: Optional[str] = Field(None, description="Query type")

class QueryResponse(BaseModel):
    execution_id: str
    status: str
    query: str
    query_type: str
    sql_query: str
    query_data: List[Dict[str, Any]]
    execution_time: float
    timestamp: str
    steps_completed: int
    total_steps: int
    from_cache: bool
    error: Optional[str] = None

# Global pipeline agent instance
pipeline_agent: Optional[PipelineAgent] = None

def get_pipeline_agent() -> PipelineAgent:
    """Get or create pipeline agent instance"""
    global pipeline_agent

    if pipeline_agent is None:
        try:
            # Initialize with default configuration
            config = PipelineConfig(
                context_config=ContextConfig(),
                pipeline_timeout=300,
                enable_caching=True
            )

            # TODO: Inject actual BigQuery agent and database connection
            pipeline_agent = PipelineAgent(config=config)
            logger.info("Initialized context-aware pipeline agent")

        except Exception as e:
            logger.error(f"Failed to initialize pipeline agent: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to initialize pipeline agent")

    return pipeline_agent

# Create router
router = APIRouter(prefix="/api/context-pipeline", tags=["context-pipeline"])

@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    agent: PipelineAgent = Depends(get_pipeline_agent)
):
    """Process a natural language query through the context-aware pipeline"""
    try:
        logger.info(f"Processing context-aware pipeline query: {request.query[:100]}...")

        # Update agent configuration if needed
        if request.enable_budget_integration:
            agent.config.enable_budget_integration = True

        # Process query through pipeline
        result = await agent.process_query(
            query=request.query,
            query_type=request.query_type,
            use_cache=request.use_cache
        )

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Error processing context-aware pipeline query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/template")
async def process_template_query(
    request: TemplateQueryRequest,
    agent: PipelineAgent = Depends(get_pipeline_agent)
):
    """Process a query using a specific template"""
    try:
        logger.info(f"Processing template query: {request.template_name}")

        # Generate SQL using template
        sql_result = await agent.sql_agent.generate_sql(
            query=request.query_description,
            use_template=request.template_name,
            template_params=request.parameters
        )

        if not sql_result.get('validation', {}).get('is_valid', False):
            raise HTTPException(
                status_code=400,
                detail=f"Template generation failed: {sql_result.get('validation', {}).get('errors', [])}"
            )

        # Execute the generated SQL
        execution_result = await agent.sql_agent.execute_sql(sql_result['sql_query'])

        return {
            "template_name": request.template_name,
            "sql_query": sql_result['sql_query'],
            "execution_result": execution_result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error processing template query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/custom")
async def process_custom_pipeline(
    request: CustomPipelineRequest,
    agent: PipelineAgent = Depends(get_pipeline_agent)
):
    """Process a query with custom pipeline configuration"""
    try:
        logger.info(f"Processing custom pipeline: {len(request.steps)} steps")

        # Convert API models to internal step configs
        step_configs = []
        for step_config in request.steps:
            try:
                step_type = StepType(step_config.step_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid step type: {step_config.step_type}"
                )

            internal_config = StepConfig(
                step_type=step_type,
                name=step_config.name,
                description=step_config.description,
                enabled=step_config.enabled,
                timeout=step_config.timeout,
                parameters=step_config.parameters or {}
            )
            step_configs.append(internal_config)

        # Process query with custom pipeline
        result = await agent.process_query(
            query=request.query,
            query_type=request.query_type,
            custom_pipeline=step_configs
        )

        return result

    except Exception as e:
        logger.error(f"Error processing custom pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_available_templates(
    agent: PipelineAgent = Depends(get_pipeline_agent)
):
    """Get available query templates"""
    try:
        templates = agent.sql_agent.get_available_templates()
        return {
            "templates": templates,
            "count": len(templates),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schemas")
async def get_schema_info(
    agent: PipelineAgent = Depends(get_pipeline_agent)
):
    """Get available schema information"""
    try:
        schemas = agent.sql_agent.get_schema_info()
        return {
            "schemas": schemas,
            "count": len(schemas),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting schemas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/query-types")
async def get_query_types(
    agent: PipelineAgent = Depends(get_pipeline_agent)
):
    """Get available query types"""
    try:
        query_types = agent.get_available_query_types()
        return {
            "query_types": query_types,
            "count": len(query_types),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting query types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/step-types")
async def get_step_types(
    agent: PipelineAgent = Depends(get_pipeline_agent)
):
    """Get available pipeline step types"""
    try:
        step_types = [step_type.value for step_type in agent.step_executor.get_step_types()]
        return {
            "step_types": step_types,
            "count": len(step_types),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting step types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_execution_history(
    limit: int = 50,
    agent: PipelineAgent = Depends(get_pipeline_agent)
):
    """Get recent execution history"""
    try:
        history = agent.get_execution_history(limit=limit)
        return {
            "history": history,
            "count": len(history),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting execution history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/stats")
async def get_cache_stats(
    agent: PipelineAgent = Depends(get_pipeline_agent)
):
    """Get cache statistics"""
    try:
        cache_stats = agent.get_cache_stats()
        context_stats = agent.context_loader.get_cache_stats()

        return {
            "pipeline_cache": cache_stats,
            "context_cache": context_stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/clear")
async def clear_cache(
    background_tasks: BackgroundTasks,
    agent: PipelineAgent = Depends(get_pipeline_agent)
):
    """Clear all caches"""
    try:
        def clear_all_caches():
            agent.clear_cache()
            agent.context_loader.clear_cache()
            logger.info("Cleared all context-aware pipeline caches")

        background_tasks.add_task(clear_all_caches)

        return {
            "message": "Cache clear initiated",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context")
async def get_context_info(
    agent: PipelineAgent = Depends(get_pipeline_agent)
):
    """Get context information"""
    try:
        context_info = agent.get_context_info()
        return {
            "context": context_info,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting context info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        agent = get_pipeline_agent()
        return {
            "status": "healthy",
            "pipeline_agent": "initialized",
            "context_aware": True,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )