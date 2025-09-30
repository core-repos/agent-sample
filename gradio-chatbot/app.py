#!/usr/bin/env python3

import gradio as gr
import sys
import os
from pathlib import Path
import plotly.graph_objects as go
import pandas as pd
import re
from typing import List, Tuple, Optional, Union
from dotenv import load_dotenv
import numpy as np
from datetime import datetime, timedelta

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.api_client import api_client
from components.charts import (
    create_bar_chart, create_line_chart, create_area_chart,
    create_scatter_plot, create_heatmap, create_pie_chart,
    create_indicator, create_table, create_waterfall_chart,
    create_funnel_chart, auto_select_chart, CHART_COLORS
)

# Load environment configuration
load_dotenv()

def create_chart_from_response(answer: str, query: str = "") -> Optional[go.Figure]:
    """Create appropriate chart based on response content and query"""
    
    answer_lower = answer.lower()
    query_lower = query.lower() if query else ""
    
    # Try auto-detection first
    auto_chart = auto_select_chart(answer)
    if auto_chart:
        return auto_chart
    
    # Check if we should show data as a table
    table_data = extract_table_data(answer)
    if table_data is not None and not table_data.empty:
        # If no specific chart is requested, show as table
        if not any(word in query_lower for word in ["chart", "graph", "plot", "visualiz", "trend", "heatmap", "waterfall", "funnel"]):
            return create_table(table_data, title="Data Table")
    
    # Bar chart for top/ranking data or cloud providers
    if any(word in answer_lower for word in ["top", "rank", "highest", "cloud spender", "aws", "azure", "gcp"]) or "top" in query_lower:
        # First try to match cloud providers format
        cloud_pattern = r'([A-Z]+):\s*\$?([\d,]+(?:\.\d{2})?)'
        cloud_matches = re.findall(cloud_pattern, answer)
        
        if cloud_matches and len(cloud_matches) >= 2:
            valid_matches = []
            for match in cloud_matches:
                try:
                    label = match[0].strip()
                    value = match[1].replace(',', '').strip()
                    if label and value and value != '':
                        float_value = float(value)
                        valid_matches.append((label, float_value))
                except (ValueError, IndexError):
                    continue
            
            if valid_matches:
                data = {
                    'x': [m[0] for m in valid_matches],
                    'y': [m[1] for m in valid_matches]
                }
                return create_bar_chart(
                    data,
                    title="Cloud Provider Spending",
                    show_values=True
                )
        
        # Then try numbered list format
        pattern = r'(\d+)[.)]\s*([^:$]+)[:\s]*\$?([\d,]+(?:\.\d{2})?)'
        matches = re.findall(pattern, answer)
        
        if matches:
            valid_matches = []
            for match in matches:
                try:
                    label = match[1].strip()
                    value = match[2].replace(',', '').strip()
                    if label and value and value != '':
                        float_value = float(value)
                        valid_matches.append((label, float_value))
                except (ValueError, IndexError):
                    continue
            
            if valid_matches:
                data = {
                    'x': [m[0] for m in valid_matches],
                    'y': [m[1] for m in valid_matches]
                }
                return create_bar_chart(
                    data,
                    title="Top Items by Value",
                    show_values=True
                )
    
    # Line chart for trends
    elif any(word in answer_lower + query_lower for word in ["trend", "over time", "daily", "monthly"]):
        # Try to parse actual data from response
        dates = []
        values = []
        chart_title = "Cost Trend Analysis"
        
        # Check if this is environment-based data (PROD/NON-PROD)
        if "PROD Environment" in answer and "NON-PROD Environment" in answer:
            # Parse environment-based daily costs: "2025-08-03: $180,580.55"
            prod_pattern = r'(\d{4}-\d{2}-\d{2}):\s*\$?([\d,]+(?:\.\d{2})?)'
            
            # Find PROD section
            prod_section = re.search(r'PROD Environment Daily Costs:(.*?)NON-PROD Environment', answer, re.DOTALL)
            if prod_section:
                prod_matches = re.findall(prod_pattern, prod_section.group(1))
                if prod_matches and len(prod_matches) >= 3:
                    chart_title = "PROD Environment Daily Cost Trend"
                    for date_str, cost_str in prod_matches:
                        try:
                            dates.append(date_str)
                            values.append(float(cost_str.replace(',', '')))
                        except (ValueError, IndexError):
                            continue
        
        # Pattern to match date and average: "2025-08-03: Total $198,687.55 (Avg: $1,655.73)"
        if not dates:
            date_avg_pattern = r'(\d{4}-\d{2}-\d{2}):[^(]+\(Avg:\s*\$?([\d,]+(?:\.\d{2})?)\)'
            matches = re.findall(date_avg_pattern, answer)
            
            if matches and len(matches) >= 3:  # Need at least 3 points for a trend
                chart_title = "Daily Average Cost Trend"
                for date_str, avg_str in matches:
                    try:
                        dates.append(date_str)
                        values.append(float(avg_str.replace(',', '')))
                    except (ValueError, IndexError):
                        continue
        
        # Fallback: try to parse any date-value patterns
        if not dates:
            date_total_pattern = r'(\d{4}-\d{2}-\d{2}):[^$]+\$?([\d,]+(?:\.\d{2})?)'
            matches = re.findall(date_total_pattern, answer)
            
            if matches and len(matches) >= 3:
                for date_str, total_str in matches[:15]:  # Limit to first 15 for readability
                    try:
                        dates.append(date_str)
                        values.append(float(total_str.replace(',', '')))
                    except (ValueError, IndexError):
                        continue
        
        # Create chart if we have data
        if dates and values:
            data = {
                'x': dates,
                'y': values
            }
            return create_line_chart(
                data,
                title=chart_title,
                show_dots=True,
                fill_area=False
            )
    
    # Pie chart for distribution/breakdown - ALWAYS show for environment questions
    elif "environment" in query_lower or "environment" in answer_lower or any(word in answer_lower for word in ["PROD:", "NON-PROD:"]):
        # Multiple patterns to ensure we catch the data
        patterns = [
            # Pattern 1: Bullet points with any format (including percentage)
            r'[•\-\*]\s*([A-Z][A-Z\-]*(?:\s*[A-Z\-]+)*):\s*\$?([\d,]+(?:\.\d{2})?)\s*(?:\([0-9.]+%\))?',
            # Pattern 2: Direct environment names with or without percentage
            r'(PROD|NON-PROD|Production|Non-Production):\s*\$?([\d,]+(?:\.\d{2})?)\s*(?:\([0-9.]+%\))?',
            # Pattern 3: With percentage in parentheses
            r'([A-Z][A-Z\-]*(?:\s*[A-Z\-]+)*):\s*\$?([\d,]+(?:\.\d{2})?)\s*\([0-9.]+%\)',
            # Pattern 4: Simple colon separated
            r'([A-Z][A-Za-z\-\s]+):\s*\$?([\d,]+(?:\.\d{2})?)'
        ]
        
        matches = []
        for pattern in patterns:
            matches = re.findall(pattern, answer)
            if matches:
                break
        
        # If still no matches, try to find any numeric values with labels
        if not matches:
            # Look for lines with dollar amounts
            lines = answer.split('\n')
            for line in lines:
                if '$' in line and ':' in line:
                    parts = line.split(':')
                    if len(parts) == 2:
                        label = parts[0].strip().replace('•', '').replace('-', '').replace('*', '').strip()
                        value_part = parts[1].strip()
                        # Extract number from value part
                        num_match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', value_part)
                        if num_match and label:
                            matches.append((label, num_match.group(1)))
        
        if matches and len(matches) >= 2:
            # Validate and clean data
            labels = []
            values = []
            for match in matches:
                label = match[0].strip().replace('•', '').replace('-', '').strip()
                value_str = match[1].replace(',', '').replace('$', '').strip()
                
                # Clean up label
                if 'PROD' in label.upper() and 'NON' not in label.upper():
                    label = 'PROD'
                elif 'NON' in label.upper() or 'NON-PROD' in label.upper():
                    label = 'NON-PROD'
                
                if label and value_str:
                    try:
                        value = float(value_str)
                        if value > 0:  # Only add positive values
                            labels.append(label)
                            values.append(value)
                    except (ValueError, TypeError) as e:
                        print(f"Skipping invalid value: {value_str}")
                        continue
            
            if labels and values and len(labels) >= 2:
                data = {
                    'labels': labels,
                    'values': values
                }
                
                # Determine title based on query
                if "environment" in query_lower:
                    title = "Cost Breakdown by Environment"
                elif "cloud" in query_lower:
                    title = "Cost Breakdown by Cloud Provider"
                else:
                    title = "Cost Distribution"
                
                return create_pie_chart(
                    data,
                    title=title,
                    hole=0.4
                )
    
    # Heatmap for matrix data
    elif "heatmap" in query_lower:
        matrix_data = np.random.rand(5, 5) * 100
        return create_heatmap(
            matrix_data,
            x_labels=[f'App {i+1}' for i in range(5)],
            y_labels=[f'Service {i+1}' for i in range(5)],
            title="Cost Heatmap",
            show_values=True
        )
    
    # Waterfall chart
    elif "waterfall" in query_lower:
        data = {
            'x': ['Start', 'Product A', 'Product B', 'Product C', 'End'],
            'y': [50000, 15000, -8000, 12000, 69000]
        }
        measure = ['absolute', 'relative', 'relative', 'relative', 'total']
        return create_waterfall_chart(data, title="Cost Breakdown", measure=measure)
    
    # Funnel chart
    elif "funnel" in query_lower:
        data = {
            'stages': ['Total Budget', 'Allocated', 'Spent', 'Optimized'],
            'values': [100000, 75000, 50000, 30000]
        }
        return create_funnel_chart(data, title="Budget Funnel")
    
    # Indicator for single metrics
    elif any(word in answer_lower for word in ["total", "sum", "average"]):
        match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', answer)
        if match:
            value_str = match.group(1).replace(',', '').strip()
            if value_str and value_str != '':
                value = float(value_str)
            else:
                return None
            
            if "total" in answer_lower:
                title = "Total Cost"
            elif "average" in answer_lower:
                title = "Average Cost"
            else:
                title = "Metric Value"
            
            return create_indicator(
                value,
                title=title,
                reference=value * 0.9,
                format_str="$,.0f"
            )
    
    return None

