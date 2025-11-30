# 🔧 VPS Merge Conflict Fix

## Problem
```
error: Your local changes to the following files would be overwritten by merge:
        backend/timeout_scheduler.py
Please commit your changes or stash them before you merge.
```

## Solution - Run These Commands on VPS

### Option 1: Stash Local Changes (RECOMMENDED)
```bash
cd /opt/ArtinSmartRealty

# Save local changes temporarily
git stash

# Pull latest code
git pull origin main

# Apply stashed changes (if you want to keep them)
# git stash pop

# Restart backend
docker-compose restart backend
```

---

### Option 2: Discard Local Changes (Clean Slate)
```bash
cd /opt/ArtinSmartRealty

# Discard all local changes
git reset --hard HEAD

# Pull latest code
git pull origin main

# Restart backend
docker-compose restart backend
```

---

### Option 3: Force Pull (Nuclear Option)
```bash
cd /opt/ArtinSmartRealty

# Fetch latest
git fetch origin main

# Force reset to remote
git reset --hard origin/main

# Restart backend
docker-compose restart backend
```

---

## Verify Deployment

### Check Git Status
```bash
git log --oneline -5
```

**Expected Output:**
```
c00ec42 fix: CRITICAL - Fix infinite loop in VALUE_PROPOSITION + Add consultation nudge + Implement active ghost protocol + Add appointment reminders
86e2d07 fix: Ensure voice response message is never empty
124a8cd fix: Voice acknowledgment safety check
52f99fc fix: OGA to MP3 audio conversion for voice messages
...
```

### Check Files Updated
```bash
git diff 86e2d07..c00ec42 --name-only
```

**Expected Output:**
```
backend/brain.py
backend/timeout_scheduler.py
backend/telegram_bot.py
DEPLOY_CRITICAL_FIXES.md
DEBUG_VOICE_HANDLER.md
DEBUG_VOICE_SILENT.md
FIX_DOCKER_CACHE.md
VPS_DEPLOY_NOW.md
```

---

## Test After Deployment

### Monitor Logs
```bash
docker-compose logs -f backend 2>&1 | grep -E "Ghost Protocol|VALUE_PROPOSITION|consultation|❓|📸|🔔"
```

### Send Test Messages
1. Start conversation: `/start`
2. Complete qualification
3. **Test Question Detection:**
   - Send: "Is the house furnished?"
   - **Expected:** `❓ Question detected from lead X`
   - **Expected:** Bot answers question (NOT "Great! Here are properties...")

4. **Test Photo Request:**
   - Send: "Show me photos"
   - **Expected:** `📸 Photo request detected from lead X`
   - **Expected:** Bot shows property images

5. **Test Consultation Request:**
   - Send: "I want to speak with agent"
   - **Expected:** `🔔 Consultation request detected from lead X`
   - **Expected:** Bot asks for phone number

---

## If Still Having Issues

### Check for Uncommitted Changes
```bash
git status
```

If you see modified files:
```bash
# See what was changed
git diff backend/timeout_scheduler.py

# If changes are important, commit them
git add backend/timeout_scheduler.py
git commit -m "Local VPS changes"
git pull --rebase origin main

# If changes are NOT important, discard them
git checkout -- backend/timeout_scheduler.py
git pull origin main
```

---

## Ghost Protocol Verification

After restart, wait 5 minutes and check:
```bash
docker-compose logs backend 2>&1 | grep "Ghost Protocol"
```

**Expected Output (every 5 minutes):**
```
2025-11-30 XX:XX:XX - timeout_scheduler - INFO - 👻 Ghost Protocol: Checking for inactive users...
```

---

## Common Errors & Fixes

### Error: "Already up to date" but code not updated
```bash
git fetch origin main
git reset --hard origin/main
docker-compose restart backend
```

### Error: "Not a git repository"
```bash
cd /opt/ArtinSmartRealty
git status  # Verify you're in the right directory
```

### Error: Docker compose thread exception (KeyError: 'id')
**This is harmless** - it's a docker-compose logging bug. The bot is still working.
To stop seeing it:
```bash
# Stop following logs
Ctrl+C

# Check logs without following
docker-compose logs backend | tail -50
```

---

## Success Indicators

✅ Git shows commit `c00ec42` as HEAD  
✅ Backend restarted successfully  
✅ Logs show "👻 Ghost Protocol: Checking for inactive users..." every 5 minutes  
✅ Logs show "❓ Question detected" when user asks questions in VALUE_PROPOSITION  
✅ No more infinite "Great! Here are properties..." loops  

---

## Rollback Plan (If Things Break)

```bash
cd /opt/ArtinSmartRealty
git checkout 86e2d07  # Go back to previous commit
docker-compose restart backend
```
