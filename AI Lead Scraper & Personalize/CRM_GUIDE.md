# CRM Database Guide

**How to actually use all those leads you're collecting**

---

## Why Do We Even Need This?

Here's the problem: LinkedIn caps you at about 20-30 connection requests or messages per day. Hit that limit and you're done for the day.

But here's the thing - most people put their email or phone in their LinkedIn About section. So I built a CRM that:
- Auto-saves every profile you scrape
- Pulls out emails and phone numbers automatically
- Lets you export everything to Excel
- Gives you multiple ways to reach out without hitting LinkedIn's limits

Basically: scrape 100 profiles today, export to Excel, then send emails or make calls while LinkedIn thinks you're being patient.

---

## What It Does

**Auto-saves everything:**
- Every single profile you scrape gets saved to a SQLite database on your computer
- Won't save duplicates - if you scrape someone twice, it tells you
- Stores: name, email, phone, job title, company, LinkedIn URL, about section, work history, recent posts

**Finds contact info for you:**
- Scans the About section for email addresses (using regex patterns)
- Pulls out phone numbers too (works with different formats)
- No need to manually copy-paste anything

**Excel exports:**
- Click one button, get a formatted .xlsx file
- All your leads with their contact details ready to go
- Import it into whatever CRM you actually use (Salesforce, HubSpot, whatever)

**Tracks your messages:**
- Remembers which leads you've messaged
- Saves the AI-generated messages
- Mark people as "contacted" so you don't double-message them

### 5. **Search & Filter**
- Search by name, company, email, or job title
- Filter leads instantly
- View statistics (total leads, messages sent, etc.)

---

## 🚀 How to Use

### Step 1: Enable CRM (Automatic)
The CRM is enabled by default. Nothing to configure!

### Step 2: Scrape LinkedIn Profiles
1. Navigate to any LinkedIn profile
2. Click the **"🤖 Generate Icebreaker"** button
3. Click **"Scrape Profile"**
4. **Lead is automatically saved** to the database!

### Step 3: View Your Leads
1. Click on the extension icon
2. Click **"📊 Open CRM Manager"**
3. See all your scraped leads in a table

### Step 4: Export to Excel
1. In the CRM Manager, click **"📥 Export to Excel"**
2. Excel file downloads automatically
3. Open in Excel, Google Sheets, or any spreadsheet app

---

## 📁 Database Location

The leads database is stored at:
```
i:\AI Lead Scraper & Personalize\backend\leads_database.db
```

**SQLite Format**: Can be opened with any SQLite browser (e.g., DB Browser for SQLite)

---

## 📊 Database Schema

### `leads` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-increment primary key |
| `name` | TEXT | Full name (e.g., "John Smith") |
| `email` | TEXT | Email address (auto-extracted) |
| `phone` | TEXT | Phone number (auto-extracted) |
| `job_title` | TEXT | Current job title |
| `company` | TEXT | Current company name |
| `linkedin_url` | TEXT | LinkedIn profile URL (unique) |
| `about` | TEXT | About/bio section |
| `location` | TEXT | Location (if available) |
| `experience_json` | TEXT | Full work history (JSON) |
| `recent_posts_json` | TEXT | Recent posts (JSON) |
| `generated_message` | TEXT | AI-generated message |
| `message_sent` | BOOLEAN | Whether message was sent (0/1) |
| `notes` | TEXT | Custom notes (future feature) |
| `created_at` | TIMESTAMP | When lead was added |
| `updated_at` | TIMESTAMP | Last update time |

---

## 🔄 API Endpoints

The backend provides these CRM endpoints:

### 1. Save Lead
```
POST /api/save-lead
```
Automatically called when you scrape a profile.

**Request Body**:
```json
{
  "profileData": {
    "name": "John Smith",
    "about": "Email: john@example.com...",
    "experience": [...],
    "recentPosts": [...],
    "profileUrl": "https://linkedin.com/in/johnsmith"
  },
  "productDescription": "..."
}
```

**Response**:
```json
{
  "success": true,
  "message": "Lead added successfully",
  "lead_id": 123,
  "duplicate": false
}
```

---

### 2. Get All Leads
```
GET /api/leads?limit=1000
```

**Response**:
```json
{
  "leads": [
    {
      "id": 1,
      "name": "John Smith",
      "email": "john@example.com",
      "phone": "+1-555-0123",
      "job_title": "CEO",
      "company": "Tech Corp",
      "linkedin_url": "https://linkedin.com/in/johnsmith",
      "message_sent": false,
      "created_at": "2025-12-09 10:30:00"
    },
    ...
  ]
}
```

---

### 3. Get Statistics
```
GET /api/stats
```

**Response**:
```json
{
  "total_leads": 150,
  "messages_sent": 45,
  "with_email": 120,
  "with_phone": 30
}
```

---

### 4. Export to Excel
```
GET /api/export-excel
```

Downloads an Excel file with all leads.

---

### 5. Update Generated Message
```
POST /api/update-message
```

