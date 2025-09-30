# BigQuery Analytics AI Agent - Architecture Documentation

## Context Systems Overview

The project contains **two distinct context systems** with different purposes:

### 1. Runtime Context (`/context/`)
**Purpose**: Agent runtime memory and LangChain conversation context

```
context/
├── examples/              # Simple query examples for agent reference
│   ├── cost_queries.yaml       # 10 basic cost queries
│   └── budget_queries.yaml     # Budget query examples
├── prompts/               # Agent prompt templates
│   └── budget_prompt_template.yaml
└── schemas/              # Concise schema definitions
    ├── cost_analysis.yaml      # Cost table schema with hierarchy
    └── budget_analysis.yaml    # Budget table schema
```

**Characteristics**:
- **Format**: YAML (lightweight, runtime-optimized)
- **Size**: ~262 lines (concise)
- **Content**: Essential information for agent query processing
- **Usage**: Loaded by LangChain agents during conversation
- **Focus**: Fast access, minimal overhead

**Key Files**:
- `cost_analysis.yaml`: Complete organizational hierarchy (cto → tr_product_pillar_team → tr_subpillar_name → tr_product_id → apm_id → application)
- `cost_queries.yaml`: 10 example queries covering common patterns
- Field usage rules and common SQL patterns

---

### 2. Data Generator Context (`/data-generator/scripts/context/`)
**Purpose**: Comprehensive documentation and test data generation

```
data-generator/scripts/context/
├── examples/              # Exhaustive query library
│   ├── cost_analysis_queries.json    # 40+ cost queries with metadata
│   ├── budget_queries.json           # 30+ budget queries
│   └── combined_queries.json         # 20+ multi-table queries
├── prompts/               # Detailed prompt templates
│   ├── sql_agent_prompts.yaml        # SQL generation prompts
│   └── visualization_prompts.yaml    # Chart generation prompts
├── schemas/              # Complete schema documentation
│   ├── cost_analysis.yaml            # Full schema with constraints
│   └── budget.yaml                   # Budget schema with business rules
├── pipelines/            # Workflow definitions
│   └── analysis_pipeline.yaml        # Analysis workflows
├── context_loader.py     # Python utility for loading context
└── README.md            # Context system documentation
```

**Characteristics**:
- **Format**: JSON + YAML (detailed, structured)
- **Size**: ~1,539 lines (comprehensive)
- **Content**: Complete reference documentation
- **Usage**: Development, testing, data generation
- **Focus**: Completeness, examples, best practices

**Key Features**:
- **Query Categories**: Basic aggregations, time-based, comparative analysis, advanced analytics
- **Metadata**: Each query includes description, expected result type, visualization hints, tags
- **Template Variables**: `{{ project_id }}`, `{{ dataset }}` for flexibility
- **Business Rules**: Validation rules, approval workflows, variance calculations

---

## Comparison Table

| Aspect | `/context/` | `/data-generator/scripts/context/` |
|--------|-------------|-------------------------------------|
| **Purpose** | Runtime agent context | Development documentation |
| **Format** | YAML | JSON + YAML |
| **Size** | 262 lines | 1,539 lines |
| **Examples** | 10-15 queries | 90+ queries |
| **Detail Level** | Concise | Comprehensive |
| **Loaded By** | LangChain agents | Data generators, developers |
| **Update Frequency** | Rarely | Often during development |
| **Target Audience** | AI agents | Developers, data engineers |

---

## Directory Structure With Context Systems

```
ADK-Agents/
├── context/                      # Runtime agent context
│   ├── examples/
│   ├── prompts/
│   └── schemas/
│
├── data-generator/               # Data generation & testing
│   ├── data/                     # Generated datasets
│   ├── schema/                   # BigQuery schema JSONs
│   ├── queries/                  # Sample SQL queries
│   │   ├── cost_sample_queries.sql
│   │   └── budget_sample_queries.sql
│   └── scripts/
│       ├── context/              # Comprehensive documentation
│       │   ├── examples/         # 90+ query examples
│       │   ├── schemas/          # Full schema docs
│       │   ├── prompts/          # Prompt templates
│       │   └── pipelines/        # Workflow definitions
│       ├── setup_bigquery.py
│       └── load_data_to_bigquery.py
│
├── genai-agents-backend/         # Backend API
├── gradio-chatbot/               # Frontend UI
└── tests/                        # Test suite
```

