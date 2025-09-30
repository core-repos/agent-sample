"""
Pipeline Service - Orchestrates all pipeline steps
"""
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from .base_step import BaseStep, StepResult, StepStatus

logger = logging.getLogger(__name__)

@dataclass
class PipelineResult:
    """Result of entire pipeline execution"""
    success: bool
    data: Dict[str, Any]
    step_results: List[StepResult]
    total_execution_time: float
    error: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class PipelineService:
    """
    Main pipeline service that orchestrates all steps

    Pipeline Flow:
    1. Input Processing
    2. SQL Generation (parallel: LLM + Validation)
    3. SQL Execution
    4. Visualization Processing (parallel: Detection + Data Extraction)
    5. Validation & Quality Check
    6. Response Formatting
    """

    def __init__(self):
        self.steps: List[BaseStep] = []
        self.logger = logger

    def add_step(self, step: BaseStep):
        """Add a step to the pipeline"""
        self.steps.append(step)
        self.logger.info(f"Added step to pipeline: {step.name}")

    def remove_step(self, step_name: str):
        """Remove a step from the pipeline"""
        self.steps = [step for step in self.steps if step.name != step_name]
        self.logger.info(f"Removed step from pipeline: {step_name}")

    async def execute(self, input_data: Dict[str, Any]) -> PipelineResult:
        """Execute the complete pipeline"""
        start_time = datetime.now()
        step_results = []
        current_data = input_data.copy()

        self.logger.info("Starting pipeline execution")

        try:
            for step in self.steps:
                self.logger.debug(f"Executing step: {step.name}")

                # Run the step
                result = await step.run(current_data)
                step_results.append(result)

                # Handle step result
                if result.status == StepStatus.SUCCESS:
                    # Merge step output into current data
                    current_data.update(result.data)
                    self.logger.debug(f"Step {step.name} completed successfully")

                elif result.status == StepStatus.SKIPPED:
                    # Step was skipped, continue with current data
                    self.logger.debug(f"Step {step.name} was skipped")
                    continue

                elif result.status == StepStatus.FAILED:
                    # Step failed, decide whether to continue or stop
                    self.logger.error(f"Step {step.name} failed: {result.error}")

                    # For now, stop on any failure
                    total_time = (datetime.now() - start_time).total_seconds()
                    return PipelineResult(
                        success=False,
                        data=current_data,
                        step_results=step_results,
                        total_execution_time=total_time,
                        error=f"Pipeline failed at step '{step.name}': {result.error}"
                    )

            # Pipeline completed successfully
            total_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Pipeline completed successfully in {total_time:.2f}s")

            return PipelineResult(
                success=True,
                data=current_data,
                step_results=step_results,
                total_execution_time=total_time
            )

        except Exception as e:
            total_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            self.logger.error(f"Pipeline execution failed: {error_msg}")

            return PipelineResult(
                success=False,
                data=current_data,
                step_results=step_results,
                total_execution_time=total_time,
                error=f"Pipeline execution error: {error_msg}"
            )

    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get information about the current pipeline configuration"""
        return {
            "total_steps": len(self.steps),
            "steps": [
                {
                    "name": step.name,
                    "description": step.description,
                    "type": step.__class__.__name__,
                    "required_inputs": step.get_required_inputs(),
                    "output_keys": step.get_output_keys()
                }
                for step in self.steps
            ]
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the pipeline"""
        health = {
            "pipeline_status": "healthy",
            "total_steps": len(self.steps),
            "steps_health": [],
            "timestamp": datetime.now().isoformat()
        }

        # Check each step if they have health check methods
        for step in self.steps:
            step_health = {
                "name": step.name,
                "status": "healthy"
            }

            # If step has a health_check method, call it
            if hasattr(step, 'health_check'):
                try:
                    step_result = await step.health_check()
                    step_health.update(step_result)
                except Exception as e:
                    step_health["status"] = "unhealthy"
                    step_health["error"] = str(e)

            health["steps_health"].append(step_health)

        # Determine overall health
        unhealthy_steps = [s for s in health["steps_health"] if s["status"] != "healthy"]
        if unhealthy_steps:
            health["pipeline_status"] = "unhealthy"
            health["unhealthy_steps"] = len(unhealthy_steps)

        return health