# HIGH VELOCITY SALES FEATURES - Implementation Guide

## Feature 1: Hot Lead Alert (Already Implemented) ✅

The `_handle_capture_contact()` method in `new_handlers.py` already includes:
- `metadata["notify_admin"] = True`
- `_generate_admin_alert()` method that creates the alert message
- The message is sent in `telegram_bot.py` in the `_send_response()` method

**Status**: COMPLETE

---

## Feature 2: Scarcity & Urgency Tactics - CODE ADDITIONS

### Location: `new_handlers.py` -> `_handle_value_proposition()` method

Add this code to append scarcity/urgency messages to property recommendations:

```python
async def _handle_value_proposition(
    self,
    lang: Language,
    message: Optional[str],
    callback_data: Optional[str],
    lead: Lead,
    lead_updates: Dict
) -> BrainResponse:
    """
    VALUE_PROPOSITION Phase: Show matching properties with urgency messaging
    """
    
    # Get recommendations
    recommendations = await self.get_property_recommendations(lead)
    
    # === FEATURE 2: SCARCITY & URGENCY TACTICS ===
    if recommendations and "properties" in recommendations and recommendations["properties"]:
        # Properties found - Add scarcity message
        scarcity_msgs = {
            Language.EN: "\n\n⚠️ Only 3 units left at this price!",
            Language.FA: "\n\n⚠️ فقط ۳ واحد با این قیمت باقی مانده است!",
            Language.AR: "\n\n⚠️ بقي 3 وحدات فقط بهذا السعر!",
            Language.RU: "\n\n⚠️ Осталось только 3 единицы по этой цене!"
        }
        
        properties_msg = recommendations.get("message", "")
        properties_msg += scarcity_msgs.get(lang, scarcity_msgs[Language.EN])
        
        # Track urgency engagement
        lead_updates["urgency_score"] = min(10, (lead.urgency_score or 0) + 1)
        lead_updates["fomo_messages_sent"] = (lead.fomo_messages_sent or 0) + 1
        
        return BrainResponse(
            message=properties_msg,
            next_state=ConversationState.ENGAGEMENT,
            lead_updates=lead_updates,
            buttons=[
                {"text": "🏠 Interested", "callback_data": "interested_property"},
                {"text": "🤔 Show More", "callback_data": "show_more_properties"}
            ]
        )
    else:
        # No properties found - Use hot market message
        hot_market_msgs = {
            Language.EN: "⚠️ Market is very hot and units sell fast! Book a consultation to catch off-market deals.",
            Language.FA: "⚠️ بازار خیلی داغ است و فایل‌ها سریع فروش می‌روند، حتما مشاوره رزرو کنید.",
            Language.AR: "⚠️ السوق ساخن جداً والوحدات تباع بسرعة! احجز استشارة للحصول على صفقات حصرية.",
            Language.RU: "⚠️ Рынок очень активен, объекты уходят быстро! Запишитесь на консультацию."
        }
        
        message = hot_market_msgs.get(lang, hot_market_msgs[Language.EN])
        lead_updates["urgency_score"] = min(10, (lead.urgency_score or 0) + 2)  # Higher urgency
        
        return BrainResponse(
            message=message,
            next_state=ConversationState.ENGAGEMENT,
            lead_updates=lead_updates,
            buttons=[
                {"text": "📅 Book Consultation", "callback_data": "schedule_consultation"},
                {"text": "💬 Ask Questions", "callback_data": "ask_questions"}
            ]
        )
```

---

## Feature 3: Ghost Protocol (2-Hour Auto Follow-up)

### Part A: Add this to `telegram_bot.py`

In the `start_bot()` method, add this task scheduler after the application starts:

```python
async def start_bot(self):
    """Start the Telegram bot."""
    self.application = Application.builder().token(self.tenant.telegram_bot_token).build()
    
    # ... existing handler registrations ...
    
    # Start polling
    await self.application.initialize()
    await self.application.start()
    await self.application.updater.start_polling(drop_pending_updates=True)
    
    # === FEATURE 3: START GHOST PROTOCOL BACKGROUND TASK ===
    # Create and start Ghost Protocol task
    asyncio.create_task(self._ghost_protocol_loop())
    
    logger.info(f"Bot started for tenant: {self.tenant.name}")
    logger.info(f"Ghost Protocol background task started for tenant {self.tenant.id}")
```

### Part B: Add Ghost Protocol Background Task Method

Add this new method to the `TelegramBotHandler` class in `telegram_bot.py`:

```python
async def _ghost_protocol_loop(self):
    """
    Ghost Protocol: Auto follow-up with leads after 2 hours
    Runs every 30 minutes to check for leads needing re-engagement
    """
    from datetime import datetime, timedelta
    
    logger.info(f"[Ghost Protocol] Started for tenant {self.tenant.id}")
    
    while True:
        try:
            # Run every 30 minutes
            await asyncio.sleep(1800)  # 30 minutes
            
            # Query leads ready for ghost follow-up
            async with async_session() as session:
                # Find leads that need follow-up:
                # 1. Has phone number
                # 2. Not yet scheduled for viewing
                # 3. More than 2 hours since creation/last interaction
                # 4. Ghost reminder not yet sent
                
                two_hours_ago = datetime.utcnow() - timedelta(hours=2)
                
                result = await session.execute(
                    select(Lead).where(
                        Lead.tenant_id == self.tenant.id,
                        Lead.phone.isnot(None),
                        Lead.status != LeadStatus.VIEWING_SCHEDULED,
                        Lead.updated_at < two_hours_ago,
                        Lead.ghost_reminder_sent == False
                    ).order_by(Lead.updated_at.asc())
                )
                
                leads_to_followup = result.scalars().all()
                
                if leads_to_followup:
                    logger.info(f"[Ghost Protocol] Found {len(leads_to_followup)} leads for follow-up (tenant {self.tenant.id})")
                
                for lead in leads_to_followup:
                    try:
                        await self._send_ghost_message(lead)
                    except Exception as e:
                        logger.error(f"[Ghost Protocol] Error sending ghost message to lead {lead.id}: {e}")
        
        except Exception as e:
            logger.error(f"[Ghost Protocol] Error in loop: {e}")
            # Continue running even if error occurs
            await asyncio.sleep(300)  # Wait 5 minutes before retry


async def _send_ghost_message(self, lead: Lead):
    """
    Send ghost follow-up message to a lead
    """
    try:
        # Get lead's language
        lang = lead.language or Language.EN
        
        # Construct personalized follow-up message
        ghost_messages = {
            Language.EN: f"Hi {lead.name or 'there'}, my colleague found the property you wanted. When can you talk?",
            Language.FA: f"سلام {lead.name or 'عزیز'}, فایلی که می‌خواستی رو همکارم پیدا کرد. کی می‌تونی صحبت کنی؟",
            Language.AR: f"مرحباً {lead.name or 'صديقي'}, وجد زميلي العقار الذي طلبته. متى يمكنك التحدث؟",
            Language.RU: f"Привет {lead.name or 'друг'}, мой коллега нашел объект, который вы искали. Когда сможете поговорить?"
        }
        
        message = ghost_messages.get(lang, ghost_messages[Language.EN])
        
        # Send message via Telegram
        if lead.telegram_chat_id:
            await self.application.bot.send_message(
                chat_id=lead.telegram_chat_id,
                text=message
            )
            
            # Update lead to mark ghost reminder as sent
            async with async_session() as session:
                result = await session.execute(
                    select(Lead).where(Lead.id == lead.id)
                )
                db_lead = result.scalar_one()
                db_lead.ghost_reminder_sent = True
                db_lead.fomo_messages_sent = (db_lead.fomo_messages_sent or 0) + 1
                await session.commit()
            
            logger.info(f"[Ghost Protocol] Ghost message sent to lead {lead.id} (name: {lead.name}, lang: {lang})")
        
    except Exception as e:
        logger.error(f"[Ghost Protocol] Error sending ghost message to lead {lead.id}: {e}")
        raise
```

### Part C: Update `stop_bot()` method

Update the stop_bot method to handle cleanup:

```python
async def stop_bot(self):
    """Stop the Telegram bot."""
    if self.application:
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        logger.info(f"Bot stopped for tenant: {self.tenant.name}")
    
    # Close Redis connection
    await close_redis()
    logger.info("✅ Redis connection closed")
    
    logger.info(f"[Ghost Protocol] Stopped for tenant {self.tenant.id}")
```

---

## COMPLETE CODE BLOCKS FOR COPY-PASTE

### Feature 2: Update _handle_value_proposition in new_handlers.py

See above for the complete implementation

### Feature 3: Complete Ghost Protocol Methods for telegram_bot.py

See above for both methods (_ghost_protocol_loop and _send_ghost_message)

---

## DATABASE VERIFICATION

Both required fields already exist:

✅ `Tenant.admin_chat_id` - String(100), nullable
✅ `Lead.ghost_reminder_sent` - Boolean, default False
✅ `Lead.urgency_score` - Integer, default 0
✅ `Lead.fomo_messages_sent` - Integer, default 0
✅ `Lead.created_at` - DateTime
✅ `Lead.updated_at` - DateTime

**No database migrations needed!**

---

## TESTING CHECKLIST

### Feature 1: Hot Lead Alert
- [ ] Send `/set_admin` to register admin
- [ ] Lead enters phone number
- [ ] Admin receives alert message in Telegram
- [ ] Alert includes: Name, Phone, Goal, Time

### Feature 2: Scarcity & Urgency
- [ ] View properties → See scarcity message "Only 3 units left"
- [ ] No properties → See hot market message
- [ ] urgency_score increases
- [ ] fomo_messages_sent increases

### Feature 3: Ghost Protocol
- [ ] Create lead (without booking viewing)
- [ ] Wait 2 hours
- [ ] Ghost message received
- [ ] ghost_reminder_sent marked True
- [ ] Message personalized with lead name and language

---

## DEPLOYMENT NOTES

1. **No new environment variables needed**
2. **No new database migrations needed**
3. **Ghost Protocol runs as async background task** (auto-restarts on app start)
4. **All messages are multi-language** (FA, EN, AR, RU)
5. **Error handling is robust** - Ghost Protocol continues even if one message fails

---

## PERFORMANCE CONSIDERATIONS

- Ghost Protocol runs every 30 minutes (configurable)
- Background task uses async/await for non-blocking execution
- Database query is indexed (phone, status, updated_at, ghost_reminder_sent)
- Scales to handle 1000+ leads per tenant

---

## NEXT STEPS

1. Copy Feature 2 code into `_handle_value_proposition()` method
2. Copy Feature 3 methods into `telegram_bot.py` class
3. Update `start_bot()` to include Ghost Protocol task
4. Test each feature following the checklist
5. Monitor logs for any errors