def extract_table_data(answer: str) -> Optional[pd.DataFrame]:
    """Extract table data from the response if present"""
    # Look for structured data patterns that could be displayed as a table
    
    # Pattern 1: Numbered list with values (e.g., "1. App A: $1000")
    pattern1 = r'(\d+)[.)]\s*([^:$]+)[:\s]*\$?([\d,]+(?:\.\d{2})?)'
    matches = re.findall(pattern1, answer)
    
    if len(matches) >= 2:
        data = []
        for match in matches:
            try:
                rank = match[0]
                name = match[1].strip()
                value_str = match[2].replace(',', '').strip()
                if name and value_str and value_str != '':
                    value = float(value_str)
                    data.append({'Rank': rank, 'Name': name, 'Cost ($)': f'{value:,.2f}'})
            except (ValueError, IndexError):
                continue
        
        if data:
            return pd.DataFrame(data)
    
    # Pattern 2: Key-value pairs (e.g., "Total: $5000")
    pattern2 = r'([A-Za-z][A-Za-z\s-]+?):\s*\$?([\d,]+(?:\.\d{2})?)'
    matches2 = re.findall(pattern2, answer)
    
    if len(matches2) >= 3:  # Only show as table if we have multiple rows
        data = []
        for match in matches2:
            try:
                category = match[0].strip()
                value_str = match[1].replace(',', '').strip()
                if category and value_str and value_str != '':
                    value = float(value_str)
                    data.append({'Category': category, 'Value ($)': f'{value:,.2f}'})
            except (ValueError, IndexError):
                continue
        
        if len(data) >= 3:
            return pd.DataFrame(data)
    
    return None

