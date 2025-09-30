"""
BigQuery specialized agent for SQL analytics with enhanced visualization support
"""
import json
from typing import Any, Dict, Optional, List
import re
from datetime import datetime
from .database import BigQueryConnection
from .sql_toolkit import SQLAgentBuilder
from .visualization import VisualizationProcessor
from .validators.validation_coordinator import ValidationCoordinator
from llm.factory import LLMProviderFactory
from utils.cache import CacheManager
from utils.context_loader import ContextLoader
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class BigQueryAgent:
    """Specialized agent for BigQuery analytics"""
    
    def __init__(
        self,
        llm_provider: Optional[str] = None,
        enable_cache: bool = True,
        enable_visualization: bool = True,
        enable_validation: bool = True
    ):
        self.name = "BigQueryAgent"
        self.description = "Natural language to SQL analytics for BigQuery with validation and visualization support"
        self.logger = logger

        # Initialize components
        self.connection = BigQueryConnection()
        self.llm_provider = LLMProviderFactory.create_provider(llm_provider)
        self.llm = self.llm_provider.get_model()
        self.cache_manager = CacheManager() if enable_cache else None
        self.visualization_processor = VisualizationProcessor() if enable_visualization else None
        self.validation_coordinator = ValidationCoordinator(self.connection, llm_provider) if enable_validation else None
        self.context_loader = ContextLoader()
        
        # Build SQL agent with enhanced prompt
        self.database = self.connection.get_langchain_database()
        self.agent_builder = SQLAgentBuilder(self.database, self.llm)
        
        # Create agent with enhanced prompt for better visualization support
        from langchain.agents.agent_types import AgentType
        
        self.sql_agent = self.agent_builder.create_agent(
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            prefix=self._get_enhanced_prompt() if enable_visualization else None,
            max_iterations=settings.agent_max_iterations,
            max_execution_time=settings.agent_max_execution_time,
            verbose=False,  # Disable verbose logging for production
            handle_parsing_errors=True  # Handle parsing errors gracefully
        )
        
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that input contains a question"""
        return "question" in input_data and bool(input_data["question"])
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process natural language query"""
        question = input_data["question"]
        
        # Check cache if enabled
        if self.cache_manager:
            cached_result = self.cache_manager.get(question)
            if cached_result:
                self.logger.info(f"Cache hit for: {question}")
                return cached_result
        
        try:
            # Run the SQL agent
            self.logger.info(f"Processing query: {question}")
            
            # Use invoke instead of run for better error handling
            try:
                result = self.sql_agent.invoke({"input": question})
                # Extract the output from the result dict
                if isinstance(result, dict):
                    result = result.get("output", str(result))
            except Exception as agent_error:
                # If invoke fails, try run method
                self.logger.debug(f"Agent invoke failed, trying run method: {agent_error}")
                result = self.sql_agent.run(question)
            
            # Log only first 200 chars of result to avoid clutter
            self.logger.debug(f"SQL Agent result preview: {str(result)[:200]}...")
            
            # Check if agent stopped due to limits
            if "Agent stopped" in str(result) and "limit" in str(result).lower():
                self.logger.warning(f"Agent hit limits, result may be partial: {result}")
                # Try to extract partial result if available
                if result and result != "Agent stopped due to iteration limit or time limit.":
                    response = self._parse_result(result, question)
                    response["warning"] = "Query processing hit limits, results may be partial"
                    return response
            
            # Parse result
            response = self._parse_result(result, question)
            
            # Cache result if enabled
            if self.cache_manager:
                self.cache_manager.set(question, response)
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Query processing failed: {error_msg}")
            
            # Special handling for output parsing errors
            if "output parsing error" in error_msg.lower() or "could not parse" in error_msg.lower():
                self.logger.warning("LLM output parsing error occurred")
                # Try to extract the raw LLM output from the error message
                if "LLM output:" in error_msg:
                    try:
                        # Extract the LLM output from the error message
                        llm_output_start = error_msg.find("LLM output: `") + len("LLM output: `")
                        llm_output_end = error_msg.rfind("`")
                        if llm_output_start > len("LLM output: `") - 1 and llm_output_end > llm_output_start:
                            raw_output = error_msg[llm_output_start:llm_output_end]
                            self.logger.debug(f"Extracted raw LLM output: {raw_output[:200]}...")
                            # Parse the raw output
                            response = self._parse_result(raw_output, question)
                            response["warning"] = "Response extracted from parsing error"
                            
                            # Cache result if enabled
                            if self.cache_manager:
                                self.cache_manager.set(question, response)
                            
                            return response
                    except Exception as parse_error:
                        self.logger.error(f"Failed to extract output from parsing error: {parse_error}")
            
            # Special handling for iteration/time limits
            if "iteration limit" in error_msg.lower() or "time limit" in error_msg.lower():
                self.logger.warning("Agent hit iteration or time limit")
                error_response = {
                    "success": False,
                    "answer": "The query was too complex and exceeded processing limits. Try simplifying your question.",
                    "error": "Agent iteration/time limit exceeded",
                    "metadata": {
                        "llm_provider": self.llm_provider.provider_name,
                        "model": self.llm_provider.model_name,
                        "max_iterations": settings.agent_max_iterations,
                        "max_execution_time": settings.agent_max_execution_time
                    }
                }
                return error_response
            
            # Try fallback to cached response if available
            if self.cache_manager:
                fallback = self.cache_manager.get_fallback(question)
                if fallback:
                    self.logger.info("Using fallback cached response")
                    return fallback
            
            # Last resort: Return a safe error response
            return {
                "success": False,
                "answer": f"I encountered an error processing your query: {error_msg[:200]}. Please try rephrasing your question or simplifying it.",
                "error": error_msg[:500],
                "metadata": {
                    "llm_provider": self.llm_provider.provider_name,
                    "model": self.llm_provider.model_name
                }
            }
    
    def _parse_result(self, result: str, question: str) -> Dict[str, Any]:
        """Parse agent result into structured response"""
        # Try to extract SQL query if present
        sql_query = None
        
        # Try multiple patterns to extract SQL
        sql_patterns = [
            r'```sql\n(.+?)```',  # SQL in code blocks
            r'```\n(.+?)```',     # Generic code blocks
            r'(SELECT[^;]+;?)',   # Direct SELECT statements
        ]
        
        result_upper = result.upper()
        if "SELECT" in result_upper:
            for pattern in sql_patterns:
                matches = re.findall(pattern, result, re.IGNORECASE | re.DOTALL)
                if matches:
                    sql_query = matches[0]
                    break
            
            # Fallback to line-by-line extraction
            if not sql_query:
                lines = result.split('\n')
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
                    sql_query = '\n'.join(sql_lines)
        
        # Clean up SQL query if found
        if sql_query:
            sql_query = sql_query.strip()
            # Remove markdown formatting if present
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        
        # Determine visualization type based on question
        viz_type = self._determine_visualization(question, result)
        
        return {
            "success": True,
            "answer": result,
            "sql_query": sql_query,
            "visualization": viz_type,
            "metadata": {
                "llm_provider": self.llm_provider.provider_name,
                "model": self.llm_provider.model_name,
                "cached": False
            }
        }
    
    def _determine_visualization(self, question: str, result: str) -> Optional[str]:
        """Determine appropriate visualization type"""
        question_lower = question.lower()
        result_lower = result.lower() if result else ""
        
        # Check both question and result for visualization hints
        combined_text = question_lower + " " + result_lower
        
        if any(word in combined_text for word in ["top", "ranking", "highest", "lowest", "best", "worst"]):
            return "bar"
        elif any(word in combined_text for word in ["distribution", "breakdown", "percentage", "proportion"]):
            return "pie"
        elif any(word in combined_text for word in ["trend", "over time", "timeline", "daily", "monthly", "yearly"]):
            return "line"
        elif any(word in combined_text for word in ["total", "sum", "count", "average", "mean"]):
            return "indicator"
        elif any(word in combined_text for word in ["correlation", "relationship", "versus", "vs"]):
            return "scatter"
        
        return None
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution pipeline"""
        try:
            # Validate input
            if not self.validate_input(input_data):
                raise ValueError(f"Invalid input for {self.name}")
            
            # Process
            result = await self.process(input_data)
            
            self.logger.info(f"Successfully executed {self.name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in {self.name}: {e}")
            raise
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """Get information about the connected dataset"""
        return self.connection.get_dataset_info()
    
    def _get_enhanced_prompt(self) -> str:
        """Enhanced prompt for better visualization support"""
        return f"""You are an expert BigQuery SQL analyst with advanced data visualization skills.

