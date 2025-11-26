"""
ArtinSmartRealty V2 - The Super Brain
AI Core Logic using Google Gemini 2.0 Flash
Multi-Language Support, Voice Intelligence, Turbo Qualification Flow
"""

import os
import re
import json
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass
import google.generativeai as genai

from database import (
    Lead, Tenant, ConversationState, Language,
    TransactionType, PropertyType, PaymentMethod, Purpose,
    LeadStatus, update_lead, get_available_slots, DayOfWeek
)


# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# ==================== LANGUAGE DETECTION & TRANSLATIONS ====================

LANGUAGE_PATTERNS = {
    Language.FA: r'[\u0600-\u06FF]',  # Persian/Arabic script
    Language.AR: r'[\u0600-\u06FF]',  # Arabic script (same range)
    Language.RU: r'[\u0400-\u04FF]',  # Cyrillic script
    Language.EN: r'^[a-zA-Z\s\d\.,!?\'\"-]+$'  # Latin only
}

# Translations dictionary
TRANSLATIONS = {
    "welcome": {
        Language.EN: "👋 Welcome! I'm {agent_name}'s AI Assistant. How can I help you find your perfect property in Dubai?",
        Language.FA: "👋 سلام! من دستیار هوش مصنوعی {agent_name} هستم. چگونه می‌توانم به شما در یافتن ملک مناسب در دبی کمک کنم؟",
        Language.AR: "👋 مرحبًا! أنا المساعد الذكي لـ {agent_name}. كيف يمكنني مساعدتك في العثور على عقارك المثالي في دبي؟",
        Language.RU: "👋 Добро пожаловать! Я AI-ассистент {agent_name}. Как я могу помочь вам найти идеальную недвижимость в Дубае?"
    },
    "hook_roi": {
        Language.EN: "🏠 Get a FREE ROI Analysis!\n\nSee how much you could earn from Dubai Real Estate investment.\n\nWould you like to receive your personalized report?",
        Language.FA: "🏠 تحلیل بازگشت سرمایه رایگان!\n\nببینید چقدر می‌توانید از سرمایه‌گذاری در املاک دبی درآمد کسب کنید.\n\nآیا می‌خواهید گزارش شخصی‌سازی شده خود را دریافت کنید؟",
        Language.AR: "🏠 احصل على تحليل عائد الاستثمار مجانًا!\n\nاكتشف كم يمكنك أن تكسب من الاستثمار العقاري في دبي.\n\nهل تريد استلام تقريرك المخصص؟",
        Language.RU: "🏠 Получите БЕСПЛАТНЫЙ анализ ROI!\n\nУзнайте, сколько вы можете заработать на недвижимости в Дубае.\n\nХотите получить персональный отчёт?"
    },
    "phone_request": {
        Language.EN: "📱 Great! To send you the personalized ROI report, I'll need your phone number.\n\nPlease share your WhatsApp number:",
        Language.FA: "📱 عالی! برای ارسال گزارش ROI شخصی‌سازی شده، به شماره تلفن شما نیاز دارم.\n\nلطفاً شماره واتساپ خود را ارسال کنید:",
        Language.AR: "📱 رائع! لإرسال تقرير العائد على الاستثمار المخصص لك، أحتاج إلى رقم هاتفك.\n\nيرجى مشاركة رقم الواتساب الخاص بك:",
        Language.RU: "📱 Отлично! Чтобы отправить вам персональный отчёт ROI, мне нужен ваш номер телефона.\n\nПожалуйста, поделитесь вашим номером WhatsApp:"
    },
    "transaction_type": {
        Language.EN: "🏘️ Are you looking to Buy or Rent?",
        Language.FA: "🏘️ آیا می‌خواهید بخرید یا اجاره کنید؟",
        Language.AR: "🏘️ هل تريد الشراء أم الإيجار؟",
        Language.RU: "🏘️ Вы хотите купить или арендовать?"
    },
    "property_type": {
        Language.EN: "🏢 What type of property?\n\n• Residential (Apartment, Villa)\n• Commercial (Office, Retail)",
        Language.FA: "🏢 چه نوع ملکی؟\n\n• مسکونی (آپارتمان، ویلا)\n• تجاری (دفتر، مغازه)",
        Language.AR: "🏢 ما نوع العقار؟\n\n• سكني (شقة، فيلا)\n• تجاري (مكتب، متجر)",
        Language.RU: "🏢 Какой тип недвижимости?\n\n• Жилая (Квартира, Вилла)\n• Коммерческая (Офис, Магазин)"
    },
    "budget": {
        Language.EN: "💰 What's your budget range?",
        Language.FA: "💰 بودجه شما چقدر است؟",
        Language.AR: "💰 ما هي ميزانيتك؟",
        Language.RU: "💰 Каков ваш бюджет?"
    },
    "payment_method": {
        Language.EN: "💳 Payment preference?",
        Language.FA: "💳 روش پرداخت ترجیحی؟",
        Language.AR: "💳 ما هي طريقة الدفع المفضلة؟",
        Language.RU: "💳 Предпочтительный способ оплаты?"
    },
    "purpose": {
        Language.EN: "🎯 What's the main purpose?\n\n• Investment (Rental Income)\n• Living (Personal Use)\n• Residency (Golden Visa)",
        Language.FA: "🎯 هدف اصلی چیست؟\n\n• سرمایه‌گذاری (درآمد اجاره)\n• زندگی (استفاده شخصی)\n• اقامت (ویزای طلایی)",
        Language.AR: "🎯 ما هو الهدف الرئيسي؟\n\n• استثمار (دخل إيجاري)\n• سكن (استخدام شخصي)\n• إقامة (تأشيرة ذهبية)",
        Language.RU: "🎯 Какова основная цель?\n\n• Инвестиции (Доход от аренды)\n• Проживание (Личное использование)\n• Резидентство (Золотая Виза)"
    },
    "schedule": {
        Language.EN: "📅 Perfect! Let's schedule a consultation.\n\nHere are available slots:",
        Language.FA: "📅 عالی! بیایید یک جلسه مشاوره تنظیم کنیم.\n\nاین زمان‌ها موجود است:",
        Language.AR: "📅 ممتاز! لنحدد موعدًا للاستشارة.\n\nإليك المواعيد المتاحة:",
        Language.RU: "📅 Отлично! Давайте запланируем консультацию.\n\nВот доступные слоты:"
    },
    "completed": {
        Language.EN: "✅ Thank you! Your consultation has been scheduled.\n\nOur agent {agent_name} will contact you at the scheduled time.\n\nSee you soon! 🏠",
        Language.FA: "✅ متشکریم! جلسه مشاوره شما تنظیم شد.\n\nمشاور ما {agent_name} در زمان مقرر با شما تماس خواهد گرفت.\n\nتا دیدار بعدی! 🏠",
        Language.AR: "✅ شكرًا لك! تم جدولة استشارتك.\n\nسيتواصل معك وكيلنا {agent_name} في الموعد المحدد.\n\nإلى اللقاء! 🏠",
        Language.RU: "✅ Спасибо! Ваша консультация запланирована.\n\nНаш агент {agent_name} свяжется с вами в назначенное время.\n\nДо скорой встречи! 🏠"
    },
    "ghost_reminder": {
        Language.EN: "👋 Hi! I noticed we didn't finish our conversation.\n\nDo you have any questions about Dubai Residency or Real Estate Investment?",
        Language.FA: "👋 سلام! متوجه شدم که گفتگوی ما تمام نشد.\n\nآیا سوالی درباره اقامت دبی یا سرمایه‌گذاری در املاک دارید؟",
        Language.AR: "👋 مرحبًا! لاحظت أننا لم ننهِ محادثتنا.\n\nهل لديك أي أسئلة حول الإقامة في دبي أو الاستثمار العقاري؟",
        Language.RU: "👋 Привет! Я заметил, что мы не закончили наш разговор.\n\nЕсть вопросы о резидентстве в Дубае или инвестициях в недвижимость?"
    },
    "btn_yes": {
        Language.EN: "✅ Yes",
        Language.FA: "✅ بله",
        Language.AR: "✅ نعم",
        Language.RU: "✅ Да"
    },
    "btn_no": {
        Language.EN: "❌ No",
        Language.FA: "❌ خیر",
        Language.AR: "❌ لا",
        Language.RU: "❌ Нет"
    },
    "btn_buy": {
        Language.EN: "🏠 Buy",
        Language.FA: "🏠 خرید",
        Language.AR: "🏠 شراء",
        Language.RU: "🏠 Купить"
    },
    "btn_rent": {
        Language.EN: "🏠 Rent",
        Language.FA: "🏠 اجاره",
        Language.AR: "🏠 إيجار",
        Language.RU: "🏠 Аренда"
    },
    "btn_residential": {
        Language.EN: "🏢 Residential",
        Language.FA: "🏢 مسکونی",
        Language.AR: "🏢 سكني",
        Language.RU: "🏢 Жилая"
    },
    "btn_commercial": {
        Language.EN: "🏢 Commercial",
        Language.FA: "🏢 تجاری",
        Language.AR: "🏢 تجاري",
        Language.RU: "🏢 Коммерческая"
    },
    "btn_cash": {
        Language.EN: "💵 Cash",
        Language.FA: "💵 نقدی",
        Language.AR: "💵 نقدًا",
        Language.RU: "💵 Наличные"
    },
    "btn_installment": {
        Language.EN: "📊 Installment",
        Language.FA: "📊 اقساط",
        Language.AR: "📊 تقسيط",
        Language.RU: "📊 Рассрочка"
    },
    "btn_investment": {
        Language.EN: "📈 Investment",
        Language.FA: "📈 سرمایه‌گذاری",
        Language.AR: "📈 استثمار",
        Language.RU: "📈 Инвестиции"
    },
    "btn_living": {
        Language.EN: "🏡 Living",
        Language.FA: "🏡 زندگی",
        Language.AR: "🏡 سكن",
        Language.RU: "🏡 Проживание"
    },
    "btn_residency": {
        Language.EN: "🛂 Residency/Visa",
        Language.FA: "🛂 اقامت/ویزا",
        Language.AR: "🛂 إقامة/تأشيرة",
        Language.RU: "🛂 Резидентство/Виза"
    }
}

