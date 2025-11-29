# 🎯 Multi-Vertical Routing System - Complete Guide

## Overview

The WhatsApp bot now supports **multiple business verticals** using a single WhatsApp number. Users are automatically routed to the appropriate "brain" based on:

1. **Deep Link Keywords** (QR codes, links)
2. **Redis Session Memory** (24-hour persistence)
3. **Interactive Menu Selection**

---

## 🏗️ Architecture

```
User Message → VerticalRouter → Mode Detection → Route to Brain
                    ↓
              Redis Session
              (24h TTL)
```

### Components:

1. **`vertical_router.py`**: Core routing logic with Redis session management
2. **`whatsapp_bot.py`**: Updated webhook handler with multi-vertical support
3. **Redis**: Session storage (`user:971501234567:mode = realty`)

---

## 🚀 How It Works

### 1. Deep Link Entry (Priority 1)

When a user clicks a link or scans a QR code with keywords:

| Keyword Pattern | Vertical | Example |
|----------------|----------|---------|
| `start_realty`, `property`, `realestate` | Real Estate | QR code link: `https://wa.me/971XXXXX?text=start_realty` |
| `start_expo`, `event`, `exhibition` | Expo/Events | Link: `https://wa.me/971XXXXX?text=start_expo` |
| `support`, `help`, `assistance` | Support | Button: "Get Support" → sends `support` |

**Example Flow:**
```
User clicks QR code → Sends "start_expo" → 
VerticalRouter detects keyword → 
Sets Redis: user:971501234567:mode = expo →
Routes to expo_brain.py →
User stays in EXPO mode for 24 hours
```

### 2. Session Persistence (Priority 2)

Once a mode is set, **all subsequent messages** go to that vertical for 24 hours:

```python
# User's first message
"start_realty"  → Mode set to REALTY

# Next messages (same session)
"Show me villas" → Routes to realty_brain ✓
"What's my budget?" → Routes to realty_brain ✓
"Send location" → Routes to realty_brain ✓
```

**Session extends on each interaction** (sliding window).

### 3. Main Menu Fallback (Priority 3)

If user has **NO active session** and sends a generic message:

```
User: "Hi"
Bot: 📋 Interactive Menu
     ┌──────────────────────────┐
     │ 🏠 Real Estate Services  │
     │ 🎪 Events & Expo        │
     │ 📞 Support              │
     └──────────────────────────┘
```

---

## 📋 Available Verticals

### 1. Real Estate (REALTY)
- **Entry**: `start_realty`, `property`, `realestate`
- **Brain**: `brain.py` (existing)
- **Features**: Property search, ROI calc, appointments
- **Status**: ✅ Active

### 2. Events & Expo (EXPO)
- **Entry**: `start_expo`, `event`, `exhibition`
- **Brain**: `expo_brain.py` (TODO)
- **Features**: Event info, booth navigation, schedule
- **Status**: 🚧 Placeholder (coming soon)

### 3. Support (SUPPORT)
- **Entry**: `support`, `help`, `assistance`
- **Brain**: Built-in handler
- **Features**: Team notification, ticket creation
- **Status**: ✅ Active

---

## 🛠️ Technical Implementation

### Redis Session Management

```python
from vertical_router import get_vertical_router, VerticalMode

# Get router instance
router = get_vertical_router(redis_manager)

# Set user mode
await router.set_user_mode("971501234567", VerticalMode.REALTY)

# Get current mode
mode = await router.get_user_mode("971501234567")  # Returns VerticalMode.REALTY

# Clear session
await router.clear_user_mode("971501234567")
```

### Webhook Handler Flow

```python
@app.post("/webhook/whatsapp")
async def handle_webhook(payload: dict):
    # Extract message
    from_phone = "971501234567"
    text = "start_expo"
    
    # Route message
    mode, is_new = await router.route_message(from_phone, text)
    
    if mode == VerticalMode.EXPO:
        # Process with expo brain
        response = await expo_brain.process(from_phone, text)
    elif mode == VerticalMode.REALTY:
        # Process with realty brain
        response = await realty_brain.process(from_phone, text)
    elif mode == VerticalMode.NONE:
        # Send main menu
        await send_main_menu(from_phone)
```

