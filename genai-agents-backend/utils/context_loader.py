import yaml
import json
import os
from pathlib import Path
from typing import Dict, Any, List

class ContextLoader:
    """Load context information for BigQuery schema and examples"""

    def __init__(self):
        self.context_dir = Path(__file__).parent.parent.parent / "context"

    def load_budget_schema(self) -> Dict[str, Any]:
        """Load budget table schema with field constraints"""
        schema_file = self.context_dir / "schemas" / "budget_analysis.yaml"
        if schema_file.exists():
            with open(schema_file, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def load_budget_examples(self) -> Dict[str, Any]:
        """Load budget query examples"""
        examples_file = self.context_dir / "examples" / "budget_queries.yaml"
        if examples_file.exists():
            with open(examples_file, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def load_budget_prompt_template(self) -> str:
        """Load budget-specific prompt template"""
        prompt_file = self.context_dir / "prompts" / "budget_prompt_template.yaml"
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                data = yaml.safe_load(f)
                return data.get('prompt_template', '')
        return ""

    def get_valid_budget_fields(self) -> List[str]:
        """Get list of valid field names for budget table"""
        schema = self.load_budget_schema()
        if 'schema' in schema:
            return [field['field_name'] for field in schema['schema']]
        return [
            'cto', 'tr_product_pillar_team', 'tr_subpillar_name',
            'tr_product_id', 'tr_product', 'fy_24_budget', 'fy_25_budget',
            'fy_26_budget', 'fy26_ytd_spend', 'fy26_projected_spend'
        ]

    def get_budget_field_descriptions(self) -> Dict[str, str]:
        """Get field descriptions for budget table"""
        schema = self.load_budget_schema()
        descriptions = {}
        if 'schema' in schema:
            for field in schema['schema']:
                descriptions[field['field_name']] = field['description']
        return descriptions

    def build_enhanced_prompt(self, base_question: str) -> str:
        """Build enhanced prompt with budget context"""
        budget_template = self.load_budget_prompt_template()
        if budget_template:
            return f"{budget_template}\n\nUser Question: {base_question}"
        return base_question

    def validate_budget_query(self, sql_query: str) -> tuple[bool, List[str]]:
        """Validate that SQL query only uses valid budget fields"""
        valid_fields = self.get_valid_budget_fields()
        forbidden_fields = ['budget_id', 'budget_name', 'id', 'name']

        errors = []

        # Check for forbidden fields
        for forbidden in forbidden_fields:
            if forbidden in sql_query.lower():
                errors.append(f"Forbidden field '{forbidden}' found in query")

        # Check if query references budget_analysis table
        if 'budget_analysis' in sql_query.lower():
            # Extract potential field references (basic check)
            import re
            field_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
            matches = re.findall(field_pattern, sql_query)

            for match in matches:
                if (match.lower() not in ['select', 'from', 'where', 'group', 'by', 'order', 'sum', 'count', 'avg', 'max', 'min', 'round', 'case', 'when', 'then', 'else', 'end', 'as', 'and', 'or', 'not', 'null', 'desc', 'asc', 'distinct', 'having', 'limit', 'offset'] and
                    match not in valid_fields and
                    not match.isdigit() and
                    match not in ['gac', 'prod', '471220', 'agent', 'bq', 'dataset', 'budget', 'analysis']):
                    if len(match) > 2:  # Ignore very short matches
                        errors.append(f"Potentially invalid field '{match}' - valid fields are: {', '.join(valid_fields)}")

        return len(errors) == 0, errors