# Budget options in AED
BUDGET_OPTIONS = {
    Language.EN: ["Under 500K AED", "500K - 1M AED", "1M - 2M AED", "2M - 5M AED", "5M+ AED"],
    Language.FA: ["زیر 500 هزار درهم", "500 هزار تا 1 میلیون درهم", "1 تا 2 میلیون درهم", "2 تا 5 میلیون درهم", "بالای 5 میلیون درهم"],
    Language.AR: ["أقل من 500 ألف درهم", "500 ألف - 1 مليون درهم", "1 - 2 مليون درهم", "2 - 5 مليون درهم", "أكثر من 5 مليون درهم"],
    Language.RU: ["До 500 тыс. AED", "500 тыс. - 1 млн AED", "1 - 2 млн AED", "2 - 5 млн AED", "5+ млн AED"]
}

BUDGET_RANGES = {
    0: (0, 500000),
    1: (500000, 1000000),
    2: (1000000, 2000000),
    3: (2000000, 5000000),
    4: (5000000, None)
}


# ==================== HELPER CLASSES ====================

@dataclass
class BrainResponse:
    """Response from the Brain to be sent back through the platform."""
    message: str
    buttons: Optional[List[Dict[str, str]]] = None  # [{text, callback_data}]
    next_state: Optional[ConversationState] = None
    lead_updates: Optional[Dict[str, Any]] = None
    should_generate_roi: bool = False
    schedule_slots: Optional[List[Dict]] = None


