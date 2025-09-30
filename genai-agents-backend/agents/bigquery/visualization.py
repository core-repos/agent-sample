"""
Visualization detection and data extraction for BigQuery results
"""
import re
from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class VisualizationProcessor:
    """Process query results for visualization"""
    
    def __init__(self):
        self.visualization_patterns = self._init_visualization_patterns()
        
    def _init_visualization_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for detecting visualization types"""
        return {
            "bar": ["top", "highest", "lowest", "ranking", "best", "worst", "compare", "top 5", "top 10"],
            "pie": ["distribution", "breakdown", "proportion", "percentage", "split", "composition"],
            "line": ["trend", "over time", "timeline", "progression", "historical", "daily trend", "monthly trend", "by date"],
            "area": ["cumulative", "stacked", "accumulated", "running total", "cumulative cost"],
            "scatter": ["correlation", "relationship", "versus", "compared to"],
            "heatmap": ["matrix", "grid", "cross-reference", "by day and hour"],
            "treemap": ["hierarchical", "nested", "drill-down", "category breakdown"],
            "funnel": ["conversion", "pipeline", "stages", "drop-off"],
            "gauge": ["score", "rating", "utilization", "capacity"],
            "indicator": ["total", "sum", "count", "average", "metric", "kpi"],
            "bubble": ["three dimensions", "size and", "weighted"],
            "waterfall": ["changes", "bridge", "incremental"],
            "sankey": ["flow", "transfer", "movement"],
            "radar": ["multi-dimensional", "comparison across", "profile"]
        }
    
    def determine_visualization(self, question: str, answer: str, hint: Optional[str] = None) -> Tuple[Optional[str], Dict[str, Any]]:
        """Determine best visualization type and extract data"""
        # Use hint if provided
        if hint and hint in self.visualization_patterns:
            chart_data = self.extract_chart_data(answer, hint)
            return hint, chart_data

        question_lower = question.lower()

        # Priority-based pattern matching (check more specific patterns first)

        # 1. Check for cumulative/area charts FIRST (more specific)
        if any(pattern in question_lower for pattern in self.visualization_patterns["area"]):
            chart_data = self.extract_chart_data(answer, "area")
            return "area", chart_data

        # 2. Check for line charts (avoid false positives from "daily" keyword)
        # Only trigger line chart if it's clearly a trend request, not a ranking
        line_keywords = ["trend", "over time", "timeline", "progression", "historical", "by date"]
        has_line_keyword = any(keyword in question_lower for keyword in line_keywords)
        has_ranking_keyword = any(keyword in question_lower for keyword in ["top", "ranking", "highest", "lowest", "best", "worst"])

        if has_line_keyword and not has_ranking_keyword:
            chart_data = self.extract_chart_data(answer, "line")
            return "line", chart_data

        # 3. Check other specific patterns
        for viz_type, patterns in self.visualization_patterns.items():
            if viz_type in ["line", "area"]:  # Already handled above
                continue
            if any(pattern in question_lower for pattern in patterns):
                chart_data = self.extract_chart_data(answer, viz_type)
                return viz_type, chart_data

        # Default based on answer structure
        if "1." in answer or "1)" in answer:
            return "bar", self.extract_chart_data(answer, "bar")
        elif "%" in answer and ("•" in answer or "-" in answer):
            return "pie", self.extract_chart_data(answer, "pie")
        elif re.search(r'\d{4}-\d{2}-\d{2}', answer):
            # Check if it looks like multi-series (has category - date pattern)
            if re.search(r'[A-Za-z0-9\s]+-\s*\d{4}-\d{2}-\d{2}', answer):
                return "line", self.extract_chart_data(answer, "line")
            # Single series trend
            return "line", self.extract_chart_data(answer, "line")
        elif "$" in answer and any(word in answer.lower() for word in ["total", "sum", "average"]):
            return "indicator", self.extract_chart_data(answer, "indicator")

        return None, {}
    
    def extract_chart_data(self, answer: str, viz_type: str) -> Dict[str, Any]:
        """Extract structured data for charts from answer text"""
        chart_data = {"type": viz_type, "data": {}}
        
        try:
            if viz_type == "bar":
                chart_data["data"] = self._extract_bar_data(answer)
            elif viz_type == "pie":
                chart_data["data"] = self._extract_pie_data(answer)
            elif viz_type == "line":
                chart_data["data"] = self._extract_line_data(answer)
            elif viz_type == "indicator":
                chart_data["data"] = self._extract_indicator_data(answer)
            elif viz_type == "scatter":
                chart_data["data"] = self._extract_scatter_data(answer)
            elif viz_type == "heatmap":
                chart_data["data"] = self._extract_heatmap_data(answer)
            elif viz_type == "area":
                chart_data["data"] = self._extract_line_data(answer)  # Similar to line
            elif viz_type == "gauge":
                chart_data["data"] = self._extract_gauge_data(answer)
            else:
                # Generic extraction for other types
                chart_data["data"] = self._extract_generic_data(answer)
                
        except Exception as e:
            logger.error(f"Error extracting {viz_type} data: {e}")
            
        return chart_data
    
    def _extract_bar_data(self, answer: str) -> Dict[str, Any]:
        """Extract bar chart data"""
        # Pattern: "1. Name: $123" or "1) Name ($123)"
        patterns = [
            r'(\d+)[.)]\s*([^:$\(]+)[:)]\s*\$?([\d,]+\.?\d*)',
            r'(\d+)[.)]\s*([^:$]+)\s*\(\$?([\d,]+\.?\d*)\)',
            r'([^:]+):\s*\$?([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, answer)
            if matches:
                labels = []
                values = []
                
                for match in matches:
                    try:
                        if len(match) == 3:
                            label = match[1].strip()
                            value_str = match[2].replace(',', '').strip()
                        elif len(match) == 2:
                            label = match[0].strip()
                            value_str = match[1].replace(',', '').strip()
                        else:
                            continue
                        
                        # Skip if empty values
                        if not value_str or not label:
                            continue
                            
                        value = float(value_str)
                        labels.append(label)
                        values.append(value)
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Skipping invalid bar data: {match}, error: {e}")
                        continue
                
                if labels and values:
                    return {"labels": labels, "values": values}
        return {}
    
    def _extract_pie_data(self, answer: str) -> Dict[str, Any]:
        """Extract pie chart data"""
        # Pattern: "• Category: $123 (45%)" or "- Category: $123"
        patterns = [
            r'[•·-]\s*([^:$]+)[:]\s*\$?([\d,]+\.?\d*)\s*\(?([\d.]+)?%?\)?',
            r'([^:]+):\s*\$?([\d,]+\.?\d*)\s*\(?([\d.]+)?%?\)?'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, answer)
            if matches:
                labels = []
                values = []
                percentages = []
                
                for match in matches:
                    try:
                        label = match[0].strip()
                        value_str = match[1].replace(',', '').strip()
                        
                        # Skip if empty values
                        if not value_str or not label:
                            continue
                        
                        value = float(value_str)
                        labels.append(label)
                        values.append(value)
                        
                        # Handle percentage if present
                        if len(match) > 2 and match[2]:
                            pct_str = match[2].strip()
                            if pct_str:
                                percentages.append(float(pct_str))
                            else:
                                percentages.append(0)
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Skipping invalid pie data: {match}, error: {e}")
                        continue
                
                if labels and values:
                    data = {"labels": labels, "values": values}
                    if percentages:
                        data["percentages"] = percentages
                    return data
        return {}
    
    def _extract_line_data(self, answer: str) -> Dict[str, Any]:
        """Extract line chart data (supports both single and multi-series)"""
        # Pattern for multi-series: "App1 - 2024-01-01: $123" or "Category - Date: Value"
        multi_series_pattern = r'([^-\n]+?)\s*-\s*(\d{4}-\d{2}-\d{2})[:]*\s*\$?([\d,]+\.?\d*)'
        multi_matches = re.findall(multi_series_pattern, answer)

        if multi_matches:
            # Multi-series data detected
            series_data = {}
            dates_set = set()

            for match in multi_matches:
                try:
                    series_name = match[0].strip()
                    date = match[1].strip()
                    value_str = match[2].replace(',', '').strip()

                    if not value_str or not date or not series_name:
                        continue

                    value = float(value_str)
                    dates_set.add(date)

                    if series_name not in series_data:
                        series_data[series_name] = {"name": series_name, "dates": [], "values": []}

                    series_data[series_name]["dates"].append(date)
                    series_data[series_name]["values"].append(value)

                except (ValueError, IndexError) as e:
                    logger.debug(f"Skipping invalid multi-series line data: {match}, error: {e}")
                    continue

            if series_data:
                return {
                    "type": "multi-series",
                    "dates": sorted(list(dates_set)),
                    "series": list(series_data.values())
                }

        # Pattern for single series: "2024-01-01: $123" or "Jan 2024: $123"
        single_series_patterns = [
            r'(\d{4}-\d{2}-\d{2})[:]*\s*\$?([\d,]+\.?\d*)',
            r'(\w+\s+\d{4})[:]*\s*\$?([\d,]+\.?\d*)',
            r'(\w+\s+\d+)[:]*\s*\$?([\d,]+\.?\d*)'
        ]

        for pattern in single_series_patterns:
            matches = re.findall(pattern, answer)
            if matches:
                dates = []
                values = []

                for match in matches:
                    try:
                        date = match[0].strip()
                        value_str = match[1].replace(',', '').strip()

                        # Skip if empty values
                        if not value_str or not date:
                            continue

                        value = float(value_str)
                        dates.append(date)
                        values.append(value)
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Skipping invalid line data: {match}, error: {e}")
                        continue

                if dates and values:
                    return {"type": "single-series", "dates": dates, "values": values}
        return {}
    
    def _extract_indicator_data(self, answer: str) -> Dict[str, Any]:
        """Extract KPI indicator data"""
        # Extract the main numeric value
        pattern = r'\$?([\d,]+\.?\d*)'
        matches = re.findall(pattern, answer)
        
        if matches:
            for match in matches:
                try:
                    value_str = match.replace(',', '').strip()
                    if not value_str:
                        continue
                    value = float(value_str)
                    
                    # Determine title based on context
                    title = "Metric"
                    if "total" in answer.lower():
                        title = "Total Cost"
                    elif "average" in answer.lower():
                        title = "Average Cost"
                    elif "sum" in answer.lower():
                        title = "Sum"
                    elif "count" in answer.lower():
                        title = "Count"
                        
                    return {
                        "value": value,
                        "title": title,
                        "format": "currency" if "$" in answer else "number"
                    }
                except (ValueError, IndexError) as e:
                    logger.debug(f"Skipping invalid indicator data: {match}, error: {e}")
                    continue
        return {}
    
    def _extract_scatter_data(self, answer: str) -> Dict[str, Any]:
        """Extract scatter plot data"""
        # Pattern: "Name: x=123, y=456" or "Name (123, 456)"
        patterns = [
            r'([^:,\(]+)[:]*\s*\(?x=?([\d,]+\.?\d*),?\s*y=?([\d,]+\.?\d*)\)?',
            r'([^:,\(]+)[:]*\s*\(?([\d,]+\.?\d*),\s*([\d,]+\.?\d*)\)?'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, answer)
            if matches:
                points = []
                for match in matches:
                    try:
                        label = match[0].strip()
                        x_str = match[1].replace(',', '').strip()
                        y_str = match[2].replace(',', '').strip()
                        
                        # Skip if empty values
                        if not x_str or not y_str or not label:
                            continue
                        
                        points.append({
                            "label": label,
                            "x": float(x_str),
                            "y": float(y_str)
                        })
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Skipping invalid scatter data: {match}, error: {e}")
                        continue
                
                if points:
                    return {"points": points}
        return {}
    
    def _extract_heatmap_data(self, answer: str) -> Dict[str, Any]:
        """Extract heatmap data"""
        # This requires structured matrix data
        # Look for table-like structure
        lines = answer.split('\n')
        matrix = []
        rows = []
        cols = []
        
        for line in lines:
            if '|' in line or '\t' in line:
                # Parse table row
                parts = re.split(r'[|\t]', line)
                if parts:
                    row_data = []
                    for part in parts:
                        try:
                            value = float(re.sub(r'[^0-9.-]', '', part))
                            row_data.append(value)
                        except:
                            if part.strip():
                                if not cols:
                                    cols.append(part.strip())
                                else:
                                    rows.append(part.strip())
                    if row_data:
                        matrix.append(row_data)
        
        return {"matrix": matrix, "rows": rows, "cols": cols}
    
    def _extract_gauge_data(self, answer: str) -> Dict[str, Any]:
        """Extract gauge chart data"""
        # Look for percentage or score
        patterns = [
            r'([\d.]+)%',
            r'([\d.]+)\s*(?:out of|/)\s*([\d.]+)',
            r'(?:score|rating|utilization)[:\s]+([\d.]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                try:
                    if isinstance(matches[0], tuple):
                        value_str = str(matches[0][0]).strip()
                        if not value_str:
                            continue
                        value = float(value_str)
                        max_val = 100
                        if len(matches[0]) > 1:
                            max_str = str(matches[0][1]).strip()
                            if max_str:
                                max_val = float(max_str)
                    else:
                        value_str = str(matches[0]).strip()
                        if not value_str:
                            continue
                        value = float(value_str)
                        max_val = 100
                        
                    return {
                        "value": value,
                        "max": max_val,
                        "title": "Score" if "score" in answer.lower() else "Metric"
                    }
                except (ValueError, IndexError) as e:
                    logger.debug(f"Skipping invalid gauge data: {matches[0]}, error: {e}")
                    continue
        return {}
    
    def _extract_generic_data(self, answer: str) -> Dict[str, Any]:
        """Generic data extraction for other chart types"""
        # Try to extract any numeric values with labels
        pattern = r'([^:,\d]+)[:]*\s*\$?([\d,]+\.?\d*)'
        matches = re.findall(pattern, answer)
        
        if matches:
            labels = []
            values = []
            
            for match in matches:
                try:
                    label = match[0].strip()
                    value_str = match[1].replace(',', '').strip()
                    
                    # Skip if empty values
                    if not value_str or not label:
                        continue
                    
                    value = float(value_str)
                    labels.append(label)
                    values.append(value)
                except (ValueError, IndexError) as e:
                    logger.debug(f"Skipping invalid generic data: {match}, error: {e}")
                    continue
            
            if labels and values:
                return {"labels": labels, "values": values}
        return {}
    
    def extract_insights(self, answer: str, viz_type: Optional[str]) -> List[str]:
        """Extract key insights from the answer"""
        insights = []
        
        try:
            # Keywords that indicate insights
            insight_keywords = [
                'highest', 'lowest', 'average', 'total', 'increase', 'decrease',
                'most', 'least', 'significant', 'notable', 'trend', 'pattern'
            ]
            
            sentences = re.split(r'[.!?]', answer)
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in insight_keywords):
                    clean_sentence = sentence.strip()
                    if clean_sentence:
                        insights.append(clean_sentence + '.')
            
            # Add visualization-specific insights
            if viz_type:
                if viz_type == "bar" and insights:
                    insights.append("Rankings show clear leaders and laggards.")
                elif viz_type == "pie" and "%" in answer:
                    insights.append("Distribution reveals concentration patterns.")
                elif viz_type == "line" and "trend" in answer.lower():
                    insights.append("Time series shows directional movement.")
                elif viz_type == "indicator":
                    insights.append("Key metric provides performance snapshot.")
                    
        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
        
        # Return top 3 most relevant insights
        return insights[:3]