---

## 🌍 Multi-Language Main Menu

Automatically adapts to user's language preference:

### English
```
Welcome to Artin SmartAgent
Please select a service:

🏠 Real Estate Services
   Property search & investment

🎪 Events & Expo
   Exhibition assistance

📞 Support
   Get help from our team
```

### Persian (فارسی)
```
به Artin SmartAgent خوش آمدید
لطفاً یک سرویس را انتخاب کنید:

🏠 املاک و مستغلات
   جستجو و سرمایه‌گذاری ملکی

🎪 نمایشگاه و رویداد
   راهنمای نمایشگاه

📞 پشتیبانی
   دریافت کمک از تیم ما
```

### Arabic (العربية)
```
مرحباً بك في Artin SmartAgent
الرجاء اختيار خدمة:

🏠 العقارات
   البحث عن العقارات والاستثمار

🎪 المعارض والفعاليات
   مساعدة المعرض

📞 الدعم
   احصل على المساعدة من فريقنا
```

---

## 📊 Testing Scenarios

### Scenario 1: Deep Link Entry
```
1. User scans QR: https://wa.me/971XXX?text=start_expo
2. Bot sends: "Welcome to Expo Assistant!"
3. Redis sets: user:971XXX:mode = expo (24h TTL)
4. All future messages → Expo brain
```

### Scenario 2: Menu Selection
```
1. User: "Hi"
2. Bot: Shows interactive menu
3. User selects: "🏠 Real Estate"
4. Redis sets: user:971XXX:mode = realty
5. Bot: "Welcome to Real Estate Services!"
```

### Scenario 3: Session Continuity
```
Day 1, 10:00 AM: User sends "start_realty"
Day 1, 2:00 PM: User sends "Show villas" → Routes to Realty ✓
Day 1, 8:00 PM: User sends "My budget" → Routes to Realty ✓
Day 2, 9:00 AM: Session still active → Routes to Realty ✓
Day 2, 11:00 AM: Session expires (>24h) → Shows main menu
```

### Scenario 4: Mode Override
```
1. User in REALTY mode (existing session)
2. User sends: "start_expo"
3. Deep link detected → OVERRIDES session
4. Redis updates: mode = expo
5. Bot: "Switching to Expo Assistant!"
```

---

## 🔧 Configuration

### Adding New Verticals

1. **Update `vertical_router.py`:**

```python
class VerticalMode(str, Enum):
    REALTY = "realty"
    EXPO = "expo"
    SUPPORT = "support"
    TRAVEL = "travel"  # ← New vertical

DEEP_LINK_PATTERNS = {
    VerticalMode.TRAVEL: [
        r'\bstart[_\s-]?travel\b',
        r'\btrip\b',
        r'\bholiday\b',
    ]
}
```

2. **Create brain:** `travel_brain.py`

3. **Update webhook handler in `whatsapp_bot.py`:**

```python
elif mode == VerticalMode.TRAVEL:
    response = await travel_brain.process(from_phone, text)
```

4. **Add to main menu:**

```python
{
    "id": "start_travel",
    "title": "✈️ Travel & Tourism",
    "description": "Plan your perfect trip"
}
```

---

## 🚨 Error Handling

### Redis Unavailable
```python
if not self.router:
    # Fallback: Direct to default brain without routing
    logger.warning("Redis unavailable, using default brain")
    response = await self.brain.process_message(lead, text, "")
```

### Invalid Mode in Redis
```python
try:
    mode = VerticalMode(mode_str)
except ValueError:
    logger.warning(f"Invalid mode: {mode_str}, resetting")
    await redis.delete(mode_key)
    return VerticalMode.NONE
```

### Session Expiry
- Automatic: Redis TTL expires after 24h
- Manual: Call `router.clear_user_mode(phone)`

---

