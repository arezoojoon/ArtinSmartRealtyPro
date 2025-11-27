"""
ArtinSmartRealty V2 - Telegram Bot Interface
Handles Telegram API calls and passes everything to brain.py
"""

import os
import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
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
    AppointmentType, async_session
)
from brain import Brain, BrainResponse, process_telegram_message, process_voice_message

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


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
        
        self.application = Application.builder().token(self.tenant.telegram_bot_token).build()
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.application.add_handler(MessageHandler(filters.CONTACT, self.handle_contact))
        
        # Start polling
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        
        logger.info(f"Bot started for tenant: {self.tenant.name}")
    
    async def stop_bot(self):
        """Stop the Telegram bot."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info(f"Bot stopped for tenant: {self.tenant.name}")
    
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
        chat_id = update.effective_chat.id
        
        # Prepare keyboard if buttons exist
        reply_markup = None
        if response.buttons:
            reply_markup = self._build_inline_keyboard(response.buttons)
        
        # Send message
        if update.callback_query:
            # Edit existing message for callback queries
            try:
                await update.callback_query.edit_message_text(
                    text=response.message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
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
        
        if updates:
            await update_lead(lead.id, **updates)
        
        # Handle ROI generation if requested
        if response.should_generate_roi:
            try:
                from roi_engine import generate_roi_pdf
                from io import BytesIO
                
                # Generate PDF
                pdf_bytes = await generate_roi_pdf(
                    tenant=self.tenant,
                    lead=lead,
                    property_value=lead.budget_max or lead.budget_min
                )
                
                # Send PDF as document
                pdf_file = BytesIO(pdf_bytes)
                pdf_file.name = f"roi_analysis_{lead.id}.pdf"
                
                lang = lead.language or Language.EN
                caption_map = {
                    Language.EN: "📊 Here's your personalized ROI Analysis Report!",
                    Language.FA: "📊 این هم گزارش تحلیل سود سرمایه‌گذاری شما!",
                    Language.AR: "📊 إليك تقرير تحليل العائد على الاستثمار الشخصي!",
                    Language.RU: "📊 Вот ваш персональный отчёт ROI!"
                }
                
                await update.message.reply_document(
                    document=pdf_file,
                    filename=f"ROI_Analysis_{self.tenant.name}.pdf",
                    caption=caption_map.get(lang, caption_map[Language.EN])
                )
                
            except Exception as e:
                logger.error(f"Failed to generate ROI PDF: {e}")
                # Don't fail the whole message if PDF generation fails
                pass
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        lead = await self._get_or_create_lead(update)
        
        # Reset conversation state for new start
        await update_lead(lead.id, conversation_state=ConversationState.START)
        lead.conversation_state = ConversationState.START
        
        # Process through Brain
        response = await self.brain.process_message(lead, "/start")
        await self._send_response(update, context, response, lead)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks."""
        query = update.callback_query
        await query.answer()  # Acknowledge the callback
        
        lead = await self._get_or_create_lead(update)
        callback_data = query.data
        
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
        
        # Process through Brain
        response = await self.brain.process_message(lead, "", callback_data)
        await self._send_response(update, context, response, lead)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        lead = await self._get_or_create_lead(update)
        message_text = update.message.text
        
        # Process through Brain
        response = await self.brain.process_message(lead, message_text)
        await self._send_response(update, context, response, lead)
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages."""
        lead = await self._get_or_create_lead(update)
        
        # Download voice file
        voice = update.message.voice
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
        
        await self._send_response(update, context, response, lead)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages - find similar properties."""
        lead = await self._get_or_create_lead(update)
        
        # Get the largest photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Download to bytes
        image_bytes = await file.download_as_bytearray()
        
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
        contact = update.message.contact
        
        # Update lead with phone number
        if contact.phone_number:
            await update_lead(lead.id, phone=contact.phone_number)
        
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


# ==================== BOT MANAGER ====================

class BotManager:
    """
    Manages multiple Telegram bots for multi-tenant system.
    """
    
    def __init__(self):
        self.bots: Dict[int, TelegramBotHandler] = {}
    
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
