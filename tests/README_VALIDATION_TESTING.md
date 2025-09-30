# Validation System Testing

This directory contains tests for the validation agents system that validates SQL generation and graph data.

## Test Scripts

### 1. Basic Reliability Test - `test_basic_validation_10_times.py`
**Recommended for initial testing**

Tests 4 simple queries 10 times each to verify basic reliability:

```bash
python tests/test_basic_validation_10_times.py
```

**What it tests:**
- Each query runs 10 times with validation enabled
- Measures success rate, response time, and consistency
- Checks if validation produces reliable results
- Simple pass/fail reliability score

**Expected output:**
- Success rate should be >75% for good reliability
- Response times should be consistent
- Validation should succeed for most queries

### 2. Comprehensive Validation Test - `test_validation_10_times.py`
**For detailed validation analysis**

Tests 7 complex queries 10 times each with detailed validation analysis:

```bash
python tests/test_validation_10_times.py
```

**What it tests:**
- Full validation pipeline testing
- Detailed validation analysis
- Consistency metrics
- Error pattern analysis
- Performance statistics

### 3. Updated Legacy Test - `test_all_queries.py`
**Comparison testing**

Tests queries both with and without validation:

```bash
python tests/test_all_queries.py
```

**What it tests:**
- Compares validation vs non-validation results
- Shows validation improvements
- Tests all 7 example queries
- Validation performance reporting

## Test Queries Used

The tests use example queries representing different visualization types:

1. **Aggregation**: "What is the total cost?" (→ indicator)
2. **Ranking**: "Show me the top 5 applications by cost" (→ bar)
3. **Distribution**: "What's the cost breakdown by environment?" (→ pie)
4. **Trend**: "Display the daily cost trend for last 30 days" (→ line)
5. **Correlation**: "Show cost correlation between applications" (→ scatter)
6. **Matrix**: "Create a heatmap of costs by service" (→ heatmap)
7. **Pipeline**: "Generate funnel chart for budget allocation" (→ funnel)

## Running the Tests

### Prerequisites

1. **Backend Running**: Ensure the backend is running on localhost:8010
```bash
cd genai-agents-backend && python app.py
```

2. **Environment**: Make sure your .env file has required API keys
```env
ANTHROPIC_API_KEY=sk-ant-...
GCP_PROJECT_ID=your-project
BQ_DATASET=agent_bq_dataset
```

3. **Dependencies**: Install required packages
```bash
pip install -r requirements.txt
```

### Quick Start

For initial validation testing, run the basic test:

```bash
# Quick reliability check (4 queries × 10 runs = 40 requests)
python tests/test_basic_validation_10_times.py
```

Expected output:
```
🧪 VALIDATION SYSTEM - 10 TIMES RELIABILITY TEST
===============================================

[1/4] Query: What is the total cost?
🔄 Testing 10 times: What is the total cost?
  Run  1/10... ✅ 2.3s
  Run  2/10... ✅ 1.8s
  ...

📊 RELIABILITY TEST RESULTS
============================
🎯 Overall Success Rate: 87% (35/40)
⏱️  Total Test Duration: 95.2 seconds
🏆 RELIABILITY SCORE: 87.0/100
✅ GOOD - Validation system is reliable
```

### Understanding Results

#### Reliability Scores
- **90-100**: Excellent reliability, production ready
- **75-89**: Good reliability, acceptable for use
- **50-74**: Fair reliability, needs improvement
- **<50**: Poor reliability, requires fixes

#### Key Metrics
- **Success Rate**: Percentage of requests that completed successfully
- **Response Time**: Average time per request (should be <5s)
- **Consistency**: Whether repeated queries return consistent results
- **Validation Success**: Whether validation pipeline completes successfully

#### Common Issues and Solutions

**Low Success Rate (<75%)**
- Check if backend is running on correct port
- Verify API keys are valid
- Check BigQuery connection
- Review error messages in detailed output

**High Response Times (>10s)**
- Database connection may be slow
- LLM API calls timing out
- Network connectivity issues
- Check server load

**Inconsistent Results**
- LLM may be producing different outputs
- Cache may be interfering (disabled in tests)
- Validation logic may need tuning

**Validation Failures**
- SQL syntax issues
- BigQuery permissions
- Invalid chart data extraction
- LLM API limits

### Troubleshooting

#### Backend Not Responding
```bash
# Check if backend is running
curl http://localhost:8010/health

# Check validation health
curl http://localhost:8010/api/bigquery/validation/health
```

#### Database Connection Issues
```bash
# Test database connection
python -c "
from genai-agents-backend.agents.bigquery.database import BigQueryConnection
conn = BigQueryConnection()
print('Connection test:', conn.test_connection())
"
```

#### API Key Issues
```bash
# Verify environment variables
python -c "
import os
print('Anthropic:', bool(os.getenv('ANTHROPIC_API_KEY')))
print('GCP Project:', os.getenv('GCP_PROJECT_ID'))
"
```

### Test Results Files

Tests generate JSON files with detailed results:

- `validation_10x_test_TIMESTAMP.json` - Basic test results
- `validation_reliability_test_TIMESTAMP.json` - Comprehensive test results

These files contain:
- Individual test run details
- Performance statistics
- Error analysis
- Consistency metrics

### Continuous Testing

For continuous validation testing, you can run tests periodically:

```bash
# Run basic test every hour
while true; do
  python tests/test_basic_validation_10_times.py
  sleep 3600
done
```

Or set up as a cron job:
```bash
# Add to crontab for hourly testing
0 * * * * cd /path/to/project && python tests/test_basic_validation_10_times.py >> validation_tests.log 2>&1
```

## Integration with CI/CD

Add validation testing to your CI pipeline:

```yaml
# .github/workflows/validation-test.yml
name: Validation Tests
on: [push, pull_request]
jobs:
  validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Start backend
        run: cd genai-agents-backend && python app.py &
      - name: Wait for backend
        run: sleep 30
      - name: Run validation tests
        run: python tests/test_basic_validation_10_times.py
```

This ensures validation reliability is maintained across code changes.