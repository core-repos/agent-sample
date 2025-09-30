# Context System for Pipeline Step Agents

A comprehensive context management system for BigQuery analytics agents that provides schemas, query examples, prompt templates, and pipeline definitions.

## Overview

This context system enables agents to access structured information about:
- **Database schemas** - Table structures and constraints
- **Query examples** - SQL patterns and best practices
- **Prompt templates** - Agent-specific prompts and instructions
- **Pipeline definitions** - Workflow orchestration and step coordination

## Directory Structure

```
context/
├── schemas/              # Table schemas in YAML format
│   ├── cost_analysis.yaml
│   └── budget.yaml
├── examples/             # SQL query examples in JSON format
│   ├── cost_analysis_queries.json
│   ├── budget_queries.json
│   └── combined_queries.json
├── prompts/              # Agent prompt templates in YAML format
│   ├── sql_agent_prompts.yaml
│   └── visualization_prompts.yaml
├── pipelines/            # Pipeline step definitions in YAML format
│   └── analysis_pipeline.yaml
├── context_loader.py     # Python utility for loading context
└── README.md            # This documentation
```

## Schema Files

### cost_analysis.yaml
Defines the structure of the cost analysis table including:
- Field definitions with types and constraints
- Indexes and clustering information
- Sample data statistics
- Common query patterns
- Validation rules

### budget.yaml
Defines the budget tracking table including:
- Budget allocation and spending fields
- Computed fields for utilization metrics
- Business rules and approval workflows
- Variance calculation patterns

## Example Query Files

### cost_analysis_queries.json
Contains 40+ example queries organized by category:
- **Basic aggregations** - Totals, averages, counts
- **Time-based queries** - Trends, seasonal patterns
- **Application analysis** - Top applications, efficiency metrics
- **Cloud provider analysis** - Cost comparisons, utilization
- **Team analysis** - Cost allocation, efficiency
- **Advanced analytics** - Anomaly detection, correlations

### budget_queries.json
Contains 30+ budget-specific queries:
- **Budget overview** - Allocation summaries, status distribution
- **Utilization analysis** - Usage rates, efficiency metrics
- **Variance analysis** - Budget vs actual, overspend identification
- **Burn rate analysis** - Spending velocity, projections
- **Alert queries** - Risk identification, attention-required items

### combined_queries.json
Contains 20+ queries that join cost and budget data:
- **Cost vs budget comparisons** - Variance analysis
- **Performance metrics** - Efficiency ratios, ROI analysis
- **Forecasting** - Predictive analysis, scenario planning
- **Financial reporting** - Executive summaries, quarterly reviews

## Prompt Templates

### sql_agent_prompts.yaml
Specialized prompts for SQL generation agents:
- **Base SQL agent** - General BigQuery expertise
- **Cost analysis specialist** - Cost table focused
- **Budget analysis specialist** - Budget table focused
- **Combined analysis specialist** - Multi-table joins
- **Visualization advisor** - Chart recommendations

### visualization_prompts.yaml
Prompts for chart generation and visualization:
- **Chart type specialists** - 14 different chart types
- **Visualization decision engine** - Smart chart selection
- **Data preparation** - Format data for charts
- **Best practices** - Color schemes, accessibility

## Pipeline Definitions

### analysis_pipeline.yaml
Defines reusable analysis workflows:
- **Cost analysis pipeline** - End-to-end cost analysis
- **Budget analysis pipeline** - Budget tracking workflow
- **Variance analysis pipeline** - Cost vs budget comparison
- **Forecasting pipeline** - Predictive analysis workflow

Each pipeline includes:
- Step definitions and dependencies
- Input/output specifications
- Context file references
- Error handling and retry policies

## Usage

### Python Context Loader

```python
from context_loader import ContextLoader, AgentContextManager

# Initialize context loader
config = ContextConfig(
    project_id="my-project",
    dataset="agent_bq_dataset"
)
loader = ContextLoader(config)

# Load specific schema
cost_schema = loader.get_schema("cost_analysis")

# Get example queries for cost analysis
cost_examples = loader.get_example_queries(table="cost_analysis")

# Get prompts for SQL agent
sql_prompts = loader.get_prompt_template("sql_agent")

# Build context for agent request
agent = AgentContextManager("cost_analysis_specialist", loader)
context = agent.build_context_for_request(
    "Show top 10 applications by cost",
    time_period="last_30_days"
)
```

