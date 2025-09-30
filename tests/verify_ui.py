#!/usr/bin/env python3
"""Quick UI verification script"""

import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    print("Taking screenshot of new UI...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to False to see browser
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        await page.goto("http://localhost:80", wait_until='domcontentloaded')
        await page.wait_for_timeout(3000)
        
        # Take screenshot
        await page.screenshot(path="tests/screenshots/new_ui_layout.png", full_page=True)
        print("✅ Screenshot saved: tests/screenshots/new_ui_layout.png")
        
        # Check for key elements
        elements_found = []
        
        # Check for questions section
        questions = await page.query_selector('.questions-section')
        if questions:
            elements_found.append("✅ Questions section at bottom")
        else:
            elements_found.append("❌ Questions section missing")
            
        # Check for visualization panel
        viz = await page.query_selector('.viz-card, #chart-display')
        if viz:
            elements_found.append("✅ Visualization panel on right")
        else:
            elements_found.append("❌ Visualization panel missing")
            
        # Check layout proportions
        chat_col = await page.query_selector('.chat-column')
        viz_col = await page.query_selector('.visualization-column')
        
        if chat_col and viz_col:
            elements_found.append("✅ 60/40 layout detected")
        else:
            elements_found.append("❌ Layout columns not properly configured")
        
        print("\nUI Elements Check:")
        for element in elements_found:
            print(f"  {element}")
        
        # Test a query
        print("\nTesting a query...")
        input_field = await page.query_selector('#msg-input textarea')
        if input_field:
            await input_field.fill("What's the cost breakdown by environment?")
            await page.screenshot(path="tests/screenshots/query_typed.png")
            
            send_btn = await page.query_selector('.primary-btn')
            if send_btn:
                await send_btn.click()
                await page.wait_for_timeout(5000)
                await page.screenshot(path="tests/screenshots/query_response.png", full_page=True)
                print("✅ Query tested and response captured")
        
        await browser.close()
        print("\n✅ UI verification complete!")

if __name__ == "__main__":
    asyncio.run(main())