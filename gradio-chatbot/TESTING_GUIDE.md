# Testing Guide - New Minimal UI

## Quick Start

### 1. Application is Already Running
The app should already be running at: **http://localhost:7860**

```bash
# Verify it's running
curl -s http://localhost:7860 >/dev/null && echo "✓ Running" || echo "✗ Not running"
```

### 2. Open in Browser
```bash
open http://localhost:7860
```

---

## What to Check

### ✅ Layout Verification

#### 1. Button Layout (CRITICAL)
**Expected**: Two buttons side-by-side in a row

```
┌──────────────────────────────────────┐
│  [   Send Button   ] [Clear Button]  │
└──────────────────────────────────────┘
```

**NOT** (Old broken behavior):
```
┌──────────────────────────────────────┐
│       [   Send Button   ]            │
│       [  Clear Button   ]            │
└──────────────────────────────────────┘
```

**How to Verify**:
1. Open http://localhost:7860
2. Look below the chat input box
3. You should see TWO buttons HORIZONTALLY
4. Send button should be dark (primary)
5. Clear button should be white with border (secondary)

#### 2. Overall Layout
```
┌─────────────────────────────────────┬─────────────────┐
│ Chat Area (70%)                     │ Sidebar (30%)   │
│                                     │                 │
│ ┌─────────────────────────────────┐ │ 📊 Visualization│
│ │ Chat messages appear here       │ │ [Chart area]    │
│ │                                 │ │                 │
│ │                                 │ │ 💡 Quick Queries│
│ └─────────────────────────────────┘ │ [Button 1]      │
│                                     │ [Button 2]      │
│ Input: Ask a question...            │ [Button 3]      │
│ [   Send   ] [  Clear  ]            │ [Button 4]      │
│                                     │ [Button 5]      │
└─────────────────────────────────────┴─────────────────┘
```

---

## Functional Tests

### Test 1: Basic Query
1. Click "What is the total cost?" quick query button
2. Query should populate input box
3. Click "Send" button
4. Should see response in chat
5. Should see KPI indicator in sidebar

**Expected Result**:
- Response appears in chat
- Chart appears in right sidebar
- Input box clears

### Test 2: Chart Visualization
1. Type: "What are the top 5 applications by cost?"
2. Press Enter or click Send
3. Wait for response

**Expected Result**:
- Bar chart appears in sidebar
- Shows top 5 applications
- Values are properly formatted

### Test 3: Clear Function
1. Send a few queries
2. Click "Clear" button

**Expected Result**:
- Chat history clears
- Input box clears
- Chart area clears

### Test 4: Quick Query Buttons
Test each button in the sidebar:

1. ✓ "What is the total cost?"
2. ✓ "Top 5 applications by cost"
3. ✓ "Cost breakdown by environment"
4. ✓ "Daily cost trend"
5. ✓ "Top cloud providers"

**Expected Result**:
- Each button populates input box
- You can then click Send to execute

---

## Visual Inspection

### Colors Should Be:
- Background: Light gray (#f8f9fa)
- Chat area: White
- Input border: Light gray (#e1e8ed)
- Input border (focus): Blue (#3b82f6)
- Send button: Dark slate (#1e293b)
- Clear button: White with dark border
- Sidebar: White with left border

### Typography Should Be:
- Clean and readable
- No emoji overflow
- Proper spacing
- Professional appearance

### Buttons Should:
- Be equal width
- Have 10px gap between them
- Change color on hover
- Be easily clickable
- Show proper cursor (pointer)

---

## Performance Checks

### Page Load
- **Old version**: ~3-4 seconds
- **New version**: ~1-2 seconds
- Should feel noticeably faster

### Rendering
- No layout shift after initial render
- Buttons don't "jump" or reposition
- Smooth hover transitions

---

## Error Scenarios

### Test 5: Backend Down
1. Stop backend if running
2. Try to send a query

**Expected Result**:
- Error message in chat
- No crash
- App remains functional

### Test 6: Empty Input
1. Click Send with empty input

**Expected Result**:
- Nothing happens (no error)
- Input remains empty

---

## Browser Testing

### Recommended Browsers
- ✓ Chrome (primary)
- ✓ Safari
- ✓ Firefox
- ✓ Edge

### Mobile Responsive
- Layout should adapt on narrow screens
- Buttons might stack on very small screens (expected)

---

## Comparison Test

### Open Both Versions (Optional)
```bash
# Terminal 1: New version (already running)
# Running on port 7860

# Terminal 2: Old version (if you want to compare)
cd /Users/gurukallam/projects/ADK-Agents/gradio-chatbot
cp app.py app.py.new
cp app.py.backup app.py
python app.py  # Will run on port 7861 if 7860 is taken
```

**Compare**:
- Layout quality
- Button positioning
- Load speed
- Overall polish

---

## Developer Tools Inspection

### Chrome DevTools
1. Open DevTools (F12)
2. Inspect button row
3. Check computed styles

**Should see**:
```css
#btn-row {
  display: flex;
  flex-direction: row;
  gap: 10px;
}
```

**Should NOT see**:
- Conflicting display: block
- flex-direction: column
- Complex nested !important rules

---

## Screenshot Checklist

Take screenshots of:
1. ✓ Full page layout
2. ✓ Button row (horizontal)
3. ✓ Chart in sidebar
4. ✓ Chat with response
5. ✓ All 5 quick queries visible

---

## Success Criteria

### Must Have ✅
- [ ] Buttons are horizontal
- [ ] Send button is dark
- [ ] Clear button is outlined
- [ ] Charts display in sidebar
- [ ] Quick queries work
- [ ] No console errors
- [ ] Fast page load

### Nice to Have
- [ ] Smooth animations
- [ ] Clean professional look
- [ ] Mobile responsive
- [ ] No layout shift

---

## Troubleshooting

### Issue: Buttons Still Vertical
**Check**:
1. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
2. Clear browser cache
3. Check DevTools for CSS conflicts
4. Verify correct file is running (not backup)

### Issue: No Charts Showing
**Check**:
1. Backend is running on port 8010
2. Check console for API errors
3. Verify chart_data in response

### Issue: Styles Not Applied
**Check**:
1. CSS is in the correct Blocks() declaration
2. No JavaScript errors blocking render
3. Gradio version is compatible

---

## Rollback Plan

If something is broken:
```bash
cd /Users/gurukallam/projects/ADK-Agents/gradio-chatbot
cp app.py.backup app.py
# Restart the app
```

---

## Report Issues

If you find issues, document:
1. Browser and version
2. Screenshot
3. Console errors
4. Steps to reproduce
5. Expected vs actual behavior

---

## Next Steps After Testing

1. ✓ Verify button layout works
2. ✓ Test all functionality
3. ✓ Check performance
4. Document any issues
5. Consider additional improvements
6. Update documentation
7. Commit changes if successful

---

**Ready to test? Open http://localhost:7860 now!**