Dataset: {self.connection.project_id}.{self.connection.dataset_id}

Cost table 'cost_analysis' has these columns (13 fields):
- date: Date of cost
- cto: Tech organization
- cloud: Cloud provider (AWS, Azure, GCP)
- tr_product_pillar_team: Team name
- tr_subpillar_name: Sub-pillar name
- tr_product_id: Product identifier (INTEGER)
- tr_product: Product name
- apm_id: Application Portfolio Management ID (STRING)
- application: Application name
- service_name: Service name
- managed_service: Managed service name (EC2, S3, etc)
- environment: PROD or NON-PROD
- cost: Daily cost in USD

APPLICATION HIERARCHY: cto → tr_product_pillar_team → tr_subpillar_name → tr_product_id → apm_id → application

Budget table 'budget_analysis' has these EXACT columns (DO NOT use any other field names):
- cto: Chief Technology Officer organization
- tr_product_pillar_team: Product pillar team name
- tr_subpillar_name: Sub-pillar name
- tr_product_id: Unique product identifier (INTEGER)
- tr_product: Product name
- fy_24_budget: Fiscal Year 2024 budget in USD (FLOAT)
- fy_25_budget: Fiscal Year 2025 budget in USD (FLOAT)
- fy_26_budget: Fiscal Year 2026 budget in USD (FLOAT)
- fy26_ytd_spend: FY26 year-to-date spending in USD (FLOAT)
- fy26_projected_spend: FY26 projected total spending in USD (FLOAT)

