"""
Configuration settings for Analytics Assistant
"""

# API Configuration
BACKEND_URL = "http://localhost:8010/api/ask"
BACKEND_HEALTH_URL = "http://localhost:8010/api/health"
BACKEND_EXAMPLES_URL = "http://localhost:8010/api/examples"

# UI Configuration
APP_TITLE = "BigQuery Agent"
APP_DESCRIPTION = "AI-powered data analysis and insights"
SERVER_PORT = 7860
SERVER_HOST = "0.0.0.0"

# Chart Configuration
CHART_HEIGHT = 350
CHART_COLORS = [
    '#667eea', '#764ba2', '#f59e0b', '#10b981', 
    '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899'
]

# Quick Insights - Predefined queries
QUICK_INSIGHTS = [
    "What is the total cost?",
    "Show top 5 applications by cost",
    "What's the average cost per application?",
    "Display costs by environment",
    "List unique cloud providers",
    "Show cost trends",
    "What are the most expensive services?",
    "Break down costs by team"
]

# Theme Configuration - Modern Agent Style
THEME_CONFIG = {
    'primary_color': '#3b82f6',  # Modern blue
    'secondary_color': '#6366f1',  # Indigo accent
    'neutral_color': '#64748b',
    'success_color': '#10b981',
    'warning_color': '#f59e0b',
    'error_color': '#ef4444',
    'background_color': '#f8fafc',
    'card_color': '#ffffff',
    'border_color': '#e2e8f0',
    'font_family': 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif'
}

# Response Configuration
MAX_RESPONSE_TIME = 30  # seconds
CACHE_DURATION = 300  # seconds
MAX_RETRIES = 3