# Pipeline Step Agents System

A context-aware pipeline system for SQL generation that uses YAML/JSON context files to improve query accuracy and reduce reliance on hard-coded logic.

## Overview

The pipeline step agents system provides:

- **Dynamic Context Loading**: Load table schemas, query templates, and examples from files
- **Template-Based SQL Generation**: Use Jinja2 templates for consistent SQL patterns
- **Multi-Step Processing**: Chain processing steps with error handling and retries
- **Budget Integration**: Automatically integrate budget data when needed
- **Caching & Performance**: Intelligent caching at multiple levels

## Architecture

```
Natural Language Query
         ↓
  Context Loader (YAML/JSON)
         ↓
  SQL Agent (Templates + Context)
         ↓
  Step Executor (Pipeline Steps)
         ↓
  BigQuery Execution
         ↓
  Result Processing
```

## Components

### 1. Context Loader (`context_loader.py`)

Loads context from external files:

- **Schema Files** (`context/schemas/*.yaml`): Table definitions, columns, relationships
- **Template Files** (`context/templates/*.json`): Jinja2 SQL templates
- **Example Files** (`context/examples/*.json`): Query/SQL example pairs

### 2. SQL Agent (`sql_agent.py`)

Context-aware SQL generation:

- Query type detection (aggregation, time_series, etc.)
- Template-based generation using Jinja2
- Context-aware prompt building
- SQL validation and execution

### 3. Step Executor (`step_executor.py`)

Pipeline step management:

- **ContextLoadStep**: Load relevant context
- **SQLGenerationStep**: Generate SQL with context
- **SQLValidationStep**: Validate generated SQL
- **SQLExecutionStep**: Execute against database
- **BudgetIntegrationStep**: Add budget data if needed

### 4. Pipeline Agent (`pipeline_agent.py`)

Main orchestrator:

- Sequential and parallel step execution
- Caching and performance optimization
- Error handling and retries
- Execution history tracking

## Usage Examples

### Basic Query Processing

```python
from agents.pipeline import PipelineAgent, PipelineConfig

# Initialize agent
config = PipelineConfig(enable_caching=True)
agent = PipelineAgent(config=config)

# Process query
result = await agent.process_query(
    query="What is the total cost for application X?",
    query_type="aggregation"
)

print(result['sql_query'])
print(result['query_data'])
```

### Template-Based Generation

```python
# Generate SQL using template
result = await agent.sql_agent.generate_sql(
    query="Get cost breakdown",
    use_template="cost_by_dimension",
    template_params={
        "group_columns": "application, environment",
        "cost_column": "cost",
        "table_name": "cost_analysis",
        "limit": 10
    }
)
```

### Custom Pipeline

```python
from agents.pipeline.step_executor import StepConfig, StepType

# Define custom steps
custom_steps = [
    StepConfig(
        step_type=StepType.CONTEXT_LOAD,
        name="load_context",
        timeout=10
    ),
    StepConfig(
        step_type=StepType.SQL_GENERATION,
        name="generate_sql",
        timeout=30
    ),
    StepConfig(
        step_type=StepType.BUDGET_INTEGRATION,
        name="add_budget",
        enabled=True
    )
]

result = await agent.process_query(
    query="Show budget variance by application",
    custom_pipeline=custom_steps
)
```

## Context File Examples

### Schema File (`context/schemas/agent_bq_dataset.yaml`)

```yaml
tables:
  cost_analysis:
    description: "Daily cost records"
    columns:
      - name: date
        type: DATE
        description: "Record date"
      - name: application
        type: STRING
        description: "Application name"
      - name: cost
        type: FLOAT64
        description: "Daily cost in USD"
    sample_queries:
      - "SELECT SUM(cost) FROM cost_analysis"
      - "SELECT application, SUM(cost) FROM cost_analysis GROUP BY application"
```

### Template File (`context/templates/aggregation.json`)

```json
{
  "templates": {
    "total_cost": {
      "description": "Calculate total cost with filters",
      "template": "SELECT SUM({{ cost_column }}) as total_cost FROM {{ table_name }} {% if date_filter %}WHERE date >= '{{ date_filter }}'{% endif %}",
      "parameters": ["cost_column", "table_name", "date_filter"],
      "example": "SELECT SUM(cost) as total_cost FROM cost_analysis WHERE date >= '2024-01-01'"
    }
  }
}
```

### Example File (`context/examples/aggregation.json`)

