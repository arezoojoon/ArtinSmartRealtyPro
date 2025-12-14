# Privacy Policy

**Artin Lead Scraper & Personalizer**

Effective: December 9, 2025  
Last Updated: December 9, 2025

Built by **ArtinSmartAgent** (Arezoo Mohammadzadegan)

**Contact**: info@artinsmartagent.com | [www.artinsmartagent.com](https://www.artinsmartagent.com)

---

## The Short Version

We don't store your data. Seriously. Everything runs locally on your computer, and the only external service we use is Google's Gemini AI (which you control via your own API key).

---

## What Data Gets Collected

**When you scrape a LinkedIn profile, we grab:**
- Profile name
- About section (if they have one)
- Job history (last 2 positions)
- Recent posts (last 3 if available)

**Important stuff to know:**
- This only happens when YOU click "Scrape Profile"
- Data is processed on YOUR computer first
- It gets sent to YOUR backend server (that YOU run)
- We don't have servers - there's nowhere for us to store your data
- The only third party that sees it is Google Gemini (for AI generation)

**What you configure:**
- Your product description (stored in Chrome's local storage)
- Your backend API endpoint (also stored locally)

**What we DON'T collect:**
- Your LinkedIn password (we don't even see it)
- Your cookies or login tokens
- Private messages
- Your connections list
- Emails or phone numbers (unless they're public on the profile)
- Anything from profiles you don't explicitly scrape

---

## How We Use the Data

### Data Processing Flow:
1. **You** click "Scrape Profile" on a LinkedIn page
2. **Extension** extracts public profile data visible on that page
3. **Extension** sends data to YOUR backend API (http://localhost:8000 by default)
4. **Your Backend** sends data to Google Gemini API for AI message generation
5. **Generated message** is returned to the Extension
6. **You** copy and use the message

### Third-Party Services:
- **Google Gemini AI**: We use Google's Gemini API to generate personalized messages. Google's privacy policy applies: https://policies.google.com/privacy
- **Note**: You provide your own Gemini API key, so data is processed under YOUR Google account

---

## Data Storage

### Local Storage (Chrome Extension):
- Product description
- API endpoint URL
- Rate limiting timestamps

**Duration**: Stored until you uninstall the Extension or clear Chrome storage.

### Backend Storage:
- We provide the backend code, but YOU host it
- YOU control what data (if any) is logged or stored
- Default configuration: NO persistent storage (data is processed and discarded)

---

## Data Sharing

We do NOT sell, trade, or share your data with third parties, except:
- **Google Gemini API**: Required for AI message generation (subject to Google's privacy policy)
- **You**: You control your own backend server and can choose to log data

---

## Your Rights

You have the right to:
- ✅ **Access**: View all data stored by the Extension (check Chrome storage)
- ✅ **Delete**: Uninstall the Extension to remove all local data
- ✅ **Control**: Disable the Extension at any time
- ✅ **Transparency**: Review our open-source code

---

## Compliance

### GDPR (EU Users):
- Legal Basis: Consent (you explicitly click "Scrape Profile")
- Data Controller: You (the user) - you control your own backend
- Data Processor: Google Gemini (for AI processing)

### CCPA (California Users):
- We do not sell personal information
- You can request data deletion by uninstalling the Extension

---

## Children's Privacy

This Extension is NOT intended for users under 18 years old. We do not knowingly collect data from children.

---

## Security

- ✅ API keys stored on backend only (never in Extension code)
- ✅ HTTPS recommended for production backend
- ✅ Rate limiting to prevent abuse
- ✅ No cloud storage of scraped data

**Note**: Security of your self-hosted backend is YOUR responsibility.

---

## Changes to This Policy

We may update this Privacy Policy. Changes will be posted with a new "Last Updated" date.

---

## Contact Us

For privacy concerns or questions:
- **Email**: info@artinsmartagent.com
- **Website**: https://www.artinsmartagent.com
- **Company**: ArtinSmartAgent
- **Developer**: Arezoo Mohammadzadegan

---

## Consent

By using Artin Lead Scraper & Personalizer, you consent to this Privacy Policy.

---

**Last Updated**: December 9, 2025  
**Version**: 1.0.0
