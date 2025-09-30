# Identified Gaps in BigQuery Analytics AI Agent

## Critical Issues Found

### 1. **LINE CHART ACCUMULATION ISSUE** ⚠️ CRITICAL
**Problem**: When user asks "daily cost by application in line chart", system may be generating cumulative/running total queries instead of simple daily values.

**Root Cause**:
- Prompt doesn't explicitly instruct to avoid `SUM() OVER()` window functions for line charts
- Context templates show cumulative patterns that may confuse the LLM
- No clear distinction between "daily trend" (simple values) vs "cumulative trend" (running total)

**Impact**: Line charts show accumulating values instead of actual daily costs

---

### 2. **CONFUSION BETWEEN LINE vs AREA CHARTS**
**Problem**: System uses "area" for cumulative but prompt doesn't distinguish clearly.

**Root Cause**:
- Pattern detection: `line` = ["daily", "trend"] but also `area` = ["cumulative", "accumulated"]
- Prompt doesn't explain when to use LINE vs AREA
- Users asking for "daily cost" get wrong visualization type

**Impact**: Wrong chart type selected, cumulative when user wants simple daily

---

### 3. **NO ROLLING AVERAGE GUIDANCE**
**Problem**: Prompt doesn't guide when to use rolling averages vs simple daily values.

**Root Cause**:
- Context shows `AVG(SUM(cost)) OVER (...)` examples
- No clear rules: use rolling average only when explicitly requested
- LLM may add rolling averages unnecessarily

**Impact**: Overcomplicated queries for simple "daily cost" requests

---

### 4. **PER-APPLICATION BREAKDOWN NOT CLEAR**
**Problem**: Query "daily cost by per application" may not properly group by both date AND application.

**Root Cause**:
- Prompt doesn't show multi-series line chart patterns
- No example: `GROUP BY date, application ORDER BY date, application`
- LLM may aggregate across all applications instead of per-app lines

**Impact**: Single line instead of multiple lines per application

---

### 5. **MISSING MULTI-SERIES LINE CHART SUPPORT**
**Problem**: Frontend may not support multiple series in line charts properly.

**Root Cause**:
- `_extract_line_data()` expects single series: `{"dates": [], "values": []}`
- No support for: `{"dates": [], "series": [{"name": "App1", "values": []}, ...]}`
- Multi-app trends can't be visualized correctly

**Impact**: Can't show comparative trends across applications

---

### 6. **NO EXPLICIT NON-CUMULATIVE INSTRUCTIONS**
**Problem**: Prompt doesn't explicitly say "DO NOT use window functions for simple daily trends".

**Root Cause**:
- Prompt line 323 says "Include dates and values" but doesn't prohibit cumulative
- Context templates show advanced window functions
- No clear rule: use window functions ONLY when explicitly requested

**Impact**: LLM adds complexity unnecessarily

---

### 7. **VISUALIZATION TYPE DETECTION TOO BROAD**
**Problem**: Pattern matching catches too many keywords, wrong chart type selected.

**Root Cause**:
```python
"line": ["trend", "over time", "timeline", "progression", "historical", "daily", "monthly"]
```
- "daily" triggers line chart even if user wants bar chart of top apps by daily cost
- Keyword matching without context understanding

**Impact**: Wrong visualization selected, user gets unexpected chart type

---

### 8. **NO DATE RANGE DEFAULTS FOR TRENDS**
**Problem**: User asks "daily cost trend" without specifying date range, query may return all data or fail.

**Root Cause**:
- Prompt line 333: `DATE_SUB(CURRENT_DATE(), INTERVAL X DAY)` but no default X
- No guidance: default to last 30 days for daily trends
- May generate query without WHERE clause

**Impact**: Performance issues or empty results

---

### 9. **MISSING QUERY PATTERN EXAMPLES IN PROMPT**
**Problem**: Prompt doesn't show concrete SQL examples for common scenarios.

**Root Cause**:
- Lines 313-327 show format rules but not actual SQL patterns
- No example: "For daily cost by application: `SELECT date, application, SUM(cost) as daily_cost FROM ... GROUP BY date, application`"
- LLM must infer patterns instead of following examples

**Impact**: Inconsistent query generation, trial and error

---

### 10. **NO AGGREGATION LEVEL GUIDANCE**
**Problem**: User asks "daily cost" but doesn't specify if they want by app, by service, by cloud, etc.

**Root Cause**:
- Prompt doesn't handle ambiguous aggregation requests
- No rule: "If no grouping specified, aggregate across all dimensions"
- May group by wrong dimension or miss grouping

**Impact**: Wrong aggregation level, unexpected results

---

### 11. **CONTEXT TEMPLATES CONFLICT WITH SIMPLE QUERIES**
**Problem**: Advanced templates in `/context/templates/time_series.json` show window functions, LLM copies them.