def chat_response(message: str, history: List) -> Tuple[str, List, Optional[go.Figure]]:
    """Process message and return response with visualization"""

    if not message or not message.strip():
        return "", history, None

    # Add user message to history
    history = history or []
    history.append({"role": "user", "content": message})

    try:
        # API Call - validation happens in backend pipeline automatically
        api_response = api_client.ask_question(message)

        # Handle the API client response structure
        if api_response.get('success') and api_response.get('data'):
            response = api_response['data']
            answer = response.get('answer', 'Unable to process request.')

            # Use structured chart_data from backend instead of parsing text
            visualization = None
            chart_data = response.get('chart_data')
            visualization_type = response.get('visualization')

            if chart_data and visualization_type:
                try:
                    if visualization_type == 'indicator' and chart_data.get('type') == 'indicator':
                        data = chart_data.get('data', {})
                        visualization = create_indicator(
                            value=data.get('value', 0),
                            title=data.get('title', 'Metric'),
                            reference=data.get('value', 0) * 0.9,
                            format_str="$,.0f"
                        )
                    elif visualization_type == 'bar' and chart_data.get('type') == 'bar':
                        data = chart_data.get('data', {})
                        visualization = create_bar_chart(
                            data=data,
                            title=f"Top {len(data.get('labels', []))} Items by Cost",
                            x_axis_title="Applications",
                            y_axis_title="Cost ($)"
                        )
                    elif visualization_type == 'pie' and chart_data.get('type') == 'pie':
                        data = chart_data.get('data', {})
                        visualization = create_pie_chart(
                            data=data,
                            title="Cost Distribution",
                            hole=0.4
                        )
                    elif visualization_type == 'line' or chart_data.get('type') == 'line':
                        data = chart_data.get('data', {})
                        # Convert to format expected by line chart
                        line_data = {
                            'x': data.get('dates', []),
                            'y': data.get('values', [])
                        }
                        visualization = create_line_chart(
                            data=line_data,
                            title="Daily Cost Trend",
                            x_axis_title="Date",
                            y_axis_title="Cost ($)"
                        )
                except Exception as e:
                    print(f"Chart creation error: {e}")
                    # Fallback to text parsing if structured data fails
                    visualization = create_chart_from_response(answer, message)
            else:
                # Fallback to text parsing for older responses
                visualization = create_chart_from_response(answer, message)

        else:
            # Handle error case
            error_msg = api_response.get('error', 'Unknown error occurred')
            answer = f"Error: {error_msg}"
            visualization = None

    except Exception as e:
        answer = f"Error: {str(e)}"
        visualization = None

    # Add bot response to history
    history.append({"role": "assistant", "content": answer})

    return "", history, visualization

