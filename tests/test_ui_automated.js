const puppeteer = require('puppeteer');

/**
 * Automated UI test for all example queries
 * Tests the Gradio interface with actual browser automation
 */
async function testAllQueries() {
    const browser = await puppeteer.launch({ 
        headless: true,  // Set to false to see browser
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });
    
    console.log('Opening Gradio app at http://localhost:7860...');
    await page.goto('http://localhost:7860', { waitUntil: 'networkidle2' });
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const queries = [
        "What is the total cost?",
        "Show me the top 10 applications by cost",
        "What's the cost breakdown by environment?",
        "Display the daily cost trend for last 30 days",
        "Create a heatmap of costs by service",
        "Show waterfall chart of cost components",
        "Generate funnel chart for budget allocation"
    ];
    
    console.log('\n========== Testing All Queries ==========\n');
    
    const results = [];
    
    for (let i = 0; i < queries.length; i++) {
        const query = queries[i];
        console.log(`[${i+1}/7] Testing: "${query}"`);
        
        // Clear input and type query
        await page.click('#input-text textarea');
        await page.evaluate(() => document.querySelector('#input-text textarea').value = '');
        await page.type('#input-text textarea', query);
        
        // Send query
        await page.click('.send-btn button');
        
        // Wait for response
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        // Check for errors in chat
        const hasError = await page.evaluate(() => {
            const messages = document.querySelectorAll('.message');
            const lastMessage = messages[messages.length - 1];
            return lastMessage && lastMessage.textContent.includes('Error:');
        });
        
        // Check for chart
        const hasChart = await page.evaluate(() => {
            const chart = document.querySelector('#chart-display .js-plotly-plot');
            return chart !== null;
        });
        
        // Get response text
        const responseText = await page.evaluate(() => {
            const messages = document.querySelectorAll('.message');
            const lastMessage = messages[messages.length - 1];
            return lastMessage ? lastMessage.textContent.substring(0, 100) : '';
        });
        
        const result = {
            query: query,
            success: !hasError,
            hasChart: hasChart,
            response: responseText
        };
        
        results.push(result);
        
        console.log(`   Result: ${hasError ? '❌ ERROR' : '✅ SUCCESS'} | Chart: ${hasChart ? 'Yes' : 'No'}`);
        
        if (!hasError && responseText) {
            console.log(`   Response: ${responseText}...`);
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Summary
    console.log('\n========== Test Summary ==========');
    const successful = results.filter(r => r.success).length;
    const withCharts = results.filter(r => r.hasChart).length;
    
    console.log(`✅ Successful: ${successful}/${queries.length}`);
    console.log(`📊 With Charts: ${withCharts}/${queries.length}`);
    console.log(`❌ Failed: ${queries.length - successful}/${queries.length}`);
    
    if (successful === queries.length) {
        console.log('\n🎉 All tests passed!');
    } else {
        console.log('\n⚠️ Some tests failed');
        const failed = results.filter(r => !r.success);
        failed.forEach(r => {
            console.log(`   - "${r.query}"`);
        });
    }
    
    await browser.close();
    process.exit(successful === queries.length ? 0 : 1);
}

// Run tests
testAllQueries().catch(error => {
    console.error('Test failed:', error);
    process.exit(1);
});