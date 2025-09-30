"""
Step 4: SQL Execution
Executes validated SQL query against BigQuery
"""
from typing import Dict, Any, List
from ..base_step import BaseStep, StepResult, StepStatus
from agents.bigquery.database import BigQueryConnection

class SQLExecutionStep(BaseStep):
    """Execute SQL query against BigQuery"""

    def __init__(self):
        super().__init__(
            name="sql_execution",
            description="Execute SQL query against BigQuery database"
        )
        self.connection = BigQueryConnection()

    def get_required_inputs(self) -> List[str]:
        return ["sql_query"]

    def get_output_keys(self) -> List[str]:
        return ["query_result", "execution_metadata"]

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that we have SQL to execute"""
        validated_sql = input_data.get("validated_sql")
        sql_query = input_data.get("sql_query")

        self.logger.debug(f"SQL validation - validated_sql: {validated_sql}, sql_query: {sql_query}")

        final_sql = validated_sql or sql_query
        if final_sql and final_sql.strip():
            self.logger.debug(f"SQL query found: {final_sql[:100]}...")
            return True
        else:
            self.logger.error(f"No valid SQL query found. validated_sql: {validated_sql}, sql_query: {sql_query}")
            self.logger.error(f"Input data keys: {list(input_data.keys())}")
            return False

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute the SQL query"""
        # Use validated SQL if available, otherwise fall back to original
        sql_query = input_data.get("validated_sql") or input_data.get("sql_query")

        try:
            self.logger.info("Executing SQL query against BigQuery")

            # Get database connection
            db = self.connection.get_langchain_database()

            # Execute the query
            result = db.run(sql_query)

            # Analyze the result
            execution_metadata = self._analyze_result(result, sql_query)

            self.logger.info(f"SQL execution completed: {execution_metadata['result_type']}")

            return StepResult(
                step_name=self.name,
                status=StepStatus.SUCCESS,
                data={
                    "query_result": result,
                    "execution_metadata": execution_metadata,
                    "executed_sql": sql_query
                }
            )

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"SQL execution failed: {error_msg}")

            return StepResult(
                step_name=self.name,
                status=StepStatus.FAILED,
                data={},
                error=f"SQL execution failed: {error_msg}"
            )

    def _analyze_result(self, result: str, sql_query: str) -> Dict[str, Any]:
        """Analyze query result to understand its characteristics"""
        metadata = {
            "result_length": len(result),
            "result_type": "unknown",
            "row_count": 0,
            "has_data": bool(result and result.strip()),
            "query_type": self._classify_query_type(sql_query)
        }

        if not result or not result.strip():
            metadata["result_type"] = "empty"
            return metadata

        # Try to count rows by counting newlines (rough estimate)
        lines = result.strip().split('\n')
        metadata["row_count"] = len(lines)

        # Classify result type
        if metadata["row_count"] == 1:
            # Single value result
            metadata["result_type"] = "single_value"
        elif metadata["row_count"] <= 5:
            metadata["result_type"] = "small_dataset"
        elif metadata["row_count"] <= 50:
            metadata["result_type"] = "medium_dataset"
        else:
            metadata["result_type"] = "large_dataset"

        # Check if result contains numerical data
        import re
        if re.search(r'[\d,]+\.?\d*', result):
            metadata["contains_numbers"] = True

        # Check if result contains dates
        if re.search(r'\d{4}-\d{2}-\d{2}', result):
            metadata["contains_dates"] = True

        return metadata

    def _classify_query_type(self, sql_query: str) -> str:
        """Classify the type of SQL query"""
        query_upper = sql_query.upper()

        if 'COUNT(' in query_upper or 'SUM(' in query_upper:
            return "aggregation"
        elif 'GROUP BY' in query_upper:
            return "grouping"
        elif 'ORDER BY' in query_upper and 'LIMIT' in query_upper:
            return "ranking"
        elif 'WHERE' in query_upper and 'DATE' in query_upper:
            return "filtered_temporal"
        elif 'JOIN' in query_upper:
            return "join"
        else:
            return "select"

    async def health_check(self) -> Dict[str, Any]:
        """Check health of SQL execution"""
        health = {"status": "healthy"}

        try:
            # Test database connection
            if not self.connection.test_connection():
                health["status"] = "unhealthy"
                health["error"] = "Database connection failed"
            else:
                health["connection"] = "ok"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)

        return health