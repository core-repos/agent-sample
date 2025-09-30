"""
Step executor for pipeline agents - handles individual step execution
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pipeline.base_step import BaseStep, StepResult, StepStatus
from agents.pipeline.sql_agent import SQLAgent
from agents.pipeline.context_loader import ContextLoader

logger = logging.getLogger(__name__)

class StepType(Enum):
    """Types of pipeline steps"""
    CONTEXT_LOAD = "context_load"
    SQL_GENERATION = "sql_generation"
    SQL_VALIDATION = "sql_validation"
    SQL_EXECUTION = "sql_execution"
    RESULT_PROCESSING = "result_processing"
    VISUALIZATION = "visualization"
    BUDGET_INTEGRATION = "budget_integration"

@dataclass
class StepConfig:
    """Configuration for a pipeline step"""
    step_type: StepType
    name: str
    description: str
    enabled: bool = True
    timeout: int = 30
    retry_count: int = 2
    parameters: Dict[str, Any] = None

class ContextLoadStep(BaseStep):
    """Step for loading context data"""

    def __init__(self, name: str, context_loader: ContextLoader, config: Dict[str, Any] = None):
        super().__init__(name, "Load context data for SQL generation")
        self.context_loader = context_loader
        self.config = config or {}

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Load context data based on query type"""
        try:
            query = input_data.get('query', '')
            query_type = input_data.get('query_type', 'general')

            # Load context for the query type
            context = self.context_loader.get_context_for_query_type(query_type)

            return StepResult(
                step_name=self.name,
                status=StepStatus.SUCCESS,
                data={
                    **input_data,
                    'context': context,
                    'schemas_loaded': len(context.get('schemas', {})),
                    'templates_loaded': len(context.get('templates', {})),
                    'examples_loaded': len(context.get('examples', []))
                }
            )

        except Exception as e:
            return StepResult(
                step_name=self.name,
                status=StepStatus.FAILED,
                data=input_data,
                error=f"Failed to load context: {str(e)}"
            )

    def get_required_inputs(self) -> List[str]:
        return ['query']

    def get_output_keys(self) -> List[str]:
        return ['context', 'schemas_loaded', 'templates_loaded', 'examples_loaded']

class SQLGenerationStep(BaseStep):
    """Step for generating SQL queries"""

    def __init__(self, name: str, sql_agent: SQLAgent, config: Dict[str, Any] = None):
        super().__init__(name, "Generate SQL query from natural language")
        self.sql_agent = sql_agent
        self.config = config or {}

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Generate SQL query using the SQL agent"""
        try:
            query = input_data.get('query', '')
            query_type = input_data.get('query_type')
            use_template = self.config.get('use_template')
            template_params = self.config.get('template_params')

            # Generate SQL
            result = await self.sql_agent.generate_sql(
                query=query,
                query_type=query_type,
                use_template=use_template,
                template_params=template_params
            )

            return StepResult(
                step_name=self.name,
                status=StepStatus.SUCCESS if result.get('validation', {}).get('is_valid', False) else StepStatus.FAILED,
                data={
                    **input_data,
                    'sql_query': result.get('sql_query', ''),
                    'generation_result': result,
                    'validation_errors': result.get('validation', {}).get('errors', []),
                    'validation_warnings': result.get('validation', {}).get('warnings', [])
                },
                error=None if result.get('validation', {}).get('is_valid', False) else 'SQL validation failed'
            )

        except Exception as e:
            return StepResult(
                step_name=self.name,
                status=StepStatus.FAILED,
                data=input_data,
                error=f"Failed to generate SQL: {str(e)}"
            )

    def get_required_inputs(self) -> List[str]:
        return ['query']

    def get_output_keys(self) -> List[str]:
        return ['sql_query', 'generation_result', 'validation_errors', 'validation_warnings']

class SQLValidationStep(BaseStep):
    """Step for validating SQL queries"""

    def __init__(self, name: str, sql_agent: SQLAgent, config: Dict[str, Any] = None):
        super().__init__(name, "Validate generated SQL query")
        self.sql_agent = sql_agent
        self.config = config or {}

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Validate SQL query"""
        try:
            sql_query = input_data.get('sql_query', '')

            if not sql_query:
                return StepResult(
                    step_name=self.name,
                    status=StepStatus.FAILED,
                    data=input_data,
                    error="No SQL query to validate"
                )

            # Validate SQL
            validation = self.sql_agent.validate_sql_syntax(sql_query)

            return StepResult(
                step_name=self.name,
                status=StepStatus.SUCCESS if validation.get('is_valid', False) else StepStatus.FAILED,
                data={
                    **input_data,
                    'validation_result': validation,
                    'is_valid': validation.get('is_valid', False)
                },
                error=None if validation.get('is_valid', False) else f"Validation errors: {validation.get('errors', [])}"
            )

        except Exception as e:
            return StepResult(
                step_name=self.name,
                status=StepStatus.FAILED,
                data=input_data,
                error=f"Failed to validate SQL: {str(e)}"
            )

    def get_required_inputs(self) -> List[str]:
        return ['sql_query']

    def get_output_keys(self) -> List[str]:
        return ['validation_result', 'is_valid']

