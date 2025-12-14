"""
ArtinSmartRealty V2 - WhatsApp Bot Interface
Handles WhatsApp Business API calls and passes everything to brain.py
Supports both Meta WhatsApp Cloud API and Twilio WhatsApp API

=== UI ADAPTATION STRATEGY ===
The Brain returns button lists that work perfectly for Telegram but need adaptation for WhatsApp:

TELEGRAM vs WHATSAPP BUTTON CONSTRAINTS:
- Telegram: Unlimited inline buttons in keyboard layout
- WhatsApp: Max 3 Reply Buttons OR Max 10 List Items

ADAPTATION LOGIC (implemented in whatsapp_providers.py):
1. IF buttons <= 3: Use WhatsApp Reply Buttons (Quick Reply)
2. IF buttons > 3: Use WhatsApp List Message with "Select Option" button
   - Section Title: "Available Options"
   - Each button becomes a list row (max 10)

EXAMPLE FLOWS:
- Language Selection (4 options): List Message
- Goal Selection (3 options): Reply Buttons  
- Budget Ranges (5 options): List Message
- Property Types (6+ options): List Message
- Buy/Rent (2 options): Reply Buttons

This ensures IDENTICAL user experience while respecting platform constraints.
"""

import os
import logging
import httpx
from typing import Optional, Dict, List, Any
from datetime import datetime