CRITICAL BUDGET FIELD RULES:
- ONLY use these exact field names: cto, tr_product_pillar_team, tr_subpillar_name, tr_product_id, tr_product, fy_24_budget, fy_25_budget, fy_26_budget, fy26_ytd_spend, fy26_projected_spend
- NEVER use: budget_id, budget_name, id, name (these fields DO NOT exist)
- Use tr_product_id for product identification, not budget_id
- Use tr_product for product names, not budget_name

CRITICAL QUERY GENERATION RULES:

1. For SIMPLE DAILY TRENDS (Line Charts):
   - DO NOT use window functions (SUM() OVER, AVG() OVER, LAG, LEAD, etc.) UNLESS explicitly requested
   - Use simple aggregation: SELECT date, SUM(cost) as daily_cost FROM cost_analysis WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) GROUP BY date ORDER BY date
   - Default to last 30 days if no date range specified
   - Each date should show the actual daily cost, NOT cumulative/running total
   - ORDER BY date ASC (chronological order)

2. For PER-APPLICATION TRENDS (Multi-Series Line Chart):
   - GROUP BY both date AND application: GROUP BY date, application
   - ORDER BY date, application (to group series properly)
   - Example: SELECT date, application, SUM(cost) as daily_cost FROM cost_analysis WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) GROUP BY date, application ORDER BY date, application
   - Response should show: "App1 - 2024-01-01: $500, App1 - 2024-01-02: $600, App2 - 2024-01-01: $300..."

3. For CUMULATIVE TRENDS (Area Charts - ONLY when explicitly requested):
   - Use window function ONLY when user says "cumulative", "running total", "accumulated"
   - Example: SELECT date, SUM(SUM(cost)) OVER (ORDER BY date) as cumulative_cost FROM cost_analysis GROUP BY date ORDER BY date
   - DO NOT use cumulative for simple "daily trend" requests

4. For ROLLING AVERAGES (ONLY when explicitly requested):
   - Add rolling average ONLY if user says "rolling average", "moving average", "smoothed", "7-day average"
   - Example: SELECT date, SUM(cost) as daily_cost, AVG(SUM(cost)) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as rolling_7day_avg FROM cost_analysis GROUP BY date ORDER BY date

