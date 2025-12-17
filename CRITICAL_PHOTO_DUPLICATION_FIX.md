# 🐛 CRITICAL BUG: Duplicate Photos & Repetitive Property Presentation

## Problem Summary

User @Webmaster202 testing bot @samanahmadi_Bot reported:
**"همش هم عکس تکراری میفرستسی"** - Bot keeps sending the same photos repeatedly

### What's Happening:
1. ✅ User asks for properties: "roi بده پرزنت کن معرفی کن ملک رو"
2. ❌ Bot sends 4 photos (BUT 2 are duplicates of each other!)
3. ❌ User complains about duplicate photos  
4. ❌ Bot sends THE SAME 4 PHOTOS AGAIN!
5. ❌ This repeats endlessly - no new properties shown

### Root Causes:

#### 🔴 Bug #1: Database Returns Duplicate Properties
**Location:** `backend/brain.py` line ~2050 `get_real_properties_from_db()`

The database query returns DUPLICATE rows because either:
- Properties were inserted multiple times (SQL script ran 2x?)
- Query doesn't use `DISTINCT` or unique constraint

**Evidence from logs:**
```
🏠 **4 ملک مناسب برای شما:**

1. **Sky Gardens - Marina Heights**  ← Property ID 1
2. **Sky Gardens - Marina Heights**  ← DUPLICATE OF #1!
3. **Business Bay Studio**           ← Property ID 3
4. **Business Bay Studio**           ← DUPLICATE OF #3!
```

#### 🔴 Bug #2: No Property Rotation Logic
**Location:** `backend/brain.py` line 3592 (VALUE_PROPOSITION photo request handling)

Every time user asks for photos/properties, the bot runs:
```python
real_properties = await self.get_real_properties_from_db(lead, limit=5)
```

This ALWAYS returns the same 5 properties (sorted by `is_featured DESC, price ASC`). No tracking of "already shown" properties!

#### 🔴 Bug #3: Not Using Professional Property Presenter
**Location:** `backend/telegram_bot.py` line 706

The code path for `brain.current_properties` → `present_all_properties()` is NEVER triggered because:
- `brain.py` line 3600 sets `media_files` directly in BrainResponse
- Never sets `self.current_properties`
- Professional presenter with Media Groups & ROI PDFs is bypassed!

## Solutions

### ✅ Fix #1: Prevent Duplicate Properties in Database

**File:** `backend/brain.py` around line 2050

```python
async def get_real_properties_from_db(self, lead: Lead, limit: int = 5, offset: int = 0) -> List[Dict]:
    """Get real properties from database with DISTINCT constraint"""
    query = (
        select(TenantProperty)
        .distinct(TenantProperty.id)  # ✅ ADD DISTINCT
        .where(
            TenantProperty.tenant_id == lead.tenant_id,
            TenantProperty.is_available == True,
            TenantProperty.transaction_type == lead.transaction_type or TenantProperty.transaction_type == TransactionType.BUY,
            TenantProperty.property_type == lead.property_type or TenantProperty.property_type == PropertyType.APARTMENT
        )
        .order_by(TenantProperty.is_featured.desc(), TenantProperty.price.asc())
        .limit(limit)
        .offset(offset)  # ✅ ADD OFFSET for pagination
    )
```

### ✅ Fix #2: Track Shown Properties & Rotate

**File:** `backend/brain.py` line ~3592

```python
# Inside VALUE_PROPOSITION handler, photo request detection:

# 2. DETECT PHOTO/IMAGE/PDF REQUEST
photo_keywords = ["photo", "picture", "image", "عکس", "تصویر", "صورة", "pdf", "ملک", "property"]
if any(kw in message_lower for kw in photo_keywords):
    logger.info(f"📸 Photo/PDF/Property request detected from lead {lead.id}")
    
    # ✅ Track already shown properties in conversation_data
    conversation_data = lead.conversation_data or {}
    shown_property_ids = set(conversation_data.get("shown_property_ids", []))
    offset = len(shown_property_ids)  # Skip already shown
    
    # ✅ Get NEXT batch of properties (pagination)
    real_properties = await self.get_real_properties_from_db(lead, limit=3, offset=offset)
    
    if real_properties:
        # ✅ Mark these as shown
        new_ids = [p['id'] for p in real_properties]
        shown_property_ids.update(new_ids)
        conversation_data["shown_property_ids"] = list(shown_property_ids)
        
        logger.info(f"✅ Found {len(real_properties)} NEW properties (total shown: {len(shown_property_ids)})")
        
        # ✅ Use professional presenter instead of inline photos
        self.current_properties = real_properties  # Trigger property_presenter
        
        intro_msg = {
            Language.FA: f"🌟 عالی! {len(real_properties)} ملک جدید برات پیدا کردم.\n\nبا عکس‌های حرفه‌ای، مشخصات کامل و گزارش ROI ارائه می‌کنم...",
            Language.EN: f"🌟 Excellent! Found {len(real_properties)} new properties for you.\n\nPresenting with professional photos, full specs, and ROI reports...",
        }
        
        return BrainResponse(
            message=intro_msg.get(lang, intro_msg[Language.EN]),
            next_state=ConversationState.VALUE_PROPOSITION,
            lead_updates={"conversation_data": conversation_data}  # Save shown IDs
        )
    else:
        # No more properties
        no_more_msg = {
            Language.FA: "✅ تمام املاک موجود رو بهتون نشون دادم!\n\nبرای بازدید کدوم یکی وقت میگیریم؟",
            Language.EN: "✅ I've shown you all available properties!\n\nWhich ones would you like to schedule viewings for?"
        }
        return BrainResponse(
            message=no_more_msg.get(lang, no_more_msg[Language.EN]),
            next_state=ConversationState.VALUE_PROPOSITION,
            buttons=[
                {"text": "📅 رزرو بازدید", "callback_data": "schedule_consultation"}
            ]
        )
```

