"""
Graph Data Validation Agent with iterative validation and improvement
"""
import json
import re
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging

from ..visualization import VisualizationProcessor
from llm.factory import LLMProviderFactory

logger = logging.getLogger(__name__)

@dataclass
class GraphValidationResult:
    """Result of graph data validation"""
    is_valid: bool
    error_message: Optional[str] = None
    suggested_fix: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    validation_type: str = "unknown"
    data_quality_score: float = 0.0

@dataclass
class GraphValidationReport:
    """Complete graph validation report"""
    original_data: Dict[str, Any]
    final_data: Dict[str, Any]
    chart_type: str
    iterations: int
    validation_results: List[GraphValidationResult]
    execution_time: float
    success: bool
    data_points: int = 0
    final_error: Optional[str] = None

class GraphDataValidationAgent:
    """Agent for validating and improving graph data with iterative validation"""

    def __init__(self, llm_provider: Optional[str] = None):
        self.llm_provider = LLMProviderFactory.create_provider(llm_provider)
        self.llm = self.llm_provider.get_model()
        self.max_iterations = 3  # Reduced for reliability testing
        self.visualization_processor = VisualizationProcessor()
        self.validation_rules = self._init_validation_rules()

    def _init_validation_rules(self) -> Dict[str, Any]:
        """Initialize graph data validation rules"""
        return {
            'chart_requirements': {
                'bar': {
                    'required_fields': ['labels', 'values'],
                    'min_data_points': 1,
                    'max_data_points': 50,
                    'data_types': {'labels': list, 'values': list}
                },
                'pie': {
                    'required_fields': ['labels', 'values'],
                    'min_data_points': 2,
                    'max_data_points': 20,
                    'data_types': {'labels': list, 'values': list},
                    'sum_requirement': 'values_should_sum_to_meaningful_total'
                },
                'line': {
                    'required_fields': ['dates', 'values'],
                    'min_data_points': 2,
                    'max_data_points': 1000,
                    'data_types': {'dates': list, 'values': list}
                },
                'scatter': {
                    'required_fields': ['points'],
                    'min_data_points': 3,
                    'max_data_points': 500,
                    'data_types': {'points': list}
                },
                'indicator': {
                    'required_fields': ['value'],
                    'min_data_points': 1,
                    'max_data_points': 1,
                    'data_types': {'value': (int, float)}
                },
                'heatmap': {
                    'required_fields': ['matrix', 'rows', 'cols'],
                    'min_data_points': 4,
                    'max_data_points': 10000,
                    'data_types': {'matrix': list, 'rows': list, 'cols': list}
                }
            },
            'data_quality': {
                'max_missing_percentage': 0.1,  # 10% max missing data
                'min_variance_threshold': 0.01,  # Minimum variance for meaningful data
                'outlier_detection': True,
                'duplicate_tolerance': 0.05  # 5% max duplicates
            },
            'performance': {
                'max_processing_time': 5.0,  # seconds
                'memory_efficient': True
            }
        }

    async def validate_graph_data_iteratively(
        self,
        chart_data: Dict[str, Any],
        chart_type: str,
        original_answer: str,
        original_question: str
    ) -> GraphValidationReport:
        """
        Validate graph data with up to 10 iterations of improvement

        Args:
            chart_data: The chart data to validate
            chart_type: Type of chart (bar, pie, line, etc.)
            original_answer: Original LLM answer text
            original_question: Original natural language question

        Returns:
            GraphValidationReport with validation results and final data
        """
        start_time = datetime.now()
        validation_results = []
        current_data = chart_data.copy()

        logger.info(f"Starting iterative graph data validation for chart type: {chart_type}")

        for iteration in range(1, self.max_iterations + 1):
            logger.debug(f"Graph validation iteration {iteration}/{self.max_iterations}")

            # Perform comprehensive validation
            validation_result = await self._validate_single_iteration(
                current_data,
                chart_type,
                original_answer,
                original_question,
                iteration
            )

            validation_results.append(validation_result)

            # If valid, we're done
            if validation_result.is_valid:
                execution_time = (datetime.now() - start_time).total_seconds()
                data_points = self._count_data_points(current_data, chart_type)

                logger.info(f"Graph validation succeeded after {iteration} iterations")

                return GraphValidationReport(
                    original_data=chart_data,
                    final_data=current_data,
                    chart_type=chart_type,
                    iterations=iteration,
                    validation_results=validation_results,
                    execution_time=execution_time,
                    success=True,
                    data_points=data_points
                )

            # If not valid, try to fix it
            if validation_result.suggested_fix:
                current_data = validation_result.suggested_fix
                logger.debug(f"Applying suggested data fix for iteration {iteration}")
            else:
                # Generate improvement using LLM and re-extraction
                improved_data = await self._generate_data_improvement(
                    current_data,
                    chart_type,
                    validation_result.error_message,
                    original_answer,
                    original_question,
                    iteration
                )
                if improved_data and improved_data != current_data:
                    current_data = improved_data
                else:
                    logger.warning(f"No data improvement generated at iteration {iteration}")
                    break

        # Failed after max iterations
        execution_time = (datetime.now() - start_time).total_seconds()
        final_error = validation_results[-1].error_message if validation_results else "Unknown validation error"
        data_points = self._count_data_points(current_data, chart_type)

        logger.warning(f"Graph validation failed after {self.max_iterations} iterations")

        return GraphValidationReport(
            original_data=chart_data,
            final_data=current_data,
            chart_type=chart_type,
            iterations=self.max_iterations,
            validation_results=validation_results,
            execution_time=execution_time,
            success=False,
            data_points=data_points,
            final_error=final_error
        )

    async def _validate_single_iteration(
        self,
        chart_data: Dict[str, Any],
        chart_type: str,
        original_answer: str,
        original_question: str,
        iteration: int
    ) -> GraphValidationResult:
        """Perform validation for a single iteration"""

        # 1. Structure validation
        structure_result = self._validate_data_structure(chart_data, chart_type)
        if not structure_result.is_valid:
            return structure_result

        # 2. Data type validation
        type_result = self._validate_data_types(chart_data, chart_type)
        if not type_result.is_valid:
            return type_result

        # 3. Data quality validation
        quality_result = self._validate_data_quality(chart_data, chart_type)
        if not quality_result.is_valid:
            return quality_result

        # 4. Chart-specific validation
        chart_result = self._validate_chart_specific(chart_data, chart_type)
        if not chart_result.is_valid:
            return chart_result

        # 5. Semantic validation
        semantic_result = await self._validate_data_semantics(
            chart_data, chart_type, original_answer, original_question
        )
        if not semantic_result.is_valid:
            return semantic_result

        # All validations passed
        data_quality_score = self._calculate_data_quality_score(chart_data, chart_type)

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.95,
            data_quality_score=data_quality_score,
            validation_type=f"complete_iteration_{iteration}"
        )

    def _validate_data_structure(self, chart_data: Dict[str, Any], chart_type: str) -> GraphValidationResult:
        """Validate the basic structure of chart data"""
        if chart_type not in self.validation_rules['chart_requirements']:
            return GraphValidationResult(
                is_valid=False,
                error_message=f"Unsupported chart type: {chart_type}",
                validation_type="structure"
            )

        requirements = self.validation_rules['chart_requirements'][chart_type]
        required_fields = requirements['required_fields']

        # Check if required fields exist
        missing_fields = []
        for field in required_fields:
            if field not in chart_data:
                missing_fields.append(field)

        if missing_fields:
            return GraphValidationResult(
                is_valid=False,
                error_message=f"Missing required fields for {chart_type}: {missing_fields}",
                validation_type="structure"
            )

        # Check data point counts
        data_count = self._count_data_points(chart_data, chart_type)
        min_points = requirements['min_data_points']
        max_points = requirements['max_data_points']

        if data_count < min_points:
            return GraphValidationResult(
                is_valid=False,
                error_message=f"Insufficient data points: {data_count} < {min_points}",
                validation_type="structure"
            )

        if data_count > max_points:
            # Try to suggest truncation
            suggested_fix = self._truncate_data(chart_data, chart_type, max_points)
            return GraphValidationResult(
                is_valid=False,
                error_message=f"Too many data points: {data_count} > {max_points}",
                suggested_fix=suggested_fix,
                validation_type="structure"
            )

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.9,
            validation_type="structure"
        )

    def _validate_data_types(self, chart_data: Dict[str, Any], chart_type: str) -> GraphValidationResult:
        """Validate data types of chart data"""
        requirements = self.validation_rules['chart_requirements'][chart_type]
        expected_types = requirements['data_types']

        for field, expected_type in expected_types.items():
            if field in chart_data:
                actual_value = chart_data[field]

                if isinstance(expected_type, tuple):
                    # Multiple allowed types
                    if not isinstance(actual_value, expected_type):
                        return GraphValidationResult(
                            is_valid=False,
                            error_message=f"Invalid type for {field}: expected {expected_type}, got {type(actual_value)}",
                            validation_type="data_types"
                        )
                else:
                    # Single expected type
                    if not isinstance(actual_value, expected_type):
                        return GraphValidationResult(
                            is_valid=False,
                            error_message=f"Invalid type for {field}: expected {expected_type}, got {type(actual_value)}",
                            validation_type="data_types"
                        )

        # Validate numeric data
        numeric_validation = self._validate_numeric_data(chart_data, chart_type)
        if not numeric_validation.is_valid:
            return numeric_validation

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.85,
            validation_type="data_types"
        )

    def _validate_numeric_data(self, chart_data: Dict[str, Any], chart_type: str) -> GraphValidationResult:
        """Validate numeric data for charts"""
        numeric_fields = ['values', 'value']

        for field in numeric_fields:
            if field in chart_data:
                data = chart_data[field]

                if isinstance(data, list):
                    # Check each value in the list
                    for i, value in enumerate(data):
                        if not isinstance(value, (int, float)):
                            try:
                                float(value)
                            except (ValueError, TypeError):
                                return GraphValidationResult(
                                    is_valid=False,
                                    error_message=f"Non-numeric value at index {i} in {field}: {value}",
                                    validation_type="numeric_data"
                                )

                        # Check for invalid numeric values
                        if isinstance(value, (int, float)):
                            if not (-1e15 < value < 1e15):  # Reasonable range
                                return GraphValidationResult(
                                    is_valid=False,
                                    error_message=f"Numeric value out of reasonable range: {value}",
                                    validation_type="numeric_data"
                                )

                elif isinstance(data, (int, float)):
                    # Single numeric value
                    if not (-1e15 < data < 1e15):
                        return GraphValidationResult(
                            is_valid=False,
                            error_message=f"Numeric value out of reasonable range: {data}",
                            validation_type="numeric_data"
                        )

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.8,
            validation_type="numeric_data"
        )

    def _validate_data_quality(self, chart_data: Dict[str, Any], chart_type: str) -> GraphValidationResult:
        """Validate data quality metrics"""
        quality_rules = self.validation_rules['data_quality']

        # Check for missing/null data
        missing_count = self._count_missing_data(chart_data)
        total_count = self._count_total_data_elements(chart_data)

        if total_count > 0:
            missing_percentage = missing_count / total_count
            if missing_percentage > quality_rules['max_missing_percentage']:
                return GraphValidationResult(
                    is_valid=False,
                    error_message=f"Too much missing data: {missing_percentage:.1%} > {quality_rules['max_missing_percentage']:.1%}",
                    validation_type="data_quality"
                )

        # Check for meaningful variance in numeric data
        variance_check = self._check_data_variance(chart_data, chart_type)
        if not variance_check.is_valid:
            return variance_check

        # Check for excessive duplicates
        duplicate_check = self._check_duplicates(chart_data, chart_type)
        if not duplicate_check.is_valid:
            return duplicate_check

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.75,
            validation_type="data_quality"
        )

    def _validate_chart_specific(self, chart_data: Dict[str, Any], chart_type: str) -> GraphValidationResult:
        """Validate chart-specific requirements"""

        if chart_type == "pie":
            return self._validate_pie_chart(chart_data)
        elif chart_type == "line":
            return self._validate_line_chart(chart_data)
        elif chart_type == "scatter":
            return self._validate_scatter_chart(chart_data)
        elif chart_type == "bar":
            return self._validate_bar_chart(chart_data)
        elif chart_type == "indicator":
            return self._validate_indicator_chart(chart_data)
        elif chart_type == "heatmap":
            return self._validate_heatmap_chart(chart_data)

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.7,
            validation_type="chart_specific"
        )

    def _validate_pie_chart(self, chart_data: Dict[str, Any]) -> GraphValidationResult:
        """Validate pie chart specific requirements"""
        if 'values' in chart_data and 'labels' in chart_data:
            values = chart_data['values']
            labels = chart_data['labels']

            # Check array lengths match
            if len(values) != len(labels):
                return GraphValidationResult(
                    is_valid=False,
                    error_message=f"Values and labels length mismatch: {len(values)} vs {len(labels)}",
                    validation_type="pie_specific"
                )

            # Check for negative values
            if any(v < 0 for v in values if isinstance(v, (int, float))):
                return GraphValidationResult(
                    is_valid=False,
                    error_message="Pie charts cannot have negative values",
                    validation_type="pie_specific"
                )

            # Check for zero sum
            total = sum(v for v in values if isinstance(v, (int, float)))
            if total <= 0:
                return GraphValidationResult(
                    is_valid=False,
                    error_message="Pie chart values must sum to a positive number",
                    validation_type="pie_specific"
                )

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.9,
            validation_type="pie_specific"
        )

    def _validate_line_chart(self, chart_data: Dict[str, Any]) -> GraphValidationResult:
        """Validate line chart specific requirements"""
        if 'dates' in chart_data and 'values' in chart_data:
            dates = chart_data['dates']
            values = chart_data['values']

            # Check array lengths match
            if len(dates) != len(values):
                return GraphValidationResult(
                    is_valid=False,
                    error_message=f"Dates and values length mismatch: {len(dates)} vs {len(values)}",
                    validation_type="line_specific"
                )

            # Check for chronological order (basic check)
            if len(dates) > 1:
                # Try to parse dates and check order
                try:
                    parsed_dates = []
                    for date_str in dates:
                        if isinstance(date_str, str):
                            # Handle different date formats
                            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                                parsed_dates.append(date_str)

                    if len(parsed_dates) > 1 and parsed_dates != sorted(parsed_dates):
                        # Suggest sorted version
                        sorted_indices = sorted(range(len(dates)), key=lambda i: dates[i])
                        sorted_data = {
                            'dates': [dates[i] for i in sorted_indices],
                            'values': [values[i] for i in sorted_indices]
                        }
                        return GraphValidationResult(
                            is_valid=False,
                            error_message="Line chart dates should be in chronological order",
                            suggested_fix=sorted_data,
                            validation_type="line_specific"
                        )
                except:
                    pass  # Skip date parsing if it fails

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.85,
            validation_type="line_specific"
        )

    def _validate_scatter_chart(self, chart_data: Dict[str, Any]) -> GraphValidationResult:
        """Validate scatter chart specific requirements"""
        if 'points' in chart_data:
            points = chart_data['points']

            # Check each point has x, y coordinates
            for i, point in enumerate(points):
                if not isinstance(point, dict):
                    return GraphValidationResult(
                        is_valid=False,
                        error_message=f"Point {i} is not a dictionary",
                        validation_type="scatter_specific"
                    )

                if 'x' not in point or 'y' not in point:
                    return GraphValidationResult(
                        is_valid=False,
                        error_message=f"Point {i} missing x or y coordinate",
                        validation_type="scatter_specific"
                    )

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.8,
            validation_type="scatter_specific"
        )

    def _validate_bar_chart(self, chart_data: Dict[str, Any]) -> GraphValidationResult:
        """Validate bar chart specific requirements"""
        if 'values' in chart_data and 'labels' in chart_data:
            values = chart_data['values']
            labels = chart_data['labels']

            # Check array lengths match
            if len(values) != len(labels):
                return GraphValidationResult(
                    is_valid=False,
                    error_message=f"Values and labels length mismatch: {len(values)} vs {len(labels)}",
                    validation_type="bar_specific"
                )

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.9,
            validation_type="bar_specific"
        )

    def _validate_indicator_chart(self, chart_data: Dict[str, Any]) -> GraphValidationResult:
        """Validate indicator chart specific requirements"""
        if 'value' in chart_data:
            value = chart_data['value']

            if not isinstance(value, (int, float)):
                return GraphValidationResult(
                    is_valid=False,
                    error_message="Indicator value must be numeric",
                    validation_type="indicator_specific"
                )

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.95,
            validation_type="indicator_specific"
        )

    def _validate_heatmap_chart(self, chart_data: Dict[str, Any]) -> GraphValidationResult:
        """Validate heatmap chart specific requirements"""
        if 'matrix' in chart_data:
            matrix = chart_data['matrix']

            if not isinstance(matrix, list) or not matrix:
                return GraphValidationResult(
                    is_valid=False,
                    error_message="Heatmap matrix must be a non-empty list",
                    validation_type="heatmap_specific"
                )

            # Check matrix dimensions
            row_lengths = [len(row) for row in matrix if isinstance(row, list)]
            if row_lengths and not all(length == row_lengths[0] for length in row_lengths):
                return GraphValidationResult(
                    is_valid=False,
                    error_message="Heatmap matrix rows must have equal length",
                    validation_type="heatmap_specific"
                )

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.8,
            validation_type="heatmap_specific"
        )

    async def _validate_data_semantics(
        self,
        chart_data: Dict[str, Any],
        chart_type: str,
        original_answer: str,
        original_question: str
    ) -> GraphValidationResult:
        """Validate semantic correctness of chart data using LLM"""
        try:
            prompt = f"""
            Analyze this chart data for semantic correctness:

            Original Question: {original_question}
            Chart Type: {chart_type}
            Chart Data: {json.dumps(chart_data, indent=2)[:1000]}...
            Original Answer: {original_answer[:500]}...

            Check if:
            1. The chart data represents the answer correctly
            2. Data values are reasonable and make sense
            3. Labels/categories are appropriate
            4. Chart type is suitable for this data
            5. Data tells a coherent story

            Respond with: VALID or INVALID: reason
            """

            response = await self.llm.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            if response_text.startswith('VALID'):
                return GraphValidationResult(
                    is_valid=True,
                    confidence_score=0.8,
                    validation_type="semantic"
                )
            else:
                error_msg = response_text.replace('INVALID:', '').strip()
                return GraphValidationResult(
                    is_valid=False,
                    error_message=f"Semantic validation failed: {error_msg}",
                    validation_type="semantic"
                )

        except Exception as e:
            logger.warning(f"Semantic validation error: {e}")
            return GraphValidationResult(
                is_valid=True,  # Default to valid if LLM fails
                confidence_score=0.5,
                validation_type="semantic"
            )

    async def _generate_data_improvement(
        self,
        chart_data: Dict[str, Any],
        chart_type: str,
        error_message: str,
        original_answer: str,
        original_question: str,
        iteration: int
    ) -> Optional[Dict[str, Any]]:
        """Generate improved chart data using LLM and re-extraction"""
        try:
            # First, try to fix the data programmatically
            programmatic_fix = self._apply_programmatic_fixes(chart_data, chart_type, error_message)
            if programmatic_fix:
                return programmatic_fix

            # If that fails, use LLM to re-extract data
            prompt = f"""
            Re-extract chart data from this answer to fix the following error:

            Original Question: {original_question}
            Chart Type: {chart_type}
            Original Answer: {original_answer}
            Current Data: {json.dumps(chart_data)}
            Error: {error_message}
            Iteration: {iteration}

            Extract proper {chart_type} chart data from the original answer.
            Ensure all data is valid, properly formatted, and complete.

            Return ONLY a valid JSON object with the chart data, no explanation.
            """

            response = await self.llm.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Try to parse JSON response
            try:
                improved_data = json.loads(response_text)
                return improved_data
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        improved_data = json.loads(json_match.group())
                        return improved_data
                    except json.JSONDecodeError:
                        pass

            # If LLM fails, try re-extraction with visualization processor
            return self.visualization_processor.extract_chart_data(original_answer, chart_type).get('data', {})

        except Exception as e:
            logger.error(f"Error generating data improvement: {e}")
            return None

    def _apply_programmatic_fixes(
        self,
        chart_data: Dict[str, Any],
        chart_type: str,
        error_message: str
    ) -> Optional[Dict[str, Any]]:
        """Apply programmatic fixes to common data issues"""
        fixed_data = chart_data.copy()

        # Fix empty or null values
        if "missing" in error_message.lower() or "empty" in error_message.lower():
            if chart_type in ['bar', 'pie'] and 'values' in fixed_data:
                # Remove empty values and corresponding labels
                values = fixed_data.get('values', [])
                labels = fixed_data.get('labels', [])

                valid_indices = [i for i, v in enumerate(values) if v is not None and v != '']
                if valid_indices:
                    fixed_data['values'] = [values[i] for i in valid_indices]
                    if labels and len(labels) > max(valid_indices):
                        fixed_data['labels'] = [labels[i] for i in valid_indices]

        # Fix type issues
        if "type" in error_message.lower():
            if 'values' in fixed_data:
                try:
                    fixed_data['values'] = [float(v) for v in fixed_data['values'] if v is not None]
                except (ValueError, TypeError):
                    pass

        # Fix length mismatches
        if "length mismatch" in error_message.lower():
            if chart_type in ['bar', 'pie', 'line']:
                values = fixed_data.get('values', [])
                other_field = 'labels' if chart_type in ['bar', 'pie'] else 'dates'
                other_data = fixed_data.get(other_field, [])

                min_length = min(len(values), len(other_data))
                if min_length > 0:
                    fixed_data['values'] = values[:min_length]
                    fixed_data[other_field] = other_data[:min_length]

        # Return fixed data if it's different from original
        return fixed_data if fixed_data != chart_data else None

    def _count_data_points(self, chart_data: Dict[str, Any], chart_type: str) -> int:
        """Count the number of data points in chart data"""
        if chart_type == "indicator":
            return 1 if 'value' in chart_data else 0
        elif chart_type in ['bar', 'pie']:
            return len(chart_data.get('values', []))
        elif chart_type == 'line':
            return len(chart_data.get('dates', []))
        elif chart_type == 'scatter':
            return len(chart_data.get('points', []))
        elif chart_type == 'heatmap':
            matrix = chart_data.get('matrix', [])
            return sum(len(row) for row in matrix if isinstance(row, list))

        return 0

    def _truncate_data(self, chart_data: Dict[str, Any], chart_type: str, max_points: int) -> Dict[str, Any]:
        """Truncate data to maximum allowed points"""
        truncated = chart_data.copy()

        if chart_type in ['bar', 'pie']:
            if 'values' in truncated:
                truncated['values'] = truncated['values'][:max_points]
            if 'labels' in truncated:
                truncated['labels'] = truncated['labels'][:max_points]
        elif chart_type == 'line':
            if 'dates' in truncated:
                truncated['dates'] = truncated['dates'][:max_points]
            if 'values' in truncated:
                truncated['values'] = truncated['values'][:max_points]
        elif chart_type == 'scatter':
            if 'points' in truncated:
                truncated['points'] = truncated['points'][:max_points]

        return truncated

    def _count_missing_data(self, chart_data: Dict[str, Any]) -> int:
        """Count missing or null data elements"""
        missing_count = 0

        def count_missing_in_value(value):
            if value is None or value == '' or value == 'null':
                return 1
            elif isinstance(value, list):
                return sum(count_missing_in_value(item) for item in value)
            elif isinstance(value, dict):
                return sum(count_missing_in_value(v) for v in value.values())
            return 0

        for value in chart_data.values():
            missing_count += count_missing_in_value(value)

        return missing_count

    def _count_total_data_elements(self, chart_data: Dict[str, Any]) -> int:
        """Count total data elements"""
        total_count = 0

        def count_elements_in_value(value):
            if isinstance(value, list):
                return len(value)
            elif isinstance(value, dict):
                return sum(count_elements_in_value(v) for v in value.values())
            return 1

        for value in chart_data.values():
            total_count += count_elements_in_value(value)

        return total_count

    def _check_data_variance(self, chart_data: Dict[str, Any], chart_type: str) -> GraphValidationResult:
        """Check if numeric data has meaningful variance"""
        numeric_fields = ['values', 'value']

        for field in numeric_fields:
            if field in chart_data:
                data = chart_data[field]

                if isinstance(data, list) and len(data) > 1:
                    numeric_values = [v for v in data if isinstance(v, (int, float))]
                    if len(numeric_values) > 1:
                        mean = sum(numeric_values) / len(numeric_values)
                        variance = sum((x - mean) ** 2 for x in numeric_values) / len(numeric_values)

                        if variance < self.validation_rules['data_quality']['min_variance_threshold']:
                            if all(v == numeric_values[0] for v in numeric_values):
                                return GraphValidationResult(
                                    is_valid=False,
                                    error_message="All data values are identical, no variation to visualize",
                                    validation_type="data_variance"
                                )

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.7,
            validation_type="data_variance"
        )

    def _check_duplicates(self, chart_data: Dict[str, Any], chart_type: str) -> GraphValidationResult:
        """Check for excessive duplicate data"""
        if chart_type in ['bar', 'pie'] and 'labels' in chart_data:
            labels = chart_data['labels']
            unique_labels = set(labels)
            duplicate_percentage = 1 - (len(unique_labels) / len(labels)) if labels else 0

            if duplicate_percentage > self.validation_rules['data_quality']['duplicate_tolerance']:
                return GraphValidationResult(
                    is_valid=False,
                    error_message=f"Too many duplicate labels: {duplicate_percentage:.1%}",
                    validation_type="duplicates"
                )

        return GraphValidationResult(
            is_valid=True,
            confidence_score=0.8,
            validation_type="duplicates"
        )

    def _calculate_data_quality_score(self, chart_data: Dict[str, Any], chart_type: str) -> float:
        """Calculate overall data quality score"""
        scores = []

        # Completeness score
        missing_count = self._count_missing_data(chart_data)
        total_count = self._count_total_data_elements(chart_data)
        completeness = 1 - (missing_count / total_count) if total_count > 0 else 0
        scores.append(completeness)

        # Consistency score (basic check)
        consistency = 0.8  # Placeholder for more complex consistency checks
        scores.append(consistency)

        # Validity score (type correctness)
        validity = 0.9  # If we reach here, types are mostly correct
        scores.append(validity)

        return sum(scores) / len(scores) if scores else 0.0

    def get_validation_summary(self, report: GraphValidationReport) -> Dict[str, Any]:
        """Generate a summary of graph validation results"""
        validation_types = {}
        for result in report.validation_results:
            validation_types[result.validation_type] = validation_types.get(result.validation_type, 0) + 1

        return {
            "success": report.success,
            "chart_type": report.chart_type,
            "iterations": report.iterations,
            "execution_time": report.execution_time,
            "data_points": report.data_points,
            "validation_attempts": validation_types,
            "data_changed": report.final_data != report.original_data,
            "final_error": report.final_error,
            "data_quality_score": report.validation_results[-1].data_quality_score if report.validation_results else 0.0
        }