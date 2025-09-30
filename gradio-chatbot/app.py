#!/usr/bin/env python3

import gradio as gr
import sys
import os
from pathlib import Path
import plotly.graph_objects as go
import pandas as pd
import re
from typing import List, Tuple, Optional
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.api_client import api_client
from components.charts import (
    create_bar_chart, create_line_chart, create_pie_chart,
    create_indicator
)

# Load environment configuration
load_dotenv()

def chat_response(message: str, history: List) -> Tuple[str, List, Optional[go.Figure]]:
    """Process message and return response with visualization"""

    if not message or not message.strip():
        return "", history, None

    # Add user message to history
    history = history or []
    history.append({"role": "user", "content": message})

    try:
        # API Call
        api_response = api_client.ask_question(message)

        # Handle the API client response structure
        if api_response.get('success') and api_response.get('data'):
            response = api_response['data']
            answer = response.get('answer', 'Unable to process request.')

            # Use structured chart_data from backend
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
                    visualization = None
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
    return "", [], None

def create_app():
    """Create a minimal, clean Gradio interface"""

    # Minimal CSS - focus on essentials only
    custom_css = """
    /* Clean professional theme */
    .gradio-container {
        max-width: 100% !important;
        background: #f8f9fa !important;
    }

    /* Chat area */
    #chatbot {
        height: 600px !important;
        border-radius: 8px !important;
    }

    /* Input textbox */
    #msg-input textarea {
        border-radius: 8px !important;
        border: 2px solid #e1e8ed !important;
    }

    #msg-input textarea:focus {
        border-color: #3b82f6 !important;
    }

    /* Button row - ensure horizontal layout */
    #btn-row {
        display: flex !important;
        flex-direction: row !important;
        gap: 10px !important;
    }

    /* Sidebar styling */
    #viz-sidebar {
        border-left: 1px solid #e1e8ed !important;
        padding-left: 20px !important;
    }

    /* Hide footer */
    footer {
        display: none !important;
    }
    """

    with gr.Blocks(css=custom_css, title="BigQuery Analytics AI") as app:

        with gr.Row():
            # Left Column - Chat Interface (70%)
            with gr.Column(scale=7):
                gr.Markdown("## BigQuery Analytics AI")

                chatbot = gr.Chatbot(
                    type="messages",
                    show_label=False,
                    elem_id="chatbot",
                    height=600
                )

                msg_input = gr.Textbox(
                    show_label=False,
                    placeholder="Ask a question about your data...",
                    lines=2,
                    elem_id="msg-input"
                )

                # TWO BUTTONS IN A ROW - Using gr.Row()
                with gr.Row(elem_id="btn-row"):
                    send_btn = gr.Button("Send", variant="primary", size="lg")
                    clear_btn = gr.Button("Clear", variant="secondary", size="lg")

            # Right Column - Sidebar (30%)
            with gr.Column(scale=3, elem_id="viz-sidebar"):
                gr.Markdown("### 📊 Visualization")

                chart_display = gr.Plot(
                    show_label=False,
                    visible=True
                )

                gr.Markdown("### 💡 Quick Queries")

                # Query buttons
                with gr.Column():
                    btn1 = gr.Button("What is the total cost?", size="sm")
                    btn2 = gr.Button("Top 5 applications by cost", size="sm")
                    btn3 = gr.Button("Cost breakdown by environment", size="sm")
                    btn4 = gr.Button("Daily cost trend", size="sm")
                    btn5 = gr.Button("Top cloud providers", size="sm")

        # Event Handlers
        def handle_submit(message, history):
            """Handle message submission"""
            msg_result, hist_result, chart_result = chat_response(message, history)
            return msg_result, hist_result, chart_result if chart_result else gr.update()

        # Submit on Enter or Send button
        msg_input.submit(
            fn=handle_submit,
            inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot, chart_display]
        )

        send_btn.click(
            fn=handle_submit,
            inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot, chart_display]
        )

        # Clear button
        clear_btn.click(
            fn=clear_chat,
            outputs=[msg_input, chatbot, chart_display]
        )

        # Quick query buttons
        btn1.click(lambda: "What is the total cost?", outputs=msg_input)
        btn2.click(lambda: "What are the top 5 applications by cost?", outputs=msg_input)
        btn3.click(lambda: "What's the cost breakdown by environment?", outputs=msg_input)
        btn4.click(lambda: "Show me the daily cost trend", outputs=msg_input)
        btn5.click(lambda: "Which cloud provider has the highest cost?", outputs=msg_input)

    return app

def main():
    """Main function to launch the app"""
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