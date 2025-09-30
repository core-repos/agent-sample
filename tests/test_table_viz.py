#!/usr/bin/env python3
"""Test that tables are shown as visualizations"""

import pandas as pd
from gradio_chatbot.app import create_chart_from_response, extract_table_data
from gradio_chatbot.components.charts import create_table

# Test response with table data
test_answer = """Here are the top 5 applications by cost:

1. E-commerce: $219,048.62
2. Payments: $111,990.81
3. Finance: $98,456.23
4. Marketing: $87,234.56
5. Analytics: $76,543.21

Total for top 5: $593,273.43"""

# Test extraction
table_data = extract_table_data(test_answer)
print("Extracted table data:")
print(table_data)
print()

# Test chart creation (should create table viz)
viz = create_chart_from_response(test_answer, "Show me the top 5 applications")
print(f"Visualization type: {type(viz)}")
print(f"Has data: {viz is not None}")

if viz:
    print("Table visualization created successfully!")
else:
    print("Failed to create table visualization")