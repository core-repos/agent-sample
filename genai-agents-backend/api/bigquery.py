"""
BigQuery API router
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from agents.bigquery.agent import BigQueryAgent
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/bigquery", tags=["bigquery"])

# Request/Response models
class QueryRequest(BaseModel):
    question: str
    llm_provider: Optional[str] = None
    use_cache: bool = True
    enable_validation: bool = True
    visualization_hint: Optional[str] = None

class QueryResponse(BaseModel):
    success: bool
    answer: str
    sql_query: Optional[str] = None
    visualization: Optional[str] = None
    chart_data: Optional[Dict[str, Any]] = None
    validation_report: Optional[Dict[str, Any]] = None
    warnings: Optional[list] = None
    metadata: Dict[str, Any]

# Initialize agent (singleton)
_agent = None

def get_agent(provider: Optional[str] = None) -> BigQueryAgent:
    """Get or create BigQuery agent instance"""
    global _agent
    if _agent is None or (provider and provider != getattr(_agent.llm_provider, 'provider_name', None)):
        _agent = BigQueryAgent(llm_provider=provider, enable_visualization=True, enable_validation=True)
    return _agent

@router.post("/ask", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process natural language query against BigQuery"""
    try:
        # Use the original working BigQuery agent directly
        agent = get_agent(request.llm_provider)

        logger.info(f"Processing query with agent: {request.question}")

        # Process with the agent (this is the original working method)
        result = await agent.process_with_visualization(
            request.question,
            visualization_hint=request.visualization_hint,
            use_cache=request.use_cache
        )

        # Map to response format
        response = QueryResponse(
            success=result.get("success", True),
            answer=result.get("answer", ""),
            sql_query=result.get("sql_query"),
            visualization=result.get("visualization"),
            chart_data=result.get("chart_data"),
            validation_report=result.get("validation_report"),
            warnings=result.get("warnings", []),
            metadata=result.get("metadata", {})
        )

        return response

    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/examples")
async def get_examples():
    """Get sample questions"""
    agent = get_agent()
    return {
        "examples": agent.get_sample_questions()
    }

@router.get("/dataset-info")
async def get_dataset_info():
    """Get information about the connected dataset"""
    try:
        agent = get_agent()
        return agent.get_dataset_info()
    except Exception as e:
        logger.error(f"Failed to get dataset info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers")
async def get_providers():
    """Get available LLM providers"""
    from llm.factory import LLMProviderFactory
    return {
        "providers": LLMProviderFactory.get_available_providers()
    }

@router.get("/validation/examples")
async def get_validation_examples():
    """Get example queries for testing validation"""
    agent = get_agent()
    if hasattr(agent, 'validation_coordinator') and agent.validation_coordinator:
        return {
            "validation_examples": agent.validation_coordinator.get_validation_examples()
        }
    return {"validation_examples": []}

@router.get("/validation/health")
async def validation_health_check():
    """Check health of validation components"""
    try:
        agent = get_agent()
        if hasattr(agent, 'validation_coordinator') and agent.validation_coordinator:
            health = await agent.validation_coordinator.health_check()
            return health
        return {"status": "validation_disabled"}
    except Exception as e:
        logger.error(f"Validation health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))