# Artin Lead Scraper & Personalizer

**LinkedIn outreach, but smarter**

Built by **Arezoo Mohammadzadegan** at [ArtinSmartAgent](https://www.artinsmartagent.com)

---

## What's This?

You know how LinkedIn outreach is tedious? You find someone interesting, read their profile, check their posts, then stare at a blank message box trying to write something that doesn't sound copy-pasted.

I got tired of that, so I built this Chrome extension. It scrapes LinkedIn profiles (carefully - we don't want to get flagged), sends the data to Google's Gemini AI, and generates personalized icebreaker messages. Plus, it saves everything to a local database so you can export to Excel when you hit LinkedIn's daily message limits.

**📧 Questions?** Email me at info@artinsmartagent.com

---

## What It Does

**The scraping part:**
- Grabs About section, job experience, and recent posts from LinkedIn profiles
- Uses multiple fallback selectors because LinkedIn changes their HTML constantly
- Adds random delays (500-1500ms) so you don't look like a bot

**The AI part:**
- Sends profile data to Google Gemini Pro (completely free, no credit card)
- Uses a Pain-Agitate-Solution framework to write messages that actually sound good
- Generates 75-word icebreakers personalized to what they posted about

**The CRM part:**
- Auto-saves every lead to a SQLite database on your computer
- Extracts emails and phone numbers from About sections
- Export to Excel when you need to reach out via email instead of LinkedIn
- Prevents duplicates - won't save the same person twice

**The practical stuff:**
- Side panel UI that stays out of your way
- Rate limiting (10 messages/min) so LinkedIn doesn't get suspicious
- Everything stored locally - your data stays on your machine

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Chrome Extension (Frontend)            │
│  - Manifest V3                           │
│  - Content Script (DOM Scraping)         │
│  - Popup (Settings)                      │
│  - Side Panel (Main UI)                  │
└─────────────┬───────────────────────────┘
              │
              │ HTTP Request
              │ (Profile Data + Product Description)
              ▼
┌─────────────────────────────────────────┐
│  Backend API (Python/FastAPI)            │
│  - Middleware for OpenAI                 │
│  - Secure API Key Storage                │
│  - Chain of Thought Prompting            │
└─────────────┬───────────────────────────┘
              │
              │ OpenAI API Call
              ▼
┌─────────────────────────────────────────┐
│  OpenAI GPT-4o-mini                      │
│  - PAS Framework                         │
│  - Personalized Message Generation       │
└─────────────────────────────────────────┘
```

---

## How to Install

### What You Need

- Chrome browser (or any Chromium-based browser)
- Python 3.8 or newer
- Google Gemini API key ([grab one here - it's free](https://makersuite.google.com/app/apikey))
- A LinkedIn account

### Step 1: Get the Code

Either clone this repo or download it:

```bash
cd "i:\AI Lead Scraper & Personalize"
```

### Step 2: Backend Setup

Open PowerShell and do this:

```powershell
cd backend

# Make a virtual environment
python -m venv venv

# Turn it on
.\venv\Scripts\Activate.ps1
.\venv\Scripts\Activate.ps1
```

4. Install dependencies:
```powershell
pip install -r requirements.txt
```

5. Create your `.env` file:
```powershell
Copy-Item .env.example .env
```

6. Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

7. Start the backend server:
```powershell
python main.py
```

You should see:
```
🚀 Starting AI Lead Scraper & Personalizer API...
🌐 API will be available at: http://localhost:8000
📚 API docs at: http://localhost:8000/docs
```

### Step 3: Load Chrome Extension

1. Open Chrome and go to `chrome://extensions/`

2. Enable **Developer Mode** (toggle in top-right corner)

3. Click **"Load unpacked"**

4. Select the project root directory: `i:\AI Lead Scraper & Personalize`

5. The extension should now appear in your extensions list! 🎉

### Step 4: Configure Extension

1. Click the extension icon in Chrome toolbar

2. In the popup, enter:
   - **Your Product/Service**: Describe what you sell (e.g., "I sell AI-powered sales automation software")
   - **Backend API Endpoint**: Should be `http://localhost:8000` (default)

3. Click **"Save Settings"**

## 📖 How to Use

### Basic Workflow

1. **Navigate to a LinkedIn Profile**
   - Go to any LinkedIn profile (e.g., `https://linkedin.com/in/someone`)

2. **Open the Side Panel**
   - Click the floating **"🤖 Generate Icebreaker"** button on the LinkedIn page
   - Or click the extension icon and select **"Open Side Panel"**

3. **Scrape Profile Data**
   - In the side panel, click **"🔍 Scrape Profile"**
   - The extension will extract:
     - Name
     - About section
     - Current job position
     - Recent posts/activity (last 3 posts)

4. **Generate Personalized Message**
   - Click **"✨ Generate Personalized Message"**
   - Wait 3-5 seconds for AI to generate your message
   - The message will appear using the Pain-Agitate-Solution framework

5. **Copy & Send**
   - Click **"📋 Copy to Clipboard"**
   - Paste into LinkedIn DM and send!

### Manual Fallback (If Scraping Fails)

If LinkedIn's DOM changes or posts don't load:

1. Click **"✏️ Manual Input (Fallback)"**
2. Manually copy/paste a recent post from the profile
3. Generate message as usual

## 🧠 How the AI Works

### Chain of Thought Prompting

The backend uses a sophisticated system prompt with the **Pain-Agitate-Solution** framework:

```
Hook: Start by genuinely mentioning their recent post (prove you read it)
Bridge: Connect their topic to a problem your product solves
Soft CTA: Ask a low-friction question (e.g., 'Worth a chat?')
```

### Example

**Input:**
- Name: John Doe
- Recent Post: "Just closed a $500k deal but our sales team is drowning in manual data entry..."
- Your Product: "I sell sales automation software"

**Generated Message:**
```
Hey John! Saw your post about closing that massive deal - congrats! 
Manual data entry killing your team's productivity must be brutal at scale. 
We help sales teams automate that busywork so reps can actually sell. 
Worth a quick chat about cutting that admin time by 80%?
```

**Word Count**: 48 words ✅

## 🛡️ Security & Privacy

- ✅ **API keys stored server-side only** (never in extension code)
- ✅ **No data is stored** (stateless API)
- ✅ **HTTPS recommended** for production deployments
- ✅ **CORS configured** to only allow extension requests
- ⚠️ **Never commit `.env` file** to version control

## ⚠️ LinkedIn Detection Prevention

The extension implements several anti-detection measures:

- **Human-like delays** (500-1500ms between DOM reads)
- **Rate limiting** (max 10 requests/minute)
- **No automated navigation** (user must manually visit profiles)
- **Random timing variations** to mimic human behavior

### Best Practices

- Don't scrape more than 10-15 profiles per hour
- Manually navigate between profiles (don't automate clicks)
- Use LinkedIn normally between scrapes
- If you get logged out, wait 24 hours before resuming

## 💰 Cost Estimate

Using **GPT-4o-mini** (extremely cheap):

- **Price**: ~$0.00015 per message
- **1,000 messages**: ~$0.15
- **10,000 messages**: ~$1.50

Compare to manual outreach: priceless! 🚀

## 🐛 Troubleshooting

### Extension Issues

**"Failed to extract profile data"**
- LinkedIn might have changed their DOM structure
- Try the manual input fallback
- Refresh the LinkedIn page and try again

**"Failed to communicate with content script"**
- Reload the extension at `chrome://extensions/`
- Refresh the LinkedIn page

### Backend Issues

**"OpenAI API key not configured"**
- Check your `.env` file exists in `backend/` directory
- Verify `OPENAI_API_KEY` is set correctly
- Restart the backend server

**"Connection refused" errors**
- Make sure backend is running on `http://localhost:8000`
- Check firewall/antivirus isn't blocking the port
- Try accessing `http://localhost:8000` in your browser

### LinkedIn Detection

**Got logged out of LinkedIn**
- You scraped too fast
- Wait 24 hours
- Reduce scraping frequency
- Use more human-like intervals between requests

## 📁 Project Structure

```
i:\AI Lead Scraper & Personalize\
├── manifest.json              # Extension manifest (Manifest V3)
├── background.js              # Service worker (handles API calls)
├── content.js                 # LinkedIn DOM scraper
├── popup.html/js              # Settings popup
├── sidepanel.html/js          # Main UI interface
├── icons/                     # Extension icons
├── backend/
│   ├── main.py                # FastAPI server
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # API keys (gitignored)
│   └── .env.example           # Template for .env
├── .gitignore
└── README.md
```

## 🔧 Development

### Testing the Backend Locally

```powershell
cd backend
python main.py
```

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### Debugging the Extension

1. Go to `chrome://extensions/`
2. Find your extension and click **"Inspect views: service worker"**
3. Open the Console tab to see logs from `background.js`
4. On LinkedIn pages, open DevTools Console to see `content.js` logs

### Modifying the AI Prompt

Edit `backend/main.py` and modify the `system_prompt` variable to change how the AI generates messages.

## 🚀 Production Deployment

For production use:

1. **Deploy backend to a server** (Heroku, AWS, DigitalOcean, etc.)
2. **Use HTTPS** (required for production Chrome extensions)
3. **Update `apiEndpoint`** in extension settings to your production URL
4. **Package extension** for Chrome Web Store (optional)

### Deploy Backend to Heroku (Example)

```bash
# Install Heroku CLI, then:
heroku create your-app-name
heroku config:set OPENAI_API_KEY=your_key_here
git push heroku main
```

Update extension settings to: `https://your-app-name.herokuapp.com`

## 📝 License

This project is for educational/personal use. LinkedIn's Terms of Service prohibit automated scraping - use responsibly and at your own risk.

## 🤝 Contributing

This is a personal project, but feel free to fork and customize!

## 💡 Tips for Best Results

1. **Target profiles with recent activity** - the AI needs posts to work with
2. **Be specific in your product description** - helps the AI make better connections
3. **Review before sending** - AI is smart but not perfect, always read the message
4. **A/B test your product description** - see which descriptions generate better messages
5. **Use on decision-makers** - personalization works best on busy people who get lots of generic DMs

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review browser console logs (F12)
3. Check backend server logs
4. Verify your OpenAI API key is valid and has credits

---

**Built with ❤️ for personalized cold outreach**

Remember: Quality > Quantity. Personalized messages get 5x better response rates than spray-and-pray! 🎯