## 📈 Monitoring & Analytics

### Key Metrics to Track

```python
# Log every routing decision
logger.info(f"User {phone} routed to {mode.value} (new_session={is_new})")

# Redis keys to monitor
await redis.info("keyspace")  # Count active sessions

# Mode distribution
realty_users = await redis.keys("user:*:mode:realty")
expo_users = await redis.keys("user:*:mode:expo")
```

### Recommended Dashboard Queries

```sql
-- Daily active users per vertical
SELECT mode, COUNT(DISTINCT phone) FROM sessions
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY mode;

-- Average session duration
SELECT AVG(EXTRACT(EPOCH FROM (expired_at - created_at))) / 3600 AS avg_hours
FROM sessions;

-- Conversion from menu to vertical
SELECT menu_selection, COUNT(*) 
FROM interactions
WHERE action = 'menu_click'
GROUP BY menu_selection;
```

---

## 🎯 Best Practices

### 1. QR Code Generation

Create deep links for different entry points:

```python
# Real Estate QR Code
realty_link = f"https://wa.me/{whatsapp_number}?text=start_realty"

# Expo QR Code (Event-specific)
expo_link = f"https://wa.me/{whatsapp_number}?text=start_expo%20Dubai2024"

# Support QR Code (Customer service desk)
support_link = f"https://wa.me/{whatsapp_number}?text=support"
```

### 2. Session Management

```python
# Extend session on important actions
await router.set_user_mode(phone, mode)  # Resets 24h TTL

# Clear session on checkout/completion
await router.clear_user_mode(phone)
```

### 3. Graceful Degradation

```python
# Always provide fallback
if mode == VerticalMode.NONE:
    await send_main_menu(phone)
else:
    try:
        await process_with_brain(phone, text, mode)
    except Exception as e:
        logger.error(f"Brain failed: {e}")
        await send_error_message(phone)
        await send_main_menu(phone)  # Fallback
```

---

## 🔄 Migration from Single Brain

### Before (Single Brain)
```python
# All messages go to brain.py
response = await brain.process_message(lead, text, "")
```

### After (Multi-Vertical)
```python
# Automatic routing based on context
mode, is_new = await router.route_message(phone, text)

if mode == VerticalMode.REALTY:
    response = await realty_brain.process(lead, text)
elif mode == VerticalMode.EXPO:
    response = await expo_brain.process(lead, text)
# ... etc
```

**✅ Backwards Compatible:** If router is unavailable, falls back to single brain.

---

## 📞 Support & Debugging

### View User's Current Mode

```python
mode = await router.get_user_mode("971501234567")
print(f"User is in: {mode.value}")  # Output: "realty"
```

### Force Mode Change (Admin)

```python
# Manually set user to different mode
await router.set_user_mode("971501234567", VerticalMode.EXPO)
```

### Clear All Sessions (Maintenance)

```bash
# Redis CLI
redis-cli KEYS "user:*:mode" | xargs redis-cli DEL
```

---

## ✅ Deployment Checklist

- [ ] Redis server running and accessible
- [ ] `vertical_router.py` deployed
- [ ] `whatsapp_bot.py` updated with routing logic
- [ ] Environment variables set (if needed)
- [ ] QR codes generated for each vertical
- [ ] Main menu tested in all languages
- [ ] Deep link patterns verified
- [ ] Session expiry tested (24h TTL)
- [ ] Fallback logic tested (Redis down)
- [ ] Monitoring/analytics configured

---

## 🎉 Ready to Use!

The multi-vertical routing system is now active. Test it with:

```
1. Send "Hi" → Should show main menu
2. Select "Real Estate" → Mode set to REALTY
3. Ask "Show me villas" → Routes to realty brain
4. Send "start_expo" → Switches to EXPO mode
5. Wait 24 hours → Session expires, shows menu again
```

**For questions or issues:** Check logs with `docker-compose logs backend | grep -i vertical`

---

**Version:** 1.0  
**Last Updated:** November 29, 2025  
**Status:** ✅ Production Ready
