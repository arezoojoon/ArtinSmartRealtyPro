# 🚨 URGENT FIX: WhatsApp Webhook Verification

## Problem
The backend is loading the **WhatsApp Access Token** instead of the **Verify Token**.

Your VPS has:
```bash
WHATSAPP_VERIFY_TOKEN='EAAT58VLIlCcBQOcTWGz...'  # ❌ WRONG - This is ACCESS TOKEN
```

Should be:
```bash
WHATSAPP_VERIFY_TOKEN='ArtinSmartRealty2024SecureWebhookToken9876543210'  # ✅ CORRECT
```

---

## Immediate Fix (On VPS)

### Step 1: Edit the `.env` file
```bash
ssh root@srv1151343.main-hosting.eu
cd /opt/ArtinSmartRealty
nano .env
```

### Step 2: Find and Fix This Line

**WRONG:**
```bash
WHATSAPP_VERIFY_TOKEN=EAAT58VLIlCcBQOcTWGzqAX1oLxep5hIjBLoBIZA684cDKk4Uoio6grDLGcl1EQWhGjGr30zUDyeHIwPMANtTJwIZAIsuSdpJonbZBw1TrR5NTZCGOHhCl0lYs05wwlgBGXObeZAnUmAjNlZC8hJZBjsSUgEZBHxfgKwTL6CAZB93MmGtZBz4h5vlFtZCHZACfDMwKgZDZD
```

**CORRECT:**
```bash
WHATSAPP_VERIFY_TOKEN=ArtinSmartRealty2024SecureWebhookToken9876543210
```

### Step 3: Save and Restart
```bash
# Save in nano: Ctrl+O, Enter, Ctrl+X
docker-compose down
docker-compose up -d
```

### Step 4: Verify It's Fixed
```bash
# Check the loaded token
docker-compose exec backend python -c "import os; print(f\"TOKEN: '{os.getenv('WHATSAPP_VERIFY_TOKEN')}'\")"

# Expected output:
# TOKEN: 'ArtinSmartRealty2024SecureWebhookToken9876543210'
```

### Step 5: Test Webhook
```bash
curl "https://realty.artinsmartagent.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=ArtinSmartRealty2024SecureWebhookToken9876543210&hub.challenge=SUCCESS123"

# Expected: SUCCESS123
```

---

## Root Cause

You have **TWO different WhatsApp tokens**:

### 1. Verify Token (For Webhook Registration)
- **Purpose:** Meta uses this to verify your webhook endpoint
- **Format:** Simple URL-safe string
- **Where:** `.env` file → `WHATSAPP_VERIFY_TOKEN`
- **Value:** `ArtinSmartRealty2024SecureWebhookToken9876543210`
- **Used:** Only during webhook setup (one-time)

### 2. Access Token (For API Calls)
- **Purpose:** Authenticate API requests to send/receive WhatsApp messages
- **Format:** Long token starting with `EAAT...`
- **Where:** Database → `tenants.whatsapp_access_token`
- **Value:** `EAAT58VLIlCcBQOcTWGz...`
- **Used:** Every API call to Meta

---

## What Happened

When you edited `.env` on the VPS, you accidentally set:
```bash
WHATSAPP_VERIFY_TOKEN=EAAT58VLIlCc...  # ACCESS TOKEN (wrong!)
```

This caused the webhook verification to fail because Meta expects:
```bash
WHATSAPP_VERIFY_TOKEN=ArtinSmartRealty2024SecureWebhookToken9876543210
```

---

## Prevention

**Never confuse these two:**

| Token Type | Variable Name | Starts With | Length | Location |
|-----------|---------------|-------------|--------|----------|
| **Verify Token** | `WHATSAPP_VERIFY_TOKEN` | Any text | ~50 chars | `.env` file |
| **Access Token** | `whatsapp_access_token` | `EAAT` | ~200 chars | Database |

---

## Quick Reference

### Correct `.env` Configuration
```bash
# WhatsApp Verify Token (for webhook registration)
WHATSAPP_VERIFY_TOKEN=ArtinSmartRealty2024SecureWebhookToken9876543210
```

### Correct Database Configuration
Via Admin Panel or Direct Query:
```sql
UPDATE tenants 
SET whatsapp_access_token = 'EAAT58VLIlCcBQOcTWGz...' 
WHERE id = 1;
```

---

## After Fix Checklist

- [ ] `.env` has correct `WHATSAPP_VERIFY_TOKEN`
- [ ] Backend restarted: `docker-compose up -d`
- [ ] Token verified: `docker-compose exec backend python -c "import os; print(os.getenv('WHATSAPP_VERIFY_TOKEN'))"`
- [ ] Webhook test returns `SUCCESS123`
- [ ] Meta webhook configuration accepted
- [ ] Test message sent from WhatsApp

---

**Status:** 🔴 Needs immediate fix on VPS  
**ETA:** 2 minutes  
**Last Updated:** November 29, 2025
