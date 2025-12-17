# 🚨 DEPLOYMENT NEEDED - Property Presenter Fix

## Issue
Bot keeps asking questions instead of presenting properties with photos. User says "send me pic" repeatedly but gets no images.

## Root Cause
Commit **ce6d83e** (property presenter fix) is in GitHub but **NOT deployed to production server**.

The fix ensures `brain.current_properties` is ALWAYS set before checking if properties were shown before, allowing the property presenter integration in `telegram_bot.py` to work even on repeat requests.

## Deployment Steps

### Option 1: Automated Script (Recommended)
```bash
# SSH to production server
ssh <your_server>

# Navigate to project
cd /opt/ArtinSmartRealtyPro

# Run deployment script
chmod +x DEPLOY_PROPERTY_FIX.sh
./DEPLOY_PROPERTY_FIX.sh
```

### Option 2: Manual Steps
```bash
# SSH to production
ssh <your_server>
cd /opt/ArtinSmartRealtyPro

# Pull latest code
git pull origin main

# Verify commit
git log -1 --oneline  # Should show: ce6d83e Fix: همیشه current_properties را set کن...

# Rebuild backend
docker-compose build --no-cache backend

# Restart all services
docker-compose down
docker-compose up -d

# Monitor logs
docker-compose logs -f backend | grep "🏠"
```

## Testing After Deployment

1. **Open Telegram:** @samanahmadi_Bot (Tenant ID: 2)
2. **Test conversation:**
   ```
   User: hi
   Bot: [greeting]
   
   User: send me properties
   Bot: [text list of properties]
   Bot: 🏠 Property Photo (Media Group with actual photos)
   Bot: [Property caption with specs]
   Bot: 📄 ROI.pdf
   ```

3. **Expected logs:**
   ```
   🏠 Brain has 2 properties to present
   📸 Sending property 1/2: Sky Gardens
   ✅ Media group sent successfully (6 photos)
   📄 Generating ROI PDF for Sky Gardens
   ✅ PDF sent successfully
   ```

4. **Repeat test:**
   ```
   User: show me again
   Bot: [Should NOT repeat text but SHOULD still present with photos]
   ```

## Verification Checklist
- [ ] Commit ce6d83e deployed to production
- [ ] Backend container rebuilt (image has new code)
- [ ] All containers running healthy
- [ ] Test bot shows properties with Media Groups
- [ ] PDF files are sent
- [ ] Repeat property requests still trigger presentation
- [ ] No more "🏠 Property Photo" placeholder captions

## Rollback (if needed)
```bash
cd /opt/ArtinSmartRealtyPro
git reset --hard b24df19  # Previous working commit
docker-compose build --no-cache backend
docker-compose up -d
```

## Files Changed in ce6d83e
- `backend/brain.py` (lines 1810-1830)
  - Moved `self.current_properties = properties[:3]` BEFORE repetition check
  - Now properties presenter always has data even on repeat requests

## What This Fixes
- ✅ Properties now presented with photos on first request
- ✅ Properties still presented with photos on repeat requests
- ✅ No more infinite conversation loop
- ✅ Professional presentation: Photos → Caption → PDF
- ✅ Telegram Media Groups working (up to 10 photos per property)

## Production Server Details
- Docker Compose stack running
- Backend container: `artinrealty-backend`
- Logs show: `INFO: 172.18.0.7:XXXXX` (Docker network IPs)
- Current state: **OLD CODE** (before ce6d83e)
