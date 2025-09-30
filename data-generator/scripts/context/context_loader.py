#!/usr/bin/env python3
"""
Context Loader for Pipeline Step Agents
Loads context files (schemas, examples, prompts, pipelines) for agent operations
Version: 1.0.0
Created: 2024-09-28
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContextConfig:
    """Configuration for context loading"""
    project_id: str = "{{ GCP_PROJECT_ID }}"
    dataset: str = "agent_bq_dataset"
    current_date: str = "{{ CURRENT_DATE }}"
    context_root: str = "./context"

class ContextLoader:
    """
    Context loader for pipeline step agents
    Provides access to schemas, examples, prompts, and pipeline definitions
    """

    def __init__(self, config: ContextConfig = None):
        self.config = config or ContextConfig()
        self.context_root = Path(self.config.context_root)
        self._schemas = {}
        self._examples = {}
        self._prompts = {}
        self._pipelines = {}

        # Verify context directory structure
        self._verify_structure()

    def _verify_structure(self):
        """Verify context directory structure exists"""
        required_dirs = ["schemas", "examples", "prompts", "pipelines"]
        for dir_name in required_dirs:
            dir_path = self.context_root / dir_name
            if not dir_path.exists():
                raise FileNotFoundError(f"Required context directory not found: {dir_path}")
        logger.info(f"Context structure verified at {self.context_root}")

    def load_all_context(self) -> Dict[str, Any]:
        """Load all context files"""
        return {
            "schemas": self.load_schemas(),
            "examples": self.load_examples(),
            "prompts": self.load_prompts(),
            "pipelines": self.load_pipelines()
        }

    def load_schemas(self) -> Dict[str, Any]:
        """Load all schema files"""
        if not self._schemas:
            schemas_dir = self.context_root / "schemas"
            for schema_file in schemas_dir.glob("*.yaml"):
                table_name = schema_file.stem
                with open(schema_file, 'r') as f:
                    self._schemas[table_name] = yaml.safe_load(f)
                logger.info(f"Loaded schema: {table_name}")
        return self._schemas

    def load_examples(self) -> Dict[str, Any]:
        """Load all example query files"""
        if not self._examples:
            examples_dir = self.context_root / "examples"
            for example_file in examples_dir.glob("*.json"):
                example_name = example_file.stem
                with open(example_file, 'r') as f:
                    self._examples[example_name] = json.load(f)
                logger.info(f"Loaded examples: {example_name}")
        return self._examples

    def load_prompts(self) -> Dict[str, Any]:
        """Load all prompt template files"""
        if not self._prompts:
            prompts_dir = self.context_root / "prompts"
            for prompt_file in prompts_dir.glob("*.yaml"):
                prompt_name = prompt_file.stem
                with open(prompt_file, 'r') as f:
                    self._prompts[prompt_name] = yaml.safe_load(f)
                logger.info(f"Loaded prompts: {prompt_name}")
        return self._prompts

    def load_pipelines(self) -> Dict[str, Any]:
        """Load all pipeline definition files"""
        if not self._pipelines:
            pipelines_dir = self.context_root / "pipelines"
            for pipeline_file in pipelines_dir.glob("*.yaml"):
                pipeline_name = pipeline_file.stem
                with open(pipeline_file, 'r') as f:
                    self._pipelines[pipeline_name] = yaml.safe_load(f)
                logger.info(f"Loaded pipeline: {pipeline_name}")
        return self._pipelines

    def get_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema for specific table"""
        schemas = self.load_schemas()
        if table_name not in schemas:
            raise KeyError(f"Schema not found for table: {table_name}")
        return schemas[table_name]

    def get_schema_fields(self, table_name: str) -> List[Dict[str, Any]]:
        """Get field definitions for specific table"""
        schema = self.get_schema(table_name)
        return schema.get("schema", {}).get("fields", [])

    def get_example_queries(self, query_type: str = None, table: str = None) -> Dict[str, Any]:
        """Get example queries filtered by type or table"""
        examples = self.load_examples()

        if table:
            # Filter by table
            table_examples = {}
            for key, value in examples.items():
                if table in key or value.get("metadata", {}).get("table") == table:
                    table_examples[key] = value
            examples = table_examples

        if query_type:
            # Filter by query type
            filtered_examples = {}
            for key, value in examples.items():
                if query_type in value.get("query_examples", {}):
                    filtered_examples[key] = value
            examples = filtered_examples

        return examples

    def get_prompt_template(self, agent_type: str, prompt_name: str = None) -> Dict[str, Any]:
        """Get prompt template for specific agent type"""
        prompts = self.load_prompts()

        # Look for agent-specific prompts
        for prompt_file, prompt_data in prompts.items():
            if agent_type in prompt_file:
                if prompt_name:
                    templates = prompt_data.get("prompt_templates", {})
                    if prompt_name in templates:
                        return templates[prompt_name]
                return prompt_data

        raise KeyError(f"Prompt template not found for agent: {agent_type}")

    def get_pipeline_definition(self, pipeline_name: str) -> Dict[str, Any]:
        """Get pipeline definition by name"""
        pipelines = self.load_pipelines()

        for pipeline_file, pipeline_data in pipelines.items():
            pipeline_templates = pipeline_data.get("pipeline_templates", {})
            if pipeline_name in pipeline_templates:
                return pipeline_templates[pipeline_name]

        raise KeyError(f"Pipeline definition not found: {pipeline_name}")

    def render_template(self, template: str, **kwargs) -> str:
        """Render template with parameters"""
        # Simple template rendering - replace {{ variable }} patterns
        rendered = template

        # Add default parameters
        default_params = {
            "project_id": self.config.project_id,
            "dataset": self.config.dataset,
            "current_date": self.config.current_date
        }
        default_params.update(kwargs)

        for key, value in default_params.items():
            placeholder = f"{{{{ {key} }}}}"
            rendered = rendered.replace(placeholder, str(value))

        return rendered

    def get_visualization_hints(self, data_characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Get visualization recommendations based on data characteristics"""
        viz_prompts = self.get_prompt_template("visualization", "visualization_decision_engine")
        decision_matrix = viz_prompts.get("decision_matrix", {})

        recommendations = {}

        # Analyze data characteristics
        if data_characteristics.get("is_single_value"):
            recommendations = decision_matrix.get("data_characteristics", {}).get("single_value", {})
        elif data_characteristics.get("is_time_series"):
            recommendations = decision_matrix.get("data_characteristics", {}).get("time_series", {})
        elif data_characteristics.get("is_categorical"):
            recommendations = decision_matrix.get("data_characteristics", {}).get("categorical_values", {})
        elif data_characteristics.get("has_two_variables"):
            recommendations = decision_matrix.get("data_characteristics", {}).get("two_variables", {})

        return recommendations

    def validate_context(self) -> Dict[str, List[str]]:
        """Validate context files and return any issues"""
        issues = {
            "missing_files": [],
            "invalid_schemas": [],
            "broken_references": []
        }

        try:
            # Validate schemas
            schemas = self.load_schemas()
            for name, schema in schemas.items():
                if not schema.get("schema", {}).get("fields"):
                    issues["invalid_schemas"].append(f"No fields defined in {name}")

            # Validate examples
            examples = self.load_examples()
            for name, example_set in examples.items():
                if not example_set.get("query_examples"):
                    issues["invalid_schemas"].append(f"No query examples in {name}")

            # Validate prompts
            prompts = self.load_prompts()
            for name, prompt_set in prompts.items():
                if not prompt_set.get("prompt_templates"):
                    issues["invalid_schemas"].append(f"No prompt templates in {name}")

            # Validate pipelines
            pipelines = self.load_pipelines()
            for name, pipeline_set in pipelines.items():
                if not pipeline_set.get("pipeline_templates"):
                    issues["invalid_schemas"].append(f"No pipeline templates in {name}")

        except Exception as e:
            issues["missing_files"].append(str(e))

        return issues

class AgentContextManager:
    """
    Context manager for individual agents
    Provides contextual information based on agent type and current operation
    """

    def __init__(self, agent_type: str, context_loader: ContextLoader):
        self.agent_type = agent_type
        self.loader = context_loader
        self.context_cache = {}

    def get_relevant_schemas(self) -> Dict[str, Any]:
        """Get schemas relevant to this agent type"""
        all_schemas = self.loader.load_schemas()

        # SQL agents need all table schemas
        if "sql" in self.agent_type.lower():
            return all_schemas

        # Visualization agents need schema metadata for chart recommendations
        if "visualization" in self.agent_type.lower():
            return {name: schema.get("metadata", {}) for name, schema in all_schemas.items()}

        return all_schemas

    def get_relevant_examples(self) -> Dict[str, Any]:
        """Get examples relevant to this agent type"""
        if "cost" in self.agent_type.lower():
            return self.loader.get_example_queries(table="cost_analysis")
        elif "budget" in self.agent_type.lower():
            return self.loader.get_example_queries(table="budget")
        elif "combined" in self.agent_type.lower():
            return self.loader.get_example_queries(query_type="combined")

        return self.loader.load_examples()

    def get_agent_prompts(self) -> Dict[str, Any]:
        """Get prompts for this agent type"""
        try:
            return self.loader.get_prompt_template(self.agent_type)
        except KeyError:
            # Return generic prompts if agent-specific not found
            prompts = self.loader.load_prompts()
            return prompts.get("sql_agent_prompts", {}) if prompts else {}

    def build_context_for_request(self, user_request: str, **kwargs) -> Dict[str, Any]:
        """Build complete context for processing a user request"""
        context = {
            "agent_type": self.agent_type,
            "user_request": user_request,
            "schemas": self.get_relevant_schemas(),
            "examples": self.get_relevant_examples(),
            "prompts": self.get_agent_prompts(),
            "request_metadata": kwargs
        }

        # Add any additional context based on agent type
        if "sql" in self.agent_type.lower():
            context["common_patterns"] = self._get_sql_patterns()
        elif "visualization" in self.agent_type.lower():
            context["chart_types"] = self._get_chart_types()

        return context

    def _get_sql_patterns(self) -> Dict[str, List[str]]:
        """Get common SQL patterns from examples"""
        examples = self.get_relevant_examples()
        patterns = {}

        for example_set in examples.values():
            common_patterns = example_set.get("common_patterns", {})
            for pattern_type, pattern_list in common_patterns.items():
                if pattern_type not in patterns:
                    patterns[pattern_type] = []
                patterns[pattern_type].extend(pattern_list)

        return patterns

    def _get_chart_types(self) -> List[str]:
        """Get available chart types for visualization"""
        viz_prompts = self.get_agent_prompts()
        return viz_prompts.get("metadata", {}).get("supported_charts", [])

# Example usage and testing
def main():
    """Example usage of the context loader"""

    # Initialize context loader
    config = ContextConfig(
        project_id="my-analytics-project",
        dataset="agent_bq_dataset",
        current_date="2024-09-28"
    )

    loader = ContextLoader(config)

    # Load all context
    try:
        context = loader.load_all_context()
        print(f"Loaded context with {len(context['schemas'])} schemas, "
              f"{len(context['examples'])} example sets, "
              f"{len(context['prompts'])} prompt sets, "
              f"{len(context['pipelines'])} pipeline sets")

        # Validate context
        issues = loader.validate_context()
        if any(issues.values()):
            print("Context validation issues found:")
            for issue_type, issue_list in issues.items():
                if issue_list:
                    print(f"  {issue_type}: {issue_list}")
        else:
            print("Context validation passed")

        # Example: Get cost analysis schema
        cost_schema = loader.get_schema("cost_analysis")
        print(f"\nCost analysis table has {len(cost_schema['schema']['fields'])} fields")

        # Example: Get SQL agent context
        sql_agent = AgentContextManager("sql_agent", loader)
        request_context = sql_agent.build_context_for_request(
            "Show me the top 5 applications by cost",
            time_period="last_30_days"
        )
        print(f"\nSQL agent context includes {len(request_context['examples'])} example sets")

    except Exception as e:
        print(f"Error loading context: {e}")

if __name__ == "__main__":
    main()