# Budget Analysis Setup and Integration

This document provides complete setup instructions for the budget analysis system integration with ADK-Agents.

## Overview

The budget analysis system adds quarterly budget tracking and variance analysis to the existing cost analytics platform. It enables:

- **Budget vs Actual Analysis**: Compare planned spending with actual costs
- **Budget Status Tracking**: Monitor departments that are over budget, warning, or on track
- **Forecast Analysis**: Project end-of-quarter spending based on current trends
- **Category Analysis**: Track budget performance by department categories

## Quick Setup

### 1. Install Dependencies

```bash
cd genai-agents-backend
pip install python-dateutil==2.8.2
```

### 2. Run Budget Setup Script

```bash
cd data-generator/scripts
python setup_bigquery.py
```

This will:
- Create the `budget_analysis` table alongside `cost_analysis`
- Generate realistic budget data for 8 quarters (6 past + current + 1 future)
- Calculate budget utilization and status based on actual costs
- Verify data integrity with sample queries

### 3. Test Budget Queries

After setup, try these sample queries in the application:

**Budget Status**:
- "Which departments are over budget?"
- "Show current quarter budget utilization"
- "Which teams have budget warnings?"

**Budget Analysis**:
- "Compare allocated vs spent budget by department"
- "What's the budget vs actual spending comparison?"
- "Show budget trends over the last 4 quarters"

**Budget Forecasting**:
- "What's the forecast vs budget for this quarter?"
- "Which departments are projected to exceed budget?"

## Detailed Schema

### budget_analysis Table Structure

| Field | Type | Description |
|-------|------|-------------|
| `budget_id` | STRING | Unique ID (DEPT-YYYY-QN format) |
| `department` | STRING | Department name (matches cost_analysis.tr_product_pillar_team) |
| `period_start` | DATE | Quarter start date |
| `period_end` | DATE | Quarter end date |
| `allocated_budget` | FLOAT | Planned budget amount (USD) |
| `spent_budget` | FLOAT | Actual spending (USD) |
| `remaining_budget` | FLOAT | Budget remaining (USD) |
| `utilization_percentage` | FLOAT | Spent/allocated * 100 |
| `status` | STRING | ACTIVE, WARNING, EXCEEDED, COMPLETED |
| `budget_category` | STRING | INFRASTRUCTURE, DEVELOPMENT, DATA_ANALYTICS, OPERATIONS |
| `forecast_end_spend` | FLOAT | Projected quarter-end spending |
| `created_date` | DATE | Budget creation date |
| `last_updated` | TIMESTAMP | Last calculation update |

### Data Relationships

```
cost_analysis.tr_product_pillar_team = budget_analysis.department
```

The system automatically calculates `spent_budget` by aggregating costs from `cost_analysis` for each department and quarter period.

## Generated Data Characteristics

### Realistic Budget Scenarios

The setup script generates realistic business scenarios:

1. **Over-Budget Departments**: Some teams exceed their allocated budget (status: EXCEEDED)
2. **Warning Departments**: Teams approaching budget limits (status: WARNING, 80%+ utilization)
3. **Efficient Departments**: Teams operating within budget (status: ACTIVE)
4. **Seasonal Patterns**: Budget utilization varies by quarter and department type

### Department Categories

- **INFRASTRUCTURE**: Platform, DevOps, Infrastructure teams
- **DEVELOPMENT**: Frontend, Backend teams
- **DATA_ANALYTICS**: Data, ML teams
- **OPERATIONS**: Security and other operational teams

### Quarter Coverage

- **Historical Data**: 6 completed quarters with realistic utilization patterns
- **Current Quarter**: Active period with partial spending and forecasts
- **Future Quarter**: Planned budgets with zero spending

## Sample Queries and Expected Results

### 1. Budget Status Overview

**Query**: "Show current quarter budget status"

**Expected Results**:
```
Department    | Allocated  | Spent     | Utilization | Status
Platform      | $125,000   | $98,500   | 78.8%      | ACTIVE
Data          | $85,000    | $89,250   | 105.0%     | EXCEEDED
Security      | $45,000    | $38,100   | 84.7%      | WARNING
```

### 2. Budget Variance Analysis

**Query**: "Which departments have the highest budget variance?"

**Expected Results**:
```
Department    | Budget Variance | Status
Data          | +$4,250        | EXCEEDED
ML            | +$2,100        | EXCEEDED
Platform      | -$26,500       | ACTIVE
```

### 3. Budget Forecasting

**Query**: "What's the budget forecast for this quarter?"

**Expected Results**:
```
Department    | Allocated  | Forecast   | Variance   | Forecast Status
Data          | $85,000    | $92,000    | +$7,000   | OVER_FORECAST
Platform      | $125,000   | $118,000   | -$7,000   | ON_TRACK
Security      | $45,000    | $42,000    | -$3,000   | UNDER_FORECAST
```

