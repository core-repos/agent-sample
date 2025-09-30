"""
Validation Coordinator that orchestrates SQL and Graph validation agents
"""
import asyncio
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from .sql_validator import SQLValidationAgent, SQLValidationReport
from .graph_validator import GraphDataValidationAgent, GraphValidationReport
from ..database import BigQueryConnection
from ..visualization import VisualizationProcessor

logger = logging.getLogger(__name__)

@dataclass
class ValidationCoordinatorReport:
    """Complete validation report from coordinator"""
    sql_report: Optional[SQLValidationReport]
    graph_report: Optional[GraphValidationReport]
    final_result: Dict[str, Any]
    total_iterations: int
    total_execution_time: float
    success: bool
    coordinator_error: Optional[str] = None

class ValidationCoordinator:
    """
    Coordinates SQL and Graph validation agents with iterative validation
    Ensures both SQL generation and graph data are validated before final output
    """

    def __init__(self, connection: BigQueryConnection, llm_provider: Optional[str] = None):
        self.connection = connection
        self.sql_validator = SQLValidationAgent(connection, llm_provider)
        self.graph_validator = GraphDataValidationAgent(llm_provider)
        self.visualization_processor = VisualizationProcessor()
        self.max_total_iterations = 6  # 3 SQL + 3 Graph = 6 total max

    async def validate_complete_pipeline(
        self,
        original_question: str,
        sql_query: str,
        llm_answer: str,
        expected_viz_type: Optional[str] = None
    ) -> ValidationCoordinatorReport:
        """
        Validate the complete pipeline: SQL -> Execution -> Data -> Graph

        Args:
            original_question: Original natural language question
            sql_query: Generated SQL query
            llm_answer: LLM's textual answer
            expected_viz_type: Expected visualization type

        Returns:
            ValidationCoordinatorReport with complete validation results
        """
        start_time = datetime.now()
        total_iterations = 0

        logger.info(f"Starting complete pipeline validation for: {original_question}")

        try:
            # Phase 1: Validate and improve SQL query
            logger.debug("Phase 1: SQL Validation")
            sql_report = await self.sql_validator.validate_sql_iteratively(
                sql_query=sql_query,
                original_question=original_question,
                expected_result_type="visualization_data"
            )
            total_iterations += sql_report.iterations

            if not sql_report.success:
                logger.warning("SQL validation failed, cannot proceed to graph validation")
                execution_time = (datetime.now() - start_time).total_seconds()

                return ValidationCoordinatorReport(
                    sql_report=sql_report,
                    graph_report=None,
                    final_result={
                        "success": False,
                        "error": f"SQL validation failed: {sql_report.final_error}",
                        "sql_query": sql_report.final_query,
                        "answer": llm_answer
                    },
                    total_iterations=total_iterations,
                    total_execution_time=execution_time,
                    success=False,
                    coordinator_error="SQL validation failed"
                )

            # Phase 2: Execute validated SQL and extract data
            logger.debug("Phase 2: SQL Execution and Data Extraction")
            executed_data, execution_error = await self._execute_validated_sql(sql_report.final_query)

            if execution_error:
                logger.warning(f"SQL execution failed: {execution_error}")
                execution_time = (datetime.now() - start_time).total_seconds()

                return ValidationCoordinatorReport(
                    sql_report=sql_report,
                    graph_report=None,
                    final_result={
                        "success": False,
                        "error": f"SQL execution failed: {execution_error}",
                        "sql_query": sql_report.final_query,
                        "answer": llm_answer
                    },
                    total_iterations=total_iterations,
                    total_execution_time=execution_time,
                    success=False,
                    coordinator_error="SQL execution failed"
                )

            # Phase 3: Determine visualization and extract chart data
            logger.debug("Phase 3: Visualization Detection and Data Extraction")
            viz_type, initial_chart_data = self.visualization_processor.determine_visualization(
                original_question, llm_answer, expected_viz_type
            )

            if not viz_type:
                logger.warning("No suitable visualization type detected")
                # Return successful result without visualization
                execution_time = (datetime.now() - start_time).total_seconds()

                return ValidationCoordinatorReport(
                    sql_report=sql_report,
                    graph_report=None,
                    final_result={
                        "success": True,
                        "answer": llm_answer,
                        "sql_query": sql_report.final_query,
                        "visualization": None,
                        "warning": "No visualization could be generated"
                    },
                    total_iterations=total_iterations,
                    total_execution_time=execution_time,
                    success=True
                )

            # Phase 4: Validate and improve graph data
            logger.debug(f"Phase 4: Graph Data Validation for {viz_type}")
            graph_report = await self.graph_validator.validate_graph_data_iteratively(
                chart_data=initial_chart_data,
                chart_type=viz_type,
                original_answer=llm_answer,
                original_question=original_question
            )
            total_iterations += graph_report.iterations

            # Phase 5: Combine results
            logger.debug("Phase 5: Combining Final Results")
            final_result = self._combine_validation_results(
                sql_report=sql_report,
                graph_report=graph_report,
                original_question=original_question,
                llm_answer=llm_answer,
                executed_data=executed_data
            )

            execution_time = (datetime.now() - start_time).total_seconds()
            overall_success = sql_report.success and graph_report.success

            logger.info(f"Pipeline validation completed - Success: {overall_success}, Total Iterations: {total_iterations}")

            return ValidationCoordinatorReport(
                sql_report=sql_report,
                graph_report=graph_report,
                final_result=final_result,
                total_iterations=total_iterations,
                total_execution_time=execution_time,
                success=overall_success
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Validation coordinator error: {e}")

            return ValidationCoordinatorReport(
                sql_report=None,
                graph_report=None,
                final_result={
                    "success": False,
                    "error": f"Validation coordinator error: {str(e)}",
                    "answer": llm_answer
                },
                total_iterations=total_iterations,
                total_execution_time=execution_time,
                success=False,
                coordinator_error=str(e)
            )

    async def _execute_validated_sql(self, sql_query: str) -> Tuple[Optional[str], Optional[str]]:
        """Execute validated SQL query and return results"""
        try:
            db = self.connection.get_langchain_database()
            result = db.run(sql_query)
            return result, None
        except Exception as e:
            return None, str(e)

    def _combine_validation_results(
        self,
        sql_report: SQLValidationReport,
        graph_report: GraphValidationReport,
        original_question: str,
        llm_answer: str,
        executed_data: Optional[str]
    ) -> Dict[str, Any]:
        """Combine SQL and graph validation results into final response"""

        # Base response structure
        response = {
            "success": sql_report.success and graph_report.success,
            "answer": llm_answer,
            "sql_query": sql_report.final_query,
            "metadata": {
                "validation": {
                    "sql_iterations": sql_report.iterations,
                    "graph_iterations": graph_report.iterations,
                    "total_iterations": sql_report.iterations + graph_report.iterations,
                    "sql_success": sql_report.success,
                    "graph_success": graph_report.success,
                    "execution_time": sql_report.execution_time + graph_report.execution_time
                }
            }
        }

        # Add visualization data if graph validation succeeded
        if graph_report.success and graph_report.final_data:
            response["visualization"] = graph_report.chart_type
            response["chart_data"] = graph_report.final_data
            response["data_points"] = graph_report.data_points

            # Extract insights from the validated data
            insights = self.visualization_processor.extract_insights(
                llm_answer,
                graph_report.chart_type
            )
            if insights:
                response["insights"] = insights

        # Add warnings if there were issues
        warnings = []

        if sql_report.iterations > 5:
            warnings.append(f"SQL required {sql_report.iterations} validation iterations")

        if graph_report.iterations > 5:
            warnings.append(f"Graph data required {graph_report.iterations} validation iterations")

        if not graph_report.success:
            warnings.append(f"Graph validation failed: {graph_report.final_error}")

        if sql_report.final_query != sql_report.original_query:
            warnings.append("SQL query was modified during validation")

        if graph_report.final_data != graph_report.original_data:
            warnings.append("Chart data was modified during validation")

        if warnings:
            response["warnings"] = warnings

        # Add executed data for debugging if available
        if executed_data:
            response["metadata"]["executed_data_preview"] = executed_data[:200] + "..." if len(executed_data) > 200 else executed_data

        # Add quality scores
        if graph_report.validation_results:
            last_result = graph_report.validation_results[-1]
            response["metadata"]["data_quality_score"] = last_result.data_quality_score

        return response

    async def validate_sql_only(self, sql_query: str, original_question: str) -> SQLValidationReport:
        """Validate only SQL query without graph data"""
        return await self.sql_validator.validate_sql_iteratively(
            sql_query=sql_query,
            original_question=original_question,
            expected_result_type="data"
        )

    async def validate_graph_only(
        self,
        chart_data: Dict[str, Any],
        chart_type: str,
        original_answer: str,
        original_question: str
    ) -> GraphValidationReport:
        """Validate only graph data without SQL"""
        return await self.graph_validator.validate_graph_data_iteratively(
            chart_data=chart_data,
            chart_type=chart_type,
            original_answer=original_answer,
            original_question=original_question
        )

    def get_validation_examples(self) -> List[Dict[str, str]]:
        """Get example queries from test data for validation"""
        return [
            {
                "question": "What is the total cost?",
                "expected_visualization": "indicator",
                "expected_sql_pattern": "SELECT SUM(cost)",
                "category": "aggregation"
            },
            {
                "question": "Show me the top 5 applications by cost",
                "expected_visualization": "bar",
                "expected_sql_pattern": "ORDER BY.*DESC.*LIMIT 5",
                "category": "ranking"
            },
            {
                "question": "What's the cost breakdown by environment?",
                "expected_visualization": "pie",
                "expected_sql_pattern": "GROUP BY environment",
                "category": "distribution"
            },
            {
                "question": "Display the daily cost trend for last 30 days",
                "expected_visualization": "line",
                "expected_sql_pattern": "DATE_SUB.*30.*ORDER BY date",
                "category": "trend"
            },
            {
                "question": "Show cost correlation between applications",
                "expected_visualization": "scatter",
                "expected_sql_pattern": "application.*cost",
                "category": "correlation"
            },
            {
                "question": "Create a heatmap of costs by service and environment",
                "expected_visualization": "heatmap",
                "expected_sql_pattern": "managed_service.*environment",
                "category": "matrix"
            },
            {
                "question": "Show waterfall chart of cost components",
                "expected_visualization": "waterfall",
                "expected_sql_pattern": "SUM.*GROUP BY",
                "category": "decomposition"
            }
        ]

    def get_validation_summary(self, report: ValidationCoordinatorReport) -> Dict[str, Any]:
        """Generate comprehensive validation summary"""
        summary = {
            "overall_success": report.success,
            "total_iterations": report.total_iterations,
            "total_execution_time": report.total_execution_time,
            "phases_completed": []
        }

        if report.sql_report:
            summary["sql_validation"] = self.sql_validator.get_validation_summary(report.sql_report)
            summary["phases_completed"].append("sql_validation")

        if report.graph_report:
            summary["graph_validation"] = self.graph_validator.get_validation_summary(report.graph_report)
            summary["phases_completed"].append("graph_validation")

        if report.final_result:
            summary["has_visualization"] = "visualization" in report.final_result
            summary["has_chart_data"] = "chart_data" in report.final_result
            summary["warnings_count"] = len(report.final_result.get("warnings", []))

        summary["coordinator_error"] = report.coordinator_error

        return summary

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on validation components"""
        health = {
            "timestamp": datetime.now().isoformat(),
            "sql_validator": "unknown",
            "graph_validator": "unknown",
            "database_connection": "unknown"
        }

        try:
            # Test database connection
            if self.connection.test_connection():
                health["database_connection"] = "healthy"
            else:
                health["database_connection"] = "unhealthy"
        except Exception as e:
            health["database_connection"] = f"error: {str(e)}"

        try:
            # Test SQL validator with simple query
            simple_sql_test = await self.sql_validator.validate_sql_iteratively(
                "SELECT COUNT(*) FROM cost_analysis LIMIT 1",
                "test query",
                "test"
            )
            health["sql_validator"] = "healthy" if simple_sql_test.success else "unhealthy"
        except Exception as e:
            health["sql_validator"] = f"error: {str(e)}"

        try:
            # Test graph validator with simple data
            simple_graph_test = await self.graph_validator.validate_graph_data_iteratively(
                {"value": 100},
                "indicator",
                "The total is 100",
                "What is the total?"
            )
            health["graph_validator"] = "healthy" if simple_graph_test.success else "unhealthy"
        except Exception as e:
            health["graph_validator"] = f"error: {str(e)}"

        health["overall"] = "healthy" if all(
            status == "healthy" for status in [
                health["sql_validator"],
                health["graph_validator"],
                health["database_connection"]
            ]
        ) else "unhealthy"

        return health