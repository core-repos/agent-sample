"""
Step 6: Chart Data Extraction
Extracts structured data for chart visualization from query results
"""
from typing import Dict, Any, List, Optional
from ..base_step import BaseStep, StepResult, StepStatus
from agents.bigquery.visualization import VisualizationProcessor
import re
import logging

logger = logging.getLogger(__name__)

class ChartDataExtractionStep(BaseStep):
    """Extract structured chart data from query results"""

    def __init__(self):
        super().__init__(
            name="chart_data_extraction",
            description="Extract structured data for chart visualization"
        )
        self.visualization_processor = VisualizationProcessor()

    def get_required_inputs(self) -> List[str]:
        return ["visualization_type", "query_result", "llm_response"]

    def get_output_keys(self) -> List[str]:
        return ["chart_data", "extraction_metadata"]

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Extract chart data from query results"""
        viz_type = input_data["visualization_type"]
        query_result = input_data.get("query_result", "")
        llm_response = input_data.get("llm_response", "")

        try:
            # Use the existing visualization processor to extract data
            chart_data = self.visualization_processor.extract_chart_data(llm_response, viz_type)

            # If chart data extraction from LLM response failed, try query result
            if not chart_data.get("data") and query_result:
                chart_data = self.visualization_processor.extract_chart_data(query_result, viz_type)

            # If still no data, try alternative extraction methods
            if not chart_data.get("data"):
                chart_data = self._fallback_extraction(query_result, viz_type)

            # Generate extraction metadata
            extraction_metadata = {
                "extraction_method": self._determine_extraction_method(chart_data, llm_response, query_result),
                "data_points": self._count_data_points(chart_data.get("data", {}), viz_type),
                "data_quality": self._assess_data_quality(chart_data.get("data", {}), viz_type),
                "extraction_success": bool(chart_data.get("data"))
            }

            # Add insights if available
            if chart_data.get("data"):
                insights = self.visualization_processor.extract_insights(llm_response or query_result, viz_type)
                chart_data["insights"] = insights

            return StepResult(
                step_name=self.name,
                status=StepStatus.SUCCESS,
                data={
                    "chart_data": chart_data,
                    "extraction_metadata": extraction_metadata
                }
            )

        except Exception as e:
            logger.error(f"Chart data extraction failed: {e}")
            return StepResult(
                step_name=self.name,
                status=StepStatus.FAILED,
                data={},
                error=f"Chart data extraction failed: {str(e)}"
            )

    def _fallback_extraction(self, result: str, viz_type: str) -> Dict[str, Any]:
        """Fallback extraction methods when standard extraction fails"""
        if not result:
            return {"type": viz_type, "data": {}}

        try:
            if viz_type == "indicator":
                return self._extract_indicator_fallback(result)
            elif viz_type == "bar":
                return self._extract_bar_fallback(result)
            elif viz_type == "pie":
                return self._extract_pie_fallback(result)
            elif viz_type == "line":
                return self._extract_line_fallback(result)
            else:
                return self._extract_generic_fallback(result, viz_type)

        except Exception as e:
            logger.warning(f"Fallback extraction failed for {viz_type}: {e}")
            return {"type": viz_type, "data": {}}

    def _extract_indicator_fallback(self, result: str) -> Dict[str, Any]:
        """Extract single indicator value"""
        # Look for any numeric value
        numbers = re.findall(r'[\d,]+\.?\d*', result)
        if numbers:
            try:
                value = float(numbers[0].replace(',', ''))
                return {
                    "type": "indicator",
                    "data": {
                        "value": value,
                        "title": "Metric",
                        "format": "currency" if "$" in result else "number"
                    }
                }
            except ValueError:
                pass

        return {"type": "indicator", "data": {}}

    def _extract_bar_fallback(self, result: str) -> Dict[str, Any]:
        """Extract bar chart data from raw result"""
        lines = result.strip().split('\n')
        labels = []
        values = []

        for line in lines:
            # Try to extract label and value from each line
            parts = line.split()
            if len(parts) >= 2:
                label_parts = []
                value = None

                for part in parts:
                    # Check if this part looks like a number
                    clean_part = re.sub(r'[^\d.]', '', part)
                    if clean_part and '.' in clean_part or clean_part.isdigit():
                        try:
                            value = float(clean_part)
                            break
                        except ValueError:
                            pass
                    else:
                        label_parts.append(part)

                if value is not None and label_parts:
                    labels.append(' '.join(label_parts))
                    values.append(value)

        if labels and values:
            return {
                "type": "bar",
                "data": {"labels": labels, "values": values}
            }

        return {"type": "bar", "data": {}}

    def _extract_pie_fallback(self, result: str) -> Dict[str, Any]:
        """Extract pie chart data from raw result"""
        # Similar to bar but look for percentages
        return self._extract_bar_fallback(result)  # Reuse bar logic for now

    def _extract_line_fallback(self, result: str) -> Dict[str, Any]:
        """Extract line chart data from raw result"""
        lines = result.strip().split('\n')
        dates = []
        values = []

        for line in lines:
            # Look for date patterns
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', line)
            if date_match:
                date = date_match.group()
                # Look for numeric value in the same line
                numbers = re.findall(r'[\d,]+\.?\d*', line)
                if numbers:
                    try:
                        value = float(numbers[-1].replace(',', ''))  # Take last number
                        dates.append(date)
                        values.append(value)
                    except ValueError:
                        pass

        if dates and values:
            return {
                "type": "line",
                "data": {"dates": dates, "values": values}
            }

        return {"type": "line", "data": {}}

    def _extract_generic_fallback(self, result: str, viz_type: str) -> Dict[str, Any]:
        """Generic extraction for other chart types"""
        # Try to extract any label-value pairs
        lines = result.strip().split('\n')
        labels = []
        values = []

        for line in lines:
            # Split on common delimiters
            for delimiter in [':', '|', '\t']:
                if delimiter in line:
                    parts = line.split(delimiter)
                    if len(parts) >= 2:
                        label = parts[0].strip()
                        value_str = parts[1].strip()

                        # Extract numeric value
                        numbers = re.findall(r'[\d,]+\.?\d*', value_str)
                        if numbers:
                            try:
                                value = float(numbers[0].replace(',', ''))
                                labels.append(label)
                                values.append(value)
                                break
                            except ValueError:
                                pass

        if labels and values:
            return {
                "type": viz_type,
                "data": {"labels": labels, "values": values}
            }

        return {"type": viz_type, "data": {}}

    def _determine_extraction_method(self, chart_data: Dict, llm_response: str, query_result: str) -> str:
        """Determine which extraction method was used"""
        if chart_data.get("data"):
            if llm_response and self.visualization_processor.extract_chart_data(llm_response, "bar").get("data"):
                return "llm_response_standard"
            elif query_result:
                return "query_result_fallback"
            else:
                return "manual_fallback"
        else:
            return "extraction_failed"

    def _count_data_points(self, data: Dict[str, Any], viz_type: str) -> int:
        """Count the number of data points"""
        if viz_type == "indicator":
            return 1 if data.get("value") is not None else 0
        elif viz_type in ["bar", "pie"]:
            return len(data.get("values", []))
        elif viz_type == "line":
            return len(data.get("dates", []))
        elif viz_type == "scatter":
            return len(data.get("points", []))
        else:
            return len(data.get("labels", [])) if "labels" in data else 0

    def _assess_data_quality(self, data: Dict[str, Any], viz_type: str) -> str:
        """Assess the quality of extracted data"""
        data_points = self._count_data_points(data, viz_type)

        if data_points == 0:
            return "no_data"
        elif data_points < 2 and viz_type not in ["indicator"]:
            return "insufficient_data"
        elif data_points > 100:
            return "too_much_data"
        else:
            return "good"