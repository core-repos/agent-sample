"""
SQL Validation Agent with iterative validation and improvement
"""
import re
import sqlparse
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from ..database import BigQueryConnection
from llm.factory import LLMProviderFactory
from config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of SQL validation"""
    is_valid: bool
    error_message: Optional[str] = None
    suggested_fix: Optional[str] = None
    confidence_score: float = 0.0
    validation_type: str = "unknown"

@dataclass
class SQLValidationReport:
    """Complete SQL validation report"""
    original_query: str
    final_query: str
    iterations: int
    validation_results: List[ValidationResult]
    execution_time: float
    success: bool
    final_error: Optional[str] = None

class SQLValidationAgent:
    """Agent for validating and improving SQL queries with iterative validation"""

    def __init__(self, connection: BigQueryConnection, llm_provider: Optional[str] = None):
        self.connection = connection
        self.llm_provider = LLMProviderFactory.create_provider(llm_provider)
        self.llm = self.llm_provider.get_model()
        self.max_iterations = 3  # Reduced for reliability testing
        self.validation_rules = self._init_validation_rules()

    def _init_validation_rules(self) -> Dict[str, Any]:
        """Initialize SQL validation rules for BigQuery"""
        return {
            'syntax_patterns': {
                'select_required': r'\bSELECT\b',
                'from_required': r'\bFROM\b',
                'valid_functions': [
                    'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'FORMAT',
                    'ROUND', 'DATE_SUB', 'CURRENT_DATE', 'EXTRACT',
                    'GROUP_CONCAT', 'STRING_AGG', 'ARRAY_AGG'
                ],
                'invalid_functions': ['LIMIT_OFFSET', 'ROWNUM'],
                'required_table_prefix': f'{settings.gcp_project_id}.{settings.bq_dataset}.'
            },
            'bigquery_specific': {
                'dataset_format': f'{settings.gcp_project_id}.{settings.bq_dataset}',
                'date_functions': ['DATE_SUB', 'DATE_ADD', 'CURRENT_DATE'],
                'string_functions': ['STRING_AGG', 'CONCAT'],
                'aggregate_functions': ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN']
            },
            'performance_rules': {
                'max_result_rows': 1000,
                'recommend_limit': True,
                'avoid_select_star': True
            }
        }

    async def validate_sql_iteratively(
        self,
        sql_query: str,
        original_question: str,
        expected_result_type: str = "data"
    ) -> SQLValidationReport:
        """
        Validate SQL query with up to 10 iterations of improvement

        Args:
            sql_query: The SQL query to validate
            original_question: Original natural language question
            expected_result_type: Expected result type (data, aggregation, etc.)

        Returns:
            SQLValidationReport with validation results and final query
        """
        start_time = datetime.now()
        validation_results = []
        current_query = sql_query.strip()

        logger.info(f"Starting iterative SQL validation for: {original_question}")

        for iteration in range(1, self.max_iterations + 1):
            logger.debug(f"Validation iteration {iteration}/{self.max_iterations}")

            # Perform comprehensive validation
            validation_result = await self._validate_single_iteration(
                current_query,
                original_question,
                expected_result_type,
                iteration
            )

            validation_results.append(validation_result)

            # If valid, we're done
            if validation_result.is_valid:
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"SQL validation succeeded after {iteration} iterations")

                return SQLValidationReport(
                    original_query=sql_query,
                    final_query=current_query,
                    iterations=iteration,
                    validation_results=validation_results,
                    execution_time=execution_time,
                    success=True
                )

            # If not valid, try to fix it
            if validation_result.suggested_fix:
                current_query = validation_result.suggested_fix
                logger.debug(f"Applying suggested fix for iteration {iteration}")
            else:
                # Generate improvement using LLM
                improved_query = await self._generate_sql_improvement(
                    current_query,
                    validation_result.error_message,
                    original_question,
                    iteration
                )
                if improved_query and improved_query != current_query:
                    current_query = improved_query
                else:
                    logger.warning(f"No improvement generated at iteration {iteration}")
                    break

        # Failed after max iterations
        execution_time = (datetime.now() - start_time).total_seconds()
        final_error = validation_results[-1].error_message if validation_results else "Unknown validation error"

        logger.warning(f"SQL validation failed after {self.max_iterations} iterations")

        return SQLValidationReport(
            original_query=sql_query,
            final_query=current_query,
            iterations=self.max_iterations,
            validation_results=validation_results,
            execution_time=execution_time,
            success=False,
            final_error=final_error
        )

    async def _validate_single_iteration(
        self,
        sql_query: str,
        original_question: str,
        expected_result_type: str,
        iteration: int
    ) -> ValidationResult:
        """Perform validation for a single iteration"""

        # 1. Syntax validation
        syntax_result = self._validate_syntax(sql_query)
        if not syntax_result.is_valid:
            return syntax_result

        # 2. BigQuery specific validation
        bigquery_result = self._validate_bigquery_specifics(sql_query)
        if not bigquery_result.is_valid:
            return bigquery_result

        # 3. Semantic validation
        semantic_result = await self._validate_semantics(sql_query, original_question)
        if not semantic_result.is_valid:
            return semantic_result

        # 4. Execution validation (dry run)
        execution_result = await self._validate_execution(sql_query)
        if not execution_result.is_valid:
            return execution_result

        # 5. Performance validation
        performance_result = self._validate_performance(sql_query)
        if not performance_result.is_valid:
            return performance_result

        # All validations passed
        return ValidationResult(
            is_valid=True,
            confidence_score=0.95,
            validation_type=f"complete_iteration_{iteration}"
        )

    def _validate_syntax(self, sql_query: str) -> ValidationResult:
        """Validate SQL syntax"""
        try:
            # Parse SQL using sqlparse
            parsed = sqlparse.parse(sql_query)
            if not parsed:
                return ValidationResult(
                    is_valid=False,
                    error_message="Empty or invalid SQL query",
                    validation_type="syntax"
                )

            query_upper = sql_query.upper()

            # Check for required keywords
            if not re.search(self.validation_rules['syntax_patterns']['select_required'], query_upper):
                return ValidationResult(
                    is_valid=False,
                    error_message="SQL query must contain SELECT statement",
                    suggested_fix=f"SELECT * FROM {self.validation_rules['bigquery_specific']['dataset_format']}.cost_analysis LIMIT 10",
                    validation_type="syntax"
                )

            if not re.search(self.validation_rules['syntax_patterns']['from_required'], query_upper):
                return ValidationResult(
                    is_valid=False,
                    error_message="SQL query must contain FROM clause",
                    validation_type="syntax"
                )

            # Check for invalid functions
            for invalid_func in self.validation_rules['syntax_patterns']['invalid_functions']:
                if invalid_func in query_upper:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Invalid function '{invalid_func}' for BigQuery",
                        validation_type="syntax"
                    )

            return ValidationResult(
                is_valid=True,
                confidence_score=0.9,
                validation_type="syntax"
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Syntax parsing error: {str(e)}",
                validation_type="syntax"
            )

    def _validate_bigquery_specifics(self, sql_query: str) -> ValidationResult:
        """Validate BigQuery specific requirements"""
        query_upper = sql_query.upper()

        # Check if table names are properly qualified
        dataset_format = self.validation_rules['bigquery_specific']['dataset_format']

        if 'FROM cost_analysis' in sql_query and dataset_format not in sql_query:
            fixed_query = sql_query.replace(
                'cost_analysis',
                f'{dataset_format}.cost_analysis'
            ).replace(
                'FROM cost_analysis',
                f'FROM {dataset_format}.cost_analysis'
            )
            return ValidationResult(
                is_valid=False,
                error_message="Table name must be fully qualified with project and dataset",
                suggested_fix=fixed_query,
                validation_type="bigquery_specific"
            )

        # Check for BigQuery date functions
        if 'CURDATE()' in query_upper or 'NOW()' in query_upper:
            fixed_query = sql_query.replace('CURDATE()', 'CURRENT_DATE()').replace('NOW()', 'CURRENT_DATETIME()')
            return ValidationResult(
                is_valid=False,
                error_message="Use BigQuery date functions: CURRENT_DATE(), CURRENT_DATETIME()",
                suggested_fix=fixed_query,
                validation_type="bigquery_specific"
            )

        return ValidationResult(
            is_valid=True,
            confidence_score=0.85,
            validation_type="bigquery_specific"
        )

    async def _validate_semantics(self, sql_query: str, original_question: str) -> ValidationResult:
        """Validate semantic correctness using LLM"""
        try:
            prompt = f"""
            Analyze this SQL query for semantic correctness given the original question:

            Original Question: {original_question}
            SQL Query: {sql_query}

            Table Schema:
            - cost_analysis (date, cto, cloud, tr_product_pillar_team, tr_subpillar_name, tr_product_id, tr_product, application, service_name, managed_service, environment, cost)

            Check if:
            1. The SQL query answers the original question
            2. Column names are correct
            3. Aggregations are appropriate
            4. Filters make sense
            5. GROUP BY clauses are correct

            Respond with: VALID or INVALID: reason
            """

            response = await self.llm.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            if response_text.startswith('VALID'):
                return ValidationResult(
                    is_valid=True,
                    confidence_score=0.8,
                    validation_type="semantic"
                )
            else:
                error_msg = response_text.replace('INVALID:', '').strip()
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Semantic validation failed: {error_msg}",
                    validation_type="semantic"
                )

        except Exception as e:
            logger.warning(f"Semantic validation error: {e}")
            return ValidationResult(
                is_valid=True,  # Default to valid if LLM fails
                confidence_score=0.5,
                validation_type="semantic"
            )

    async def _validate_execution(self, sql_query: str) -> ValidationResult:
        """Validate SQL execution with dry run"""
        try:
            # Add LIMIT for dry run safety
            test_query = sql_query
            if 'LIMIT' not in test_query.upper():
                test_query += ' LIMIT 1'

            # Try to execute the query
            db = self.connection.get_langchain_database()
            result = db.run(test_query)

            return ValidationResult(
                is_valid=True,
                confidence_score=0.95,
                validation_type="execution"
            )

        except Exception as e:
            error_msg = str(e)

            # Common BigQuery error fixes
            suggested_fix = None
            if 'not found' in error_msg.lower():
                # Table not found - add proper qualification
                dataset_format = self.validation_rules['bigquery_specific']['dataset_format']
                suggested_fix = sql_query.replace(
                    'cost_analysis',
                    f'{dataset_format}.cost_analysis'
                )
            elif 'invalid date' in error_msg.lower():
                # Date format issue
                suggested_fix = sql_query.replace(
                    'CURDATE()',
                    'CURRENT_DATE()'
                )

            return ValidationResult(
                is_valid=False,
                error_message=f"Query execution failed: {error_msg}",
                suggested_fix=suggested_fix,
                validation_type="execution"
            )

    def _validate_performance(self, sql_query: str) -> ValidationResult:
        """Validate query performance characteristics"""
        query_upper = sql_query.upper()

        # Check for LIMIT clause for large result sets
        if 'LIMIT' not in query_upper and 'COUNT(' not in query_upper:
            if any(word in query_upper for word in ['SELECT *', 'SELECT cost_analysis.*']):
                return ValidationResult(
                    is_valid=False,
                    error_message="Query may return too many rows, consider adding LIMIT",
                    suggested_fix=sql_query + ' LIMIT 100',
                    validation_type="performance"
                )

        # Check for SELECT *
        if 'SELECT *' in query_upper and self.validation_rules['performance_rules']['avoid_select_star']:
            return ValidationResult(
                is_valid=False,
                error_message="Avoid SELECT * for better performance, specify columns",
                validation_type="performance"
            )

        return ValidationResult(
            is_valid=True,
            confidence_score=0.75,
            validation_type="performance"
        )

    async def _generate_sql_improvement(
        self,
        sql_query: str,
        error_message: str,
        original_question: str,
        iteration: int
    ) -> Optional[str]:
        """Generate improved SQL query using LLM"""
        try:
            prompt = f"""
            Improve this BigQuery SQL query to fix the following error:

            Original Question: {original_question}
            Current SQL: {sql_query}
            Error: {error_message}
            Iteration: {iteration}

            Requirements:
            1. Fix the specific error mentioned
            2. Ensure proper BigQuery syntax
            3. Use fully qualified table names: {settings.gcp_project_id}.{settings.bq_dataset}.cost_analysis
            4. Keep the query focused on answering the original question
            5. Add appropriate LIMIT if needed

            Table Schema:
            cost_analysis: date, cto, cloud, tr_product_pillar_team, tr_subpillar_name, tr_product_id, tr_product, application, service_name, managed_service, environment, cost

            Return only the corrected SQL query without explanation.
            """

            response = await self.llm.ainvoke(prompt)
            improved_query = response.content if hasattr(response, 'content') else str(response)

            # Clean up the response
            improved_query = improved_query.strip()
            if improved_query.startswith('```sql'):
                improved_query = improved_query.replace('```sql', '').replace('```', '').strip()

            # Basic validation of improvement
            if improved_query and len(improved_query) > 10 and 'SELECT' in improved_query.upper():
                return improved_query

            return None

        except Exception as e:
            logger.error(f"Error generating SQL improvement: {e}")
            return None

    def get_validation_summary(self, report: SQLValidationReport) -> Dict[str, Any]:
        """Generate a summary of validation results"""
        validation_types = {}
        for result in report.validation_results:
            validation_types[result.validation_type] = validation_types.get(result.validation_type, 0) + 1

        return {
            "success": report.success,
            "iterations": report.iterations,
            "execution_time": report.execution_time,
            "validation_attempts": validation_types,
            "final_query": report.final_query,
            "original_query": report.original_query,
            "query_changed": report.final_query != report.original_query,
            "final_error": report.final_error
        }