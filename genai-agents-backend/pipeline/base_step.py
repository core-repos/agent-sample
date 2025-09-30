"""
Base classes for pipeline steps
"""
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StepStatus(Enum):
    """Status of a pipeline step"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class StepResult:
    """Result of a pipeline step"""
    step_name: str
    status: StepStatus
    data: Dict[str, Any]
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class BaseStep(ABC):
    """Base class for all pipeline steps"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"pipeline.{name}")

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute the step with input data and return result"""
        pass

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the step"""
        return True

    def get_required_inputs(self) -> List[str]:
        """Get list of required input keys"""
        return []

    def get_output_keys(self) -> List[str]:
        """Get list of output keys this step produces"""
        return []

    async def run(self, input_data: Dict[str, Any]) -> StepResult:
        """Run the step with error handling and timing"""
        start_time = datetime.now()

        try:
            self.logger.info(f"Starting step: {self.name}")

            # Validate input
            if not self.validate_input(input_data):
                return StepResult(
                    step_name=self.name,
                    status=StepStatus.FAILED,
                    data={},
                    error="Input validation failed"
                )

            # Execute step
            result = await self.execute(input_data)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time

            self.logger.info(f"Completed step: {self.name} in {execution_time:.2f}s")
            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            self.logger.error(f"Step {self.name} failed: {error_msg}")

            return StepResult(
                step_name=self.name,
                status=StepStatus.FAILED,
                data={},
                error=error_msg,
                execution_time=execution_time
            )

class ConditionalStep(BaseStep):
    """Step that can be skipped based on conditions"""

    @abstractmethod
    def should_execute(self, input_data: Dict[str, Any]) -> bool:
        """Determine if this step should be executed"""
        pass

    async def run(self, input_data: Dict[str, Any]) -> StepResult:
        """Run with conditional logic"""
        if not self.should_execute(input_data):
            self.logger.info(f"Skipping step: {self.name}")
            return StepResult(
                step_name=self.name,
                status=StepStatus.SKIPPED,
                data=input_data  # Pass through input data
            )

        return await super().run(input_data)

class ParallelStep(BaseStep):
    """Step that can run multiple sub-steps in parallel"""

    def __init__(self, name: str, sub_steps: List[BaseStep], description: str = ""):
        super().__init__(name, description)
        self.sub_steps = sub_steps

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute all sub-steps in parallel"""
        import asyncio

        # Run all sub-steps concurrently
        tasks = [step.run(input_data) for step in self.sub_steps]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        step_results = []
        combined_data = input_data.copy()
        has_errors = False

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                step_results.append(StepResult(
                    step_name=self.sub_steps[i].name,
                    status=StepStatus.FAILED,
                    data={},
                    error=str(result)
                ))
                has_errors = True
            else:
                step_results.append(result)
                if result.status == StepStatus.SUCCESS:
                    combined_data.update(result.data)
                elif result.status == StepStatus.FAILED:
                    has_errors = True

        # Determine overall status
        if has_errors:
            status = StepStatus.FAILED
            error = f"One or more parallel steps failed"
        else:
            status = StepStatus.SUCCESS
            error = None

        return StepResult(
            step_name=self.name,
            status=status,
            data={
                **combined_data,
                "parallel_results": [
                    {
                        "step": r.step_name,
                        "status": r.status.value,
                        "execution_time": r.execution_time
                    } for r in step_results
                ]
            },
            error=error
        )