# End-to-End Testing Checklist

Use this checklist to verify your installation is working correctly.

## ✅ Pre-Flight Checklist

### Backend Setup
- [ ] Python 3.8+ installed (`python --version`)
- [ ] Backend virtual environment created
- [ ] Dependencies installed (`pip list` shows fastapi, openai, etc.)
- [ ] `.env` file exists with valid OpenAI API key
- [ ] Backend server starts without errors
- [ ] Can access `http://localhost:8000` in browser
- [ ] Can access `http://localhost:8000/docs` (Swagger UI)

### Extension Setup
- [ ] Extension loaded in Chrome (`chrome://extensions/`)
- [ ] No errors shown in extension card
- [ ] Extension icon appears in Chrome toolbar
- [ ] Icons display correctly (not broken image)
- [ ] Can open popup by clicking extension icon
- [ ] Can save settings in popup

## 🧪 Test Scenarios

### Test 1: Backend Health Check

**Steps:**
1. Open PowerShell
2. Run: `Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get`

**Expected Result:**
```json
{
  "status": "healthy",
  "openai_configured": true,
  "model": "gpt-4o-mini"
}
```

**Status:** [ ] PASS [ ] FAIL

---

### Test 2: Extension Settings

**Steps:**
1. Click extension icon
2. Enter product description: "I sell AI automation software"
3. Verify API endpoint: `http://localhost:8000`
4. Click "Save Settings"

**Expected Result:**
- Green success message appears
- Settings persist after closing popup

**Status:** [ ] PASS [ ] FAIL

---

### Test 3: Profile Scraping

**Steps:**
1. Go to any LinkedIn profile (e.g., https://linkedin.com/in/williamhgates)
2. Wait for floating button to appear (bottom-right)
3. Click "🤖 Generate Icebreaker" button
4. Side panel opens
5. Click "🔍 Scrape Profile"

**Expected Result:**
- Profile data card appears
- Shows name, about, experience
- Shows recent posts (or warning if none found)

**Status:** [ ] PASS [ ] FAIL

**Notes:** _________________________________

---

### Test 4: Message Generation

**Steps:**
1. After scraping profile (Test 3)
2. Click "✨ Generate Personalized Message"
3. Wait 3-5 seconds

**Expected Result:**
- Loading spinner appears
- Message appears in green box
- Message references profile's recent post
- Message is under 75 words
- Message ends with a question

**Status:** [ ] PASS [ ] FAIL

**Generated Message:**
```
_________________________________________________
_________________________________________________
_________________________________________________
```

**Quality Check:**
- [ ] References their post genuinely
- [ ] Connects to product offering
- [ ] Feels natural, not robotic
- [ ] Under 75 words
- [ ] Ends with low-friction question

---

### Test 5: Manual Input Fallback

**Steps:**
1. Click "✏️ Manual Input (Fallback)"
2. Paste this test post:
   ```
   Just finished Q4 and our sales team hit 120% of quota! 
   But manually tracking all these deals in spreadsheets is killing us.
   We need better pipeline visibility.
   ```
3. Click "✨ Generate Personalized Message"

**Expected Result:**
- Message generated successfully
- References the pipeline/tracking pain point

**Status:** [ ] PASS [ ] FAIL

---

### Test 6: Copy to Clipboard

**Steps:**
1. After generating message (Test 4 or 5)
2. Click "📋 Copy to Clipboard"

**Expected Result:**
- Button text changes to "✅ Copied!"
- Can paste message (Ctrl+V)

**Status:** [ ] PASS [ ] FAIL

---

### Test 7: Multiple Profiles

**Steps:**
1. Navigate to 3 different LinkedIn profiles
2. Scrape each profile
3. Generate message for each

**Expected Results:**
- All 3 scrapes succeed
- All 3 messages generated
- Each message is unique and personalized
- No rate limit errors

**Status:** [ ] PASS [ ] FAIL

**Profiles tested:**
1. _________________________________
2. _________________________________
3. _________________________________

---

### Test 8: Error Handling

**Test 8a: Backend Offline**

**Steps:**
1. Stop backend server (Ctrl+C)
2. Try to generate message

**Expected Result:**
- Error message appears
- Clear indication backend is unreachable

**Status:** [ ] PASS [ ] FAIL

---

**Test 8b: Invalid API Key**

**Steps:**
1. Edit `backend/.env`
2. Change API key to: `OPENAI_API_KEY=invalid_key`
3. Restart backend
4. Try to generate message

**Expected Result:**
- Error message about invalid API key

**Status:** [ ] PASS [ ] FAIL

**Remember to fix:** Reset `.env` with valid key after test!

---

**Test 8c: No Recent Posts**

**Steps:**
1. Find a profile with no recent posts
2. Scrape profile
3. Click "Generate Message"

**Expected Result:**
- Warning message about no posts
- Suggests using manual input
- Manual input option visible

**Status:** [ ] PASS [ ] FAIL

---

### Test 9: Performance Check

**Steps:**
1. Scrape a profile
2. Time how long message generation takes

**Expected Result:**
- Scraping: < 5 seconds
- Message generation: 2-5 seconds
- Total: < 10 seconds

**Measured Times:**
- Scraping: _________ seconds
- Generation: _________ seconds
- Total: _________ seconds

**Status:** [ ] PASS [ ] FAIL

---

### Test 10: Cost Verification

**Steps:**
1. Generate 5 messages
2. Check OpenAI usage dashboard: https://platform.openai.com/usage
3. Verify cost

**Expected Result:**
- ~$0.00075 total (5 messages × $0.00015)
- Token usage: 500-1500 total tokens

**Actual Cost:** $___________
**Actual Tokens:** ___________

**Status:** [ ] PASS [ ] FAIL

---

## 📊 Test Summary

Total Tests: 10
Passed: ___ / 10
Failed: ___ / 10

### Issues Found:
1. _________________________________
2. _________________________________
3. _________________________________

### Notes:
_________________________________
_________________________________
_________________________________

---

## 🚀 Production Readiness

If all tests pass, your system is ready for:

- [ ] Small-scale testing (5-10 profiles/day)
- [ ] Gradual ramp-up (monitor response rates)
- [ ] Cost monitoring (set OpenAI billing alerts)
- [ ] Regular DOM selector updates (as needed)

## ⚠️ Safety Reminders

- Don't scrape more than 10-15 profiles per hour
- Always review messages before sending
- Monitor LinkedIn for detection/logout
- Track API costs to avoid surprises
- Use responsibly and ethically

---

## 📝 Testing Date: ______________

**Tester:** _____________________

**Overall Status:** [ ] READY FOR USE [ ] NEEDS FIXES

**Signature:** _____________________
