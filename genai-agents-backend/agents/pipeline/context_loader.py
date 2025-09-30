"""
Context loader for pipeline agents - loads YAML/JSON context files
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TableSchema:
    """Table schema definition"""
    name: str
    columns: List[Dict[str, Any]]
    description: str
    sample_queries: List[str] = None
    relationships: List[Dict[str, str]] = None

@dataclass
class QueryTemplate:
    """Query template definition"""
    name: str
    description: str
    template: str
    parameters: List[str]
    example: str
    category: str

@dataclass
class ContextConfig:
    """Configuration for context loading"""
    schema_dir: str = "context/schemas"
    templates_dir: str = "context/templates"
    examples_dir: str = "context/examples"
    cache_enabled: bool = True
    cache_ttl: int = 3600

class ContextLoader:
    """Loads and manages context files for pipeline agents"""

    def __init__(self, config: ContextConfig = None):
        self.config = config or ContextConfig()
        self._cache = {}
        self._cache_timestamps = {}

        # Set base directory (project root)
        self.base_dir = Path(__file__).parent.parent.parent.parent

        logger.info(f"Initialized ContextLoader with base directory: {self.base_dir}")

    def _get_file_path(self, relative_path: str) -> Path:
        """Get absolute file path from relative path"""
        return self.base_dir / relative_path

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if not self.config.cache_enabled:
            return False

        if cache_key not in self._cache_timestamps:
            return False

        cache_time = self._cache_timestamps[cache_key]
        now = datetime.now().timestamp()
        return (now - cache_time) < self.config.cache_ttl

    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file with error handling"""
        try:
            if not file_path.exists():
                logger.warning(f"YAML file not found: {file_path}")
                return {}

            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                logger.debug(f"Loaded YAML file: {file_path}")
                return content or {}

        except Exception as e:
            logger.error(f"Error loading YAML file {file_path}: {str(e)}")
            return {}

    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON file with error handling"""
        try:
            if not file_path.exists():
                logger.warning(f"JSON file not found: {file_path}")
                return {}

            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                logger.debug(f"Loaded JSON file: {file_path}")
                return content or {}

        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {str(e)}")
            return {}

    def load_table_schemas(self, schema_files: List[str] = None) -> Dict[str, TableSchema]:
        """Load table schemas from YAML files"""
        cache_key = f"schemas_{hash(str(schema_files))}"

        if self._is_cache_valid(cache_key):
            logger.debug("Returning cached table schemas")
            return self._cache[cache_key]

        schemas = {}
        schema_dir = self._get_file_path(self.config.schema_dir)

        if not schema_dir.exists():
            logger.warning(f"Schema directory not found: {schema_dir}")
            return schemas

        # If specific files requested, load only those
        if schema_files:
            files_to_load = [schema_dir / f for f in schema_files]
        else:
            # Load all YAML files in directory
            files_to_load = list(schema_dir.glob("*.yaml")) + list(schema_dir.glob("*.yml"))

        for file_path in files_to_load:
            if not file_path.exists():
                logger.warning(f"Schema file not found: {file_path}")
                continue

            schema_data = self._load_yaml_file(file_path)

            for table_name, table_def in schema_data.get('tables', {}).items():
                try:
                    schema = TableSchema(
                        name=table_name,
                        columns=table_def.get('columns', []),
                        description=table_def.get('description', ''),
                        sample_queries=table_def.get('sample_queries', []),
                        relationships=table_def.get('relationships', [])
                    )
                    schemas[table_name] = schema
                    logger.debug(f"Loaded schema for table: {table_name}")

                except Exception as e:
                    logger.error(f"Error parsing schema for table {table_name}: {str(e)}")

        # Cache results
        if self.config.cache_enabled:
            self._cache[cache_key] = schemas
            self._cache_timestamps[cache_key] = datetime.now().timestamp()

        logger.info(f"Loaded {len(schemas)} table schemas")
        return schemas

    def load_query_templates(self, template_files: List[str] = None) -> Dict[str, QueryTemplate]:
        """Load query templates from JSON files"""
        cache_key = f"templates_{hash(str(template_files))}"

        if self._is_cache_valid(cache_key):
            logger.debug("Returning cached query templates")
            return self._cache[cache_key]

        templates = {}
        templates_dir = self._get_file_path(self.config.templates_dir)

        if not templates_dir.exists():
            logger.warning(f"Templates directory not found: {templates_dir}")
            return templates

        # If specific files requested, load only those
        if template_files:
            files_to_load = [templates_dir / f for f in template_files]
        else:
            # Load all JSON files in directory
            files_to_load = list(templates_dir.glob("*.json"))

        for file_path in files_to_load:
            if not file_path.exists():
                logger.warning(f"Template file not found: {file_path}")
                continue

            template_data = self._load_json_file(file_path)

            for template_name, template_def in template_data.get('templates', {}).items():
                try:
                    template = QueryTemplate(
                        name=template_name,
                        description=template_def.get('description', ''),
                        template=template_def.get('template', ''),
                        parameters=template_def.get('parameters', []),
                        example=template_def.get('example', ''),
                        category=template_def.get('category', 'general')
                    )
                    templates[template_name] = template
                    logger.debug(f"Loaded template: {template_name}")

                except Exception as e:
                    logger.error(f"Error parsing template {template_name}: {str(e)}")

        # Cache results
        if self.config.cache_enabled:
            self._cache[cache_key] = templates
            self._cache_timestamps[cache_key] = datetime.now().timestamp()

        logger.info(f"Loaded {len(templates)} query templates")
        return templates

    def load_sql_examples(self, example_files: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Load SQL examples from JSON files"""
        cache_key = f"examples_{hash(str(example_files))}"

        if self._is_cache_valid(cache_key):
            logger.debug("Returning cached SQL examples")
            return self._cache[cache_key]

        examples = {}
        examples_dir = self._get_file_path(self.config.examples_dir)

        if not examples_dir.exists():
            logger.warning(f"Examples directory not found: {examples_dir}")
            return examples

        # If specific files requested, load only those
        if example_files:
            files_to_load = [examples_dir / f for f in example_files]
        else:
            # Load all JSON files in directory
            files_to_load = list(examples_dir.glob("*.json"))

        for file_path in files_to_load:
            if not file_path.exists():
                logger.warning(f"Example file not found: {file_path}")
                continue

            example_data = self._load_json_file(file_path)
            category = file_path.stem  # Use filename as category

            examples[category] = example_data.get('examples', [])
            logger.debug(f"Loaded {len(examples[category])} examples for category: {category}")

        # Cache results
        if self.config.cache_enabled:
            self._cache[cache_key] = examples
            self._cache_timestamps[cache_key] = datetime.now().timestamp()

        total_examples = sum(len(ex) for ex in examples.values())
        logger.info(f"Loaded {total_examples} SQL examples across {len(examples)} categories")
        return examples

    def get_context_for_query_type(self, query_type: str) -> Dict[str, Any]:
        """Get relevant context for a specific query type"""
        try:
            # Load all context data
            schemas = self.load_table_schemas()
            templates = self.load_query_templates()
            examples = self.load_sql_examples()

            # Filter templates by query type/category
            relevant_templates = {
                name: template for name, template in templates.items()
                if template.category == query_type or query_type.lower() in template.name.lower()
            }

            # Filter examples by query type
            relevant_examples = examples.get(query_type, [])

            context = {
                'schemas': schemas,
                'templates': relevant_templates,
                'examples': relevant_examples,
                'query_type': query_type,
                'metadata': {
                    'total_schemas': len(schemas),
                    'relevant_templates': len(relevant_templates),
                    'relevant_examples': len(relevant_examples),
                    'loaded_at': datetime.now().isoformat()
                }
            }

            logger.info(f"Generated context for query type '{query_type}': "
                       f"{len(schemas)} schemas, {len(relevant_templates)} templates, "
                       f"{len(relevant_examples)} examples")

            return context

        except Exception as e:
            logger.error(f"Error getting context for query type {query_type}: {str(e)}")
            return {}

    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Cleared context cache")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_enabled': self.config.cache_enabled,
            'cache_entries': len(self._cache),
            'cache_ttl': self.config.cache_ttl,
            'cache_keys': list(self._cache.keys())
        }