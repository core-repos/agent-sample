# Context Systems - Quick Reference Guide

## Two Context Directories Explained

This project has **two separate `context/` directories** that serve different purposes. Understanding the difference is crucial for development and maintenance.

---

## 1. `/context/` (Project Root)

**Location**: `/Users/gurukallam/projects/ADK-Agents/context/`

### Purpose
Runtime agent context for LangChain SQL agents. This is the **lean, fast context** loaded during query processing.

### What's Inside
```
context/
├── examples/
│   ├── cost_queries.yaml      # 10 essential cost query examples
│   └── budget_queries.yaml    # Budget query examples
├── prompts/
│   └── budget_prompt_template.yaml
└── schemas/
    ├── cost_analysis.yaml     # 97 lines - complete hierarchy
    └── budget_analysis.yaml   # 67 lines
```

### Key Characteristics
- **Total Size**: ~262 lines
- **Format**: YAML only
- **Query Examples**: 10-15 essential patterns
- **Schema Detail**: Hierarchy explanation, field rules, common patterns
- **Loading**: Fast, minimal memory footprint
- **Updates**: Rarely, only for critical changes

### Example Content (cost_queries.yaml)
```yaml
examples:
  - question: "What is the total cost?"
    sql: "SELECT SUM(cost) AS total_cost FROM `gac-prod-471220`.`agent_bq_dataset`.`cost_analysis`"
    description: "Simple aggregation of all costs"

  - question: "Show me cost by cloud provider"
    sql: "SELECT cloud, SUM(cost) AS total_cost, COUNT(*) AS record_count FROM ..."
    description: "Cost breakdown by cloud provider (AWS, Azure, GCP)"
```

### When to Use
- Agent needs quick reference during query generation
- Runtime performance is critical
- Essential query patterns needed
- Schema hierarchy lookup

---

## 2. `/data-generator/scripts/context/` (Data Generator)

**Location**: `/Users/gurukallam/projects/ADK-Agents/data-generator/scripts/context/`

### Purpose
Comprehensive documentation and query library for **data generation, testing, and development**.

### What's Inside
```
data-generator/scripts/context/
├── examples/
│   ├── cost_analysis_queries.json  # 353 lines - 40+ queries
│   ├── budget_queries.json         # 260 lines - 30+ queries
│   └── combined_queries.json       # 221 lines - 20+ queries
├── prompts/
│   ├── sql_agent_prompts.yaml      # 24,994 lines - extensive prompts
│   └── visualization_prompts.yaml  # 11,499 lines - chart prompts
├── schemas/
│   ├── cost_analysis.yaml          # 325 lines - detailed schema
│   └── budget.yaml                 # 380 lines - full budget schema
├── pipelines/
│   └── analysis_pipeline.yaml      # 15,468 lines - workflow definitions
├── context_loader.py               # Python utility
└── README.md                       # Documentation
```

### Key Characteristics
- **Total Size**: ~1,539 lines (query examples alone)
- **Format**: JSON + YAML
- **Query Examples**: 90+ comprehensive queries with metadata
- **Schema Detail**: Complete field descriptions, constraints, business rules
- **Loading**: Development/testing only
- **Updates**: Frequently during development

### Example Content (cost_analysis_queries.json)
```json
{
  "total_cost_all_time": {
    "description": "Calculate total cost across all time periods",
    "sql": "SELECT SUM(cost) as total_cost FROM `{{ project_id }}.{{ dataset }}.cost_analysis`",
    "expected_result_type": "scalar",
    "visualization_hint": "kpi_indicator",
    "parameters": {},
    "tags": ["aggregation", "total", "kpi"],
    "complexity": "basic",
    "estimated_execution_time": "< 1s"
  }
}
```

### When to Use
- Developing new query patterns
- Testing comprehensive scenarios
- Generating sample data
- Understanding all available queries
- Building test suites
- Documentation reference

---

## Quick Comparison

| Feature | `/context/` | `/data-generator/scripts/context/` |
|---------|-------------|-------------------------------------|
| **Purpose** | Runtime agent memory | Development documentation |
| **Audience** | AI agents | Developers |
| **Size** | 262 lines | 1,539+ lines |
| **Format** | YAML | JSON + YAML |
| **Examples** | 10-15 queries | 90+ queries |
| **Details** | Concise | Comprehensive |
| **Metadata** | Minimal | Rich (tags, complexity, timing) |
| **Updates** | Rare | Frequent |
| **Performance** | Optimized for speed | Optimized for completeness |
| **Project IDs** | Hardcoded for speed | Template variables for flexibility |

---

## Organizational Hierarchy (Both Systems)

Both context systems document this hierarchy:

```
Level 1: cto (CTO Organization)
    └── Level 2: tr_product_pillar_team (Product Pillar Team)
        └── Level 3: tr_subpillar_name (Sub-Pillar)
            └── Level 4: tr_product_id (Product ID) + tr_product (Product Name)
                └── Level 5: apm_id (Application Portfolio Management ID)
                    └── Level 6: application (Individual Application)
                        └── Level 7: service_name (Service Instance)
```