class SQLExecutionStep(BaseStep):
    """Step for executing SQL queries"""

    def __init__(self, name: str, sql_agent: SQLAgent, config: Dict[str, Any] = None):
        super().__init__(name, "Execute SQL query against database")
        self.sql_agent = sql_agent
        self.config = config or {}

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute SQL query"""
        try:
            sql_query = input_data.get('sql_query', '')

            if not sql_query:
                return StepResult(
                    step_name=self.name,
                    status=StepStatus.FAILED,
                    data=input_data,
                    error="No SQL query to execute"
                )

            # Check if validation passed (if available)
            if 'is_valid' in input_data and not input_data['is_valid']:
                return StepResult(
                    step_name=self.name,
                    status=StepStatus.SKIPPED,
                    data=input_data,
                    error="Skipped execution due to validation failure"
                )

            # Execute SQL
            execution_result = await self.sql_agent.execute_sql(sql_query)

            return StepResult(
                step_name=self.name,
                status=StepStatus.SUCCESS if execution_result.get('success', False) else StepStatus.FAILED,
                data={
                    **input_data,
                    'execution_result': execution_result,
                    'query_data': execution_result.get('data'),
                    'row_count': len(execution_result.get('data', [])) if execution_result.get('data') else 0
                },
                error=execution_result.get('error') if not execution_result.get('success') else None
            )

        except Exception as e:
            return StepResult(
                step_name=self.name,
                status=StepStatus.FAILED,
                data=input_data,
                error=f"Failed to execute SQL: {str(e)}"
            )

    def get_required_inputs(self) -> List[str]:
        return ['sql_query']

    def get_output_keys(self) -> List[str]:
        return ['execution_result', 'query_data', 'row_count']

class BudgetIntegrationStep(BaseStep):
    """Step for integrating budget analysis data"""

    def __init__(self, name: str, sql_agent: SQLAgent, config: Dict[str, Any] = None):
        super().__init__(name, "Integrate budget analysis data with query results")
        self.sql_agent = sql_agent
        self.config = config or {}

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Integrate budget data"""
        try:
            query_data = input_data.get('query_data', [])
            original_query = input_data.get('query', '')

            # Check if budget integration is needed
            if not self._should_integrate_budget(original_query):
                return StepResult(
                    step_name=self.name,
                    status=StepStatus.SKIPPED,
                    data={
                        **input_data,
                        'budget_integrated': False,
                        'skip_reason': 'Budget integration not needed for this query'
                    }
                )

            # Generate budget integration query
            budget_query = self._generate_budget_query(original_query, input_data.get('sql_query', ''))

            if budget_query:
                # Execute budget query
                budget_result = await self.sql_agent.execute_sql(budget_query)

                if budget_result.get('success', False):
                    # Merge budget data with original results
                    integrated_data = self._merge_budget_data(query_data, budget_result.get('data', []))

                    return StepResult(
                        step_name=self.name,
                        status=StepStatus.SUCCESS,
                        data={
                            **input_data,
                            'query_data': integrated_data,
                            'budget_data': budget_result.get('data', []),
                            'budget_integrated': True,
                            'budget_query': budget_query
                        }
                    )

            return StepResult(
                step_name=self.name,
                status=StepStatus.FAILED,
                data=input_data,
                error="Failed to generate or execute budget query"
            )

        except Exception as e:
            return StepResult(
                step_name=self.name,
                status=StepStatus.FAILED,
                data=input_data,
                error=f"Failed to integrate budget data: {str(e)}"
            )

    def _should_integrate_budget(self, query: str) -> bool:
        """Determine if budget integration is needed"""
        budget_keywords = ['budget', 'forecast', 'planned', 'target', 'vs budget', 'variance', 'fy24', 'fy25', 'fy26']
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in budget_keywords)

    def _generate_budget_query(self, original_query: str, sql_query: str) -> str:
        """Generate SQL query to fetch budget data"""
        # Updated to use the correct budget_analysis table
        return """
        SELECT
            cto,
            tr_product_pillar_team,
            tr_subpillar_name,
            tr_product_id,
            tr_product,
            fy_24_budget,
            fy_25_budget,
            fy_26_budget,
            fy26_ytd_spend,
            fy26_projected_spend
        FROM budget_analysis
        WHERE fy_26_budget > 0
        """

    def _merge_budget_data(self, query_data: List[Dict], budget_data: List[Dict]) -> List[Dict]:
        """Merge query results with budget data"""
        # Create budget lookup by tr_product_id
        budget_lookup = {}
        for budget_row in budget_data:
            tr_product_id = budget_row.get('tr_product_id')
            if tr_product_id:
                budget_lookup[tr_product_id] = budget_row

        # Add budget information to query data
        enhanced_data = []
        for row in query_data:
            enhanced_row = row.copy()
            tr_product_id = row.get('tr_product_id')

            if tr_product_id and tr_product_id in budget_lookup:
                budget_info = budget_lookup[tr_product_id]
                enhanced_row['fy_26_budget'] = budget_info.get('fy_26_budget', 0)
                enhanced_row['fy26_ytd_spend'] = budget_info.get('fy26_ytd_spend', 0)
                enhanced_row['fy26_projected_spend'] = budget_info.get('fy26_projected_spend', 0)

                # Calculate budget variance if cost data is available
                if 'cost' in row and budget_info.get('fy_26_budget', 0) > 0:
                    budget_amount = budget_info.get('fy_26_budget', 0)
                    enhanced_row['budget_variance'] = row['cost'] - budget_amount
                    enhanced_row['budget_variance_pct'] = ((row['cost'] - budget_amount) / budget_amount) * 100

            enhanced_data.append(enhanced_row)

        return enhanced_data

    def get_required_inputs(self) -> List[str]:
        return ['query', 'query_data']

    def get_output_keys(self) -> List[str]:
        return ['budget_data', 'budget_integrated', 'budget_query']