# ==================== BRAIN CLASS ====================

class Brain:
    """
    The Super Brain - AI Core for ArtinSmartRealty
    Handles all conversation logic, language detection, voice processing,
    and state machine for Turbo Qualification Flow.
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.agent_name = tenant.name or "ArtinSmartRealty"
        
        # Initialize Gemini model
        if GEMINI_API_KEY:
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None
    
    def detect_language(self, text: str) -> Language:
        """Auto-detect language from text."""
        if not text:
            return Language.EN
        
        # Check for Persian/Arabic characters
        if re.search(LANGUAGE_PATTERNS[Language.FA], text):
            # Try to distinguish Persian from Arabic using common words
            persian_words = ['است', 'این', 'آن', 'من', 'تو', 'ما', 'شما', 'چه', 'که']
            arabic_words = ['هذا', 'هذه', 'أنا', 'أنت', 'نحن', 'ما', 'لا', 'في']
            
            persian_count = sum(1 for word in persian_words if word in text)
            arabic_count = sum(1 for word in arabic_words if word in text)
            
            return Language.FA if persian_count >= arabic_count else Language.AR
        
        # Check for Cyrillic (Russian)
        if re.search(LANGUAGE_PATTERNS[Language.RU], text):
            return Language.RU
        
        return Language.EN
    
    def get_text(self, key: str, lang: Language, **kwargs) -> str:
        """Get translated text with variable substitution."""
        text = TRANSLATIONS.get(key, {}).get(lang, TRANSLATIONS.get(key, {}).get(Language.EN, key))
        return text.format(agent_name=self.agent_name, **kwargs)
    
    def get_budget_options(self, lang: Language) -> List[str]:
        """Get budget options in the specified language."""
        return BUDGET_OPTIONS.get(lang, BUDGET_OPTIONS[Language.EN])
    
    async def process_voice(self, audio_data: bytes, file_extension: str = "ogg") -> Tuple[str, Dict[str, Any]]:
        """
        Process voice message using Gemini.
        Returns transcript and extracted entities.
        """
        if not self.model:
            return "", {}
        
        try:
            # Create a prompt for voice transcription and entity extraction
            # Note: Actual audio processing would require additional setup
            # This is a placeholder for the voice processing logic
            
            # For production, you'd use Gemini's multimodal capabilities
            # or a dedicated speech-to-text service
            
            return "", {}
        except Exception as e:
            print(f"Voice processing error: {e}")
            return "", {}
    
    async def extract_entities_from_text(self, text: str, lang: Language) -> Dict[str, Any]:
        """
        Use Gemini to extract real estate entities from text.
        Returns: budget, location, property_type, residency_goal, etc.
        """
        if not self.model or not text:
            return {}
        
        try:
            prompt = f"""
            Analyze this real estate inquiry and extract relevant information.
            Text: "{text}"
            
            Extract the following if mentioned:
            - budget_min: number (in AED)
            - budget_max: number (in AED)
            - location: string (area/neighborhood in Dubai)
            - property_type: "residential" or "commercial"
            - transaction_type: "buy" or "rent"
            - purpose: "investment", "living", or "residency" (Golden Visa)
            - bedrooms: number
            - preferences: list of strings (e.g., "sea view", "high floor")
            
            Return ONLY a valid JSON object with the extracted fields.
            If a field is not mentioned, omit it from the response.
            """
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            # Parse JSON from response
            response_text = response.text.strip()
            # Try to extract JSON from the response
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return {}
        except Exception as e:
            print(f"Entity extraction error: {e}")
            return {}
    
    async def generate_ai_response(self, user_message: str, lead: Lead, context: str = "") -> str:
        """
        Generate a contextual AI response using Gemini.
        Used for free-form questions outside the qualification flow.
        """
        if not self.model:
            return self.get_text("welcome", lead.language or Language.EN)
        
        try:
            system_prompt = f"""
            You are {self.agent_name}'s professional AI assistant for Dubai Real Estate.
            
            CRITICAL RULES:
            1. ALWAYS respond in {lead.language.value.upper()} language
            2. Be helpful, professional, and knowledgeable about Dubai real estate
            3. Mention Golden Visa opportunities when relevant (minimum 2M AED investment)
            4. Keep responses concise and actionable
            5. If asked about specific properties, mention that the agent can provide listings
            
            Agent: {self.agent_name}
            Current lead status: {lead.status.value if lead.status else 'new'}
            Budget interest: {lead.budget_min}-{lead.budget_max} {lead.budget_currency or 'AED'}
            Purpose: {lead.purpose.value if lead.purpose else 'not specified'}
            
            Context: {context}
            """
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                [system_prompt, f"User says: {user_message}"]
            )
            
            return response.text.strip()
        except Exception as e:
            print(f"AI response error: {e}")
            return self.get_text("welcome", lead.language or Language.EN)
    
    async def process_message(
        self, 
        lead: Lead, 
        message: str, 
        callback_data: Optional[str] = None
    ) -> BrainResponse:
        """
        Main entry point for processing user messages.
        Implements the Turbo Qualification State Machine.
        """
        lang = lead.language or self.detect_language(message)
        current_state = lead.conversation_state or ConversationState.START
        
        # Update lead language if detected differently
        lead_updates = {"language": lang}
        
        # State Machine Logic
        if current_state == ConversationState.START:
            return self._handle_start(lang)
        
        elif current_state == ConversationState.WELCOME:
            return self._handle_welcome_response(lang, callback_data)
        
        elif current_state == ConversationState.HOOK:
            return self._handle_hook_response(lang, callback_data)
        
        elif current_state == ConversationState.PHONE_GATE:
            return await self._handle_phone_gate(lang, message, lead_updates)
        
        elif current_state == ConversationState.TRANSACTION_TYPE:
            return self._handle_transaction_type(lang, callback_data, lead_updates)
        
        elif current_state == ConversationState.PROPERTY_TYPE:
            return self._handle_property_type(lang, callback_data, lead_updates)
        
        elif current_state == ConversationState.BUDGET:
            return self._handle_budget(lang, callback_data, lead_updates)
        
        elif current_state == ConversationState.PAYMENT_METHOD:
            return self._handle_payment_method(lang, callback_data, lead_updates)
        
        elif current_state == ConversationState.PURPOSE:
            return self._handle_purpose(lang, callback_data, lead_updates)
        
        elif current_state == ConversationState.SCHEDULE:
            return await self._handle_schedule(lang, callback_data, lead)
        
        elif current_state == ConversationState.COMPLETED:
            # For completed leads, use AI for free-form conversation
            ai_response = await self.generate_ai_response(message, lead)
            return BrainResponse(message=ai_response)
        
        # Default: restart flow
        return self._handle_start(lang)
    
    def _handle_start(self, lang: Language) -> BrainResponse:
        """Initial state - send welcome message."""
        return BrainResponse(
            message=self.get_text("welcome", lang),
            next_state=ConversationState.WELCOME,
            buttons=[
                {"text": self.get_text("btn_yes", lang), "callback_data": "start_yes"},
                {"text": self.get_text("btn_no", lang), "callback_data": "start_no"}
            ]
        )
    
    def _handle_welcome_response(self, lang: Language, callback_data: Optional[str]) -> BrainResponse:
        """Handle response to welcome message - proceed to hook."""
        return BrainResponse(
            message=self.get_text("hook_roi", lang),
            next_state=ConversationState.HOOK,
            buttons=[
                {"text": self.get_text("btn_yes", lang), "callback_data": "roi_yes"},
                {"text": self.get_text("btn_no", lang), "callback_data": "roi_no"}
            ]
        )
    
    def _handle_hook_response(self, lang: Language, callback_data: Optional[str]) -> BrainResponse:
        """Handle ROI hook response - proceed to phone gate."""
        if callback_data == "roi_yes":
            return BrainResponse(
                message=self.get_text("phone_request", lang),
                next_state=ConversationState.PHONE_GATE,
                should_generate_roi=True
            )
        else:
            # Skip ROI but still collect phone
            return BrainResponse(
                message=self.get_text("phone_request", lang),
                next_state=ConversationState.PHONE_GATE
            )
    
    async def _handle_phone_gate(self, lang: Language, message: str, lead_updates: Dict) -> BrainResponse:
        """Hard gate - collect phone number."""
        # Extract phone number from message
        phone_pattern = r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}'
        phone_match = re.search(phone_pattern, message)
        
        if phone_match:
            phone = phone_match.group().strip()
            lead_updates["phone"] = phone
            lead_updates["status"] = LeadStatus.CONTACTED
            
            return BrainResponse(
                message=self.get_text("transaction_type", lang),
                next_state=ConversationState.TRANSACTION_TYPE,
                lead_updates=lead_updates,
                buttons=[
                    {"text": self.get_text("btn_buy", lang), "callback_data": "tx_buy"},
                    {"text": self.get_text("btn_rent", lang), "callback_data": "tx_rent"}
                ]
            )
        else:
            # Invalid phone - ask again
            return BrainResponse(
                message=self.get_text("phone_request", lang),
                next_state=ConversationState.PHONE_GATE
            )
    
    def _handle_transaction_type(self, lang: Language, callback_data: Optional[str], lead_updates: Dict) -> BrainResponse:
        """Handle Buy/Rent selection."""
        if callback_data == "tx_buy":
            lead_updates["transaction_type"] = TransactionType.BUY
        else:
            lead_updates["transaction_type"] = TransactionType.RENT
        
        return BrainResponse(
            message=self.get_text("property_type", lang),
            next_state=ConversationState.PROPERTY_TYPE,
            lead_updates=lead_updates,
            buttons=[
                {"text": self.get_text("btn_residential", lang), "callback_data": "prop_res"},
                {"text": self.get_text("btn_commercial", lang), "callback_data": "prop_comm"}
            ]
        )
    
    def _handle_property_type(self, lang: Language, callback_data: Optional[str], lead_updates: Dict) -> BrainResponse:
        """Handle Residential/Commercial selection."""
        if callback_data == "prop_res":
            lead_updates["property_type"] = PropertyType.RESIDENTIAL
        else:
            lead_updates["property_type"] = PropertyType.COMMERCIAL
        
        # Build budget buttons
        budget_options = self.get_budget_options(lang)
        buttons = [{"text": opt, "callback_data": f"budget_{i}"} for i, opt in enumerate(budget_options)]
        
        return BrainResponse(
            message=self.get_text("budget", lang),
            next_state=ConversationState.BUDGET,
            lead_updates=lead_updates,
            buttons=buttons
        )
    
    def _handle_budget(self, lang: Language, callback_data: Optional[str], lead_updates: Dict) -> BrainResponse:
        """Handle budget selection."""
        if callback_data and callback_data.startswith("budget_"):
            budget_idx = int(callback_data.split("_")[1])
            budget_range = BUDGET_RANGES.get(budget_idx, (0, None))
            lead_updates["budget_min"] = budget_range[0]
            lead_updates["budget_max"] = budget_range[1]
        
        return BrainResponse(
            message=self.get_text("payment_method", lang),
            next_state=ConversationState.PAYMENT_METHOD,
            lead_updates=lead_updates,
            buttons=[
                {"text": self.get_text("btn_cash", lang), "callback_data": "pay_cash"},
                {"text": self.get_text("btn_installment", lang), "callback_data": "pay_install"}
            ]
        )
    
    def _handle_payment_method(self, lang: Language, callback_data: Optional[str], lead_updates: Dict) -> BrainResponse:
        """Handle Cash/Installment selection."""
        if callback_data == "pay_cash":
            lead_updates["payment_method"] = PaymentMethod.CASH
        else:
            lead_updates["payment_method"] = PaymentMethod.INSTALLMENT
        
        return BrainResponse(
            message=self.get_text("purpose", lang),
            next_state=ConversationState.PURPOSE,
            lead_updates=lead_updates,
            buttons=[
                {"text": self.get_text("btn_investment", lang), "callback_data": "purp_invest"},
                {"text": self.get_text("btn_living", lang), "callback_data": "purp_living"},
                {"text": self.get_text("btn_residency", lang), "callback_data": "purp_residency"}
            ]
        )
    
    def _handle_purpose(self, lang: Language, callback_data: Optional[str], lead_updates: Dict) -> BrainResponse:
        """Handle purpose selection."""
        if callback_data == "purp_invest":
            lead_updates["purpose"] = Purpose.INVESTMENT
        elif callback_data == "purp_living":
            lead_updates["purpose"] = Purpose.LIVING
        else:
            lead_updates["purpose"] = Purpose.RESIDENCY
        
        lead_updates["status"] = LeadStatus.QUALIFIED
        
        return BrainResponse(
            message=self.get_text("schedule", lang),
            next_state=ConversationState.SCHEDULE,
            lead_updates=lead_updates,
            # Slots will be populated by the caller
            schedule_slots=[]
        )
    
    async def _handle_schedule(self, lang: Language, callback_data: Optional[str], lead: Lead) -> BrainResponse:
        """Handle scheduling selection."""
        if callback_data and callback_data.startswith("slot_"):
            # User selected a slot
            return BrainResponse(
                message=self.get_text("completed", lang),
                next_state=ConversationState.COMPLETED,
                lead_updates={"status": LeadStatus.VIEWING_SCHEDULED}
            )
        
        # Fetch available slots
        slots = await get_available_slots(lead.tenant_id)
        if slots:
            # Format slots for display
            slot_buttons = []
            for slot in slots[:5]:  # Max 5 options
                day = slot.day_of_week.value.capitalize()
                time_str = slot.start_time.strftime("%H:%M")
                slot_buttons.append({
                    "text": f"{day} {time_str}",
                    "callback_data": f"slot_{slot.id}"
                })
            
            return BrainResponse(
                message=self.get_text("schedule", lang),
                next_state=ConversationState.SCHEDULE,
                buttons=slot_buttons
            )
        else:
            # No slots available - complete anyway
            return BrainResponse(
                message=self.get_text("completed", lang),
                next_state=ConversationState.COMPLETED,
                lead_updates={"status": LeadStatus.QUALIFIED}
            )
    
    def get_ghost_reminder(self, lead: Lead) -> BrainResponse:
        """Get ghost protocol reminder message."""
        lang = lead.language or Language.EN
        return BrainResponse(
            message=self.get_text("ghost_reminder", lang),
            buttons=[
                {"text": self.get_text("btn_yes", lang), "callback_data": "ghost_yes"},
                {"text": self.get_text("btn_no", lang), "callback_data": "ghost_no"}
            ]
        )


# ==================== UTILITY FUNCTIONS ====================

async def process_telegram_message(
    tenant: Tenant,
    lead: Lead,
    message_text: str,
    callback_data: Optional[str] = None
) -> BrainResponse:
    """
    Convenience function to process a Telegram message through the Brain.
    """
    brain = Brain(tenant)
    return await brain.process_message(lead, message_text, callback_data)


async def process_voice_message(
    tenant: Tenant,
    lead: Lead,
    audio_data: bytes,
    file_extension: str = "ogg"
) -> Tuple[str, BrainResponse]:
    """
    Process a voice message and return transcript + response.
    """
    brain = Brain(tenant)
    transcript, entities = await brain.process_voice(audio_data, file_extension)
    
    # Update lead with extracted entities if any
    if entities:
        lead_updates = {}
        if "budget_min" in entities:
            lead_updates["budget_min"] = entities["budget_min"]
        if "budget_max" in entities:
            lead_updates["budget_max"] = entities["budget_max"]
        if "property_type" in entities:
            pt = entities["property_type"].lower()
            lead_updates["property_type"] = PropertyType.RESIDENTIAL if pt == "residential" else PropertyType.COMMERCIAL
        if "transaction_type" in entities:
            tt = entities["transaction_type"].lower()
            lead_updates["transaction_type"] = TransactionType.BUY if tt == "buy" else TransactionType.RENT
        if "purpose" in entities:
            p = entities["purpose"].lower()
            if p == "investment":
                lead_updates["purpose"] = Purpose.INVESTMENT
            elif p == "living":
                lead_updates["purpose"] = Purpose.LIVING
            else:
                lead_updates["purpose"] = Purpose.RESIDENCY
        if "preferences" in entities:
            lead_updates["taste_tags"] = entities["preferences"]
        
        if lead_updates:
            await update_lead(lead.id, **lead_updates)
    
    # Process as regular message with transcript
    response = await brain.process_message(lead, transcript or "voice message")
    
    return transcript, response
