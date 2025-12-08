"""
ArtinSmartRealty V2 - Telegram Bot Interface
Handles Telegram API calls and passes everything to brain.py
"""

import os
import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from sqlalchemy.future import select

from database import (
    Tenant, Lead, AgentAvailability, get_tenant_by_bot_token, get_or_create_lead,
    update_lead, ConversationState, book_slot, create_appointment,
    AppointmentType, async_session, Language, get_available_slots, DayOfWeek
)
from brain import Brain, BrainResponse, process_telegram_message, process_voice_message
from redis_manager import redis_manager, init_redis, close_redis
from context_recovery import save_context_to_redis, handle_user_message_with_recovery
from inline_keyboards import edit_message_with_checkmark

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Enable DEBUG logging for telegram library to see all updates
logging.getLogger('telegram').setLevel(logging.DEBUG)
logging.getLogger('telegram.ext').setLevel(logging.DEBUG)


class TelegramBotHandler:
    """
    Telegram Bot Handler - Strict Interface to Brain
    This class ONLY handles Telegram API calls and delegates ALL logic to Brain.
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.brain = Brain(tenant)
        self.application: Optional[Application] = None
    
    async def start_bot(self):
        """Initialize and start the Telegram bot."""
        if not self.tenant.telegram_bot_token:
            logger.error(f"No Telegram token for tenant {self.tenant.id}")
            return
        
        # Initialize Redis for session management
        await init_redis()
        logger.info(f"✅ Redis initialized for tenant {self.tenant.id}")
        
        self.application = Application.builder().token(self.tenant.telegram_bot_token).build()
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CommandHandler("set_admin", self.handle_set_admin))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.application.add_handler(MessageHandler(filters.CONTACT, self.handle_contact))
        
        # Start polling
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        
        # === FEATURE 3: START GHOST PROTOCOL BACKGROUND TASK ===
        # Launch Ghost Protocol background task for lead re-engagement
        asyncio.create_task(self._ghost_protocol_loop())
        
        logger.info(f"Bot started for tenant: {self.tenant.name}")
        logger.info(f"🔄 Ghost Protocol background task started for tenant {self.tenant.id}")
    
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
        logger.info(f"🔄 Ghost Protocol background task stopped for tenant {self.tenant.id}")
    
    def _build_inline_keyboard(self, buttons: List[Dict[str, str]]) -> InlineKeyboardMarkup:
        """Build Telegram inline keyboard from button list."""
        keyboard = []
        row = []
        
        for i, btn in enumerate(buttons):
            row.append(InlineKeyboardButton(
                text=btn["text"],
                callback_data=btn["callback_data"]
            ))
            
            # 2 buttons per row, except for budget which gets 1 per row
            if len(row) == 2 or "budget" in btn["callback_data"]:
                keyboard.append(row)
                row = []
        
        if row:  # Add remaining buttons
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _get_or_create_lead(self, update: Update) -> Lead:
        """Get or create lead from Telegram update."""
        user = update.effective_user
        chat_id = str(update.effective_chat.id)
        username = user.username if user else None
        
        lead = await get_or_create_lead(
            tenant_id=self.tenant.id,
            telegram_chat_id=chat_id,
            telegram_username=username
        )
        
        # Update name if available and not set
        if user and not lead.name:
            name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            if name:
                await update_lead(lead.id, name=name)
                lead.name = name
        
        return lead
    
    async def _send_response(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        response: BrainResponse,
        lead: Lead
    ):
        """Send Brain response to user via Telegram."""
        from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
        
        chat_id = update.effective_chat.id
        
        # DEBUG: Log response details
        logger.info(f"🔍 _send_response - Lead {lead.id}: buttons={len(response.buttons) if response.buttons else 0}, request_contact={response.request_contact}, message_len={len(response.message)}")
        
        # Prepare keyboard
        reply_markup = None
        
        # Priority 1: Contact request button (ReplyKeyboard)
        if response.request_contact:
            button_text = {
                Language.EN: "📱 Share Phone Number",
                Language.FA: "📱 اشتراک‌گذاری شماره تلفن",
                Language.AR: "📱 شارك رقم الهاتف",
                Language.RU: "📱 Поделиться номером"
            }.get(lead.language, "📱 Share Phone Number")
            
            contact_button = KeyboardButton(button_text, request_contact=True)
            reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
            logger.info(f"📱 Showing contact request button for lead {lead.id}")
        
        # Priority 2: Inline buttons
        elif response.buttons:
            logger.info(f"🔘 Building keyboard with {len(response.buttons)} buttons: {[b['text'] for b in response.buttons]}")
            reply_markup = self._build_inline_keyboard(response.buttons)
        
        # Send message
        if update.callback_query:
            # Edit existing message for callback queries
            try:
                await update.callback_query.edit_message_text(
                    text=response.message,
                    reply_markup=reply_markup if not response.request_contact else None,  # Can't use ReplyKeyboard with edit
                    parse_mode='HTML'
                )
                # Send contact request as new message if needed
                if response.request_contact:
                    button_text = {
                        Language.EN: "📱 Share Phone Number",
                        Language.FA: "📱 اشتراک‌گذاری شماره تلفن",
                        Language.AR: "📱 شارك رقم الهاتف",
                        Language.RU: "📱 Поделиться номером"
                    }.get(lead.language, "📱 Share Phone Number")
                    contact_button = KeyboardButton(button_text, request_contact=True)
                    reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="👇",
                        reply_markup=reply_markup
                    )
            except Exception:
                # If edit fails, send new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=response.message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=response.message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        # Update lead state if needed
        updates = response.lead_updates or {}
        if response.next_state:
            updates["conversation_state"] = response.next_state
        
        logger.info(f"💾 Saving updates for Lead {lead.id}: {updates}")
        
        if updates:
            await update_lead(lead.id, **updates)
            logger.info(f"✅ Lead {lead.id} updated successfully")
        
        # Handle PDF delivery if metadata flag is set
        send_pdf = False
        if response.metadata and response.metadata.get("send_pdf"):
            send_pdf = True
        elif response.should_generate_roi:
            send_pdf = True
        
        if send_pdf:
            try:
                from roi_engine import generate_roi_pdf
                from io import BytesIO
                
                lang = lead.language or Language.EN
                
                # Send "Preparing..." message first
                preparing_msgs = {
                    Language.EN: "📊 Preparing your personalized ROI report... This will take just a moment!",
                    Language.FA: "📊 در حال آماده‌سازی گزارش ROI شخصی‌سازی شده... چند لحظه صبر کنید!",
                    Language.AR: "📊 جاري تحضير تقرير العائد على الاستثمار الشخصي... سيستغرق لحظات فقط!",
                    Language.RU: "📊 Готовлю персональный отчёт ROI... Это займёт всего мгновение!"
                }
                
                # Determine chat context
                if update.message:
                    chat_id = update.message.chat_id
                elif update.callback_query:
                    chat_id = update.callback_query.message.chat_id
                else:
                    logger.error("No valid chat context for ROI PDF")
                    return
                
                # Send preparing message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=preparing_msgs.get(lang, preparing_msgs[Language.EN])
                )
                
                # Generate PDF
                pdf_bytes = await generate_roi_pdf(
                    tenant=self.tenant,
                    lead=lead,
                    property_value=lead.budget_max or lead.budget_min
                )
                
                # Send PDF as document
                pdf_file = BytesIO(pdf_bytes)
                pdf_file.name = f"roi_analysis_{lead.id}.pdf"
                
                caption_map = {
                    Language.EN: "📊 Here's your personalized ROI Analysis Report!",
                    Language.FA: "📊 این هم گزارش تحلیل سود سرمایه‌گذاری شما!",
                    Language.AR: "📊 إليك تقرير تحليل العائد على الاستثمار الشخصي!",
                    Language.RU: "📊 Вот ваш персональный отчёт ROI!"
                }
                
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=pdf_file,
                    filename=f"ROI_Analysis_{self.tenant.name}.pdf",
                    caption=caption_map.get(lang, caption_map[Language.EN])
                )
                
            except Exception as e:
                logger.error(f"Failed to generate ROI PDF: {e}")
                import traceback
                traceback.print_exc()
                # Don't fail the whole message if PDF generation fails
        
        # === NEW: Handle admin notifications for hot leads ===
        if response.metadata and response.metadata.get("notify_admin"):
            admin_chat_id = self.tenant.admin_chat_id
            
            if admin_chat_id:
                try:
                    admin_message = response.metadata.get("admin_message", "🚨 New hot lead!")
                    await context.bot.send_message(
                        chat_id=admin_chat_id,
                        text=admin_message,
                        parse_mode='HTML'
                    )
                    logger.info(f"🚨 Admin notification sent to {admin_chat_id} for lead {lead.id}")
                except Exception as e:
                    logger.error(f"❌ Failed to notify admin ({admin_chat_id}): {e}")
            else:
                logger.warning(f"⚠️ Admin ID not set for tenant {self.tenant.id}. Use /set_admin to configure.")
        # ===================================================
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        lead = await self._get_or_create_lead(update)
        
        logger.info(f"🔄 /start command - Lead {lead.id}: Before reset - state={lead.conversation_state}, lang={lead.language}")
        
        # Reset conversation state AND conversation data for fresh start
        await update_lead(
            lead.id, 
            conversation_state=ConversationState.START,
            conversation_data={},  # Clear all previous conversation data
            filled_slots={},  # Clear all filled slots
            pending_slot=None  # Clear pending slot
        )
        # CRITICAL: Update lead object in memory too!
        lead.conversation_state = ConversationState.START.value  # Store string value, not enum
        lead.language = None  # Reset language to show language selection
        lead.conversation_data = {}
        lead.filled_slots = {}
        lead.pending_slot = None
        
        logger.info(f"🔄 /start command - Lead {lead.id}: After reset - state={lead.conversation_state}, cleared conversation_data")
        
        # Process through Brain
        response = await self.brain.process_message(lead, "/start")
        await self._send_response(update, context, response, lead)
    
    async def handle_set_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /set_admin command to register the current user as admin for notifications.
        Usage: /set_admin
        """
        chat_id = str(update.effective_chat.id)
        
        try:
            # Update tenant with admin_chat_id
            async with async_session() as session:
                result = await session.execute(
                    select(Tenant).where(Tenant.id == self.tenant.id)
                )
                tenant = result.scalar_one_or_none()
                
                if tenant:
                    tenant.admin_chat_id = chat_id
                    await session.commit()
                    
                    success_msg = {
                        Language.FA: f"✅ تبریک!\n\nشما ({chat_id}) به عنوان ادمین برای دریافت هشدارهای لید ثبت شدید.\n\n🚀 از این به بعد، به محض ثبت شماره مشتری، برای شما هشدار ارسال می‌شود.",
                        Language.EN: f"✅ Congratulations!\n\nYou ({chat_id}) have been registered as admin for lead notifications.\n\n🚀 From now on, you'll receive alerts when customers submit their phone numbers.",
                        Language.AR: f"✅ مبروك!\n\nتم تسجيلك كمسؤول لاستقبال تنبيهات العملاء.\n\n🚀 ستتلقى إشعارات فورية عند تسجيل رقم العميل.",
                        Language.RU: f"✅ Поздравляем!\n\nВы ({chat_id}) зарегистрированы как администратор для уведомлений о лидах.\n\n🚀 Теперь вы будете получать оповещения при регистрации номера клиента."
                    }
                    
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=success_msg.get(Language.FA, success_msg[Language.EN])
                    )
                    
                    logger.info(f"✅ Admin registered: {chat_id} for tenant {self.tenant.id}")
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="❌ Error: Tenant not found!"
                    )
                    logger.error(f"❌ Tenant {self.tenant.id} not found when setting admin")
        
        except Exception as e:
            logger.error(f"❌ Error setting admin: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ An error occurred. Please try again."
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks with race condition protection."""
        query = update.callback_query
        
        # Ignore disabled buttons (anti-loop protection)
        if query.data in ["selected", "disabled"]:
            await query.answer("Already selected ✅")
            return
        
        await query.answer()  # Acknowledge the callback
        
        lead = await self._get_or_create_lead(update)
        telegram_id = str(update.effective_chat.id)
        callback_data = query.data
        
        # CRITICAL FIX #8: Refresh lead object - use fresh instance directly
        async with async_session() as session:
            result = await session.execute(select(Lead).where(Lead.id == lead.id))
            fresh_lead = result.scalars().first()
            if fresh_lead:
                logger.info(f"🔄 Refreshed lead {lead.id}, state={fresh_lead.conversation_state}")
                lead = fresh_lead  # Replace object reference
        
        # FIX #6: Ghost Protocol - Update last interaction timestamp
        if redis_manager.redis_client:
            await redis_manager.redis_client.set(f"user:{lead.id}:last_interaction", datetime.now().isoformat())
            logger.info(f"⏰ Updated last_interaction for user {lead.id} (callback)")
        
        # CRITICAL: Acquire lock to prevent race conditions
        if telegram_id not in user_locks:
            user_locks[telegram_id] = Lock()
        
        async with user_locks[telegram_id]:
            logger.info(f"🔒 Lock acquired for callback user {telegram_id}")
        
        # Add checkmark to selected button (anti-loop)
        selected_button_text = None
        if query.message and query.message.reply_markup:
            for row in query.message.reply_markup.inline_keyboard:
                for button in row:
                    if button.callback_data == callback_data:
                        selected_button_text = button.text
                        break
        
        # Handle slot booking
        if callback_data.startswith("slot_"):
            slot_id = int(callback_data.split("_")[1])
            success = await book_slot(slot_id, lead.id)
            
            if success:
                # Get slot details to calculate actual appointment time
                async with async_session() as session:
                    result = await session.execute(
                        select(AgentAvailability).where(AgentAvailability.id == slot_id)
                    )
                    slot = result.scalar_one_or_none()
                    
                    if slot:
                        # Calculate next occurrence of this day
                        now = datetime.utcnow()
                        today = now.date()
                        days_ahead = {
                            'monday': 0, 'tuesday': 1, 'wednesday': 2,
                            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
                        }
                        target_day = days_ahead.get(slot.day_of_week.value, 0)
                        current_day = today.weekday()
                        days_until = (target_day - current_day + 7) % 7
                        
                        # If same day, check if time has passed
                        if days_until == 0:
                            if now.time() >= slot.start_time:
                                days_until = 7  # Schedule for next week
                        
                        appointment_date = datetime.combine(
                            today + timedelta(days=days_until),
                            slot.start_time
                        )
                        
                        # Create appointment with calculated date
                        await create_appointment(
                            lead_id=lead.id,
                            appointment_type=AppointmentType.OFFICE,
                            scheduled_date=appointment_date
                        )
        
        # Handle schedule consultation request - Show available time slots
        elif callback_data == "schedule_consultation":
            # Get available slots from database
            available_slots = await get_available_slots(self.tenant.id)
            
            if not available_slots:
                # No slots available
                no_slots_msg = {
                    Language.EN: "⏰ Currently, we don't have available time slots. Please contact us directly or try again later.",
                    Language.FA: "⏰ در حال حاضر وقت خالی نداریم. لطفاً مستقیماً با ما تماس بگیرید یا بعداً تلاش کنید.",
                    Language.AR: "⏰ حالياً، ليس لدينا فترات زمنية متاحة. يرجى الاتصال بنا مباشرة أو المحاولة لاحقاً.",
                    Language.RU: "⏰ В настоящее время у нас нет доступных временных слотов. Пожалуйста, свяжитесь с нами напрямую или попробуйте позже."
                }
                lang = lead.language or Language.FA
                await query.edit_message_text(no_slots_msg.get(lang, no_slots_msg[Language.EN]))
                return
            
            # Build calendar message with available slots
            lang = lead.language or Language.FA
            calendar_header = {
                Language.EN: "📅 **Available Consultation Times**\n\nPlease select a time that works best for you:",
                Language.FA: "📅 **وقت‌های خالی مشاوره**\n\nلطفاً زمانی که برایتان مناسب است انتخاب کنید:",
                Language.AR: "📅 **أوقات الاستشارة المتاحة**\n\nيرجى اختيار الوقت الذي يناسبك:",
                Language.RU: "📅 **Доступное время консультации**\n\nПожалуйста, выберите удобное для вас время:"
            }
            
            # Group slots by day
            from collections import defaultdict
            slots_by_day = defaultdict(list)
            for slot in available_slots:
                day_name = slot.day_of_week.value.capitalize()
                time_range = f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
                slots_by_day[day_name].append({
                    'id': slot.id,
                    'time': time_range,
                    'start': slot.start_time
                })
            
            # Build inline keyboard with slots
            keyboard = []
            day_translations = {
                'Monday': {'en': '📅 Mon', 'fa': '📅 دوشنبه', 'ar': '📅 الاثنين', 'ru': '📅 Пн'},
                'Tuesday': {'en': '📅 Tue', 'fa': '📅 سه‌شنبه', 'ar': '📅 الثلاثاء', 'ru': '📅 Вт'},
                'Wednesday': {'en': '📅 Wed', 'fa': '📅 چهارشنبه', 'ar': '📅 الأربعاء', 'ru': '📅 Ср'},
                'Thursday': {'en': '📅 Thu', 'fa': '📅 پنج‌شنبه', 'ar': '📅 الخميس', 'ru': '📅 Чт'},
                'Friday': {'en': '📅 Fri', 'fa': '📅 جمعه', 'ar': '📅 الجمعة', 'ru': '📅 Пт'},
                'Saturday': {'en': '📅 Sat', 'fa': '📅 شنبه', 'ar': '📅 السبت', 'ru': '📅 Сб'},
                'Sunday': {'en': '📅 Sun', 'fa': '📅 یکشنبه', 'ar': '📅 الأحد', 'ru': '📅 Вс'}
            }
            
            lang_key = {'en': 'en', 'fa': 'fa', 'ar': 'ar', 'ru': 'ru'}.get(lang.value, 'fa')
            
            for day_name in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                if day_name in slots_by_day:
                    # Sort slots by start time
                    sorted_slots = sorted(slots_by_day[day_name], key=lambda x: x['start'])
                    
                    # Add day header button (disabled)
                    day_label = day_translations.get(day_name, {}).get(lang_key, day_name)
                    keyboard.append([InlineKeyboardButton(day_label, callback_data="disabled")])
                    
                    # Add time slot buttons (2 per row)
                    row = []
                    for slot in sorted_slots:
                        btn = InlineKeyboardButton(
                            f"🕐 {slot['time']}", 
                            callback_data=f"slot_{slot['id']}"
                        )
                        row.append(btn)
                        if len(row) == 2:
                            keyboard.append(row)
                            row = []
                    if row:  # Add remaining buttons
                        keyboard.append(row)
            
            # Send calendar with slots
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                calendar_header.get(lang, calendar_header[Language.EN]),
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        # Process through Brain
        response = await self.brain.process_message(lead, "", callback_data)
        
        # Add checkmark to selected button after Brain processing
        if selected_button_text:
            await edit_message_with_checkmark(update, context, selected_button_text)
            logger.info(f"✅ Checkmark added to button: {selected_button_text}")
        
        # Save context to Redis
        await save_context_to_redis(lead)
        logger.info(f"💾 Saved callback context to Redis for lead {lead.id}")
        
        await self._send_response(update, context, response, lead)
        logger.info(f"🔓 Lock released for callback user {telegram_id}")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages with race condition protection."""
        lead = await self._get_or_create_lead(update)
        message_text = update.message.text
        telegram_id = str(update.effective_chat.id)
        
        #  CRITICAL FIX #9: Refresh lead and COPY attributes to preserve data after session closes
        # We must copy the fresh state to the original lead object before session closes
        async with async_session() as session:
            result = await session.execute(select(Lead).where(Lead.id == lead.id))
            fresh_lead = result.scalars().first()
            if fresh_lead:
                logger.info(f"🔄 Refreshed lead {lead.id}, state={fresh_lead.conversation_state}")
                # Copy the ACTUAL conversation_state value (string) to the lead object
                # This ensures the value persists after session closes
                lead.conversation_state = fresh_lead.conversation_state
                lead.language = fresh_lead.language
                lead.conversation_data = fresh_lead.conversation_data
                logger.info(f"✅ Copied state to lead object: {lead.conversation_state}")
        
        # CRITICAL: Ghost Protocol - Update last interaction timestamp on EVERY message
        if redis_manager.redis_client:
            timestamp = datetime.now().isoformat()
            await redis_manager.redis_client.set(f"user:{lead.id}:last_interaction", timestamp)
            logger.info(f"⏰ Updated last_interaction for user {lead.id} at {timestamp}")
        else:
            logger.warning(f"⚠️ Redis not available - cannot update last_interaction for user {lead.id}")
        
        # CRITICAL: Acquire lock to prevent race conditions (2 messages in 1 second)
        if telegram_id not in user_locks:
            user_locks[telegram_id] = Lock()
        
        async with user_locks[telegram_id]:
            logger.info(f"🔒 Lock acquired for user {telegram_id}")
            
            # Load context from Redis (with recovery if timeout occurred)
            redis_context = await redis_manager.get_context(telegram_id, self.tenant.id)
            if redis_context:
                logger.info(f"📦 Loaded Redis context for lead {lead.id}: state={redis_context.get('state')}")
            
            # Process through Brain
            response = await self.brain.process_message(lead, message_text)
            
            # Save context to Redis after processing
            await save_context_to_redis(lead)
            logger.info(f"💾 Saved context to Redis for lead {lead.id}")
            
            await self._send_response(update, context, response, lead)
            logger.info(f"🔓 Lock released for user {telegram_id}")
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages with slot filling protection."""
        lead = await self._get_or_create_lead(update)
        
        # CRITICAL FIX #8: Refresh lead object - use fresh instance directly
        async with async_session() as session:
            result = await session.execute(select(Lead).where(Lead.id == lead.id))
            fresh_lead = result.scalars().first()
            if fresh_lead:
                logger.info(f"🔄 Refreshed lead {lead.id}, state={fresh_lead.conversation_state}")
                lead = fresh_lead  # Replace object reference
        
        # ZOMBIE STATE PROTECTION: If in SLOT_FILLING with pending button selection, guide them
        if lead.conversation_state == ConversationState.SLOT_FILLING and lead.pending_slot:
            lang = lead.language or Language.EN
            voice_redirect = {
                Language.EN: "I'll process your voice in a moment! First, please select an option from the buttons above to continue.",
                Language.FA: "یه لحظه بعد صداتو پردازش میکنم! اول لطفاً یکی از دکمه‌های بالا رو انتخاب کن.",
                Language.AR: "سأعالج رسالتك الصوتية بعد قليل! أولاً، اختر خياراً من الأزرار أعلاه.",
                Language.RU: "Обработаю голосовое чуть позже! Сначала выберите вариант из кнопок выше."
            }
            await update.message.reply_text(voice_redirect.get(lang, voice_redirect[Language.EN]))
            return
        
        # Check if voice exists
        if not update.message.voice:
            await update.message.reply_text("No voice message received. Please try again.")
            return
        
        # Download voice file
        voice = update.message.voice
        
        # Check voice duration (max 5 minutes)
        if voice.duration > 300:
            await update.message.reply_text("Voice message too long (max 5 minutes). Please send a shorter message.")
            return
        
        file = await context.bot.get_file(voice.file_id)
        
        # Download to bytes
        audio_bytes = await file.download_as_bytearray()
        
        # Process through Brain
        transcript, response = await process_voice_message(
            tenant=self.tenant,
            lead=lead,
            audio_data=bytes(audio_bytes),
            file_extension="ogg"
        )
        
        # Update lead with transcript if available
        if transcript:
            await update_lead(lead.id, voice_transcript=transcript)
            logger.info(f"🎤 Voice transcript saved for lead {lead.id}: {transcript[:100]}...")
        
        # Save context to Redis after voice processing
        await save_context_to_redis(lead)
        logger.info(f"💾 Saved voice context to Redis for lead {lead.id}")
        
        # DEBUG: Log response before sending
        logger.info(f"🎤 Voice response ready - message_len={len(response.message)}, has_buttons={bool(response.buttons)}")
        
        await self._send_response(update, context, response, lead)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages - find similar properties OR handle unexpected photo during slot filling."""
        lead = await self._get_or_create_lead(update)
        
        # ZOMBIE STATE PROTECTION: If in SLOT_FILLING, guide back to slots
        if lead.conversation_state == ConversationState.SLOT_FILLING:
            lang = lead.language or Language.EN
            fallback_msgs = {
                Language.EN: "I see you sent a photo! I'll analyze it in a moment, but first let's finish your property preferences. Please select your budget:",
                Language.FA: "عکس فرستادید! یه لحظه بعد بررسی میکنم، اما اول بیا ترجیحاتت رو کامل کنیم. لطفاً بودجه انتخاب کن:",
                Language.AR: "أرى أنك أرسلت صورة! سأحللها بعد قليل، لكن دعنا ننهي تفضيلاتك. اختر ميزانيتك:",
                Language.RU: "Вижу, вы отправили фото! Проанализирую чуть позже, но сначала завершим предпочтения. Выберите бюджет:"
            }
            
            from brain import BUDGET_RANGES
            budget_buttons = []
            for idx, (min_val, max_val) in BUDGET_RANGES.items():
                label = f"{min_val:,} - {max_val:,} AED" if max_val else f"{min_val:,}+ AED"
                budget_buttons.append({"text": label, "callback_data": f"budget_{idx}"})
            
            response = BrainResponse(
                message=fallback_msgs.get(lang, fallback_msgs[Language.EN]),
                next_state=ConversationState.SLOT_FILLING,
                buttons=budget_buttons
            )
            await self._send_response(update, context, response, lead)
            return
        
        # Check if photo exists
        if not update.message.photo:
            await update.message.reply_text("No photo received. Please try again.")
            return
        
        # Get the largest photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Download to bytes
        image_bytes = await file.download_as_bytearray()
        
        # Validate image size (max 20MB for Gemini)
        if len(image_bytes) > 20 * 1024 * 1024:
            await update.message.reply_text("Image too large (max 20MB). Please send a smaller image.")
            return
        
        # Send processing message
        lang = lead.language or Language.EN
        from brain import Brain
        brain = Brain(self.tenant)
        processing_msg = brain.get_text("image_processing", lang)
        await update.message.reply_text(processing_msg)
        
        # Process through Brain
        from brain import process_image_message
        description, response = await process_image_message(
            tenant=self.tenant,
            lead=lead,
            image_data=bytes(image_bytes),
            file_extension="jpg"
        )
        
        await self._send_response(update, context, response, lead)
    
    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle shared contact (phone number)."""
        lead = await self._get_or_create_lead(update)
        
        # CRITICAL FIX #8: Refresh lead object - use fresh instance directly
        async with async_session() as session:
            result = await session.execute(select(Lead).where(Lead.id == lead.id))
            fresh_lead = result.scalars().first()
            if fresh_lead:
                logger.info(f"🔄 Refreshed lead {lead.id}, state={fresh_lead.conversation_state}")
                lead = fresh_lead  # Replace object reference
        
        contact = update.message.contact
        
        # Update lead with phone number
        if contact.phone_number:
            await update_lead(lead.id, phone=contact.phone_number)
            logger.info(f"📞 Lead {lead.id} shared phone number: {contact.phone_number}")
        
        # Process as if they entered the phone number
        response = await self.brain.process_message(lead, contact.phone_number)
        await self._send_response(update, context, response, lead)
    
    async def send_ghost_reminder(self, lead: Lead):
        """Send ghost protocol reminder to a lead."""
        if not self.application or not lead.telegram_chat_id:
            return
        
        response = self.brain.get_ghost_reminder(lead)
        reply_markup = self._build_inline_keyboard(response.buttons) if response.buttons else None
        
        try:
            await self.application.bot.send_message(
                chat_id=int(lead.telegram_chat_id),
                text=response.message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            # Mark reminder as sent
            await update_lead(lead.id, ghost_reminder_sent=True)
            logger.info(f"Ghost reminder sent to lead {lead.id}")
        except Exception as e:
            logger.error(f"Failed to send ghost reminder to lead {lead.id}: {e}")
    
    async def send_appointment_reminder(self, lead: Lead, appointment_time: datetime):
        """Send appointment reminder to lead."""
        if not self.application or not lead.telegram_chat_id:
            return
        
        # Format reminder message based on language
        lang = lead.language
        time_str = appointment_time.strftime("%A, %B %d at %H:%M")
        
        messages = {
            "en": f"⏰ Reminder: You have an appointment tomorrow!\n\n📅 {time_str}\n\nWe look forward to seeing you!",
            "fa": f"⏰ یادآوری: شما فردا یک قرار ملاقات دارید!\n\n📅 {time_str}\n\nمنتظر دیدار شما هستیم!",
            "ar": f"⏰ تذكير: لديك موعد غدًا!\n\n📅 {time_str}\n\nنتطلع إلى رؤيتك!",
            "ru": f"⏰ Напоминание: У вас завтра встреча!\n\n📅 {time_str}\n\nЖдём вас!"
        }
        
        message = messages.get(lang.value if lang else "en", messages["en"])
        
        try:
            await self.application.bot.send_message(
                chat_id=int(lead.telegram_chat_id),
                text=message,
                parse_mode='HTML'
            )
            logger.info(f"Appointment reminder sent to lead {lead.id}")
        except Exception as e:
            logger.error(f"Failed to send appointment reminder to lead {lead.id}: {e}")

    # === FEATURE 3: GHOST PROTOCOL METHODS ===
    
    async def _ghost_protocol_loop(self):
        """
        Ghost Protocol V2: Two-stage follow-up system
        
        STAGE 1 - FAST NUDGE (15 minutes):
        - Quick check-in: "Are you still there?"
        - Triggers FOMO: "I just found something crazy"
        
        STAGE 2 - VALUE NUDGE (2 hours):
        - Provides value: "My colleague found the property you wanted"
        - Creates urgency: "When can you talk?"
        
        Runs every 5 minutes to check for leads needing re-engagement
        
        Database flags:
        - fast_nudge_sent: Tracks if 15-min nudge was sent
        - ghost_reminder_sent: Tracks if 2-hour nudge was sent
        """
        logger.info(f"[Ghost Protocol V2] Started for tenant {self.tenant.id}")
        
        while True:
            try:
                # Run check every 5 minutes for faster response
                await asyncio.sleep(300)
                
                async with async_session() as session:
                    now = datetime.utcnow()
                    
                    # === STAGE 1: FAST NUDGE (15-20 mins of inactivity) ===
                    fifteen_mins_ago = now - timedelta(minutes=15)
                    twenty_mins_ago = now - timedelta(minutes=20)
                    
                    # Query leads who:
                    # - Were active 15-20 mins ago
                    # - Haven't received fast nudge yet
                    # - Have engaged (at least some conversation data)
                    result_fast = await session.execute(
                        select(Lead).where(
                            Lead.tenant_id == self.tenant.id,
                            Lead.updated_at < fifteen_mins_ago,
                            Lead.updated_at > twenty_mins_ago,
                            Lead.conversation_data.isnot(None),  # Has engaged before
                            Lead.conversation_data['fast_nudge_sent'].astext.is_(None)  # Fast nudge not sent
                        ).order_by(Lead.updated_at.desc()).limit(10)
                    )
                    
                    fast_nudge_leads = result_fast.scalars().all()
                    
                    if fast_nudge_leads:
                        logger.info(f"[Ghost Protocol V2] Found {len(fast_nudge_leads)} leads for FAST NUDGE")
                    
                    for lead in fast_nudge_leads:
                        try:
                            await self._send_fast_nudge(lead, session)
                        except Exception as e:
                            logger.error(f"[Fast Nudge] Error for lead {lead.id}: {e}")
                    
                    # === STAGE 2: VALUE NUDGE (2 hours of inactivity) ===
                    two_hours_ago = now - timedelta(hours=2)
                    
                    result_value = await session.execute(
                        select(Lead).where(
                            Lead.tenant_id == self.tenant.id,
                            Lead.phone.isnot(None),  # Has shared contact
                            Lead.status != ConversationState.VIEWING_SCHEDULED,  # Hasn't booked yet
                            Lead.updated_at < two_hours_ago,
                            Lead.ghost_reminder_sent == False  # Value nudge not sent
                        ).order_by(Lead.updated_at.asc()).limit(10)
                    )
                    
                    value_nudge_leads = result_value.scalars().all()
                    
                    if value_nudge_leads:
                        logger.info(f"[Ghost Protocol V2] Found {len(value_nudge_leads)} leads for VALUE NUDGE")
                    
                    for lead in value_nudge_leads:
                        try:
                            await self._send_ghost_message(lead)
                        except Exception as e:
                            logger.error(f"[Value Nudge] Error for lead {lead.id}: {e}")
            
            except Exception as e:
                logger.error(f"[Ghost Protocol V2] Error in loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _send_fast_nudge(self, lead: Lead, session):
        """
        Send quick 15-minute check-in to prevent lead from going cold.
        
        Messages are casual and create curiosity (FOMO):
        - "Are you still with me?"
        - "I just found something crazy"
        """
        try:
            lang = lead.language or Language.EN
            
            fast_nudge_messages = {
                Language.EN: "Hey! Still there? 👀\n\nI just found something CRAZY that matches what you're looking for. Want to see it?",
                Language.FA: "هستی؟ 👀\n\nیه چیزی دیدم که باورت نمیشه، دقیقاً همون چیزیه که دنبالشی. می‌خوای ببینی؟",
                Language.AR: "مرحبًا! لا تزال هناك؟ 👀\n\nوجدت للتو شيئًا جنونيًا يطابق ما تبحث عنه. تريد أن ترى؟",
                Language.RU: "Привет! Вы ещё здесь? 👀\n\nТолько что нашёл БЕЗУМНУЮ вещь, которая идеально вам подходит. Хотите увидеть?"
            }
            
            message = fast_nudge_messages.get(lang, fast_nudge_messages[Language.EN])
            
            if lead.telegram_chat_id:
                await self.application.bot.send_message(
                    chat_id=int(lead.telegram_chat_id),
                    text=message
                )
                
                # Mark fast nudge as sent in conversation_data
                conversation_data = lead.conversation_data or {}
                conversation_data['fast_nudge_sent'] = True
                conversation_data['fast_nudge_at'] = datetime.utcnow().isoformat()
                
                result = await session.execute(
                    select(Lead).where(Lead.id == lead.id)
                )
                db_lead = result.scalar_one()
                db_lead.conversation_data = conversation_data
                db_lead.fomo_messages_sent = (db_lead.fomo_messages_sent or 0) + 1
                await session.commit()
                
                logger.info(f"[Fast Nudge] Sent to lead {lead.id} ({lang.value})")
        
        except Exception as e:
            logger.error(f"[Fast Nudge] Error sending to lead {lead.id}: {e}")
            raise

    async def _send_ghost_message(self, lead: Lead):
        """
        Send personalized ghost follow-up message to re-engage cold lead
        
        Message format:
        - Personalized with lead name
        - Multi-language support (EN/FA/AR/RU)
        - Implies value without pressure (colleague found property)
        
        After sending:
        - Mark ghost_reminder_sent = True
        - Increment fomo_messages_sent counter
        """
        try:
            # Get lead's preferred language
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
                    chat_id=int(lead.telegram_chat_id),
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
                    db_lead.updated_at = datetime.utcnow()
                    await session.commit()
                
                logger.info(f"[Ghost Protocol] Ghost message sent to lead {lead.id} (name: {lead.name}, lang: {lang.value})")
        
        except Exception as e:
            logger.error(f"[Ghost Protocol] Error sending ghost message to lead {lead.id}: {e}")
            raise


# ==================== MORNING COFFEE REPORT ====================

async def generate_daily_report(tenant_id: int) -> Dict[str, str]:
    """
    Generate daily "Wolf Closer Morning Report" - NOT just stats, but ACTION LIST!
    
    Transforms overnight activity into an ACTIONABLE hit list with:
    - Hot leads with phone numbers (clickable WhatsApp links)
    - Budget-qualified prospects
    - Viewing-ready candidates
    - Direct call-to-action for agent
    
    This is a WEAPON, not a report.
    """
    try:
        async with async_session() as session:
            now = datetime.utcnow()
            yesterday = now - timedelta(days=1)
            
            # Metric A: Count active conversations (updated in last 24h)
            chat_result = await session.execute(
                select(Lead).where(
                    Lead.tenant_id == tenant_id,
                    Lead.updated_at >= yesterday
                )
            )
            active_conversations = len(chat_result.scalars().all())
            
            # Metric B: NEW STRATEGY - Get HOT LEADS (qualified + phone + not booked yet)
            hot_leads_result = await session.execute(
                select(Lead).where(
                    Lead.tenant_id == tenant_id,
                    Lead.phone.isnot(None),  # Has phone
                    Lead.status != ConversationState.VIEWING_SCHEDULED,  # Not booked yet = opportunity!
                    Lead.budget_max.isnot(None),  # Budget qualified
                    Lead.updated_at >= yesterday  # Active in last 24h
                ).order_by(Lead.budget_max.desc()).limit(10)  # Top 10 by budget
            )
            hot_leads_list = hot_leads_result.scalars().all()
            
            # Metric C: Count total new leads with phone (for stats)
            total_leads_result = await session.execute(
                select(Lead).where(
                    Lead.tenant_id == tenant_id,
                    Lead.phone.isnot(None),
                    Lead.created_at >= yesterday
                )
            )
            total_new_leads_count = len(total_leads_result.scalars().all())
            
            # Metric D: Find DIAMOND lead (highest budget or Golden Visa seeker)
            diamond_result = await session.execute(
                select(Lead).where(
                    Lead.tenant_id == tenant_id,
                    Lead.created_at >= yesterday,
                    ((Lead.purpose == Purpose.RESIDENCY) | (Lead.budget_max >= 2000000))  # Golden Visa or 2M+
                ).order_by(Lead.budget_max.desc())
            )
            diamond_leads = diamond_result.scalars().all()
            
            # Generate highlight message
            highlight_msg_en = highlight_msg_fa = highlight_msg_ar = highlight_msg_ru = ""
            if diamond_leads:
                lead = diamond_leads[0]
                budget_str = f"{lead.budget_max:,.0f} AED" if lead.budget_max else "High"
                if lead.purpose == Purpose.RESIDENCY:
                    highlight_msg_en = f"🛂 Golden Visa seeker (Budget: {budget_str})!"
                    highlight_msg_fa = f"🛂 خریدار گلدن ویزا (بودجه: {budget_str})!"
                    highlight_msg_ar = f"🛂 باحث عن التأشيرة الذهبية (الميزانية: {budget_str})!"
                    highlight_msg_ru = f"🛂 Ищет Golden Visa (Бюджет: {budget_str})!"
                else:
                    highlight_msg_en = f"💎 High-value investor ({budget_str})!"
                    highlight_msg_fa = f"💎 سرمایه‌گذار VIP ({budget_str})!"
                    highlight_msg_ar = f"💎 مستثمر كبير ({budget_str})!"
                    highlight_msg_ru = f"💎 Крупный инвестор ({budget_str})!"
            else:
                highlight_msg_en = "✨ Quality leads incoming - keep the pipeline hot!"
                highlight_msg_fa = "✨ لید‌های با کیفیت در راهند - خط رو گرم نگه دار!"
                highlight_msg_ar = "✨ عملاء جيدون قادمون - حافظ على الخط ساخنًا!"
                highlight_msg_ru = "✨ Качественные лиды на подходе - держи воронку горячей!"
            
            # Generate multilingual weaponized reports
            reports = {
                Language.EN.value: generate_wolf_report_en(active_conversations, total_new_leads_count, hot_leads_list, highlight_msg_en),
                Language.FA.value: generate_wolf_report_fa(active_conversations, total_new_leads_count, hot_leads_list, highlight_msg_fa),
                Language.AR.value: generate_wolf_report_ar(active_conversations, total_new_leads_count, hot_leads_list, highlight_msg_ar),
                Language.RU.value: generate_wolf_report_ru(active_conversations, total_new_leads_count, hot_leads_list, highlight_msg_ru),
            }
            
            logger.info(f"[Wolf Report] Generated for tenant {tenant_id}: {active_conversations} chats, {len(hot_leads_list)} hot leads")
            return reports
    
    except Exception as e:
        logger.error(f"[Wolf Report] Error generating report for tenant {tenant_id}: {e}")
        return {}


def generate_wolf_report_en(chat_count: int, total_leads: int, hot_leads: list, highlight: str) -> str:
    """Generate English Wolf Closer Report - Actionable Hit List!"""
    
    # Build hot leads action list with WhatsApp click-to-chat links
    hot_leads_text = ""
    if hot_leads:
        for i, lead in enumerate(hot_leads[:5], 1):  # Top 5 only
            phone_clean = lead.phone.replace('+', '').replace(' ', '').replace('-', '') if lead.phone else ''
            name = lead.name or "Prospect"
            budget = f"{lead.budget_max:,.0f} AED" if lead.budget_max else "TBD"
            
            # WhatsApp click-to-chat link
            wa_link = f"https://wa.me/{phone_clean}" if phone_clean else "#"
            
            hot_leads_text += f"{i}. [{name}]({wa_link}) - Budget: {budget}\n"
    else:
        hot_leads_text = "   (No hot leads yet - pipeline building...)"
    
    return f"""☀️ **WOLF CLOSER BRIEFING** ☕️

📊 **Last Night Stats:** {chat_count} conversations | {total_leads} qualified

🔥 **YOUR HIT LIST (Call NOW!):**
{hot_leads_text}

💎 **Diamond Lead:** {highlight}

🚀 **Action:** These leads are HOT. Strike while iron burns. Let's close!
"""


def generate_wolf_report_fa(chat_count: int, total_leads: int, hot_leads: list, highlight: str) -> str:
    """Generate Persian Wolf Closer Report - لیست هدف‌گیری!"""
    
    # Build hot leads action list with WhatsApp click-to-chat links
    hot_leads_text = ""
    if hot_leads:
        for i, lead in enumerate(hot_leads[:5], 1):  # Top 5 only
            phone_clean = lead.phone.replace('+', '').replace(' ', '').replace('-', '') if lead.phone else ''
            name = lead.name or "مشتری"
            budget = f"{lead.budget_max:,.0f} درهم" if lead.budget_max else "نامشخص"
            
            # WhatsApp click-to-chat link
            wa_link = f"https://wa.me/{phone_clean}" if phone_clean else "#"
            
            hot_leads_text += f"{i}. [{name}]({wa_link}) - بودجه: {budget}\n"
    else:
        hot_leads_text = "   (هنوز لید داغی نیست - در حال ساخت خط...)"
    
    return f"""☀️ **گزارش صبحگاهی گرگ فروش** ☕️

📊 **آمار دیشب:** {chat_count} مکالمه | {total_leads} واجد شرایط

🔥 **لیست تماس امروز (همین الان زنگ بزن!):**
{hot_leads_text}

💎 **الماس امروز:** {highlight}

🚀 **دستور:** این لیدها داغ هستند. وقتی آهن داغه باید کوبید. بریم ببندیم!
"""


def generate_wolf_report_ar(chat_count: int, total_leads: int, hot_leads: list, highlight: str) -> str:
    """Generate Arabic Wolf Closer Report"""
    
    hot_leads_text = ""
    if hot_leads:
        for i, lead in enumerate(hot_leads[:5], 1):
            phone_clean = lead.phone.replace('+', '').replace(' ', '').replace('-', '') if lead.phone else ''
            name = lead.name or "عميل"
            budget = f"{lead.budget_max:,.0f} درهم" if lead.budget_max else "غير محدد"
            wa_link = f"https://wa.me/{phone_clean}" if phone_clean else "#"
            hot_leads_text += f"{i}. [{name}]({wa_link}) - الميزانية: {budget}\n"
    else:
        hot_leads_text = "   (لا توجد عملاء ساخنون حتى الآن...)"
    
    return f"""☀️ **تقرير البائع الذئب** ☕️

📊 **إحصائيات الليلة الماضية:** {chat_count} محادثة | {total_leads} مؤهل

🔥 **قائمة الاتصال (اتصل الآن!):**
{hot_leads_text}

💎 **العميل الماسي:** {highlight}

🚀 **إجراء:** هؤلاء العملاء ساخنون. اضرب والحديد ساخن. دعنا نغلق!
"""


def generate_wolf_report_ru(chat_count: int, total_leads: int, hot_leads: list, highlight: str) -> str:
    """Generate Russian Wolf Closer Report"""
    
    hot_leads_text = ""
    if hot_leads:
        for i, lead in enumerate(hot_leads[:5], 1):
            phone_clean = lead.phone.replace('+', '').replace(' ', '').replace('-', '') if lead.phone else ''
            name = lead.name or "Клиент"
            budget = f"{lead.budget_max:,.0f} AED" if lead.budget_max else "Неизв."
            wa_link = f"https://wa.me/{phone_clean}" if phone_clean else "#"
            hot_leads_text += f"{i}. [{name}]({wa_link}) - Бюджет: {budget}\n"
    else:
        hot_leads_text = "   (Пока нет горячих лидов...)"
    
    return f"""☀️ **ОТЧЁТ ВОЛКА-ПРОДАВЦА** ☕️

📊 **Статистика за ночь:** {chat_count} разговоров | {total_leads} квалифицированных

🔥 **СПИСОК ДЛЯ ЗВОНКОВ (Звони СЕЙЧАС!):**
{hot_leads_text}

💎 **Бриллиантовый клиент:** {highlight}

🚀 **Действие:** Эти лиды горячие. Куй железо пока горячо. Закрываем!
"""


# ==================== BOT MANAGER ====================

class BotManager:
    """
    Manages multiple Telegram bots for multi-tenant system.
    Also manages the Morning Coffee Report scheduler.
    """
    
    def __init__(self):
        self.bots: Dict[int, TelegramBotHandler] = {}
        self.scheduler: Optional[AsyncIOScheduler] = None
    
    async def start_scheduler(self):
        """Start APScheduler for Morning Coffee Reports"""
        try:
            self.scheduler = AsyncIOScheduler()
            
            # Schedule Morning Coffee Report for 8:00 AM daily
            self.scheduler.add_job(
                self.send_morning_coffee_reports,
                trigger=CronTrigger(hour=8, minute=0),
                id="morning_coffee_report",
                name="Morning Coffee Report",
                replace_existing=True,
                coalesce=True,
                max_instances=1
            )
            
            self.scheduler.start()
            logger.info("✅ [Morning Coffee] APScheduler started - Reports scheduled for 08:00 AM daily")
        
        except Exception as e:
            logger.error(f"❌ [Morning Coffee] Failed to start scheduler: {e}")
    
    async def stop_scheduler(self):
        """Stop APScheduler"""
        try:
            if self.scheduler:
                self.scheduler.shutdown(wait=False)
                logger.info("✅ [Morning Coffee] APScheduler stopped")
        except Exception as e:
            logger.error(f"❌ [Morning Coffee] Error stopping scheduler: {e}")
    
    async def send_morning_coffee_reports(self):
        """
        Send Morning Coffee Reports to all tenants who have admin_chat_id set.
        This is called daily at 08:00 AM by the scheduler.
        """
        try:
            logger.info("[Morning Coffee] Starting morning report generation for all tenants...")
            
            # Query all tenants with admin_chat_id set
            async with async_session() as session:
                result = await session.execute(
                    select(Tenant).where(Tenant.admin_chat_id.isnot(None))
                )
                tenants_with_admin = result.scalars().all()
            
            if not tenants_with_admin:
                logger.info("[Morning Coffee] No tenants with admin_chat_id found")
                return
            
            logger.info(f"[Morning Coffee] Found {len(tenants_with_admin)} tenants to send reports to")
            
            # Send report to each tenant
            for tenant in tenants_with_admin:
                try:
                    # Generate report for this tenant
                    reports = await generate_daily_report(tenant.id)
                    
                    if not reports:
                        logger.warning(f"[Morning Coffee] No report generated for tenant {tenant.id}")
                        continue
                    
                    # Get tenant's language preference (default to English)
                    tenant_lang = (tenant.language or Language.EN).value if hasattr(tenant, 'language') else "en"
                    report_text = reports.get(tenant_lang, reports.get("en", ""))
                    
                    if not report_text:
                        logger.warning(f"[Morning Coffee] No report text available for tenant {tenant.id}")
                        continue
                    
                    # Send report via Telegram
                    if tenant.id in self.bots and self.bots[tenant.id].application:
                        try:
                            await self.bots[tenant.id].application.bot.send_message(
                                chat_id=int(tenant.admin_chat_id),
                                text=report_text,
                                parse_mode="HTML"
                            )
                            logger.info(f"✅ [Morning Coffee] Report sent to tenant {tenant.id} ({tenant.name})")
                        
                        except Exception as e:
                            logger.error(f"❌ [Morning Coffee] Failed to send report to tenant {tenant.id}: {e}")
                    else:
                        logger.warning(f"[Morning Coffee] Bot not running for tenant {tenant.id}")
                
                except Exception as e:
                    logger.error(f"❌ [Morning Coffee] Error processing tenant {tenant.id}: {e}")
        
        except Exception as e:
            logger.error(f"❌ [Morning Coffee] Fatal error in send_morning_coffee_reports: {e}")
    
    async def start_bot_for_tenant(self, tenant: Tenant):
        """Start a bot for a specific tenant."""
        if tenant.id in self.bots:
            logger.warning(f"Bot already running for tenant {tenant.id}")
            return
        
        handler = TelegramBotHandler(tenant)
        await handler.start_bot()
        self.bots[tenant.id] = handler
    
    async def stop_bot_for_tenant(self, tenant_id: int):
        """Stop a bot for a specific tenant."""
        if tenant_id in self.bots:
            await self.bots[tenant_id].stop_bot()
            del self.bots[tenant_id]
    
    async def stop_all_bots(self):
        """Stop all running bots."""
        for tenant_id in list(self.bots.keys()):
            await self.stop_bot_for_tenant(tenant_id)
    
    async def send_ghost_reminders(self):
        """Send ghost protocol reminders through all bots."""
        from database import get_leads_needing_reminder
        
        leads = await get_leads_needing_reminder(hours=2)
        
        for lead in leads:
            if lead.tenant_id in self.bots:
                await self.bots[lead.tenant_id].send_ghost_reminder(lead)
    
    async def send_appointment_reminders(self):
        """Send appointment reminders through all bots."""
        from database import get_appointments_needing_reminder, async_session
        from sqlalchemy.future import select
        from database import Appointment, Lead
        
        appointments = await get_appointments_needing_reminder(hours_before=24)
        
        for appointment in appointments:
            async with async_session() as session:
                # Get lead
                result = await session.execute(
                    select(Lead).where(Lead.id == appointment.lead_id)
                )
                lead = result.scalar_one_or_none()
                
                if lead and lead.tenant_id in self.bots:
                    await self.bots[lead.tenant_id].send_appointment_reminder(
                        lead, 
                        appointment.scheduled_date
                    )
                    
                    # Mark reminder as sent
                    appointment.reminder_sent = True
                    await session.commit()


# Global bot manager instance
bot_manager = BotManager()

# User locks to prevent concurrent message processing (race condition protection)
from asyncio import Lock
user_locks: Dict[str, Lock] = {}


# ==================== WEBHOOK HANDLER ====================

async def handle_telegram_webhook(token: str, update_data: dict):
    """
    Handle incoming Telegram webhook update.
    This is called from the FastAPI endpoint.
    """
    # Get tenant by token
    tenant = await get_tenant_by_bot_token(token)
    if not tenant:
        logger.error(f"Unknown bot token: {token[:10]}...")
        return
    
    # Get or create bot handler
    if tenant.id not in bot_manager.bots:
        await bot_manager.start_bot_for_tenant(tenant)
    
    handler = bot_manager.bots[tenant.id]
    
    # Process update
    update = Update.de_json(update_data, handler.application.bot)
    await handler.application.process_update(update)
