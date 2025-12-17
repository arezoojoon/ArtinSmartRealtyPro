# 🎉 How to Get FREE Gemini API Key

## Why Gemini?
- ✅ **100% FREE** (no credit card required)
- ✅ **High Limits**: 60 requests per minute (more than OpenAI)
- ✅ **Excellent Quality**: Comparable to GPT-4
- ✅ **No Hidden Costs**: Truly free!

---

## Steps to Get API Key (2 minutes)

### Step 1: Go to Google AI Studio
1. Visit: **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account (Gmail)

### Step 2: Create API Key
1. Click the **"Create API Key"** button (blue)
2. If you don't have a project, click **"Create API key in new project"**
3. Wait 5 seconds for the API Key to be created

### Step 3: Copy the API Key
1. API Key will appear - looks like this:
   ```
   AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
2. Click the **Copy** icon 📋
3. Save it somewhere secure

---

## Install in Project

### Step 1: Edit .env File
Open this file:
```
i:\AI Lead Scraper & Personalize\backend\.env
```

### Step 2: Paste the API Key
Find this line:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

Replace with your actual API Key:
```
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 3: Save
Press `Ctrl + S` and close the file.

---

## Test It

### Method 1: Run Backend
```powershell
cd "i:\AI Lead Scraper & Personalize\backend"
.\venv\Scripts\Activate.ps1
python main.py
```

You should see:
```
🚀 Starting AI Lead Scraper & Personalizer API...
🎉 Powered by Google Gemini (100% FREE!)
🌐 API running at: http://localhost:8000
```

### Method 2: Test API
Open your browser and go to:
```
http://localhost:8000/api/health
```

You should see:
```json
{
  "status": "healthy",
  "gemini_configured": true,
  "model": "gemini-pro (FREE)"
}
```

If you see `gemini_configured: true`, ✅ **Success!**

---

## Free Tier Limits

### Rate Limits (Very Generous!)
- **60 requests per minute** (RPM)
- **1500 requests per day** (RPD)
- For 10-50 LinkedIn messages per day **more than enough!**

### Comparison with OpenAI
| Feature | Gemini Free | OpenAI Free |
|---------|-------------|-------------|
| Price | **FREE** | $0.15 per 1M tokens |
| Rate Limit | 60/min | 3/min |
| Credit Card | ❌ Not required | ✅ Required |
| Quality | GPT-4 level | GPT-4o-mini |

**Conclusion**: Gemini wins! 🏆

---

## Troubleshooting

### Error: "API_KEY_INVALID"
- Copy the API Key again
- Make sure there are no extra spaces or newlines
- Did you save the `.env` file?

### Error: "gemini_configured: false"
- Open the `.env` file
- Check the `GEMINI_API_KEY=...` line
- Restart the backend

### Error: "Rate limit exceeded"
- You sent more than 60 requests in 1 minute
- Wait 1 minute
- Our tool has rate limiting (10 messages/min) so this shouldn't happen

---

## FAQ

### Q: Is Gemini really free?
**A**: Yes! 100% free. Google provides this for developers at no cost.

### Q: Do I need a credit card?
**A**: No! Unlike OpenAI, Gemini doesn't require any credit card.

### Q: Is Gemini quality good?
**A**: Yes! Gemini Pro is equivalent to GPT-4. Works great for LinkedIn messages.

### Q: How many messages can I send per day?
**A**: Up to **1500 messages per day**! More than enough for personal lead generation.

### Q: Can I switch to OpenAI later?
**A**: Yes, our code is modular. Just change `requirements.txt` and `main.py`.

---

## You're Ready! 🚀

After setting up the API Key:

1. ✅ Start the backend: `python main.py`
2. ✅ Open the extension in Chrome
3. ✅ Open LinkedIn
4. ✅ Click "🤖 Generate Icebreaker" button

**Generate your AI messages for free!** 💬✨

---

**Final Note**: If the API Key doesn't work, let me know. I'll help! 🙋‍♂️

