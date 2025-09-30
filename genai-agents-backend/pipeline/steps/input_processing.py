"""
Step 1: Input Processing
Validates and processes user input
"""
from typing import Dict, Any, List
from ..base_step import BaseStep, StepResult, StepStatus

class InputProcessingStep(BaseStep):
    """Process and validate user input"""

    def __init__(self):
        super().__init__(
            name="input_processing",
            description="Validate and process user input"
        )

    def get_required_inputs(self) -> List[str]:
        return ["question"]

    def get_output_keys(self) -> List[str]:
        return ["processed_question", "metadata", "settings"]

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that we have a question"""
        return "question" in input_data and bool(input_data["question"].strip())

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Process the input data"""
        question = input_data["question"].strip()

        # Extract settings with defaults
        settings = {
            "enable_validation": input_data.get("enable_validation", True),
            "use_cache": input_data.get("use_cache", True),
            "visualization_hint": input_data.get("visualization_hint"),
            "llm_provider": input_data.get("llm_provider", "anthropic"),
            "timeout": input_data.get("timeout", 120)
        }

        # Analyze question characteristics
        question_lower = question.lower()
        metadata = {
            "question_length": len(question),
            "question_type": self._classify_question_type(question_lower),
            "expected_viz_type": self._predict_visualization_type(question_lower),
            "complexity": self._assess_complexity(question_lower),
            "language": "english"  # Could be enhanced with language detection
        }

        return StepResult(
            step_name=self.name,
            status=StepStatus.SUCCESS,
            data={
                "processed_question": question,
                "metadata": metadata,
                "settings": settings,
                "original_input": input_data
            }
        )

    def _classify_question_type(self, question: str) -> str:
        """Classify the type of question"""
        if any(word in question for word in ["total", "sum", "count", "how many", "how much"]):
            return "aggregation"
        elif any(word in question for word in ["top", "highest", "lowest", "best", "worst", "rank"]):
            return "ranking"
        elif any(word in question for word in ["breakdown", "distribution", "percentage", "split"]):
            return "distribution"
        elif any(word in question for word in ["trend", "over time", "timeline", "daily", "monthly"]):
            return "trend"
        elif any(word in question for word in ["correlation", "relationship", "versus", "compared"]):
            return "correlation"
        elif any(word in question for word in ["average", "mean", "median"]):
            return "statistical"
        else:
            return "general"

    def _predict_visualization_type(self, question: str) -> str:
        """Predict the best visualization type based on question"""
        question_type = self._classify_question_type(question)

        type_to_viz = {
            "aggregation": "indicator",
            "ranking": "bar",
            "distribution": "pie",
            "trend": "line",
            "correlation": "scatter",
            "statistical": "indicator"
        }

        return type_to_viz.get(question_type, "bar")

    def _assess_complexity(self, question: str) -> str:
        """Assess question complexity"""
        complexity_indicators = [
            "and", "or", "but", "where", "when", "group by", "order by",
            "filter", "exclude", "include", "multiple", "compare", "analyze"
        ]

        indicator_count = sum(1 for indicator in complexity_indicators if indicator in question)

        if indicator_count >= 3:
            return "high"
        elif indicator_count >= 1:
            return "medium"
        else:
            return "low"