"""
Step 2: SQL Generation
Generates SQL query from natural language using LLM
"""
from typing import Dict, Any, List
from ..base_step import BaseStep, StepResult, StepStatus
from agents.bigquery.database import BigQueryConnection
from agents.bigquery.sql_toolkit import SQLAgentBuilder
from llm.factory import LLMProviderFactory
from config.settings import settings

class SQLGenerationStep(BaseStep):
    """Generate SQL query from natural language"""

    def __init__(self):
        super().__init__(
            name="sql_generation",
            description="Convert natural language to SQL query"
        )
        self.connection = BigQueryConnection()
        self.database = self.connection.get_langchain_database()

    def get_required_inputs(self) -> List[str]:
        return ["processed_question", "settings"]

    def get_output_keys(self) -> List[str]:
        return ["sql_query", "llm_response", "generation_metadata"]

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Generate SQL query"""
        question = input_data["processed_question"]
        settings = input_data["settings"]
        metadata = input_data.get("metadata", {})

        # Initialize LLM provider
        llm_provider = LLMProviderFactory.create_provider(settings.get("llm_provider"))
        llm = llm_provider.get_model()

        # Build SQL agent
        agent_builder = SQLAgentBuilder(self.database, llm)

        # Create enhanced prompt based on question type
        enhanced_prompt = self._get_enhanced_prompt(metadata.get("question_type"), metadata.get("expected_viz_type"))

        sql_agent = agent_builder.create_agent(
            max_iterations=settings.get("max_iterations", 15),
            max_execution_time=settings.get("timeout", 60),
            prefix=enhanced_prompt
        )

        try:
            # Generate SQL using the agent
            self.logger.info(f"Generating SQL for: {question}")

            # Use invoke for better error handling
            try:
                result = sql_agent.invoke({"input": question})
                if isinstance(result, dict):
                    llm_response = result.get("output", str(result))
                else:
                    llm_response = str(result)
            except Exception as agent_error:
                self.logger.debug(f"Agent invoke failed, trying run method: {agent_error}")
                llm_response = sql_agent.run(question)

            # Extract SQL query from response
            sql_query = self._extract_sql_query(llm_response)

            # Generate metadata about the SQL generation
            generation_metadata = {
                "llm_provider": llm_provider.provider_name,
                "model": llm_provider.model_name,
                "response_length": len(llm_response),
                "sql_extracted": bool(sql_query),
                "generation_method": "langchain_agent"
            }

            return StepResult(
                step_name=self.name,
                status=StepStatus.SUCCESS,
                data={
                    "sql_query": sql_query,
                    "llm_response": llm_response,
                    "generation_metadata": generation_metadata
                }
            )

        except Exception as e:
            self.logger.error(f"SQL generation failed: {e}")
            return StepResult(
                step_name=self.name,
                status=StepStatus.FAILED,
                data={},
                error=f"SQL generation failed: {str(e)}"
            )

    def _get_enhanced_prompt(self, question_type: str, expected_viz_type: str) -> str:
        """Get enhanced prompt based on question characteristics"""
        base_prompt = f"""You are an expert BigQuery SQL analyst with advanced data visualization skills.

Dataset: {settings.gcp_project_id}.{settings.bq_dataset}

Main table 'cost_analysis' has these columns:
- date: Date of cost
- cto: Tech organization
- cloud: Cloud provider (AWS, Azure, GCP)
- tr_product_pillar_team: Team name
- tr_subpillar_name: Sub-pillar name
- tr_product_id: Product identifier
- tr_product: Product name
- application: Application name
- service_name: Service name
- managed_service: Managed service name (EC2, S3, etc)
- environment: PROD or NON-PROD
- cost: Daily cost in USD

Question Type: {question_type}
Expected Visualization: {expected_viz_type}

IMPORTANT FORMATTING RULES FOR VISUALIZATIONS:
"""

        # Add specific formatting rules based on expected visualization
        if expected_viz_type == "bar":
            base_prompt += """
For TOP/RANKING queries (Bar Charts):
   Format: "1. [Name]: $[Amount]" or "1) [Name] ($[Amount])"
   Example: "1. Application A: $45,000"
"""
        elif expected_viz_type == "pie":
            base_prompt += """
For DISTRIBUTION/BREAKDOWN (Pie Charts):
   Format: "• [Category]: $[Amount] ([Percentage]%)"
   Example: "• Production: $750,000 (53.5%)"
"""
        elif expected_viz_type == "line":
            base_prompt += """
For TREND/TIME SERIES (Line Charts):
   Include dates and values in the response
   Example: "2024-01-01: $45,000, 2024-01-02: $46,500..."
"""
        elif expected_viz_type == "indicator":
            base_prompt += """
For TOTALS/METRICS (KPI Indicators):
   Format: "The total/average [metric] is $[Amount]"
   Example: "The total cost is $1,400,212.47"
"""

        base_prompt += """
SQL Guidelines:
- Use proper BigQuery SQL syntax
- Format costs with 2 decimals using FORMAT() or ROUND()
- Limit to relevant rows (usually 5-20 for visualizations)
- Use DATE_SUB(CURRENT_DATE(), INTERVAL X DAY) for date ranges
- Order results appropriately (DESC for top, ASC for trends)

Always structure your response to be easily parseable for visualization."""

        return base_prompt

    def _extract_sql_query(self, response: str) -> str:
        """Extract SQL query from LLM response"""
        import re

        # Try multiple patterns to extract SQL
        sql_patterns = [
            r'```sql\n(.+?)```',  # SQL in code blocks
            r'```\n(.+?)```',     # Generic code blocks
            r'(SELECT[^;]+;?)',   # Direct SELECT statements
        ]

        response_upper = response.upper()
        if "SELECT" in response_upper:
            for pattern in sql_patterns:
                matches = re.findall(pattern, response, re.IGNORECASE | re.DOTALL)
                if matches:
                    sql_query = matches[0].strip()
                    # Remove markdown formatting if present
                    sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
                    return sql_query

            # Fallback to line-by-line extraction
            lines = response.split('\n')
            sql_lines = []
            in_sql = False
            for line in lines:
                if "SELECT" in line.upper():
                    in_sql = True
                if in_sql:
                    sql_lines.append(line)
                    if ";" in line:
                        break
            if sql_lines:
                return '\n'.join(sql_lines).strip()

        return None

    async def health_check(self) -> Dict[str, Any]:
        """Check health of SQL generation components"""
        health = {"status": "healthy"}

        try:
            # Test database connection
            if not self.connection.test_connection():
                health["status"] = "unhealthy"
                health["error"] = "Database connection failed"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)

        return health