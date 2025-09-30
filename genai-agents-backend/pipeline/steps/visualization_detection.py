"""
Step 5: Visualization Detection
Determines the best visualization type for the query and result
"""
from typing import Dict, Any, List, Optional, Tuple
from ..base_step import BaseStep, StepResult, StepStatus

class VisualizationDetectionStep(BaseStep):
    """Detect appropriate visualization type based on query and data"""

    def __init__(self):
        super().__init__(
            name="visualization_detection",
            description="Determine best visualization type for the data"
        )
        self.visualization_patterns = self._init_visualization_patterns()

    def get_required_inputs(self) -> List[str]:
        return ["processed_question", "query_result"]

    def get_output_keys(self) -> List[str]:
        return ["visualization_type", "detection_metadata"]

    def _init_visualization_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for detecting visualization types"""
        return {
            "bar": ["top", "highest", "lowest", "ranking", "best", "worst", "compare"],
            "pie": ["distribution", "breakdown", "proportion", "percentage", "split", "composition"],
            "line": ["trend", "over time", "timeline", "progression", "historical", "daily", "monthly"],
            "scatter": ["correlation", "relationship", "versus", "compared to"],
            "heatmap": ["matrix", "grid", "cross-reference", "by day and hour"],
            "treemap": ["hierarchical", "nested", "drill-down", "category breakdown"],
            "funnel": ["conversion", "pipeline", "stages", "drop-off"],
            "gauge": ["score", "rating", "utilization", "capacity"],
            "indicator": ["total", "sum", "count", "average", "metric", "kpi"],
            "area": ["cumulative", "stacked", "accumulated"],
            "bubble": ["three dimensions", "size and", "weighted"],
            "waterfall": ["changes", "bridge", "incremental"],
            "sankey": ["flow", "transfer", "movement"],
            "radar": ["multi-dimensional", "comparison across", "profile"]
        }

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Determine the best visualization type"""
        question = input_data["processed_question"]
        query_result = input_data.get("query_result", "")
        metadata = input_data.get("metadata", {})
        execution_metadata = input_data.get("execution_metadata", {})

        # Use hint if provided
        settings = input_data.get("settings", {})
        hint = settings.get("visualization_hint")

        if hint and hint in self.visualization_patterns:
            detection_metadata = {
                "detection_method": "user_hint",
                "confidence": 1.0,
                "alternative_suggestions": []
            }

            return StepResult(
                step_name=self.name,
                status=StepStatus.SUCCESS,
                data={
                    "visualization_type": hint,
                    "detection_metadata": detection_metadata
                }
            )

        # Detect visualization type using multiple methods
        detection_result = self._detect_visualization_type(
            question, query_result, metadata, execution_metadata
        )

        return StepResult(
            step_name=self.name,
            status=StepStatus.SUCCESS,
            data={
                "visualization_type": detection_result["type"],
                "detection_metadata": detection_result["metadata"]
            }
        )

    def _detect_visualization_type(
        self,
        question: str,
        result: str,
        metadata: Dict[str, Any],
        execution_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect visualization type using multiple approaches"""

        question_lower = question.lower()
        result_lower = result.lower() if result else ""

        # Method 1: Pattern matching in question
        pattern_scores = {}
        for viz_type, patterns in self.visualization_patterns.items():
            score = sum(1 for pattern in patterns if pattern in question_lower)
            if score > 0:
                pattern_scores[viz_type] = score

        # Method 2: Metadata-based detection
        predicted_type = metadata.get("expected_viz_type")
        question_type = metadata.get("question_type")

        # Method 3: Result structure analysis
        structure_type = self._analyze_result_structure(result, execution_metadata)

        # Method 4: Combined analysis
        combined_text = question_lower + " " + result_lower

        # Score different visualization types
        viz_scores = {}

        # Pattern-based scoring
        for viz_type, score in pattern_scores.items():
            viz_scores[viz_type] = viz_scores.get(viz_type, 0) + score * 0.4

        # Metadata-based scoring
        if predicted_type:
            viz_scores[predicted_type] = viz_scores.get(predicted_type, 0) + 0.3

        # Structure-based scoring
        if structure_type:
            viz_scores[structure_type] = viz_scores.get(structure_type, 0) + 0.2

        # Fallback analysis
        fallback_type = self._fallback_detection(combined_text, execution_metadata)
        if fallback_type:
            viz_scores[fallback_type] = viz_scores.get(fallback_type, 0) + 0.1

        # Determine best visualization type
        if viz_scores:
            best_type = max(viz_scores, key=viz_scores.get)
            confidence = min(viz_scores[best_type], 1.0)

            # Get alternative suggestions
            sorted_scores = sorted(viz_scores.items(), key=lambda x: x[1], reverse=True)
            alternatives = [{"type": t, "score": s} for t, s in sorted_scores[1:4]]
        else:
            # Ultimate fallback
            best_type = "bar"  # Default safe choice
            confidence = 0.2
            alternatives = []

        return {
            "type": best_type,
            "metadata": {
                "detection_method": "multi_method",
                "confidence": confidence,
                "pattern_scores": pattern_scores,
                "predicted_type": predicted_type,
                "structure_type": structure_type,
                "question_type": question_type,
                "alternative_suggestions": alternatives
            }
        }

    def _analyze_result_structure(self, result: str, execution_metadata: Dict[str, Any]) -> Optional[str]:
        """Analyze result structure to suggest visualization"""
        if not result:
            return None

        row_count = execution_metadata.get("row_count", 0)
        query_type = execution_metadata.get("query_type", "")

        # Single value results
        if row_count == 1 or query_type == "aggregation":
            return "indicator"

        # Multiple rows with ranking
        if query_type == "ranking" and row_count <= 20:
            return "bar"

        # Grouping results
        if query_type == "grouping":
            if row_count <= 10:
                return "pie"
            else:
                return "bar"

        # Time-based data
        if execution_metadata.get("contains_dates") and row_count > 2:
            return "line"

        # Large datasets
        if row_count > 50:
            return "heatmap"

        return None

    def _fallback_detection(self, combined_text: str, execution_metadata: Dict[str, Any]) -> Optional[str]:
        """Fallback detection based on simple keywords"""
        if any(word in combined_text for word in ["top", "ranking", "highest", "lowest"]):
            return "bar"
        elif any(word in combined_text for word in ["distribution", "breakdown", "percentage"]):
            return "pie"
        elif any(word in combined_text for word in ["trend", "over time", "daily", "monthly"]):
            return "line"
        elif any(word in combined_text for word in ["total", "sum", "count", "average"]):
            return "indicator"
        elif any(word in combined_text for word in ["correlation", "relationship", "versus"]):
            return "scatter"

        return None