```json
{
  "examples": [
    {
      "query": "What is the total cost?",
      "sql": "SELECT SUM(cost) as total_cost FROM cost_analysis",
      "explanation": "Simple aggregation to get total cost",
      "result_type": "single_value"
    }
  ]
}
```

## API Endpoints

The system provides REST API endpoints at `/api/context-pipeline/`:

- `POST /query` - Process natural language query
- `POST /template` - Use specific template
- `POST /custom` - Custom pipeline configuration
- `GET /templates` - Available templates
- `GET /schemas` - Schema information
- `GET /query-types` - Supported query types
- `GET /history` - Execution history
- `GET /cache/stats` - Cache statistics

## Configuration

### Pipeline Config

```python
config = PipelineConfig(
    context_config=ContextConfig(
        schema_dir="context/schemas",
        templates_dir="context/templates",
        examples_dir="context/examples",
        cache_enabled=True,
        cache_ttl=3600
    ),
    pipeline_timeout=300,
    max_retries=2,
    enable_budget_integration=False,
    enable_parallel_execution=False,
    enable_caching=True
)
```

### Context Config

```python
context_config = ContextConfig(
    schema_dir="custom/schemas",
    templates_dir="custom/templates",
    examples_dir="custom/examples",
    cache_enabled=True,
    cache_ttl=1800  # 30 minutes
)
```

## Query Type Detection

The system automatically detects query types based on keywords:

- **aggregation**: sum, count, total, average
- **time_series**: trend, daily, monthly, over time
- **comparison**: compare, vs, versus, difference
- **ranking**: top, bottom, highest, lowest
- **filtering**: where, filter, specific, only
- **analytical**: correlation, analysis, pattern

## Budget Integration

Automatic budget integration when:

- Query contains budget-related keywords
- `enable_budget_integration=True` in config
- BudgetIntegrationStep is enabled

Budget integration adds:
- Budget amounts from budget_table
- Variance calculations (actual vs budget)
- Percentage variance metrics

## Performance Features

### Caching
- **Context Cache**: Loaded schemas/templates (TTL configurable)
- **Pipeline Cache**: Complete query results (TTL configurable)
- **LRU Eviction**: Memory-efficient cache management

### Parallel Execution
- Independent steps run in parallel
- Dependency graph analysis
- Automatic step ordering

### Error Handling
- Exponential backoff retries
- Step-level timeout handling
- Graceful degradation

## Integration with Existing System

The pipeline agents extend the existing BigQuery agent system:

1. **Backward Compatibility**: Existing APIs continue to work
2. **Gradual Migration**: New features can be adopted incrementally
3. **Shared Resources**: Uses existing database connections and LLM providers
4. **Monitoring**: Integrates with existing logging and metrics

## Best Practices

### Context Files
- Keep schemas synchronized with actual database
- Use descriptive template names and parameters
- Provide multiple examples per query type
- Version control context files

### Templates
- Use parameterized templates for flexibility
- Include data type conversions
- Add performance optimizations (indexes, limits)
- Document template usage and parameters

### Pipeline Design
- Start with default pipeline configuration
- Add custom steps only when needed
- Monitor execution times and optimize bottlenecks
- Use caching for frequently accessed data

### Error Handling
- Set appropriate timeouts for each step
- Configure retry counts based on step criticality
- Monitor and alert on pipeline failures
- Implement circuit breaker patterns for external services

## Troubleshooting

### Common Issues

1. **Context Not Loading**
   - Check file paths and permissions
   - Verify YAML/JSON syntax
   - Enable debug logging

2. **Template Errors**
   - Validate Jinja2 syntax
   - Check parameter names match
   - Test templates in isolation

3. **SQL Generation Failures**
   - Review context prompt construction
   - Check LLM provider connectivity
   - Validate schema information

4. **Performance Issues**
   - Enable appropriate caching
   - Optimize template complexity
   - Monitor step execution times

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger('agents.pipeline').setLevel(logging.DEBUG)
```

### Health Checks

Monitor system health:

```bash
curl http://localhost:8010/api/context-pipeline/health
```

## Future Enhancements

- **Schema Auto-Discovery**: Automatically detect and update schemas
- **Template Learning**: Generate templates from successful queries
- **Cost Optimization**: Query cost estimation and optimization
- **Multi-Database Support**: Support for multiple data sources
- **Real-time Updates**: Live schema and data updates