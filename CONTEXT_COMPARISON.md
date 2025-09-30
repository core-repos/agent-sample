# Context Systems - Visual Comparison

## Side-by-Side Comparison

### `/context/` vs `/data-generator/scripts/context/`

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          TWO CONTEXT SYSTEMS                                    │
├─────────────────────────────────────┬───────────────────────────────────────────┤
│     /context/                       │  /data-generator/scripts/context/         │
│     (Runtime Agent Context)         │  (Development Documentation)              │
├─────────────────────────────────────┼───────────────────────────────────────────┤
│                                     │                                           │
│  PURPOSE                            │  PURPOSE                                  │
│  ├─ LangChain memory                │  ├─ Comprehensive reference              │
│  ├─ Fast query generation           │  ├─ Data generation guidance             │
│  └─ Runtime performance             │  └─ Testing & development                │
│                                     │                                           │
│  SIZE: 262 lines                    │  SIZE: 1,539+ lines                      │
│                                     │                                           │
├─────────────────────────────────────┼───────────────────────────────────────────┤
│                                     │                                           │
│  STRUCTURE                          │  STRUCTURE                                │
│  context/                           │  data-generator/scripts/context/          │
│  ├── examples/                      │  ├── examples/                            │
│  │   ├── cost_queries.yaml (61L)   │  │   ├── cost_analysis_queries.json(353L)│
│  │   └── budget_queries.yaml (37L) │  │   ├── budget_queries.json (260L)      │
│  ├── prompts/                       │  │   └── combined_queries.json (221L)    │
│  │   └── budget_prompt... (37L)    │  ├── prompts/                             │
│  └── schemas/                       │  │   ├── sql_agent_prompts.yaml (24,994L)│
│      ├── cost_analysis.yaml (97L)  │  │   └── visualization_prompts.yaml(11K+L)│
│      └── budget_analysis.yaml(67L) │  ├── schemas/                             │
│                                     │  │   ├── cost_analysis.yaml (325L)       │
│                                     │  │   └── budget.yaml (380L)              │
│                                     │  ├── pipelines/                           │
│                                     │  │   └── analysis_pipeline.yaml (15K+L)  │
│                                     │  ├── context_loader.py                    │
│                                     │  └── README.md                            │
│                                     │                                           │
├─────────────────────────────────────┼───────────────────────────────────────────┤
│                                     │                                           │
│  QUERY EXAMPLES                     │  QUERY EXAMPLES                           │
│  ├─ 10 cost queries                 │  ├─ 40+ cost queries                     │
│  ├─ 5 budget queries                │  ├─ 30+ budget queries                   │
│  └─ Simple format                   │  ├─ 20+ combined queries                 │
│                                     │  └─ Rich metadata                         │
│                                     │                                           │
├─────────────────────────────────────┼───────────────────────────────────────────┤
│                                     │                                           │
│  EXAMPLE FORMAT                     │  EXAMPLE FORMAT                           │
│                                     │                                           │
│  YAML (Simple):                     │  JSON (Detailed):                         │
│  ```yaml                            │  ```json                                  │
│  - question: "Total cost?"          │  {                                        │
│    sql: "SELECT SUM(cost)..."       │    "total_cost_all_time": {              │
│    description: "Aggregation"       │      "description": "Calculate...",      │
│  ```                                │      "sql": "SELECT SUM...",             │
│                                     │      "expected_result_type": "scalar",   │
│  Hardcoded project IDs              │      "visualization_hint": "indicator",  │
│  Fast parsing                       │      "parameters": {},                   │
│  Minimal metadata                   │      "tags": ["aggregation", "kpi"],     │
│                                     │      "complexity": "basic"               │
│                                     │    }                                     │
│                                     │  }                                       │
│                                     │  Template variables                      │
│                                     │  Slow parsing (comprehensive)            │
│                                     │  Rich metadata for testing               │
│                                     │                                           │
├─────────────────────────────────────┼───────────────────────────────────────────┤
│                                     │                                           │
│  LOADED BY                          │  LOADED BY                                │
│  ├─ genai-agents-backend/           │  ├─ data-generator scripts                │
│  │   agents/bigquery/agent.py      │  ├─ Test suites                           │
│  └─ LangChain SQL agents            │  ├─ Development tools                     │
│                                     │  └─ Documentation generators              │
│                                     │                                           │
├─────────────────────────────────────┼───────────────────────────────────────────┤
│                                     │                                           │
│  UPDATE FREQUENCY                   │  UPDATE FREQUENCY                         │
│  Rarely - only critical changes     │  Frequently - during development          │
│                                     │                                           │
├─────────────────────────────────────┼───────────────────────────────────────────┤
│                                     │                                           │
│  TARGET AUDIENCE                    │  TARGET AUDIENCE                          │
│  AI Agents (Claude, GPT, Gemini)    │  Developers, Data Engineers               │
│                                     │                                           │
└─────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## Query Example Comparison

### Runtime Context (`/context/examples/cost_queries.yaml`)
```yaml
examples:
  - question: "What is the total cost?"
    sql: "SELECT SUM(cost) AS total_cost FROM `gac-prod-471220`.`agent_bq_dataset`.`cost_analysis`"
    description: "Simple aggregation of all costs"

  - question: "Show me cost by cloud provider"
    sql: "SELECT cloud, SUM(cost) AS total_cost, COUNT(*) AS record_count
          FROM `gac-prod-471220`.`agent_bq_dataset`.`cost_analysis`
          GROUP BY cloud ORDER BY total_cost DESC"
    description: "Cost breakdown by cloud provider (AWS, Azure, GCP)"
```

**Characteristics**:
- ✅ Fast to parse (YAML)
- ✅ Hardcoded project IDs (no template processing)
- ✅ Natural language questions
- ✅ Minimal metadata
- ✅ Optimized for agent memory

---

### Development Context (`/data-generator/scripts/context/examples/cost_analysis_queries.json`)
```json
{
  "metadata": {
    "table": "cost_analysis",
    "dataset": "agent_bq_dataset",
    "description": "SQL query examples for cost analysis operations",
    "version": "1.0.0",
    "query_categories": ["aggregations", "filters", "time_series"]
  },
  "query_examples": {
    "basic_aggregations": {
      "total_cost_all_time": {
        "description": "Calculate total cost across all time periods",
        "sql": "SELECT SUM(cost) as total_cost FROM `{{ project_id }}.{{ dataset }}.cost_analysis`",
        "expected_result_type": "scalar",
        "visualization_hint": "kpi_indicator",
        "parameters": {},
        "tags": ["aggregation", "total", "kpi"],
        "complexity": "basic",
        "estimated_execution_time": "< 1s",
        "validation_rules": ["cost_must_be_positive"],
        "sample_result": {
          "total_cost": 27506708.68
        }
      },
      "total_cost_by_cloud": {
        "description": "Total cost breakdown by cloud provider",
        "sql": "SELECT cloud, SUM(cost) as total_cost
                FROM `{{ project_id }}.{{ dataset }}.cost_analysis`
                GROUP BY cloud ORDER BY total_cost DESC",
        "expected_result_type": "grouped",
        "visualization_hint": "bar_chart",
        "parameters": {},
        "tags": ["aggregation", "grouping", "cloud_provider"],
        "complexity": "basic",
        "estimated_execution_time": "< 1s"
      }
    },
    "time_based_queries": {
      "daily_cost_trend_30_days": {
        "description": "Daily cost trend for the last 30 days",
        "sql": "SELECT date, SUM(cost) as daily_cost
                FROM `{{ project_id }}.{{ dataset }}.cost_analysis`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY date ORDER BY date",
        "expected_result_type": "time_series",
        "visualization_hint": "line_chart",
        "parameters": {
          "days": 30
        },
        "tags": ["time_series", "trend", "daily"],
        "complexity": "intermediate"
      }
    }
  }
}
```

**Characteristics**:
- ✅ Template variables (`{{ project_id }}`, `{{ dataset }}`)
- ✅ Rich metadata (tags, complexity, execution time)
- ✅ Organized by category
- ✅ Sample results for validation
- ✅ Visualization hints
- ✅ Estimated execution times
- ✅ Validation rules
- ✅ Complete for testing

---

## Schema Comparison

### Runtime Schema (`/context/schemas/cost_analysis.yaml` - 97 lines)
```yaml
table_name: cost_analysis
dataset: agent_bq_dataset
project: gac-prod-471220
description: "Cost analysis table with organizational hierarchy"

hierarchy_explanation: |
  cto -> tr_product_pillar_team -> tr_subpillar_name ->
  tr_product_id -> apm_id -> application

schema:
  - field_name: date
    type: DATE
    description: "Date of the cost entry"

  - field_name: cost
    type: FLOAT
    description: "Daily cost in USD"

important_notes:
  - "Use tr_product_id for product identification"
  - "The hierarchy flows: cto -> ... -> application"

sample_queries:
  - "SELECT SUM(cost) FROM cost_analysis WHERE date >= '2024-01-01'"
```

**Focus**: Essential information for agent query generation

---

### Development Schema (`/data-generator/scripts/context/schemas/cost_analysis.yaml` - 325 lines)
```yaml
table_name: cost_analysis
dataset: agent_bq_dataset
project: "{{ project_id }}"
description: "Complete cost analysis schema with constraints and business rules"

metadata:
  version: "2.0.0"
  last_updated: "2024-09-29"
  maintainer: "Data Engineering Team"
  data_classification: "Confidential"

hierarchy:
  levels:
    - level: 1
      field: cto
      description: "Chief Technology Officer organization"
      cardinality: "low"
      example: "ENTERPRISE FINANCE TECH"

    - level: 2
      field: tr_product_pillar_team
      parent: cto
      description: "Product pillar team under CTO"
      cardinality: "medium"
      example: "Data Science Platform"

schema_definition:
  fields:
    - name: date
      type: DATE
      mode: NULLABLE
      description: "Date of the cost entry"
      constraints:
        - "NOT NULL in production"
        - "Must be <= CURRENT_DATE"
      validation_rules:
        - rule: "date_in_past"
          sql: "date <= CURRENT_DATE()"

    - name: cost
      type: FLOAT64
      mode: NULLABLE
      description: "Daily cost in USD"
      constraints:
        - "Must be >= 0"
        - "Precision: 2 decimal places"
      validation_rules:
        - rule: "cost_positive"
          sql: "cost >= 0"
        - rule: "cost_reasonable"
          sql: "cost < 1000000"

indexes:
  clustering:
    - date
    - cloud
    - tr_product_pillar_team

  partition:
    field: date
    type: DAY
    expiration_days: 730

statistics:
  row_count: 10800
  date_range:
    min: "2024-07-01"
    max: "2024-09-29"
  total_cost: 27506708.68

sample_data:
  - date: "2024-09-29"
    cto: "ENTERPRISE FINANCE TECH"
    cloud: "AWS"
    cost: 1250.50
```

**Focus**: Complete documentation for data generation, validation, testing

---

## Usage Matrix

| Task | Use `/context/` | Use `/data-generator/scripts/context/` |
|------|----------------|----------------------------------------|
| Agent query generation | ✅ Primary | ❌ Too slow |
| Testing query patterns | ⚠️ Limited | ✅ Comprehensive |
| Data generation | ❌ Not enough detail | ✅ Complete |
| Schema lookup | ✅ Fast reference | ✅ Complete docs |
| Adding new queries | ⚠️ Only if essential | ✅ All queries |
| Development | ⚠️ Basic info | ✅ Full reference |
| Production runtime | ✅ Optimized | ❌ Not used |
| Documentation | ⚠️ Basic | ✅ Complete |

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER QUESTION                               │
│                  "What is the total cost?"                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GRADIO FRONTEND                               │
│                  (gradio-chatbot/)                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                               │
│              (genai-agents-backend/)                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 BIGQUERY AGENT                                  │
│          (agents/bigquery/agent.py)                             │
│                                                                 │
│  LOADS: /context/                                               │
│  ├─ examples/cost_queries.yaml     ◄─── RUNTIME CONTEXT        │
│  ├─ schemas/cost_analysis.yaml     ◄─── FAST LOADING           │
│  └─ prompts/...                                                 │
│                                                                 │
│  Does NOT Load:                                                 │
│  ❌ /data-generator/scripts/context/  ◄─── TOO SLOW            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BIGQUERY DATABASE                             │
│           (gac-prod-471220.agent_bq_dataset)                    │
└─────────────────────────────────────────────────────────────────┘


MEANWHILE, FOR DEVELOPMENT:

┌─────────────────────────────────────────────────────────────────┐
│              DATA GENERATION SCRIPTS                            │
│         (data-generator/scripts/)                               │
│                                                                 │
│  LOADS: data-generator/scripts/context/                         │
│  ├─ examples/cost_analysis_queries.json  ◄─── 40+ QUERIES      │
│  ├─ examples/budget_queries.json         ◄─── 30+ QUERIES      │
│  ├─ examples/combined_queries.json       ◄─── 20+ QUERIES      │
│  ├─ schemas/cost_analysis.yaml          ◄─── COMPLETE SCHEMA   │
│  ├─ prompts/sql_agent_prompts.yaml      ◄─── 24K+ LINES        │
│  └─ pipelines/analysis_pipeline.yaml    ◄─── 15K+ LINES        │
│                                                                 │
│  Uses for:                                                      │
│  ✅ Generating test data                                        │
│  ✅ Validating queries                                          │
│  ✅ Building comprehensive test suites                          │
│  ✅ Documentation reference                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

1. **Two Different Purposes**:
   - `/context/` = Runtime speed and efficiency
   - `/data-generator/scripts/context/` = Development completeness

2. **Size Matters**:
   - Runtime context: 262 lines (fast)
   - Development context: 1,539+ lines (comprehensive)

3. **Format Differences**:
   - Runtime: YAML only (fast parsing)
   - Development: JSON + YAML (rich metadata)

4. **Query Examples**:
   - Runtime: 10-15 essential patterns
   - Development: 90+ comprehensive examples

5. **Update Strategy**:
   - Development context is source of truth
   - Runtime context gets critical updates only
   - Never load development context during agent runtime

6. **When to Use Each**:
   - Agent query generation → `/context/`
   - Testing and development → `/data-generator/scripts/context/`
   - Both needed, different purposes

---

For detailed architecture, see [ARCHITECTURE.md](./ARCHITECTURE.md)
For quick reference, see [CONTEXT_SYSTEMS_EXPLAINED.md](./CONTEXT_SYSTEMS_EXPLAINED.md)