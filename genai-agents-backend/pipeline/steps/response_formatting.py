"""
Step 8: Response Formatting
Formats final response for frontend consumption
"""
from typing import Dict, Any, List
from ..base_step import BaseStep, StepResult, StepStatus
from datetime import datetime

class ResponseFormattingStep(BaseStep):
    """Format final response for frontend"""

    def __init__(self):
        super().__init__(
            name="response_formatting",
            description="Format final response for frontend consumption"
        )

    def get_required_inputs(self) -> List[str]:
        return ["processed_question"]

    def get_output_keys(self) -> List[str]:
        return ["final_response"]

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Format the final response"""
        try:
            # Build the final response
            final_response = self._build_response(input_data)

            return StepResult(
                step_name=self.name,
                status=StepStatus.SUCCESS,
                data={"final_response": final_response}
            )

        except Exception as e:
            self.logger.error(f"Response formatting failed: {e}")
            # Even if formatting fails, return a basic response
            basic_response = self._build_error_response(input_data, str(e))

            return StepResult(
                step_name=self.name,
                status=StepStatus.SUCCESS,  # Don't fail the whole pipeline
                data={"final_response": basic_response}
            )

    def _build_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the complete response"""
        # Base response structure
        response = {
            "success": True,
            "answer": data.get("llm_response", "Query processed successfully"),
            "timestamp": datetime.now().isoformat()
        }

        # Add SQL information
        if "sql_query" in data or "validated_sql" in data:
            response["sql_query"] = data.get("validated_sql") or data.get("sql_query")

        # Add visualization information
        if "visualization_type" in data:
            response["visualization"] = data["visualization_type"]

        # Add chart data
        if "validated_chart_data" in data:
            chart_data = data["validated_chart_data"]
            response["chart_data"] = chart_data.get("data", {})
            if chart_data.get("insights"):
                response["insights"] = chart_data["insights"]
        elif "chart_data" in data:
            chart_data = data["chart_data"]
            response["chart_data"] = chart_data.get("data", {})
            if chart_data.get("insights"):
                response["insights"] = chart_data["insights"]

        # Add pipeline metadata
        pipeline_metadata = self._build_pipeline_metadata(data)
        if pipeline_metadata:
            response["pipeline_metadata"] = pipeline_metadata

        # Add validation information if available
        validation_info = self._build_validation_info(data)
        if validation_info:
            response["validation_report"] = validation_info

        # Add warnings
        warnings = self._collect_warnings(data)
        if warnings:
            response["warnings"] = warnings

        # Add metadata
        response["metadata"] = self._build_metadata(data)

        return response

    def _build_error_response(self, data: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Build error response"""
        return {
            "success": False,
            "answer": f"An error occurred while processing your query: {error}",
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "processed_question": data.get("processed_question", ""),
                "error_step": "response_formatting"
            }
        }

    def _build_pipeline_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build pipeline execution metadata"""
        metadata = {}

        # Add step execution information
        steps_completed = []
        total_execution_time = 0

        # Check which steps completed
        step_indicators = [
            ("input_processing", "metadata"),
            ("sql_generation", "sql_query"),
            ("sql_validation", "validation_results"),
            ("sql_execution", "query_result"),
            ("visualization_detection", "visualization_type"),
            ("chart_data_extraction", "chart_data"),
            ("data_validation", "data_validation_results"),
            ("response_formatting", "final_response")
        ]

        for step_name, indicator_key in step_indicators:
            if indicator_key in data:
                steps_completed.append(step_name)

        metadata["steps_completed"] = steps_completed
        metadata["total_steps"] = len(step_indicators)

        # Add timing information if available
        if "generation_metadata" in data:
            gen_meta = data["generation_metadata"]
            metadata["llm_provider"] = gen_meta.get("llm_provider")
            metadata["model"] = gen_meta.get("model")

        return metadata

    def _build_validation_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build validation information"""
        validation_info = {}

        # SQL validation results
        if "validation_results" in data:
            sql_results = data["validation_results"]
            validation_info["sql_validation"] = {
                "total_checks": len(sql_results),
                "passed_checks": sum(1 for r in sql_results if r.get("is_valid")),
                "query_modified": data.get("validated_sql") != data.get("sql_query")
            }

        # Data validation results
        if "data_validation_results" in data:
            data_results = data["data_validation_results"]
            validation_info["data_validation"] = {
                "total_checks": len(data_results),
                "passed_checks": sum(1 for r in data_results if r.get("is_valid")),
                "data_modified": "validated_chart_data" in data
            }

        # Overall validation success
        if validation_info:
            sql_success = validation_info.get("sql_validation", {}).get("passed_checks", 0) > 0
            data_success = validation_info.get("data_validation", {}).get("passed_checks", 0) > 0
            validation_info["success"] = sql_success and data_success

        return validation_info

    def _collect_warnings(self, data: Dict[str, Any]) -> List[str]:
        """Collect warnings from pipeline execution"""
        warnings = []

        # SQL validation warnings
        if "validation_results" in data:
            for result in data["validation_results"]:
                if not result.get("is_valid") and result.get("severity") == "warning":
                    warnings.append(f"SQL: {result.get('error', 'Unknown warning')}")

        # Data validation warnings
        if "data_validation_results" in data:
            for result in data["data_validation_results"]:
                if not result.get("is_valid") and result.get("severity") == "warning":
                    warnings.append(f"Data: {result.get('error', 'Unknown warning')}")

        # Query modification warnings
        if data.get("validated_sql") and data.get("validated_sql") != data.get("sql_query"):
            warnings.append("SQL query was modified during validation")

        # Chart data warnings
        if "extraction_metadata" in data:
            extraction_meta = data["extraction_metadata"]
            if extraction_meta.get("data_quality") == "insufficient_data":
                warnings.append("Insufficient data for optimal visualization")
            elif extraction_meta.get("data_quality") == "too_much_data":
                warnings.append("Large dataset may affect visualization performance")

        return warnings

    def _build_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build general metadata"""
        metadata = {
            "question_processed": data.get("processed_question", ""),
            "pipeline_version": "1.0",
            "timestamp": datetime.now().isoformat()
        }

        # Add input metadata
        if "metadata" in data:
            input_meta = data["metadata"]
            metadata.update({
                "question_type": input_meta.get("question_type"),
                "complexity": input_meta.get("complexity"),
                "expected_viz_type": input_meta.get("expected_viz_type")
            })

        # Add execution metadata
        if "execution_metadata" in data:
            exec_meta = data["execution_metadata"]
            metadata.update({
                "query_type": exec_meta.get("query_type"),
                "result_type": exec_meta.get("result_type"),
                "row_count": exec_meta.get("row_count")
            })

        # Add detection metadata
        if "detection_metadata" in data:
            detect_meta = data["detection_metadata"]
            metadata.update({
                "detection_method": detect_meta.get("detection_method"),
                "detection_confidence": detect_meta.get("confidence")
            })

        return metadata