# Artin Lead Scraper & Personalizer - Dev Notes

## How This Thing Works

Two main parts:

**Chrome Extension** - The frontend you see in the browser. Lives in the root directory with files like `content.js`, `background.js`, `sidepanel.js`. Scrapes LinkedIn and shows the UI.

**FastAPI Backend** - Python server in the `backend/` folder. Talks to Google's Gemini AI and manages the SQLite database. Runs on localhost:8000.

**The flow:**
1. Extension scrapes a LinkedIn profile (name, job, recent posts)
2. Sends JSON to `localhost:8000/api/generate-message`
3. Backend asks Gemini AI to write a personalized message
4. Saves everything to SQLite (leads_database.db)
5. Returns message to extension, which displays it in the side panel

Pretty straightforward.

## Stuff That'll Bite You If You're Not Careful

### 1. LinkedIn Scraping (content.js)

LinkedIn changes their DOM structure constantly, so I added fallback selectors everywhere. For example, `extractName()` tries 4 different CSS selectors before giving up.

**Anti-detection tricks:**
- `humanDelay(500-1500ms)` between every action (randomized so it looks human)
- Never hardcode delays - always use `CONFIG.DELAYS.*` so it's easy to tune
- Posts require scrolling first because LinkedIn lazy-loads them (`extractRecentPosts()` handles this)

### 2. Message Passing (the Manifest V3 headache)

This one took me way too long to figure out. In Manifest V3, if you have an async message handler in `background.js`, you MUST return `true` or the message channel closes before your async work finishes.

See lines 22, 31, 41 in `background.js` - every async handler has `return true;` at the end. Remove that and watch everything break mysteriously.

Also implemented rate limiting (10 messages/min) in `checkRateLimit()` to avoid spamming the API.

### 3. Security & XSS Prevention
- **Never use `innerHTML`**: All user data uses `.textContent` or HTML escaping (`replace(/</g, '&lt;')`)
- **API keys**: NEVER in extension code - always in `backend/.env` (GEMINI_API_KEY)
- **CORS**: Backend allows `chrome-extension://*` origins (see `main.py` line 25-30)

### 4. CRM Database (database.py)
- **Auto-save**: Every scraped profile automatically saved to SQLite (`leads_database.db`)
- **Duplicate detection**: `linkedin_url` is UNIQUE - returns `{duplicate: true}` if exists
- **Contact extraction**: Regex auto-extracts email/phone from About section (`_extract_email()`, `_extract_phone()`)
- **Excel export**: Uses pandas + openpyxl - triggered via `/api/export-excel` endpoint

## Development Workflows

### Running Backend
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python main.py
# Runs on http://localhost:8000 (uvicorn auto-reload disabled for stability)
```

### Installing New Dependencies
Backend uses `requirements.txt`:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install <package>
pip freeze > requirements.txt  # Update requirements
```

### Testing Extension
1. Load unpacked in Chrome: `chrome://extensions/` → "Load unpacked" → select project root
2. Navigate to LinkedIn profile
3. Click purple floating button "🤖 Generate Icebreaker"
4. Check backend terminal for API calls/errors

### Common Commands
- **Restart backend**: Stop process → `python main.py`
- **Clear database**: Delete `backend/leads_database.db` (auto-recreates on next run)
- **Export leads**: Open CRM Manager (`crm.html`) → click "Export to Excel"

## Key Files & Responsibilities

| File | Purpose | Critical Notes |
|------|---------|----------------|
| `content.js` | LinkedIn DOM scraper | Injects floating button, extracts profile data, 324 lines |
| `background.js` | Service worker | Handles API calls, rate limiting, message passing (108 lines) |
| `sidepanel.js` | Main UI logic | Profile display, message generation, CRM save (260+ lines) |
| `backend/main.py` | FastAPI server | 7 endpoints (generate, save-lead, export-excel, etc.), 326 lines |
| `backend/database.py` | SQLite CRM | LeadsCRM class, auto-save, Excel export (313 lines) |
| `manifest.json` | Extension config | Permissions: activeTab, storage, sidePanel, tabs |

## AI Model Integration

**Google Gemini Pro (FREE tier)**:
- Model: `gemini-pro` (initialized once in `main.py` line 48)
- Prompt: Pain-Agitate-Solution framework (see `main.py` `/api/generate-message`)
- Temperature: 0.8, max_tokens: 200 (Chain of Thought prompting)
- Full prompt includes: name, job title, recent post (300 chars), product description

## Common Pitfalls

1. **Async message handlers without `return true`**: Causes race conditions → messages fail
2. **Hardcoded delays/limits**: Always use `CONFIG` object (anti-pattern: `setTimeout(500)`)
3. **Forgetting MutationObserver cleanup**: Call `observer.disconnect()` in `window.unload` to prevent memory leaks
4. **Backend not running**: Extension will fail silently - always check `http://localhost:8000/api/health`
5. **LinkedIn URL changes**: If scraping breaks, check CSS selectors in `extractName()`, `extractAbout()`, `extractExperience()`

## Extension-Specific Conventions

- **File naming**: `sidepanel.js` (not `sidePanel.js` or `side-panel.js`) - matches Chrome API
- **Error handling**: Always check `chrome.runtime.lastError` after chrome API calls
- **Storage**: Use `chrome.storage.local` (not localStorage) for settings (productDescription, apiEndpoint)
- **Permissions**: `tabs` required for `chrome.tabs.query()` - added in manifest after QA review

## Branding

- **Name**: "Artin Lead Scraper & Personalizer" (not "AI Lead Scraper")
- **Company**: ArtinSmartAgent
- **Developer**: Arezoo Mohammadzadegan
- **Contact**: info@artinsmartagent.com | www.artinsmartagent.com
- All UI text is **English** (backend startup messages are English, not Persian)

## Documentation Structure

- `README.md`: Full setup guide (364 lines)
- `QUICKSTART.md`: 5-minute guide
- `CRM_GUIDE.md`: Database/Excel export usage
- `PUBLISHING_GUIDE.md`: Chrome Web Store submission
- `QA_REPORT.md`: Known bugs and fixes (Persian)
- `ARCHITECTURE.md`: ASCII diagrams
