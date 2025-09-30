# UI Visual Testing with Playwright

## Overview

This directory contains Playwright-based visual testing scripts to validate the Gradio chatbot UI and capture screenshots for debugging.

## Setup

### 1. Install Dependencies

```bash
npm install
npx playwright install chromium
```

### 2. Start the Application

**Terminal 1 - Backend:**
```bash
cd genai-agents-backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd gradio-chatbot
python app.py
```

Wait for both services to be ready:
- Backend: http://localhost:8010
- Frontend: http://localhost:7860

## Running Tests

### Visual UI Test

This test validates the UI layout, measures elements, and captures screenshots:

```bash
cd tests
node test_ui_visual.js
```

### What the Test Does

1. **Loads the Frontend** - Opens http://localhost:7860 in Chromium
2. **Takes Screenshots** - Captures full-page screenshots at each step
3. **Measures Layout**:
   - Button positions and sizes
   - Horizontal alignment check
   - Spacing between elements
   - Sidebar width ratio (70:30)
4. **Validates Styles**:
   - Button colors (Send: black, Clear: white outline)
   - Button heights (48px)
   - Border radius (8px)
   - Hover effects
5. **Tests Interactions**:
   - Query button clicks
   - Input population
   - Hover states

### Test Output

The test will:
- Print detailed measurements to console
- Save screenshots to `tests/screenshots/`
- Keep browser open for 10 seconds for manual inspection
- Show ✅/❌ for each validation

### Screenshots Created

- `01_initial_load.png` - Initial page load
- `02_send_hover.png` - Send button hover state
- `03_query_clicked.png` - After clicking a query button
- `error.png` - If any error occurs

## What We're Testing

### Layout Issues

- ✅ **Buttons horizontal** (not stacked vertically)
- ✅ **Proper spacing** (12px gap between elements)
- ✅ **Button heights** (48px each)
- ✅ **Column ratio** (70:30 chat:sidebar)

### Button Issues

- ✅ **Send button** - Black background, white text
- ✅ **Clear button** - White background, black border
- ✅ **Min width** - 100px minimum
- ✅ **Border radius** - 8px rounded corners
- ✅ **Hover effects** - Color change + subtle animation

### Sidebar Issues

- ✅ **Query buttons** - Full width in sidebar
- ✅ **Left alignment** - Text aligned left
- ✅ **Click interaction** - Populates input field
- ✅ **Icon display** - Shows 📋 on right

## Debugging Failed UI

If the test reports issues:

1. **Check Screenshots**
   ```bash
   open tests/screenshots/01_initial_load.png
   ```

2. **Review Console Output**
   - Look for ❌ marks in the output
   - Check measurements (Y coordinates, widths, heights)

3. **Common Issues**:

   **Buttons Stacked:**
   - Check if `gr.Row(elem_id="button-row")` exists
   - Verify buttons have `scale=1` attribute
   - Check CSS `#button-row { gap: 12px }`

   **Wrong Button Sizes:**
   - Verify CSS `.send-btn button { height: 48px; min-width: 100px }`
   - Check for conflicting CSS rules

   **Poor Spacing:**
   - Check `#input-text { margin-bottom: 12px }`
   - Verify `#button-row { gap: 12px }`

## Manual Testing Checklist

After running Playwright tests, manually verify:

- [ ] Page loads without errors
- [ ] Chat area visible and scrollable
- [ ] Input box accepts text
- [ ] Send button works (sends message)
- [ ] Clear button works (clears chat)
- [ ] Query buttons populate input
- [ ] Visualizations appear in sidebar
- [ ] Responsive on different screen sizes

## Fixing Issues

### If Buttons Are Stacked

Edit `gradio-chatbot/app.py` around line 827:

```python
# WRONG - Buttons in Column (stacked)
with gr.Column():
    send_btn = gr.Button("Send")
    clear_btn = gr.Button("Clear")

# RIGHT - Buttons in Row (horizontal)
with gr.Row(elem_id="button-row"):
    send_btn = gr.Button("Send", scale=1)
    clear_btn = gr.Button("Clear", scale=1)
```

### If Spacing Is Wrong

Check CSS around line 510:

```css
#button-row {
    gap: 12px !important;  /* Space between buttons */
    margin-top: 0 !important;
}
```

### If Button Styles Are Wrong

Check CSS around line 516:

```css
.send-btn button {
    background: #1e293b !important;  /* Black */
    height: 48px !important;
    min-width: 100px !important;
}

.clear-btn button {
    background: white !important;  /* White */
    border: 2px solid #1e293b !important;  /* Black border */
}
```

## Advanced Testing

### Different Screen Sizes

Modify `test_ui_visual.js` line 15:

```javascript
// Desktop
viewport: { width: 1920, height: 1080 }

// Laptop
viewport: { width: 1366, height: 768 }

// Tablet
viewport: { width: 768, height: 1024 }

// Mobile
viewport: { width: 375, height: 667 }
```

### Headless Mode

For CI/CD, change line 10:

```javascript
const browser = await chromium.launch({
    headless: true,  // Run without browser UI
    slowMo: 0        // Full speed
});
```

## Troubleshooting

### Playwright Installation Issues

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npx playwright install --force chromium
```

### Port Already in Use

```bash
# Find and kill process on port 7860
lsof -ti:7860 | xargs kill -9

# Find and kill process on port 8010
lsof -ti:8010 | xargs kill -9
```

### Test Timeout

Increase timeout in `test_ui_visual.js`:

```javascript
await page.goto(FRONTEND_URL, {
    waitUntil: 'networkidle',
    timeout: 60000  // 60 seconds
});
```

## CI/CD Integration

Add to `.github/workflows/ui-test.yml`:

```yaml
name: UI Visual Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npx playwright install --with-deps chromium
      - name: Start Backend
        run: cd genai-agents-backend && python app.py &
      - name: Start Frontend
        run: cd gradio-chatbot && python app.py &
      - name: Wait for Services
        run: sleep 10
      - name: Run UI Tests
        run: cd tests && node test_ui_visual.js
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: screenshots
          path: tests/screenshots/
```

## Results Interpretation

### ✅ All Tests Pass

```
✅ ALL VISUAL TESTS PASSED!
The UI looks clean and properly formatted.
```

Your UI is working correctly!

### ❌ Issues Found

```
❌ ISSUES FOUND:
  ❌ Buttons appear stacked (Y diff: 150px, expected <5px)
  ❌ Button heights incorrect (Send: 56px, Clear: 56px, expected: 48px)
```

Follow the "Fixing Issues" section above to resolve problems.

## Support

For issues with testing:
1. Check screenshots in `tests/screenshots/`
2. Review console output for specific errors
3. Verify both services are running
4. Check browser console (press F12 during manual inspection)

For UI design issues:
1. See `FIXES_APPLIED.md` for recent changes
2. Review `gradio-chatbot/app.py` CSS section (lines 455-806)
3. Check component structure (lines 810-860)