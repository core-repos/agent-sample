"""
SQL Agent with context-aware SQL generation
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from jinja2 import Template, Environment, BaseLoader
import re

from .context_loader import ContextLoader, ContextConfig
from ..bigquery.agent import BigQueryAgent
from ..bigquery.database import BigQueryConnection

logger = logging.getLogger(__name__)

class TemplateLoader(BaseLoader):
    """Custom Jinja2 template loader for SQL templates"""

    def __init__(self, templates: Dict[str, str]):
        self.templates = templates

    def get_source(self, environment, template):
        if template not in self.templates:
            raise FileNotFoundError(f"Template '{template}' not found")

        source = self.templates[template]
        return source, None, lambda: True

class SQLAgent:
    """Context-aware SQL generation agent"""

    def __init__(self,
                 context_loader: ContextLoader = None,
                 bigquery_agent: BigQueryAgent = None,
                 database_connection: BigQueryConnection = None):

        self.context_loader = context_loader or ContextLoader()
        self.bigquery_agent = bigquery_agent
        self.database_connection = database_connection

        # Initialize Jinja2 environment
        self.jinja_env = None
        self._init_template_environment()

        logger.info("Initialized SQLAgent with context support")

    def _init_template_environment(self):
        """Initialize Jinja2 template environment"""
        try:
            # Load templates from context
            templates = self.context_loader.load_query_templates()
            template_dict = {name: template.template for name, template in templates.items()}

            # Create custom loader and environment
            loader = TemplateLoader(template_dict)
            self.jinja_env = Environment(loader=loader)

            # Add custom filters
            self.jinja_env.filters['quote_identifier'] = self._quote_identifier
            self.jinja_env.filters['format_date'] = self._format_date
            self.jinja_env.filters['escape_string'] = self._escape_string

            logger.debug(f"Initialized Jinja2 environment with {len(template_dict)} templates")

        except Exception as e:
            logger.error(f"Error initializing template environment: {str(e)}")
            self.jinja_env = Environment()

    def _quote_identifier(self, identifier: str) -> str:
        """Quote SQL identifier (table/column names)"""
        return f"`{identifier}`"

    def _format_date(self, date_str: str, format_type: str = 'bigquery') -> str:
        """Format date for specific SQL dialect"""
        if format_type == 'bigquery':
            return f"DATE('{date_str}')"
        return f"'{date_str}'"

    def _escape_string(self, value: str) -> str:
        """Escape string value for SQL"""
        return value.replace("'", "''")

    def detect_query_type(self, query: str) -> str:
        """Detect the type of query being requested"""
        query_lower = query.lower()

        # Define query type patterns
        patterns = {
            'aggregation': ['sum', 'count', 'avg', 'total', 'average', 'group by'],
            'time_series': ['trend', 'over time', 'daily', 'monthly', 'yearly', 'time'],
            'comparison': ['compare', 'vs', 'versus', 'difference', 'between'],
            'ranking': ['top', 'bottom', 'rank', 'highest', 'lowest', 'best', 'worst'],
            'filtering': ['where', 'filter', 'specific', 'only', 'exclude'],
            'join': ['join', 'combine', 'merge', 'related', 'with'],
            'analytical': ['correlation', 'analysis', 'pattern', 'insight', 'relationship']
        }

        # Score each query type
        scores = {}
        for query_type, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                scores[query_type] = score

        # Return the highest scoring type, default to 'general'
        if scores:
            detected_type = max(scores, key=scores.get)
            logger.debug(f"Detected query type '{detected_type}' for query: {query[:50]}...")
            return detected_type

        logger.debug(f"No specific query type detected, using 'general' for: {query[:50]}...")
        return 'general'

    def build_context_prompt(self, query: str, query_type: str = None) -> str:
        """Build context-aware prompt for SQL generation"""
        try:
            # Detect query type if not provided
            if not query_type:
                query_type = self.detect_query_type(query)

            # Get relevant context
            context = self.context_loader.get_context_for_query_type(query_type)

            # Build schema information
            schema_info = []
            for table_name, schema in context.get('schemas', {}).items():
                columns_info = []
                for col in schema.columns:
                    col_desc = f"  - {col['name']} ({col['type']})"
                    if col.get('description'):
                        col_desc += f": {col['description']}"
                    columns_info.append(col_desc)

                table_info = f"""
Table: {table_name}
Description: {schema.description}
Columns:
{chr(10).join(columns_info)}"""

                if schema.sample_queries:
                    table_info += f"""
Sample Queries:
{chr(10).join(f'  - {q}' for q in schema.sample_queries)}"""

                schema_info.append(table_info)

            # Build template examples
            template_examples = []
            for template_name, template in context.get('templates', {}).items():
                example = f"""
Template: {template_name}
Description: {template.description}
Example: {template.example}"""
                template_examples.append(example)

            # Build SQL examples
            sql_examples = []
            for example in context.get('examples', []):
                ex_info = f"""
Query: {example.get('query', '')}
SQL: {example.get('sql', '')}
Explanation: {example.get('explanation', '')}"""
                sql_examples.append(ex_info)

            # Combine into comprehensive prompt
            prompt = f"""
You are a SQL expert specializing in BigQuery. Generate accurate SQL queries based on the user's request.

USER REQUEST: {query}

QUERY TYPE: {query_type}

AVAILABLE SCHEMAS:
{chr(10).join(schema_info)}

RELEVANT TEMPLATES:
{chr(10).join(template_examples)}