class StepExecutor:
    """Executor for pipeline steps with context management"""

    def __init__(self,
                 context_loader: ContextLoader,
                 sql_agent: SQLAgent):
        self.context_loader = context_loader
        self.sql_agent = sql_agent
        self.step_registry = {}
        self._register_default_steps()

        logger.info("Initialized StepExecutor with default steps")

    def _register_default_steps(self):
        """Register default step types"""
        self.step_registry = {
            StepType.CONTEXT_LOAD: ContextLoadStep,
            StepType.SQL_GENERATION: SQLGenerationStep,
            StepType.SQL_VALIDATION: SQLValidationStep,
            StepType.SQL_EXECUTION: SQLExecutionStep,
            StepType.BUDGET_INTEGRATION: BudgetIntegrationStep
        }

    def register_step_type(self, step_type: StepType, step_class: type):
        """Register a custom step type"""
        self.step_registry[step_type] = step_class
        logger.debug(f"Registered custom step type: {step_type}")

    def create_step(self, config: StepConfig) -> BaseStep:
        """Create a step instance from configuration"""
        try:
            step_class = self.step_registry.get(config.step_type)
            if not step_class:
                raise ValueError(f"Unknown step type: {config.step_type}")

            # Create step with appropriate dependencies
            if config.step_type == StepType.CONTEXT_LOAD:
                step = step_class(config.name, self.context_loader, config.parameters)
            elif config.step_type in [StepType.SQL_GENERATION, StepType.SQL_VALIDATION,
                                     StepType.SQL_EXECUTION, StepType.BUDGET_INTEGRATION]:
                step = step_class(config.name, self.sql_agent, config.parameters)
            else:
                step = step_class(config.name, config.parameters)

            logger.debug(f"Created step '{config.name}' of type {config.step_type}")
            return step

        except Exception as e:
            logger.error(f"Error creating step '{config.name}': {str(e)}")
            raise

    def create_pipeline_steps(self, step_configs: List[StepConfig]) -> List[BaseStep]:
        """Create multiple pipeline steps from configurations"""
        steps = []
        for config in step_configs:
            if config.enabled:
                step = self.create_step(config)
                steps.append(step)
            else:
                logger.debug(f"Skipping disabled step: {config.name}")

        logger.info(f"Created {len(steps)} pipeline steps")
        return steps

    def get_default_pipeline_config(self) -> List[StepConfig]:
        """Get default pipeline configuration"""
        return [
            StepConfig(
                step_type=StepType.CONTEXT_LOAD,
                name="load_context",
                description="Load context data for query processing",
                timeout=10
            ),
            StepConfig(
                step_type=StepType.SQL_GENERATION,
                name="generate_sql",
                description="Generate SQL from natural language query",
                timeout=30
            ),
            StepConfig(
                step_type=StepType.SQL_VALIDATION,
                name="validate_sql",
                description="Validate generated SQL query",
                timeout=5
            ),
            StepConfig(
                step_type=StepType.SQL_EXECUTION,
                name="execute_sql",
                description="Execute SQL query against database",
                timeout=60
            ),
            StepConfig(
                step_type=StepType.BUDGET_INTEGRATION,
                name="integrate_budget",
                description="Integrate budget analysis data if needed",
                timeout=30,
                enabled=False  # Disabled by default
            )
        ]

    def get_step_types(self) -> List[StepType]:
        """Get available step types"""
        return list(self.step_registry.keys())