5. For GRANULARITY (Daily/Weekly/Monthly):
   - Daily: GROUP BY date (default for "daily" keyword)
   - Weekly: GROUP BY DATE_TRUNC(date, WEEK) for "weekly" keyword
   - Monthly: GROUP BY FORMAT_DATE('%Y-%m', date) for "monthly" keyword

IMPORTANT FORMATTING RULES FOR VISUALIZATIONS:

1. For TOP/RANKING queries (Bar Charts):
   Format: "1. [Name]: $[Amount]" or "1) [Name] ($[Amount])"
   Example: "1. Application A: $45,000"

2. For DISTRIBUTION/BREAKDOWN (Pie Charts):
   Format: "• [Category]: $[Amount] ([Percentage]%)"
   Example: "• Production: $750,000 (53.5%)"

3. For SIMPLE TREND/TIME SERIES (Line Charts):
   Format: "Date: $Amount" for single series OR "Category - Date: $Amount" for multi-series
   Example Single: "2024-01-01: $45,000, 2024-01-02: $46,500..."
   Example Multi: "App1 - 2024-01-01: $500, App1 - 2024-01-02: $600, App2 - 2024-01-01: $300..."

4. For TOTALS/METRICS (KPI Indicators):
   Format: "The total/average [metric] is $[Amount]"
   Example: "The total cost is $1,400,212.47"

SQL Guidelines:
- Use proper BigQuery SQL syntax
- Format costs with 2 decimals using FORMAT() or ROUND()
- Limit to relevant rows (usually 5-20 for visualizations, 30-90 days for trends)
- Default date range: DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) for daily trends
- Order results appropriately (DESC for top, ASC for trends)

