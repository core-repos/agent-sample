/**
 * Playwright UI Visual Testing and Debugging
 * Tests the Gradio chatbot UI and captures screenshots
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8010';
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:7860';
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function testUI() {
    console.log('🎭 Starting Playwright UI Visual Test\n');

    const browser = await chromium.launch({
        headless: false,  // Show browser to see what's happening
        slowMo: 500       // Slow down actions to see them
    });

    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });

    const page = await context.newPage();

    try {
        // Test 1: Load the page
        console.log('📄 Loading frontend...');
        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);

        // Take full page screenshot
        await page.screenshot({
            path: path.join(SCREENSHOT_DIR, '01_initial_load.png'),
            fullPage: true
        });
        console.log('✅ Screenshot saved: 01_initial_load.png\n');

        // Test 2: Inspect layout structure
        console.log('🔍 Inspecting layout structure...');

        const chatbot = await page.locator('#main-chatbot').count();
        const inputBox = await page.locator('#input-text').count();
        const sendButton = await page.locator('.send-btn button').count();
        const clearButton = await page.locator('.clear-btn button').count();
        const sidebar = await page.locator('#sidebar-container').count();
        const queryButtons = await page.locator('.query-item button').count();

        console.log(`  Chatbot: ${chatbot ? '✅' : '❌'} Found`);
        console.log(`  Input Box: ${inputBox ? '✅' : '❌'} Found`);
        console.log(`  Send Button: ${sendButton ? '✅' : '❌'} Found`);
        console.log(`  Clear Button: ${clearButton ? '✅' : '❌'} Found`);
        console.log(`  Sidebar: ${sidebar ? '✅' : '❌'} Found`);
        console.log(`  Query Buttons: ${queryButtons > 0 ? '✅' : '❌'} Found (${queryButtons})\n`);

        // Test 3: Measure button positions and sizes
        console.log('📏 Measuring button layout...');

        const inputBoxElem = await page.locator('#input-text textarea');
        const sendBtn = await page.locator('.send-btn button');
        const clearBtn = await page.locator('.clear-btn button');

        const inputBounds = await inputBoxElem.boundingBox();
        const sendBounds = await sendBtn.boundingBox();
        const clearBounds = await clearBtn.boundingBox();

        if (inputBounds && sendBounds && clearBounds) {
            console.log(`  Input Box: ${inputBounds.width}px x ${inputBounds.height}px`);
            console.log(`  Send Button: ${sendBounds.width}px x ${sendBounds.height}px at Y=${sendBounds.y}`);
            console.log(`  Clear Button: ${clearBounds.width}px x ${clearBounds.height}px at Y=${clearBounds.y}`);

            // Check if buttons are horizontally aligned
            const heightDiff = Math.abs(sendBounds.y - clearBounds.y);
            const horizontallyAligned = heightDiff < 5;

            console.log(`  Buttons Aligned: ${horizontallyAligned ? '✅' : '❌'} (Y diff: ${heightDiff}px)`);

            // Check spacing
            const spacing = sendBounds.x - (inputBounds.x + inputBounds.width);
            console.log(`  Input-to-Send Spacing: ${spacing.toFixed(1)}px\n`);
        }

        // Test 4: Check button styles
        console.log('🎨 Checking button styles...');

        const sendStyle = await sendBtn.evaluate(el => {
            const computed = window.getComputedStyle(el);
            return {
                background: computed.backgroundColor,
                color: computed.color,
                height: computed.height,
                borderRadius: computed.borderRadius,
                minWidth: computed.minWidth
            };
        });

        const clearStyle = await clearBtn.evaluate(el => {
            const computed = window.getComputedStyle(el);
            return {
                background: computed.backgroundColor,
                color: computed.color,
                height: computed.height,
                borderRadius: computed.borderRadius,
                border: computed.border,
                minWidth: computed.minWidth
            };
        });

        console.log('  Send Button:');
        console.log(`    Background: ${sendStyle.background}`);
        console.log(`    Color: ${sendStyle.color}`);
        console.log(`    Height: ${sendStyle.height}`);
        console.log(`    Border Radius: ${sendStyle.borderRadius}`);
        console.log(`    Min Width: ${sendStyle.minWidth}`);

        console.log('  Clear Button:');
        console.log(`    Background: ${clearStyle.background}`);
        console.log(`    Color: ${clearStyle.color}`);
        console.log(`    Height: ${clearStyle.height}`);
        console.log(`    Border: ${clearStyle.border}`);
        console.log(`    Min Width: ${clearStyle.minWidth}\n`);

        // Test 5: Hover effect
        console.log('🖱️  Testing hover effects...');
        await sendBtn.hover();
        await page.waitForTimeout(500);
        await page.screenshot({
            path: path.join(SCREENSHOT_DIR, '02_send_hover.png'),
            fullPage: true
        });
        console.log('✅ Screenshot saved: 02_send_hover.png\n');

        // Test 6: Click query button
        console.log('🔘 Testing query button click...');
        const firstQueryBtn = page.locator('.query-item button').first();
        await firstQueryBtn.click();
        await page.waitForTimeout(1000);
        await page.screenshot({
            path: path.join(SCREENSHOT_DIR, '03_query_clicked.png'),
            fullPage: true
        });
        console.log('✅ Screenshot saved: 03_query_clicked.png\n');

        // Test 7: Check input value after query click
        const inputValue = await inputBoxElem.inputValue();
        console.log(`  Input Value: "${inputValue}"`);
        console.log(`  Query Populated: ${inputValue.length > 0 ? '✅' : '❌'}\n`);

        // Test 8: Measure sidebar query buttons
        console.log('📋 Checking sidebar query buttons...');
        const queryBtns = await page.locator('.query-item button').all();

        for (let i = 0; i < Math.min(queryBtns.length, 3); i++) {
            const btn = queryBtns[i];
            const bounds = await btn.boundingBox();
            const text = await btn.textContent();

            if (bounds) {
                console.log(`  Button ${i + 1}: "${text.trim()}" - ${bounds.width}px x ${bounds.height}px`);
            }
        }

        // Test 9: Check responsive layout
        console.log('\n📱 Testing responsive layout...');

        const chatColumn = await page.locator('div.gr-column').first().boundingBox();
        const sidebarColumn = await page.locator('#sidebar-container').boundingBox();

        if (chatColumn && sidebarColumn) {
            const chatPercent = (chatColumn.width / 1920 * 100).toFixed(1);
            const sidebarPercent = (sidebarColumn.width / 1920 * 100).toFixed(1);

            console.log(`  Chat Column: ${chatColumn.width}px (${chatPercent}%)`);
            console.log(`  Sidebar: ${sidebarColumn.width}px (${sidebarPercent}%)`);
            console.log(`  Expected Ratio: 70:30 (7:3)`);
            console.log(`  Actual Ratio: ${chatPercent}:${sidebarPercent}\n`);
        }

        // Test 10: Visual regression check
        console.log('🎯 Visual Layout Assessment:');

        const issues = [];

        // Check if buttons are stacked (Y coordinate difference > 50px)
        if (sendBounds && clearBounds) {
            const yDiff = Math.abs(sendBounds.y - clearBounds.y);
            if (yDiff > 50) {
                issues.push(`❌ Buttons appear stacked (Y diff: ${yDiff}px, expected <5px)`);
            } else {
                console.log(`  ✅ Buttons properly horizontal (Y diff: ${yDiff.toFixed(1)}px)`);
            }
        }

        // Check button heights
        if (sendBounds && clearBounds) {
            const expectedHeight = 48;
            const sendHeightOK = Math.abs(sendBounds.height - expectedHeight) < 10;
            const clearHeightOK = Math.abs(clearBounds.height - expectedHeight) < 10;

            if (sendHeightOK && clearHeightOK) {
                console.log(`  ✅ Button heights correct (~48px)`);
            } else {
                issues.push(`❌ Button heights incorrect (Send: ${sendBounds.height}px, Clear: ${clearBounds.height}px, expected: 48px)`);
            }
        }

        // Check sidebar query buttons are full width
        const sidebarWidth = sidebarColumn ? sidebarColumn.width : 0;
        const firstQueryBtnBounds = await firstQueryBtn.boundingBox();

        if (firstQueryBtnBounds) {
            const btnWidthPercent = (firstQueryBtnBounds.width / sidebarWidth * 100);
            if (btnWidthPercent > 85) {
                console.log(`  ✅ Query buttons full-width (${btnWidthPercent.toFixed(1)}% of sidebar)`);
            } else {
                issues.push(`❌ Query buttons not full-width (${btnWidthPercent.toFixed(1)}% of sidebar, expected >85%)`);
            }
        }

        // Final summary
        console.log('\n' + '='.repeat(60));
        if (issues.length === 0) {
            console.log('✅ ALL VISUAL TESTS PASSED!');
            console.log('The UI looks clean and properly formatted.');
        } else {
            console.log('❌ ISSUES FOUND:');
            issues.forEach(issue => console.log(`  ${issue}`));
        }
        console.log('='.repeat(60));

        console.log(`\n📸 Screenshots saved to: ${SCREENSHOT_DIR}`);
        console.log('   - 01_initial_load.png');
        console.log('   - 02_send_hover.png');
        console.log('   - 03_query_clicked.png');

        // Keep browser open for manual inspection
        console.log('\n⏸️  Browser will stay open for 10 seconds for manual inspection...');
        await page.waitForTimeout(10000);

    } catch (error) {
        console.error('❌ Test failed:', error);
        await page.screenshot({
            path: path.join(SCREENSHOT_DIR, 'error.png'),
            fullPage: true
        });
        throw error;
    } finally {
        await browser.close();
    }
}

// Run the test
testUI().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
});