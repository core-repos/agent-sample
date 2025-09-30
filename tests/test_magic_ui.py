#!/usr/bin/env python3
"""
Test script to verify Magic UI integration with data visualizations
"""

import sys
from pathlib import Path
import time

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "gradio-chatbot"))

def test_magic_ui_styles():
    """Test that Magic UI styles are properly loaded"""
    magic_css_path = Path(__file__).parent / "gradio-chatbot" / "styles" / "magic-ui.css"
    
    if not magic_css_path.exists():
        print("❌ Magic UI CSS file not found")
        return False
    
    with open(magic_css_path, 'r') as f:
        content = f.read()
        
    # Check for key Magic UI features
    checks = [
        ("--magic-primary", "Magic primary color variable"),
        ("--magic-gradient-primary", "Magic gradient definition"),
        ("glassmorphism", "Glassmorphism effects"),
        (".plotly", "Plotly chart protection styles"),
        ("@keyframes", "Animation definitions"),
    ]
    
    all_passed = True
    for check, description in checks:
        if check.lower() in content.lower():
            print(f"✅ {description} found")
        else:
            print(f"❌ {description} missing")
            all_passed = False
    
    return all_passed

def test_visualization_components():
    """Test that visualization components are intact"""
    from components.charts import (
        create_bar_chart, create_line_chart, create_pie_chart,
        create_indicator, create_heatmap
    )
    
    print("\n📊 Testing visualization components:")
    
    tests = [
        ("Bar Chart", lambda: create_bar_chart({'x': ['A', 'B', 'C'], 'y': [1, 2, 3]}, title="Test Bar")),
        ("Line Chart", lambda: create_line_chart({'x': [1, 2, 3], 'y': [1, 4, 9]}, title="Test Line")),
        ("Pie Chart", lambda: create_pie_chart({'labels': ['A', 'B'], 'values': [60, 40]}, title="Test Pie")),
        ("Indicator", lambda: create_indicator(12345, title="Test KPI")),
        ("Heatmap", lambda: create_heatmap([[1, 2], [3, 4]], ['X1', 'X2'], ['Y1', 'Y2'], title="Test Heat")),
    ]
    
    all_passed = True
    for name, test_func in tests:
        try:
            fig = test_func()
            if fig:
                print(f"✅ {name} created successfully")
            else:
                print(f"❌ {name} returned None")
                all_passed = False
        except Exception as e:
            print(f"❌ {name} failed: {str(e)}")
            all_passed = False
    
    return all_passed

def test_mcp_configuration():
    """Test MCP server configuration"""
    import json
    
    print("\n🔧 Testing MCP configuration:")
    
    mcp_config_path = Path(__file__).parent / ".mcp.json"
    
    if not mcp_config_path.exists():
        print("❌ MCP configuration file not found")
        return False
    
    with open(mcp_config_path, 'r') as f:
        config = json.load(f)
    
    required_servers = ['magic', 'playwright', 'filesystem']
    all_found = True
    
    for server in required_servers:
        if server in config.get('servers', {}):
            print(f"✅ {server.capitalize()} MCP server configured")
        else:
            print(f"❌ {server.capitalize()} MCP server missing")
            all_found = False
    
    return all_found

def main():
    """Run all tests"""
    print("=" * 60)
    print("🎨 Testing Magic UI Integration for BigQuery Analytics AI")
    print("=" * 60)
    
    results = []
    
    # Test 1: Magic UI Styles
    print("\n💅 Testing Magic UI styles:")
    results.append(test_magic_ui_styles())
    
    # Test 2: Visualization Components
    results.append(test_visualization_components())
    
    # Test 3: MCP Configuration
    results.append(test_mcp_configuration())
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    
    if all(results):
        print("✅ All tests passed! Magic UI integration successful.")
        print("\n🚀 To see the enhanced interface, run:")
        print("   cd gradio-chatbot && python app.py")
        print("\n🎨 Magic UI Features:")
        print("   • Glassmorphism effects on all containers")
        print("   • Animated gradient backgrounds")
        print("   • Smooth hover transitions")
        print("   • Magical button effects")
        print("   • Enhanced color palette")
        print("   • Data visualizations preserved")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()