### ✅ Fix #3: Activate Professional Property Presenter

**File:** `backend/brain.py` line ~3467 (AFFIRMATIVE response in VALUE_PROPOSITION)

```python
# When user says "yes" after financing message:
if is_pure_affirmative:
    logger.info(f"✅ AFFIRMATIVE RESPONSE detected from lead {lead.id}")
    
    # ✅ Query database for properties
    query = select(TenantProperty).where(
        TenantProperty.tenant_id == lead.tenant_id,
        # ❌ REMOVE THIS LINE - column doesn't exist!
        # TenantProperty.is_active == True  
    )
    
    # ✅ Track shown properties
    conversation_data = lead.conversation_data or {}
    shown_ids = set(conversation_data.get("shown_property_ids", []))
    
    if shown_ids:
        query = query.where(TenantProperty.id.notin_(shown_ids))  # Exclude already shown
    
    query = query.order_by(TenantProperty.is_featured.desc(), TenantProperty.price.asc()).limit(3)
    
    result = await session.execute(query)
    properties = result.scalars().all()
    
    properties_list = [convert_property_to_dict(p) for p in properties]
    
    # ✅ UPDATE shown IDs
    shown_ids.update([p['id'] for p in properties_list])
    conversation_data["shown_property_ids"] = list(shown_ids)
    
    # ✅ SET current_properties to trigger professional presenter
    self.current_properties = properties_list[:3]
    
    return BrainResponse(
        message="عالی! بذار براتون املاک رو با جزئیات کامل ارسال کنم...",
        lead_updates={"conversation_data": conversation_data}
    )
```

## Database Cleanup (Production Server)

On `/opt/ArtinSmartRealtyPro`, run these commands to remove duplicate properties:

```bash
# Connect to database
docker exec -i artinrealty-db psql -U postgres -d artinrealty

# Find duplicates
SELECT name, COUNT(*) as count 
FROM tenant_properties 
WHERE tenant_id = 2 
GROUP BY name 
HAVING COUNT(*) > 1;

# Delete duplicates (keep lowest ID for each name)
DELETE FROM tenant_properties
WHERE id NOT IN (
    SELECT MIN(id)
    FROM tenant_properties
    WHERE tenant_id = 2
    GROUP BY name
);

# Verify unique properties
SELECT id, name, bedrooms, price FROM tenant_properties WHERE tenant_id = 2 ORDER BY id;
```

## Testing Checklist

After deploying fixes:

1. ✅ **/start** - Fresh conversation
2. ✅ User asks: **"ملک نشون بده"** 
   - **Expected:** 3 unique properties with Media Groups (up to 10 photos each!)
   - **Expected:** Professional presentation with ROI details
3. ✅ User asks again: **"عکس بیشتر بده"**
   - **Expected:** 3 DIFFERENT properties (next batch)
   - **Expected:** NO duplicates from first batch
4. ✅ User types: **"بله"** (affirmative after financing)
   - **Expected:** Properties sent via `present_all_properties()`
   - **Expected:** ROI PDF option buttons

## Files to Modify

1. **`backend/brain.py`**
   - Line ~2050: Add `DISTINCT` + `offset` to `get_real_properties_from_db()`
   - Line ~3467: Remove `is_active` check, add property rotation
   - Line ~3592: Add shown property tracking + set `self.current_properties`

2. **`backend/property_presenter.py`** 
   - Already has professional presenter - just needs to be triggered!

3. **Production Database** (srv1195426)
   - Remove duplicate property rows

## Deployment Commands

```bash
# On production server
cd /opt/ArtinSmartRealtyPro/ArtinSmartRealty

# Pull latest code
git pull origin main

# Rebuild backend
docker-compose build --no-cache backend
docker-compose up -d backend

# Clean duplicate properties (see SQL above)
docker exec -it artinrealty-db psql -U postgres -d artinrealty

# Monitor logs
docker-compose logs -f backend | grep -E "Found.*properties|current_properties|Presented"
```

## Success Criteria

✅ Each photo request shows **NEW unique properties**  
✅ Properties presented with **Media Groups** (multiple photos per property)  
✅ **ROI PDF** buttons appear for each property  
✅ No duplicate property names in same presentation  
✅ User can browse through ALL 12-14 properties by asking multiple times  
✅ Professional presentation matches `property_presenter.py` flow  

---

**Priority:** 🔴 CRITICAL - Blocks user testing, creates poor UX impression  
**Impact:** Bot appears broken/amateurish instead of professional AI agent  
**Estimated Fix Time:** 30 minutes coding + 10 minutes testing
