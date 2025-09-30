# Test Suite for BigQuery Analytics AI

## Overview
This directory contains automated tests for the BigQuery Analytics AI platform.

## Test Files

### 1. `test_all_queries.py`
- **Purpose**: Tests all 7 example queries via the backend API
- **Type**: API Integration Test
- **Requirements**: Backend running on http://localhost:8010

**Usage:**
```bash
python test_all_queries.py
```

### 2. `test_ui_automated.js`
- **Purpose**: Tests the complete UI flow with browser automation
- **Type**: End-to-End UI Test
- **Requirements**: 
  - Both backend (port 8010) and frontend (port 7860) running
  - Puppeteer installed (`npm install puppeteer`)

**Usage:**
```bash
node test_ui_automated.js
```

## Test Coverage

Both test suites cover the following queries:
1. "What is the total cost?"
2. "Show me the top 10 applications by cost"
3. "What's the cost breakdown by environment?"
4. "Display the daily cost trend for last 30 days"
5. "Create a heatmap of costs by service"
6. "Show waterfall chart of cost components"
7. "Generate funnel chart for budget allocation"

## Running All Tests

### Quick Test (API only):
```bash
cd tests
python test_all_queries.py
```

### Full Test (API + UI):
```bash
# Terminal 1: Start backend
cd genai-agents-backend
python app.py

# Terminal 2: Start frontend
cd gradio-chatbot
python app.py

# Terminal 3: Run tests
cd tests
python test_all_queries.py
node test_ui_automated.js
```

## Expected Results
- All 7 queries should return successful responses
- Each query should generate appropriate visualizations
- No errors should appear in frontend or backend
- Response times should be under 10 seconds per query

## CI/CD Integration
These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run API Tests
  run: python tests/test_all_queries.py
  
- name: Run UI Tests
  run: node tests/test_ui_automated.js
```