### Template Rendering

Templates support variable substitution:

```python
# Template with variables
template = "SELECT * FROM `{{ project_id }}.{{ dataset }}.{{ table }}`"

# Render with parameters
query = loader.render_template(
    template,
    project_id="my-project",
    dataset="agent_bq_dataset",
    table="cost_analysis"
)
```

## Agent Integration Patterns

### SQL Generation Agents

1. Load relevant table schemas
2. Get example queries for patterns
3. Apply agent-specific prompts
4. Generate optimized BigQuery SQL
5. Include visualization hints

### Visualization Agents

1. Analyze data characteristics
2. Get chart type recommendations
3. Apply visualization best practices
4. Generate chart configurations
5. Provide customization options

### Pipeline Orchestration

1. Load pipeline definition
2. Execute steps in sequence
3. Pass context between steps
4. Handle errors and retries
5. Generate comprehensive reports

## Best Practices

### Schema Design
- Include comprehensive field metadata
- Define validation rules and constraints
- Document business logic and calculations
- Provide sample data and statistics

### Query Examples
- Organize by analysis type and complexity
- Include performance optimization hints
- Provide visualization recommendations
- Document business use cases

### Prompt Templates
- Make templates agent-specific
- Include context loading instructions
- Provide error handling guidance
- Support parameter customization

### Pipeline Definitions
- Define clear step dependencies
- Include comprehensive error handling
- Support parameter customization
- Provide monitoring and logging

## Configuration

### Environment Variables

```bash
# BigQuery Configuration
export GCP_PROJECT_ID="your-project-id"
export BQ_DATASET="agent_bq_dataset"

# Context Configuration
export CONTEXT_ROOT="./context"
export CACHE_ENABLED="true"
```

### Context Loading Configuration

```python
config = ContextConfig(
    project_id=os.getenv("GCP_PROJECT_ID"),
    dataset=os.getenv("BQ_DATASET", "agent_bq_dataset"),
    current_date=datetime.now().strftime("%Y-%m-%d"),
    context_root=os.getenv("CONTEXT_ROOT", "./context")
)
```

## Validation and Testing

### Context Validation

```python
# Validate all context files
issues = loader.validate_context()
if any(issues.values()):
    print("Validation issues found:", issues)
```

### Testing Queries

```python
# Test query examples
examples = loader.get_example_queries(table="cost_analysis")
for category, queries in examples["query_examples"].items():
    for query_name, query_info in queries.items():
        sql = query_info["sql"]
        # Test SQL syntax and execution
```

## Extensibility

### Adding New Tables

1. Create schema YAML file in `schemas/`
2. Add example queries in `examples/`
3. Update prompt templates if needed
4. Add pipeline steps for new analysis types

### Adding New Chart Types

1. Add chart specialist prompt in `visualization_prompts.yaml`
2. Include configuration templates
3. Update decision engine recommendations
4. Add example use cases

### Adding New Pipelines

1. Define pipeline in `pipelines/analysis_pipeline.yaml`
2. Specify step dependencies and context files
3. Include error handling and monitoring
4. Document usage and customization options

## Performance Considerations

- **Lazy loading** - Context files loaded on demand
- **Caching** - Loaded context cached in memory
- **Selective loading** - Load only relevant context per agent
- **Template rendering** - Efficient variable substitution

## Security and Compliance

- **No hardcoded credentials** - Use environment variables
- **Data access patterns** - Follow least privilege principle
- **Query validation** - Validate SQL before execution
- **Audit logging** - Track context access and usage

## Troubleshooting

### Common Issues

1. **Missing context files** - Verify directory structure
2. **Invalid YAML/JSON** - Check file syntax
3. **Template rendering errors** - Verify variable names
4. **Schema mismatches** - Update schemas when tables change

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
loader = ContextLoader(config)
```

## Contributing

When adding new context files:

1. Follow existing naming conventions
2. Include comprehensive metadata
3. Add validation rules where appropriate
4. Document business logic and use cases
5. Test with context loader utility

## Version History

- **v1.0.0** (2024-09-28) - Initial comprehensive context system
  - Schema definitions for cost_analysis and budget tables
  - 90+ example queries across 3 categories
  - Agent-specific prompt templates
  - 4 complete analysis pipelines
  - Python context loader utility