**Example Hierarchy**:
```
ENTERPRISE FINANCE TECH (cto)
└── Data Science Platform (tr_product_pillar_team)
    └── ML Infrastructure (tr_subpillar_name)
        └── 700 / experimentation platform (tr_product_id / tr_product)
            └── APM-DS-001 (apm_id)
                └── experiment-api (application)
                    └── experiment-api-prod-1 (service_name)
```

---

## File Organization

### Runtime Context Files (`/context/`)
1. **schemas/cost_analysis.yaml**
   - 97 lines
   - Hierarchy explanation
   - Field definitions
   - Important notes
   - Sample queries (5 examples)

2. **examples/cost_queries.yaml**
   - 61 lines
   - 10 query examples
   - Field usage rules
   - Common patterns

3. **examples/budget_queries.yaml**
   - 37 lines
   - Budget-specific queries
   - Status calculations

### Development Context Files (`/data-generator/scripts/context/`)
1. **examples/cost_analysis_queries.json**
   - 353 lines
   - 40+ queries organized by category:
     - Basic aggregations (8 queries)
     - Time-based queries (10 queries)
     - Application analysis (8 queries)
     - Cloud provider analysis (6 queries)
     - Team analysis (5 queries)
     - Advanced analytics (5+ queries)

2. **examples/budget_queries.json**
   - 260 lines
   - 30+ budget queries:
     - Budget overview (5 queries)
     - Utilization analysis (8 queries)
     - Variance analysis (7 queries)
     - Burn rate analysis (5 queries)
     - Alert queries (5+ queries)

3. **examples/combined_queries.json**
   - 221 lines
   - 20+ multi-table queries:
     - Cost vs budget comparisons
     - Performance metrics
     - Forecasting
     - Financial reporting

4. **schemas/cost_analysis.yaml**
   - 325 lines
   - Complete field documentation
   - Data types and constraints
   - Clustering and indexing
   - Sample data statistics
   - Validation rules

5. **prompts/sql_agent_prompts.yaml**
   - 24,994 lines
   - Specialized SQL prompts:
     - Base SQL agent
     - Cost analysis specialist
     - Budget analysis specialist
     - Combined analysis specialist
     - Visualization advisor

---

## Usage Guidelines

### For AI Agents (Use `/context/`)
```python
# Backend loads runtime context
import yaml
with open('context/examples/cost_queries.yaml') as f:
    examples = yaml.safe_load(f)
```

### For Developers (Use `/data-generator/scripts/context/`)
```python
# Load comprehensive query library
import json
with open('data-generator/scripts/context/examples/cost_analysis_queries.json') as f:
    queries = json.load(f)
```

### For Data Generation (Use `/data-generator/scripts/context/`)
```python
# Use context loader utility
from data-generator.scripts.context.context_loader import load_all_context
context = load_all_context()
```

---

## Maintenance Workflow

### Schema Changes
1. **Update** `/data-generator/scripts/context/schemas/` first (source of truth)
2. **Test** with comprehensive query examples
3. **Sync** critical changes to `/context/schemas/` for runtime
4. **Verify** agents still generate correct queries

### New Query Patterns
1. **Add** to `/data-generator/scripts/context/examples/` with full metadata
2. **Test** thoroughly with data generation
3. **Promote** essential patterns to `/context/examples/` for runtime
4. **Document** in query category READMEs

### Performance Optimization
1. **Profile** runtime context loading time
2. **Keep** `/context/` files under 300 lines total
3. **Use** `/data-generator/scripts/context/` for exhaustive examples
4. **Optimize** YAML structure for fast parsing

---

## Common Pitfalls

❌ **DON'T**:
- Load `/data-generator/scripts/context/` during agent runtime (too slow)
- Add 100s of examples to `/context/` (defeats performance purpose)
- Duplicate maintenance across both systems
- Use template variables in `/context/` (agents need concrete values)

✅ **DO**:
- Keep `/context/` minimal and fast
- Use `/data-generator/scripts/context/` as comprehensive reference
- Update schemas in data-generator first, sync to runtime second
- Add metadata to data-generator examples for testing
- Document query patterns in both places appropriately

---

## Quick Decision Tree

**Question**: Which context directory should I update?

```
Are you adding a new query example?
├─ YES → Is it essential for agent runtime?
│   ├─ YES → Add to `/context/examples/` (keep it concise)
│   └─ NO → Add to `/data-generator/scripts/context/examples/` (full metadata)
└─ NO → Are you changing the schema?
    ├─ YES → Update both (data-generator first, then runtime)
    └─ NO → Are you adding documentation?
        ├─ For developers → `/data-generator/scripts/context/`
        └─ For agents → `/context/`
```

---

## Summary

- **`/context/`** = Fast, lean runtime context for AI agents
- **`/data-generator/scripts/context/`** = Rich, comprehensive documentation for development

Both are essential, but serve different purposes. Keep them in sync for schema changes, but optimize each for its specific use case.

For detailed architecture information, see [ARCHITECTURE.md](./ARCHITECTURE.md).