from database import (
    Tenant, Lead, get_tenant_by_whatsapp_phone_id, get_or_create_lead,
    update_lead, ConversationState, book_slot, create_appointment,
    AppointmentType, async_session, Language
)
from brain import Brain, BrainResponse
from whatsapp_providers import get_whatsapp_provider, WhatsAppProvider
from vertical_router import get_vertical_router, VerticalMode, VerticalRouter
from redis_manager import RedisManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class WhatsAppBotHandler:
    """
    WhatsApp Bot Handler - Multi-Vertical Routing + Brain Interface
    Auto-detects and uses either Meta WhatsApp Cloud API or Twilio WhatsApp API.
    Routes users to appropriate business vertical (Realty, Expo, etc.)
    """
    
    def __init__(self, tenant: Tenant, redis_manager: Optional[RedisManager] = None):
        self.tenant = tenant
        self.brain = Brain(tenant)
        self.provider = get_whatsapp_provider(tenant)
        self.redis_manager = redis_manager
        self.router: Optional[VerticalRouter] = None
        
        # Initialize router if Redis available
        if redis_manager:
            self.router = get_vertical_router(redis_manager)
        
        if not self.provider:
            logger.warning(f"No WhatsApp provider configured for tenant {tenant.id}")
    
    async def send_message(
        self,
        to_phone: str,
        message: str,
        buttons: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """Send a message via WhatsApp (auto-routes to configured provider)."""
        if not self.provider:
            logger.error(f"WhatsApp not configured for tenant {self.tenant.id}")
            return False
        
        return await self.provider.send_message(to_phone, message, buttons)
    
    async def _get_or_create_lead(self, from_phone: str, profile_name: Optional[str] = None) -> Lead:
        """Get or create lead from WhatsApp phone number."""
        lead = await get_or_create_lead(
            tenant_id=self.tenant.id,
            whatsapp_phone=from_phone,
            source="whatsapp"
        )
        
        # Update name if available and not set
        if profile_name and not lead.name:
            await update_lead(lead.id, name=profile_name)
            lead.name = profile_name
        
        # Set phone if not set
        if not lead.phone:
            await update_lead(lead.id, phone=from_phone)
            lead.phone = from_phone
        
        return lead
    
    async def _get_or_create_lead_for_tenant(
        self, 
        from_phone: str, 
        profile_name: Optional[str],
        tenant_id: int
    ) -> Lead:
        """Get or create lead for a specific tenant (used in deep link routing)."""
        lead = await get_or_create_lead(
            tenant_id=tenant_id,
            whatsapp_phone=from_phone,
            source="whatsapp_deeplink"
        )
        
        # Update name if available and not set
        if profile_name and not lead.name:
            await update_lead(lead.id, name=profile_name)
            lead.name = profile_name
        
        # Set phone if not set
        if not lead.phone:
            await update_lead(lead.id, phone=from_phone)
            lead.phone = from_phone
        
        return lead
    
    async def _send_response(self, to_phone: str, response: BrainResponse, lead: Lead):
        """
        Send Brain response to user via WhatsApp.
        Mirrors the Telegram bot's comprehensive handling:
        - Message + Buttons (adapted for WhatsApp UI)
        - Contact request handling
        - ROI PDF generation and delivery
        - Admin notifications
        """
        message = response.message
        buttons = response.buttons
        
        # Handle contact request (WhatsApp doesn't have native "request contact" button like Telegram)
        if response.request_contact:
            contact_prompt = {
                Language.EN: "\n\n📱 Please share your phone number to continue.",
                Language.FA: "\n\n📱 لطفاً شماره تماس خود را برای ادامه ارسال کنید.",
                Language.AR: "\n\n📱 يرجى مشاركة رقم هاتفك للمتابعة.",
                Language.RU: "\n\n📱 Пожалуйста, поделитесь своим номером телефона."
            }
            message += contact_prompt.get(lead.language, contact_prompt[Language.EN])
        
        # Send main message with buttons
        await self.send_message(to_phone, message, buttons)
        
        # Update lead state if needed
        updates = response.lead_updates or {}
        if response.next_state:
            updates["conversation_state"] = response.next_state
        
        logger.info(f"💾 Saving updates for Lead {lead.id}: {updates}")
        
        if updates:
            await update_lead(lead.id, **updates)
            logger.info(f"✅ Lead {lead.id} updated successfully")
        
        # Handle PDF delivery if metadata flag is set (matching Telegram bot logic)
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
                
                # Send "Preparing..." message first (matching Telegram)
                preparing_msgs = {
                    Language.EN: "📊 Preparing your personalized ROI report... This will take just a moment!",
                    Language.FA: "📊 در حال آماده‌سازی گزارش ROI شخصی‌سازی شده... چند لحظه صبر کنید!",
                    Language.AR: "📊 جاري تحضير تقرير العائد على الاستثمار الشخصي... سيستغرق لحظات فقط!",
                    Language.RU: "📊 Готовлю персональный отчёт ROI... Это займёт всего мгновение!"
                }
                
                await self.send_message(
                    to_phone,
                    preparing_msgs.get(lang, preparing_msgs[Language.EN])
                )
                
                # Generate PDF
                pdf_bytes = await generate_roi_pdf(
                    tenant=self.tenant,
                    lead=lead,
                    property_value=lead.budget_max or lead.budget_min
                )
                
                # TODO: Upload PDF to cloud storage and get URL
                # For WhatsApp, we need to upload to a publicly accessible URL first
                # Example: AWS S3, Google Cloud Storage, or your file server
                # pdf_url = await self._upload_pdf_to_storage(pdf_bytes, f"roi_analysis_{lead.id}.pdf")
                
                caption_map = {
                    Language.EN: "📊 Here's your personalized ROI Analysis Report!",
                    Language.FA: "📊 این هم گزارش تحلیل سود سرمایه‌گذاری شما!",
                    Language.AR: "📊 إليك تقرير تحليل العائد على الاستثمار الشخصي!",
                    Language.RU: "📊 Вот ваш персональный отчёт ROI!"
                }
                
                logger.info(f"📄 ROI PDF generated ({len(pdf_bytes)} bytes) for lead {lead.id}")
                logger.warning("⚠️ PDF upload to cloud storage not implemented. Add upload logic here.")
                
                # Placeholder for sending document
                # await self.provider.send_document(
                #     to_phone,
                #     pdf_url,
                #     filename=f"ROI_Analysis_{self.tenant.name}.pdf",
                #     caption=caption_map.get(lang, caption_map[Language.EN])
                # )
                
            except Exception as e:
                logger.error(f"Failed to generate ROI PDF: {e}")
                import traceback
                traceback.print_exc()
                # Don't fail the whole message if PDF generation fails
        
        # === Handle admin notifications for hot leads (matching Telegram bot) ===
        if response.metadata and response.metadata.get("notify_admin"):
            admin_chat_id = self.tenant.admin_chat_id
            
            if admin_chat_id:
                try:
                    admin_message = response.metadata.get("admin_message", "🚨 New hot lead!")
                    
                    # Send to admin via Telegram (assuming admin uses Telegram)
                    # If admin wants WhatsApp notifications, add WhatsApp send logic here
                    if self.tenant.telegram_bot_token:
                        import telegram
                        bot = telegram.Bot(token=self.tenant.telegram_bot_token)
                        await bot.send_message(
                            chat_id=admin_chat_id,
                            text=admin_message,
                            parse_mode='HTML'
                        )
                        logger.info(f"🚨 Admin notification sent to {admin_chat_id} for lead {lead.id}")
                except Exception as e:
                    logger.error(f"❌ Failed to notify admin ({admin_chat_id}): {e}")
            else:
                logger.warning(f"⚠️ Admin ID not set for tenant {self.tenant.id}. Use /set_admin to configure.")
        # ======================================================================
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Handle incoming WhatsApp webhook with multi-vertical routing.
        
        Routing Priority:
        1. Deep link detection (TENANT_XXX, start_expo, start_realty) → Set mode
        2. Existing Redis session → Route to stored mode
        3. Menu selection → Set mode
        4. No mode → Send main menu
        
        Returns True if handled successfully.
        """
        if not self.provider:
            logger.error("No WhatsApp provider configured")
            return False
        
        try:
            # Parse webhook using provider
            parsed = self.provider.parse_webhook(payload)
            if not parsed:
                return False
            
            from_phone = parsed.get("from_phone")
            profile_name = parsed.get("profile_name")
            message_type = parsed.get("message_type")
            text = parsed.get("text")
            
            # ===== DEEP LINK TENANT ROUTING =====
            # Check if message contains TENANT_XXX pattern
            import re
            if message_type == "text" and text:
                tenant_match = re.search(r'TENANT_(\d+)', text)
                if tenant_match:
                    deep_link_tenant_id = int(tenant_match.group(1))
                    logger.info(f"🔗 Deep link detected: Routing to Tenant ID {deep_link_tenant_id}")
                    
                    # Get the specific tenant (FIX: Properly close session)
                    from database import async_session, Tenant
                    from sqlalchemy import select
                    
                    target_tenant = None
                    async with async_session() as session:
                        result = await session.execute(
                            select(Tenant).where(Tenant.id == deep_link_tenant_id)
                        )
                        target_tenant = result.scalar_one_or_none()
                    # Session auto-closed here
                    
                    if target_tenant:
                        # Create handler for this tenant
                        from brain import Brain
                        tenant_brain = Brain(target_tenant)
                        
                        # Get or create lead for this tenant
                        lead = await self._get_or_create_lead_for_tenant(
                            from_phone, profile_name, deep_link_tenant_id
                        )
                        
                        # Send welcome message
                        welcome_msg = {
                            Language.EN: f"👋 Welcome! You've connected with {target_tenant.name or target_tenant.company_name}.\n\nHow can we help you with Dubai Real Estate today?",
                            Language.FA: f"👋 خوش آمدید! شما به {target_tenant.name or target_tenant.company_name} متصل شدید.\n\nچطور میتونیم در املاک دبی کمکتون کنیم؟",
                            Language.AR: f"👋 مرحباً! تم توصيلك مع {target_tenant.name or target_tenant.company_name}.\n\nكيف يمكننا مساعدتك في عقارات دبي؟",
                            Language.RU: f"👋 Добро пожаловать! Вы подключились к {target_tenant.name or target_tenant.company_name}.\n\nКак мы можем помочь вам с недвижимостью в Дубае?"
                        }
                        
                        lang = lead.language or Language.EN
                        await self.send_message(from_phone, welcome_msg.get(lang, welcome_msg[Language.EN]))
                        
                        # Store tenant mapping in Redis for future messages
                        import redis.asyncio as redis
                        redis_client = None
                        try:
                            redis_client = redis.from_url(
                                os.getenv("REDIS_URL", "redis://localhost:6379"),
                                decode_responses=True
                            )
                            await redis_client.set(
                                f"whatsapp_tenant_map:{from_phone}",
                                str(deep_link_tenant_id),
                                ex=86400 * 30  # 30 days
                            )
                        finally:
                            if redis_client:
                                await redis_client.aclose()
                        
                        return True
            
            # Check if this phone number has a mapped tenant from previous deep link
            import redis.asyncio as redis
            redis_client = None
            mapped_tenant_id = None
            try:
                redis_client = redis.from_url(
                    os.getenv("REDIS_URL", "redis://localhost:6379"),
                    decode_responses=True
                )
                mapped_tenant_id = await redis_client.get(f"whatsapp_tenant_map:{from_phone}")
            finally:
                if redis_client:
                    await redis_client.aclose()
            
            if mapped_tenant_id:
                # Route to the mapped tenant
                logger.info(f"📍 Routing to previously mapped Tenant ID {mapped_tenant_id}")
                
                from database import async_session, Tenant
                from sqlalchemy import select
                
                mapped_tenant = None
                async with async_session() as session:
                    result = await session.execute(
                        select(Tenant).where(Tenant.id == int(mapped_tenant_id))
                    )
                    mapped_tenant = result.scalar_one_or_none()
                # Session auto-closed
                
                if mapped_tenant:
                    from brain import Brain
                    tenant_brain = Brain(mapped_tenant)
                    
                    lead = await self._get_or_create_lead_for_tenant(
                        from_phone, profile_name, int(mapped_tenant_id)
                    )
                    
                    # Process message with tenant's brain
                    if message_type == "text" and text:
                        response = await tenant_brain.process_message(lead, text, callback_data=None)
                        await self.send_message(from_phone, response.message, response.buttons)
                        
                        # Update lead
                        updates = response.lead_updates or {}
                        if response.next_state:
                            updates["conversation_state"] = response.next_state
                        if updates:
                                await update_lead(lead.id, **updates)
                        
                        return True
            
            # Get or create lead
            lead = await self._get_or_create_lead(from_phone, profile_name)
            
            # ===== MULTI-VERTICAL ROUTING LOGIC =====
            if message_type == "text" and text and self.router:
                # Route message to appropriate vertical
                mode, is_new_session = await self.router.route_message(from_phone, text)
                
                logger.info(f"Routed user {from_phone} to mode: {mode.value} (new={is_new_session})")
                
                # Handle based on mode
                if mode == VerticalMode.NONE:
                    # No mode detected - send main menu
                    await self._send_main_menu(from_phone, lead)
                    return True
                
                elif mode == VerticalMode.REALTY:
                    # Real Estate vertical - use existing brain
                    if is_new_session:
                        # Welcome message for new realty session
                        welcome_text = self._get_vertical_welcome(mode, lead.language or Language.EN)
                        response = await self.brain.process_message(lead, welcome_text, callback_data=None)
                    else:
                        # Continue existing conversation
                        response = await self.brain.process_message(lead, text, callback_data=None)
                    
                    await self._send_response(from_phone, response, lead)
                    return True
                
                elif mode == VerticalMode.EXPO:
                    # Expo vertical - TODO: Implement expo_brain.py
                    await self._handle_expo_mode(from_phone, text, lead, is_new_session)
                    return True
                
                elif mode == VerticalMode.SUPPORT:
                    # Support vertical
                    await self._handle_support_mode(from_phone, text, lead)
                    return True
            
            # Fallback: Process without routing (backwards compatibility)
            elif message_type == "text" and text:
                response = await self.brain.process_message(lead, text, callback_data=None)
                await self._send_response(from_phone, response, lead)
            
            elif message_type == "image":
                # Handle image - find similar properties
                image_id = parsed.get("media_id")
                
                if image_id:
                    try:
                        # Send processing message
                        from brain import Language
                        lang = lead.language or Language.EN
                        processing_msg = self.brain.get_text("image_processing", lang)
                        await self.send_message(from_phone, processing_msg)
                        
                        # Download and process image with timeout handling
                        image_url = await self._get_media_url(image_id)
                        if not image_url:
                            error_msg = self.brain.get_text("image_error", lang)
                            await self.send_message(from_phone, error_msg)
                            return True
                        
                        # Download image data
                        import httpx
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            headers = {"Authorization": f"Bearer {self.tenant.whatsapp_access_token}"}
                            img_response = await client.get(image_url, headers=headers)
                            
                            if img_response.status_code == 200:
                                image_data = img_response.content
                                
                                # Validate size (max 20MB)
                                if len(image_data) > 20 * 1024 * 1024:
                                    size_error = {
                                        Language.EN: "Image too large (max 20MB). Please send a smaller image.",
                                        Language.FA: "حجم تصویر بیش از حد مجاز است (حداکثر ۲۰ مگابایت). لطفا تصویر کوچکتری ارسال کنید.",
                                        Language.AR: "الصورة كبيرة جدًا (الحد الأقصى 20 ميجابايت). يرجى إرسال صورة أصغر.",
                                        Language.RU: "Изображение слишком большое (макс 20МБ). Отправьте изображение меньшего размера."
                                    }.get(lang, "Image too large (max 20MB)")
                                    await self.send_message(from_phone, size_error)
                                    return True
                                
                                # Process through brain
                                from brain import process_image_message
                                description, response = await process_image_message(
                                    tenant=self.tenant,
                                    lead=lead,
                                    image_data=image_data,
                                    file_extension="jpg"
                                )
                                await self._send_response(from_phone, response, lead)
                                
                                # Update lead state after image processing
                                updates = response.lead_updates or {}
                                if response.next_state:
                                    updates["conversation_state"] = response.next_state
                                if updates:
                                    await update_lead(lead.id, **updates)
                            else:
                                # Update lead state after image processing
                                updates = response.lead_updates or {}
                                if response.next_state:
                                    updates["conversation_state"] = response.next_state
                                if updates:
                                    await update_lead(lead.id, **updates)
                                
                                # Update lead state
                                updates = response.lead_updates or {}
                                if response.next_state:
                                    updates["conversation_state"] = response.next_state
                                if updates:
                                    await update_lead(lead.id, **updates)
                            else:
                                logger.error(f"Failed to download image: {img_response.status_code}")
                                error_msg = self.brain.get_text("image_error", lang)
                                await self.send_message(from_phone, error_msg)
                    except httpx.TimeoutException:
                        logger.error("Image download timeout")
                        timeout_error = {
                            Language.EN: "Image download timed out. Please try again.",
                            Language.FA: "زمان دانلود تصویر به پایان رسید. لطفا دوباره تلاش کنید.",
                            Language.AR: "انتهت مهلة تنزيل الصورة. يرجى المحاولة مرة أخرى.",
                            Language.RU: "Время загрузки изображения истекло. Попробуйте снова."
                        }.get(lang, "Image download timed out")
                        await self.send_message(from_phone, timeout_error)
                    except Exception as e:
                        logger.error(f"Error processing WhatsApp image: {e}")
                        error_msg = self.brain.get_text("image_error", lang)
                        await self.send_message(from_phone, error_msg)
            
            elif message_type == "audio":
                # Handle voice message
                audio_id = parsed.get("media_id")
                
                if audio_id:
                    try:
                        # Download and process voice
                        audio_url = await self._get_media_url(audio_id)
                        if not audio_url:
                            from brain import Language
                            lang = lead.language or Language.EN
                            error_msg = self.brain.get_text("voice_error", lang)
                            await self.send_message(from_phone, error_msg)
                            return True
                        
                        # Download audio data with timeout handling
                        import httpx
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            headers = {"Authorization": f"Bearer {self.tenant.whatsapp_access_token}"}
                            audio_response = await client.get(audio_url, headers=headers)
                            
                            if audio_response.status_code == 200:
                                audio_data = audio_response.content
                                
                                # Validate size (max 16MB for Gemini)
                                if len(audio_data) > 16 * 1024 * 1024:
                                    from brain import Language
                                    lang = lead.language or Language.EN
                                    size_error = {
                                        Language.EN: "Voice message too large (max 16MB). Please send a shorter message.",
                                        Language.FA: "حجم پیام صوتی بیش از حد مجاز است (حداکثر ۱۶ مگابایت). لطفا پیام کوتاه‌تری ارسال کنید.",
                                        Language.AR: "رسالة صوتية كبيرة جدًا (الحد الأقصى 16 ميجابايت). يرجى إرسال رسالة أقصر.",
                                        Language.RU: "Голосовое сообщение слишком большое (макс 16МБ). Отправьте более короткое сообщение."
                                    }.get(lang, "Voice message too large (max 16MB)")
                                    await self.send_message(from_phone, size_error)
                                    return True
                                
                                # Process through brain
                                from brain import process_voice_message
                                transcript, response = await process_voice_message(
                                    tenant=self.tenant,
                                    lead=lead,
                                    audio_data=audio_data,
                                    file_extension="ogg"
                                )
                                await self._send_response(from_phone, response, lead)
                            else:
                                logger.error(f"Failed to download audio: {audio_response.status_code}")
                                from brain import Language
                                lang = lead.language or Language.EN
                                error_msg = self.brain.get_text("voice_error", lang)
                                await self.send_message(from_phone, error_msg)
                    except httpx.TimeoutException:
                        logger.error("Voice download timeout")
                        from brain import Language
                        lang = lead.language or Language.EN
                        timeout_error = {
                            Language.EN: "Voice download timed out. Please try again.",
                            Language.FA: "زمان دانلود پیام صوتی به پایان رسید. لطفا دوباره تلاش کنید.",
                            Language.AR: "انتهت مهلة تنزيل الرسالة الصوتية. يرجى المحاولة مرة أخرى.",
                            Language.RU: "Время загрузки голосового сообщения истекло. Попробуйте снова."
                        }.get(lang, "Voice download timed out")
                        await self.send_message(from_phone, timeout_error)
                    except Exception as e:
                        logger.error(f"Error processing WhatsApp voice: {e}")
                        from brain import Language
                        lang = lead.language or Language.EN
                        error_msg = self.brain.get_text("voice_error", lang)
                        await self.send_message(from_phone, error_msg)
            
            elif message_type == "location":
                # Handle location sharing
                location = parsed.get("location", {})
                lat = location.get("latitude")
                lon = location.get("longitude")
                
                if lat and lon:
                    location_text = f"📍 Location: {lat}, {lon}"
                    response = await self.brain.process_message(lead, location_text, "")
                    await self._send_response(from_phone, response, lead)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle webhook: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def _send_main_menu(self, to_phone: str, lead: Lead):
        """Send main menu with vertical selection options."""
        if not self.router:
            # Fallback if router not available
            await self.send_message(
                to_phone,
                "👋 Welcome! Please send 'start_realty' for real estate or 'start_expo' for expo services."
            )
            return
        
        menu = self.router.get_main_menu_content(
            self.tenant, 
            lead.language.value if lead.language else "EN"
        )
        
        # Send as interactive list message
        success = await self.provider.send_message(
            to_phone,
            menu["body"],
            buttons=[
                {"text": row["title"], "callback_data": row["id"]}
                for section in menu["sections"]
                for row in section["rows"]
            ]
        )
        
        if not success:
            # Fallback to simple text if interactive fails
            text_menu = f"{menu['header']}\n\n{menu['body']}\n\n"
            for section in menu["sections"]:
                for row in section["rows"]:
                    text_menu += f"{row['title']}\n{row['description']}\n\n"
            await self.send_message(to_phone, text_menu)
    
    def _get_vertical_welcome(self, mode: VerticalMode, language: Language) -> str:
        """Get welcome message for a specific vertical."""
        messages = {
            VerticalMode.REALTY: {
                Language.EN: "Welcome to Real Estate Services! How can I help you find your perfect property today?",
                Language.FA: "به سرویس املاک خوش آمدید! چطور می‌توانم به شما در یافتن ملک ایده‌آل کمک کنم؟",
                Language.AR: "مرحباً بك في خدمات العقارات! كيف يمكنني مساعدتك في العثور على العقار المثالي؟",
                Language.RU: "Добро пожаловать в службу недвижимости! Как я могу помочь вам найти идеальную недвижимость?"
            },
            VerticalMode.EXPO: {
                Language.EN: "Welcome to Expo Assistant! I'll help you navigate the exhibition.",
                Language.FA: "به دستیار نمایشگاه خوش آمدید! من به شما در بازدید از نمایشگاه کمک می‌کنم.",
                Language.AR: "مرحباً بك في مساعد المعرض! سأساعدك في التنقل في المعرض.",
                Language.RU: "Добро пожаловать в помощник выставки! Я помогу вам ориентироваться на выставке."
            },
            VerticalMode.SUPPORT: {
                Language.EN: "Welcome to Support! How can our team assist you?",
                Language.FA: "به پشتیبانی خوش آمدید! تیم ما چطور می‌تواند به شما کمک کند؟",
                Language.AR: "مرحباً بك في الدعم! كيف يمكن لفريقنا مساعدتك؟",
                Language.RU: "Добро пожаловать в поддержку! Как наша команда может вам помочь?"
            }
        }
        
        return messages.get(mode, {}).get(language, messages[mode][Language.EN])
    
    async def _handle_expo_mode(self, from_phone: str, text: str, lead: Lead, is_new_session: bool):
        """Handle Expo vertical (placeholder for expo_brain.py)."""
        # TODO: Implement expo_brain.py with exhibition logic
        if is_new_session:
            welcome = self._get_vertical_welcome(VerticalMode.EXPO, lead.language or Language.EN)
            await self.send_message(from_phone, welcome)
        else:
            # Simple echo for now - replace with expo_brain logic
            await self.send_message(
                from_phone,
                f"🎪 Expo Mode Active\n\nYou said: {text}\n\n(Expo brain coming soon!)"
            )
    
    async def _handle_support_mode(self, from_phone: str, text: str, lead: Lead):
        """Handle Support vertical."""
        # Support logic - forward to human agent or provide help
        support_message = {
            Language.EN: "📞 Support request received!\n\nOur team will contact you shortly.\n\nYour message: {text}",
            Language.FA: "📞 درخواست پشتیبانی دریافت شد!\n\nتیم ما به زودی با شما تماس خواهد گرفت.\n\nپیام شما: {text}",
            Language.AR: "📞 تم استلام طلب الدعم!\n\nسيتصل بك فريقنا قريباً.\n\nرسالتك: {text}",
            Language.RU: "📞 Запрос в поддержку получен!\n\nНаша команда свяжется с вами в ближайшее время.\n\nВаше сообщение: {text}"
        }
        
        lang = lead.language or Language.EN
        message = support_message.get(lang, support_message[Language.EN]).format(text=text)
        
        await self.send_message(from_phone, message)
        
        # TODO: Log support request to database or notification system
        logger.info(f"Support request from {from_phone}: {text}")
    
    async def _get_media_url(self, media_id: str) -> Optional[str]:
        """Get download URL for a media file."""
        if not self.tenant.whatsapp_access_token:
            return None
        
        url = f"{self.api_base}/{media_id}"
        headers = {
            "Authorization": f"Bearer {self.tenant.whatsapp_access_token}"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("url")
        except httpx.HTTPError as e:
            logger.error(f"Failed to get media URL: {e}")
            return None
    
    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[List[Dict]] = None
    ) -> bool:
        """Send a WhatsApp template message (for initiating conversations)."""
        if not self.tenant.whatsapp_phone_number_id or not self.tenant.whatsapp_access_token:
            logger.error(f"WhatsApp not configured for tenant {self.tenant.id}")
            return False
        
        url = f"{self.api_base}/{self.tenant.whatsapp_phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.tenant.whatsapp_access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                logger.info(f"Template message sent to {to_phone}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send template message: {e}")
            return False


# ==================== WEBHOOK VERIFICATION ====================

def verify_webhook(mode: str, token: str, challenge: str, verify_token: str) -> Optional[str]:
    """
    Verify WhatsApp webhook subscription.
    Called when Meta sends a GET request to verify the webhook.
    """
    if mode == "subscribe" and token == verify_token:
        logger.info("WhatsApp webhook verified")
        return challenge
    else:
        logger.warning(f"WhatsApp webhook verification failed: mode={mode}")
        return None


# ==================== MULTI-TENANT BOT MANAGER ====================

class WhatsAppBotManager:
    """
    Manages WhatsApp bots for multiple tenants with vertical routing.
    Unlike Telegram, WhatsApp uses webhooks so we don't need to maintain connections.
    """
    
    def __init__(self):
        self.handlers: Dict[str, WhatsAppBotHandler] = {}  # phone_number_id -> handler
        self.redis_managers: Dict[int, RedisManager] = {}  # tenant_id -> RedisManager
    
    async def get_redis_manager(self, tenant: Tenant) -> Optional[RedisManager]:
        """Get or create RedisManager for tenant."""
        if tenant.id in self.redis_managers:
            return self.redis_managers[tenant.id]
        
        try:
            redis_manager = RedisManager()
            await redis_manager.connect()
            self.redis_managers[tenant.id] = redis_manager
            logger.info(f"RedisManager created for tenant {tenant.id}")
            return redis_manager
        except Exception as e:
            logger.error(f"Failed to create RedisManager for tenant {tenant.id}: {e}")
            return None
    
    async def get_handler(self, phone_number_id: str) -> Optional[WhatsAppBotHandler]:
        """Get or create handler for a tenant by phone number ID."""
        if phone_number_id in self.handlers:
            return self.handlers[phone_number_id]
        
        # Load tenant from database
        tenant = await get_tenant_by_whatsapp_phone_id(phone_number_id)
        if not tenant:
            logger.warning(f"No tenant found for WhatsApp phone ID: {phone_number_id}")
            return None
        
        # Get RedisManager for vertical routing
        redis_manager = await self.get_redis_manager(tenant)
        
        handler = WhatsAppBotHandler(tenant, redis_manager)
        self.handlers[phone_number_id] = handler
        logger.info(f"WhatsApp handler created for tenant {tenant.id} (phone_id: {phone_number_id})")
        return handler
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> bool:
        """Route webhook to appropriate handler."""
        try:
            entry = payload.get("entry", [])
            if not entry:
                return False
            
            changes = entry[0].get("changes", [])
            if not changes:
                return False
            
            value = changes[0].get("value", {})
            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            
            if not phone_number_id:
                logger.warning("No phone_number_id in webhook payload")
                return False
            
            handler = await self.get_handler(phone_number_id)
            if not handler:
                return False
            
            return await handler.handle_webhook(payload)
            
        except Exception as e:
            logger.error(f"Error routing WhatsApp webhook: {e}")
            return False


# Global bot manager instance
whatsapp_bot_manager = WhatsAppBotManager()
