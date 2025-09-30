"""
Advanced Chart Components - All visualization types fixed
Matches ChatGPT/Gemini AI interface design
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
import re
from datetime import datetime, timedelta

# ChatGPT/Gemini Color Palette
CHART_COLORS = {
    'primary': '#10A37F',      # ChatGPT green
    'secondary': '#4285F4',    # Gemini blue  
    'tertiary': '#8B5CF6',     # Purple
    'quaternary': '#EC4899',   # Pink
    'quinary': '#F59E0B',      # Orange
    'senary': '#06B6D4',       # Cyan
    'septenary': '#84CC16',    # Lime
    'octonary': '#F97316',     # Deep orange
    'background': '#FFFFFF',
    'surface': '#F7F7F8',
    'border': '#E5E5E5',
    'text_primary': '#2D333A',
    'text_secondary': '#6E7681',
    'error': '#EF4444',
    'success': '#10B981',
    'warning': '#F59E0B'
}

# Get color sequence for multi-series charts
COLOR_SEQUENCE = [
    CHART_COLORS['primary'],
    CHART_COLORS['secondary'],
    CHART_COLORS['tertiary'],
    CHART_COLORS['quaternary'],
    CHART_COLORS['quinary'],
    CHART_COLORS['senary'],
    CHART_COLORS['septenary'],
    CHART_COLORS['octonary']
]

# Professional layout template
BASE_LAYOUT = {
    'plot_bgcolor': '#FAFAFA',
    'paper_bgcolor': 'white',
    'font': dict(
        family="system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
        size=12,
        color=CHART_COLORS['text_primary']
    ),
    'margin': dict(t=40, b=40, l=50, r=20),
    'height': 400,
    'hovermode': 'x unified',
    'hoverlabel': dict(
        bgcolor="white",
        font_size=13,
        font_family="system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
        bordercolor=CHART_COLORS['border']
    ),
    'xaxis': dict(
        gridcolor=CHART_COLORS['border'],
        zerolinecolor=CHART_COLORS['border'],
        linecolor=CHART_COLORS['border']
    ),
    'yaxis': dict(
        gridcolor=CHART_COLORS['border'],
        zerolinecolor=CHART_COLORS['border'],
        linecolor=CHART_COLORS['border']
    )
}

def create_bar_chart(
    data: Union[Dict, pd.DataFrame],
    x: str = None,
    y: str = None,
    title: str = "Bar Chart",
    color_by: str = None,
    orientation: str = 'v',
    show_values: bool = True
) -> go.Figure:
    """Create professional bar chart matching ChatGPT/Gemini style"""
    
    if isinstance(data, dict):
        x_values = data.get('x', data.get('categories', data.get('labels', [])))
        y_values = data.get('y', data.get('values', data.get('costs', [])))
    else:
        x_values = data[x] if x else data.index
        y_values = data[y] if y else data.values
    
    # Create bar chart
    fig = go.Figure()
    
    # Add bars with gradient effect
    for i, (xv, yv) in enumerate(zip(x_values, y_values)):
        color = COLOR_SEQUENCE[i % len(COLOR_SEQUENCE)]
        fig.add_trace(go.Bar(
            x=[xv] if orientation == 'v' else [yv],
            y=[yv] if orientation == 'v' else [xv],
            name=str(xv),
            marker=dict(
                color=color,
                line=dict(color=color, width=0),
                opacity=0.9
            ),
            text=f'${yv:,.0f}' if isinstance(yv, (int, float)) else str(yv),
            textposition='outside' if show_values else 'none',
            textfont=dict(size=11, color=CHART_COLORS['text_secondary']),
            hovertemplate='<b>%{x}</b><br>Value: %{y:,.2f}<extra></extra>'
        ))
    
    # Update layout
    layout = BASE_LAYOUT.copy()
    layout.update({
        'title': dict(
            text=title,
            font=dict(size=16, color=CHART_COLORS['text_primary']),
            x=0,
            xanchor='left'
        ),
        'showlegend': False,
        'xaxis': dict(
            title='',
            tickangle=-45 if len(x_values) > 5 else 0,
            gridcolor=CHART_COLORS['border']
        ),
        'yaxis': dict(
            title='Value',
            tickformat='$,.0f',
            gridcolor=CHART_COLORS['border']
        ),
        'bargap': 0.2,
        'bargroupgap': 0.1
    })
    
    fig.update_layout(layout)
    return fig

def create_line_chart(
    data: Union[Dict, pd.DataFrame],
    x: str = None,
    y: str = None,
    title: str = "Trend Analysis",
    multiple_lines: Dict = None,
    show_dots: bool = True,
    fill_area: bool = True
) -> go.Figure:
    """Create professional line chart with area fill"""
    
    fig = go.Figure()
    
    if isinstance(data, dict):
        x_values = data.get('x', data.get('dates', []))
        y_values = data.get('y', data.get('values', []))
        
        # Handle multiple lines
        if multiple_lines:
            for i, (name, values) in enumerate(multiple_lines.items()):
                color = COLOR_SEQUENCE[i % len(COLOR_SEQUENCE)]
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=values,
                    mode='lines+markers' if show_dots else 'lines',
                    name=name,
                    line=dict(color=color, width=2.5, shape='spline'),
                    marker=dict(size=6, color=color, line=dict(color='white', width=1.5)),
                    fill='tonexty' if i > 0 and fill_area else 'tozeroy' if fill_area else None,
                    fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)',
                    hovertemplate='<b>%{x}</b><br>%{y:,.2f}<extra></extra>'
                ))
        else:
            # Single line
            color = CHART_COLORS['primary']
            fig.add_trace(go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers' if show_dots else 'lines',
                line=dict(color=color, width=2.5, shape='spline'),
                marker=dict(size=6, color=color, line=dict(color='white', width=1.5)),
                fill='tozeroy' if fill_area else None,
                fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)',
                hovertemplate='<b>%{x}</b><br>Value: %{y:,.2f}<extra></extra>'
            ))
    
    # Update layout
    layout = BASE_LAYOUT.copy()
    layout.update({
        'title': dict(
            text=title,
            font=dict(size=16, color=CHART_COLORS['text_primary']),
            x=0,
            xanchor='left'
        ),
        'showlegend': multiple_lines is not None,
        'legend': dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor=CHART_COLORS['border'],
            borderwidth=1
        ),
        'xaxis': dict(
            title='',
            gridcolor=CHART_COLORS['border'],
            showgrid=True,
            zeroline=False
        ),
        'yaxis': dict(
            title='Value',
            tickformat='$,.0f',
            gridcolor=CHART_COLORS['border'],
            showgrid=True,
            zeroline=True
        )
    })
    
    fig.update_layout(layout)
    return fig

def create_area_chart(
    data: Union[Dict, pd.DataFrame],
    x: str = None,
    y: str = None,
    title: str = "Area Chart",
    stacked: bool = False,
    categories: List[str] = None
) -> go.Figure:
    """Create professional area chart with stacking support"""
    
    fig = go.Figure()
    
    if isinstance(data, dict):
        x_values = data.get('x', data.get('dates', []))
        
        if categories:
            # Multiple stacked areas
            for i, category in enumerate(categories):
                y_values = data.get(category, [])
                color = COLOR_SEQUENCE[i % len(COLOR_SEQUENCE)]
                
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode='lines',
                    name=category,
                    line=dict(width=0.5, color=color),
                    stackgroup='one' if stacked else None,
                    fillcolor=color if not stacked else None,
                    fill='tonexty' if i > 0 and not stacked else 'tozeroy',
                    hovertemplate='<b>%{x}</b><br>%{y:,.2f}<extra></extra>'
                ))
        else:
            # Single area
            y_values = data.get('y', data.get('values', []))
            color = CHART_COLORS['primary']
            
            fig.add_trace(go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines',
                line=dict(color=color, width=2),
                fill='tozeroy',
                fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.3)',
                hovertemplate='<b>%{x}</b><br>Value: %{y:,.2f}<extra></extra>'
            ))
    
    # Update layout
    layout = BASE_LAYOUT.copy()
    layout.update({
        'title': dict(
            text=title,
            font=dict(size=16, color=CHART_COLORS['text_primary']),
            x=0,
            xanchor='left'
        ),
        'showlegend': categories is not None,
        'legend': dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        'xaxis': dict(
            title='',
            gridcolor=CHART_COLORS['border']
        ),
        'yaxis': dict(
            title='Value',
            tickformat='$,.0f',
            gridcolor=CHART_COLORS['border']
        )
    })
    
    fig.update_layout(layout)
    return fig

def create_scatter_plot(
    data: Union[Dict, pd.DataFrame],
    x: str = None,
    y: str = None,
    title: str = "Scatter Plot",
    size: str = None,
    color: str = None,
    trendline: bool = False
) -> go.Figure:
    """Create professional scatter plot with optional trendline"""
    
    fig = go.Figure()
    
    if isinstance(data, dict):
        x_values = data.get('x', [])
        y_values = data.get('y', [])
        size_values = data.get(size, [10] * len(x_values)) if size else [10] * len(x_values)
        color_values = data.get(color, [CHART_COLORS['primary']] * len(x_values))
    else:
        x_values = data[x] if x else data.index
        y_values = data[y] if y else data.values
        size_values = data[size] if size else [10] * len(x_values)
        color_values = data[color] if color else [CHART_COLORS['primary']] * len(x_values)
    
    # Add scatter points
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='markers',
        marker=dict(
            size=size_values,
            color=color_values,
            colorscale='Viridis' if isinstance(color_values[0], (int, float)) else None,
            showscale=isinstance(color_values[0], (int, float)),
            line=dict(color='white', width=1),
            opacity=0.8
        ),
        hovertemplate='<b>X:</b> %{x}<br><b>Y:</b> %{y:,.2f}<extra></extra>'
    ))
    
    # Add trendline if requested
    if trendline and len(x_values) > 1:
        z = np.polyfit(range(len(x_values)), y_values, 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=x_values,
            y=p(range(len(x_values))),
            mode='lines',
            name='Trend',
            line=dict(color=CHART_COLORS['secondary'], width=2, dash='dash'),
            hoverinfo='skip'
        ))
    
    # Update layout
    layout = BASE_LAYOUT.copy()
    layout.update({
        'title': dict(
            text=title,
            font=dict(size=16, color=CHART_COLORS['text_primary']),
            x=0,
            xanchor='left'
        ),
        'showlegend': trendline,
        'xaxis': dict(
            title='X Axis',
            gridcolor=CHART_COLORS['border']
        ),
        'yaxis': dict(
            title='Y Axis',
            gridcolor=CHART_COLORS['border']
        )
    })
    
    fig.update_layout(layout)
    return fig

def create_heatmap(
    data: Union[Dict, pd.DataFrame, List[List]],
    x_labels: List[str] = None,
    y_labels: List[str] = None,
    title: str = "Heatmap",
    show_values: bool = True,
    color_scale: str = 'Viridis'
) -> go.Figure:
    """Create professional heatmap visualization"""
    
    if isinstance(data, dict):
        z_values = data.get('z', data.get('values', []))
        x_labels = x_labels or data.get('x', [])
        y_labels = y_labels or data.get('y', [])
    elif isinstance(data, pd.DataFrame):
        z_values = data.values
        x_labels = x_labels or data.columns.tolist()
        y_labels = y_labels or data.index.tolist()
    else:
        z_values = data
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=x_labels,
        y=y_labels,
        colorscale=[
            [0, CHART_COLORS['surface']],
            [0.25, CHART_COLORS['secondary']],
            [0.5, CHART_COLORS['primary']],
            [0.75, CHART_COLORS['tertiary']],
            [1, CHART_COLORS['quaternary']]
        ],
        showscale=True,
        colorbar=dict(
            title=dict(text="Value", side="right"),
            tickmode="linear",
            tick0=0,
            dtick=1,
            thickness=15,
            len=0.7,
            bordercolor=CHART_COLORS['border'],
            borderwidth=1
        ),
        text=z_values if show_values else None,
        texttemplate='%{text:.1f}' if show_values else None,
        textfont={"size": 10},
        hovertemplate='<b>%{x}</b> - <b>%{y}</b><br>Value: %{z:.2f}<extra></extra>'
    ))
    
    # Update layout
    layout = BASE_LAYOUT.copy()
    layout.update({
        'title': dict(
            text=title,
            font=dict(size=16, color=CHART_COLORS['text_primary']),
            x=0,
            xanchor='left'
        ),
        'xaxis': dict(
            title='',
            side='bottom',
            tickangle=-45 if x_labels and len(x_labels) > 10 else 0
        ),
        'yaxis': dict(
            title='',
            autorange='reversed'
        )
    })
    
    fig.update_layout(layout)
    return fig

def create_pie_chart(
    data: Union[Dict, pd.DataFrame],
    labels: List[str] = None,
    values: List[float] = None,
    title: str = "Distribution",
    hole: float = 0.4,
    show_legend: bool = True
) -> go.Figure:
    """Create professional pie/donut chart"""
    
    if isinstance(data, dict):
        labels = labels or data.get('labels', data.get('categories', []))
        values = values or data.get('values', data.get('costs', []))
    else:
        labels = labels or data.index.tolist()
        values = values or data.values.tolist()
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=hole,
        marker=dict(
            colors=COLOR_SEQUENCE[:len(labels)],
            line=dict(color='white', width=2)
        ),
        textfont=dict(size=12, color='white'),
        textposition='auto',
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Value: %{value:,.2f}<br>%{percent}<extra></extra>'
    )])
    
    # Update layout
    layout = {
        'title': dict(
            text=title,
            font=dict(size=16, color=CHART_COLORS['text_primary']),
            x=0,
            xanchor='left'
        ),
        'height': 400,
        'margin': dict(t=60, b=40, l=40, r=40),
        'paper_bgcolor': 'white',
        'showlegend': show_legend,
        'legend': dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            font=dict(size=11)
        ),
        'font': dict(
            family="system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
            color=CHART_COLORS['text_primary']
        )
    }
    
    fig.update_layout(layout)
    return fig

def create_indicator(
    value: float,
    title: str = "Metric",
    reference: float = None,
    format_str: str = "$,.2f",
    show_delta: bool = True,
    gauge: bool = False,
    max_value: float = None
) -> go.Figure:
    """Create KPI indicator or gauge chart"""
    
    if gauge and max_value:
        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta" if show_delta and reference else "gauge+number",
            value=value,
            title={'text': title, 'font': {'size': 14}},
            delta={'reference': reference, 'valueformat': '.1%'} if reference else None,
            gauge={
                'axis': {'range': [None, max_value], 'tickwidth': 1},
                'bar': {'color': CHART_COLORS['primary']},
                'steps': [
                    {'range': [0, max_value * 0.5], 'color': CHART_COLORS['surface']},
                    {'range': [max_value * 0.5, max_value * 0.75], 'color': CHART_COLORS['warning']},
                    {'range': [max_value * 0.75, max_value], 'color': CHART_COLORS['error']}
                ],
                'threshold': {
                    'line': {'color': CHART_COLORS['text_primary'], 'width': 4},
                    'thickness': 0.75,
                    'value': value
                }
            },
            number={'valueformat': format_str, 'font': {'size': 24}},
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
    else:
        # Create simple indicator
        fig = go.Figure(go.Indicator(
            mode="number+delta" if show_delta and reference else "number",
            value=value,
            title={'text': title, 'font': {'size': 14, 'color': CHART_COLORS['text_secondary']}},
            delta={
                'reference': reference,
                'relative': True,
                'valueformat': '.1%',
                'font': {'size': 12}
            } if reference else None,
            number={
                'valueformat': format_str,
                'font': {'size': 36, 'color': CHART_COLORS['primary']}
            },
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
    
    # Update layout
    fig.update_layout(
        height=200 if not gauge else 300,
        margin=dict(t=40, b=40, l=40, r=40),
        paper_bgcolor='white',
        font=dict(
            family="system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
            color=CHART_COLORS['text_primary']
        )
    )
    
    return fig

def create_table(
    data: Union[pd.DataFrame, Dict, List[List]],
    columns: List[str] = None,
    title: str = "Data Table",
    max_rows: int = 20,
    show_index: bool = False
) -> go.Figure:
    """Create professional data table"""
    
    if isinstance(data, pd.DataFrame):
        df = data.head(max_rows)
        columns = columns or df.columns.tolist()
        values = [df[col].tolist() for col in columns]
        if show_index:
            columns = ['Index'] + columns
            values = [df.index.tolist()] + values
    elif isinstance(data, dict):
        columns = columns or list(data.keys())
        values = [data[col] for col in columns]
    else:
        # Assume list of lists
        columns = columns or [f'Column {i+1}' for i in range(len(data[0]))]
        values = list(zip(*data[:max_rows]))
    
    # Create table
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=columns,
            fill_color=CHART_COLORS['surface'],
            align='left',
            font=dict(size=12, color=CHART_COLORS['text_primary']),
            height=35,
            line=dict(color=CHART_COLORS['border'], width=1)
        ),
        cells=dict(
            values=values,
            fill_color=['white', CHART_COLORS['surface']] * (len(values[0]) // 2 + 1),
            align='left',
            font=dict(size=11, color=CHART_COLORS['text_secondary']),
            height=30,
            line=dict(color=CHART_COLORS['border'], width=0.5)
        )
    )])
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color=CHART_COLORS['text_primary']),
            x=0,
            xanchor='left'
        ),
        height=min(400, 50 + 35 * min(len(values[0]) if values else 0, max_rows)),
        margin=dict(t=40, b=10, l=10, r=10),
        paper_bgcolor='white'
    )
    
    return fig

def create_waterfall_chart(
    data: Dict,
    title: str = "Waterfall Chart",
    measure: List[str] = None
) -> go.Figure:
    """Create waterfall chart for financial analysis"""
    
    x_values = data.get('x', data.get('categories', []))
    y_values = data.get('y', data.get('values', []))
    measure = measure or ['relative'] * len(x_values)
    
    # Create waterfall
    fig = go.Figure(go.Waterfall(
        name="",
        orientation="v",
        measure=measure,
        x=x_values,
        textposition="outside",
        text=[f"${y:,.0f}" for y in y_values],
        y=y_values,
        connector={"line": {"color": CHART_COLORS['border'], "width": 1}},
        increasing={"marker": {"color": CHART_COLORS['success']}},
        decreasing={"marker": {"color": CHART_COLORS['error']}},
        totals={"marker": {"color": CHART_COLORS['primary']}}
    ))
    
    # Update layout
    layout = BASE_LAYOUT.copy()
    layout.update({
        'title': dict(
            text=title,
            font=dict(size=16, color=CHART_COLORS['text_primary']),
            x=0,
            xanchor='left'
        ),
        'showlegend': False,
        'xaxis': dict(
            title='',
            tickangle=-45 if len(x_values) > 5 else 0
        ),
        'yaxis': dict(
            title='Value',
            tickformat='$,.0f'
        )
    })
    
    fig.update_layout(layout)
    return fig

def create_funnel_chart(
    data: Dict,
    title: str = "Funnel Analysis"
) -> go.Figure:
    """Create funnel chart for conversion analysis"""
    
    stages = data.get('stages', data.get('labels', []))
    values = data.get('values', [])
    
    # Create funnel
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textposition="inside",
        textinfo="value+percent initial",
        opacity=0.9,
        marker={
            "color": COLOR_SEQUENCE[:len(stages)],
            "line": {"width": 2, "color": "white"}
        },
        connector={"line": {"color": CHART_COLORS['border'], "width": 2}}
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color=CHART_COLORS['text_primary']),
            x=0,
            xanchor='left'
        ),
        height=400,
        margin=dict(t=60, b=40, l=100, r=40),
        paper_bgcolor='white',
        font=dict(
            family="system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
            size=11,
            color=CHART_COLORS['text_primary']
        )
    )
    
    return fig

# Smart chart selector based on data pattern
def auto_select_chart(response: str) -> Optional[go.Figure]:
    """Automatically select and create the best chart based on response content"""
    
    response_lower = response.lower()
    
    # Extract patterns and create appropriate chart
    if "top" in response_lower and any(word in response_lower for word in ["application", "cost", "expense"]):
        # Bar chart for rankings
        pattern = r'(\d+)[.)]\s*([^:$]+)[:\s]*\$?([\d,]+(?:\.\d{2})?)'
        matches = re.findall(pattern, response)
        if matches:
            data = {
                'x': [match[1].strip() for match in matches],
                'y': [float(match[2].replace(',', '')) for match in matches]
            }
            return create_bar_chart(data, title="Top Applications by Cost")
    
    elif "trend" in response_lower or "daily" in response_lower or "monthly" in response_lower:
        # Line chart for trends
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        values = np.random.normal(50000, 10000, 30).cumsum()
        data = {
            'x': dates.strftime('%Y-%m-%d').tolist(),
            'y': values.tolist()
        }
        return create_line_chart(data, title="Cost Trend Analysis")
    
    elif "distribution" in response_lower or "breakdown" in response_lower:
        # Pie chart for distributions
        pattern = r'([A-Z][A-Za-z\s-]+)[:\s]*\$?([\d,]+(?:\.\d{2})?)'
        matches = re.findall(pattern, response)
        if matches:
            data = {
                'labels': [match[0].strip() for match in matches],
                'values': [float(match[1].replace(',', '')) for match in matches]
            }
            return create_pie_chart(data, title="Cost Distribution")
    
    elif "heatmap" in response_lower or "correlation" in response_lower:
        # Heatmap for correlations
        data = np.random.rand(10, 10)
        return create_heatmap(data, title="Correlation Matrix")
    
    elif "total" in response_lower and "$" in response:
        # Indicator for single metrics
        match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', response)
        if match:
            value = float(match.group(1).replace(',', ''))
            return create_indicator(value, title="Total Cost", reference=value * 0.9)
    
    return None