**Request Body**:
```json
{
  "linkedin_url": "https://linkedin.com/in/johnsmith",
  "message": "Hey John, loved your post about..."
}
```

---

### 6. Mark Message as Sent
```
POST /api/mark-sent
```

**Request Body**:
```json
{
  "linkedin_url": "https://linkedin.com/in/johnsmith"
}
```

---

## 💡 Use Cases

### 1. **Bypass LinkedIn Message Limits**
LinkedIn limits you to:
- **20-30 messages per day** (free account)
- **100-150 messages per day** (Sales Navigator)

**Solution**: 
- Scrape 100+ profiles per day (no limit!)
- Export emails/phones to Excel
- Contact via **email** or **phone** instead!

---

### 2. **Build a Cold Email List**
1. Scrape 500 LinkedIn profiles in your niche
2. Export to Excel
3. Filter for leads with emails (e.g., 300 with emails)
4. Import to email marketing tool (Mailchimp, SendGrid)
5. Send personalized cold emails!

**Advantage**: No LinkedIn restrictions!

---

### 3. **Multi-Channel Outreach**
1. LinkedIn message (20/day)
2. Email outreach (unlimited)
3. Phone calls (for high-value leads)
4. Follow-up tracking in CRM

---

### 4. **Team Collaboration**
1. Export Excel file
2. Share with sales team
3. Each person takes 50 leads
4. Track who contacted whom

---

## 📈 Example Workflow

### Scenario: Finding 100 Real Estate Agents in Dubai

**Day 1**:
1. Search LinkedIn: "Real Estate Manager Dubai"
2. Visit 50 profiles
3. Click "Scrape Profile" on each
4. **Result**: 50 leads in database

**Day 2**:
1. Visit 50 more profiles
2. Scrape each one
3. **Result**: 100 total leads

**Day 3**:
1. Open CRM Manager
2. Click "Export to Excel"
3. **Result**: Excel file with 100 leads

**Day 4**:
1. Filter leads with emails (e.g., 60 have emails)
2. Send personalized cold emails
3. **Result**: No LinkedIn message limits!

**Day 5**:
1. Filter leads with phone numbers (e.g., 20 have phones)
2. Call high-value prospects
3. Mark as "Message Sent" in CRM

---

## 🔒 Privacy & Security

### Data Storage:
- ✅ **Local only**: Database stored on YOUR computer
- ✅ **No cloud**: Data never leaves your machine
- ✅ **You control it**: Backup, delete, export anytime

### GDPR Compliance:
- ✅ Only scrape publicly visible LinkedIn data
- ✅ Don't scrape private messages or hidden data
- ✅ Respect data privacy laws in your country

### Best Practices:
- 🚫 Don't scrape thousands of profiles per day (LinkedIn may flag you)
- ✅ Scrape 20-50 profiles per day (safe limit)
- ✅ Take breaks between scraping sessions
- ✅ Only contact people relevant to your offer

---

## 🐛 Troubleshooting

### Problem 1: "Lead already exists"
**Solution**: This person was scraped before. Database prevents duplicates.

### Problem 2: No email/phone extracted
**Solution**: Not all LinkedIn profiles show contact info publicly. Some leads will have blank emails/phones.

### Problem 3: CRM Manager shows 0 leads
**Solution**: 
1. Check backend is running (`python main.py`)
2. Make sure you've scraped at least 1 profile
3. Click "Refresh Data"

### Problem 4: Excel export fails
**Solution**:
1. Make sure `openpyxl` and `pandas` are installed:
   ```bash
   pip install openpyxl pandas
   ```
2. Check backend terminal for errors

---

## 📊 Excel Export Format

The exported Excel file includes these columns:

| Column | Example |
|--------|---------|
| Name | John Smith |
| Email | john@example.com |
| Phone | +1-555-0123 |
| Job Title | CEO |
| Company | Tech Corp |
| LinkedIn URL | https://linkedin.com/in/johnsmith |
| About | Serial entrepreneur... (500 chars) |
| Generated Message | Hey John, loved your post... (1000 chars) |
| Message Sent | Yes / No |
| Notes | (blank) |
| Added Date | 12/09/2025 |
| Last Updated | 12/09/2025 |

---

## 🎯 Pro Tips

### 1. **Target Specific Industries**
Search LinkedIn for:
- "Software Engineer at Google"
- "Marketing Manager at Startup"
- "Real Estate Agent Dubai"

Then scrape all results → Export → Cold email campaign!

### 2. **Use AI Messages in Emails**
The "Generated Message" column in Excel contains AI-written icebreakers. Copy/paste into your email campaigns!

### 3. **Follow-Up Tracking**
Mark leads as "Message Sent" after contacting them. Filter for "Pending" leads to see who still needs follow-up.

### 4. **Backup Your Database**
Copy `leads_database.db` to Dropbox/Google Drive weekly. Don't lose your hard work!

---

## 📞 Support

For CRM-related questions:
- **Email**: info@artinsmartagent.com
- **Website**: www.artinsmartagent.com
- **Developer**: Arezoo Mohammadzadegan

---

**Enjoy building your lead database! 🚀**
