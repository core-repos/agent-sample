"""
Step 7: Data Validation
Validates extracted chart data for quality and consistency
"""
from typing import Dict, Any, List
from ..base_step import ConditionalStep, StepResult, StepStatus

class DataValidationStep(ConditionalStep):
    """Validate chart data quality and consistency"""

    def __init__(self):
        super().__init__(
            name="data_validation",
            description="Validate chart data for quality and consistency"
        )

    def get_required_inputs(self) -> List[str]:
        return ["chart_data", "visualization_type"]

    def get_output_keys(self) -> List[str]:
        return ["validated_chart_data", "data_validation_results"]

    def should_execute(self, input_data: Dict[str, Any]) -> bool:
        """Only execute if validation is enabled and we have chart data"""
        settings = input_data.get("settings", {})
        chart_data = input_data.get("chart_data", {})
        return settings.get("enable_validation", True) and bool(chart_data.get("data"))

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Validate chart data"""
        chart_data = input_data["chart_data"]
        viz_type = input_data["visualization_type"]

        validation_results = []
        validated_data = chart_data.copy()

        # 1. Structure Validation
        structure_result = self._validate_structure(chart_data, viz_type)
        validation_results.append(structure_result)

        # 2. Data Type Validation
        type_result = self._validate_data_types(chart_data, viz_type)
        validation_results.append(type_result)

        # 3. Data Quality Validation
        quality_result = self._validate_data_quality(chart_data, viz_type)
        validation_results.append(quality_result)

        # 4. Chart-Specific Validation
        chart_result = self._validate_chart_specific(chart_data, viz_type)
        validation_results.append(chart_result)

        # Apply any fixes
        if any(r.get("suggested_fix") for r in validation_results):
            for result in validation_results:
                if result.get("suggested_fix"):
                    validated_data = result["suggested_fix"]
                    break

        # Determine overall status
        has_critical_errors = any(r["severity"] == "error" for r in validation_results)
        status = StepStatus.FAILED if has_critical_errors else StepStatus.SUCCESS

        return StepResult(
            step_name=self.name,
            status=status,
            data={
                "validated_chart_data": validated_data,
                "data_validation_results": validation_results
            }
        )

    def _validate_structure(self, chart_data: Dict[str, Any], viz_type: str) -> Dict[str, Any]:
        """Validate basic data structure"""
        data = chart_data.get("data", {})

        required_fields = self._get_required_fields(viz_type)
        missing_fields = []

        for field in required_fields:
            if field not in data:
                missing_fields.append(field)

        if missing_fields:
            return {
                "check": "structure",
                "is_valid": False,
                "severity": "error",
                "error": f"Missing required fields for {viz_type}: {missing_fields}"
            }

        return {
            "check": "structure",
            "is_valid": True,
            "severity": "info",
            "message": "Data structure is valid"
        }

    def _validate_data_types(self, chart_data: Dict[str, Any], viz_type: str) -> Dict[str, Any]:
        """Validate data types"""
        data = chart_data.get("data", {})

        # Validate numeric fields
        numeric_fields = ["values", "value"]
        for field in numeric_fields:
            if field in data:
                values = data[field]
                if isinstance(values, list):
                    for i, value in enumerate(values):
                        if not isinstance(value, (int, float)):
                            return {
                                "check": "data_types",
                                "is_valid": False,
                                "severity": "error",
                                "error": f"Non-numeric value at index {i} in {field}: {value}"
                            }
                elif not isinstance(values, (int, float)):
                    return {
                        "check": "data_types",
                        "is_valid": False,
                        "severity": "error",
                        "error": f"Field {field} must be numeric: {type(values)}"
                    }

        return {
            "check": "data_types",
            "is_valid": True,
            "severity": "info",
            "message": "Data types are valid"
        }

    def _validate_data_quality(self, chart_data: Dict[str, Any], viz_type: str) -> Dict[str, Any]:
        """Validate data quality"""
        data = chart_data.get("data", {})

        # Check for empty data
        if not data:
            return {
                "check": "data_quality",
                "is_valid": False,
                "severity": "error",
                "error": "Chart data is empty"
            }

        # Check data point count
        data_count = self._count_data_points(data, viz_type)
        min_points, max_points = self._get_data_point_limits(viz_type)

        if data_count < min_points:
            return {
                "check": "data_quality",
                "is_valid": False,
                "severity": "error",
                "error": f"Insufficient data points: {data_count} < {min_points}"
            }

        if data_count > max_points:
            # Suggest truncation
            truncated_data = self._truncate_data(data, viz_type, max_points)
            return {
                "check": "data_quality",
                "is_valid": False,
                "severity": "warning",
                "error": f"Too many data points: {data_count} > {max_points}",
                "suggested_fix": {"data": truncated_data}
            }

        return {
            "check": "data_quality",
            "is_valid": True,
            "severity": "info",
            "message": f"Data quality is good ({data_count} points)"
        }

    def _validate_chart_specific(self, chart_data: Dict[str, Any], viz_type: str) -> Dict[str, Any]:
        """Chart-specific validation rules"""
        data = chart_data.get("data", {})

        if viz_type == "pie":
            return self._validate_pie_chart(data)
        elif viz_type == "line":
            return self._validate_line_chart(data)
        elif viz_type == "bar":
            return self._validate_bar_chart(data)
        elif viz_type == "indicator":
            return self._validate_indicator_chart(data)

        return {
            "check": "chart_specific",
            "is_valid": True,
            "severity": "info",
            "message": f"No specific validation for {viz_type}"
        }

    def _validate_pie_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate pie chart specific requirements"""
        if "values" in data:
            values = data["values"]

            # Check for negative values
            if any(v < 0 for v in values if isinstance(v, (int, float))):
                return {
                    "check": "pie_chart",
                    "is_valid": False,
                    "severity": "error",
                    "error": "Pie charts cannot have negative values"
                }

            # Check for zero sum
            total = sum(v for v in values if isinstance(v, (int, float)))
            if total <= 0:
                return {
                    "check": "pie_chart",
                    "is_valid": False,
                    "severity": "error",
                    "error": "Pie chart values must sum to a positive number"
                }

        return {
            "check": "pie_chart",
            "is_valid": True,
            "severity": "info",
            "message": "Pie chart validation passed"
        }

    def _validate_line_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate line chart specific requirements"""
        if "dates" in data and "values" in data:
            dates = data["dates"]
            values = data["values"]

            # Check array lengths match
            if len(dates) != len(values):
                return {
                    "check": "line_chart",
                    "is_valid": False,
                    "severity": "error",
                    "error": f"Dates and values length mismatch: {len(dates)} vs {len(values)}"
                }

        return {
            "check": "line_chart",
            "is_valid": True,
            "severity": "info",
            "message": "Line chart validation passed"
        }

    def _validate_bar_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate bar chart specific requirements"""
        if "values" in data and "labels" in data:
            values = data["values"]
            labels = data["labels"]

            # Check array lengths match
            if len(values) != len(labels):
                return {
                    "check": "bar_chart",
                    "is_valid": False,
                    "severity": "error",
                    "error": f"Values and labels length mismatch: {len(values)} vs {len(labels)}"
                }

        return {
            "check": "bar_chart",
            "is_valid": True,
            "severity": "info",
            "message": "Bar chart validation passed"
        }

    def _validate_indicator_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate indicator chart specific requirements"""
        if "value" not in data:
            return {
                "check": "indicator_chart",
                "is_valid": False,
                "severity": "error",
                "error": "Indicator chart must have a value"
            }

        value = data["value"]
        if not isinstance(value, (int, float)):
            return {
                "check": "indicator_chart",
                "is_valid": False,
                "severity": "error",
                "error": "Indicator value must be numeric"
            }

        return {
            "check": "indicator_chart",
            "is_valid": True,
            "severity": "info",
            "message": "Indicator chart validation passed"
        }

    def _get_required_fields(self, viz_type: str) -> List[str]:
        """Get required fields for each chart type"""
        requirements = {
            "bar": ["labels", "values"],
            "pie": ["labels", "values"],
            "line": ["dates", "values"],
            "scatter": ["points"],
            "indicator": ["value"],
            "heatmap": ["matrix"]
        }
        return requirements.get(viz_type, [])

    def _get_data_point_limits(self, viz_type: str) -> tuple:
        """Get min and max data points for each chart type"""
        limits = {
            "bar": (1, 50),
            "pie": (2, 20),
            "line": (2, 1000),
            "scatter": (3, 500),
            "indicator": (1, 1),
            "heatmap": (4, 10000)
        }
        return limits.get(viz_type, (1, 100))

    def _count_data_points(self, data: Dict[str, Any], viz_type: str) -> int:
        """Count data points in chart data"""
        if viz_type == "indicator":
            return 1 if "value" in data else 0
        elif viz_type in ["bar", "pie"]:
            return len(data.get("values", []))
        elif viz_type == "line":
            return len(data.get("dates", []))
        elif viz_type == "scatter":
            return len(data.get("points", []))
        else:
            return 0

    def _truncate_data(self, data: Dict[str, Any], viz_type: str, max_points: int) -> Dict[str, Any]:
        """Truncate data to maximum allowed points"""
        truncated = data.copy()

        if viz_type in ["bar", "pie"]:
            if "values" in truncated:
                truncated["values"] = truncated["values"][:max_points]
            if "labels" in truncated:
                truncated["labels"] = truncated["labels"][:max_points]
        elif viz_type == "line":
            if "dates" in truncated:
                truncated["dates"] = truncated["dates"][:max_points]
            if "values" in truncated:
                truncated["values"] = truncated["values"][:max_points]

        return truncated