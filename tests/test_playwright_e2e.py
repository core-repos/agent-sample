#!/usr/bin/env python3
"""
End-to-End Playwright Tests for BigQuery Analytics AI
Tests all example queries and captures screenshots for UI verification
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright
import json
import time

# Configuration
BASE_URL = "http://localhost:80"
SCREENSHOT_DIR = "tests/screenshots"
LOG_FILE = "tests/test_results.log"

# All example queries from the UI
EXAMPLE_QUERIES = [
    "What is the total cost?",
    "Show me the top 10 applications by cost",
    "What's the cost breakdown by environment?",
    "Display the daily cost trend for last 30 days",
    "Create a heatmap of costs by service",
    "Show waterfall chart of cost components",
    "Generate funnel chart for budget allocation"
]

class TestResults:
    def __init__(self):
        self.results = []
        self.errors = []
        self.warnings = []
        
    def add_result(self, query, success, duration, details=""):
        self.results.append({
            "query": query,
            "success": success,
            "duration": duration,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_error(self, error):
        self.errors.append({
            "error": str(error),
            "timestamp": datetime.now().isoformat()
        })
    
    def save_report(self):
        report = {
            "test_run": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r["success"]),
            "failed": sum(1 for r in self.results if not r["success"]),
            "errors": self.errors,
            "results": self.results
        }
        
        with open(LOG_FILE, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

async def test_query(page, query, index, test_results):
    """Test a single query and capture results"""
    print(f"\n🔍 Testing Query {index + 1}/{len(EXAMPLE_QUERIES)}: {query}")
    start_time = time.time()
    
    try:
        # Clear any existing chat
        clear_button = await page.query_selector('.secondary-btn')
        if clear_button:
            await clear_button.click()
            await page.wait_for_timeout(500)
        
        # Find and fill the input textarea
        input_selector = '#msg-input textarea'
        await page.wait_for_selector(input_selector, timeout=5000)
        await page.fill(input_selector, query)
        
        # Take screenshot before sending
        screenshot_name = f"query_{index + 1}_before.png"
        await page.screenshot(path=f"{SCREENSHOT_DIR}/{screenshot_name}")
        print(f"  📸 Screenshot saved: {screenshot_name}")
        
        # Click send button
        send_button = await page.query_selector('.primary-btn')
        await send_button.click()
        
        # Wait for response (wait for bot message to appear)
        print(f"  ⏳ Waiting for response...")
        await page.wait_for_selector('.message.bot, .bot-message, [data-testid="bot"]', timeout=30000)
        await page.wait_for_timeout(2000)  # Additional wait for chart rendering
        
        # Check if visualization appeared
        chart_element = await page.query_selector('#chart-display .plotly, #chart-display canvas')
        has_chart = chart_element is not None
        
        # Take screenshot after response
        screenshot_name = f"query_{index + 1}_after.png"
        await page.screenshot(path=f"{SCREENSHOT_DIR}/{screenshot_name}", full_page=True)
        print(f"  📸 Screenshot saved: {screenshot_name}")
        
        # Get the response text
        bot_messages = await page.query_selector_all('.message.bot, .bot-message, [data-testid="bot"]')
        response_text = ""
        if bot_messages:
            last_message = bot_messages[-1]
            response_text = await last_message.inner_text()
            print(f"  ✅ Response received: {response_text[:100]}...")
        
        # Check for errors in console
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text()) if msg.type == "error" else None)
        
        duration = time.time() - start_time
        success = bool(response_text) and len(console_errors) == 0
        
        details = f"Chart: {'Yes' if has_chart else 'No'}, Response length: {len(response_text)}"
        if console_errors:
            details += f", Console errors: {console_errors}"
            
        test_results.add_result(query, success, duration, details)
        
        if success:
            print(f"  ✅ Test passed in {duration:.2f}s - {details}")
        else:
            print(f"  ❌ Test failed - {details}")
            
    except Exception as e:
        duration = time.time() - start_time
        test_results.add_result(query, False, duration, str(e))
        test_results.add_error(str(e))
        print(f"  ❌ Error: {e}")
        
        # Capture error screenshot
        try:
            screenshot_name = f"query_{index + 1}_error.png"
            await page.screenshot(path=f"{SCREENSHOT_DIR}/{screenshot_name}", full_page=True)
            print(f"  📸 Error screenshot saved: {screenshot_name}")
        except:
            pass

async def check_ui_elements(page, test_results):
    """Check all UI elements are present and functioning"""
    print("\n🎨 Checking UI Elements...")
    
    ui_checks = {
        "Header": ".app-header",
        "Chat Interface": "#chatbot",
        "Input Field": "#msg-input textarea",
        "Send Button": ".primary-btn",
        "Clear Button": ".secondary-btn",
        "Visualization Panel": "#chart-display",
        "Example Queries": ".example-btn",
        "Expand Button": ".expand-btn"
    }
    
    all_present = True
    for name, selector in ui_checks.items():
        element = await page.query_selector(selector)
        if element:
            print(f"  ✅ {name}: Present")
        else:
            print(f"  ❌ {name}: Missing")
            all_present = False
            test_results.add_error(f"UI element missing: {name} ({selector})")
    
    return all_present

async def check_responsiveness(page, test_results):
    """Test responsive design at different viewport sizes"""
    print("\n📱 Testing Responsive Design...")
    
    viewports = [
        {"name": "Desktop", "width": 1920, "height": 1080},
        {"name": "Tablet", "width": 768, "height": 1024},
        {"name": "Mobile", "width": 375, "height": 667}
    ]
    
    for viewport in viewports:
        await page.set_viewport_size(width=viewport["width"], height=viewport["height"])
        await page.wait_for_timeout(1000)
        
        screenshot_name = f"responsive_{viewport['name'].lower()}.png"
        await page.screenshot(path=f"{SCREENSHOT_DIR}/{screenshot_name}")
        print(f"  📸 {viewport['name']} screenshot: {screenshot_name}")

async def main():
    """Main test runner"""
    print("=" * 60)
    print("🚀 BigQuery Analytics AI - E2E Playwright Tests")
    print("=" * 60)
    
    # Create screenshot directory
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    test_results = TestResults()
    
    async with async_playwright() as p:
        # Launch browser with options for better debugging
        browser = await p.chromium.launch(
            headless=True,  # Set to False to see the browser
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        
        # Enable console logging
        page = await context.new_page()
        
        # Capture console messages
        console_logs = []
        page.on("console", lambda msg: console_logs.append({
            "type": msg.type,
            "text": msg.text(),
            "time": datetime.now().isoformat()
        }))
        
        try:
            # Navigate to the application
            print(f"\n📍 Navigating to {BASE_URL}...")
            await page.goto(BASE_URL, wait_until='networkidle', timeout=30000)
            print("  ✅ Page loaded successfully")
            
            # Take initial screenshot
            await page.screenshot(path=f"{SCREENSHOT_DIR}/initial_load.png", full_page=True)
            print(f"  📸 Initial screenshot saved")
            
            # Check UI elements
            await check_ui_elements(page, test_results)
            
            # Test all example queries
            for i, query in enumerate(EXAMPLE_QUERIES):
                await test_query(page, query, i, test_results)
                await page.wait_for_timeout(2000)  # Wait between queries
            
            # Test responsive design
            await check_responsiveness(page, test_results)
            
            # Check for any console errors
            error_logs = [log for log in console_logs if log["type"] == "error"]
            if error_logs:
                print(f"\n⚠️  Found {len(error_logs)} console errors:")
                for error in error_logs[:5]:  # Show first 5 errors
                    print(f"  - {error['text'][:100]}")
                    test_results.add_error(f"Console error: {error['text']}")
            
            # Save all console logs
            with open(f"{SCREENSHOT_DIR}/console_logs.json", 'w') as f:
                json.dump(console_logs, f, indent=2)
            
        except Exception as e:
            print(f"\n❌ Test execution failed: {e}")
            test_results.add_error(f"Test execution failed: {e}")
            
            # Capture failure screenshot
            try:
                await page.screenshot(path=f"{SCREENSHOT_DIR}/failure.png", full_page=True)
            except:
                pass
        
        finally:
            await browser.close()
    
    # Generate and save test report
    report = test_results.save_report()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {report['total_tests']}")
    print(f"✅ Passed: {report['passed']}")
    print(f"❌ Failed: {report['failed']}")
    print(f"⚠️  Errors: {len(report['errors'])}")
    print(f"\n📁 Results saved to: {LOG_FILE}")
    print(f"📸 Screenshots saved to: {SCREENSHOT_DIR}/")
    
    # Production readiness check
    print("\n" + "=" * 60)
    print("🏁 PRODUCTION READINESS CHECK")
    print("=" * 60)
    
    is_ready = True
    
    if report['failed'] > 0:
        print("❌ Some tests failed - Fix required")
        is_ready = False
    else:
        print("✅ All functional tests passed")
    
    if len(report['errors']) > 0:
        print(f"❌ Found {len(report['errors'])} errors - Review required")
        is_ready = False
    else:
        print("✅ No errors detected")
    
    if report['passed'] == report['total_tests']:
        print("✅ All queries returning responses")
    else:
        print("❌ Some queries not working properly")
        is_ready = False
    
    if is_ready:
        print("\n🎉 APPLICATION IS PRODUCTION READY! 🎉")
    else:
        print("\n⚠️  Application needs fixes before going live")
        print("Review the test results and screenshots for details")
    
    return is_ready

if __name__ == "__main__":
    asyncio.run(main())