## Integration with Existing System

### Backend Changes

The budget system integrates seamlessly with existing components:

1. **BigQuery Agent**: Enhanced to understand budget table relationships
2. **SQL Toolkit**: Recognizes budget-specific query patterns
3. **Visualization**: Supports budget-specific chart types (gauge, waterfall)

### Frontend Enhancements

New visualization types for budget analysis:

1. **Gauge Charts**: Budget utilization percentages
2. **Waterfall Charts**: Budget variance analysis
3. **KPI Indicators**: Total allocated, spent, remaining amounts
4. **Status-Based Color Coding**: Visual indicators for budget health

### New Quick Insights

Budget-related quick query buttons:
- 💰 Budget Status
- 📊 Budget Utilization
- ⚠️ Budget Warnings
- 📈 Budget Trends
- 🎯 Budget Forecast

## Maintenance and Updates

### Daily Budget Updates

The system automatically updates budget calculations daily:

1. **Spent Budget**: Recalculated from latest cost_analysis data
2. **Utilization Percentage**: Updated based on new spending
3. **Status**: Automatically updated based on utilization thresholds
4. **Forecast**: Recalculated using 7-day rolling average burn rate

### Status Calculation Logic

```sql
CASE
    WHEN period_end < CURRENT_DATE() THEN
        CASE WHEN utilization_percentage >= 100 THEN 'EXCEEDED'
             ELSE 'COMPLETED' END
    WHEN utilization_percentage >= 100 THEN 'EXCEEDED'
    WHEN utilization_percentage >= 80 THEN 'WARNING'
    ELSE 'ACTIVE'
END
```

## Troubleshooting

### Common Issues

1. **"Budget table not found"**
   - Solution: Run `python setup_bigquery.py` to create the budget table

2. **"No budget data for current quarter"**
   - Solution: The setup script generates data including current quarter, check date ranges

3. **"Budget calculations don't match costs"**
   - Solution: Budget spent amounts are calculated from cost_analysis aggregations, verify data consistency

### Data Validation

Run these queries to validate budget data integrity:

```sql
-- Check budget calculation accuracy
SELECT
    department,
    allocated_budget,
    spent_budget,
    utilization_percentage,
    ROUND((spent_budget / allocated_budget) * 100, 2) as calculated_utilization
FROM budget_analysis
WHERE ABS(utilization_percentage - (spent_budget / allocated_budget * 100)) > 0.1;

-- Verify department relationships
SELECT DISTINCT department
FROM budget_analysis
WHERE department NOT IN (
    SELECT DISTINCT tr_product_pillar_team
    FROM cost_analysis
    WHERE tr_product_pillar_team IS NOT NULL
);
```

## Advanced Features

### Budget Categories Analysis

Query budget performance by category:

```sql
SELECT
    budget_category,
    COUNT(*) as dept_count,
    SUM(allocated_budget) as total_allocated,
    SUM(spent_budget) as total_spent,
    AVG(utilization_percentage) as avg_utilization
FROM budget_analysis
WHERE period_start <= CURRENT_DATE() AND period_end >= CURRENT_DATE()
GROUP BY budget_category;
```

### Multi-Quarter Trending

Analyze budget trends across quarters:

```sql
SELECT
    department,
    period_start,
    utilization_percentage,
    LAG(utilization_percentage) OVER (
        PARTITION BY department ORDER BY period_start
    ) as prev_quarter_utilization
FROM budget_analysis
ORDER BY department, period_start;
```

## Performance Considerations

### Recommended Indexes

For optimal query performance:

```sql
-- Primary index
CREATE INDEX idx_budget_id ON budget_analysis(budget_id);

-- Department and period filtering
CREATE INDEX idx_dept_period ON budget_analysis(department, period_start, period_end);

-- Status filtering
CREATE INDEX idx_status ON budget_analysis(status, period_start);
```

### Query Optimization Tips

1. **Use period filters early**: Always filter by period_start/period_end in WHERE clauses
2. **Leverage current quarter**: Cache current quarter results for dashboard queries
3. **Limit historical data**: Focus on recent quarters for trending analysis

## Support and Documentation

### Additional Resources

- **Schema Documentation**: `/data-generator/scripts/context/schemas/budget_analysis_schema.md`
- **Query Examples**: `/data-generator/scripts/context/examples/budget_queries.md`
- **Integration Guide**: `/data-generator/scripts/context/pipelines/budget_integration.md`
- **Prompt Templates**: `/data-generator/scripts/context/prompts/budget_analysis_prompts.md`

### Getting Help

For issues or questions:

1. Check this README for common solutions
2. Review the detailed schema documentation
3. Validate data integrity using provided queries
4. Test with sample budget queries listed above