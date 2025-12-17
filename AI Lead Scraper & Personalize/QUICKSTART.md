# Quick Start Guide

**Two ways to get started: Easy (1 minute) or Manual (5 minutes)**

---

## 🚀 EASY WAY (Recommended for Lazy People)

Just run our one-click setup script:

```powershell
# Navigate to the folder where you extracted this
cd "path\to\AI Lead Scraper & Personalize"

# Run the magic setup script
.\SETUP.ps1
```

**That's it!** The script will:
- ✅ Check Python installation
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Open browser to get your FREE Gemini API key
- ✅ Create .env file automatically
- ✅ Test the backend
- ✅ Show you what to do next

**Time**: 2-3 minutes (mostly waiting for installs)

Then every day you want to use it:
```powershell
.\quick-start.ps1
```
**Done!** Backend starts automatically.

---

## 📖 MANUAL WAY (If You Want Control)

### What You Need

- Chrome browser
- Python 3.8+ on your computer
- A Google account (for the free Gemini API key)

That's it. No paid subscriptions, no credit card.

---

### Step 1: Get Your Free Gemini API Key

We use Google's Gemini AI (100% free, no credit card):

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with any Google account
3. Click "Create API Key" (blue button)
4. Copy the key (starts with `AIza...`)

The free tier gives you 1,500 requests per day - more than enough!

---

### Step 2: Set Up the Backend

Open PowerShell and run these commands:

```powershell
# Navigate to where you extracted the extension
cd "path\to\AI Lead Scraper & Personalize"

# Go to the backend folder
cd backend

# Create a Python virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install the required packages
pip install -r requirements.txt

# Create your environment file
Copy-Item .env.example .env

# Open it and paste your API key
notepad .env
# Change GEMINI_API_KEY=your_key_here to your actual key

# Start the server
python main.py
```

**Keep this terminal running!** The backend must stay open while you use the extension.

You should see: `Server running on http://localhost:8000` ✅

---

### Step 3: Install Chrome Extension

1. Open Chrome and go to: `chrome://extensions/`
2. Enable **Developer Mode** (toggle in top-right corner)
3. Click **"Load unpacked"** button
4. Select the **root folder** where you extracted this extension (NOT the backend folder)
5. Extension loaded! You'll see the purple icon in your toolbar ✅

---

### Step 4: Configure Extension

1. Click the extension icon in Chrome toolbar (purple icon)
2. Enter your product/service description:
   - Example: "I help real estate agents get more listings with AI-powered marketing"
   - This tells the AI what you're selling
3. API Endpoint: `http://localhost:8000` (should already be set)
4. Click **"Save Settings"**

---

### Step 5: Test It Out!

1. Go to **any LinkedIn profile** in Chrome
2. You'll see a purple **"🤖 Generate Icebreaker"** floating button appear
3. Click it once to open the side panel
4. Click **"🚀 Create Personalized Message"** button
5. Wait 5-10 seconds while the AI:
   - ✅ Scrapes the profile (name, job, about, posts)
   - ✅ Generates a personalized message
   - ✅ Auto-saves the lead to your CRM database
6. Copy the message and send it on LinkedIn! 🎉

**Pro Tip**: If the profile has no recent posts, the AI will automatically use their About section instead. It always works!
---

## 📝 First Time Checklist

- [ ] Python 3.8+ installed
- [ ] Gemini API key obtained (FREE from Google)
- [ ] Backend server running on port 8000
- [ ] Extension loaded in Chrome
- [ ] Product description saved in extension settings
- [ ] Tested on a LinkedIn profile
- [ ] Got your first AI-generated message!

---

## ⚠️ Common Issues

**"API key not configured"**
→ Check `backend/.env` file has your Gemini API key (not OpenAI!)

**"Connection refused" or "Failed to connect"**
→ Make sure backend server is running (`python main.py` or `.\quick-start.ps1`)

**"No recent posts found" message**
→ This is normal! The extension automatically uses their About section instead. No action needed.

**Backend window closed accidentally**
→ Just run `.\quick-start.ps1` again to restart it

**Extension not showing floating button on LinkedIn**
→ Refresh the LinkedIn page. The button appears on profile pages only (not feed/search).

---

## 🎯 Pro Tips

- **Best time to scrape**: Morning 9-11 AM (less LinkedIn traffic)
- **Safe limit**: 100 profiles per day to avoid detection
- **Message length**: Keep under 75 words for better response rates
- **Test descriptions**: Try 2-3 different product descriptions to see what works best
- **Backup your data**: Export CRM to Excel weekly (click "CRM Manager" in extension)

---

## 🚀 Next Level: Automation

Once you have some leads, open the **Automation Dashboard**:

1. Click extension icon → **"🤖 Automation Dashboard"**
2. Send 10 LinkedIn messages per day automatically
3. Prepare email campaigns (bulk CSV export)
4. Prepare WhatsApp campaigns (pre-filled links)

See [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md) for complete automation strategy.

---

## 📖 Full Documentation

- **README.md**: Complete overview and features
- **AUTOMATION_GUIDE.md**: Multi-channel campaign strategy
- **CRM_GUIDE.md**: Database management and Excel export
- **PUBLISHING_GUIDE.md**: How to publish to Chrome Web Store
- **GEMINI_SETUP.md**: Detailed API key setup guide

---

**Need help?** Email: info@artinsmartagent.com | www.artinsmartagent.com