Always structure your response to be easily parseable for visualization."""
    
    async def process_with_validation(
        self,
        question: str,
        visualization_hint: Optional[str] = None,
        use_cache: bool = True,
        enable_validation: bool = True
    ) -> Dict[str, Any]:
        """Process question with full validation pipeline (10 iterations each for SQL and graph)"""
        # Check cache first
        cache_key = f"validated_{question}_{visualization_hint}" if visualization_hint else f"validated_{question}"
        if use_cache and self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached:
                self.logger.info(f"Cache hit for validated query: {question}")
                return cached

        try:
            # First get the basic SQL and answer
            basic_result = await self.process({"question": question, "use_cache": False})
            sql_query = basic_result.get("sql_query", "")
            answer = basic_result.get("answer", "")

            if not sql_query or not answer:
                self.logger.warning("No SQL query or answer generated for validation")
                return basic_result

            # Run full validation pipeline if validation is enabled
            if enable_validation and self.validation_coordinator:
                self.logger.info(f"Starting validated processing for: {question}")

                validation_report = await self.validation_coordinator.validate_complete_pipeline(
                    original_question=question,
                    sql_query=sql_query,
                    llm_answer=answer,
                    expected_viz_type=visualization_hint
                )

                # Use validated result
                result = validation_report.final_result
                result["validation_report"] = {
                    "success": validation_report.success,
                    "total_iterations": validation_report.total_iterations,
                    "execution_time": validation_report.total_execution_time,
                    "sql_iterations": validation_report.sql_report.iterations if validation_report.sql_report else 0,
                    "graph_iterations": validation_report.graph_report.iterations if validation_report.graph_report else 0
                }

                self.logger.info(f"Validation completed - Success: {validation_report.success}, Iterations: {validation_report.total_iterations}")

            else:
                # Fallback to basic processing with visualization
                result = await self.process_with_visualization(question, visualization_hint, False)

            result["timestamp"] = datetime.now().isoformat()

            # Cache the validated result
            if use_cache and self.cache_manager:
                self.cache_manager.set(cache_key, result)

            return result

        except Exception as e:
            self.logger.error(f"Error in validated processing: {e}")
            # Fallback to basic processing
            return await self.process_with_visualization(question, visualization_hint, use_cache)

    async def process_with_visualization(
        self,
        question: str,
        visualization_hint: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Process question with visualization support (legacy method)"""
        # Check cache
        cache_key = f"{question}_{visualization_hint}" if visualization_hint else question
        if use_cache and self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached:
                self.logger.info(f"Cache hit for: {question}")
                return cached

        try:
            # Process the question
            result = await self.process({"question": question, "use_cache": use_cache})
            answer = result.get("answer", "")

            # Add visualization if processor is available
            if self.visualization_processor:
                viz_type, chart_data = self.visualization_processor.determine_visualization(
                    question, answer, visualization_hint
                )
                result["visualization_type"] = viz_type
                result["chart_data"] = chart_data

                # Extract insights
                insights = self.visualization_processor.extract_insights(answer, viz_type)
                result["insights"] = insights

            result["timestamp"] = datetime.now().isoformat()

            # Cache the enhanced result
            if use_cache and self.cache_manager:
                self.cache_manager.set(cache_key, result)

            return result

        except Exception as e:
            self.logger.error(f"Error in visualization processing: {e}")
            # Return basic result without visualization
            return await self.process({"question": question, "use_cache": use_cache})
    
    def get_sample_questions(self) -> list:
        """Get sample questions for the dataset"""
        return [
            "What is the total cost?",
            "Show me the top 5 applications by cost",
            "What's the cost breakdown by environment?",
            "Display monthly cost trends",
            "Which resource has the highest cost?",
            "Show cost distribution by service",
            "What's the average cost per application?",
            "List all unique environments",
            "Show me costs greater than $10,000",
            "What percentage of cost is from production?"
        ]
    
    def get_visualization_examples(self) -> List[Dict[str, str]]:
        """Get example questions with visualization types"""
        return [
            {"question": "What are the top 5 applications by cost?", "visualization": "bar", "category": "Ranking"},
            {"question": "Show me the cost distribution by environment", "visualization": "pie", "category": "Distribution"},
            {"question": "Display the daily cost trend for the last 30 days", "visualization": "line", "category": "Trend"},
            {"question": "What is the total cost across all applications?", "visualization": "indicator", "category": "Metric"},
            {"question": "Show the correlation between application size and cost", "visualization": "scatter", "category": "Correlation"},
            {"question": "Display cost heatmap by day and service", "visualization": "heatmap", "category": "Matrix"},
            {"question": "Show hierarchical cost breakdown by team and application", "visualization": "treemap", "category": "Hierarchical"},
            {"question": "Display the conversion funnel from dev to prod", "visualization": "funnel", "category": "Pipeline"},
            {"question": "Show resource utilization gauge", "visualization": "gauge", "category": "Score"},
            {"question": "Display cumulative cost over time", "visualization": "area", "category": "Cumulative"}
        ]
    
    def get_chart_types(self) -> List[Dict[str, str]]:
        """Get supported chart types with descriptions"""
        return [
            {"type": "bar", "name": "Bar Chart", "use_case": "Rankings and comparisons"},
            {"type": "pie", "name": "Pie Chart", "use_case": "Distribution and proportions"},
            {"type": "line", "name": "Line Chart", "use_case": "Trends over time"},
            {"type": "scatter", "name": "Scatter Plot", "use_case": "Correlations and relationships"},
            {"type": "heatmap", "name": "Heat Map", "use_case": "Matrix data visualization"},
            {"type": "treemap", "name": "Tree Map", "use_case": "Hierarchical data"},
            {"type": "funnel", "name": "Funnel Chart", "use_case": "Process stages"},
            {"type": "gauge", "name": "Gauge Chart", "use_case": "Performance metrics"},
            {"type": "indicator", "name": "KPI Indicator", "use_case": "Single metrics"},
            {"type": "area", "name": "Area Chart", "use_case": "Cumulative trends"},
            {"type": "bubble", "name": "Bubble Chart", "use_case": "Three-dimensional data"},
            {"type": "waterfall", "name": "Waterfall Chart", "use_case": "Incremental changes"},
            {"type": "sankey", "name": "Sankey Diagram", "use_case": "Flow visualization"},
            {"type": "radar", "name": "Radar Chart", "use_case": "Multi-dimensional comparison"}
        ]