def clear_chat():
    """Clear all chat and visualizations"""
    return "", [], gr.update(visible=False), gr.update(visible=False)

def expand_chart(chart_data):
    """Show chart in full screen modal"""
    if chart_data is None:
        return gr.update(visible=False), None
    return gr.update(visible=True), chart_data

def close_fullscreen():
    """Close full screen modal"""
    return gr.update(visible=False), None

def show_inline_chart(chart_data):
    """Show inline chart and expand button when chart is available"""
    if chart_data is None:
        return gr.update(visible=False), gr.update(visible=False)
    return gr.update(visible=True), gr.update(visible=True)

def create_app():
    """Create the Gradio interface with sidebar chart layout"""
    
    with gr.Blocks(
        css="""
        /* Professional light theme with clean design */
        .gradio-container {
            background: #f8f9fa !important;
            color: #2c3e50 !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            max-width: 100% !important;
            padding: 20px !important;
        }

        /* Main chatbot styling */
        #main-chatbot {
            height: calc(100vh - 250px) !important;
            min-height: 500px !important;
            border: 1px solid #e1e8ed !important;
            border-radius: 8px !important;
            background: white !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
            padding: 16px !important;
        }

        /* Input box styling - professional and clean */
        #input-footer {
            margin-top: 16px !important;
            padding: 0 !important;
        }

        #input-text {
            margin-bottom: 12px !important;
        }

        #input-text textarea {
            background: white !important;
            border: 2px solid #e1e8ed !important;
            border-radius: 8px !important;
            color: #2c3e50 !important;
            font-size: 1rem !important;
            padding: 14px 16px !important;
            transition: border-color 0.2s ease !important;
            line-height: 1.5 !important;
            min-height: 48px !important;
            resize: none !important;
        }

        #input-text textarea:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
            outline: none !important;
        }

        #input-text textarea::placeholder {
            color: #94a3b8 !important;
        }

        /* Button row layout - Force horizontal layout */
        #button-row {
            display: flex !important;
            flex-direction: row !important;
            gap: 12px !important;
            margin-top: 0 !important;
            align-items: center !important;
        }

        /* Ensure Row container renders as flex */
        #button-row.row {
            display: flex !important;
            flex-direction: row !important;
        }

        /* Button styling - Send button (primary) */
        .send-btn,
        .send-btn button {
            background: #1e293b !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            padding: 12px 24px !important;
            transition: all 0.2s ease !important;
            font-size: 0.95rem !important;
            height: 48px !important;
            min-width: 100px !important;
            flex: 1 !important;
        }

        .send-btn button:hover {
            background: #334155 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(30, 41, 59, 0.3) !important;
        }

        /* Clear button styling (secondary) */
        .clear-btn,
        .clear-btn button {
            background: white !important;
            color: #1e293b !important;
            border: 2px solid #1e293b !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            padding: 12px 24px !important;
            transition: all 0.2s ease !important;
            font-size: 0.95rem !important;
            height: 48px !important;
            min-width: 100px !important;
            flex: 1 !important;
        }

        .clear-btn button:hover {
            background: #f8f9fa !important;
            border-color: #334155 !important;
        }

        /* Sidebar styling */
        #sidebar-container {
            background: white !important;
            border-left: 1px solid #e1e8ed !important;
            padding: 20px !important;
            height: 100% !important;
        }

        /* Chart in sidebar */
        #sidebar-chart {
            height: 320px !important;
            width: 100% !important;
            border: 1px solid #e1e8ed !important;
            border-radius: 8px !important;
            background: white !important;
            margin-bottom: 20px !important;
        }

        /* Sidebar headings */
        .sidebar-heading {
            margin-bottom: 16px !important;
        }

        .sidebar-heading h3 {
            color: #1e293b !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            margin: 0 0 2px 0 !important;
            letter-spacing: -0.01em !important;
        }

        .sidebar-subheading {
            color: #64748b !important;
            font-size: 0.8rem !important;
            margin: 0 !important;
        }

        /* Query list styling - clean and professional */
        .query-list {
            background: transparent !important;
            border-radius: 0px !important;
            padding: 0px !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 0px !important;
        }

        .query-item button {
            background: transparent !important;
            border: none !important;
            border-bottom: 1px solid #e1e8ed !important;
            border-radius: 0px !important;
            padding: 14px 12px !important;
            margin-bottom: 0px !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            font-size: 0.875rem !important;
            color: #475569 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            width: 100% !important;
            text-align: left !important;
            font-weight: 400 !important;
            height: auto !important;
            min-height: 48px !important;
        }

        .query-item button:hover {
            background: #f1f5f9 !important;
            color: #3b82f6 !important;
            padding-left: 16px !important;
        }

        .query-item button::after {
            content: "📋" !important;
            font-size: 0.9rem !important;
            opacity: 0.5 !important;
            transition: opacity 0.2s ease !important;
            margin-left: auto !important;
        }

        .query-item button:hover::after {
            opacity: 1 !important;
        }

        /* Expand button */
        #expand-btn {
            background: #3b82f6 !important;
            color: white !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 4px 10px !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
            cursor: pointer !important;
        }

        #expand-btn:hover {
            background: #2563eb !important;
        }

        /* Fullscreen modal */
        #fullscreen-modal {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background: rgba(0, 0, 0, 0.9) !important;
            z-index: 9999 !important;
            padding: 20px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }

        #fullscreen-chart {
            height: 85vh !important;
            width: 95vw !important;
            max-width: 1400px !important;
        }

        #close-btn {
            background: #ef4444 !important;
            color: white !important;
            border: none !important;
            padding: 8px 16px !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
            cursor: pointer !important;
        }

        #close-btn:hover {
            background: #dc2626 !important;
        }

        /* General button styling */
        button {
            border-radius: 8px !important;
        }

        /* Hide Gradio branding and footer */
        footer {
            display: none !important;
        }

        .gradio-container footer {
            display: none !important;
        }

        /* Hide "Use via API" and "Built with Gradio" */
        a[href*="api"] {
            display: none !important;
        }

        .footer {
            display: none !important;
        }

        .api-docs {
            display: none !important;
        }
        """
    ) as app:


        with gr.Row():
            # Left side - Chat interface (70% width)
            with gr.Column(scale=7):
                chatbot = gr.Chatbot(
                    type="messages",
                    show_label=False,
                    elem_id="main-chatbot"
                )

                # Input area with horizontal button layout
                with gr.Column(elem_id="input-footer"):
                    msg_input = gr.Textbox(
                        show_label=False,
                        placeholder="Ask a question about your data...",
                        lines=1,
                        elem_id="input-text"
                    )
                    with gr.Row(elem_id="button-row"):
                        send_btn = gr.Button("Send", variant="primary", elem_classes="send-btn", scale=1)
                        clear_btn = gr.Button("Clear", variant="secondary", elem_classes="clear-btn", scale=1)

            # Right sidebar (30% width)
            with gr.Column(scale=3, elem_id="sidebar-container"):
                # Visualization section
                with gr.Column(elem_classes="sidebar-heading"):
                    gr.Markdown("### 📊 Visualization")

                with gr.Row():
                    with gr.Column(scale=10):
                        pass
                    expand_btn = gr.Button(
                        "Expand",
                        size="sm",
                        visible=False,
                        elem_id="expand-btn"
                    )

                sidebar_chart = gr.Plot(
                    show_label=False,
                    elem_id="sidebar-chart",
                    visible=False
                )

                # Commonly asked queries as a clean list
                with gr.Column(elem_classes="sidebar-heading"):
                    gr.Markdown("### 💡 Quick Queries")

                with gr.Column(elem_classes="query-list"):
                    gr.Button("Total cost", size="sm", elem_classes="query-item").click(
                        lambda: "What is the total cost?",
                        outputs=msg_input
                    )

                    gr.Button("Top 5 applications", size="sm", elem_classes="query-item").click(
                        lambda: "What are the top 5 applications by cost?",
                        outputs=msg_input
                    )

                    gr.Button("Cost by environment", size="sm", elem_classes="query-item").click(
                        lambda: "What's the cost breakdown by environment?",
                        outputs=msg_input
                    )

                    gr.Button("Daily cost trend", size="sm", elem_classes="query-item").click(
                        lambda: "Show me the daily cost trend",
                        outputs=msg_input
                    )

                    gr.Button("Top cloud providers", size="sm", elem_classes="query-item").click(
                        lambda: "Which cloud provider has the highest cost?",
                        outputs=msg_input
                    )

                    gr.Button("PROD vs NON-PROD", size="sm", elem_classes="query-item").click(
                        lambda: "Compare PROD and NON-PROD environment costs",
                        outputs=msg_input
                    )
        
        # Full-screen modal for visualization
        with gr.Row(visible=False, elem_id="fullscreen-modal") as fullscreen_modal:
            with gr.Column():
                with gr.Row():
                    with gr.Column(scale=10):
                        gr.HTML("<h3>📊 Data Visualization - Full Screen</h3>")
                    with gr.Column(scale=1):
                        close_btn = gr.Button(
                            "✕", 
                            size="sm",
                            variant="secondary",
                            elem_id="close-btn"
                        )
                fullscreen_chart = gr.Plot(
                    show_label=False,
                    elem_id="fullscreen-chart"
                )
        
        # Event Handlers
        def handle_message_and_show_chart(message, history):
            """Handle message and update sidebar chart visibility"""
            msg_result, hist_result, chart_result = chat_response(message, history)

            # Update chart visibility in sidebar
            if chart_result is not None:
                chart_visible = gr.update(visible=True, value=chart_result)
                btn_visible = gr.update(visible=True)
            else:
                chart_visible = gr.update(visible=False)
                btn_visible = gr.update(visible=False)

            return msg_result, hist_result, chart_visible, btn_visible

        msg_input.submit(
            fn=handle_message_and_show_chart,
            inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot, sidebar_chart, expand_btn]
        )

        send_btn.click(
            fn=handle_message_and_show_chart,
            inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot, sidebar_chart, expand_btn]
        )

        clear_btn.click(
            fn=clear_chat,
            outputs=[msg_input, chatbot, sidebar_chart, expand_btn]
        )

        # Full-screen modal handlers
        expand_btn.click(
            fn=expand_chart,
            inputs=[sidebar_chart],
            outputs=[fullscreen_modal, fullscreen_chart]
        )
        
        close_btn.click(
            fn=close_fullscreen,
            outputs=[fullscreen_modal, fullscreen_chart]
        )
    
    return app

def main():
    """Main function to launch the app"""
    # Get configuration from environment
    frontend_host = os.getenv('FRONTEND_HOST', '0.0.0.0')
    frontend_port = int(os.getenv('FRONTEND_PORT', '7860'))
    backend_url = os.getenv('API_BASE_URL', os.getenv('BACKEND_URL', 'http://localhost:8010'))

    print("🚀 Starting BigQuery Analytics AI")
    print("=" * 50)

    # Check backend health
    try:
        if api_client.check_health():
            print(f"✓ Backend: Online at {backend_url}")
    except:
        print(f"✗ Backend: Offline - Please start backend at {backend_url}")

    print(f"✓ Frontend: Starting at http://{frontend_host}:{frontend_port}")
    print("📊 Visualizations: 14 chart types supported")
    print("=" * 50)

    # Create and launch app
    app = create_app()
    app.launch(
        server_name=frontend_host,
        server_port=frontend_port,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()