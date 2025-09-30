"""
LangChain SQL Toolkit integration
"""
from typing import Optional, Any
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents import AgentExecutor
from langchain.agents.agent_types import AgentType
from langchain.schema.language_model import BaseLanguageModel
import logging

logger = logging.getLogger(__name__)

class SQLAgentBuilder:
    """Builder for creating SQL agents with LangChain"""
    
    def __init__(self, database: SQLDatabase, llm: BaseLanguageModel):
        self.database = database
        self.llm = llm
        self.toolkit = SQLDatabaseToolkit(db=database, llm=llm)
        
    def create_agent(
        self,
        agent_type: AgentType = AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose: bool = False,
        handle_parsing_errors: bool = True,
        max_iterations: int = 30,  # Increased from 15 to 30
        max_execution_time: Optional[float] = 60.0,  # 60 seconds timeout
        prefix: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Create a SQL agent
        
        Args:
            agent_type: Type of agent to create
            verbose: Whether to print verbose output
            handle_parsing_errors: Whether to handle parsing errors gracefully
            max_iterations: Maximum number of iterations (default: 30)
            max_execution_time: Maximum execution time in seconds (default: 60)
            **kwargs: Additional arguments for the agent
            
        Returns:
            SQL Agent instance
        """
        # Build kwargs for agent creation
        agent_kwargs = {
            "llm": self.llm,
            "toolkit": self.toolkit,
            "agent_type": agent_type,
            "verbose": verbose,
            "handle_parsing_errors": True,  # Always handle parsing errors gracefully
            "max_iterations": max_iterations,
            "return_intermediate_steps": False,  # Don't return intermediate steps to reduce token usage
            **kwargs
        }
        
        # Add max_execution_time if provided
        if max_execution_time is not None:
            agent_kwargs["max_execution_time"] = max_execution_time
        
        # Add prefix if provided
        if prefix:
            agent_kwargs["prefix"] = prefix
            
        agent = create_sql_agent(**agent_kwargs)
        
        # If agent is an AgentExecutor, ensure parsing errors are handled
        if isinstance(agent, AgentExecutor):
            agent.handle_parsing_errors = True
        
        logger.info(f"Created SQL agent with {agent_type}")
        return agent
    
    def get_table_info(self) -> str:
        """Get information about database tables"""
        return self.database.get_table_info()
    
    def run_query(self, query: str) -> str:
        """Run a raw SQL query"""
        try:
            return self.database.run(query)
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise