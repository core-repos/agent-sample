"""
Step 3: SQL Validation
Validates generated SQL query for syntax, execution, and performance
"""
from typing import Dict, Any, List
from ..base_step import ConditionalStep, StepResult, StepStatus
import sqlparse
import re

class SQLValidationStep(ConditionalStep):
    """Validate SQL query for correctness and performance"""

    def __init__(self):
        super().__init__(
            name="sql_validation",
            description="Validate SQL syntax, execution, and performance"
        )

    def get_required_inputs(self) -> List[str]:
        return ["sql_query", "settings"]

    def get_output_keys(self) -> List[str]:
        return ["validated_sql", "validation_results", "validation_metadata"]

    def should_execute(self, input_data: Dict[str, Any]) -> bool:
        """Only execute if validation is enabled and we have SQL"""
        settings = input_data.get("settings", {})
        sql_query = input_data.get("sql_query")
        return settings.get("enable_validation", True) and bool(sql_query)

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that we have SQL query"""
        return "sql_query" in input_data and bool(input_data["sql_query"])

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Validate the SQL query"""
        sql_query = input_data["sql_query"]
        settings = input_data["settings"]

        validation_results = []
        validated_sql = sql_query
        has_errors = False

        # 1. Syntax Validation
        syntax_result = self._validate_syntax(sql_query)
        validation_results.append(syntax_result)
        if not syntax_result["is_valid"]:
            has_errors = True

        # 2. BigQuery Specific Validation
        bigquery_result = self._validate_bigquery_specifics(sql_query)
        validation_results.append(bigquery_result)
        if not bigquery_result["is_valid"] and bigquery_result.get("suggested_fix"):
            validated_sql = bigquery_result["suggested_fix"]

        # 3. Performance Validation
        performance_result = self._validate_performance(sql_query)
        validation_results.append(performance_result)
        if not performance_result["is_valid"] and performance_result.get("suggested_fix"):
            validated_sql = performance_result["suggested_fix"]

        # 4. Execution Validation (dry run)
        execution_result = await self._validate_execution(validated_sql)
        validation_results.append(execution_result)
        if not execution_result["is_valid"]:
            has_errors = True

        # Generate validation metadata
        validation_metadata = {
            "total_checks": len(validation_results),
            "passed_checks": sum(1 for r in validation_results if r["is_valid"]),
            "query_modified": validated_sql != sql_query,
            "severity": "error" if has_errors else "warning" if any(not r["is_valid"] for r in validation_results) else "success"
        }

        status = StepStatus.SUCCESS if not has_errors else StepStatus.FAILED

        return StepResult(
            step_name=self.name,
            status=status,
            data={
                "validated_sql": validated_sql,
                "validation_results": validation_results,
                "validation_metadata": validation_metadata
            }
        )

    def _validate_syntax(self, sql_query: str) -> Dict[str, Any]:
        """Validate SQL syntax"""
        try:
            parsed = sqlparse.parse(sql_query)
            if not parsed:
                return {
                    "check": "syntax",
                    "is_valid": False,
                    "error": "Empty or invalid SQL query"
                }

            query_upper = sql_query.upper()

            # Check for required keywords
            if not re.search(r'\bSELECT\b', query_upper):
                return {
                    "check": "syntax",
                    "is_valid": False,
                    "error": "SQL query must contain SELECT statement"
                }

            if not re.search(r'\bFROM\b', query_upper):
                return {
                    "check": "syntax",
                    "is_valid": False,
                    "error": "SQL query must contain FROM clause"
                }

            return {
                "check": "syntax",
                "is_valid": True,
                "message": "SQL syntax is valid"
            }

        except Exception as e:
            return {
                "check": "syntax",
                "is_valid": False,
                "error": f"Syntax parsing error: {str(e)}"
            }

    def _validate_bigquery_specifics(self, sql_query: str) -> Dict[str, Any]:
        """Validate BigQuery specific requirements"""
        from config.settings import settings

        # Check if table names are properly qualified
        dataset_format = f"{settings.gcp_project_id}.{settings.bq_dataset}"

        if 'cost_analysis' in sql_query and dataset_format not in sql_query:
            fixed_query = sql_query.replace(
                'cost_analysis',
                f'{dataset_format}.cost_analysis'
            )
            return {
                "check": "bigquery_specific",
                "is_valid": False,
                "error": "Table name must be fully qualified with project and dataset",
                "suggested_fix": fixed_query
            }

        # Check for BigQuery date functions
        query_upper = sql_query.upper()
        if 'CURDATE()' in query_upper or 'NOW()' in query_upper:
            fixed_query = sql_query.replace('CURDATE()', 'CURRENT_DATE()').replace('NOW()', 'CURRENT_DATETIME()')
            return {
                "check": "bigquery_specific",
                "is_valid": False,
                "error": "Use BigQuery date functions: CURRENT_DATE(), CURRENT_DATETIME()",
                "suggested_fix": fixed_query
            }

        return {
            "check": "bigquery_specific",
            "is_valid": True,
            "message": "BigQuery compatibility validated"
        }

    def _validate_performance(self, sql_query: str) -> Dict[str, Any]:
        """Validate query performance characteristics"""
        query_upper = sql_query.upper()

        # Check for LIMIT clause for large result sets
        if 'LIMIT' not in query_upper and 'COUNT(' not in query_upper:
            if any(word in query_upper for word in ['SELECT *', 'SELECT cost_analysis.*']):
                return {
                    "check": "performance",
                    "is_valid": False,
                    "error": "Query may return too many rows, consider adding LIMIT",
                    "suggested_fix": sql_query + ' LIMIT 100'
                }

        # Check for SELECT *
        if 'SELECT *' in query_upper:
            return {
                "check": "performance",
                "is_valid": False,
                "error": "Avoid SELECT * for better performance, specify columns"
            }

        return {
            "check": "performance",
            "is_valid": True,
            "message": "Performance characteristics acceptable"
        }

    async def _validate_execution(self, sql_query: str) -> Dict[str, Any]:
        """Validate SQL execution with dry run"""
        try:
            from agents.bigquery.database import BigQueryConnection

            # Add LIMIT for dry run safety
            test_query = sql_query
            if 'LIMIT' not in test_query.upper():
                test_query += ' LIMIT 1'

            # Try to execute the query
            connection = BigQueryConnection()
            db = connection.get_langchain_database()
            result = db.run(test_query)

            return {
                "check": "execution",
                "is_valid": True,
                "message": "Query executes successfully"
            }

        except Exception as e:
            error_msg = str(e)
            return {
                "check": "execution",
                "is_valid": False,
                "error": f"Query execution failed: {error_msg}"
            }