EXAMPLE QUERIES:
{chr(10).join(sql_examples)}

GUIDELINES:
1. Use proper BigQuery syntax and functions
2. Always qualify table names with dataset if needed
3. Use appropriate aggregation and filtering
4. Consider performance implications
5. Include helpful comments in complex queries
6. Validate column names against the schema
7. Use appropriate data types and conversions

Generate a complete, executable SQL query that answers the user's request:
"""

            logger.debug(f"Built context prompt for query type '{query_type}' "
                        f"({len(context.get('schemas', {}))} schemas, "
                        f"{len(context.get('templates', {}))} templates, "
                        f"{len(context.get('examples', []))} examples)")

            return prompt.strip()

        except Exception as e:
            logger.error(f"Error building context prompt: {str(e)}")
            # Fallback to basic prompt
            return f"""
Generate a BigQuery SQL query for the following request:

{query}

Please provide a complete, executable SQL query.
"""

    def apply_template(self, template_name: str, parameters: Dict[str, Any]) -> str:
        """Apply parameters to a specific template"""
        try:
            if not self.jinja_env:
                raise ValueError("Template environment not initialized")

            template = self.jinja_env.get_template(template_name)
            rendered_sql = template.render(**parameters)

            logger.debug(f"Applied template '{template_name}' with parameters: {list(parameters.keys())}")
            return rendered_sql.strip()

        except Exception as e:
            logger.error(f"Error applying template '{template_name}': {str(e)}")
            raise

    def validate_sql_syntax(self, sql: str) -> Dict[str, Any]:
        """Basic SQL syntax validation"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        try:
            # Basic checks
            sql_upper = sql.upper().strip()

            # Check for required SELECT
            if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
                validation_result['errors'].append("Query must start with SELECT or WITH")
                validation_result['is_valid'] = False

            # Check for balanced parentheses
            if sql.count('(') != sql.count(')'):
                validation_result['errors'].append("Unbalanced parentheses")
                validation_result['is_valid'] = False

            # Check for SQL injection patterns
            dangerous_patterns = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
            for pattern in dangerous_patterns:
                if pattern in sql_upper:
                    validation_result['warnings'].append(f"Contains potentially dangerous operation: {pattern}")

            # Check for proper table references
            if '`' not in sql and '.' in sql:
                validation_result['warnings'].append("Consider using backticks for table/column names")

        except Exception as e:
            validation_result['errors'].append(f"Validation error: {str(e)}")
            validation_result['is_valid'] = False

        return validation_result

    async def generate_sql(self,
                          query: str,
                          query_type: str = None,
                          use_template: str = None,
                          template_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate SQL query with context awareness"""
        start_time = datetime.now()

        try:
            logger.info(f"Generating SQL for query: {query[:100]}...")

            # If using a specific template
            if use_template and template_params:
                logger.debug(f"Using template '{use_template}' with parameters")
                sql = self.apply_template(use_template, template_params)
                method = 'template'
            else:
                # Use context-aware generation
                context_prompt = self.build_context_prompt(query, query_type)

                # Use BigQuery agent for SQL generation
                if self.bigquery_agent:
                    logger.debug("Using BigQueryAgent for SQL generation")
                    result = await self.bigquery_agent.process(context_prompt)
                    sql = result.get('sql_query', '')
                    method = 'agent'
                else:
                    logger.warning("No BigQuery agent available, returning context prompt")
                    sql = context_prompt
                    method = 'prompt_only'

            # Validate generated SQL
            validation = self.validate_sql_syntax(sql)

            execution_time = (datetime.now() - start_time).total_seconds()

            result = {
                'sql_query': sql,
                'query_type': query_type or self.detect_query_type(query),
                'generation_method': method,
                'validation': validation,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }

            if use_template:
                result['template_used'] = use_template
                result['template_params'] = template_params

            logger.info(f"Generated SQL in {execution_time:.2f}s using {method}")
            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error generating SQL: {str(e)}")

            return {
                'sql_query': '',
                'query_type': query_type or 'unknown',
                'generation_method': 'error',
                'validation': {'is_valid': False, 'errors': [str(e)], 'warnings': []},
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    async def execute_sql(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query using database connection"""
        try:
            if not self.database_connection:
                raise ValueError("No database connection available")

            logger.info(f"Executing SQL query: {sql[:100]}...")
            start_time = datetime.now()

            # Execute query
            result = await self.database_connection.execute_query(sql)

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                'success': True,
                'data': result,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error executing SQL: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': 0.0,
                'timestamp': datetime.now().isoformat()
            }

    def get_available_templates(self) -> Dict[str, Any]:
        """Get list of available query templates"""
        try:
            templates = self.context_loader.load_query_templates()
            return {
                name: {
                    'description': template.description,
                    'parameters': template.parameters,
                    'category': template.category,
                    'example': template.example
                }
                for name, template in templates.items()
            }
        except Exception as e:
            logger.error(f"Error getting available templates: {str(e)}")
            return {}

    def get_schema_info(self) -> Dict[str, Any]:
        """Get available schema information"""
        try:
            schemas = self.context_loader.load_table_schemas()
            return {
                name: {
                    'description': schema.description,
                    'columns': schema.columns,
                    'sample_queries': schema.sample_queries,
                    'relationships': schema.relationships
                }
                for name, schema in schemas.items()
            }
        except Exception as e:
            logger.error(f"Error getting schema info: {str(e)}")
            return {}