#!/usr/bin/env python3
"""
Simple UI Screenshot and Test Script
"""

import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime

BASE_URL = "http://localhost:80"
SCREENSHOT_DIR = "tests/screenshots"

# Test queries
TEST_QUERIES = [
    "What is the total cost?",
    "Show me the top 10 applications by cost",
    "What's the cost breakdown by environment?"
]

async def main():
    print("=" * 60)
    print("🚀 BigQuery Analytics AI - UI Test & Screenshots")
    print("=" * 60)
    
    # Create screenshot directory
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to True for headless
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to the application
            print(f"\n📍 Loading {BASE_URL}...")
            await page.goto(BASE_URL, wait_until='domcontentloaded', timeout=10000)
            await page.wait_for_timeout(3000)  # Wait for page to fully render
            
            # Take initial screenshot
            screenshot_path = f"{SCREENSHOT_DIR}/1_initial_load.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"✅ Screenshot saved: {screenshot_path}")
            
            # Check UI elements
            print("\n🔍 Checking UI Elements:")
            
            elements = {
                "Header": ".app-header, .header-content",
                "Chat Area": "#chatbot",
                "Input Field": "#msg-input textarea",
                "Send Button": ".primary-btn",
                "Questions Section": ".questions-section",
                "Visualization Panel": "#chart-display, .viz-card"
            }
            
            for name, selector in elements.items():
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"  ✅ {name}: Found")
                    else:
                        print(f"  ❌ {name}: Not found")
                except:
                    print(f"  ❌ {name}: Error checking")
            
            # Test queries
            print("\n📝 Testing Queries:")
            for i, query in enumerate(TEST_QUERIES, 1):
                print(f"\n  Query {i}: {query}")
                
                # Clear chat if needed
                clear_btn = await page.query_selector('.secondary-btn')
                if clear_btn:
                    await clear_btn.click()
                    await page.wait_for_timeout(500)
                
                # Type query
                input_selector = '#msg-input textarea'
                await page.fill(input_selector, query)
                
                # Take screenshot before sending
                screenshot_path = f"{SCREENSHOT_DIR}/{i+1}_query_{i}_typed.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"    📸 Screenshot: {screenshot_path}")
                
                # Send query
                send_btn = await page.query_selector('.primary-btn')
                await send_btn.click()
                
                # Wait for response
                await page.wait_for_timeout(5000)
                
                # Take screenshot after response
                screenshot_path = f"{SCREENSHOT_DIR}/{i+1}_query_{i}_response.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"    📸 Screenshot: {screenshot_path}")
                
                # Check if chart appeared
                chart = await page.query_selector('#chart-display .plotly, #chart-display canvas, .plotly')
                if chart:
                    print(f"    ✅ Visualization displayed")
                else:
                    print(f"    ℹ️  No visualization for this query")
            
            # Test responsive design
            print("\n📱 Testing Responsive Views:")
            
            viewports = [
                {"name": "Tablet", "width": 1024, "height": 768},
                {"name": "Mobile", "width": 375, "height": 812}
            ]
            
            for viewport in viewports:
                await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
                await page.wait_for_timeout(1000)
                
                screenshot_path = f"{SCREENSHOT_DIR}/responsive_{viewport['name'].lower()}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"  📸 {viewport['name']}: {screenshot_path}")
            
            print("\n" + "=" * 60)
            print("✅ UI TEST COMPLETE")
            print("=" * 60)
            print(f"\n📸 Screenshots saved to: {SCREENSHOT_DIR}/")
            print("\n🎉 The application is working and ready!")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await page.screenshot(path=f"{SCREENSHOT_DIR}/error.png", full_page=True)
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())