**Root Cause**:
```json
"rolling_avg_with_daily": {
  "template": "... AVG(SUM(cost)) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) ..."
}
```
- LLM sees advanced patterns and applies to simple requests
- No hierarchy: simple first, advanced only if needed

**Impact**: Overcomplicated queries for basic requests

---

### 12. **NO TREND SMOOTHING GUIDANCE**
**Problem**: Prompt doesn't explain when to smooth trends vs show raw data.

**Root Cause**:
- No rule: "Use raw daily values by default, add smoothing only if user asks for 'smoothed', 'rolling average', 'moving average'"
- LLM may randomly add smoothing

**Impact**: Inconsistent output, sometimes smoothed sometimes not

---

### 13. **MISSING MULTIPLE METRICS SUPPORT**
**Problem**: User asks "daily cost and count by date" but visualization only supports single metric.

**Root Cause**:
- `_extract_line_data()` returns: `{"dates": [], "values": []}`
- No support for multiple y-axes or dual metrics
- Query may return both but only first metric visualized

**Impact**: Second metric ignored in visualization

---

### 14. **NO ZERO-VALUE HANDLING FOR SPARSE DATA**
**Problem**: Daily trend may have gaps for days with no data.

**Root Cause**:
- No guidance to fill missing dates with zeros
- No use of: `GENERATE_DATE_ARRAY()` for complete date range
- Line chart shows gaps or connects non-consecutive days

**Impact**: Misleading trend visualization

---

### 15. **PROMPT DOESN'T DISTINGUISH GRANULARITY LEVELS**
**Problem**: "daily", "weekly", "monthly" trends need different GROUP BY strategies.

**Root Cause**:
- Prompt line 323 treats all time series the same
- No examples showing:
  - Daily: `GROUP BY date`
  - Weekly: `GROUP BY DATE_TRUNC(date, WEEK)`
  - Monthly: `GROUP BY FORMAT_DATE('%Y-%m', date)`

**Impact**: Wrong granularity, may show daily when user wants monthly

---

## Priority Fixes

### Must Fix (Blocking Issues)
1. ✅ Line chart accumulation - add explicit non-cumulative instructions
2. ✅ Multi-series support - update data extraction for per-app trends
3. ✅ Clear LINE vs AREA distinction in prompt

### Should Fix (Important)
4. ✅ Add concrete SQL pattern examples to prompt
5. ✅ Add default date range guidance (30 days)
6. ✅ Improve visualization type detection logic

### Nice to Have (Enhancements)
7. ✅ Multiple metrics support
8. ✅ Zero-value handling for sparse data
9. ✅ Granularity level examples (daily/weekly/monthly)
10. ✅ Rolling average guidance

---

## Recommended Solutions

### Solution 1: Enhanced Prompt with Clear Rules
```python
CRITICAL QUERY GENERATION RULES:

For SIMPLE DAILY TRENDS (Line Charts):
- DO NOT use window functions (SUM() OVER, AVG() OVER, etc.)
- Use simple aggregation: SELECT date, SUM(cost) as daily_cost FROM ...
- GROUP BY date only (or date + category for multi-series)
- ORDER BY date ASC
- Default to last 30 days if no range specified

For CUMULATIVE TRENDS (Area Charts):
- ONLY use when user explicitly says "cumulative", "running total", "accumulated"
- Use window function: SUM(SUM(cost)) OVER (ORDER BY date) as cumulative_cost

For PER-APPLICATION TRENDS (Multi-Series Line Chart):
- GROUP BY date, application
- ORDER BY date, application
- Response format: Include both date and application in results

For ROLLING AVERAGES:
- ONLY add when user explicitly requests "rolling average", "moving average", "smoothed"
- Example: AVG(SUM(cost)) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
```

### Solution 2: Update Visualization Data Extraction
Add support for multi-series line charts:
```python
def _extract_line_data_multi_series(self, answer: str) -> Dict[str, Any]:
    """Extract multi-series line chart data"""
    # Pattern: "App1 - 2024-01-01: $123, 2024-01-02: $456"
    # Or table format with columns: Date | App1 | App2 | App3
    ...
```

### Solution 3: Improve Pattern Detection
Add context-aware pattern matching:
```python
def _detect_line_vs_area(self, question: str) -> str:
    """Distinguish between simple trend and cumulative"""
    if any(word in question.lower() for word in ["cumulative", "running total", "accumulated"]):
        return "area"
    elif any(word in question.lower() for word in ["daily", "trend", "over time"]):
        return "line"
    return "line"  # default to simple line
```

---

## Testing Checklist

After fixes, test these queries:
- ✅ "Show daily cost trend for last 30 days" → Simple line chart, no accumulation
- ✅ "Daily cost by application" → Multi-series line chart, one line per app
- ✅ "Cumulative cost over time" → Area chart with running total
- ✅ "Daily cost with 7-day rolling average" → Line chart with smoothing
- ✅ "Monthly cost trend" → Line chart with monthly granularity
- ✅ "Cost trend by cloud provider" → Multi-series, one line per cloud