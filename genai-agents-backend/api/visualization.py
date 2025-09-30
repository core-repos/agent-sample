"""
Visualization API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from agents.bigquery.agent import BigQueryAgent
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["visualization"])

# Request/Response models
class VisualizationRequest(BaseModel):
    question: str
    visualization_hint: Optional[str] = None
    use_cache: bool = True

class VisualizationResponse(BaseModel):
    question: str
    answer: str
    visualization_type: Optional[str] = None
    chart_data: Optional[Dict[str, Any]] = None
    insights: Optional[List[str]] = None
    sql_query: Optional[str] = None
    metadata: Dict[str, Any]
    timestamp: str
    success: bool = True

# Agent instance (shared with bigquery router)
_agent = None

def get_agent() -> BigQueryAgent:
    """Get or create BigQuery agent with visualization support"""
    global _agent
    if _agent is None:
        _agent = BigQueryAgent(enable_visualization=True)
    return _agent

@router.post("/visualize", response_model=VisualizationResponse)
async def visualize_query(request: VisualizationRequest):
    """Process query with visualization support"""
    try:
        agent = get_agent()
        result = await agent.process_with_visualization(
            question=request.question,
            visualization_hint=request.visualization_hint,
            use_cache=request.use_cache
        )
        
        return VisualizationResponse(
            question=request.question,
            answer=result.get("answer", ""),
            visualization_type=result.get("visualization_type"),
            chart_data=result.get("chart_data"),
            insights=result.get("insights"),
            sql_query=result.get("sql_query"),
            metadata=result.get("metadata", {}),
            timestamp=result.get("timestamp", ""),
            success=result.get("success", True)
        )
        
    except Exception as e:
        logger.error(f"Visualization processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chart-types")
async def get_chart_types():
    """Get supported chart types"""
    agent = get_agent()
    return {
        "chart_types": agent.get_chart_types()
    }

@router.get("/visualization-examples")
async def get_visualization_examples():
    """Get example questions with visualizations"""
    agent = get_agent()
    return {
        "examples": agent.get_visualization_examples()
    }