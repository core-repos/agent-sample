"""
Pipeline API router - New pipeline-based architecture
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pipeline.pipeline_factory import PipelineFactory
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

# Request/Response models
class PipelineRequest(BaseModel):
    question: str
    llm_provider: Optional[str] = "anthropic"
    enable_validation: bool = True
    use_cache: bool = True
    visualization_hint: Optional[str] = None
    timeout: Optional[int] = 120
    pipeline_type: Optional[str] = "standard"

class PipelineResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    pipeline_metadata: Optional[Dict[str, Any]] = None
    execution_time: float
    error: Optional[str] = None

# Singleton pipeline instances
_pipelines = {}

def get_pipeline(pipeline_type: str = "standard"):
    """Get or create pipeline instance"""
    if pipeline_type not in _pipelines:
        if pipeline_type == "standard":
            _pipelines[pipeline_type] = PipelineFactory.create_standard_pipeline()
        elif pipeline_type == "simple":
            _pipelines[pipeline_type] = PipelineFactory.create_simple_pipeline()
        elif pipeline_type == "validation_heavy":
            _pipelines[pipeline_type] = PipelineFactory.create_validation_heavy_pipeline()
        else:
            # Default to standard
            _pipelines[pipeline_type] = PipelineFactory.create_standard_pipeline()

    return _pipelines[pipeline_type]

@router.post("/execute", response_model=PipelineResponse)
async def execute_pipeline(request: PipelineRequest):
    """Execute query using pipeline architecture"""
    try:
        # Get pipeline instance
        pipeline = get_pipeline(request.pipeline_type)

        # Prepare input data
        input_data = {
            "question": request.question,
            "llm_provider": request.llm_provider,
            "enable_validation": request.enable_validation,
            "use_cache": request.use_cache,
            "visualization_hint": request.visualization_hint,
            "timeout": request.timeout
        }

        # Execute pipeline
        logger.info(f"Executing {request.pipeline_type} pipeline for: {request.question}")
        result = await pipeline.execute(input_data)

        # Return response
        return PipelineResponse(
            success=result.success,
            data=result.data,
            pipeline_metadata={
                "pipeline_type": request.pipeline_type,
                "total_steps": len(pipeline.steps),
                "step_results": [
                    {
                        "step": r.step_name,
                        "status": r.status.value,
                        "execution_time": r.execution_time
                    }
                    for r in result.step_results
                ]
            },
            execution_time=result.total_execution_time,
            error=result.error
        )

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types")
async def get_pipeline_types():
    """Get available pipeline types"""
    return {
        "available_pipelines": PipelineFactory.get_available_pipelines()
    }

@router.get("/info/{pipeline_type}")
async def get_pipeline_info(pipeline_type: str):
    """Get detailed information about a pipeline"""
    try:
        pipeline = get_pipeline(pipeline_type)
        return {
            "pipeline_type": pipeline_type,
            "info": pipeline.get_pipeline_info()
        }
    except Exception as e:
        logger.error(f"Failed to get pipeline info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def pipeline_health_check():
    """Check health of pipeline system"""
    try:
        # Check standard pipeline health
        pipeline = get_pipeline("standard")
        health = await pipeline.health_check()

        return {
            "pipeline_system": "healthy",
            "standard_pipeline": health,
            "available_types": list(PipelineFactory.get_available_pipelines().keys())
        }
    except Exception as e:
        logger.error(f"Pipeline health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/custom")
async def execute_custom_pipeline(
    request: PipelineRequest,
    enable_sql_validation: bool = True,
    enable_data_validation: bool = True,
    use_parallel_processing: bool = True
):
    """Execute query with custom pipeline configuration"""
    try:
        # Create custom pipeline
        pipeline = PipelineFactory.create_custom_pipeline(
            enable_sql_validation=enable_sql_validation,
            enable_data_validation=enable_data_validation,
            use_parallel_processing=use_parallel_processing
        )

        # Prepare input data
        input_data = {
            "question": request.question,
            "llm_provider": request.llm_provider,
            "enable_validation": request.enable_validation,
            "use_cache": request.use_cache,
            "visualization_hint": request.visualization_hint,
            "timeout": request.timeout
        }

        # Execute pipeline
        logger.info(f"Executing custom pipeline for: {request.question}")
        result = await pipeline.execute(input_data)

        return PipelineResponse(
            success=result.success,
            data=result.data,
            pipeline_metadata={
                "pipeline_type": "custom",
                "configuration": {
                    "sql_validation": enable_sql_validation,
                    "data_validation": enable_data_validation,
                    "parallel_processing": use_parallel_processing
                },
                "total_steps": len(pipeline.steps),
                "step_results": [
                    {
                        "step": r.step_name,
                        "status": r.status.value,
                        "execution_time": r.execution_time
                    }
                    for r in result.step_results
                ]
            },
            execution_time=result.total_execution_time,
            error=result.error
        )

    except Exception as e:
        logger.error(f"Custom pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))