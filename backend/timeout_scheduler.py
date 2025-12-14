"""
Timeout Scheduler for Bot Follow-up Messages
Sends automatic reminders if user goes silent for 10+ minutes
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from telegram import Bot
from database import ConversationState, Language, get_lead_by_telegram_id
from redis_manager import redis_manager

logger = logging.getLogger(__name__)

# Follow-up messages by state and language
FOLLOWUP_MESSAGES = {
    ConversationState.HARD_GATE: {
        Language.EN: "Hey! Still there? 👋\n\nYour detailed PDF report is ready to send. Just share your phone number and I'll send it right away!",
        Language.FA: "هنوز هستی؟ 👋\n\nگزارش کامل PDF آماده ارساله. فقط شماره‌تو بده تا الان بفرستم!",
        Language.AR: "ما زلت هنا؟ 👋\n\nتقرير PDF المفصل جاهز للإرسال. فقط شارك رقم هاتفك وسأرسله على الفور!",
        Language.RU: "Вы еще здесь? 👋\n\nВаш подробный PDF-отчет готов к отправке. Просто поделитесь номером телефона, и я отправлю его прямо сейчас!"
    },
    ConversationState.SLOT_FILLING: {
        Language.EN: "Hey! Are you still interested? 🤔\n\nWe were just finding the perfect property for you. Want to continue?",
        Language.FA: "سلام! هنوز علاقه‌مندی؟ 🤔\n\nداشتیم بهترین ملک رو برات پیدا می‌کردیم. می‌خوای ادامه بدیم؟",
        Language.AR: "مرحبًا! هل ما زلت مهتمًا؟ 🤔\n\nكنا نبحث عن العقار المثالي لك. هل تريد المتابعة؟",
        Language.RU: "Привет! Вы все еще заинтересованы? 🤔\n\nМы искали идеальную недвижимость для вас. Хотите продолжить?"
    },
    ConversationState.WARMUP: {
        Language.EN: "Hello again! 👋\n\nAre you still looking for property in Dubai? Let me know!",
        Language.FA: "سلام دوباره! 👋\n\nهنوز به دنبال ملک در دبی هستی؟ بهم بگو!",
        Language.AR: "مرحبًا مرة أخرى! 👋\n\nهل ما زلت تبحث عن عقار في دبي؟ أخبرني!",
        Language.RU: "Привет снова! 👋\n\nВы все еще ищете недвижимость в Дубае? Дайте знать!"
    }
}


class TimeoutScheduler:
    """Manages timeout tracking and sends follow-up messages."""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the timeout scheduler background task."""
        if self.running:
            logger.warning("Timeout scheduler already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info("⏱️ Timeout scheduler started")
    
    async def stop(self):
        """Stop the timeout scheduler."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("⏱️ Timeout scheduler stopped")
    
    async def _run_scheduler(self):
        """Background task that runs ghost protocol and appointment reminders."""
        while self.running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # TASK 1: Ghost Protocol - Check for inactive users
                logger.info("👻 Ghost Protocol: Checking for inactive users...")
                await self._check_ghost_users()
                
                # TASK 2: Appointment Reminders (every hour only)
                current_minute = datetime.now().minute
                if current_minute < 5:  # Run once per hour (first 5 minutes)
                    logger.info("📅 Checking appointment reminders...")
                    await self._check_appointment_reminders()
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Timeout scheduler error: {e}")
    
    async def _check_ghost_users(self):
        """Find leads inactive for 15+ minutes and send follow-up."""
        try:
            from database import async_session, Lead
            from sqlalchemy.future import select
            
            async with async_session() as session:
                # Get all leads not in COMPLETED state
                result = await session.execute(
                    select(Lead).where(Lead.conversation_state != ConversationState.COMPLETED)
                )
                leads = result.scalars().all()
                
                for lead in leads:
                    if not lead.telegram_chat_id:
                        continue
                    
                    try:
                        # Get last_interaction from Redis
                        if redis_manager.redis_client:
                            last_interaction_str = await redis_manager.redis_client.get(
                                f"user:{lead.id}:last_interaction"
                            )
                            
                            if last_interaction_str:
                                last_interaction = datetime.fromisoformat(last_interaction_str.decode() if isinstance(last_interaction_str, bytes) else last_interaction_str)
                                now = datetime.now()
                                time_elapsed = now - last_interaction
                                
                                # If inactive for 15+ minutes, send follow-up
                                if time_elapsed > timedelta(minutes=15):
                                    # Check if already sent follow-up recently
                                    followup_sent_key = f"user:{lead.id}:followup_sent"
                                    already_sent = await redis_manager.redis_client.get(followup_sent_key)
                                    
                                    if not already_sent:
                                        logger.info(f"📧 Sending follow-up to lead {lead.id} (inactive for {time_elapsed.total_seconds()/60:.0f} min)")
                                        
                                        # Build follow-up message with new property hook
                                        followup_msg = {
                                            Language.EN: f"Are you still interested? I found a new unit matching your budget. Want to see it? 🏠",
                                            Language.FA: f"هنوز علاقه‌مندی؟ من یک واحد جدید با بودجه‌ات پیدا کردم. می‌خوای ببینی؟ 🏠",
                                            Language.AR: f"هل ما زلت مهتمًا؟ وجدت وحدة جديدة تناسب ميزانيتك. هل تريد أن تراها؟ 🏠",
                                            Language.RU: f"Вы все еще заинтересованы? Я нашел новую квартиру по вашему бюджету. Хотите посмотреть? 🏠"
                                        }
                                        
                                        msg = followup_msg.get(lead.language or Language.EN, followup_msg[Language.EN])
                                        
                                        # Send message
                                        try:
                                            await self.bot.send_message(
                                                chat_id=lead.telegram_chat_id,
                                                text=msg
                                            )
                                            logger.info(f"✅ Follow-up sent to {lead.telegram_chat_id}")
                                            
                                            # Mark as sent (expires in 24 hours)
                                            await redis_manager.redis_client.setex(
                                                followup_sent_key,
                                                86400,  # 24 hours
                                                "1"
                                            )
                                        except Exception as e:
                                            logger.warning(f"⚠️ Failed to send follow-up to {lead.telegram_chat_id}: {e}")
                    except Exception as e:
                        logger.warning(f"⚠️ Ghost Protocol error for lead {lead.id}: {e}")
        except Exception as e:
            logger.error(f"❌ Ghost Protocol check failed: {e}")
    
    async def _check_appointment_reminders(self):
        """Find appointments scheduled for Now + 24h and send reminder."""
        try:
            from database import async_session, Appointment, Lead
            from sqlalchemy.future import select
            
            async with async_session() as session:
                # Get appointments scheduled for tomorrow (24h from now)
                tomorrow = datetime.now() + timedelta(hours=24)
                tomorrow_start = tomorrow.replace(minute=0, second=0, microsecond=0)
                tomorrow_end = tomorrow_start + timedelta(hours=1)
                
                result = await session.execute(
                    select(Appointment).where(
                        Appointment.scheduled_time >= tomorrow_start,
                        Appointment.scheduled_time < tomorrow_end,
                        Appointment.status == "confirmed"
                    )
                )
                appointments = result.scalars().all()
                
                for appt in appointments:
                    try:
                        # Get lead
                        lead_result = await session.execute(
                            select(Lead).where(Lead.id == appt.lead_id)
                        )
                        lead = lead_result.scalars().first()
                        
                        if not lead or not lead.telegram_chat_id:
                            continue
                        
                        # Format time
                        time_str = appt.scheduled_time.strftime("%I:%M %p")
                        
                        # Build reminder message
                        reminder_msg = {
                            Language.EN: f"⏰ Reminder: Your consultation is tomorrow at {time_str}. Looking forward to meeting you!",
                            Language.FA: f"⏰ یادآوری: مشاوره شما فردا ساعت {time_str} است. منتظر دیدارتان هستم!",
                            Language.AR: f"⏰ تذكير: استشارتك غدًا في {time_str}. نتطلع للقائك!",
                            Language.RU: f"⏰ Напоминание: Ваша консультация завтра в {time_str}. С нетерпением жду встречи!"
                        }
                        
                        msg = reminder_msg.get(lead.language or Language.EN, reminder_msg[Language.EN])
                        
                        # Send reminder
                        await self.bot.send_message(
                            chat_id=lead.telegram_chat_id,
                            text=msg
                        )
                        logger.info(f"✅ Appointment reminder sent to {lead.telegram_chat_id} for appt {appt.id}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to send appointment reminder: {e}")
        except Exception as e:
            logger.error(f"❌ Appointment reminder check failed: {e}")
    
    async def set_timeout(
        self,
        telegram_id: int,
        tenant_id: int,
        state: ConversationState,
        timeout_minutes: int = 10
    ):
        """
        Set timeout tracker for user in specific state.
        
        Args:
            telegram_id: Telegram user ID
            tenant_id: Tenant ID
            state: Current conversation state
            timeout_minutes: Minutes to wait before follow-up
        """
        await redis_manager.set_timeout_tracker(
            telegram_id=telegram_id,
            tenant_id=tenant_id,
            state=state.value,
            timeout_minutes=timeout_minutes
        )
        
        # Schedule follow-up message
        asyncio.create_task(
            self._send_followup_after_delay(
                telegram_id=telegram_id,
                tenant_id=tenant_id,
                state=state,
                delay_minutes=timeout_minutes
            )
        )
    
    async def clear_timeout(self, telegram_id: int, tenant_id: int):
        """Clear timeout tracker (user responded)."""
        await redis_manager.clear_timeout_tracker(telegram_id, tenant_id)
    
    async def _send_followup_after_delay(
        self,
        telegram_id: int,
        tenant_id: int,
        state: ConversationState,
        delay_minutes: int
    ):
        """
        Wait for specified delay, then send follow-up if user still silent.
        
        Args:
            telegram_id: Telegram user ID
            tenant_id: Tenant ID
            state: Conversation state when timeout was set
            delay_minutes: How long to wait
        """
        try:
            # Wait for delay
            await asyncio.sleep(delay_minutes * 60)
            
            # Check if timeout tracker still exists (not cleared by user response)
            tracker = await redis_manager.get_timeout_tracker(telegram_id, tenant_id)
            
            if tracker and not tracker.get("sent"):
                # Get lead for language preference
                from database import AsyncSessionLocal
                async with AsyncSessionLocal() as db:
                    lead = await get_lead_by_telegram_id(db, telegram_id, tenant_id)
                    
                    if not lead:
                        logger.warning(f"Lead not found: {telegram_id}")
                        return
                    
                    lang = lead.language or Language.FA
                    
                    # Get appropriate follow-up message
                    messages = FOLLOWUP_MESSAGES.get(state, FOLLOWUP_MESSAGES[ConversationState.WARMUP])
                    followup_text = messages.get(lang, messages[Language.EN])
                    
                    # Send follow-up message
                    await self.bot.send_message(
                        chat_id=telegram_id,
                        text=followup_text
                    )
                    
                    # Mark as sent
                    await redis_manager.mark_timeout_sent(telegram_id, tenant_id)
                    
                    logger.info(f"📨 Follow-up sent to user {telegram_id} (state: {state.value})")
        
        except asyncio.CancelledError:
            logger.debug(f"Follow-up cancelled for user {telegram_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send follow-up to {telegram_id}: {e}")


# Global instance (will be initialized with bot)
timeout_scheduler: Optional[TimeoutScheduler] = None


def init_timeout_scheduler(bot: Bot) -> TimeoutScheduler:
    """Initialize timeout scheduler with bot instance."""
    global timeout_scheduler
    timeout_scheduler = TimeoutScheduler(bot)
    return timeout_scheduler
