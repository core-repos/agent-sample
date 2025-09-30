"""
Pipeline Agent - Main orchestrator for context-aware SQL generation
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import sys
from pathlib import Path

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.pipeline.context_loader import ContextLoader, ContextConfig
from agents.pipeline.sql_agent import SQLAgent
from agents.pipeline.step_executor import StepExecutor, StepConfig, StepType
from pipeline.base_step import BaseStep, StepResult, StepStatus

logger = logging.getLogger(__name__)

class PipelineConfig:
    """Configuration for pipeline agent"""

    def __init__(self,
                 context_config: ContextConfig = None,
                 pipeline_timeout: int = 300,
                 max_retries: int = 2,
                 enable_budget_integration: bool = False,
                 enable_parallel_execution: bool = False,
                 enable_caching: bool = True):

        self.context_config = context_config or ContextConfig()
        self.pipeline_timeout = pipeline_timeout
        self.max_retries = max_retries
        self.enable_budget_integration = enable_budget_integration
        self.enable_parallel_execution = enable_parallel_execution
        self.enable_caching = enable_caching

class PipelineAgent:
    """Main pipeline orchestrator for context-aware SQL generation"""

    def __init__(self,
                 config: PipelineConfig = None,
                 bigquery_agent = None,
                 database_connection = None):

        self.config = config or PipelineConfig()

        # Initialize components
        self.context_loader = ContextLoader(self.config.context_config)
        self.sql_agent = SQLAgent(
            context_loader=self.context_loader,
            bigquery_agent=bigquery_agent,
            database_connection=database_connection
        )
        self.step_executor = StepExecutor(self.context_loader, self.sql_agent)

        # Pipeline state
        self.pipeline_cache = {} if self.config.enable_caching else None
        self.execution_history = []

        logger.info("Initialized PipelineAgent with context-aware SQL generation")

    def _generate_cache_key(self, query: str, pipeline_config: List[StepConfig]) -> str:
        """Generate cache key for pipeline execution"""
        import hashlib
        content = f"{query}_{[s.name for s in pipeline_config]}"
        return hashlib.md5(content.encode()).hexdigest()

    def _is_cache_valid(self, cache_key: str, ttl: int = 3600) -> bool:
        """Check if cached result is still valid"""
        if not self.pipeline_cache or cache_key not in self.pipeline_cache:
            return False

        cache_entry = self.pipeline_cache[cache_key]
        cache_time = cache_entry.get('timestamp', 0)
        now = datetime.now().timestamp()
        return (now - cache_time) < ttl

    async def process_query(self,
                           query: str,
                           query_type: str = None,
                           custom_pipeline: List[StepConfig] = None,
                           use_cache: bool = True) -> Dict[str, Any]:
        """Process a natural language query through the pipeline"""

        start_time = datetime.now()
        execution_id = f"exec_{int(start_time.timestamp())}"

        try:
            logger.info(f"Processing query [{execution_id}]: {query[:100]}...")

            # Detect query type if not provided
            if not query_type:
                query_type = self.sql_agent.detect_query_type(query)

            # Use custom pipeline or default
            pipeline_config = custom_pipeline or self._get_default_pipeline_config(query_type)

            # Check cache if enabled
            cache_key = self._generate_cache_key(query, pipeline_config)
            if use_cache and self.config.enable_caching and self._is_cache_valid(cache_key):
                logger.info(f"Returning cached result for query [{execution_id}]")
                cached_result = self.pipeline_cache[cache_key]['result']
                cached_result['from_cache'] = True
                return cached_result

            # Create pipeline steps
            steps = self.step_executor.create_pipeline_steps(pipeline_config)

            # Execute pipeline
            pipeline_result = await self._execute_pipeline(
                steps=steps,
                initial_data={'query': query, 'query_type': query_type},
                execution_id=execution_id
            )

            # Build final result
            final_result = self._build_final_result(pipeline_result, start_time, execution_id)

            # Cache result if successful
            if (use_cache and self.config.enable_caching and
                final_result.get('status') == 'success'):
                self.pipeline_cache[cache_key] = {
                    'result': final_result,
                    'timestamp': datetime.now().timestamp()
                }

            # Store in execution history
            self.execution_history.append({
                'execution_id': execution_id,
                'query': query,
                'query_type': query_type,
                'status': final_result.get('status'),
                'execution_time': final_result.get('execution_time'),
                'timestamp': start_time.isoformat()
            })

            logger.info(f"Completed query processing [{execution_id}] in "
                       f"{final_result.get('execution_time', 0):.2f}s")

            return final_result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error processing query [{execution_id}]: {str(e)}")

            return {
                'execution_id': execution_id,
                'status': 'error',
                'error': str(e),
                'query': query,
                'query_type': query_type,
                'execution_time': execution_time,
                'timestamp': start_time.isoformat(),
                'steps_completed': 0,
                'from_cache': False
            }

    async def _execute_pipeline(self,
                               steps: List[BaseStep],
                               initial_data: Dict[str, Any],
                               execution_id: str) -> List[StepResult]:
        """Execute pipeline steps sequentially or in parallel"""

        if self.config.enable_parallel_execution:
            return await self._execute_parallel_pipeline(steps, initial_data, execution_id)
        else:
            return await self._execute_sequential_pipeline(steps, initial_data, execution_id)

    async def _execute_sequential_pipeline(self,
                                          steps: List[BaseStep],
                                          initial_data: Dict[str, Any],
                                          execution_id: str) -> List[StepResult]:
        """Execute pipeline steps sequentially"""

        results = []
        current_data = initial_data.copy()

        for i, step in enumerate(steps):
            try:
                logger.debug(f"Executing step {i+1}/{len(steps)}: {step.name} [{execution_id}]")

                # Execute step with retry logic
                step_result = await self._execute_step_with_retry(step, current_data)
                results.append(step_result)

                # Update current data for next step
                if step_result.status == StepStatus.SUCCESS:
                    current_data.update(step_result.data)
                elif step_result.status == StepStatus.FAILED:
                    logger.error(f"Step {step.name} failed: {step_result.error}")
                    # Stop pipeline on failure
                    break
                # Continue on SKIPPED status

            except Exception as e:
                logger.error(f"Unexpected error in step {step.name}: {str(e)}")
                results.append(StepResult(
                    step_name=step.name,
                    status=StepStatus.FAILED,
                    data=current_data,
                    error=f"Unexpected error: {str(e)}"
                ))
                break

        return results

    async def _execute_parallel_pipeline(self,
                                        steps: List[BaseStep],
                                        initial_data: Dict[str, Any],
                                        execution_id: str) -> List[StepResult]:
        """Execute independent pipeline steps in parallel"""

        # Identify dependencies between steps
        dependency_graph = self._build_dependency_graph(steps)

        # Execute steps in dependency order with parallelization
        executed_steps = set()
        results = []
        current_data = initial_data.copy()

        while len(executed_steps) < len(steps):
            # Find steps that can be executed (dependencies satisfied)
            ready_steps = [
                step for step in steps
                if step.name not in executed_steps and
                all(dep in executed_steps for dep in dependency_graph.get(step.name, []))
            ]

            if not ready_steps:
                logger.error("Circular dependency detected in pipeline")
                break

            # Execute ready steps in parallel
            if len(ready_steps) == 1:
                # Single step - execute normally
                step_result = await self._execute_step_with_retry(ready_steps[0], current_data)
                results.append(step_result)
                executed_steps.add(ready_steps[0].name)

                if step_result.status == StepStatus.SUCCESS:
                    current_data.update(step_result.data)

            else:
                # Multiple steps - execute in parallel
                tasks = [
                    self._execute_step_with_retry(step, current_data)
                    for step in ready_steps
                ]
                parallel_results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, result in enumerate(parallel_results):
                    if isinstance(result, Exception):
                        result = StepResult(
                            step_name=ready_steps[i].name,
                            status=StepStatus.FAILED,
                            data=current_data,
                            error=str(result)
                        )

                    results.append(result)
                    executed_steps.add(ready_steps[i].name)

                    if result.status == StepStatus.SUCCESS:
                        current_data.update(result.data)

        return results

    def _build_dependency_graph(self, steps: List[BaseStep]) -> Dict[str, List[str]]:
        """Build dependency graph for steps based on input/output requirements"""
        dependencies = {}

        for step in steps:
            step_deps = []
            required_inputs = step.get_required_inputs()

            for other_step in steps:
                if other_step.name != step.name:
                    output_keys = other_step.get_output_keys()
                    if any(inp in output_keys for inp in required_inputs):
                        step_deps.append(other_step.name)

            dependencies[step.name] = step_deps

        return dependencies

    async def _execute_step_with_retry(self, step: BaseStep, input_data: Dict[str, Any]) -> StepResult:
        """Execute step with retry logic"""
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    step.run(input_data),
                    timeout=getattr(step, 'timeout', 30)
                )

                if result.status != StepStatus.FAILED:
                    return result

                last_error = result.error
                if attempt < self.config.max_retries:
                    logger.warning(f"Step {step.name} failed (attempt {attempt + 1}), retrying: {result.error}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except asyncio.TimeoutError:
                last_error = f"Step timeout after {getattr(step, 'timeout', 30)}s"
                logger.error(f"Step {step.name} timed out (attempt {attempt + 1})")

            except Exception as e:
                last_error = str(e)
                logger.error(f"Step {step.name} error (attempt {attempt + 1}): {str(e)}")

        # All retries failed
        return StepResult(
            step_name=step.name,
            status=StepStatus.FAILED,
            data=input_data,
            error=f"Failed after {self.config.max_retries + 1} attempts: {last_error}"
        )

    def _get_default_pipeline_config(self, query_type: str) -> List[StepConfig]:
        """Get default pipeline configuration based on query type"""
        base_config = self.step_executor.get_default_pipeline_config()

        # Enable budget integration for budget-related queries
        if query_type in ['budget', 'variance', 'planning'] or self.config.enable_budget_integration:
            for config in base_config:
                if config.step_type == StepType.BUDGET_INTEGRATION:
                    config.enabled = True

        return base_config

    def _build_final_result(self,
                           pipeline_results: List[StepResult],
                           start_time: datetime,
                           execution_id: str) -> Dict[str, Any]:
        """Build final result from pipeline execution"""

        execution_time = (datetime.now() - start_time).total_seconds()

        # Determine overall status
        if not pipeline_results:
            status = 'error'
            error = 'No steps executed'
        elif any(r.status == StepStatus.FAILED for r in pipeline_results):
            status = 'failed'
            error = 'One or more steps failed'
        else:
            status = 'success'
            error = None

        # Extract key data from final step result
        final_data = pipeline_results[-1].data if pipeline_results else {}

        # Build step summary
        step_summary = [
            {
                'name': result.step_name,
                'status': result.status.value,
                'execution_time': result.execution_time,
                'error': result.error
            }
            for result in pipeline_results
        ]

        result = {
            'execution_id': execution_id,
            'status': status,
            'error': error,
            'query': final_data.get('query', ''),
            'query_type': final_data.get('query_type', ''),
            'sql_query': final_data.get('sql_query', ''),
            'query_data': final_data.get('query_data', []),
            'execution_time': execution_time,
            'timestamp': start_time.isoformat(),
            'steps_completed': len([r for r in pipeline_results if r.status == StepStatus.SUCCESS]),
            'total_steps': len(pipeline_results),
            'step_summary': step_summary,
            'from_cache': False
        }

        # Add optional data if available
        if 'validation_result' in final_data:
            result['validation'] = final_data['validation_result']

        if 'budget_integrated' in final_data:
            result['budget_integrated'] = final_data['budget_integrated']
            result['budget_data'] = final_data.get('budget_data', [])

        if 'context' in final_data:
            result['context_metadata'] = final_data['context'].get('metadata', {})

        return result

    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        return self.execution_history[-limit:] if self.execution_history else []

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.pipeline_cache:
            return {'cache_enabled': False}

        return {
            'cache_enabled': True,
            'cache_entries': len(self.pipeline_cache),
            'cache_keys': list(self.pipeline_cache.keys())
        }

    def clear_cache(self):
        """Clear pipeline cache"""
        if self.pipeline_cache:
            self.pipeline_cache.clear()
            logger.info("Cleared pipeline cache")

    def get_available_query_types(self) -> List[str]:
        """Get available query types from context"""
        return [
            'aggregation', 'time_series', 'comparison', 'ranking',
            'filtering', 'join', 'analytical', 'budget', 'general'
        ]

    def get_context_info(self) -> Dict[str, Any]:
        """Get information about loaded context"""
        return {
            'schemas': self.sql_agent.get_schema_info(),
            'templates': self.sql_agent.get_available_templates(),
            'cache_stats': self.context_loader.get_cache_stats()
        }