---

## Schema Hierarchy Reference

Both context systems document this organizational hierarchy:

```
cto (CTO Organization)
└── tr_product_pillar_team (Product Pillar Team)
    └── tr_subpillar_name (Sub-Pillar)
        └── tr_product_id (Product ID)
            └── apm_id (Application Portfolio Management ID)
                └── application (Individual Application)
                    └── service_name (Service Instance)
```

**Example**:
```
ENTERPRISE FINANCE TECH (cto)
└── Data Science Platform (tr_product_pillar_team)
    └── ML Infrastructure (tr_subpillar_name)
        └── 700 (tr_product_id) / experimentation platform (tr_product)
            └── APM-DS-001 (apm_id)
                └── experiment-api (application)
                    └── experiment-api-prod-1 (service_name)
```

---

## Query Example Comparison

### Runtime Context (`/context/examples/cost_queries.yaml`)
```yaml
- question: "What is the total cost?"
  sql: "SELECT SUM(cost) AS total_cost FROM `gac-prod-471220`.`agent_bq_dataset`.`cost_analysis`"
  description: "Simple aggregation of all costs"
```

### Data Generator Context (`/data-generator/scripts/context/examples/cost_analysis_queries.json`)
```json
{
  "total_cost_all_time": {
    "description": "Calculate total cost across all time periods",
    "sql": "SELECT SUM(cost) as total_cost FROM `{{ project_id }}.{{ dataset }}.cost_analysis`",
    "expected_result_type": "scalar",
    "visualization_hint": "kpi_indicator",
    "parameters": {},
    "tags": ["aggregation", "total", "kpi"]
  }
}
```

**Key Differences**:
1. Runtime context uses hardcoded project/dataset for speed
2. Data generator uses template variables for flexibility
3. Data generator includes metadata for testing and validation
4. Runtime context focuses on natural language questions

---

## When to Update Each System

### Update `/context/` (Runtime) when:
- Adding new critical query patterns agents must know
- Changing schema structure (hierarchy, field names)
- Updating business rules that affect query generation
- Adding new prompt templates for agents

### Update `/data-generator/scripts/context/` when:
- Creating comprehensive query test suites
- Documenting advanced analytics patterns
- Adding new visualization examples
- Building data generation pipelines
- Creating developer documentation

---

## Best Practices

### For Runtime Context (`/context/`)
1. Keep files minimal and fast to parse
2. Use YAML for readability and compactness
3. Include only essential queries and patterns
4. Update when schema changes occur
5. Focus on agent performance

### For Data Generator Context (`/data-generator/scripts/context/`)
1. Document ALL query patterns comprehensively
2. Include metadata for automated testing
3. Use template variables for portability
4. Organize by complexity and use case
5. Add examples for every visualization type
6. Document business logic and validation rules

---

## Integration Points

### Backend Integration
```python
# genai-agents-backend/agents/bigquery/agent.py
# Loads runtime context for query generation
context_path = os.path.join(project_root, "context")
```

### Data Generator Integration
```python
# data-generator/scripts/context/context_loader.py
# Loads comprehensive context for data generation
context_path = os.path.join(script_dir, "context")
```

### Test Integration
```python
# tests/test_all_queries.py
# References both contexts for comprehensive testing
runtime_context = load_yaml("context/examples/cost_queries.yaml")
test_queries = load_json("data-generator/scripts/context/examples/cost_analysis_queries.json")
```

---

## Maintenance Guidelines

1. **Schema Changes**: Update BOTH context systems when schema changes
2. **New Features**: Add to data-generator context first, then runtime if essential
3. **Query Optimization**: Test in data-generator context, promote best queries to runtime
4. **Documentation**: Keep data-generator context as source of truth
5. **Performance**: Profile runtime context loading time regularly

---

## Summary

- **`/context/`** = **Lean, fast, runtime-optimized** agent memory
- **`/data-generator/scripts/context/`** = **Rich, detailed, comprehensive** documentation

Both are essential but serve different purposes in the system architecture.