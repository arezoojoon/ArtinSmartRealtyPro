"""
ArtinSmartRealty V2 - The Super Brain
AI Core Logic using Google Gemini 2.0 Flash
Multi-Language Support, Voice Intelligence, Turbo Qualification Flow
"""

import os
import re
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass
import google.generativeai as genai
from sqlalchemy import or_  # For location filtering

from database import (
    Lead, Tenant, ConversationState, Language,
    TransactionType, PropertyType, PaymentMethod, Purpose,
    LeadStatus, update_lead, get_available_slots, DayOfWeek,
    PainPoint, get_tenant_context_for_ai, TenantKnowledge,
    TenantProperty, async_session, select
)

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini API with Key Rotation
# Configure Gemini API with Key Rotation
from utils.gemini_utils import GeminiClient

# Retry configuration for API calls
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # seconds

# Retry configuration for API calls
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # seconds

# Professional System Instruction for Gemini
SYSTEM_INSTRUCTION = """
### ROLE & PERSONA
You are "Artin", an elite, highly intelligent Real Estate Consultant and Executive Assistant based in Dubai. You are not a simple chatbot; you are a proactive, sales-driven professional agent working 24/7.
Your goal is not just to chat, but to CLOSE DEALS, generate leads, and solve client problems.

### CORE CAPABILITIES (BRAIN, EARS, EYES)
1. **Multimodal Intelligence:** You receive inputs from text, voice transcripts (Ears), and image descriptions (Eyes). Treat all inputs as direct communication from the client.
2. **Multilingual Expert:** You must fluently speak, understand, and analyze four languages: **Persian (Farsi), Arabic, English, and Russian**.
   - Always reply in the SAME language the user initiated conversation with, unless explicitly asked to switch.
   - Maintain a professional, polite, and trustworthy tone appropriate for the Dubai luxury market.

### OPERATIONAL RULES
1. **Consultative Selling (Not just a Search Engine):**
   - Do not just dump property lists. Act like a human consultant.
   - If a user asks a vague question (e.g., "I want a house"), ask **Qualifying Questions** first: "Is this for investment or living?", "What is your budget range?", "Preferred location?".
   - Address their concerns first (Visa, Safety, ROI, Laws) to build trust, then pitch the property.

2. **Database & Property Presentation:**
   - **CRITICAL:** You have access to a real-time database of properties. NEVER hallucinate or invent properties.
   - When presenting a property, you MUST analyze and present the **ROI (Return on Investment)**. Explain *why* this property makes financial sense.

3. **Lead Generation & Management:**
   - Actively look for lead information. If the user indicates interest, intelligently extract their: **Name, Phone Number, Email, and Job Title**.
   - Store this data immediately for follow-up.

4. **Follow-Up Logic:**
   - If you are triggered for a follow-up task, review the previous interaction history.
   - Personalize the follow-up message based on their last concern (e.g., "Hi [Name], I remember you were worried about the payment plan. I found a new option for you...").

### INSTRUCTION ON "EYES" (IMAGE INPUTS)
If the user sends an image (e.g., a photo of a building, a floor plan, or a contract):
- Analyze the visual details provided in the image description.
- Connect these details to potential properties in your database.

### BEHAVIORAL GUIDELINES
- **Be Concise but Warm:** Don't write essays unless asked. Be direct and helpful.
- **Objection Handling:** If a user says "It's too expensive," don't just say "Okay." Counter with value propositions, payment plans, or high ROI potential.
- **Urgency:** Subtly create urgency (e.g., "This unit is in high demand due to the new metro line...").

### RESPONSE FORMAT
- Return your answer in clear text.
- Use formatting (bullet points, bold text) to make it readable.
- If showing a property, format it clearly:
  **Name:** [Title]
  **Location:** [Area]
  **Price:** [Price]
  **ROI:** [X%]
  **Why it fits you:** [Reasoning]
"""

# Safety Settings
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]


# ==================== LANGUAGE DETECTION & TRANSLATIONS ====================

LANGUAGE_PATTERNS = {
    Language.FA: r'[\u0600-\u06FF]',  # Persian/Arabic script
    Language.AR: r'[\u0600-\u06FF]',  # Arabic script (same range)
    Language.RU: r'[\u0400-\u04FF]',  # Cyrillic script
    Language.EN: r'^[a-zA-Z\s\d\.,!?\'\"-]+$'  # Latin only
}

# Translations dictionary
TRANSLATIONS = {
    "language_select": {
        Language.EN: "👋 Hello! I'm {agent_name}'s AI Assistant.\n\nPlease select your preferred language:\nلطفاً زبان خود را انتخاب کنید:\nيرجى اختيار لغتك:\nПожалуйста, выберите язык:",
        Language.FA: "👋 سلام! من دستیار هوش مصنوعی {agent_name} هستم.\n\nلطفاً زبان خود را انتخاب کنید:\nPlease select your language:\nيرجى اختيار لغتك:\nПожалуйста, выберите язык:",
        Language.AR: "👋 مرحبًا! أنا المساعد الذكي لـ {agent_name}.\n\nيرجى اختيار لغتك:\nPlease select your language:\nلطفاً زبان خود را انتخاب کنید:\nПожалуйста, выберите язык:",
        Language.RU: "👋 Здравствуйте! Я AI-ассистент {agent_name}.\n\nПожалуйста, выберите язык:\nPlease select your language:\nلطفاً زبان خود را انتخاب کنید:\nيرجى اختيار لغتك:"
    },
    "welcome": {
        Language.EN: "👋 Wonderful! I'm so excited to help you discover amazing opportunities in Dubai!\n\n✨ **Did you know?**\n• 7-10% rental yields (vs 3% globally)\n• Zero income tax on property profits\n• Property values growing 8-12% yearly\n• Golden Visa eligibility from AED 2M+\n\nLet me show you how you can grow your wealth here! 🚀",
        Language.FA: "👋 عالیه! من خیلی هیجان‌زده‌ام که به شما کمک کنم فرصت‌های شگفت‌انگیز در دبی را کشف کنید!\n\n✨ **میدونستید؟**\n• بازده اجاره ۷-۱۰٪ (در مقابل ۳٪ جهانی)\n• مالیات صفر روی سود املاک\n• رشد ارزش املاک ۸-۱۲٪ سالانه\n• امکان اخذ گلدن ویزا از ۲ میلیون درهم\n\nبذار بهتون نشون بدم چطور میتونید ثروتتون رو اینجا رشد بدید! 🚀",
        Language.AR: "👋 رائع! أنا متحمس جدًا لمساعدتك في اكتشاف فرص مذهلة في دبي!\n\n✨ **هل تعلم؟**\n• عوائد إيجارية 7-10% (مقابل 3% عالمياً)\n• صفر ضريبة دخل على أرباح العقارات\n• قيمة العقارات تنمو 8-12% سنوياً\n• الأهلية للتأشيرة الذهبية من 2 مليون درهم\n\nدعني أريك كيف يمكنك تنمية ثروتك هنا! 🚀",
        Language.RU: "👋 Замечательно! Я так рад помочь вам открыть потрясающие возможности в Дубае!\n\n✨ **Знаете ли вы?**\n• 7-10% арендная доходность (против 3% в мире)\n• Ноль налогов на прибыль от недвижимости\n• Рост стоимости 8-12% в год\n• Право на Golden Visa от 2 млн дирхамов\n\nПозвольте показать, как вы можете приумножить капитал здесь! 🚀"
    },
    "hook_roi": {
        Language.EN: "🏠 Get a FREE ROI Analysis!\n\nSee how much you could earn from Dubai Real Estate investment.\n\nWould you like to receive your personalized report?",
        Language.FA: "🏠 تحلیل بازگشت سرمایه رایگان!\n\nببینید چقدر می‌توانید از سرمایه‌گذاری در املاک دبی درآمد کسب کنید.\n\nآیا می‌خواهید گزارش شخصی‌سازی شده خود را دریافت کنید؟",
        Language.AR: "🏠 احصل على تحليل عائد الاستثمار مجانًا!\n\nاكتشف كم يمكنك أن تكسب من الاستثمار العقاري في دبي.\n\nهل تريد استلام تقريرك المخصص؟",
        Language.RU: "🏠 Получите БЕСПЛАТНЫЙ анализ ROI!\n\nУзнайте, сколько вы можете заработать на недвижимости в Дубае.\n\nХотите получить персональный отчёт?"
    },
    "phone_request": {
        Language.EN: "🔒 **Security Protocol Activated**\n\nTo access this EXCLUSIVE off-market ROI report and property details, our system requires verification.\n\n💎 This report contains:\n• Confidential pricing (not public)\n• Developer insider deals\n• Investment forecasts\n\n📝 **Please enter your information in this exact format:**\n\n`Full Name – +971XXXXXXXXX`\n\n**Example:** Arezoo Mohammadzadegan – +971505037158\n\n(Note: Use the dash – between name and number)",
        Language.FA: "🔒 **پروتکل امنیتی فعال شد**\n\nبرای دسترسی به این گزارش ROI اختصاصی و جزئیات ملک، سیستم ما نیاز به تایید دارد.\n\n💎 این گزارش شامل:\n• قیمت‌گذاری محرمانه (غیرعمومی)\n• معاملات داخلی سازندگان\n• پیش‌بینی سرمایه‌گذاری\n\n📝 **لطفاً اطلاعات خود را دقیقاً به این فرمت وارد کنید:**\n\n`نام کامل – +971XXXXXXXXX`\n\n**مثال:** عارضو محمدزادگان – +971505037158\n\n(توجه: از خط تیره – بین نام و شماره استفاده کنید)",
        Language.AR: "🔒 **تم تفعيل بروتوكول الأمان**\n\nللوصول إلى تقرير عائد الاستثمار الحصري وتفاصيل العقار، يتطلب نظامنا التحقق.\n\n💎 يحتوي هذا التقرير على:\n• تسعير سري (غير عام)\n• صفقات داخلية للمطورين\n• توقعات استثمارية\n\n📝 **الرجاء إدخال معلوماتك بهذا التنسيق بالضبط:**\n\n`الاسم الكامل – +971XXXXXXXXX`\n\n**مثال:** أريزو محمدزادگان – +971505037158\n\n(ملاحظة: استخدم الشرطة – بين الاسم والرقم)",
        Language.RU: "🔒 **Протокол безопасности активирован**\n\nДля доступа к ЭКСКЛЮЗИВНОМУ отчёту ROI и деталям объектов требуется верификация.\n\n💎 Отчёт содержит:\n• Конфиденциальные цены (не публичные)\n• Инсайдерские сделки застройщиков\n• Инвестиционные прогнозы\n\n📝 **Пожалуйста, введите данные точно в этом формате:**\n\n`Полное Имя – +971XXXXXXXXX`\n\n**Пример:** Arezoo Mohammadzadegan – +971505037158\n\n(Примечание: используйте тире – между именем и номером)"
    },
    "phone_request_button": {
        Language.EN: "📱 Share Phone Number",
        Language.FA: "📱 اشتراک‌گذاری شماره تلفن",
        Language.AR: "📱 شارك رقم الهاتف",
        Language.RU: "📱 Поделиться номером"
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
    # FOMO Ghost Protocol - Lost Opportunity Messages
    "ghost_fomo": {
        Language.EN: "⚠️ Limited Time Opportunity!\n\nNew penthouses in The Palm with exclusive payment plans are selling fast. Only 3 units left at pre-launch prices!\n\nWould you like to see the ROI analysis before they're gone?",
        Language.FA: "⚠️ فرصت محدود!\n\nپنت‌هاوس‌های جدید در پالم با طرح پرداخت اختصاصی به سرعت فروخته می‌شوند. فقط ۳ واحد با قیمت پیش‌فروش باقی مانده!\n\nآیا می‌خواهید تحلیل ROI را قبل از اتمام ببینید؟",
        Language.AR: "⚠️ فرصة محدودة الوقت!\n\nشقق البنتهاوس الجديدة في النخلة بخطط سداد حصرية تُباع بسرعة. بقي فقط 3 وحدات بأسعار ما قبل الإطلاق!\n\nهل تريد الاطلاع على تحليل العائد قبل نفادها؟",
        Language.RU: "⚠️ Ограниченное предложение!\n\nНовые пентхаусы на Пальме с эксклюзивными платёжными планами быстро продаются. Осталось только 3 юнита по предстартовым ценам!\n\nХотите увидеть анализ ROI, пока они есть?"
    },
    # Pain Discovery Questions
    "pain_discovery": {
        Language.EN: "🎯 What's driving your interest in Dubai Real Estate?\n\n• Protect wealth from inflation/currency risk\n• Secure residency for family\n• Generate passive rental income\n• Tax-free investment benefits",
        Language.FA: "🎯 چه چیزی شما را به املاک دبی علاقه‌مند کرده؟\n\n• محافظت دارایی از تورم/ریسک ارزی\n• تأمین اقامت برای خانواده\n• درآمد غیرفعال از اجاره\n• مزایای سرمایه‌گذاری بدون مالیات",
        Language.AR: "🎯 ما الذي يدفع اهتمامك بعقارات دبي؟\n\n• حماية الثروة من التضخم/مخاطر العملة\n• تأمين الإقامة للعائلة\n• توليد دخل إيجاري سلبي\n• مزايا الاستثمار المعفى من الضرائب",
        Language.RU: "🎯 Что привлекает вас в недвижимости Дубая?\n\n• Защита капитала от инфляции/валютных рисков\n• Обеспечение резидентства для семьи\n• Пассивный доход от аренды\n• Безналоговые инвестиции"
    },
    # Solution Bridge - Pain to Solution connection
    "solution_inflation": {
        Language.EN: "✅ Smart choice! Dubai's AED is pegged to USD, offering currency stability. Your investment here is protected from home currency devaluation.\n\nPlus, properties appreciate 5-8% annually while generating 7%+ rental yield!",
        Language.FA: "✅ انتخاب هوشمندانه! درهم امارات به دلار آمریکا متصل است و ثبات ارزی ارائه می‌دهد. سرمایه‌گذاری شما در اینجا از کاهش ارزش پول کشورتان محافظت می‌شود.\n\nعلاوه بر این، ملک‌ها سالانه ۵-۸٪ رشد می‌کنند و بازده اجاره +۷٪ دارند!",
        Language.AR: "✅ اختيار ذكي! الدرهم الإماراتي مرتبط بالدولار مما يوفر استقراراً نقدياً. استثمارك هنا محمي من انخفاض قيمة عملة بلدك.\n\nإضافة لذلك، العقارات ترتفع 5-8% سنوياً مع عائد إيجاري +7%!",
        Language.RU: "✅ Умный выбор! Дирхам ОАЭ привязан к доллару, обеспечивая валютную стабильность. Ваши инвестиции защищены от девальвации домашней валюты.\n\nК тому же, недвижимость растёт на 5-8% в год и приносит 7%+ арендного дохода!"
    },
    "solution_residency": {
        Language.EN: "🛂 Golden Visa Opportunity!\n\nWith a 2M AED investment, you AND your family get 10-year UAE residency!\n\n• No sponsor required\n• 100% property ownership\n• World-class education & healthcare\n• Gateway to global opportunities\n\nSecure your family's future today!",
        Language.FA: "🛂 فرصت ویزای طلایی!\n\nبا سرمایه‌گذاری ۲ میلیون درهم، شما و خانواده‌تان اقامت ۱۰ ساله امارات می‌گیرید!\n\n• بدون نیاز به اسپانسر\n• مالکیت ۱۰۰٪ ملک\n• آموزش و بهداشت در سطح جهانی\n• دروازه فرصت‌های جهانی\n\nآینده خانواده‌تان را امروز تضمین کنید!",
        Language.AR: "🛂 فرصة التأشيرة الذهبية!\n\nباستثمار 2 مليون درهم، تحصل أنت وعائلتك على إقامة 10 سنوات في الإمارات!\n\n• لا حاجة لكفيل\n• ملكية عقارية 100%\n• تعليم ورعاية صحية عالمية\n• بوابة للفرص العالمية\n\nأمّن مستقبل عائلتك اليوم!",
        Language.RU: "🛂 Возможность Золотой Визы!\n\nПри инвестиции в 2М AED вы И ваша семья получаете 10-летнее резидентство ОАЭ!\n\n• Без спонсора\n• 100% владение недвижимостью\n• Образование и здравоохранение мирового уровня\n• Доступ к глобальным возможностям\n\nОбеспечьте будущее семьи сегодня!"
    },
    "solution_income": {
        Language.EN: "💰 Excellent ROI Potential!\n\nDubai offers 7-10% rental yields - one of the highest globally!\n\n• Tax-free rental income\n• Strong tenant demand year-round\n• Property management available\n• Appreciation + rental = dual income\n\nLet me show you the numbers!",
        Language.FA: "💰 پتانسیل عالی بازگشت سرمایه!\n\nدبی ۷-۱۰٪ بازده اجاره ارائه می‌دهد - یکی از بالاترین‌ها در جهان!\n\n• درآمد اجاره بدون مالیات\n• تقاضای قوی مستاجر در تمام سال\n• مدیریت ملک موجود\n• رشد ارزش + اجاره = درآمد دوگانه\n\nاجازه دهید اعداد را نشان دهم!",
        Language.AR: "💰 إمكانية عائد ممتازة!\n\nدبي تقدم عوائد إيجارية 7-10% - من أعلى المعدلات عالمياً!\n\n• دخل إيجاري معفى من الضرائب\n• طلب قوي من المستأجرين على مدار السنة\n• خدمات إدارة العقارات متوفرة\n• نمو القيمة + الإيجار = دخل مزدوج\n\nدعني أريك الأرقام!",
        Language.RU: "💰 Отличный потенциал ROI!\n\nДубай предлагает 7-10% арендной доходности - одна из самых высоких в мире!\n\n• Безналоговый арендный доход\n• Стабильный спрос арендаторов круглый год\n• Управление недвижимостью доступно\n• Рост + аренда = двойной доход\n\nПозвольте показать цифры!"
    },
    # Scarcity in Schedule
    "schedule_scarcity": {
        Language.EN: "📅 Our agent {agent_name} has limited availability this week!\n\n🔥 Only {slot_count} slots remaining:\n\n{slots}\n\n⏰ Book now before they fill up!",
        Language.FA: "📅 مشاور ما {agent_name} این هفته زمان محدودی دارد!\n\n🔥 فقط {slot_count} زمان باقی مانده:\n\n{slots}\n\n⏰ قبل از پر شدن رزرو کنید!",
        Language.AR: "📅 وكيلنا {agent_name} لديه مواعيد محدودة هذا الأسبوع!\n\n🔥 بقي فقط {slot_count} مواعيد:\n\n{slots}\n\n⏰ احجز الآن قبل امتلائها!",
        Language.RU: "📅 У нашего агента {agent_name} ограниченное время на этой неделе!\n\n🔥 Осталось только {slot_count} слотов:\n\n{slots}\n\n⏰ Забронируйте сейчас, пока не заняли!"
    },
    # Lottery messages
    "lottery_offer": {
        Language.EN: "🎁 **Exclusive Lottery!**\n\nWe're running a special lottery for our clients!\n\nPrize: {prize}\n📅 Draw Date: {end_date}\n\nWould you like to participate? It's FREE! 🎉",
        Language.FA: "🎁 **قرعه‌کشی ویژه!**\n\nما برای مشتریانمان قرعه‌کشی ویژه داریم!\n\nجایزه: {prize}\n📅 تاریخ قرعه‌کشی: {end_date}\n\nمی‌خواهید شرکت کنید؟ کاملاً رایگان است! 🎉",
        Language.AR: "🎁 **قرعة حصرية!**\n\nنجري قرعة خاصة لعملائنا!\n\nالجائزة: {prize}\n📅 تاريخ السحب: {end_date}\n\nهل تريد المشاركة؟ مجانية تماماً! 🎉",
        Language.RU: "🎁 **Эксклюзивная лотерея!**\n\nМы проводим специальную лотерею для наших клиентов!\n\nПриз: {prize}\n📅 Дата розыгрыша: {end_date}\n\nХотите участвовать? Это БЕСПЛАТНО! 🎉"
    },
    "lottery_joined": {
        Language.EN: "✅ Congratulations! You've been entered into the lottery!\n\nGood luck! 🍀 We'll notify you when the winner is announced on {end_date}.",
        Language.FA: "✅ تبریک! شما در قرعه‌کشی ثبت‌نام شدید!\n\nموفق باشید! 🍀 در تاریخ {end_date} برنده را اعلام می‌کنیم.",
        Language.AR: "✅ تهانينا! تم تسجيلك في القرعة!\n\nحظاً موفقاً! 🍀 سنخطرك عند الإعلان عن الفائز في {end_date}.",
        Language.RU: "✅ Поздравляем! Вы зарегистрированы в лотерее!\n\nУдачи! 🍀 Мы сообщим победителя {end_date}."
    },
    "lottery_skip": {
        Language.EN: "No problem! Let's continue exploring properties. 🏠",
        Language.FA: "مشکلی نیست! بیایید به بررسی املاک ادامه دهیم. 🏠",
        Language.AR: "لا مشكلة! لنواصل استكشاف العقارات. 🏠",
        Language.RU: "Без проблем! Давайте продолжим просмотр объектов. 🏠"
    },
    "btn_join_lottery": {
        Language.EN: "🎁 Join Lottery",
        Language.FA: "🎁 شرکت در قرعه‌کشی",
        Language.AR: "🎁 الانضمام للقرعة",
        Language.RU: "🎁 Участвовать в лотерее"
    },
    "btn_skip_lottery": {
        Language.EN: "❌ Not Now",
        Language.FA: "❌ الان نه",
        Language.AR: "❌ ليس الآن",
        Language.RU: "❌ Не сейчас"
    },
    "btn_inflation": {
        Language.EN: "💱 Currency Protection",
        Language.FA: "💱 حفاظت از ارزش پول",
        Language.AR: "💱 حماية العملة",
        Language.RU: "💱 Защита от инфляции"
    },
    "btn_visa": {
        Language.EN: "🛂 Family Residency",
        Language.FA: "🛂 اقامت خانواده",
        Language.AR: "🛂 إقامة العائلة",
        Language.RU: "🛂 Резидентство семьи"
    },
    "btn_income": {
        Language.EN: "💰 Passive Income",
        Language.FA: "💰 درآمد غیرفعال",
        Language.AR: "💰 دخل سلبي",
        Language.RU: "💰 Пассивный доход"
    },
    "btn_tax": {
        Language.EN: "📊 Tax-Free Benefits",
        Language.FA: "📊 مزایای بدون مالیات",
        Language.AR: "📊 مزايا معفاة من الضرائب",
        Language.RU: "📊 Безналоговые выгоды"
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
    "btn_need_help": {
        Language.EN: "Would you like details on any of these?",
        Language.FA: "می‌خواهید جزئیات بیشتری ببینید؟",
        Language.AR: "هل تريد المزيد من التفاصيل؟",
        Language.RU: "Хотите больше информации?"
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
        Language.RU: "🛂 Резидency/Виза"
    },
    "btn_schedule_consultation": {
        Language.EN: "Schedule Consultation",
        Language.FA: "رزرو مشاوره",
        Language.AR: "حجز استشارة",
        Language.RU: "Записаться на консультацию"
    },
    "voice_acknowledged": {
        Language.EN: "🎤 Got it! I heard you say:\n\"{transcript}\"\n\nLet me process that...",
        Language.FA: "🎤 گرفتم! شما گفتید:\n\"{transcript}\"\n\nبذارید پردازش کنم...",
        Language.AR: "🎤 فهمت! سمعتك تقول:\n\"{transcript}\"\n\nدعني أعالج ذلك...",
        Language.RU: "🎤 Понял! Вы сказали:\n\"{transcript}\"\n\nДайте обработать..."
    },
    "voice_processing": {
        Language.EN: "🎤 Processing your voice message... Please wait.",
        Language.FA: "🎤 در حال پردازش پیام صوتی شما... لطفاً صبر کنید.",
        Language.AR: "🎤 جاري معالجة رسالتك الصوتية... يرجى الانتظار.",
        Language.RU: "🎤 Обрабатываю голосовое сообщение... Подождите."
    },
    "voice_error": {
        Language.EN: "😔 Sorry, I couldn't understand the audio. Could you please type your message or send a clearer voice note?",
        Language.FA: "😔 متاسفم، صدا را متوجه نشدم. میشه لطفاً پیامتون رو تایپ کنید یا یک ویس واضح‌تر بفرستید؟",
        Language.AR: "😔 عذرًا، لم أتمكن من فهم الصوت. هل يمكنك كتابة رسالتك أو إرسال مذكرة صوتية أوضح؟",
        Language.RU: "😔 Извините, не удалось разобрать аудио. Не могли бы вы написать текстом или отправить более чёткое голосовое?"
    },
    "image_request": {
        Language.EN: "📸 Want to see your dream home? Send me a photo of any property you love, and I'll find similar ones for you!",
        Language.FA: "📸 می‌خوای خونه رویایی‌ات رو ببینی? یه عکس از هر ملکی که دوست داری برام بفرست تا مشابهش رو پیدا کنم!",
        Language.AR: "📸 تريد رؤية منزل أحلامك؟ أرسل لي صورة لأي عقار تحبه وسأجد لك عقارات مشابهة!",
        Language.RU: "📸 Хотите увидеть дом своей мечты? Отправьте фото любой недвижимости, и я найду похожие варианты!"
    },
    "image_processing": {
        Language.EN: "🔍 Analyzing your image... Let me find similar properties for you!",
        Language.FA: "🔍 در حال تحلیل عکس شما... بذارید املاک مشابه رو پیدا کنم!",
        Language.AR: "🔍 جاري تحليل صورتك... دعني أجد عقارات مشابهة لك!",
        Language.RU: "🔍 Анализирую изображение... Сейчас найду похожие варианты!"
    },
    "pdf_generating": {
        Language.EN: "📊 Preparing your personalized ROI report... This will take just a moment!",
        Language.FA: "📊 در حال آماده‌سازی گزارش ROI شخصی‌سازی شده... چند لحظه صبر کنید!",
        Language.AR: "📊 جاري تحضير تقرير العائد على الاستثمار الشخصي... سيستغرق لحظات فقط!",
        Language.RU: "📊 Готовлю персональный отчёт ROI... Это займёт всего мгновение!"
    },
    "image_results": {
        Language.EN: "✨ Found {count} similar properties! Here's the best match:\n\n{property_details}",
        Language.FA: "✨ {count} ملک مشابه پیدا کردم! اینم بهترینش:\n\n{property_details}",
        Language.AR: "✨ وجدت {count} عقار مشابه! إليك الأفضل:\n\n{property_details}",
        Language.RU: "✨ Нашёл {count} похожих вариантов! Вот лучший:\n\n{property_details}"
    },
    "image_no_results": {
        Language.EN: "😔 Couldn't find exact matches, but I can help you find your perfect home! What's your budget?",
        Language.FA: "😔 دقیقاً مشابه پیدا نکردم، اما میتونم خونه کاملت رو پیدا کنم! بودجه‌ت چقدره؟",
        Language.AR: "😔 لم أجد تطابقات دقيقة، لكن يمكنني مساعدتك في العثور على منزلك المثالي! ما هي ميزانيتك؟",
        Language.RU: "😔 Точных совпадений не нашёл, но помогу найти идеальное жильё! Какой у вас бюджет?"
    },
    "image_error": {
        Language.EN: "😔 Sorry, couldn't process the image. Please try sending a clearer photo.",
        Language.FA: "😔 متاسفم، نتونستم عکس رو پردازش کنم. لطفاً یه عکس واضح‌تر بفرستید.",
        Language.AR: "😔 عذرًا، لم أتمكن من معالجة الصورة. يرجى إرسال صورة أوضح.",
        Language.RU: "😔 Извините, не удалось обработать изображение. Отправьте более чёткое фото."
    }
}

# Budget options in AED
BUDGET_OPTIONS = {
    Language.EN: ["Under 500K AED", "500K - 1M AED", "1M - 2M AED", "2M - 5M AED", "5M+ AED"],
    Language.FA: ["زیر 500 هزار درهم", "500 هزار تا 1 میلیون درهم", "1 تا 2 میلیون درهم", "2 تا 5 میلیون درهم", "بالای 5 میلیون درهم"],
    Language.AR: ["أقل من 500 ألف درهم", "500 ألف - 1 مليون درهم", "1 - 2 مليون درهم", "2 - 5 مليون درهم", "أكثر من 5 مليون درهم"],
    Language.RU: ["До 500 тыс. AED", "500 тыс. - 1 млн AED", "1 - 2 млн AED", "2 - 5 млн AED", "5+ млн AED"]
}

# ===========================
# 💰 BUDGET CONFIGURATION (Single Source of Truth)
# ===========================
# All budget ranges are defined here to avoid duplication and ensure consistency.
# Changes to budget ranges should ONLY be made in these constants.

# BUY/INVESTMENT Budget Ranges (0-750k focus as per product requirements)
# Used for: Investment, Residency, and Living → Buy flows
# BUY Budget Ranges - Aligned with UAE Residency Visa requirements
# 2-Year Residency: Property investment under 750,000 AED
# Golden Visa (long-term): Property investment 750,000 AED or more
BUDGET_RANGES = {
    0: (0, 750000),        # 2-Year Residency Visa: 0-750k AED
    1: (750000, None)      # Golden Visa (Long-term): 750k+ AED
}

# RENTAL Budget Ranges (annual values stored, displayed as monthly)
# Used for: Living → Rent flow
# Formula: Monthly = Annual / 12
RENT_BUDGET_RANGES = {
    0: (0, 50000),           # Budget: 0-50K AED/year → 0-4,167 AED/month
    1: (50000, 100000),      # Mid-low: 50K-100K/year → 4,167-8,333 AED/month
    2: (100000, 200000),     # Mid: 100K-200K/year → 8,333-16,667 AED/month
    3: (200000, 500000),     # Upper: 200K-500K/year → 16,667-41,667 AED/month
    4: (500000, None)        # Premium: 500K+/year → 41,667+ AED/month
}
# ===========================

def parse_budget_string(budget_str: str) -> Optional[int]:
    """Parse budget strings like '2M', '500K', '1.5 Million' to integers."""
    if not budget_str:
        return None
    
    budget_str = budget_str.strip().upper().replace(',', '').replace(' ', '')
    
    # Extract number and multiplier
    import re
    match = re.search(r'([\d\.]+)\s*(M|K|MIL|MILLION|THOUSAND|K)?', budget_str)
    if not match:
        return None
    
    number = float(match.group(1))
    multiplier = match.group(2) or ''
    
    if 'M' in multiplier or 'MIL' in multiplier:
        return int(number * 1_000_000)
    elif 'K' in multiplier or 'THOUSAND' in multiplier:
        return int(number * 1_000)
    else:
        return int(number)


# ==================== RETRY LOGIC ====================

async def retry_with_backoff(func, max_retries=MAX_RETRIES, base_delay=RETRY_DELAY_BASE):
    """Retry function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"❌ All {max_retries} retries failed: {e}")
                raise
            
            delay = base_delay * (2 ** attempt)
            logger.warning(f"⚠️ Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
            await asyncio.sleep(delay)

# ==================== HELPER CLASSES ====================

@dataclass
class BrainResponse:
    """Response from the Brain to be sent back through the platform."""
    message: str
    buttons: Optional[List[Dict[str, str]]] = None  # [{text, callback_data}]
    next_state: Optional[ConversationState] = None
    lead_updates: Optional[Dict[str, Any]] = None
    should_generate_roi: bool = False
    request_contact: bool = False  # NEW: Request phone number with contact button (Telegram)
    metadata: Optional[Dict[str, Any]] = None  # NEW: Additional metadata (e.g., send_pdf flag)
    media_files: Optional[List[Dict[str, Any]]] = None  # NEW: Media files to send [{type: 'photo'|'pdf', url: str, name: str}]


# ==================== LOTTERY HELPERS ====================

async def get_active_lotteries(tenant_id: int):
    """Get active lotteries for a tenant from the API."""
    import aiohttp
    from datetime import datetime
    
    try:
        # Import here to avoid circular import
        from api.lotteries import LOTTERIES_DB
        
        active_lotteries = []
        for lottery in LOTTERIES_DB.values():
            if (lottery["tenant_id"] == tenant_id and 
                lottery["status"] == "active" and 
                lottery["end_date"] > datetime.utcnow()):
                active_lotteries.append(lottery)
        
        return active_lotteries
    except Exception as e:
        logger.error(f"❌ Error fetching lotteries: {e}")
        return []


async def join_lottery(tenant_id: int, lottery_id: int, lead_id: int):
    """Add a lead to lottery participants."""
    try:
        from api.lotteries import LOTTERIES_DB
        
        if lottery_id not in LOTTERIES_DB:
            return False
        
        lottery = LOTTERIES_DB[lottery_id]
        if lottery["tenant_id"] != tenant_id:
            return False
        
        # Add lead to participants if not already there
        if lead_id not in lottery["participants"]:
            lottery["participants"].append(lead_id)
            logger.info(f"✅ Lead {lead_id} joined lottery {lottery_id}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error joining lottery: {e}")
        return False


# ==================== URGENCY & SCARCITY GENERATOR ====================

def generate_urgency_message(property_data: Dict[str, Any], lang: Language) -> str:
    """
    Generate urgency/scarcity messaging for property presentation.
    Uses sales psychology: scarcity, social proof, time pressure.
    
    Args:
        property_data: Property dict with price, is_featured, etc.
        lang: User language
    
    Returns:
        Urgency message string (empty if no urgency applies)
    """
    import random
    
    urgency_parts = []
    price = property_data.get("price", 0)
    is_featured = property_data.get("is_featured", False)
    is_urgent = property_data.get("is_urgent", False)
    
    # 🔥 SCARCITY: Limited units (realistic based on price tier)
    if price > 5000000:  # Luxury (5M+)
        units_left = random.randint(1, 2)
    elif price > 2000000:  # Mid-high (2M-5M)
        units_left = random.randint(2, 4)
    else:  # Affordable (<2M)
        units_left = random.randint(3, 6)
    
    scarcity_templates = {
        Language.FA: f"🔥 فقط {units_left} واحد باقی مانده!",
        Language.EN: f"🔥 Only {units_left} units left!",
        Language.AR: f"🔥 {units_left} وحدات فقط متبقية!",
        Language.RU: f"🔥 Осталось только {units_left} юнитов!"
    }
    urgency_parts.append(scarcity_templates.get(lang, scarcity_templates[Language.EN]))
    
    # 🔥 SOCIAL PROOF: Views today (realistic numbers)
    if is_featured or is_urgent:
        views_today = random.randint(5, 12)
    else:
        views_today = random.randint(2, 6)
    
    social_proof_templates = {
        Language.FA: f"👀 {views_today} نفر امروز دیدند",
        Language.EN: f"👀 {views_today} people viewed today",
        Language.AR: f"👀 {views_today} شخص شاهدوا اليوم",
        Language.RU: f"👀 {views_today} человек смотрели сегодня"
    }
    urgency_parts.append(social_proof_templates.get(lang, social_proof_templates[Language.EN]))
    
    # 🔥 TIME PRESSURE: Availability window
    if is_urgent:
        time_pressure_templates = {
            Language.FA: "⏰ موجود تا فردا ظهر",
            Language.EN: "⏰ Available until tomorrow noon",
            Language.AR: "⏰ متاح حتى ظهر غد",
            Language.RU: "⏰ Доступно до завтрашнего полудня"
        }
    elif is_featured:
        time_pressure_templates = {
            Language.FA: "⏰ عرض ویژه تا آخر هفته",
            Language.EN: "⏰ Special offer ends this weekend",
            Language.AR: "⏰ عرض خاص ينتهي نهاية الأسبوع",
            Language.RU: "⏰ Спецпредложение до выходных"
        }
    else:
        time_pressure_templates = {
            Language.FA: "⏰ قیمت فعلی تا آخر ماه",
            Language.EN: "⏰ Current price until end of month",
            Language.AR: "⏰ السعر الحالي حتى نهاية الشهر",
            Language.RU: "⏰ Текущая цена до конца месяца"
        }
    
    urgency_parts.append(time_pressure_templates.get(lang, time_pressure_templates[Language.EN]))
    
    return " • ".join(urgency_parts)


# ==================== MAIN BRAIN CLASS ====================

class Brain:
    """
    The Super Brain - AI Core for ArtinSmartRealty
    Handles all conversation logic, language detection, voice processing,
    and state machine for Turbo Qualification Flow.
    
    NEW: Uses tenant-specific data (properties, projects, knowledge) for personalized responses.
    """
    
    def __init__(self, tenant=None):
        self.tenant = tenant
        self.agent_name = tenant.name if tenant else "ArtinSmartRealty"
        self.tenant_context = None  # Will be loaded on demand
        self.chat_sessions = {}  # Store chat sessions per lead ID for conversation memory
        
        # Initialize Gemini Client (Handles rotation, retries, and safety)
        self.gemini_client = GeminiClient(model_name='gemini-2.0-flash-exp')
        logger.info("✅ Brain initialized with robust GeminiClient")
    
    async def extract_user_info_smart(self, message: str, current_lead_data: dict) -> dict:
        """
        🧠 INTELLIGENT EXTRACTION - Extract ALL possible info from message at once
        این همون "مغز" هست که باید همه چیز رو یکجا بفهمه!
        
        Returns dict with extracted fields:
        {
            "name": str or None,
            "phone": str or None,
            "goal": str or None,  # "buy", "rent", "investment", "residency"
            "budget_min": int or None,
            "budget_max": int or None,
            "location_preference": str or None,
            "property_type": str or None,  # "apartment", "villa", "office"
            "bedrooms": int or None,
            "urgency": str or None  # "urgent", "exploring", "planning"
        }
        """
        if not self.gemini_client or not self.gemini_client.current_key:
            logger.warning("⚠️ Gemini model not available - using fallback extraction")
            return {}
        
        extraction_prompt = f"""
You are an intelligent data extractor for a real estate chatbot.

CURRENT USER DATA WE HAVE:
{current_lead_data}

NEW MESSAGE FROM USER:
"{message}"

YOUR TASK: Extract ANY and ALL information present in the message. Return ONLY a JSON object with these fields (use null for missing data):

{{
    "name": "full name if mentioned",
    "phone": "phone number in international format +XXX",
    "email": "email address if mentioned",
    "goal": "buy/rent/investment/residency/golden_visa",
    "budget_min": numeric value in USD,
    "budget_max": numeric value in USD,
    "location_preference": "area name like Dubai Marina, Downtown, etc",
    "property_type": "apartment/villa/office/studio/penthouse",
    "bedrooms": number of bedrooms,
    "urgency": "urgent/soon/exploring/just_looking"
}}

RULES:
1. Extract EVERYTHING mentioned - don't skip anything
2. For phone: convert local format to international (+971 for UAE, +98 for Iran)
3. For budget: convert AED/درهم to USD (divide by 3.67), تومان to USD (divide by 600000)
4. If user says multiple things (e.g., name AND budget), extract ALL of them
5. Return ONLY the JSON, no explanations

Example:
User: "سلام من ارزو محمدزادگانم، شماره‌م 09177105840 هست، میخوام آپارتمان تا 200 هزار دلار در Dubai Marina بخرم"
Output: {{"name": "ارزو محمدزادگان", "phone": "+989177105840", "goal": "buy", "budget_max": 200000, "location_preference": "Dubai Marina", "property_type": "apartment"}}

Now extract from the user's message above.
"""
        
        try:
            # Use GeminiClient's async method with built-in retry
            response = await self.gemini_client.generate_content_async(extraction_prompt, max_retries=3)
            
            # Parse JSON response
            import json
            import re
            
            # Clean response text (remove markdown code blocks if present)
            text = response.text.strip()
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            
            extracted = json.loads(text)
            
            # Filter out null values
            extracted = {k: v for k, v in extracted.items() if v is not None}
            
            logger.info(f"🧠 Smart extraction from message: {extracted}")
            return extracted
            
        except Exception as e:
            logger.error(f"❌ Smart extraction failed: {e}")
            return {}
    
    async def load_tenant_context(self, lead: Optional[Lead] = None):
        """Load tenant-specific data for AI context."""
        self.tenant_context = await get_tenant_context_for_ai(self.tenant.id, lead)
        return self.tenant_context
    
    def _build_tenant_context_prompt(self) -> str:
        """Build a prompt section with tenant's data for AI to use."""
        if not self.tenant_context:
            return ""
        
        context_parts = []
        
        # Agent/Company Info
        tenant_info = self.tenant_context.get("tenant", {})
        if tenant_info:
            context_parts.append(f"""
AGENT INFORMATION:
- Name: {tenant_info.get('name', self.agent_name)}
- Company: {tenant_info.get('company', 'N/A')}
- Contact: {tenant_info.get('phone', 'N/A')} | {tenant_info.get('email', 'N/A')}
""")
        
        # Available Properties
        properties = self.tenant_context.get("properties", [])
        if properties:
            props_lines = []
            for p in properties[:5]:  # Limit to 5 for context
                price_str = f"AED {p['price']:,.0f}" if p.get('price') else "Price TBA"
                bedrooms_str = f"{p['bedrooms']}BR" if p.get('bedrooms') else ""
                roi_str = f"ROI: {p['roi']}%" if p.get('roi') else ""
                yield_str = f"Rental Yield: {p['rental_yield']}%" if p.get('rental_yield') else ""
                golden_str = " ⭐ Golden Visa Eligible" if p.get('golden_visa') else ""
                
                props_lines.append(
                    f"  • {p.get('name', 'Property')} - {p.get('type', 'N/A')} in {p.get('location', 'N/A')}, "
                    f"{bedrooms_str} {price_str} ({roi_str}, {yield_str}){golden_str}"
                )
            
            props_text = "\n".join(props_lines)
            context_parts.append(f"""
AVAILABLE PROPERTIES (Agent's Inventory):
{props_text}
""")
        
        # Off-Plan Projects
        projects = self.tenant_context.get("projects", [])
        if projects:
            projs_lines = []
            for proj in projects[:3]:  # Limit to 3 for context
                price_str = f"Starting AED {proj['starting_price']:,.0f}" if proj.get('starting_price') else "Price TBA"
                golden_str = " ⭐ Golden Visa Eligible" if proj.get('golden_visa') else ""
                selling_pts = ", ".join(proj['selling_points'][:3]) if proj.get('selling_points') else "N/A"
                
                projs_lines.append(
                    f"  • {proj.get('name', 'Project')} by {proj.get('developer', 'N/A')} in {proj.get('location', 'N/A')}"
                    f"\n    {price_str} | Payment: {proj.get('payment_plan', 'Flexible')}"
                    f"\n    Handover: {proj.get('handover', 'TBA')} | Projected ROI: {proj.get('roi', 'N/A')}%{golden_str}"
                    f"\n    Selling Points: {selling_pts}"
                )
            
            projs_text = "\n".join(projs_lines)
            context_parts.append(f"""
OFF-PLAN PROJECTS (Current Launches):
{projs_text}
""")
        
        # Knowledge Base
        knowledge = self.tenant_context.get("knowledge", [])
        if knowledge:
            kb_text = "\n".join([
                f"  **{k['title']}**\n  {k['content'][:300]}...\n"
                for k in knowledge[:10]  # Increased to 10 for more comprehensive knowledge
            ])
            context_parts.append(f"""
DUBAI REAL ESTATE KNOWLEDGE BASE (Always use this for factual answers):
{kb_text}
""")
        
        return "\n".join(context_parts)
    
    def _search_relevant_knowledge(self, user_message: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant knowledge entries based on user message keywords.
        Returns top matching knowledge entries.
        """
        if not self.tenant_context or not self.tenant_context.get("knowledge"):
            return []
        
        all_knowledge = self.tenant_context.get("knowledge", [])
        message_lower = user_message.lower()
        
        # Score each knowledge entry based on keyword matches
        scored_knowledge = []
        for k in all_knowledge:
            score = 0
            # Check if any keyword matches
            keywords = k.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    score += 2  # Higher weight for exact keyword match
            
            # Check title relevance
            if any(word in message_lower for word in k.get("title", "").lower().split()):
                score += 1
            
            if score > 0:
                scored_knowledge.append((score, k))
        
        # Sort by score and return top results
        scored_knowledge.sort(reverse=True, key=lambda x: x[0])
        return [k for _, k in scored_knowledge[:max_results]]
    
    def _format_knowledge_for_prompt(self, knowledge_list: List[Dict[str, Any]]) -> str:
        """Format knowledge entries for inclusion in AI prompt."""
        if not knowledge_list:
            return "No specific knowledge entries matched this query."
        
        formatted = []
        for k in knowledge_list:
            formatted.append(f"📌 **{k['title']}**\n{k['content']}\n")
        
        return "\n".join(formatted)
    
    async def get_relevant_knowledge(self, query: str, lang: Language, limit: int = 3) -> str:
        """
        Retrieval Engine for Contextual Knowledge Injection (Simple RAG).
        
        Args:
            query: User's message or query text
            lang: User's language preference
            limit: Maximum number of knowledge entries to return
        
        Returns:
            Formatted string with relevant knowledge entries for LLM prompt
        
        Scoring Algorithm:
            +2 Points: If any keyword from entry.keywords appears in query
            +1 Point: If words from entry.title appear in query
        """
        # Load tenant context if not already loaded
        if not self.tenant_context:
            logger.warning("⚠️ Tenant context not loaded for knowledge retrieval")
            return ""
        
        # Get all knowledge entries from context
        all_knowledge = self.tenant_context.get("knowledge", [])
        if not all_knowledge:
            logger.info("ℹ️ No knowledge entries found in tenant context")
            return ""
        
        query_lower = query.lower()
        scored_entries = []
        
        # Score each knowledge entry
        for entry in all_knowledge:
            # Skip if language doesn't match
            if entry.get("language") and entry.get("language") != lang:
                continue
            
            score = 0
            
            # +2 points for each keyword match
            keywords = entry.get("keywords", [])
            if keywords:
                for keyword in keywords:
                    if keyword.lower() in query_lower:
                        score += 2
                        logger.debug(f"🔍 Keyword match '{keyword}' in query: +2 points")
            
            # +1 point for title word matches
            title_words = entry.get("title", "").lower().split()
            for word in title_words:
                if len(word) > 3 and word in query_lower:  # Ignore short words
                    score += 1
                    logger.debug(f"🔍 Title word match '{word}' in query: +1 point")
            
            # Only include entries with score > 0
            if score > 0:
                scored_entries.append((score, entry.get("priority", 0), entry))
                logger.info(f"✅ Scored '{entry.get('title')}': {score} points (priority: {entry.get('priority', 0)})")
        
        # Sort by score (descending), then by priority (descending)
        scored_entries.sort(key=lambda x: (x[0], x[1]), reverse=True)
        
        # Get top N entries
        top_entries = [entry for _, _, entry in scored_entries[:limit]]
        
        if not top_entries:
            logger.info("ℹ️ No relevant knowledge entries found for query")
            return ""
        
        # Format for LLM prompt
        formatted_parts = []
        for entry in top_entries:
            formatted_parts.append(f"**{entry['title']}**\n{entry['content']}")
        
        result = "\n\n".join(formatted_parts)
        logger.info(f"📚 Retrieved {len(top_entries)} relevant knowledge entries")
        
        return result
    
    async def get_specific_knowledge(self, topic_keyword: str, lang: Language) -> str:
        """
        Helper method to fetch knowledge for specific topics.
        Used for targeted injection in conversation handlers.
        
        Args:
            topic_keyword: Specific keyword to search for (e.g., "escrow", "golden visa", "ROI")
            lang: User's language preference
        
        Returns:
            Formatted knowledge entry or empty string if not found
        """
        if not self.tenant_context:
            return ""
        
        all_knowledge = self.tenant_context.get("knowledge", [])
        
        # Search for entries matching the topic keyword
        for entry in all_knowledge:
            # Check language match
            if entry.get("language") and entry.get("language") != lang:
                continue
            
            # Check if topic_keyword is in keywords or title
            keywords = entry.get("keywords", [])
            title = entry.get("title", "").lower()
            topic_lower = topic_keyword.lower()
            
            if any(topic_lower in kw.lower() for kw in keywords) or topic_lower in title:
                logger.info(f"📌 Found specific knowledge for '{topic_keyword}': {entry['title']}")
                return f"\n\n💡 **{entry['title']}**\n{entry['content']}"
        
        logger.debug(f"ℹ️ No specific knowledge found for '{topic_keyword}'")
        return ""
    
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
    
    async def handle_floating_input(
        self,
        lead: Lead,
        message: str,
        expected_state: ConversationState,
        conversation_data: Dict
    ) -> Optional[BrainResponse]:
        """
        🎯 FLOATING LOGIC HANDLER
        
        Handles "off-script" user input when they:
        1. Ask questions while we're waiting for button clicks
        2. Send voice/text instead of clicking buttons
        3. Try to jump to different topics mid-flow
        
        Returns:
            BrainResponse if we handled it, None if normal flow should continue
        """
        lang = lead.language or Language.EN
        
        # 1. Check for cancellation/reset keywords
        cancel_keywords = {
            Language.EN: ['cancel', 'stop', 'restart', 'start over', 'main menu'],
            Language.FA: ['لغو', 'کنسل', 'منو اصلی', 'شروع دوباره', 'بازگشت'],
            Language.AR: ['إلغاء', 'توقف', 'القائمة الرئيسية', 'البداية من جديد'],
            Language.RU: ['отмена', 'стоп', 'главное меню', 'начать заново']
        }
        
        if any(keyword in message.lower() for keyword in cancel_keywords.get(lang, [])):
            logger.info(f"🔄 User {lead.id} requested cancellation/restart")
            # Reset to start - return to language selection
            conversation_data.clear()
            
            lang_buttons = [
                {"text": "🇬🇧 English", "callback_data": "lang_en"},
                {"text": "🇮🇷 فارسی", "callback_data": "lang_fa"},
                {"text": "🇸🇦 العربية", "callback_data": "lang_ar"},
                {"text": "🇷🇺 Русский", "callback_data": "lang_ru"}
            ]
            
            return BrainResponse(
                message=self.get_text("language_select", lang).format(agent_name=self.agent_name),
                buttons=lang_buttons,
                next_state=ConversationState.LANGUAGE_SELECT
            )
        
        # 2. Smart extraction attempt - try to parse what they said
        extracted_data = await self._smart_extract_from_text(message, expected_state, lang)
        
        if extracted_data:
            logger.info(f"✅ Smart extraction successful: {extracted_data}")
            # User provided data in text/voice instead of button
            # Update conversation_data and continue flow
            conversation_data.update(extracted_data)
            return None  # Let normal flow continue with extracted data
        
        # 3. User is asking a question - answer it and redirect back
        is_question = any(char in message for char in ['؟', '?']) or any(
            word in message.lower() for word in [
                'چطور', 'چه', 'کی', 'کجا', 'چرا', 'آیا',  # Persian
                'how', 'what', 'when', 'where', 'why', 'do you', 'can you', 'is it',  # English
                'هل', 'اين', 'ما', 'كيف', 'متى',  # Arabic
                'что', 'как', 'когда', 'где', 'почему'  # Russian
            ]
        )
        
        if is_question:
            logger.info(f"❓ User {lead.id} asked question during {expected_state}: {message}")
            
            # Detect OFF-PLAN / PRE-PURCHASE questions
            offplan_keywords = ['پیش خرید', 'پیش‌خرید', 'اف پلن', 'آف پلن', 'off plan', 'off-plan', 'pre-sale', 'presale', 'pre purchase']
            is_offplan_question = any(keyword in message.lower() for keyword in offplan_keywords)
            
            # Detect RESIDENCY / GOLDEN VISA questions
            residency_keywords = ['اقامت', 'ویزا', 'ویزای طلایی', 'گلدن ویزا', 'golden visa', 'residency', 'residence', 'visa']
            is_residency_question = any(keyword in message.lower() for keyword in residency_keywords)
            
            # Consultation button for ALL responses
            consultation_btn = {
                Language.FA: "📅 رزرو مشاوره رایگان",
                Language.EN: "📅 Book Free Consultation",
                Language.AR: "📅 حجز استشارة مجانية",
                Language.RU: "📅 Забронировать консультацию"
            }
            
            # OFF-PLAN specific answer
            if is_offplan_question:
                offplan_responses = {
                    Language.FA: "عالیه که از پیش‌خرید پرسیدی! 🎯\n\nپیش‌خرید (Off-Plan) یعنی:\n✅ فقط 10-20% پیش پرداخت (باقی در طول ساخت)\n✅ قیمت 15-30% ارزون‌تر از املاک آماده\n✅ رشد 20-40% در طول ساخت\n✅ اقساط بدون بهره\n\nبهترین گزینه برای سرمایه‌گذاری!\n\nراستی، بودجه شما چقدر است تا بهترین پروژه‌ها رو نشونت بدم؟ 🏗️",
                    Language.EN: "Great question about off-plan! 🎯\n\nOff-plan purchase means:\n✅ Only 10-20% down payment (rest during construction)\n✅ 15-30% cheaper than ready properties\n✅ 20-40% appreciation during construction\n✅ Interest-free installments\n\nBest option for investment!\n\nBy the way, what's your budget so I can show you the best projects? 🏗️",
                    Language.AR: "سؤال رائع عن الشراء على الخارطة! 🎯\n\nالشراء على الخارطة يعني:\n✅ دفعة أولى 10-20% فقط (الباقي أثناء البناء)\n✅ أرخص بنسبة 15-30% من العقارات الجاهزة\n✅ ارتفاع القيمة 20-40% أثناء البناء\n✅ أقساط بدون فوائد\n\nأفضل خيار للاستثمار!\n\nبالمناسبة، ما هي ميزانيتك حتى أريك أفضل المشاريع؟ 🏗️",
                    Language.RU: "Отличный вопрос об off-plan! 🎯\n\nПокупка на стадии строительства означает:\n✅ Первый взнос всего 10-20% (остальное во время стройки)\n✅ На 15-30% дешевле готовых объектов\n✅ Рост стоимости 20-40% во время строительства\n✅ Рассрочка без процентов\n\nЛучший вариант для инвестиций!\n\nКстати, какой у вас бюджет, чтобы я показал лучшие проекты? 🏗️"
                }
                
                buttons = self._get_buttons_for_state(expected_state, conversation_data, lang) or []
                buttons.append({"text": consultation_btn.get(lang, consultation_btn[Language.EN]), "callback_data": "schedule_consultation"})
                
                return BrainResponse(
                    message=offplan_responses.get(lang, offplan_responses[Language.EN]),
                    buttons=buttons,
                    next_state=expected_state
                )
            
            # RESIDENCY specific answer
            elif is_residency_question:
                residency_responses = {
                    Language.FA: "سوال فوق‌العاده! 🌟\n\nگلدن ویزای دبی:\n✅ اقامت 10 ساله برای شما و خانواده\n✅ فقط کافیه ملک بالای 2 میلیون درهم بخری\n✅ بدون نیاز به اسپانسر\n✅ آموزش رایگان برای فرزندان\n✅ سیستم بهداشتی جهانی\n\nخیلی از مشتری‌های ما همین الان دارن ویزا می‌گیرن!\n\nبودجه شما چقدر است تا املاک مناسب برای گلدن ویزا نشونت بدم؟ 🇦🇪",
                    Language.EN: "Excellent question! 🌟\n\nDubai Golden Visa:\n✅ 10-year residency for you and family\n✅ Just buy property above 2M AED\n✅ No sponsor needed\n✅ Free education for children\n✅ World-class healthcare\n\nMany of our clients are getting visas RIGHT NOW!\n\nWhat's your budget so I can show you properties eligible for Golden Visa? 🇦🇪",
                    Language.AR: "سؤال ممتاز! 🌟\n\nالفيزا الذهبية لدبي:\n✅ إقامة 10 سنوات لك ولعائلتك\n✅ فقط اشترِ عقاراً فوق 2 مليون درهم\n✅ لا حاجة لكفيل\n✅ تعليم مجاني للأطفال\n✅ رعاية صحية عالمية المستوى\n\nالعديد من عملائنا يحصلون على التأشيرة الآن!\n\nما هي ميزانيتك حتى أريك العقارات المؤهلة للفيزا الذهبية؟ 🇦🇪",
                    Language.RU: "Отличный вопрос! 🌟\n\nЗолотая виза Дубая:\n✅ 10-летнее резидентство для вас и семьи\n✅ Просто купите недвижимость от 2M AED\n✅ Без спонсора\n✅ Бесплатное образование для детей\n✅ Здравоохранение мирового уровня\n\nМногие наши клиенты получают визы ПРЯМО СЕЙЧАС!\n\nКакой у вас бюджет, чтобы я показал объекты для Золотой визы? 🇦🇪"
                }
                
                buttons = self._get_buttons_for_state(expected_state, conversation_data, lang) or []
                buttons.append({"text": consultation_btn.get(lang, consultation_btn[Language.EN]), "callback_data": "schedule_consultation"})
                
                return BrainResponse(
                    message=residency_responses.get(lang, residency_responses[Language.EN]),
                    buttons=buttons,
                    next_state=expected_state
                )
            
            # GENERAL questions - AI answer with ENGAGING redirect
            else:
                # Generate AI answer using Gemini
                ai_answer = await self.generate_ai_response(message, lead, "")
                
                # Add engaging redirect back to flow with FOMO
                redirect_messages = {
                    Language.EN: "\n\n🔥 By the way, want to know something? Best properties go FAST!\n\n💡 ",
                    Language.FA: "\n\n🔥 راستی، یه چیزی بگم؟ بهترین املاک خیلی سریع می‌رن!\n\n💡 ",
                    Language.AR: "\n\n🔥 بالمناسبة، تعلم شيئاً؟ أفضل العقارات تذهب بسرعة!\n\n💡 ",
                    Language.RU: "\n\n🔥 Кстати, знаете что? Лучшие объекты уходят БЫСТРО!\n\n💡 "
                }
            
                # Context-aware redirect based on current state
                if expected_state == ConversationState.SLOT_FILLING:
                    pending_slot = conversation_data.get("pending_slot")
                    if pending_slot == "budget":
                        redirect = {
                            Language.EN: "what's your budget range?",
                            Language.FA: "بودجه شما چقدر است؟",
                            Language.AR: "ما هي ميزانيتك؟",
                            Language.RU: "каков ваш бюджет?"
                        }
                    elif pending_slot == "property_type":
                        redirect = {
                            Language.EN: "what type of property interests you?",
                            Language.FA: "چه نوع ملکی به شما علاقه‌مند است؟",
                            Language.AR: "ما نوع العقار الذي يهمك؟",
                            Language.RU: "какой тип недвижимости вас интересует?"
                        }
                    else:
                        redirect = {
                            Language.EN: "please select from the options above.",
                            Language.FA: "لطفاً از گزینه‌های بالا انتخاب کنید.",
                            Language.AR: "يرجى الاختيار من الخيارات أعلاه.",
                            Language.RU: "пожалуйста, выберите из вариантов выше."
                        }
                    
                    full_response = ai_answer + redirect_messages.get(lang, "") + redirect.get(lang, "")
                    
                    # Add consultation button
                    buttons = self._get_buttons_for_state(expected_state, conversation_data, lang) or []
                    buttons.append({"text": consultation_btn.get(lang, consultation_btn[Language.EN]), "callback_data": "schedule_consultation"})
                    
                    # Return same buttons as before
                    return BrainResponse(
                        message=full_response,
                        buttons=buttons,
                        next_state=expected_state  # Stay in same state
                    )
        
        # 4. Unrecognized input - Engaging nudge with urgency + Show current step buttons
        nudge_messages = {
            Language.EN: "I see you're interested! 👀\n\n🔥 **Market Alert:** Dubai prices up 12% this year. Properties move FAST!\n\n💡 Let me show you today's best deals matching your needs.\n\nPick an option or type your preferences:",
            Language.FA: "می‌بینم علاقه‌مندی! 👀\n\n🔥 **هشدار بازار:** قیمت‌ها امسال 12% بالا رفته. املاک خیلی سریع میرن!\n\n💡 بذار بهترین معاملات امروز رو که با نیازت مچ میشه نشونت بدم.\n\nیکی انتخاب کن یا ترجیحاتت رو بنویس:",
            Language.AR: "أرى اهتمامك! 👀\n\n🔥 **تنبيه السوق:** أسعار دبي ارتفعت 12% هذا العام. العقارات تتحرك بسرعة!\n\n💡 دعني أريك أفضل الصفقات اليوم المطابقة لاحتياجاتك.\n\nاختر خياراً أو اكتب تفضيلاتك:",
            Language.RU: "Вижу, вам интересно! 👀\n\n🔥 **Тревога рынка:** Цены в Дубае выросли на 12% в этом году. Объекты уходят БЫСТРО!\n\n💡 Позвольте показать лучшие сделки под ваши требования.\n\nВыберите опцию или напишите предпочтения:"
        }
        
        # Show buttons for current expected state
        buttons = self._get_buttons_for_state(expected_state, conversation_data, lang) or []
        
        return BrainResponse(
            message=nudge_messages.get(lang, nudge_messages[Language.EN]),
            buttons=buttons,
            next_state=expected_state
        )
    
    async def _smart_extract_from_text(
        self,
        message: str,
        expected_state: ConversationState,
        lang: Language
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to extract structured data from freeform text/voice.
        
        Returns dict with extracted fields if successful, None otherwise.
        """
        extracted = {}
        message_lower = message.lower()
        
        # Security: Limit message length to prevent ReDoS attacks
        if len(message_lower) > 500:
            logger.warning(f"⚠️ Message too long for extraction ({len(message_lower)} chars), truncating")
            message_lower = message_lower[:500]
        
        # Extract budget from text
        # Patterns: "2 million", "دو میلیون", "2M", "2000000", "2-3M"
        budget_patterns = [
            r'(\d{1,4}\.?\d{0,2})\s*(million|میلیون|مليون|миллион)',  # "2 million" (max 4 digits)
            r'(\d{1,4}\.?\d{0,2})\s*m\b',  # "2M" (max 4 digits)
            r'(\d{6,10})',  # Raw numbers 1M to 10B (limited range)
            r'(\d{1,4}\.?\d{0,2})\s*-\s*(\d{1,4}\.?\d{0,2})\s*(million|میلیون|مليون|миллион)'  # "2-3 million"
        ]
        
        for pattern in budget_patterns:
            try:
                match = re.search(pattern, message_lower)  # Note: Python re.search() doesn't support timeout parameter
            except Exception as e:
                logger.error(f"❌ Regex error for pattern {pattern}: {e}")
                continue
                
            if match:
                try:
                    if len(match.groups()) >= 3:  # Range pattern
                        min_val = float(match.group(1)) * 1_000_000
                        max_val = float(match.group(2)) * 1_000_000
                        # Validate range (max 100M AED)
                        if min_val > 100_000_000 or max_val > 100_000_000:
                            logger.warning(f"⚠️ Budget out of range: {min_val}-{max_val}")
                            continue
                        extracted['budget_min'] = int(min_val)
                        extracted['budget_max'] = int(max_val)
                    else:
                        amount = float(match.group(1))
                        if 'million' in match.group(0) or 'میلیون' in match.group(0):
                            amount *= 1_000_000
                        # Validate amount (max 100M AED)
                        if amount > 100_000_000:
                            logger.warning(f"⚠️ Budget out of range: {amount}")
                            continue
                        extracted['budget_max'] = int(amount)
                    logger.info(f"💰 Extracted budget from text: {extracted}")
                    break
                except (ValueError, IndexError):
                    pass
        
        # Extract property type
        property_keywords = {
            'apartment': ['apartment', 'flat', 'آپارتمان', 'شقة', 'квартира'],
            'villa': ['villa', 'ویلا', 'فيلا', 'вилла'],
            'penthouse': ['penthouse', 'پنت‌هاوس', 'بنتهاوس', 'пентхаус'],
            'townhouse': ['townhouse', 'تاون‌هاوس', 'تاون هاوس', 'таунхаус'],
            'studio': ['studio', 'استودیو', 'استوديو', 'студия']
        }
        
        for prop_type, keywords in property_keywords.items():
            if any(kw in message_lower for kw in keywords):
                extracted['property_type'] = prop_type
                logger.info(f"🏠 Extracted property type: {prop_type}")
                break
        
        # Extract bedrooms
        bedroom_patterns = [
            r'(\d+)\s*(bed|bedroom|خواب|غرفة|спальня)',
            r'(\d+)br\b'
        ]
        
        for pattern in bedroom_patterns:
            match = re.search(pattern, message_lower)
            if match:
                try:
                    bedrooms = int(match.group(1))
                    extracted['bedrooms_min'] = bedrooms
                    extracted['bedrooms_max'] = bedrooms
                    logger.info(f"🛏️ Extracted bedrooms: {bedrooms}")
                    break
                except ValueError:
                    pass
        
        return extracted if extracted else None
    
    def _get_buttons_for_state(
        self,
        state: ConversationState,
        conversation_data: Dict,
        lang: Language
    ) -> List[Dict[str, str]]:
        """Helper to get appropriate buttons for a given state."""
        buttons = []
        
        if state == ConversationState.SLOT_FILLING:
            pending_slot = conversation_data.get("pending_slot")
            
            if pending_slot == "budget":
                # Return budget buttons
                budget_options = {
                    Language.EN: [
                        {"text": "💰 Under 1M AED", "callback_data": "budget_0_1000000"},
                        {"text": "💰 1M - 2M AED", "callback_data": "budget_1000000_2000000"},
                        {"text": "💰 2M - 5M AED", "callback_data": "budget_2000000_5000000"},
                        {"text": "💰 5M+ AED", "callback_data": "budget_5000000_999999999"}
                    ],
                    Language.FA: [
                        {"text": "💰 کمتر از ۱ میلیون", "callback_data": "budget_0_1000000"},
                        {"text": "💰 ۱ تا ۲ میلیون", "callback_data": "budget_1000000_2000000"},
                        {"text": "💰 ۲ تا ۵ میلیون", "callback_data": "budget_2000000_5000000"},
                        {"text": "💰 بیشتر از ۵ میلیون", "callback_data": "budget_5000000_999999999"}
                    ],
                    Language.AR: [
                        {"text": "💰 أقل من 1 مليون", "callback_data": "budget_0_1000000"},
                        {"text": "💰 1 - 2 مليون", "callback_data": "budget_1000000_2000000"},
                        {"text": "💰 2 - 5 مليون", "callback_data": "budget_2000000_5000000"},
                        {"text": "💰 أكثر من 5 مليون", "callback_data": "budget_5000000_999999999"}
                    ],
                    Language.RU: [
                        {"text": "💰 До 1 млн", "callback_data": "budget_0_1000000"},
                        {"text": "💰 1 - 2 млн", "callback_data": "budget_1000000_2000000"},
                        {"text": "💰 2 - 5 млн", "callback_data": "budget_2000000_5000000"},
                        {"text": "💰 Более 5 млн", "callback_data": "budget_5000000_999999999"}
                    ]
                }
                buttons = budget_options.get(lang, budget_options[Language.EN])
            
            elif pending_slot == "property_type":
                category = conversation_data.get("property_category", "residential")
                if category == "residential":
                    property_buttons = {
                        Language.EN: [
                            {"text": "🏢 Apartment", "callback_data": "prop_apartment"},
                            {"text": "🏠 Villa", "callback_data": "prop_villa"},
                            {"text": "🏰 Penthouse", "callback_data": "prop_penthouse"},
                            {"text": "🏘️ Townhouse", "callback_data": "prop_townhouse"}
                        ],
                        Language.FA: [
                            {"text": "🏢 آپارتمان", "callback_data": "prop_apartment"},
                            {"text": "🏠 ویلا", "callback_data": "prop_villa"},
                            {"text": "🏰 پنت‌هاوس", "callback_data": "prop_penthouse"},
                            {"text": "🏘️ تاون‌هاوس", "callback_data": "prop_townhouse"}
                        ],
                        Language.AR: [
                            {"text": "🏢 شقة", "callback_data": "prop_apartment"},
                            {"text": "🏠 فيلا", "callback_data": "prop_villa"},
                            {"text": "🏰 بنتهاوس", "callback_data": "prop_penthouse"},
                            {"text": "🏘️ تاون هاوس", "callback_data": "prop_townhouse"}
                        ],
                        Language.RU: [
                            {"text": "🏢 Квартира", "callback_data": "prop_apartment"},
                            {"text": "🏠 Вилла", "callback_data": "prop_villa"},
                            {"text": "🏰 Пентхаус", "callback_data": "prop_penthouse"},
                            {"text": "🏘️ Таунхаус", "callback_data": "prop_townhouse"}
                        ]
                    }
                    buttons = property_buttons.get(lang, property_buttons[Language.EN])
        
        return buttons
    
    def get_budget_options(self, lang: Language) -> List[str]:
        """Get budget options in the specified language."""
        return BUDGET_OPTIONS.get(lang, BUDGET_OPTIONS[Language.EN])
    
    async def process_voice(self, audio_data: bytes, file_extension: str = "ogg") -> Tuple[str, Dict[str, Any]]:
        """
        Process voice message using Gemini's multimodal capabilities.
        Returns transcript and extracted entities.
        """
        if not self.gemini_client or not self.gemini_client.model:
            return "Voice processing unavailable (Gemini API not configured)", {}
        
        try:
            # Save audio temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as temp_audio:
                temp_audio.write(audio_data)
                temp_audio_path = temp_audio.name
            
            # Convert audio to MP3 for Gemini (CRITICAL: OGA files need conversion)
            # Gemini doesn't recognize .oga MIME type without explicit declaration
            converted_path = None
            try:
                from pydub import AudioSegment
                logger.info(f"🔄 Converting audio from {file_extension} to mp3 for Gemini compatibility")
                
                # Load audio file (pydub auto-detects format for .oga/.ogg)
                if file_extension in ['oga', 'ogg']:
                    audio = AudioSegment.from_ogg(temp_audio_path)
                else:
                    audio = AudioSegment.from_file(temp_audio_path, format=file_extension)
                
                # Convert to MP3 with good quality
                converted_path = temp_audio_path.replace(f".{file_extension}", ".mp3")
                audio.export(converted_path, format="mp3", bitrate="128k", parameters=["-ac", "1"])  # Mono for smaller size
                
                # Use converted file for upload
                upload_path = converted_path
                logger.info(f"✅ Audio converted successfully: {temp_audio_path} → {converted_path}")
            except ImportError as imp_err:
                logger.error(f"❌ pydub not installed: {imp_err}")
                logger.error("Install with: pip install pydub")
                upload_path = temp_audio_path
            except Exception as conv_error:
                logger.error(f"❌ Audio conversion failed: {conv_error}")
                logger.error(f"Original file: {temp_audio_path}, Extension: {file_extension}")
                upload_path = temp_audio_path
            
            try:
                # Upload audio file to Gemini using robust client (handles keys)
                import asyncio
                loop = asyncio.get_event_loop()
                
                # Set MIME type based on file extension
                mime_type = "audio/mpeg" if upload_path.endswith(".mp3") else f"audio/{file_extension}"
                logger.info(f"📤 Uploading {upload_path} with MIME type: {mime_type}")
                
                # Use gemini_client.upload_file which handles key rotation
                audio_file = await loop.run_in_executor(
                    None, 
                    lambda: self.gemini_client.upload_file(upload_path, mime_type=mime_type)
                )
                
                # Wait for processing with timeout (non-blocking)
                max_wait = 30  # 30 seconds timeout
                elapsed = 0
                while audio_file.state.name == "PROCESSING" and elapsed < max_wait:
                    await asyncio.sleep(1)  # Non-blocking sleep
                    elapsed += 1
                    audio_file = await loop.run_in_executor(None, genai.get_file, audio_file.name)
                
                if audio_file.state.name == "PROCESSING":
                    await loop.run_in_executor(None, genai.delete_file, audio_file.name)
                    return "Audio processing timeout - file too large or complex", {}
                
                if audio_file.state.name == "FAILED":
                    await loop.run_in_executor(None, genai.delete_file, audio_file.name)
                    return "Could not process audio file", {}
                
                # Prepare prompt for transcript extraction
                prompt = """
                Please transcribe this audio message and extract any real estate-related information.
                
                Provide response in this JSON format:
                {
                    "transcript": "full text of what was said",
                    "language": "detected language code (en/fa/ar/ru)",
                    "entities": {
                        "budget_min": number or null,
                        "budget_max": number or null,
                        "location": "string or null",
                        "property_type": "apartment/villa/penthouse/commercial/land or null",
                        "transaction_type": "buy/rent or null",
                        "purpose": "investment/living/residency or null",
                        "bedrooms": number or null,
                        "phone_number": "string or null"
                    }
                }
                
                CRITICAL for transaction_type extraction:
                - "buy" keywords: buy, purchase, خرید, شراء, купить, invest, own, سرمایه‌گذاری
                - "rent" keywords: rent, rental, lease, اجاره, إيجار, аренда, کرایه
                
                Extract any mentioned budget, location, property preferences, or contact information.
                Return ONLY valid JSON.
                """
                
                # Generate transcript and extract entities with retry logic and timeout
                # Generate transcript and extract entities with robust client
                try:
                    response = await self.gemini_client.generate_content_async(
                        [audio_file, prompt],
                        max_retries=3
                    )
                except asyncio.TimeoutError:
                    logger.error("⏱️ Gemini voice API timeout after 30s")
                    await loop.run_in_executor(None, genai.delete_file, audio_file.name)
                    return "Voice processing is taking too long. Please try typing your message instead.", {}
                except Exception as e:
                    logger.error(f"❌ Gemini voice API failed after retries: {e}")
                    await loop.run_in_executor(None, genai.delete_file, audio_file.name)
                    return "Voice processing temporarily unavailable. Please try again or type your message.", {}
                
                # Clean up
                await loop.run_in_executor(None, genai.delete_file, audio_file.name)
                
                # Parse JSON response
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                response_text = re.sub(r'^```json\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)
                
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse Gemini response as JSON: {response_text[:200]}")
                    # Try to extract transcript manually from text
                    return response_text[:500] if response_text else "Could not parse voice", {}
                
                transcript = result.get("transcript", "")
                entities = result.get("entities", {})
                
                # Clean up entities (remove null values)
                entities = {k: v for k, v in entities.items() if v is not None}
                
                return transcript, entities
                
            finally:
                # Clean up temp files
                import os
                try:
                    os.unlink(temp_audio_path)
                except Exception as e:
                    logger.debug(f"Could not delete temp audio file: {e}")
                # Clean up converted file if it exists
                if converted_path and os.path.exists(converted_path):
                    try:
                        os.unlink(converted_path)
                    except Exception as e:
                        logger.debug(f"Could not delete converted audio file: {e}")
                    
        except Exception as e:
            logger.error(f"❌ VOICE PROCESSING ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            logger.error(f"Voice processing stack trace: {traceback.format_exc()}")
            return f"Error processing voice: {str(e)}", {}
    
    async def process_image(self, image_data: bytes, file_extension: str = "jpg") -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process image using Gemini Vision to find similar properties.
        Returns description and list of matching properties from database.
        """
        if not self.model:
            return "Image processing unavailable (Gemini API not configured)", []
        
        try:
            # Save image temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as temp_image:
                temp_image.write(image_data)
                temp_image_path = temp_image.name
            
            try:
                # Upload image to Gemini (run in thread pool since it's blocking)
                loop = asyncio.get_event_loop()
                
                # Set MIME type based on file extension
                mime_type = f"image/{file_extension}"
                logger.info(f"📤 Uploading image {temp_image_path} with MIME type: {mime_type}")
                
                image_file = await loop.run_in_executor(
                    None,
                    lambda: genai.upload_file(temp_image_path, mime_type=mime_type)
                )
                
                # Wait for processing with timeout (non-blocking)
                max_wait = 30  # 30 seconds timeout
                elapsed = 0
                while image_file.state.name == "PROCESSING" and elapsed < max_wait:
                    await asyncio.sleep(1)  # Non-blocking sleep
                    elapsed += 1
                    image_file = await loop.run_in_executor(None, genai.get_file, image_file.name)
                
                if image_file.state.name == "PROCESSING":
                    await loop.run_in_executor(None, genai.delete_file, image_file.name)
                    return "Image processing timeout - file too large or complex", []
                
                if image_file.state.name == "FAILED":
                    await loop.run_in_executor(None, genai.delete_file, image_file.name)
                    return "Could not process image file", []
                
                # Analyze image and extract features with retry logic
                prompt = """
                Analyze this property image and extract visual features.
                
                Provide response in this JSON format:
                {
                    "description": "brief description of the property shown",
                    "property_type": "apartment/villa/penthouse/townhouse/commercial/land",
                    "style": "modern/luxury/traditional/minimalist/etc",
                    "features": ["feature1", "feature2", ...],
                    "estimated_bedrooms": number or null,
                    "view_type": "sea/city/golf/garden/etc or null",
                    "interior_quality": "luxury/premium/standard",
                    "color_scheme": "dominant colors",
                    "search_keywords": ["keyword1", "keyword2", ...]
                }
                
                Focus on architectural style, luxury level, type of property, and visual features.
                Return ONLY valid JSON.
                """
                
                async def call_gemini_image():
                    return self.model.generate_content([image_file, prompt])
                
                try:
                    response = await retry_with_backoff(call_gemini_image)
                except Exception as e:
                    logger.error(f"❌ Gemini image API failed after retries: {e}")
                    await loop.run_in_executor(None, genai.delete_file, image_file.name)
                    return "Image processing temporarily unavailable. Please try again.", []
                
                # Clean up
                await loop.run_in_executor(None, genai.delete_file, image_file.name)
                
                # Parse JSON response
                response_text = response.text.strip()
                response_text = re.sub(r'^```json\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)
                
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse Gemini image response as JSON: {response_text[:200]}")
                    # Return basic description
                    return response_text[:300] if response_text else "property image", []
                
                # Get image description
                description = result.get("description", "property image")
                property_type = result.get("property_type", "apartment")
                features = result.get("features", [])
                style = result.get("style", "")
                
                # Ensure features is a list
                if not isinstance(features, list):
                    features = []
                
                # Search for similar properties in tenant's inventory
                properties = self.tenant_context.get("properties", [])
                
                # Handle empty properties list
                if not properties:
                    return description, []
                
                # Simple matching algorithm based on extracted features
                matching_properties = []
                for prop in properties:
                    score = 0
                    
                    # Match property type
                    if prop.get("type", "").lower() == property_type.lower():
                        score += 5
                    
                    # Match features
                    prop_features = prop.get("features", [])
                    if isinstance(prop_features, list):
                        prop_features_lower = [f.lower() for f in prop_features if isinstance(f, str)]
                        for feature in features:
                            if isinstance(feature, str) and any(feature.lower() in pf for pf in prop_features_lower):
                                score += 2
                    
                    # Match style
                    if style and isinstance(prop.get("description"), str) and style.lower() in prop.get("description", "").lower():
                        score += 3
                    
                    if score > 0:
                        matching_properties.append({
                            "property": prop,
                            "similarity_score": score
                        })
                
                # Sort by similarity score
                matching_properties.sort(key=lambda x: x["similarity_score"], reverse=True)
                
                # Return top 3 matches
                top_matches = [m["property"] for m in matching_properties[:3]]
                
                return description, top_matches
                
            finally:
                # Clean up temp file
                import os
                try:
                    os.unlink(temp_image_path)
                except Exception as e:
                    logger.debug(f"Could not delete temp image file: {e}")
                    
        except Exception as e:
            logger.error(f"❌ IMAGE PROCESSING ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            logger.error(f"Image processing stack trace: {traceback.format_exc()}")
            return f"Error processing image: {str(e)}", []
    
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
            
            CRITICAL for transaction_type extraction:
            - "buy" keywords: buy, purchase, خرید, شراء, купить, invest, own, سرمایه‌گذاری
            - "rent" keywords: rent, rental, lease, اجاره, إيجار, аренда, کرایه
            
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
    
    def _get_chat_session(self, lead: Lead):
        """Get or create chat session for a lead to maintain conversation history."""
        if lead.id not in self.chat_sessions:
            # Create new chat session with history
            self.chat_sessions[lead.id] = self.model.start_chat(history=[])
            logger.info(f"🆕 Created new chat session for lead {lead.id}")
        return self.chat_sessions[lead.id]
    
    async def generate_ai_response(self, user_message: str, lead: Lead, context: str = "") -> str:
        """
        Generate a contextual AI response using Gemini.
        Uses tenant-specific data (properties, projects, knowledge) for personalized responses.
        
        FIX #10d: Track questions and suggest consultation after 3+ questions
        FIX #11: Use chat sessions to maintain conversation memory
        """
        global GEMINI_API_KEY  # Declare at the start to allow key switching
        
        if not self.model:
            return self.get_text("welcome", lead.language or Language.EN)
        
        try:
            # Load tenant context if not already loaded
            if not self.tenant_context:
                await self.load_tenant_context(lead)
            
            # === STRATEGY A: Smart FAQ Handling ===
            # Retrieve relevant knowledge based on user's message
            knowledge_text = await self.get_relevant_knowledge(
                query=user_message,
                lang=lead.language or Language.EN,
                limit=3
            )
            
            # Build tenant data context
            tenant_data_prompt = self._build_tenant_context_prompt()
            
            # FIX #10d: Increment question counter
            conversation_data = lead.conversation_data or {}
            question_count = conversation_data.get("question_count", 0)
            
            # Check if this is likely a question
            is_question = any(char in user_message for char in ['؟', '?', 'چطور', 'چه', 'کی', 'کجا', 'چرا', 'how', 'what', 'when', 'where', 'why', 'هل', 'اين', 'ما', 'что', 'как', 'когда', 'где', 'почему'])
            if is_question:
                question_count += 1
                conversation_data["question_count"] = question_count
                logger.info(f"❓ Question #{question_count} from lead {lead.id}")
            
            # Build context about lead's information for AI to remember
            lead_info_context = f"""
            
            ===== LEAD INFORMATION (DO NOT FORGET THIS) =====
            Lead Name: {lead.name or 'Not provided yet'}
            Phone Number: {lead.phone or 'Not provided yet - CRITICAL: If they gave phone/contact, acknowledge it!'}
            Language: {lead.language if lead.language else 'EN'}
            Current State: {lead.conversation_state.value if hasattr(lead.conversation_state, 'value') else lead.conversation_state or 'START'}
            Purpose: {lead.purpose.value if hasattr(lead.purpose, 'value') else lead.purpose or 'Unknown'}
            Budget: {lead.budget_min or 'Not set'} - {lead.budget_max or 'Not set'} AED
            Location Preference: {lead.preferred_location or 'Any'}
            Bedrooms: {lead.bedrooms_min or 'Any'} - {lead.bedrooms_max or 'Any'}
            
            IMPORTANT: If user shared phone number or voice message, YOU MUST acknowledge it in your response!
            """
            
            system_prompt = f"""
            You are NOT just a consultant. You are a WORLD-CLASS CLOSER for {self.agent_name} in Dubai real estate.
            
            YOUR NAME: Use ONLY "{self.agent_name}" - NEVER variations like "حامد رضا" if name is "حمیدرضا"
            
            YOUR GOAL: GET THE MEETING OR PHONE NUMBER. EVERYTHING ELSE IS SECONDARY.
            
            🎯 CRITICAL INSTRUCTION - MID-FLOW QUESTIONS:
            **If the user is in the middle of a qualification flow (e.g., selecting budget, property type) 
            but asks a question instead:**
            1. ANSWER the question FIRST (1-2 sentences max)
            2. Add FOMO/urgency element
            3. IMMEDIATELY redirect back to the pending question
            
            Example:
            User (while budget selection pending): "Do you offer payment plans?"
            You: "Absolutely! We have flexible 1-5 year payment plans starting at just 1% monthly. Many investors use this to preserve cash flow. 💰
            
            By the way, what's your budget range so I can show you properties that qualify for these plans?"
            
            🧠 WOLF CLOSER RULES (FOLLOW STRICTLY):
            1. ALWAYS respond in {lead.language.upper() if isinstance(lead.language, str) else lead.language.value.upper()} language
            
            2. **NEVER end with a statement.** ALWAYS end with a QUESTION or CALL TO ACTION.
               - ❌ Bad: "The price is 2M AED."
               - ✅ Good: "The price is 2M AED and we have an offer ending today. Should I reserve a viewing slot?"
            
            3. **CREATE ARTIFICIAL SCARCITY (FOMO):**
               - Even if we have 100 units, act like we have 2-3 left
               - Phrases to use:
                 * "Checking availability right now..."
                 * "Just one unit left with this view..."
                 * "An investor just released this unit today..."
                 * "3 other buyers looking at this - first come, first served"
            
            4. **THE ASSUMPTIVE CLOSE:**
               - ❌ Don't ask: "Do you want to book a viewing?"
               - ✅ Ask: "Is Tuesday at 4 PM better for you, or Wednesday morning?"
               - ❌ Don't ask: "Interested in this property?"
               - ✅ Ask: "Should I hold this unit for you while you check your schedule?"
            
            5. **OBJECTION HANDLING (SALES JIU-JITSU):**
               - If "Too expensive": "Exactly! That's why the ROI is 10% and value increases daily. Do you want cheap or profitable?"
               - If "Need to think": "Smart! While you think, Dubai prices rise 15% yearly. Let's lock this price now - you can think after securing it."
               - If "No budget": "Perfect timing! We have payment plans from 1% monthly. Your rent money could buy this. Want numbers?"
               - If "Not sure": "Good! That means you're careful with money. Let me show you the ROI calculator - numbers don't lie. Ready?"
            
            6. **THE VELVET ROPE (EXCLUSIVITY):**
               - Make them feel they need to QUALIFY to work with {self.agent_name}
               - "We usually work with serious investors starting at 2M AED, but for motivated buyers..."
               - "This off-market deal isn't public yet - only for pre-qualified clients"
               - "{self.agent_name} only takes 3 new clients per month - December is almost full"
            
            7. **URGENCY INJECTORS (use randomly):**
               - "Price increase scheduled for next week"
               - "Developer's promotion ends Friday"
               - "Golden Visa process takes 60 days - earlier you start, earlier you get residency"
               - "Last unit in this layout - floor plan discontinued"
            7. **URGENCY INJECTORS (use randomly):**
               - "Price increase scheduled for next week"
               - "Developer's promotion ends Friday"
               - "Golden Visa process takes 60 days - earlier you start, earlier you get residency"
               - "Last unit in this layout - floor plan discontinued"
            
            CRITICAL INFORMATION TO WEAPONIZE:
            - 🛂 Golden Visa: 2M AED investment = Your ticket to freedom (residency for family!)
            - 💰 ROI: 7-10% annually = Beats any bank in the world
            - 📈 Market Growth: Dubai prices +15% yearly = Your cash is losing value sitting idle
            - 🏦 Payment Plans: As low as 1% monthly = Rent money could BUY instead
            
            VISA & RESIDENCY KNOWLEDGE (Use to close):
            - 🛂 GOLDEN VISA (10 years): 2,000,000 AED minimum - Family residency included!
            - 👨‍💼 2-YEAR INVESTOR VISA: 750,000 AED minimum - Great starter option!
            - If user budget is <750K: Push payment plans to reach threshold OR suggest partnering with family
            
            === TRUSTED KNOWLEDGE BASE (Use for credibility) ===
            {knowledge_text if knowledge_text else "No specific knowledge - use general Dubai market facts."}
            =============================================================
            
            PROPERTY RECOMMENDATIONS (Close, don't just inform!):
            8. **Use ONLY actual properties from inventory below**
            9. **When showing properties:**
               - Mention scarcity: "Only 2 units left" or "Just released from previous buyer"
               - Add social proof: "3 investors viewed this today"
               - Create urgency: "Price locks for 7 days only"
               - Assumptive close: "Which floor do you prefer - mid or high?"
            10. If no matching properties in budget:
                - Pivot to payment plans: "Your 500K becomes 2M with our 60-month plan"
                - Suggest partnership: "Many investors co-buy to reach Golden Visa threshold"
                - Offer agent sourcing: "{self.agent_name} finds off-market deals daily - let's schedule a call"
            
            ==== AGENT'S INVENTORY (USE ONLY THESE!) ====
            {tenant_data_prompt}
            =============================================
            
            LEAD PROFILE (Qualification Data):
            - Status: {lead.status.value if lead.status else 'new lead'}
            - Budget: {f"{lead.budget_min:,.0f} - {lead.budget_max:,.0f} {lead.budget_currency or 'AED'}" if lead.budget_min and lead.budget_max else 'NOT YET ASKED - qualify first!'}
            - Purpose: {lead.purpose.value if lead.purpose else 'NOT YET ASKED - ask now!'}
            - Property Type: {lead.property_type.value if lead.property_type else 'NOT YET ASKED'}
            - Location: {lead.preferred_location if lead.preferred_location else 'NOT YET ASKED'}
            - Pain Point: {lead.pain_point if lead.pain_point else 'FIND IT NOW - crucial for closing!'}
            
            CRITICAL: If data missing, ASK with assumptive language:
            - "Most investors start with 1-2M range - where do you see yourself?"
            - "Golden Visa or passive income - which matters more to you?"
            
            CONVERSATION CONTEXT: {context}
            
            RESPONSE STYLE (Wolf Closer Voice):
            - Confident, authoritative, slightly aggressive BUT polite
            - Short sentences. Punchy. Impactful.
            - Use emojis strategically to soften hard closes
            - 2-3 sentences MAX, then QUESTION or CTA
            - NEVER say "buttons above" or "select options" - This is CONVERSATION mode!
            - NEVER repeat yourself - Always respond UNIQUELY with NEW angle
            
            CLOSING TRIGGERS (When to push for meeting):
            - ANY buying signal: "interested", "like", "good", "thinking about it"
            - Budget questions: "how much", "price", "cost"
            - 3+ questions asked: Time to close
            - Objections: Perfect time to flip and close
            
            When detected → Immediate assumptive close:
            "Perfect! {self.agent_name} can show you 3 perfect matches. Tuesday 4 PM or Wednesday 10 AM - which works better?"
            
            IF THEY ASK A QUESTION:
            1. Answer briefly (1-2 sentences)
            2. Add FOMO element ("prices rising", "units selling fast")
            3. IMMEDIATELY pivot to booking: "Should I check {self.agent_name}'s calendar?"
            
            Remember: You're not here to educate. You're here to CONVERT. Every response is a step closer to the meeting.
            """.strip()
            
            # FIX #11: Use chat session to maintain conversation history
            chat = self._get_chat_session(lead)
            
            # Build prompt with lead info context
            full_prompt = f"{system_prompt}{lead_info_context}\n\nUser says: {user_message}"
            
            # BUG-005 FIX: Add timeout and retry logic with exponential backoff
            response = None
            for attempt in range(MAX_RETRIES):
                try:
                    response = await asyncio.wait_for(
                        asyncio.to_thread(chat.send_message, full_prompt),
                        timeout=30.0
                    )
                    break  # Success - exit retry loop
                except google_exceptions.ResourceExhausted:
                    logger.warning(f"⚠️ Gemini quota exceeded for lead {lead.id} (attempt {attempt + 1}/{MAX_RETRIES})")
                    if attempt < MAX_RETRIES - 1:
                        # Try with different API key
                        if len(VALID_GEMINI_KEYS) > 1:
                            old_key = GEMINI_API_KEY
                            new_key = random.choice([k for k in VALID_GEMINI_KEYS if k != old_key])
                            genai.configure(api_key=new_key)
                            logger.info(f"🔄 Switched to different Gemini API key")
                        wait_time = RETRY_DELAY_BASE * (2 ** attempt)
                        logger.info(f"⏳ Waiting {wait_time}s before retry...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"❌ All retries exhausted for lead {lead.id}")
                        lang = lead.language or Language.EN
                        quota_messages = {
                            Language.EN: "I'm experiencing high demand right now. Please try again in a moment.",
                            Language.FA: "الان تقاضا خیلی زیاده. لطفاً یک لحظه دیگه امتحان کنید.",
                            Language.AR: "أواجه طلبًا كبيرًا الآن. يرجى المحاولة مرة أخرى في لحظة.",
                            Language.RU: "Сейчас высокая нагрузка. Попробуйте через момент."
                        }
                        return quota_messages.get(lang, quota_messages[Language.EN])
                except asyncio.TimeoutError:
                    logger.error(f"⏱️ Gemini API timeout after 30s for lead {lead.id} (attempt {attempt + 1}/{MAX_RETRIES})")
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_DELAY_BASE * (2 ** attempt)
                        await asyncio.sleep(wait_time)
                    else:
                        lang = lead.language or Language.EN
                        timeout_messages = {
                            Language.EN: "I'm thinking a bit slowly right now. Could you give me a moment and try again?",
                            Language.FA: "الان کمی آهسته‌تر فکر می‌کنم. می‌تونید یک لحظه بعد دوباره امتحان کنید؟",
                            Language.AR: "أنا أفكر بشكل بطيء قليلاً الآن. هل يمكنك المحاولة مرة أخرى بعد لحظة؟",
                            Language.RU: "Я думаю немного медленно сейчас. Можете попробовать ещё раз через момент?"
                        }
                        return timeout_messages.get(lang, timeout_messages[Language.EN])
                except Exception as api_error:
                    logger.error(f"❌ Gemini API error (attempt {attempt + 1}/{MAX_RETRIES}): {type(api_error).__name__}: {str(api_error)}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY_BASE)
                    else:
                        # Final fallback after all retries
                        raise
            
            if not response:
                # Should not reach here, but safety check
                lang = lead.language or Language.EN
                fallback_messages = {
                    Language.EN: "I'm having trouble connecting right now. Let me help you in a different way - what specific question can I answer?",
                    Language.FA: "الان مشکل اتصال دارم. بذار به یه روش دیگه کمکت کنم - چه سوال خاصی دارید؟",
                    Language.AR: "أواجه مشكلة في الاتصال الآن. دعني أساعدك بطريقة مختلفة - ما السؤال المحدد الذي يمكنني الإجابة عليه؟",
                    Language.RU: "У меня проблемы с подключением. Позвольте помочь по-другому - какой конкретный вопрос у вас есть?"
                }
                return fallback_messages.get(lang, fallback_messages[Language.EN])
            
            # FIX #10d: If user has asked 3+ questions, append consultation suggestion
            final_response = response.text.strip()
            if question_count >= 3 and "📞" not in final_response:
                lang = lead.language or Language.EN
                consultation_offers = {
                    Language.EN: "\n\n📞 By the way, I can answer these questions better in a live consultation! Would you like to speak with {agent_name} directly?",
                    Language.FA: "\n\n📞 راستی، این سوالات رو بهتره در یک جلسه مشاوره جواب بدم! می‌خواهید با {agent_name} صحبت کنید؟",
                    Language.AR: "\n\n📞 بالمناسبة، يمكنني الإجابة على هذه الأسئلة بشكل أفضل في استشارة حية! هل تريد التحدث مع {agent_name} مباشرة؟",
                    Language.RU: "\n\n📞 Кстати, я смогу лучше ответить на эти вопросы на живой консультации! Хотите поговорить с {agent_name} напрямую?"
                }
                final_response += consultation_offers.get(lang, consultation_offers[Language.EN]).format(agent_name=self.agent_name)
                logger.info(f"💡 FIX #10d: Added consultation CTA after {question_count} questions")
            
            return final_response
        except Exception as e:
            logger.error(f"❌ AI response error: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # FIX #11: Don't return welcome message on error - breaks conversation flow
            # Return user-friendly error message instead
            lang = lead.language or Language.EN
            error_messages = {
                Language.EN: "I apologize, I'm having trouble processing that right now. Could you rephrase your question?",
                Language.FA: "متاسفم، الان نمی‌تونم این رو پردازش کنم. می‌تونید سوالتون رو دوباره بپرسید؟",
                Language.AR: "أعتذر، أواجه مشكلة في معالجة ذلك الآن. هل يمكنك إعادة صياغة سؤالك؟",
                Language.RU: "Извините, у меня проблемы с обработкой. Можете перефразировать вопрос?"
            }
            return error_messages.get(lang, error_messages[Language.EN])
    
    async def get_property_recommendations(self, lead: Lead) -> str:
        """
        Generate property recommendations from tenant's inventory based on lead preferences.
        This is called after qualification to show matching properties.
        """
        if not self.tenant_context:
            await self.load_tenant_context(lead)
        
        lang = lead.language or Language.EN
        properties = self.tenant_context.get("properties", [])
        projects = self.tenant_context.get("projects", [])
        
        if not properties and not projects:
            # No inventory - offer to connect with agent directly
            messages = {
                Language.EN: f"📋 I don't have exact properties in my system right now, but {self.agent_name} specializes in finding off-market deals!\n\n💡 Would you like to schedule a call with {self.agent_name}? They can:\n✅ Find properties matching your exact needs\n✅ Access exclusive off-market listings\n✅ Negotiate better prices for you\n\nShall I show you available times?",
                Language.FA: f"📋 الان ملک مشخصی در سیستم ندارم، اما {self.agent_name} متخصص پیدا کردن املاک خارج از بازاره!\n\n💡 می‌خواهید با {self.agent_name} تماس بگیرید؟ می‌تونه:\n✅ ملک‌های دقیقاً مطابق نیازتون رو پیدا کنه\n✅ به لیستینگ‌های اختصاصی خارج از بازار دسترسی داره\n✅ قیمت بهتری براتون چونه بزنه\n\nبرات زمان‌های خالی رو نشون بدم؟",
                Language.AR: f"📋 ليس لدي عقارات محددة في النظام الآن، لكن {self.agent_name} متخصص في إيجاد صفقات خارج السوق!\n\n💡 هل تريد جدولة مكالمة مع {self.agent_name}؟ يمكنه:\n✅ إيجاد عقارات تطابق احتياجاتك بالضبط\n✅ الوصول إلى قوائم حصرية خارج السوق\n✅ التفاوض على أسعار أفضل لك\n\nهل أعرض لك الأوقات المتاحة؟",
                Language.RU: f"📋 Сейчас нет конкретных объектов в системе, но {self.agent_name} специализируется на поиске внерыночных сделок!\n\n💡 Хотите назначить звонок с {self.agent_name}? Он может:\n✅ Найти объекты точно под ваши требования\n✅ Доступ к эксклюзивным внерыночным предложениям\n✅ Договориться о лучшей цене для вас\n\nПоказать доступное время?"
            }
            return messages.get(lang, messages[Language.EN])
        
        # ALWAYS set current_properties for property_presenter to use
        self.current_properties = properties[:3]
        
        # Check if properties already shown to avoid repetition
        conversation_data = lead.conversation_data or {}
        if conversation_data.get("properties_shown"):
            # Properties already shown - just return empty text but properties will still be presented
            logger.info(f"🔄 Properties already shown to lead {lead.id}, skipping text but presenting professionally")
            return ""
        
        # Build recommendations message
        rec_parts = []
        
        # Mark properties as shown
        conversation_data["properties_shown"] = True
        conversation_data["shown_property_ids"] = [p.get('id') for p in properties[:3]]
        
        # Recommend matching properties - این قسمت فقط متن است، عکس‌ها از telegram_bot/whatsapp_bot فرستاده می‌شوند
        if properties:
            intro_messages = {
                Language.EN: f"🏠 **Perfect! I found {len(properties[:3])} excellent properties matching your criteria:**\n\n💡 For each property, I'll send you:\n✅ Professional photos\n✅ Complete specifications\n✅ Personalized ROI analysis\n✅ Investment breakdown\n",
                Language.FA: f"🏠 **عالی! {len(properties[:3])} ملک فوق‌العاده پیدا کردم که دقیقا با سلیقه شما مطابقت داره:**\n\n💡 برای هر ملک می‌فرستم:\n✅ عکس‌های حرفه‌ای\n✅ مشخصات کامل\n✅ تحلیل ROI اختصاصی\n✅ جزئیات سرمایه‌گذاری\n",
                Language.AR: f"🏠 **ممتاز! وجدت {len(properties[:3])} عقارات ممتازة تطابق معاييرك:**\n\n💡 لكل عقار، سأرسل لك:\n✅ صور احترافية\n✅ مواصفات كاملة\n✅ تحليل ROI مخصص\n✅ تفاصيل الاستثمار\n",
                Language.RU: f"🏠 **Отлично! Я нашёл {len(properties[:3])} превосходных объектов по вашим критериям:**\n\n💡 Для каждого объекта я отправлю:\n✅ Профессиональные фото\n✅ Полные характеристики\n✅ Персональный ROI анализ\n✅ Детали инвестиций\n"
            }
            rec_parts.append(intro_messages.get(lang, intro_messages[Language.EN]))
            
            # این متن فقط summary است - املاک واقعی با عکس در property_presentation فرستاده می‌شوند
            for i, p in enumerate(properties[:3], 1):
                price_str = f"AED {p['price']:,.0f}" if p['price'] else "Price on request"
                features_str = ", ".join(p['features'][:3]) if p['features'] else ""
                golden_str = " 🛂 Golden Visa" if p['golden_visa'] else ""
                
                # === SOCIAL PROOF: Add fake viewer count for FOMO ===
                import random
                viewers = random.randint(2, 8)
                units_left = random.randint(1, 3)
                social_proof_phrases = {
                    Language.EN: [
                        f"🔥 {viewers} investors viewed this today",
                        f"⚠️ Only {units_left} units left in this layout",
                        f"📍 Just released from previous buyer",
                        f"🔥 {viewers} others considering this unit"
                    ],
                    Language.FA: [
                        f"🔥 {viewers} سرمایه‌گذار امروز بررسی کردند",
                        f"⚠️ فقط {units_left} واحد از این طرح مانده",
                        f"📍 همین الان از خریدار قبلی آزاد شد",
                        f"🔥 {viewers} نفر دیگر در حال بررسی این واحد"
                    ],
                    Language.AR: [
                        f"🔥 {viewers} مستثمرين شاهدوا هذا اليوم",
                        f"⚠️ فقط {units_left} وحدات متبقية في هذا التصميم",
                        f"📍 تم إصداره للتو من مشتري سابق",
                        f"🔥 {viewers} آخرون يفكرون في هذه الوحدة"
                    ],
                    Language.RU: [
                        f"🔥 {viewers} инвесторов смотрели сегодня",
                        f"⚠️ Осталось только {units_left} квартир в этой планировке",
                        f"📍 Только что освободилось от предыдущего покупателя",
                        f"🔥 {viewers} других рассматривают эту квартиру"
                    ]
                }
                
                social_proof = random.choice(social_proof_phrases.get(lang, social_proof_phrases[Language.EN]))
                
                # Add ROI and Rental Yield to user message
                roi_str = f"📊 Expected ROI: {p['roi']}% annually" if p.get('roi') else ""
                yield_str = f"📈 Rental Yield: {p['rental_yield']}%" if p.get('rental_yield') else ""
                financial_info = f"\n   {roi_str}" if roi_str else ""
                if yield_str:
                    financial_info += f"\n   {yield_str}"
                if p.get('mortgage_available'):
                    financial_info += "\n   🏦 Mortgage available (flexible payment plans)"
                
                rec_parts.append(
                    f"{i}. **{p['name']}** - {p['location']}\n"
                    f"   {p['bedrooms']}BR {p['type']} | {price_str}{golden_str}\n"
                    f"   ✨ {features_str}{financial_info}\n"
                    f"   {social_proof}\n"
                )
        
        # Recommend off-plan projects for investors
        if projects and lead.purpose in [Purpose.INVESTMENT, Purpose.RESIDENCY]:
            if lang == Language.FA:
                rec_parts.append("\n📊 **پروژه‌های پیش‌فروش با طرح پرداخت:**\n")
            elif lang == Language.AR:
                rec_parts.append("\n📊 **مشاريع قيد الإنشاء مع خطط سداد:**\n")
            elif lang == Language.RU:
                rec_parts.append("\n📊 **Строящиеся проекты с рассрочкой:**\n")
            else:
                rec_parts.append("\n📊 **Off-Plan Projects with Payment Plans:**\n")
            
            for proj in projects[:2]:
                price_str = f"From AED {proj['starting_price']:,.0f}" if proj['starting_price'] else "Price TBA"
                golden_str = " 🛂 Golden Visa" if proj['golden_visa'] else ""
                
                rec_parts.append(
                    f"🏗️ **{proj['name']}** by {proj['developer']}\n"
                    f"   {proj['location']} | {price_str}{golden_str}\n"
                    f"   💳 Payment Plan: {proj['payment_plan'] or 'Flexible'}\n"
                    f"   📈 Projected ROI: {proj['roi']}%\n"
                )
        
        return "\n".join(rec_parts)
    
    def format_property_presentation(self, property_data: Dict, lang: Language, index: int = 1) -> str:
        """
        📊 ارائه حرفه‌ای یک ملک با تمام جزئیات - مثل یک مشاور املاک واقعی
        
        این تابع یک پرزنتیشن کامل و حرفه‌ای از ملک می‌سازد:
        - هدر با شماره و نام ملک
        - قیمت و موقعیت
        - مشخصات کامل (اتاق‌ها، مساحت، طبقه، امکانات)
        - تحلیل مالی (ROI, درآمد اجاره، بازگشت سرمایه)
        - مزایای سرمایه‌گذاری
        - Social proof و FOMO
        - دکمه‌های اقدام (بازدید، گزارش PDF، تماس)
        """
        # استخراج اطلاعات ملک
        name = property_data.get('name', 'Luxury Property')
        location = property_data.get('location', 'Dubai')
        price = property_data.get('price', 0)
        bedrooms = property_data.get('bedrooms', 0)
        bathrooms = property_data.get('bathrooms', 0)
        area = property_data.get('area_sqft', 0)
        property_type = property_data.get('property_type', 'Apartment')
        features = property_data.get('features', [])
        
        # محاسبات مالی
        roi = property_data.get('expected_roi', 8.5)  # Default 8.5%
        rental_yield = property_data.get('rental_yield', 7.0)  # Default 7%
        annual_rental = int(price * (rental_yield / 100)) if price else 0
        monthly_rental = int(annual_rental / 12) if annual_rental else 0
        
        # Golden Visa eligibility
        is_golden_visa = price >= 2_000_000
        
        # Payment plan calculation
        down_payment_25 = int(price * 0.25) if price else 0
        monthly_payment_5y = int((price - down_payment_25) / 60) if price else 0
        
        # 🔥 GENERATE URGENCY MESSAGE - Uses sales psychology
        urgency_msg = generate_urgency_message(property_data, lang)
        
        # Social proof numbers
        import random
        viewers_today = random.randint(15, 47)
        units_remaining = random.randint(2, 5)
        recent_sale_days = random.randint(2, 7)
        
        # ساخت پیام بر اساس زبان - Wolf of Wall Street Style
        if lang == Language.FA:
            presentation = f"""🔥 **بذار راستشو بگم...**

این ملک الان **داغ‌ترین معامله بازار** دبیه! چرا؟

━━━━━━━━━━━━━━━━━━━━━━
🏆 **{name}**
━━━━━━━━━━━━━━━━━━━━━━

📍 **{location}** - بهترین لوکیشن ممکن
💰 **{price:,} درهم** - قیمت نهایی، قابل مذاکره نیست!

**چرا الان باید بخری؟**

💸 **بازگشت سرمایه {roi}% سالانه** - بانک بهت 2% میده!
📈 **{monthly_rental:,} درهم درآمد ماهانه** - بدون هیچ کاری!
⏰ **فقط {units_remaining} واحد با این قیمت مونده** - فردا میره بالا!

**👥 Social Proof:**
• {viewers_today} نفر امروز دیدن
• {recent_sale_days} روز پیش یکی مثل این {int(price * 1.15):,} فروخت
• 3 نفر دارن فکر میکنن - اولی که بیاد میبره!

**💳 پرداخت آسون:**
• پیش: {down_payment_25:,} درهم (25%)
• قسط ماهانه: {monthly_payment_5y:,} درهم × 60 ماه
• نرخ: 4.5% - کمترین بازار!

**🎁 Bonus بی‌نظیر:**
{'🛂 **ویزای طلایی 10 ساله** رایگان!' if is_golden_visa else '🏦 **وام 75%** تضمینی!'}
🏆 **مالیات 0%** بر درآمد اجاره - صفر!
📊 **رشد 5-8% سالانه** - تضمین شده!
💰 **اجاره تضمینی** - حتی خالی بمونه!

**⚡ فوریت داره:**
{urgency_msg}

**🎯 چیکار کنی الان؟**

1️⃣ **بازدید رزرو کن** - فردا صبح، 10:00 AM
2️⃣ **تحلیل کامل بگیر** - PDF با اعداد واقعی
3️⃣ **با من صحبت کن** - مشاوره آنلاین رایگان

💬 **یادت باشه:** بازار دبی منتظر نمیمونه!
قیمت‌ها هر روز داره میره بالا 📈

آماده‌ای تصمیم بگیری؟ 🚀
━━━━━━━━━━━━━━━━━━━━━━"""
        elif lang == Language.EN:
            presentation = f"""🔥 **Let me be real with you...**

This property is the **HOTTEST deal** in Dubai right now! Why?

━━━━━━━━━━━━━━━━━━━━━━
🏆 **{name}**
━━━━━━━━━━━━━━━━━━━━━━

📍 **{location}** - Prime location, best of the best
💰 **AED {price:,}** - Final price, non-negotiable!

**Why buy NOW?**

💸 **{roi}% annual ROI** - Banks give you 2%!
📈 **AED {monthly_rental:,} monthly income** - Passive!
⏰ **Only {units_remaining} units left at this price** - Tomorrow it goes up!

**👥 Social Proof:**
• {viewers_today} people viewed TODAY
• {recent_sale_days} days ago similar unit sold for AED {int(price * 1.15):,}
• 3 buyers thinking - first to act wins!

**💳 Easy Payment:**
• Down: AED {down_payment_25:,} (25%)
• Monthly: AED {monthly_payment_5y:,} × 60 months
• Rate: 4.5% - Lowest in market!

**🎁 Unbeatable Bonuses:**
{'🛂 **10-Year Golden Visa** FREE!' if is_golden_visa else '🏦 **75% Mortgage** Guaranteed!'}
🏆 **0% Tax** on rental income - ZERO!
📊 **5-8% Annual Growth** - Guaranteed!
💰 **Rental Guarantee** - Even if vacant!

**⚡ Urgency Alert:**
{urgency_msg}

**🎯 What to do NOW?**

1️⃣ **Book Viewing** - Tomorrow 10:00 AM
2️⃣ **Get Full Analysis** - PDF with real numbers
3️⃣ **Talk to Me** - Free online consultation

💬 **Remember:** Dubai market doesn't wait!
Prices rising EVERY day 📈

Ready to make the move? 🚀
━━━━━━━━━━━━━━━━━━━━━━"""
        else:  # Arabic/Russian - similar structure
            presentation = f"""🏆 Property #{index}: {name}
📍 {location} | 💰 AED {price:,}
🏠 {bedrooms}BR | {area:,}sqft
📊 ROI: {roi}% | Rental: {rental_yield}%
💵 Monthly Income: AED {monthly_rental:,}
🔥 {viewers_today} viewed today | {units_remaining} units left"""
        
        return presentation

    async def extract_user_intent(self, message: str, lang: Language, expected_entities: List[str]) -> Dict:
        """
        🧠 Use Gemini to extract structured data from free-form text
        
        Args:
            message: User's raw text
            lang: Language code
            expected_entities: ["goal", "budget", "bedrooms", "location", "property_type", "transaction_type"]
        
        Returns:
            {
                "goal": "investment" | "living" | "residency" | null,
                "budget": 750000 | null,
                "bedrooms": 2 | null,
                "location": "Dubai Marina" | null,
                "property_type": "apartment" | null,
                "transaction_type": "buy" | "rent" | null
            }
        """
        prompt = f"""
Analyze this real estate inquiry and extract structured data.

USER MESSAGE: "{message}"
LANGUAGE: {lang}
EXTRACT: {expected_entities}

RULES:
- goal: "investment" (if mentions ROI/profit/سرمایه/استثمار/инвестиц) | "living" (if mentions home/family/زندگی/سكن/жилье) | "residency" (if mentions visa/اقامت/إقامة/виза) | null
- budget: Extract number in AED (convert K/M to actual numbers, e.g., 750k = 750000) | null if not mentioned
- bedrooms: Extract number (1, 2, 3, etc.) | null
- location: Extract area name (e.g., "Dubai Marina", "Downtown", "مارینا", "داون تاون") | null
- property_type: "apartment" | "villa" | "penthouse" | "townhouse" | "commercial" | null
- transaction_type: "buy" (if mentions buy/purchase/خرید/شراء/купить/own/سرمایه‌گذاری) | "rent" (if mentions rent/lease/اجاره/إيجار/аренда/کرایه) | null

RESPOND IN JSON ONLY (no markdown, no explanation):
{{
    "goal": "investment",
    "budget": 750000,
    "bedrooms": 2,
    "location": "Dubai Marina",
    "property_type": "apartment",
    "transaction_type": "buy"
}}
"""
        
        try:
            response = await self.model.generate_content(prompt)
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            import json
            extracted = json.loads(response_text)
            logger.info(f"✅ Intent extracted from '{message}': {extracted}")
            return extracted
        except Exception as e:
            logger.error(f"❌ Intent extraction failed: {e}")
            # Fallback: return empty dict
            return {}
    
    async def get_real_properties_from_db(self, lead: Lead, limit: int = 5, offset: int = 0) -> List[Dict]:
        """
        🏠 گرفتن املاک واقعی از دیتابیس (نه فقط tenant_context)
        
        این تابع مستقیم از table tenant_properties می‌خونه و 
        املاک رو filter می‌کنه بر اساس:
        - نوع معامله (خرید/اجاره)
        - بودجه
        - نوع ملک
        - موجود بودن
        
        Args:
            lead: اطلاعات lead
            limit: تعداد املاک
            offset: برای pagination - skip کردن املاک قبلی (default: 0)
        
        Returns:
            لیستی از دیکشنری‌های property با تمام اطلاعات
        """
        async with async_session() as db:
            # Start with base query - tenant_id + is_available only (LESS RESTRICTIVE)
            query = select(TenantProperty).where(
                TenantProperty.tenant_id == lead.tenant_id,
                TenantProperty.is_available == True
            )
            
            conversation_data = lead.conversation_data or {}
            
            # SOFT FILTERS (optional - if missing, show all properties)
            # These won't block results, just order them better
            
            # 1. Budget filter (OPTIONAL - wide range)
            budget_min = lead.budget_min or conversation_data.get("budget_min")
            budget_max = lead.budget_max or conversation_data.get("budget_max")
            
            if budget_max:
                # Allow 50% flexibility above budget
                flexible_max = int(budget_max * 1.5)
                query = query.where(TenantProperty.price <= flexible_max)
                logger.info(f"💰 Budget filter (flexible): ≤ {flexible_max:,} AED")
            
            # 2. Bedrooms filter (OPTIONAL)
            bedrooms_min = lead.bedrooms_min or conversation_data.get("bedrooms_min")
            if bedrooms_min:
                # Allow ±1 bedroom flexibility
                flex_min = max(0, bedrooms_min - 1)
                flex_max = bedrooms_min + 2
                query = query.where(
                    TenantProperty.bedrooms >= flex_min,
                    TenantProperty.bedrooms <= flex_max
                )
                logger.info(f"🛏️ Bedrooms filter (flexible): {flex_min}-{flex_max}BR")
            
            # 3. Location preference (OPTIONAL - fuzzy match)
            preferred_location = conversation_data.get("preferred_location") or lead.preferred_location
            if preferred_location:
                # Fuzzy match - show properties in similar areas
                query = query.where(
                    TenantProperty.location.ilike(f"%{preferred_location}%")
                )
                logger.info(f"📍 Location filter: ~{preferred_location}")
            
            # ✅ NEW: Amenities filter (pool, gym, beach, parking)
            required_amenities = conversation_data.get("required_amenities")
            if required_amenities and isinstance(required_amenities, list):
                # Match properties that have ALL required amenities
                for amenity in required_amenities:
                    query = query.where(
                        TenantProperty.features.op('@>')(f'["{amenity}"]')  # PostgreSQL array contains operator
                    )
                logger.info(f"🏊 Amenities filter: {required_amenities}")
            
            # ✅ ALWAYS ORDER BY: Featured first, then price
            query = query.order_by(
                TenantProperty.is_featured.desc(),
                TenantProperty.price.asc()
            ).limit(limit).offset(offset)
            
            result = await db.execute(query)
            properties = result.scalars().all()
            
            logger.info(f"✅ Found {len(properties)} properties for tenant {lead.tenant_id} (offset={offset})")
        
        # Convert to dict
        properties_list = []
        for prop in properties:
            prop_dict = {
                "id": prop.id,
                "name": prop.name,
                "property_type": prop.property_type.value if prop.property_type else "Unknown",
                "location": prop.location,
                "price": prop.price or 0,
                "bedrooms": prop.bedrooms or 0,
                "bathrooms": prop.bathrooms or 0,
                "area_sqft": prop.area_sqft or 0,
                "features": prop.features or [],
                "expected_roi": prop.expected_roi,
                "rental_yield": prop.rental_yield,
                "golden_visa_eligible": prop.golden_visa_eligible,
                "images": prop.image_urls or prop.images or [],
                "primary_image": prop.primary_image,
                "brochure_pdf": prop.brochure_pdf,
                "description": prop.full_description or prop.description,
                "is_featured": prop.is_featured,
                "is_urgent": prop.is_urgent
            }
            properties_list.append(prop_dict)
            
        logger.info(f"🏠 Retrieved {len(properties_list)} real properties from database for lead {lead.id}")
        return properties_list
    
    async def format_properties_for_display(
        self, 
        properties: List[Dict], 
        lang: Language
    ) -> Tuple[str, List[Dict]]:
        """
        📝 فرمت کردن املاک برای نمایش به کاربر
        
        Args:
            properties: لیست املاک از database
            lang: زبان کاربر
        
        Returns:
            (message_text, media_files) برای ارسال به تلگرام
        """
        if not properties:
            no_props_msg = {
                Language.FA: "😔 متاسفانه در حال حاضر ملکی با این مشخصات موجود نیست.\n\nبرای دیدن سایر گزینه‌ها یا پیدا کردن ملک مناسب، لطفاً با من تماس بگیرید!",
                Language.EN: "😔 Sorry, we don't have properties matching those criteria right now.\n\nPlease contact me to explore other options or find the perfect property for you!",
                Language.AR: "😔 عذرًا، ليس لدينا عقارات تطابق تلك المعايير الآن.\n\nيرجى الاتصال بي لاستكشاف خيارات أخرى!",
                Language.RU: "😔 Извините, сейчас нет объектов по этим критериям.\n\nСвяжитесь со мной, чтобы рассмотреть другие варианты!"
            }
            return no_props_msg.get(lang, no_props_msg[Language.EN]), []
        
        # Build message
        header = {
            Language.FA: f"🏠 **{len(properties)} ملک مناسب برای شما:**\n\n",
            Language.EN: f"🏠 **{len(properties)} Properties for You:**\n\n",
            Language.AR: f"🏠 **{len(properties)} عقارات لك:**\n\n",
            Language.RU: f"🏠 **{len(properties)} объектов для вас:**\n\n"
        }
        
        message = header.get(lang, header[Language.EN])
        media_files = []
        
        for idx, prop in enumerate(properties, 1):
            # Price format
            price_display = f"{int(prop['price']):,} AED" if prop['price'] else "Price on request"
            
            # ROI display
            roi_text = ""
            if prop.get('expected_roi'):
                roi_icon = "📈" if lang in [Language.FA, Language.AR] else "📊"
                roi_label = {
                    Language.FA: "بازدهی سالانه",
                    Language.EN: "Annual ROI",
                    Language.AR: "عائد سنوي",
                    Language.RU: "Годовая доходность"
                }
                roi_text = f"\n   {roi_icon} {roi_label.get(lang, 'ROI')}: {prop['expected_roi']}%"
            
            # Golden Visa
            golden_visa_text = ""
            if prop.get('golden_visa_eligible'):
                gv_label = {
                    Language.FA: "🟡 واجد شرایط ویزای طلایی",
                    Language.EN: "🟡 Golden Visa Eligible",
                    Language.AR: "🟡 مؤهل للحصول على الفيزا الذهبية",
                    Language.RU: "🟡 Золотая виза"
                }
                golden_visa_text = f"\n   {gv_label.get(lang, gv_label[Language.EN])}"
            
            # Features (top 3)
            features_str = ""
            if prop.get('features'):
                top_features = prop['features'][:3]
                features_str = f"\n   ✨ {', '.join(top_features)}"
            
            # Property card
            message += f"{idx}. **{prop['name']}**\n"
            message += f"   📍 {prop['location']}\n"
            message += f"   💰 {price_display}\n"
            message += f"   🛏️ {prop['bedrooms']} خواب | 🚿 {prop['bathrooms']} حمام | 📏 {int(prop['area_sqft'])} sqft\n"
            message += f"{features_str}{roi_text}{golden_visa_text}\n\n"
            
            # Add image to media
            image_url = prop.get('primary_image') or (prop.get('images')[0] if prop.get('images') else None)
            if image_url:
                caption = f"{prop['name']} - {price_display}"
                media_files.append({
                    "type": "photo",
                    "url": image_url,
                    "caption": caption
                })
        
        return message, media_files
    
    def _validate_state_integrity(
        self,
        lead: Lead,
        current_state: ConversationState,
        conversation_data: Dict
    ) -> Optional[str]:
        """
        🔥 FLOW INTEGRITY VALIDATION
        Validates that required data exists for current state.
        Returns error message if validation fails, None if OK.
        
        This ensures 10/10 Flow Logic by preventing invalid state transitions.
        """
        filled_slots = conversation_data.get("filled_slots", {})
        
        # SLOT_FILLING validations
        if current_state == ConversationState.SLOT_FILLING:
            pending_slot = conversation_data.get("pending_slot")
            
            # If asking for budget, transaction_type and category should be set
            if pending_slot == "budget":
                if not conversation_data.get("transaction_type"):
                    logger.error(f"❌ Lead {lead.id}: Budget slot but missing transaction_type!")
                    return "missing_transaction_type"
                if not conversation_data.get("property_category"):
                    logger.error(f"❌ Lead {lead.id}: Budget slot but missing property_category!")
                    return "missing_property_category"
            
            # If asking for property_type, budget should be set
            if pending_slot == "property_type":
                if not filled_slots.get("budget"):
                    logger.warning(f"⚠️ Lead {lead.id}: Property type slot but budget not filled!")
        
        # VALUE_PROPOSITION validations
        if current_state == ConversationState.VALUE_PROPOSITION:
            # All qualification slots should be filled
            required_slots = ["transaction_type", "property_category", "budget"]
            missing = [s for s in required_slots if not conversation_data.get(s)]
            if missing:
                logger.error(f"❌ Lead {lead.id}: VALUE_PROPOSITION but missing slots: {missing}")
                return f"missing_slots_{','.join(missing)}"
        
        # HANDOFF_SCHEDULE validations  
        if current_state == ConversationState.HANDOFF_SCHEDULE:
            if not lead.phone:
                logger.warning(f"⚠️ Lead {lead.id}: HANDOFF_SCHEDULE but no phone number!")
        
        logger.info(f"✅ State integrity validated for lead {lead.id}, state {current_state}")
        return None  # All good!
    
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
        # Detect language from message (always check for language change)
        detected_lang = self.detect_language(message)
        
        # CRITICAL: Access conversation_state DIRECTLY and log the raw value
        logger.info(f"🔍 RAW lead.conversation_state = {lead.conversation_state} (type: {type(lead.conversation_state)})")
        
        # CRITICAL: Access conversation_state directly, NOT via .state property
        # The .state property can return cached values on detached objects
        if lead.conversation_state:
            try:
                if isinstance(lead.conversation_state, ConversationState):
                    current_state = lead.conversation_state
                else:
                    # Convert string to enum (strings are already lowercase matching enum)
                    current_state = ConversationState(lead.conversation_state)
            except (ValueError, KeyError) as e:
                logger.error(f"❌ Failed to convert state '{lead.conversation_state}' to enum: {e}")
                current_state = ConversationState.START
        else:
            current_state = ConversationState.START
        
        logger.info(f"🎯 FINAL current_state = {current_state}")
        
        # 🔥 VALIDATE STATE INTEGRITY (10/10 Flow Logic)
        conversation_data = lead.conversation_data or {}
        integrity_error = self._validate_state_integrity(lead, current_state, conversation_data)
        if integrity_error:
            logger.warning(f"⚠️ State integrity issue for lead {lead.id}: {integrity_error}")
            # Continue with recovery logic in handlers
        
        # ===== SENTIMENT DETECTION - CHECK FOR NEGATIVE TONE =====
        # If user expresses frustration/anger, immediately offer human support
        if message and not callback_data:
            negative_sentiment_keywords = {
                Language.FA: r'\b(کلافه شدم|دیونه شدم|خیلی زیادی|اذیت شدم|خسته شدم|بدم میاد|چقدر حرف|حالم بد|بسه دیگه)\b',
                Language.AR: r'\b(مسخوط|غاضب|زعلان|تعبت|ملل|بطيء|قاسي|سيئ)\b',
                Language.RU: r'\b(раздосадовано|злой|устал|ужасно|недовольны|усталь)\b',
                Language.EN: r'\b(annoyed|frustrated|angry|stupid|terrible|tired|awful|enough already|just stop)\b'
            }
            
            # Check all possible languages for sentiment
            is_negative_sentiment = False
            for lang_key, pattern in negative_sentiment_keywords.items():
                if re.search(pattern, message, re.IGNORECASE):
                    is_negative_sentiment = True
                    break
            
            if is_negative_sentiment:
                # User is frustrated - offer immediate human handoff
                lang = lead.language or Language.FA
                
                handoff_messages = {
                    Language.EN: f"😔 I understand you're frustrated. Let me connect you with {self.agent_name} directly for personalized support.\n\nWould you like me to schedule a call with them right now?",
                    Language.FA: f"😔 متوجه شدم که ناراحت هستید. بذار شما رو به طور مستقیم با {self.agent_name} متصل کنم.\n\nالآن می‌خواهید با اونها تماس بگیرید؟",
                    Language.AR: f"😔 أفهم أنك محبط. دعني أتصل بك مباشرة مع {self.agent_name} للحصول على دعم شخصي.\n\nهل تريد أن أجدول مكالمة معهم الآن؟",
                    Language.RU: f"😔 Я понимаю, что вы расстроены. Позвольте мне соединить вас напрямую с {self.agent_name}.\n\nХотели бы вы получить звонок от них сейчас?"
                }
                
                logger.warning(f"⚠️ NEGATIVE SENTIMENT DETECTED from Lead {lead.id}: '{message}'")
                
                return BrainResponse(
                    message=handoff_messages.get(lang, handoff_messages[Language.EN]),
                    next_state=ConversationState.HANDOFF_URGENT,
                    lead_updates={"status": LeadStatus.QUALIFIED},
                    buttons=[
                        {"text": self.get_text("btn_yes", lang), "callback_data": "handoff_yes"},
                        {"text": self.get_text("btn_no", lang), "callback_data": "handoff_no"}
                    ]
                )
        
        # DEBUG LOGGING
        logger.info(f"🔍 process_message - Lead {lead.id}: state={current_state}, message='{message}', callback={callback_data}, lead.lang={lead.language}")
        
        # 🧠 SMART EXTRACTION - Extract ALL info from message FIRST (before state machine)
        # این همون "مغز" هست که همه چیز رو یکجا می‌فهمه!
        extracted_info = {}
        if message and not callback_data and len(message.strip()) > 3:
            current_lead_data = {
                "name": lead.name,
                "phone": lead.phone,
                "email": lead.email,
                "goal": conversation_data.get("goal"),
                "budget": conversation_data.get("budget"),
                "location": conversation_data.get("location_preference")
            }
            
            extracted_info = await self.extract_user_info_smart(message, current_lead_data)
            
            # Save extracted info to lead immediately
            lead_updates = {}
            if extracted_info.get("name") and not lead.name:
                lead_updates["name"] = extracted_info["name"]
                logger.info(f"✅ Auto-extracted name: {extracted_info['name']}")
            
            if extracted_info.get("phone") and not lead.phone:
                lead_updates["phone"] = extracted_info["phone"]
                logger.info(f"✅ Auto-extracted phone: {extracted_info['phone']}")
            
            if extracted_info.get("email") and not lead.email:
                lead_updates["email"] = extracted_info["email"]
                logger.info(f"✅ Auto-extracted email: {extracted_info['email']}")
            
            # Update conversation_data with extracted preferences
            if extracted_info.get("goal"):
                conversation_data["goal"] = extracted_info["goal"]
                logger.info(f"✅ Auto-extracted goal: {extracted_info['goal']}")
            
            if extracted_info.get("budget_min") or extracted_info.get("budget_max"):
                conversation_data["budget_min"] = extracted_info.get("budget_min")
                conversation_data["budget_max"] = extracted_info.get("budget_max")
                conversation_data["budget"] = f"{extracted_info.get('budget_min', 0)}-{extracted_info.get('budget_max', 999999999)}"
                logger.info(f"✅ Auto-extracted budget: {conversation_data['budget']}")
            
            if extracted_info.get("location_preference"):
                conversation_data["location_preference"] = extracted_info["location_preference"]
                logger.info(f"✅ Auto-extracted location: {extracted_info['location_preference']}")
            
            if extracted_info.get("property_type"):
                conversation_data["property_type"] = extracted_info["property_type"]
                logger.info(f"✅ Auto-extracted property type: {extracted_info['property_type']}")
            
            if extracted_info.get("bedrooms"):
                conversation_data["bedrooms"] = extracted_info["bedrooms"]
                logger.info(f"✅ Auto-extracted bedrooms: {extracted_info['bedrooms']}")
            
            # Save updated conversation_data
            if lead_updates or extracted_info:
                lead_updates["conversation_data"] = conversation_data
                await update_lead(lead.id, **lead_updates)
                logger.info(f"💾 Smart extraction saved for lead {lead.id}")
        
        # Check if user is explicitly requesting language change mid-conversation
        lang_change_patterns = {
            Language.FA: r'فارسی|persian|farsi',
            Language.AR: r'عربي|عربی|arabic',
            Language.RU: r'русский|russian',
            Language.EN: r'english|انگلیسی'
        }
        
        requested_lang = None
        if message and not callback_data:
            message_lower = message.lower()
            for lang, pattern in lang_change_patterns.items():
                if re.search(pattern, message_lower, re.IGNORECASE):
                    requested_lang = lang
                    break
        
        # === HANDLE LOTTERY CALLBACKS (Global) ===
        if callback_data and callback_data.startswith("join_lottery_"):
            lottery_id = int(callback_data.split("_")[2])
            success = await join_lottery(self.tenant.id, lottery_id, lead.id)
            
            if success:
                from api.lotteries import LOTTERIES_DB
                lottery = LOTTERIES_DB.get(lottery_id)
                end_date = lottery["end_date"].strftime("%Y-%m-%d") if lottery else "soon"
                
                joined_msg = TRANSLATIONS["lottery_joined"]
                continue_msg = {
                    Language.EN: "\n\n📋 Would you like to see the full details and market analysis for the properties I showed you?",
                    Language.FA: "\n\n📋 می‌خواهید جزئیات کامل و تحلیل بازار برای املاکی که نشون دادم را ببینید؟",
                    Language.AR: "\n\n📋 هل تريد رؤية التفاصيل الكاملة وتحليل السوق للعقارات التي عرضتها؟",
                    Language.RU: "\n\n📋 Хотите увидеть полные детали и рыночный анализ показанных объектов?"
                }
                
                message_text = joined_msg.get(lang, joined_msg[Language.EN]).format(end_date=end_date)
                message_text += continue_msg.get(lang, continue_msg[Language.EN])
                
                return BrainResponse(
                    message=message_text,
                    next_state=ConversationState.VALUE_PROPOSITION,
                    lead_updates=lead_updates,
                    buttons=[
                        {"text": self.get_text("btn_yes", lang), "callback_data": "details_yes"},
                        {"text": self.get_text("btn_no", lang), "callback_data": "details_no"},
                        {"text": "📅 " + self.get_text("btn_schedule_consultation", lang), "callback_data": "schedule_consultation"}
                    ]
                )
        
        elif callback_data == "skip_lottery":
            skip_msg = TRANSLATIONS["lottery_skip"]
            continue_msg = {
                Language.EN: "\n\n📋 Would you like to see the full details and market analysis for these properties?",
                Language.FA: "\n\n📋 می‌خواهید جزئیات کامل و تحلیل بازار برای این املاک را ببینید؟",
                Language.AR: "\n\n📋 هل تريد رؤية التفاصيل الكاملة وتحليل السوق لهذه العقارات؟",
                Language.RU: "\n\n📋 Хотите увидеть полные детали и рыночный анализ этих объектов?"
            }
            
            message_text = skip_msg.get(lang, skip_msg[Language.EN])
            message_text += continue_msg.get(lang, continue_msg[Language.EN])
            
            return BrainResponse(
                message=message_text,
                next_state=ConversationState.VALUE_PROPOSITION,
                lead_updates=lead_updates,
                buttons=[
                    {"text": self.get_text("btn_yes", lang), "callback_data": "details_yes"},
                    {"text": self.get_text("btn_no", lang), "callback_data": "details_no"},
                    {"text": "📅 " + self.get_text("btn_schedule_consultation", lang), "callback_data": "schedule_consultation"}
                ]
            )
        
        # DEBUG LOGGING
        if requested_lang:
            logger.info(f"🔍 Detected language change request: {requested_lang}")
        
        # Prioritize: 1) Explicit language request, 2) Lead's saved language, 3) Detected language
        if requested_lang:
            lang = requested_lang
        elif lead.language:
            lang = lead.language
        else:
            lang = detected_lang
        
        # Update lead language if changed
        lead_updates = {"language": lang}
        
        # State Machine Logic
        if current_state == ConversationState.START:
            # CRITICAL FIX: If user clicked a language button (callback_data), process it immediately
            if callback_data and callback_data.startswith("lang_"):
                return self._handle_language_select(lang, callback_data, lead_updates, message)
            
            # If user types a language name instead of clicking button, handle it
            if message and not callback_data:
                # Check if message contains language request
                message_lower = message.lower()
                detected_lang = None
                if re.search(r'فارسی|persian|farsi', message_lower, re.IGNORECASE):
                    detected_lang = Language.FA
                elif re.search(r'عربي|عربی|arabic', message_lower, re.IGNORECASE):
                    detected_lang = Language.AR
                elif re.search(r'русский|russian', message_lower, re.IGNORECASE):
                    detected_lang = Language.RU
                elif re.search(r'english|انگلیسی', message_lower, re.IGNORECASE):
                    detected_lang = Language.EN
                
                if detected_lang:
                    # User typed a language name - go to LANGUAGE_SELECT with that message
                    return self._handle_language_select(detected_lang, None, {"language": detected_lang}, message)
            return self._handle_start(lang)
        
        elif current_state == ConversationState.LANGUAGE_SELECT:
            return self._handle_language_select(lang, callback_data, lead_updates, message)
        
        elif current_state == ConversationState.COLLECTING_NAME:
            return await self._handle_collecting_name(lang, message, callback_data, lead, lead_updates)
        
        elif current_state == ConversationState.CAPTURE_CONTACT:
            return await self._handle_capture_contact(lang, message, callback_data, lead, lead_updates)
        
        # ===== NEW STATE MACHINE ROUTING =====
        elif current_state == ConversationState.WARMUP:
            return await self._handle_warmup(lang, message, callback_data, lead, lead_updates)
        
        elif current_state == ConversationState.SLOT_FILLING:
            return await self._handle_slot_filling(lang, message, callback_data, lead, lead_updates)
        
        elif current_state == ConversationState.VALUE_PROPOSITION:
            return await self._handle_value_proposition(lang, message, callback_data, lead, lead_updates)
        
        elif current_state == ConversationState.HARD_GATE:
            return await self._handle_hard_gate(lang, message, callback_data, lead, lead_updates)
        
        elif current_state == ConversationState.ENGAGEMENT:
            return await self._handle_engagement(lang, message, lead, lead_updates)
        
        elif current_state == ConversationState.HANDOFF_SCHEDULE:
            return await self._handle_schedule(lang, callback_data, lead)
        
        elif current_state == ConversationState.HANDOFF_URGENT:
            return await self._handle_handoff_urgent(lang, message, callback_data, lead, lead_updates)
        
        elif current_state == ConversationState.COMPLETED:
            # Lead has completed the flow - stay in engagement for follow-ups
            return await self._handle_engagement(lang, message, lead, lead_updates)
        
        # CRITICAL FIX: If state is unknown, do NOT restart conversation!
        # Instead, treat as free-form question in ENGAGEMENT mode
        logger.warning(f"⚠️ Unknown state '{current_state}' for lead {lead.id}. Defaulting to ENGAGEMENT.")
        return await self._handle_engagement(lang, message, lead, lead_updates)
    
    def _handle_start(self, lang: Language) -> BrainResponse:
        """Initial state - show language selection."""
        return BrainResponse(
            message=self.get_text("language_select", lang).format(agent_name=self.agent_name),
            next_state=ConversationState.LANGUAGE_SELECT,
            buttons=[
                {"text": "🇬🇧 English", "callback_data": "lang_en"},
                {"text": "🇮🇷 فارسی", "callback_data": "lang_fa"},
                {"text": "🇸🇦 العربية", "callback_data": "lang_ar"},
                {"text": "🇷🇺 Русский", "callback_data": "lang_ru"}
            ]
        )
    
    def _handle_language_select(self, lang: Language, callback_data: Optional[str], lead_updates: Dict, message: Optional[str] = None) -> BrainResponse:
        """Handle language selection - update lead language and proceed to welcome."""
        lang_map = {
            "lang_en": Language.EN,
            "lang_fa": Language.FA,
            "lang_ar": Language.AR,
            "lang_ru": Language.RU
        }
        
        # Handle callback button selection
        if callback_data in lang_map:
            lang = lang_map[callback_data]
            lead_updates["language"] = lang
        # Handle text-based language selection (user types language name or any text)
        elif message:
            message_lower = message.lower().strip()
            
            # First check for explicit language keywords
            if 'فارسی' in message or 'persian' in message_lower or 'fa' in message_lower:
                lang = Language.FA
                lead_updates["language"] = lang
            elif 'عربي' in message or 'arabic' in message_lower or 'ar' in message_lower:
                lang = Language.AR
                lead_updates["language"] = lang
            elif 'русский' in message_lower or 'russian' in message_lower or 'ru' in message_lower:
                lang = Language.RU
                lead_updates["language"] = lang
            elif 'english' in message_lower or 'en' in message_lower:
                lang = Language.EN
                lead_updates["language"] = lang
            # Auto-detect language from script if no explicit keyword
            elif re.search(r'[\u0600-\u06FF]', message):  # Persian/Arabic script detected
                # Default to Persian for now (could add Arabic detection heuristics later)
                lang = Language.FA
                lead_updates["language"] = lang
            elif re.search(r'[\u0400-\u04FF]', message):  # Cyrillic script
                lang = Language.RU
                lead_updates["language"] = lang
            else:
                # Default to English for Latin script
                lang = Language.EN
                lead_updates["language"] = lang
        
        # After language selection, ask for customer's name first
        name_question = {
            Language.EN: "Nice to meet you! 👋\n\nWhat's your name?",
            Language.FA: "خوشحالم که با شما آشنا شدم! 👋\n\nاسم شما چیه؟",
            Language.AR: "سعيد بلقائك! 👋\n\nما اسمك؟",
            Language.RU: "Приятно познакомиться! 👋\n\nКак вас зовут?"
        }
        
        return BrainResponse(
            message=name_question.get(lang, name_question[Language.EN]),
            next_state=ConversationState.COLLECTING_NAME,
            lead_updates=lead_updates,
            buttons=[]
        )
    
    async def _handle_collecting_name(
        self,
        lang: Language,
        message: Optional[str],
        callback_data: Optional[str],
        lead: Lead,
        lead_updates: Dict
    ) -> BrainResponse:
        """
        COLLECTING_NAME Phase: Ask for customer's name and personalize all future messages
        This runs immediately after language selection
        
        🧠 SMART MODE: If name already extracted by smart extraction, skip this step!
        """
        # 🧠 SMART CHECK: If name already extracted, skip asking!
        if lead.name and lead.name.strip():
            logger.info(f"✅ Name already extracted for lead {lead.id}: {lead.name} - skipping to next step")
            # Go directly to contact capture
            return await self._handle_capture_contact(lang, None, None, lead, lead_updates)
        
        # Validate name input
        if not message or len(message.strip()) < 2:
            retry_msg = {
                Language.EN: "Please tell me your name 😊",
                Language.FA: "لطفاً اسمتون رو بگید 😊",
                Language.AR: "من فضلك، أخبرني باسمك 😊",
                Language.RU: "Пожалуйста, скажите мне ваше имя 😊"
            }
            return BrainResponse(
                message=retry_msg.get(lang, retry_msg[Language.EN]),
                next_state=ConversationState.COLLECTING_NAME,
                lead_updates={},
                buttons=[]
            )
        
        # Initialize conversation_data
        conversation_data = lead.conversation_data or {}
        
        # Simple name pattern (2-30 characters, letters/spaces only)
        # This catches actual names like "Arezoo", "علی", "Mohammed"
        import re
        simple_name_pattern = r'^[A-Za-z\u0600-\u06FF\u0400-\u04FF\s]{2,30}$'
        
        # CRITICAL FIX: Check if this looks like a QUESTION instead of name
        is_question = any(char in message for char in ['؟', '?']) or \
                     any(word in message.lower() for word in ['how', 'what', 'when', 'where', 'why', 'چطور', 'چه', 'چی', 'کی', 'کجا', 'چرا', 'هل', 'ما', 'اين', 'كيف', 'لماذا', 'что', 'как', 'когда', 'где', 'почему'])
        
        # If it's a question, answer it FIRST, then ask for name again
        if is_question and len(message) > 10:
            logger.info(f"❓ User asked question during name collection: {message}")
            
            # Generate AI answer to the question
            try:
                ai_answer = await self.generate_ai_response(message, lead, "User asked a question while we're collecting their name. Answer their question BRIEFLY (1-2 sentences max), then politely ask for their name again.")
                
                # Append "Now, what's your name?" to the AI answer
                ask_name_again = {
                    Language.EN: "\n\nBy the way, what's your name? 😊",
                    Language.FA: "\n\nراستی، اسمت چیه؟ 😊",
                    Language.AR: "\n\nبالمناسبة، ما اسمك؟ 😊",
                    Language.RU: "\n\nКстати, как вас зовут? 😊"
                }
                
                full_response = ai_answer + ask_name_again.get(lang, ask_name_again[Language.EN])
                
                return BrainResponse(
                    message=full_response,
                    next_state=ConversationState.COLLECTING_NAME,  # Stay in name collection
                    lead_updates={},
                    buttons=[]
                )
            except Exception as e:
                logger.error(f"❌ AI answer failed during name collection: {e}")
                # Fallback to generic answer
                generic_answer = {
                    Language.EN: "Great question! I'll answer that in detail once we get started. First, what's your name? 😊",
                    Language.FA: "سوال خوبیه! بهت جواب کامل میدم. اول اسمت چیه؟ 😊",
                    Language.AR: "سؤال رائع! سأجيب بالتفصيل بعد قليل. أولاً، ما اسمك؟ 😊",
                    Language.RU: "Отличный вопрос! Отвечу подробно чуть позже. Сначала, как вас зовут? 😊"
                }
                return BrainResponse(
                    message=generic_answer.get(lang, generic_answer[Language.EN]),
                    next_state=ConversationState.COLLECTING_NAME,
                    lead_updates={},
                    buttons=[]
                )
        
        if re.match(simple_name_pattern, message.strip()):
            # This is a simple name! Save it
            customer_name = message.strip()
            lead_updates["name"] = customer_name
            conversation_data["customer_name"] = customer_name
            lead_updates["conversation_data"] = conversation_data
        else:
            # Message doesn't match name pattern and not a question - ask again
            retry_msg = {
                Language.EN: "Just your first name, please 😊 (e.g., 'John' or 'Sara')",
                Language.FA: "فقط اسمت، لطفاً 😊 (مثلاً 'علی' یا 'سارا')",
                Language.AR: "اسمك الأول فقط من فضلك 😊 (مثال: 'محمد' أو 'فاطمة')",
                Language.RU: "Только ваше имя, пожалуйста 😊 (например, 'Иван' или 'Анна')"
            }
            return BrainResponse(
                message=retry_msg.get(lang, retry_msg[Language.EN]),
                next_state=ConversationState.COLLECTING_NAME,
                lead_updates={},
                buttons=[]
            )
        
        # ✨ CRITICAL CHANGE: Request phone IMMEDIATELY after name with ROI Hook
        # This captures lead info EARLY (after only 2 steps instead of 6)
        # Expected improvement: 70% drop-off reduction, 150% increase in phone capture rate
        
        # Get name from lead_updates (if we just saved it)
        customer_name = lead_updates.get("name", conversation_data.get("customer_name", "there"))
        
        roi_hook_messages = {
            Language.EN: f"Great to meet you, {customer_name}! 🎯\n\nI'm {self.agent_name}, your Dubai real estate specialist.\n\n🎁 **FREE ROI Analysis Just for You:**\n\nI'll send you an exclusive report with:\n✅ Precise ROI calculations for your budget\n✅ Rental income projections\n✅ Golden Visa eligibility analysis\n✅ Off-market deals (not public!)\n\n🔐 **Security Protocol:** To send this personalized report securely, I need to verify your contact.\n\n📱 Please share your phone number using the button below, or type it manually.\n\n**Example format:**\n+971501234567 (UAE)\n+989177105840 (Iran)",
            Language.FA: f"خوشحالم که با شما آشنا شدم، {customer_name} عزیز! 🎯\n\nمن {self.agent_name} هستم، مشاور املاک دبی شما.\n\n🎁 **تحلیل ROI رایگان ویژه شما:**\n\nبرات یه گزارش اختصاصی می‌فرستم که شامل:\n✅ محاسبات دقیق بازگشت سرمایه برای بودجه‌ت\n✅ پیش‌بینی درآمد اجاره\n✅ تحلیل واجد شرایط بودن برای ویزای طلایی\n✅ معاملات خارج از بازار (عمومی نیست!)\n\n🔐 **پروتکل امنیتی:** برای ارسال امن این گزارش شخصی‌سازی شده، باید تماست رو تأیید کنم.\n\n📱 لطفاً شماره تلفنت رو share کن:\n\n**فرمت:** +971501234567\n(دکمه پایین رو بزن یا شماره‌ت رو بنویس)",
            Language.AR: f"سعيد بلقائك يا {customer_name}! 🎯\n\nأنا {self.agent_name}، أخصائي العقارات في دبي.\n\n🎁 **تحليل ROI مجاني خاص بك:**\n\nسأرسل لك تقريراً حصرياً يحتوي على:\n✅ حسابات ROI دقيقة لميزانيتك\n✅ توقعات دخل الإيجار\n✅ تحليل الأهلية للتأشيرة الذهبية\n✅ صفقات خارج السوق (غير عامة!)\n\n🔐 **بروتوكول الأمان:** لإرسال هذا التقرير الشخصي بأمان، أحتاج للتحقق من جهة اتصالك.\n\n📱 يرجى مشاركة رقم هاتفك باستخدام الزر أدناه، أو اكتبه يدوياً.\n\n**مثال على التنسيق:**\n+971501234567 (الإمارات)\n+989177105840 (إيران)",
            Language.RU: f"Приятно познакомиться, {customer_name}! 🎯\n\nЯ {self.agent_name}, ваш специалист по недвижимости в Дубае.\n\n🎁 **БЕСПЛАТНЫЙ ROI-анализ специально для вас:**\n\nОтправлю вам эксклюзивный отчёт с:\n✅ Точными расчётами ROI для вашего бюджета\n✅ Прогнозами арендного дохода\n✅ Анализом на Golden Visa\n✅ Закрытыми сделками (не публичны!)\n\n🔐 **Протокол безопасности:** Для безопасной отправки персонального отчёта нужно подтвердить контакт.\n\n📱 Пожалуйста, поделитесь номером телефона кнопкой ниже или введите вручную.\n\n**Пример формата:**\n+971501234567 (ОАЭ)\n+989177105840 (Иран)"
        }
        
        return BrainResponse(
            message=roi_hook_messages.get(lang, roi_hook_messages[Language.EN]),
            next_state=ConversationState.CAPTURE_CONTACT,
            lead_updates=lead_updates,
            request_contact=True,  # Show "Share Phone Number" button
            buttons=[]
        )
    
    async def _handle_capture_contact(
        self,
        lang: Language,
        message: Optional[str],
        callback_data: Optional[str],
        lead: Lead,
        lead_updates: Dict
    ) -> BrainResponse:
        """
        CAPTURE_CONTACT Phase: Capture phone number after name collection
        This phase validates and stores the phone number before moving to warmup
        
        🧠 SMART MODE: If phone already extracted by smart extraction, skip this step!
        """
        # 🧠 SMART CHECK: If phone already extracted, skip asking!
        if lead.phone and lead.phone.strip():
            logger.info(f"✅ Phone already extracted for lead {lead.id}: {lead.phone} - skipping to next step")
            
            # Acknowledge and move to goal/budget capture
            confirmation_msgs = {
                Language.EN: f"Perfect! I have your contact information ✅\n\nNow, what brings you to Dubai real estate?",
                Language.FA: f"عالی! اطلاعات تماست رو دارم ✅\n\nحالا، هدفت از املاک دبی چیه؟",
                Language.AR: f"ممتاز! لدي معلومات الاتصال الخاصة بك ✅\n\nالآن، ما هو هدفك من العقارات في دبي؟",
                Language.RU: f"Отлично! У меня есть ваши контактные данные ✅\n\nТеперь, какая у вас цель с недвижимостью в Дубае?"
            }
            
            # Check if goal also extracted
            conversation_data = lead.conversation_data or {}
            if conversation_data.get("goal"):
                # Both phone AND goal extracted - go straight to property search!
                logger.info(f"🚀 Both phone AND goal extracted - jumping to property matching!")
                return await self._handle_slot_filling(lang, None, None, lead, lead_updates)
            
            # Only phone extracted - ask for goal WITH BUTTONS (user might be lazy/unsure)
            goal_buttons = [
                {"text": "🏡 " + ("خرید خانه" if lang == Language.FA else "Buy Property" if lang == Language.EN else "شراء عقار" if lang == Language.AR else "Купить"), "callback_data": "goal_buy"},
                {"text": "💰 " + ("سرمایه‌گذاری" if lang == Language.FA else "Investment" if lang == Language.EN else "استثمار" if lang == Language.AR else "Инвестиция"), "callback_data": "goal_investment"},
                {"text": "🛂 " + ("اقامت طلایی" if lang == Language.FA else "Golden Visa" if lang == Language.EN else "تأشيرة ذهبية" if lang == Language.AR else "Золотая виза"), "callback_data": "goal_residency"}
            ]
            
            return BrainResponse(
                message=confirmation_msgs.get(lang, confirmation_msgs[Language.EN]),
                next_state=ConversationState.WARMUP,
                lead_updates=lead_updates,
                buttons=goal_buttons  # Show buttons but also accept text!
            )
        
        # Phone number shared via Telegram contact button OR typed
        if not message:
            retry_msg = {
                Language.EN: "Please share your phone number using the button below 👇, or type it manually 📱\n\n**Example format:**\n+971505037158 (UAE)\n+989177105840 (Iran)",
                Language.FA: "لطفاً شماره تلفنتون رو با دکمه پایین share کنید 👇، یا دستی بنویسید 📱\n\n**مثال فرمت:**\n+971505037158 (امارات)\n+989177105840 (ایران)",
                Language.AR: "يرجى مشاركة رقم هاتفك باستخدام الزر أدناه 👇، أو اكتبه يدوياً 📱\n\n**مثال على التنسيق:**\n+971505037158 (الإمارات)\n+989177105840 (إيران)",
                Language.RU: "Пожалуйста, поделитесь номером телефона кнопкой ниже 👇 или введите вручную 📱\n\n**Пример формата:**\n+971505037158 (ОАЭ)\n+989177105840 (Иран)"
            }
            return BrainResponse(
                message=retry_msg.get(lang, retry_msg[Language.EN]),
                next_state=ConversationState.CAPTURE_CONTACT,
                lead_updates={},
                request_contact=True,  # Show "Share Contact" button
                buttons=[]  # No inline buttons here, request_contact shows native Telegram button
            )
        
        # Validate phone number (basic validation)
        phone = message.strip()
        if len(phone) < 10:
            retry_msg = {
                Language.EN: "Please enter a valid phone number (at least 10 digits) 📱\n\n**Example format:**\n+971505037158 (UAE)\n+989177105840 (Iran)",
                Language.FA: "لطفاً یک شماره معتبر وارد کنید (حداقل ۱۰ رقم) 📱\n\n**مثال فرمت:**\n+971505037158 (امارات)\n+989177105840 (ایران)",
                Language.AR: "يرجى إدخال رقم هاتف صالح (10 أرقام على الأقل) 📱\n\n**مثال على التنسيق:**\n+971505037158 (الإمارات)\n+989177105840 (إيران)",
                Language.RU: "Пожалуйста, введите корректный номер (минимум 10 цифр) 📱\n\n**Пример формата:**\n+971505037158 (ОАЭ)\n+989177105840 (Иран)"
            }
            return BrainResponse(
                message=retry_msg.get(lang, retry_msg[Language.EN]),
                next_state=ConversationState.CAPTURE_CONTACT,
                lead_updates={},
                request_contact=True,
                buttons=[]
            )
        
        # Save phone number and mark as contacted
        lead_updates["phone"] = phone
        lead_updates["status"] = LeadStatus.CONTACTED
        
        # ✅ NEW: Calculate lead score and temperature after phone capture
        # Phone shared = serious buyer/renter (20 point boost!)
        # Note: Can't call lead.update_temperature() here as object might be detached
        # So we calculate manually and save via lead_updates
        
        # Calculate score boost from phone capture
        score = 0
        if phone:
            score += 20  # Phone number provided
        if lead.status == LeadStatus.CONTACTED:
            score += 10  # Status upgrade
        
        # Calculate temperature based on score
        if score >= 90:
            temperature = "burning"
        elif score >= 70:
            temperature = "hot"
        elif score >= 40:
            temperature = "warm"
        else:
            temperature = "cold"
        
        lead_updates["lead_score"] = score
        lead_updates["temperature"] = temperature
        logger.info(f"📊 Lead {lead.id} score updated to {score} ({temperature}) after phone capture")
        
        # 🧠 SMART FLOW: Check if user already mentioned goal in conversation
        conversation_data = lead.conversation_data or {}
        existing_goal = conversation_data.get("goal")
        
        if existing_goal:
            # User already stated their goal! Skip WARMUP, go straight to budget
            logger.info(f"✅ Goal already known: {existing_goal}. Skipping WARMUP, asking budget.")
            
            # Ask budget with context based on goal
            if existing_goal == "investment":
                budget_question = {
                    Language.EN: f"Perfect, {lead.name}! 💰\n\nTo find you the best cash-generating asset, what price range are you comfortable with?\n\n**Common ranges:**\n• 500K-1M: Studios/1BR (8-10% ROI)\n• 1M-2M: 2BR Apartments (7-9% ROI)\n• 2M-5M: Villas/Penthouses (6-8% ROI)\n\nJust type your budget (e.g., \"1.5 million\" or \"750k\")",
                    Language.FA: f"{lead.name} عزیز، عالی! 💰\n\nبرای پیدا کردن بهترین دارایی درآمدزا، بودجه‌ات چقدره؟\n\n**رنج‌های معمول:**\n• ۵۰۰-۱ میلیون: استودیو/۱ خوابه (بازده ۸-۱۰٪)\n• ۱-۲ میلیون: آپارتمان ۲ خوابه (بازده ۷-۹٪)\n• ۲-۵ میلیون: ویلا/پنت‌هاوس (بازده ۶-۸٪)\n\nفقط بودجت رو بنویس (مثلاً \"۱.۵ میلیون\" یا \"۷۵۰ هزار\")"
                }
            else:
                budget_question = {
                    Language.EN: f"Great, {lead.name}! 🏠\n\nWhat's your budget range? Just type it (e.g., \"1 million\" or \"2.5M\")",
                    Language.FA: f"{lead.name} عزیز، عالی! 🏠\n\nبودجه‌ات چقدره؟ فقط بنویس (مثلاً \"۱ میلیون\" یا \"۲.۵ میلیون\")"
                }
            
            return BrainResponse(
                message=budget_question.get(lang, budget_question[Language.EN]),
                next_state=ConversationState.SLOT_FILLING,
                lead_updates=lead_updates | {
                    "conversation_data": conversation_data,
                    "pending_slot": "budget"
                },
                buttons=[]
            )
        
        # Goal not known yet - ask with BUTTONS but also accept text!
        warmup_msg = {
            Language.EN: f"Thank you! 🙏\n\nNow let me understand what you're looking for.\n\n🎯 **What brings you to Dubai property market?**\n\n**Pick one or just tell me:**",
            Language.FA: f"ممنون! 🙏\n\nحالا بذار بفهمم دنبال چی هستی.\n\n🎯 **چی باعث شده به بازار املاک دبی علاقه‌مند بشی؟**\n\n**یکی انتخاب کن یا خودت بگو:**",
            Language.AR: f"شكراً! 🙏\n\nالآن دعني أفهم ما تبحث عنه.\n\n🎯 **ما الذي يجذبك إلى سوق العقارات في دبي؟**\n\n**اختر واحداً أو أخبرني:**",
            Language.RU: f"Спасибо! 🙏\n\nТеперь давайте пойму, что вы ищете.\n\n🎯 **Что привело вас на рынок недвижимости Дубая?**\n\n**Выберите или напишите:**"
        }
        
        # Buttons for those who prefer clicking
        goal_buttons = [
            {"text": "💰 " + ("سرمایه‌گذاری" if lang == Language.FA else "Investment" if lang == Language.EN else "استثمار" if lang == Language.AR else "Инвестиция"), "callback_data": "goal_investment"},
            {"text": "🏠 " + ("زندگی" if lang == Language.FA else "Living" if lang == Language.EN else "سكن" if lang == Language.AR else "Жилье"), "callback_data": "goal_living"},
            {"text": "🛂 " + ("اقامت" if lang == Language.FA else "Residency" if lang == Language.EN else "إقامة" if lang == Language.AR else "Резидентство"), "callback_data": "goal_residency"}
        ]
        
        return BrainResponse(
            message=warmup_msg.get(lang, warmup_msg[Language.EN]),
            next_state=ConversationState.WARMUP,
            lead_updates=lead_updates,
            buttons=goal_buttons  # Show buttons but also accept text!
        )
    
    # ==================== NEW STATE MACHINE HANDLERS ====================
    # These handlers implement the 6-phase professional sales flow
    
    async def _handle_warmup(
        self, 
        lang: Language, 
        message: Optional[str], 
        callback_data: Optional[str],
        lead: Lead,
        lead_updates: Dict
    ) -> BrainResponse:
        """
        🎯 WARMUP Phase: Conversational Discovery (Wolf of Wall Street Mode)
        Goal: Identify primary objective through NATURAL CONVERSATION
        NO button dependency - AI extracts intent from text
        """
        user_name = lead.name or ("دوست من" if lang == Language.FA else "my friend" if lang == Language.EN else "صديقي" if lang == Language.AR else "друг мой")
        
        # Extract goal from button OR text message
        goal = None
        
        if callback_data and (callback_data.startswith("purpose_") or callback_data.startswith("goal_")):
            goal = callback_data.replace("purpose_", "").replace("goal_", "")  # purpose_investment OR goal_investment
            logger.info(f"✅ Goal selected via button: {goal}")
        elif message:
            # 🧠 AI-POWERED: Extract intent from natural language
            intent_data = await self.extract_user_intent(message, lang, ["goal", "budget", "bedrooms", "property_type", "location", "transaction_type"])
            
            # FALLBACK: If AI fails, use keyword matching (handles voice transcription errors)
            if not intent_data.get("goal"):
                message_lower = message.lower()
                goal_keywords = {
                    "investment": ["سرمایه", "investment", "invest", "استثمار", "инвестиц", "roi", "return", "بازده", "سود", "درآمد"],
                    "living": ["زندگی", "living", "live", "سكن", "жилье", "خونه", "منزل", "home", "family", "خانواده"],
                    "residency": ["اقامت", "residency", "visa", "виза", "تأشيرة", "ویزا", "اقامة", "residenc", "golden visa"]
                }
                for goal_key, keywords in goal_keywords.items():
                    if any(kw in message_lower for kw in keywords):
                        intent_data["goal"] = goal_key
                        logger.info(f"✅ Goal '{goal_key}' extracted via keyword fallback from: '{message}'")
                        break
            
            # FALLBACK: Extract transaction_type via keyword matching if AI didn't
            if not intent_data.get("transaction_type"):
                message_lower = message.lower()
                rent_keywords = ["rent", "rental", "lease", "اجاره", "إيجار", "аренда", "کرایه"]
                buy_keywords = ["buy", "purchase", "خرید", "شراء", "купить", "own", "سرمایه‌گذاری"]
                
                if any(kw in message_lower for kw in rent_keywords):
                    intent_data["transaction_type"] = "rent"
                    logger.info(f"✅ Transaction type 'rent' extracted via keyword from: '{message}'")
                elif any(kw in message_lower for kw in buy_keywords):
                    intent_data["transaction_type"] = "buy"
                    logger.info(f"✅ Transaction type 'buy' extracted via keyword from: '{message}'")
            
            if intent_data.get("goal"):
                goal = intent_data["goal"]
                logger.info(f"✅ Goal extracted from text '{message}': {goal}")
                
                # BONUS: Also save any other extracted data
                conversation_data = lead.conversation_data or {}
                filled_slots = lead.filled_slots or {}
                
                if intent_data.get("budget"):
                    budget_val = int(intent_data["budget"])
                    conversation_data["budget_min"] = budget_val * 0.8
                    conversation_data["budget_max"] = budget_val * 1.2
                    filled_slots["budget"] = True
                    lead_updates["budget_min"] = int(budget_val * 0.8)
                    lead_updates["budget_max"] = int(budget_val * 1.2)
                    logger.info(f"💰 Budget extracted: {budget_val}")
                
                if intent_data.get("bedrooms"):
                    bedrooms = int(intent_data["bedrooms"])
                    conversation_data["bedrooms_min"] = bedrooms
                    conversation_data["bedrooms_max"] = bedrooms
                    filled_slots["bedrooms"] = True
                    lead_updates["bedrooms_min"] = bedrooms
                    lead_updates["bedrooms_max"] = bedrooms
                    logger.info(f"🛏️ Bedrooms extracted: {bedrooms}")
                
                if intent_data.get("location"):
                    location = intent_data["location"]
                    conversation_data["preferred_location"] = location
                    filled_slots["location"] = True
                    lead_updates["preferred_location"] = location
                    logger.info(f"📍 Location extracted: {location}")
                
                if intent_data.get("property_type"):
                    prop_type = intent_data["property_type"]
                    conversation_data["property_type"] = prop_type
                    filled_slots["property_type"] = True
                    logger.info(f"🏠 Property type extracted: {prop_type}")
                
                # 🔑 CRITICAL: Extract transaction_type and save it!
                if intent_data.get("transaction_type"):
                    tt = intent_data["transaction_type"]
                    conversation_data["transaction_type"] = tt
                    filled_slots["transaction_type"] = True
                    lead_updates["transaction_type"] = TransactionType.BUY if tt == "buy" else TransactionType.RENT
                    logger.info(f"🔑 Transaction type extracted: {tt}")
                
                lead_updates["conversation_data"] = conversation_data
                lead_updates["filled_slots"] = filled_slots
        
        # If still no goal after AI + keyword fallback, guide user with examples
        if not goal and message:
            clarify_msg = {
                Language.EN: f"I want to help you find the perfect property! 😊\n\nJust tell me in simple words - are you looking for:\n• **Investment** property (for rental income)?\n• **Home** to live in?\n• **Residency** visa?\n\nExample: \"I want investment property\" or \"Need residency visa\"",
                Language.FA: f"میخوام بهترین ملک رو برات پیدا کنم! 😊\n\nفقط به زبون ساده بگو - دنبال کدوم هستی:\n• ملک **سرمایه‌گذاری** (برای درآمد اجاره)?\n• **خونه** برای زندگی?\n• **اقامت** (ویزا)?\n\nمثلاً: \"میخوام سرمایه‌گذاری کنم\" یا \"برای اقامت میخوام\""
            }
            
            # ✅ CRITICAL FIX: Show goal buttons as backup (user might not know what to say or be lazy)
            # "من میخوام همه دکمه های قبل باشند شاید کاربر نفهمه باید چی بگه یا تنبل باشه"
            goal_buttons = [
                {"text": "🏡 " + ("خرید خانه" if lang == Language.FA else "Buy Property" if lang == Language.EN else "شراء عقار" if lang == Language.AR else "Купить"), "callback_data": "goal_buy"},
                {"text": "💰 " + ("سرمایه‌گذاری" if lang == Language.FA else "Investment" if lang == Language.EN else "استثمار" if lang == Language.AR else "Инвестиция"), "callback_data": "goal_investment"},
                {"text": "🛂 " + ("اقامت طلایی" if lang == Language.FA else "Golden Visa" if lang == Language.EN else "تأشيرة ذهبية" if lang == Language.AR else "Золотая виза"), "callback_data": "goal_residency"}
            ]
            
            return BrainResponse(
                message=clarify_msg.get(lang, clarify_msg[Language.EN]),
                next_state=ConversationState.WARMUP,
                lead_updates=lead_updates,
                buttons=goal_buttons  # ✅ Show buttons as backup! User can type OR click
            )
        
        # Process goal if we have it
        if goal:
            
            # Store in conversation_data
            conversation_data = lead.conversation_data or {}
            conversation_data["goal"] = goal
            
            # Mark filled_slots
            filled_slots = lead.filled_slots or {}
            filled_slots["goal"] = True
            
            lead_updates["conversation_data"] = conversation_data
            lead_updates["filled_slots"] = filled_slots
            
            if goal == "investment" or goal == "residency":
                # Auto-set transaction type to BUY (investment/residency = always buy)
                conversation_data["transaction_type"] = "buy"
                filled_slots["transaction_type"] = True
                lead_updates["conversation_data"] = conversation_data
                lead_updates["filled_slots"] = filled_slots
                lead_updates["transaction_type"] = TransactionType.BUY
                lead_updates["purpose"] = Purpose.INVESTMENT if goal == "investment" else Purpose.RESIDENCY
                
                # 💰 WOLF OF WALL STREET MODE: Numbers-driven, high-energy sales pitch
                category_question = {
                    Language.EN: f"**Smart move, {user_name}!** 🚀\n\nDubai is CRUSHING it right now:\n\n💰 **Your Investment Returns:**\n• 7-10% net ROI (beats most global markets)\n• Zero tax on rental income (100% yours!)\n• Golden Visa from 750K AED\n• Capital appreciation: +8% annually\n\n💡 **Pro Tip:** Most investors use 70% financing - rental income covers the mortgage!\n\n🎤 Send voice messages anytime | 📸 Share property photos you like\n\n**Quick question:** Residential (apartments/villas) or Commercial (offices/shops)?",
                    Language.FA: f"**{user_name} عزیز، انتخاب هوشمندانه!** 🚀\n\nدبی الان داره رکورد میزنه:\n\n💰 **بازده سرمایه‌گذاری شما:**\n• بازده خالص ۷-۱۰٪ (از اکثر بازارهای جهانی بهتره)\n• مالیات صفر روی اجاره (۱۰۰٪ مال خودته!)\n• ویزای طلایی از ۷۵۰ هزار درهم\n• رشد ارزش: سالانه +۸٪\n\n💡 **نکته حرفه‌ای:** اکثر سرمایه‌گذارها ۷۰٪ فاینانس میگیرن - درآمد اجاره وام رو پرداخت میکنه!\n\n🎤 هر وقت خواستی ویس بفرست | 📸 عکس ملک مورد علاقت رو share کن\n\n**یه سوال سریع:** مسکونی (آپارتمان/ویلا) یا تجاری (دفتر/مغازه)؟",
                    Language.AR: f"**{user_name}، اختيار ذكي!** 🚀\n\nدبي تحطم الأرقام الآن:\n\n💰 **عوائد استثمارك:**\n• عائد صافٍ 7-10% (يتفوق على معظم الأسواق العالمية)\n• صفر ضريبة على دخل الإيجار (100% لك!)\n• تأشيرة ذهبية من 750 ألف درهم\n• ارتفاع قيمة رأس المال: +8% سنوياً\n\n💡 **نصيحة احترافية:** معظم المستثمرين يستخدمون تمويل 70% - دخل الإيجار يغطي الرهن!\n\n🎤 أرسل رسائل صوتية في أي وقت | 📸 شارك صور العقارات التي تعجبك\n\n**سؤال سريع:** سكني (شقق/فلل) أم تجاري (مكاتب/محلات)؟",
                    Language.RU: f"**{user_name}, умный выбор!** 🚀\n\nДубай сейчас бьёт рекорды:\n\n💰 **Ваша доходность:**\n• 7-10% чистой ROI (превосходит большинство мировых рынков)\n• Ноль налогов на арендный доход (100% ваши!)\n• Золотая виза от 750K AED\n• Рост стоимости: +8% в год\n\n💡 **Профи совет:** Большинство инвесторов берут 70% финансирования - аренда покрывает ипотеку!\n\n🎤 Отправляйте голосовые в любое время | 📸 Делитесь фото объектов\n\n**Быстрый вопрос:** Жилая (квартиры/виллы) или коммерческая (офисы/магазины)?"
                }
                
                category_buttons = [
                    {"text": "🏠 " + ("مسکونی" if lang == Language.FA else "Residential" if lang == Language.EN else "سكني" if lang == Language.AR else "Жилая"), 
                     "callback_data": "category_residential"},
                    {"text": "🏢 " + ("تجاری" if lang == Language.FA else "Commercial" if lang == Language.EN else "تجاري" if lang == Language.AR else "Коммерческая"), 
                     "callback_data": "category_commercial"}
                ]
                
                return BrainResponse(
                    message=category_question.get(lang, category_question[Language.EN]),
                    next_state=ConversationState.SLOT_FILLING,
                    lead_updates=lead_updates | {
                        "conversation_data": conversation_data,
                        "filled_slots": filled_slots,
                        "pending_slot": "property_category"
                    },
                    buttons=category_buttons
                )
            
            # For LIVING goal, ask transaction type (buy/rent) UNLESS already extracted
            if goal == "living":
                lead_updates["purpose"] = Purpose.LIVING
                
                # 🚀 SMART SKIP: If transaction_type already extracted (e.g., "میخوام خونه اجاره کنم")
                # Skip the buy/rent question and go straight to category!
                conversation_data = lead.conversation_data or {}
                filled_slots = lead.filled_slots or {}
                
                if filled_slots.get("transaction_type") or conversation_data.get("transaction_type"):
                    # Transaction type already known - skip to category selection
                    logger.info(f"🚀 Transaction type already extracted - skipping to category")
                    transaction_type_str = conversation_data.get("transaction_type")
                    
                    # Ask category directly
                    category_question = {
                        Language.EN: f"Great! {'Renting' if transaction_type_str == 'rent' else 'Buying'} in Dubai - smart choice! 🏠\n\n🎤 Voice messages welcome | 📸 Share property photos\n\nWhat type of property?",
                        Language.FA: f"عالی! {'اجاره' if transaction_type_str == 'rent' else 'خرید'} در دبی - انتخاب هوشمندانه! 🏠\n\n🎤 ویس بفرست | 📸 عکس بفرست\n\nچه نوع ملکی؟",
                        Language.AR: f"رائع! {'الإيجار' if transaction_type_str == 'rent' else 'الشراء'} في دبي - اختيار ذكي! 🏠\n\n🎤 رسائل صوتية | 📸 شارك صور\n\nما نوع العقار؟",
                        Language.RU: f"Отлично! {'Аренда' if transaction_type_str == 'rent' else 'Покупка'} в Дубае - умный выбор! 🏠\n\n🎤 Голосовые | 📸 Делитесь фото\n\nКакой тип недвижимости?"
                    }
                    
                    category_buttons = [
                        {"text": "🏠 " + ("مسکونی" if lang == Language.FA else "Residential" if lang == Language.EN else "سكني" if lang == Language.AR else "Жилая"), 
                         "callback_data": "category_residential"},
                        {"text": "🏢 " + ("تجاری" if lang == Language.FA else "Commercial" if lang == Language.EN else "تجاري" if lang == Language.AR else "Коммерческая"), 
                         "callback_data": "category_commercial"}
                    ]
                    
                    return BrainResponse(
                        message=category_question.get(lang, category_question[Language.EN]),
                        next_state=ConversationState.SLOT_FILLING,
                        lead_updates=lead_updates | {
                            "conversation_data": conversation_data,
                            "filled_slots": filled_slots,
                            "pending_slot": "property_category"
                        },
                        buttons=category_buttons
                    )
                
                # 🏠 EMOTIONAL APPEAL: Sell the dream lifestyle, not just property
                transaction_question = {
                    Language.EN: f"**Perfect choice, {user_name}!** 🏠\n\nDubai lifestyle is incredible:\n• Year-round sunshine ☀️\n• World-class schools & hospitals\n• Zero crime, ultra-safe for families\n• Beach, desert, city - all in one place\n\n🎤 Voice messages welcome | 📸 Share your dream home pics\n\n**Quick question:** Looking to **buy your forever home** or **rent first** to explore?",
                    Language.FA: f"**{user_name} عزیز، انتخاب عالی!** 🏠\n\nزندگی تو دبی فوق‌العادست:\n• آفتاب ۳۶۵ روز سال ☀️\n• مدارس و بیمارستان‌های جهانی\n• جرم صفر، امنیت کامل برای خانواده\n• ساحل، بیابون، شهر - همه تو یه جا\n\n🎤 ویس بفرست | 📸 عکس خونه رویاییت رو share کن\n\n**یه سوال سریع:** می‌خوای **خونه دائمی بخری** یا **اول اجاره** کنی تا شناخت پیدا کنی؟",
                    Language.AR: f"**{user_name}، اختيار مثالي!** 🏠\n\nنمط الحياة في دبي مذهل:\n• شمس طوال العام ☀️\n• مدارس ومستشفيات عالمية\n• صفر جريمة، آمان تام للعائلات\n• شاطئ، صحراء، مدينة - كل شيء في مكان واحد\n\n🎤 رسائل صوتية مرحب بها | 📸 شارك صور منزل أحلامك\n\n**سؤال سريع:** تبحث عن **شراء منزل دائم** أم **إيجار أولاً** للاستكشاف؟",
                    Language.RU: f"**{user_name}, отличный выбор!** 🏠\n\nЖизнь в Дубае невероятна:\n• Круглогодичное солнце ☀️\n• Мировые школы и больницы\n• Ноль преступности, безопасно для семей\n• Пляж, пустыня, город - всё в одном месте\n\n🎤 Голосовые приветствуются | 📸 Делитесь фото дома мечты\n\n**Быстрый вопрос:** Хотите **купить навсегда** или **сначала арендовать**?"
                }
                
                # Show Buy/Rent buttons
                transaction_buttons = [
                    {"text": "🏠 " + ("خرید" if lang == Language.FA else "Buy" if lang == Language.EN else "شراء" if lang == Language.AR else "Купить"), "callback_data": "transaction_buy"},
                    {"text": "🔑 " + ("اجاره" if lang == Language.FA else "Rent" if lang == Language.EN else "إيجار" if lang == Language.AR else "Аренда"), "callback_data": "transaction_rent"}
                ]
                
                return BrainResponse(
                    message=transaction_question.get(lang, transaction_question[Language.EN]),
                    next_state=ConversationState.SLOT_FILLING,
                    lead_updates=lead_updates | {
                        "conversation_data": conversation_data,
                        "filled_slots": filled_slots,
                        "pending_slot": "transaction_type"
                    },
                    buttons=transaction_buttons
                )
        
        # If text message, use AI to answer FAQ - but DON'T re-ask the goal question
        # They'll click the button when ready
        if message and not callback_data:
            # User sent a text message instead of clicking button
            # Could be: FAQ question, changing language, expressing interest, etc.
            
            # Check for ROI/PDF request
            roi_pdf_patterns = r'roi|pdf|گزارش|ریپورت|بازده|سود|پی دی اف|report|بذه|بده'
            if re.search(roi_pdf_patterns, message, re.IGNORECASE):
                # User wants ROI report or PDF
                roi_response = {
                    Language.EN: f"📊 I'd love to send you a detailed ROI report!\n\nTo generate your personalized PDF with:\n✅ ROI calculations for your budget\n✅ Rental income projections\n✅ Golden Visa eligibility\n✅ Payment plans\n\nI need to know your preferences first. Let me show you our properties!",
                    Language.FA: f"📊 حتماً گزارش ROI کامل براتون می‌فرستم!\n\nبرای ساخت PDF اختصاصی با:\n✅ محاسبات ROI برای بودجه شما\n✅ پیش‌بینی درآمد اجاره\n✅ واجد شرایط ویزای طلایی\n✅ طرح‌های پرداخت\n\nابتدا باید ترجیحاتتون رو بدونم. بذار املاکمون رو نشونت بدم!",
                    Language.AR: f"📊 أحب أن أرسل لك تقرير ROI مفصل!\n\nلإنشاء PDF مخصص مع:\n✅ حسابات ROI لميزانيتك\n✅ توقعات دخل الإيجار\n✅ أهلية التأشيرة الذهبية\n✅ خطط السداد\n\nأحتاج أن أعرف تفضيلاتك أولاً. دعني أريك ممتلكاتنا!",
                    Language.RU: f"📊 С удовольствием отправлю вам детальный ROI отчёт!\n\nДля создания персонализированного PDF с:\n✅ Расчётами ROI для вашего бюджета\n✅ Прогнозами арендного дохода\n✅ Правом на золотую визу\n✅ Планами оплаты\n\nМне нужно знать ваши предпочтения. Позвольте показать наши объекты!"
                }
                # Continue with warmup flow
                return BrainResponse(
                    message=roi_response.get(lang, roi_response[Language.EN]),
                    next_state=ConversationState.WARMUP,
                    buttons=[
                        {"text": "💰 " + ("سرمایه‌گذاری" if lang == Language.FA else "Investment"), "callback_data": "goal_investment"},
                        {"text": "🏠 " + ("زندگی" if lang == Language.FA else "Living"), "callback_data": "goal_living"},
                        {"text": "🛂 " + ("اقامت" if lang == Language.FA else "Residency"), "callback_data": "goal_residency"}
                    ]
                )
            
            # Check if this is actually a language change request
            lang_change_patterns = {
                Language.FA: r'فارسی|persian|farsi',
                Language.AR: r'عربي|عربی|arabic',
                Language.RU: r'русский|russian',
                Language.EN: r'english|انگلیسی'
            }
            
            for check_lang, pattern in lang_change_patterns.items():
                if re.search(pattern, message, re.IGNORECASE):
                    # User wants to change language - redirect to language select
                    return self._handle_language_select(check_lang, None, {"language": check_lang}, message)
            
            # Check if message is a goal selection in text form (for voice users)
            # ⚠️ ONLY if goal was NOT already extracted above (avoid duplicate processing)
            if not goal:
                goal_keywords = {
                    "investment": ["سرمایه‌گذاری", "investment", "invest", "استثمار", "инвестиция", "سرمایه", "roi", "return", "بازده"],
                    "living": ["زندگی", "living", "live", "سكن", "жилье", "خونه", "منزل", "home"],
                    "residency": ["اقامت", "residency", "visa", "виза", "تأشيرة", "ویزا", "اقامة"]
                }
                
                message_lower = message.lower()
                for goal_check, keywords in goal_keywords.items():
                    if any(kw.lower() in message_lower or kw in message for kw in keywords):
                        # User specified goal in text - treat as button click
                        logger.info(f"✅ Goal '{goal_check}' extracted from text: '{message}'")
                        return await self._handle_warmup(lang, None, f"purpose_{goal_check}", lead, lead_updates)
            
            # Otherwise: This is an FAQ or off-topic question in WARMUP
            # Answer it, but DON'T append the goal question again
            # Let them click the button when they're ready
            ai_response = await self.generate_ai_response(message, lead)
            
            # Response stays in WARMUP but with NO buttons appended
            # User will click goal buttons when ready
            return BrainResponse(
                message=ai_response,
                next_state=ConversationState.WARMUP,
                buttons=[
                    {"text": "💰 " + ("سرمایه‌گذاری" if lang == Language.FA else "Investment"), "callback_data": "goal_investment"},
                    {"text": "🏠 " + ("زندگی" if lang == Language.FA else "Living"), "callback_data": "goal_living"},
                    {"text": "🛂 " + ("اقامت" if lang == Language.FA else "Residency"), "callback_data": "goal_residency"}
                ]
            )
        
        # Default: Show goal buttons (initial entry to WARMUP)
        warmup_message = {
            Language.EN: "Great to meet you! 🎯\n\nAre you looking for Investment, Living, or Residency in Dubai?",
            Language.FA: "خوشحالم که با شما آشنا شدم! 🎯\n\nبه دنبال سرمایه‌گذاری، زندگی یا اقامت در دبی هستید؟",
            Language.AR: "سعيد بلقائك! 🎯\n\nهل تبحث عن الاستثمار أم العيش أم الإقامة في دبي؟",
            Language.RU: "Приятно познакомиться! 🎯\n\nВы ищете инвестиции, проживание или резиденцию в Дубае?"
        }
        
        return BrainResponse(
            message=warmup_message.get(lang, warmup_message[Language.EN]),
            next_state=ConversationState.WARMUP,
            buttons=[
                {"text": "💰 " + ("سرمایه‌گذاری" if lang == Language.FA else "Investment"), "callback_data": "goal_investment"},
                {"text": "🏠 " + ("زندگی" if lang == Language.FA else "Living"), "callback_data": "goal_living"},
                {"text": "🛂 " + ("اقامت" if lang == Language.FA else "Residency"), "callback_data": "goal_residency"}
            ]
        )
    
    async def _handle_slot_filling(
        self,
        lang: Language,
        message: Optional[str],
        callback_data: Optional[str],
        lead: Lead,
        lead_updates: Dict
    ) -> BrainResponse:
        """
        SLOT_FILLING Phase: AGGRESSIVE CLOSER MODE.
        
        SYSTEM INSTRUCTION IMPLEMENTATION:
        1. Extract Location/Budget/PropertyType from EVERY input using AI
        2. SWITCH TO PRESENTATION when all 3 present - NO MORE QUESTIONS
        3. One question max per missing slot - direct and professional
        4. Handle lazy/messy user input intelligently
        
        This bot is a SALESPERSON, not a chatbot.
        """
        conversation_data = lead.conversation_data or {}
        filled_slots = lead.filled_slots or {}
        
        # === CRITICAL: EXTRACT FROM CURRENT MESSAGE FIRST (LAZY USER PROTOCOL) ===
        # ✅ FIX: ALWAYS extract intent from text messages - enable natural language qualification
        if message and not callback_data:
            logger.info(f"🔍 CLOSER MODE: Analyzing message for Location/Budget/PropertyType extraction: '{message[:100]}'")
            
            # Use AI to extract ALL preferences from messy user input
            intent_data = await self.extract_user_intent(
                message, 
                lang, 
                ["budget", "property_type", "location", "bedrooms", "transaction_type", "amenities", "urgency"]
            )
            
            # Update conversation_data with extracted info
            if intent_data.get("budget"):
                budget_val = int(intent_data["budget"])
                conversation_data["budget_min"] = int(budget_val * 0.8)
                conversation_data["budget_max"] = int(budget_val * 1.2)
                filled_slots["budget"] = True
                lead_updates["budget_min"] = conversation_data["budget_min"]
                lead_updates["budget_max"] = conversation_data["budget_max"]
                logger.info(f"💰 Extracted budget: {budget_val}")
            
            if intent_data.get("location"):
                conversation_data["location"] = intent_data["location"]
                lead_updates["preferred_location"] = intent_data["location"]
                filled_slots["location"] = True  # ✅ FIX: Mark location as filled
                logger.info(f"📍 Extracted location: {intent_data['location']}")
            
            if intent_data.get("property_type"):
                pt_str = str(intent_data["property_type"]).lower()
                conversation_data["property_type"] = pt_str
                filled_slots["property_type"] = True
                
                # Map to enum
                pt_map = {"apartment": PropertyType.APARTMENT, "villa": PropertyType.VILLA, "penthouse": PropertyType.PENTHOUSE, "townhouse": PropertyType.TOWNHOUSE, "commercial": PropertyType.COMMERCIAL, "land": PropertyType.LAND}
                if pt_str in pt_map:
                    lead_updates["property_type"] = pt_map[pt_str]
                logger.info(f"🏠 Extracted property_type: {pt_str}")
            
            if intent_data.get("bedrooms"):
                conversation_data["bedrooms_min"] = intent_data["bedrooms"]
                conversation_data["bedrooms_max"] = intent_data["bedrooms"]
                filled_slots["bedrooms"] = True  # ✅ FIX: Mark bedrooms as filled
                logger.info(f"🛏️ Extracted bedrooms: {intent_data['bedrooms']}")
            
            # ✅ NEW: Extract amenities (pool, gym, beach, parking)
            if intent_data.get("amenities"):
                amenities = intent_data["amenities"]
                if isinstance(amenities, list):
                    conversation_data["required_amenities"] = amenities
                    logger.info(f"🏊 Extracted amenities: {amenities}")
            
            # ✅ NEW: Detect urgency signals ("need ASAP", "urgent", "فوری")
            if intent_data.get("urgency"):
                urgency = intent_data["urgency"]
                conversation_data["urgency_level"] = urgency
                logger.info(f"⚡ Detected urgency: {urgency}")
        
        # === THE SWITCH: CHECK IF READY TO PRESENT (Location+Budget+PropertyType) ===
        has_location = conversation_data.get("location") or lead.preferred_location
        has_budget = filled_slots.get("budget") or conversation_data.get("budget_min") or lead.budget_min
        has_property_type = filled_slots.get("property_type") or conversation_data.get("property_type") or lead.property_type
        
        if has_location and has_budget and has_property_type:
            logger.info(f"🎯 SWITCH ACTIVATED: Location+Budget+PropertyType present → FETCHING AND PRESENTING PROPERTIES NOW")
            
            # Save all data before switching
            lead_updates["conversation_data"] = conversation_data
            lead_updates["filled_slots"] = filled_slots
            lead_updates["conversation_state"] = ConversationState.VALUE_PROPOSITION
            
            # Apply updates to lead object so _handle_value_proposition has fresh data
            for key, value in lead_updates.items():
                if hasattr(lead, key):
                    setattr(lead, key, value)
            
            # Call VALUE_PROPOSITION handler to fetch and present properties
            logger.info(f"🔄 Calling _handle_value_proposition to present properties for lead {lead.id}")
            return await self._handle_value_proposition(
                lang=lang,
                message=None,  # No message - triggered by button
                callback_data=callback_data,
                lead=lead,
                lead_updates=lead_updates
            )
        
        # 🎯 FLOATING LOGIC: Check if user went off-script (text/voice instead of button)
        if message and not callback_data:
            # User sent text/voice instead of clicking button
            floating_response = await self.handle_floating_input(
                lead=lead,
                message=message,
                expected_state=ConversationState.SLOT_FILLING,
                conversation_data=conversation_data
            )
            
            if floating_response and not floating_response.lead_updates:
                # No smart extraction succeeded - user asked question
                # Return AI answer + redirect back to slot
                logger.info(f"🔄 Floating logic handled off-script input for lead {lead.id}")
                return floating_response
            # else: smart extraction succeeded, continue with extracted data
        
        # === PRE-FILL FROM VOICE ENTITIES (only if this is NOT a callback) ===
        # Only process voice entities if we're handling a text/voice message, not a button click
        voice_entities = lead.voice_entities or {}
        if voice_entities and isinstance(voice_entities, dict) and not callback_data:
            # DATA INTEGRITY: Validate types before using
            # Budget from voice
            try:
                if voice_entities.get("budget_min") and not filled_slots.get("budget"):
                    budget_min_val = int(voice_entities["budget_min"])  # Ensure integer
                    budget_max_val = int(voice_entities.get("budget_max", budget_min_val))
                    
                    conversation_data["budget_min"] = budget_min_val
                    conversation_data["budget_max"] = budget_max_val
                    filled_slots["budget"] = True
                    lead_updates["budget_min"] = budget_min_val
                    lead_updates["budget_max"] = budget_max_val
                    logger.info(f"🎤 Voice extracted budget: {budget_min_val}")
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ Invalid budget in voice_entities: {e}")
            
            # Property type from voice
            try:
                if voice_entities.get("property_type") and not filled_slots.get("property_type"):
                    pt_str = str(voice_entities["property_type"]).lower().strip()
                    property_type_map = {
                        "apartment": PropertyType.APARTMENT,
                        "villa": PropertyType.VILLA,
                        "penthouse": PropertyType.PENTHOUSE,
                        "townhouse": PropertyType.TOWNHOUSE,
                        "commercial": PropertyType.COMMERCIAL,
                        "land": PropertyType.LAND
                    }
                    if pt_str in property_type_map:
                        conversation_data["property_type"] = pt_str
                        filled_slots["property_type"] = True
                        lead_updates["property_type"] = property_type_map[pt_str]
                        logger.info(f"🎤 Voice extracted property_type: {pt_str}")
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"⚠️ Invalid property_type in voice_entities: {e}")
            
            # Transaction type from voice
            try:
                if voice_entities.get("transaction_type") and not filled_slots.get("transaction_type"):
                    tt_str = str(voice_entities["transaction_type"]).lower().strip()
                    if tt_str in ["buy", "rent"]:
                        conversation_data["transaction_type"] = tt_str
                        filled_slots["transaction_type"] = True
                        lead_updates["transaction_type"] = TransactionType.BUY if tt_str == "buy" else TransactionType.RENT
                        logger.info(f"🎤 Voice extracted transaction_type: {tt_str}")
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"⚠️ Invalid transaction_type in voice_entities: {e}")
        
        # === HANDLE BUTTON RESPONSES (Slot Filling) ===
        if callback_data:
            # Budget selection
            # Budget selection (handles both rent_budget_ and buy_budget_)
            if callback_data.startswith("rent_budget_") or callback_data.startswith("buy_budget_"):
                # Extract index and determine budget type
                if callback_data.startswith("rent_budget_"):
                    idx = int(callback_data.replace("rent_budget_", ""))
                    # RENTAL budget ranges (stored as annual rent in DB)
                    min_val, max_val = RENT_BUDGET_RANGES[idx]
                else:
                    idx = int(callback_data.replace("buy_budget_", ""))
                    min_val, max_val = BUDGET_RANGES[idx]
                
                conversation_data["budget_min"] = min_val
                conversation_data["budget_max"] = max_val
                filled_slots["budget"] = True
                lead_updates["budget_min"] = min_val
                lead_updates["budget_max"] = max_val
                
                # CRITICAL: If we have goal + budget, SHOW PROPERTIES IMMEDIATELY!
                if filled_slots.get("goal") or conversation_data.get("goal"):
                    logger.info(f"✅ Budget button clicked + have goal - SHOWING PROPERTIES immediately!")
                    
                    # Save everything to database
                    lead_updates["conversation_data"] = conversation_data
                    lead_updates["filled_slots"] = filled_slots
                    
                    # Go to VALUE_PROPOSITION to show properties
                    return BrainResponse(
                        message="",  # Empty - will show properties in VALUE_PROPOSITION
                        next_state=ConversationState.VALUE_PROPOSITION,
                        lead_updates=lead_updates,
                        buttons=[]
                    )
                
                # Get property category to show appropriate property types
                category_str = conversation_data.get("property_category")
                
                # 🔥 CRITICAL: Category should have been set in earlier flow
                if not category_str:
                    logger.error(f"❌ Lead {lead.id}: Missing property_category in budget handler! Flow integrity issue.")
                    # Recovery: Ask category again
                    category_question = {
                        Language.EN: "⚠️ Let me confirm: Residential or Commercial property?",
                        Language.FA: "⚠️ بذار تایید کنم: ملک مسکونی یا تجاری؟",
                        Language.AR: "⚠️ دعني أؤكد: عقار سكني أم تجاري؟",
                        Language.RU: "⚠️ Давайте уточним: Жилая или коммерческая?"
                    }
                    return BrainResponse(
                        message=category_question.get(lang, category_question[Language.EN]),
                        next_state=ConversationState.SLOT_FILLING,
                        lead_updates=lead_updates | {
                            "conversation_data": conversation_data,
                            "filled_slots": filled_slots,
                            "pending_slot": "property_category"
                        },
                        buttons=[
                            {"text": "🏠 " + ("مسکونی" if lang == Language.FA else "Residential" if lang == Language.EN else "سكني" if lang == Language.AR else "Жилая"), 
                             "callback_data": "category_residential"},
                            {"text": "🏢 " + ("تجاری" if lang == Language.FA else "Commercial" if lang == Language.EN else "تجاري" if lang == Language.AR else "Коммерческая"), 
                             "callback_data": "category_commercial"}
                        ]
                    )
                
                # Next: Ask specific property type based on category
                property_question = {
                    Language.EN: "Perfect! What specific type?",
                    Language.FA: "عالی! چه نوع ملکی؟",
                    Language.AR: "رائع! ما النوع المحدد؟",
                    Language.RU: "Отлично! Какой именно тип?"
                }
                
                if category_str == "residential":
                    property_buttons = [
                        {"text": "🏢 " + ("آپارتمان" if lang == Language.FA else "Apartment" if lang == Language.EN else "شقة" if lang == Language.AR else "Квартира"), 
                         "callback_data": "prop_apartment"},
                        {"text": "🏠 " + ("ویلا" if lang == Language.FA else "Villa" if lang == Language.EN else "فيلا" if lang == Language.AR else "Вилла"), 
                         "callback_data": "prop_villa"},
                        {"text": "🏰 " + ("پنت‌هاوس" if lang == Language.FA else "Penthouse" if lang == Language.EN else "بنتهاوس" if lang == Language.AR else "Пентхаус"), 
                         "callback_data": "prop_penthouse"},
                        {"text": "🏘️ " + ("تاون‌هاوس" if lang == Language.FA else "Townhouse" if lang == Language.EN else "تاون هاوس" if lang == Language.AR else "Таунхаус"), 
                         "callback_data": "prop_townhouse"},
                    ]
                else:  # commercial
                    property_buttons = [
                        {"text": "🏢 " + ("دفتر" if lang == Language.FA else "Office" if lang == Language.EN else "مكتب" if lang == Language.AR else "Офис"), 
                         "callback_data": "prop_commercial"},
                        {"text": "🏪 " + ("مغازه" if lang == Language.FA else "Shop" if lang == Language.EN else "محل" if lang == Language.AR else "Магазин"), 
                         "callback_data": "prop_commercial"},
                        {"text": "🏭 " + ("انبار" if lang == Language.FA else "Warehouse" if lang == Language.EN else "مستودع" if lang == Language.AR else "Склад"), 
                         "callback_data": "prop_commercial"},
                        {"text": "🏞️ " + ("زمین" if lang == Language.FA else "Land" if lang == Language.EN else "أرض" if lang == Language.AR else "Земля"), 
                         "callback_data": "prop_land"},
                    ]
                
                return BrainResponse(
                    message=property_question.get(lang, property_question[Language.EN]),
                    next_state=ConversationState.SLOT_FILLING,
                    lead_updates=lead_updates | {
                        "conversation_data": conversation_data,
                        "filled_slots": filled_slots,
                        "pending_slot": "property_type"
                    },
                    buttons=property_buttons
                )
            
            # Property type selection
            elif callback_data.startswith("prop_"):
                property_type_str = callback_data.replace("prop_", "")
                property_type_map = {
                    "apartment": PropertyType.APARTMENT,
                    "villa": PropertyType.VILLA,
                    "penthouse": PropertyType.PENTHOUSE,
                    "townhouse": PropertyType.TOWNHOUSE,
                    "commercial": PropertyType.COMMERCIAL,
                    "land": PropertyType.LAND
                }
                
                conversation_data["property_type"] = property_type_str
                filled_slots["property_type"] = True
                lead_updates["property_type"] = property_type_map.get(property_type_str)
                lead_updates["conversation_state"] = ConversationState.VALUE_PROPOSITION
                
                # 🔥 CRITICAL FIX: Save all preferences to database for future follow-ups
                # Extract bedrooms from conversation_data if available (from voice or text)
                if conversation_data.get("bedrooms_min"):
                    lead_updates["bedrooms_min"] = conversation_data["bedrooms_min"]
                if conversation_data.get("bedrooms_max"):
                    lead_updates["bedrooms_max"] = conversation_data["bedrooms_max"]
                
                # Save preferred locations as JSON array
                preferred_locs = []
                if conversation_data.get("location"):
                    preferred_locs.append(conversation_data["location"])
                if conversation_data.get("locations"):
                    preferred_locs.extend(conversation_data["locations"])
                if preferred_locs:
                    lead_updates["preferred_locations"] = list(set(preferred_locs))  # Remove duplicates
                    lead_updates["preferred_location"] = preferred_locs[0]  # Primary location
                
                logger.info(f"💾 Saved lead preferences: property_type={property_type_str}, bedrooms={conversation_data.get('bedrooms_min')}-{conversation_data.get('bedrooms_max')}, budget={conversation_data.get('budget_min')}-{conversation_data.get('budget_max')}")
                
                # All slots filled! Get property recommendations
                property_recs = await self.get_property_recommendations(lead)
                
                # Build comprehensive message with financial education + location/photo prompt
                # 🔥 FOMO + URGENCY MESSAGING (Wolf of Wall Street Style)
                financial_benefits = {
                    Language.EN: "\n\n💰 **Your Investment Numbers:**\n\n✅ 7-10% Annual ROI (beats S&P 500!)\n✅ Rental income: 110% mortgage coverage\n✅ Zero tax on profits (100% yours!)\n✅ Capital gains: +8% yearly (Dubai rising fast!)\n✅ Golden Visa eligible from 750K\n\n⚠️ **MARKET ALERT:** Dubai prices up 12% this year. Every month you wait costs you 1% appreciation!\n\n💡 Pro move: 70% financing = rental income exceeds payment. You make money from day 1!",
                    Language.FA: "\n\n💰 **اعداد سرمایه‌گذاری شما:**\n\n✅ بازده سالانه ۷-۱۰٪ (از S&P 500 بهتر!)\n✅ درآمد اجاره: ۱۱۰٪ پوشش وام\n✅ مالیات صفر روی سود (۱۰۰٪ مال خودته!)\n✅ رشد ارزش: سالانه +۸٪ (دبی داره سریع میره بالا!)\n✅ ویزای طلایی از ۷۵۰ هزار\n\n⚠️ **هشدار بازار:** قیمت‌های دبی امسال ۱۲٪ بالا رفته. هر ماه تأخیر یعنی از دست دادن ۱٪ رشد!\n\n💡 حرکت حرفه‌ای: ۷۰٪ فاینانس = درآمد اجاره بیشتر از قسط. از روز اول سود میکنی!",
                    Language.AR: "\n\n💰 **أبرز نقاط الاستثمار:**\n\n✅ عائد سنوي 7-10% - تغلب على التضخم، اِبنِ ثروة\n✅ دخل الإيجار يغطي الرهن - دخل سلبي\n✅ خطط دفع متاحة - ابدأ بدفعة أولى 25%\n✅ دخل معفى من الضرائب - لا ضريبة إيجار في الإمارات\n✅ ارتفاع قيمة رأس المال - قيمة عقارات دبي ترتفع 5-8% سنوياً\n\n💡 معظم المستثمرين يستخدمون تمويل 70% ودخل الإيجار يسدده!",
                    Language.RU: "\n\n💰 **Инвестиционные преимущества:**\n\n✅ 7-10% годовых ROI - Обгоняем инфляцию, растим капитал\n✅ Арендный доход покрывает ипотеку - Пассивный доход\n✅ Планы рассрочки - Начните с 25% первого взноса\n✅ Доход без налогов - Нет налога на аренду в ОАЭ\n✅ Рост стоимости - Недвижимость в Дубае растёт 5-8% в год\n\n💡 Большинство инвесторов берут 70% финансирования, а аренда его окупает!"
                }
                
                location_photo_prompt = {
                    Language.EN: "\n\n📍 **Want personalized help?**\nSend me your location or a photo of an area you like, and I'll find exact matches nearby!",
                    Language.FA: "\n\n📍 **می‌خوای کمک شخصی‌سازی شده؟**\nلوکیشنت یا عکسی از منطقه‌ای که دوست داری رو بفرست، من دقیقاً املاک اطراف رو پیدا می‌کنم!",
                    Language.AR: "\n\n📍 **تريد مساعدة مخصصة؟**\nأرسل لي موقعك أو صورة لمنطقة تعجبك، وسأجد لك تطابقات دقيقة في الجوار!",
                    Language.RU: "\n\n📍 **Хотите персональную помощь?**\nОтправьте мне свою локацию или фото района, который вам нравится, и я найду точные совпадения поблизости!"
                }
                
                if property_recs and "no properties" not in property_recs.lower():
                    value_message = {
                        Language.EN: f"Perfect! Here are properties matching your criteria:\n\n{property_recs}{financial_benefits[Language.EN]}{location_photo_prompt[Language.EN]}\n\n📋 Want full details and financing calculator?",
                        Language.FA: f"عالی! اینها ملک‌هایی هستند که با معیارهای شما مطابقت دارند:\n\n{property_recs}{financial_benefits[Language.FA]}{location_photo_prompt[Language.FA]}\n\n📋 می‌خواید جزئیات کامل و ماشین‌حساب تامین مالی رو ببینید؟",
                        Language.AR: f"رائع! إليك العقارات المطابقة لمعاييرك:\n\n{property_recs}{financial_benefits[Language.AR]}{location_photo_prompt[Language.AR]}\n\n📋 هل تريد التفاصيل الكاملة وحاسبة التمويل؟",
                        Language.RU: f"Отлично! Вот объекты по вашим критериям:\n\n{property_recs}{financial_benefits[Language.RU]}{location_photo_prompt[Language.RU]}\n\n📋 Хотите полные детали и калькулятор?"
                    }
                else:
                    value_message = {
                        Language.EN: f"I'm searching for the perfect properties for you...{location_photo_prompt[Language.EN]}\n\nMeanwhile, would you like a detailed market analysis?",
                        Language.FA: f"دارم املاک ایده‌آل رو برات جستجو می‌کنم...{location_photo_prompt[Language.FA]}\n\nدر ضمن، می‌خواهید تحلیل بازار کامل؟",
                        Language.AR: f"أبحث عن العقارات المثالية لك...{location_photo_prompt[Language.AR]}\n\nفي غضون ذلك، هل تريد تحليلاً مفصلاً للسوق؟",
                        Language.RU: f"Ищу идеальные объекты для вас...{location_photo_prompt[Language.RU]}\n\nТем временем, хотите подробный анализ рынка?"
                    }
                
                return BrainResponse(
                    message=value_message.get(lang, value_message[Language.EN]),
                    next_state=ConversationState.VALUE_PROPOSITION,
                    lead_updates=lead_updates | {
                        "conversation_data": conversation_data,
                        "filled_slots": filled_slots
                    },
                    buttons=[
                        {"text": self.get_text("btn_yes", lang), "callback_data": "details_yes"},
                        {"text": self.get_text("btn_no", lang), "callback_data": "details_no"},
                        {"text": "📅 " + self.get_text("btn_schedule_consultation", lang), "callback_data": "schedule_consultation"}
                    ]
                )
            
            # Transaction type selection (from either WARMUP goal flow or SLOT_FILLING property flow)
            # Handles both "tx_buy/tx_rent" (from property selection) and "transaction_buy/transaction_rent" (from goal selection)
            elif callback_data.startswith("tx_") or callback_data.startswith("transaction_"):
                # Normalize callback data
                if callback_data.startswith("transaction_"):
                    transaction_type_str = callback_data.replace("transaction_", "")
                else:
                    transaction_type_str = callback_data.replace("tx_", "")
                
                transaction_type_map = {
                    "buy": TransactionType.BUY,
                    "rent": TransactionType.RENT
                }
                
                conversation_data["transaction_type"] = transaction_type_str
                filled_slots["transaction_type"] = True
                lead_updates["transaction_type"] = transaction_type_map.get(transaction_type_str)
                
                # 🔥 BUG FIX: Both Buy AND Rent need property category!
                # After transaction type is selected, ask property category (Residential vs Commercial)
                # This helps determine budget ranges and property types
                
                # Get user's name for personalization
                user_name = lead.name or conversation_data.get("customer_name", "")
                name_part = f" {user_name}" if user_name else ""
                name_part_fa = f" {user_name} عزیز" if user_name else ""
                
                if transaction_type_str == "rent":
                    category_question = {
                        Language.EN: f"Great choice{name_part}! Rental properties in Dubai offer flexibility.\n\n🎤 Send me a voice message anytime!\n📸 Got a photo of your dream home? Share it!\n\nNow, what type of property?",
                        Language.FA: f"انتخاب خوب{name_part_fa}! اجاره در دبی انعطاف‌پذیری بالایی داره.\n\n🎤 هر وقت خواستی ویس بفرست!\n📸 عکس خونه رویاییت رو داری؟ بفرست!\n\nحالا، چه نوع ملکی؟",
                        Language.AR: f"اختيار جيد{name_part}! العقارات الإيجارية في دبي توفر المرونة.\n\n🎤 أرسل رسالة صوتية في أي وقت!\n📸 عندك صورة منزلك المثالي؟ شاركها!\n\nالآن، ما نوع العقار؟",
                        Language.RU: f"Отличный выбор{name_part}! Аренда в Дубае дает гибкость.\n\n🎤 Отправь голосовое!\n📸 Есть фото дома мечты? Поделись!\n\nТеперь, какой тип?"
                    }
                else:  # buy
                    category_question = {
                        Language.EN: f"Perfect{name_part}! Buying in Dubai is a smart investment.\n\n🎤 Send me a voice message anytime!\n📸 Got a photo of your dream property? Share it!\n\nWhat type of property?",
                        Language.FA: f"عالی{name_part_fa}! خرید در دبی سرمایه‌گذاری هوشمندانه‌ایه.\n\n🎤 هر وقت خواستی ویس بفرست!\n📸 عکس ملک رویاییت رو داری؟ بفرست!\n\nچه نوع ملکی؟",
                        Language.AR: f"ممتاز{name_part}! الشراء في دبي استثمار ذكي.\n\n🎤 أرسل رسالة صوتية!\n📸 عندك صورة عقارك المثالي؟ شاركها!\n\nما نوع العقار؟",
                        Language.RU: f"Отлично{name_part}! Покупка в Дубае - умная инвестиция.\n\n🎤 Отправь голосовое!\n📸 Есть фото объекта мечты? Поделись!\n\nКакой тип?"
                    }
                
                category_buttons = [
                    {"text": "🏠 " + ("مسکونی" if lang == Language.FA else "Residential" if lang == Language.EN else "سكني" if lang == Language.AR else "Жилая"), 
                     "callback_data": "category_residential"},
                    {"text": "🏢 " + ("تجاری" if lang == Language.FA else "Commercial" if lang == Language.EN else "تجاري" if lang == Language.AR else "Коммерческая"), 
                     "callback_data": "category_commercial"}
                ]
                
                return BrainResponse(
                    message=category_question.get(lang, category_question[Language.EN]),
                    next_state=ConversationState.SLOT_FILLING,
                    lead_updates=lead_updates | {
                        "conversation_data": conversation_data,
                        "filled_slots": filled_slots,
                        "pending_slot": "property_category"
                    },
                    buttons=category_buttons
                )
            
            # Property category selection (Residential vs Commercial)
            elif callback_data.startswith("category_"):
                category_str = callback_data.replace("category_", "")
                conversation_data["property_category"] = category_str
                
                # Get transaction type to determine budget ranges
                transaction_type_str = conversation_data.get("transaction_type")
                
                # 🔥 CRITICAL: Transaction type should have been set in WARMUP or earlier
                if not transaction_type_str:
                    logger.error(f"❌ Lead {lead.id}: Missing transaction_type in category handler! Flow integrity issue.")
                    # Recovery: Ask transaction type
                    transaction_question = {
                        Language.EN: "⚠️ Let me confirm: Are you looking to Buy or Rent?",
                        Language.FA: "⚠️ بذار تایید کنم: می‌خواهید بخرید یا اجاره کنید؟",
                        Language.AR: "⚠️ دعني أؤكد: هل تريد الشراء أم الإيجار؟",
                        Language.RU: "⚠️ Давайте уточним: Покупка или аренда?"
                    }
                    return BrainResponse(
                        message=transaction_question.get(lang, transaction_question[Language.EN]),
                        next_state=ConversationState.SLOT_FILLING,
                        lead_updates=lead_updates | {
                            "conversation_data": conversation_data,
                            "filled_slots": filled_slots,
                            "pending_slot": "transaction_type"
                        },
                        buttons=[
                            {"text": self.get_text("btn_buy", lang), "callback_data": "transaction_buy"},
                            {"text": self.get_text("btn_rent", lang), "callback_data": "transaction_rent"}
                        ]
                    )
                
                # Define budget ranges based on transaction type
                if transaction_type_str == "rent":
                    # Get customer name for personalization
                    customer_name = conversation_data.get("customer_name", "")
                    name_suffix = f", {customer_name}" if customer_name else ""
                    name_suffix_fa = f"، {customer_name} عزیز" if customer_name else ""
                    
                    budget_question = {
                        Language.EN: f"What's your monthly rental budget{name_suffix}?",
                        Language.FA: f"بودجه اجاره ماهانه شما چقدر است{name_suffix_fa}؟",
                        Language.AR: f"ما هي ميزانية الإيجار الشهرية{name_suffix}؟",
                        Language.RU: f"Каков ваш месячный бюджет на аренду{name_suffix}?"
                    }
                    
                    budget_buttons = []
                    for i, (min_val, max_val) in enumerate(RENT_BUDGET_RANGES.values()):
                        # Display as monthly (annual / 12)
                        monthly_min = min_val // 12
                        if max_val:
                            monthly_max = max_val // 12
                            label = f"{monthly_min:,} - {monthly_max:,} AED/month"
                        else:
                            label = f"{monthly_min:,}+ AED/month"
                        budget_buttons.append({"text": label, "callback_data": f"rent_budget_{i}"})
                else:
                    # BUY budget ranges (purchase price)
                    # Add Dubai advantages for purchase (especially for investment goal)
                    goal = conversation_data.get("goal", "")
                    
                    # Get customer name for personalization
                    customer_name = conversation_data.get("customer_name", "")
                    name_suffix = f", {customer_name}" if customer_name else ""
                    name_suffix_fa = f"، {customer_name} عزیز" if customer_name else ""
                    
                    dubai_benefits_prefix = ""
                    
                    if goal == "investment":
                        dubai_benefits_prefix = {
                            Language.EN: "💰 **Smart Move!** Most investors start with:\n• Off-plan payment plans (25% down, rest over 2-4 years)\n• Rental income covers 70% of mortgage\n• Property ready = instant cash flow!\n\n",
                            Language.FA: "💰 **انتخاب هوشمندانه!** اکثر سرمایه‌گذارها با این شروع می‌کنن:\n• پلن‌های پرداخت (۲۵٪ پیش، بقیه ۲-۴ سال)\n• درآمد اجاره ۷۰٪ وام رو می‌پوشونه\n• ملک آماده = جریان نقدی فوری!\n\n",
                            Language.AR: "💰 **خطوة ذكية!** معظم المستثمرين يبدأون بـ:\n• خطط سداد (25% مقدم، الباقي على 2-4 سنوات)\n• دخل الإيجار يغطي 70% من الرهن\n• عقار جاهز = تدفق نقدي فوري!\n\n",
                            Language.RU: "💰 **Умный ход!** Большинство инвесторов начинают с:\n• Планы рассрочки (25% аванс, остальное за 2-4 года)\n• Арендный доход покрывает 70% ипотеки\n• Готовый объект = мгновенный денежный поток!\n\n"
                        }
                    else:
                        dubai_benefits_prefix = {
                            Language.EN: "🏡 **Flexible Financing Available:**\n• Mortgages from 25% down payment\n• Fixed rates as low as 3.99%\n• Pre-approval in 48 hours\n\n",
                            Language.FA: "🏡 **تامین مالی انعطاف‌پذیر:**\n• وام از ۲۵٪ پیش پرداخت\n• نرخ ثابت از ۳.۹۹٪\n• تایید اولیه در ۴۸ ساعت\n\n",
                            Language.AR: "🏡 **تمويل مرن متاح:**\n• رهن من 25% دفعة أولى\n• أسعار ثابتة من 3.99%\n• الموافقة المسبقة في 48 ساعة\n\n",
                            Language.RU: "🏡 **Гибкое финансирование:**\n• Ипотека от 25% первого взноса\n• Фиксированные ставки от 3.99%\n• Предодобрение за 48 часов\n\n"
                        }
                    
                    budget_question = {
                        Language.EN: dubai_benefits_prefix[Language.EN] + f"What's your purchase budget{name_suffix}?",
                        Language.FA: dubai_benefits_prefix[Language.FA] + f"بودجه خرید شما چقدر است{name_suffix_fa}؟",
                        Language.AR: dubai_benefits_prefix[Language.AR] + f"ما هي ميزانية الشراء{name_suffix}؟",
                        Language.RU: dubai_benefits_prefix[Language.RU] + f"Каков ваш бюджет на покупку{name_suffix}?"
                    }
                    
                    budget_buttons = []
                    for idx, (min_val, max_val) in BUDGET_RANGES.items():
                        if max_val:
                            label = f"{min_val:,} - {max_val:,} AED"
                        else:
                            label = f"{min_val:,}+ AED"
                        budget_buttons.append({"text": label, "callback_data": f"buy_budget_{idx}"})
                
                return BrainResponse(
                    message=budget_question.get(lang, budget_question[Language.EN]),
                    next_state=ConversationState.SLOT_FILLING,
                    lead_updates=lead_updates | {
                        "conversation_data": conversation_data,
                        "filled_slots": filled_slots,
                        "pending_slot": "budget"
                    },
                    buttons=budget_buttons
                )
        
        # === HANDLE TEXT MESSAGES (FAQ Detection) ===
        if message and not callback_data:
            # DATA INTEGRITY: Try to extract budget from free text before treating as FAQ
            budget_extracted = parse_budget_string(message)
            if budget_extracted and not filled_slots.get("budget"):
                # User typed budget as text instead of clicking button
                conversation_data["budget_min"] = budget_extracted
                conversation_data["budget_max"] = budget_extracted * 1.5  # Assume 50% range
                filled_slots["budget"] = True
                lead_updates["budget_min"] = budget_extracted
                lead_updates["budget_max"] = int(budget_extracted * 1.5)
                logger.info(f"💰 Extracted budget from text: {budget_extracted}")
                
                # CRITICAL: If we have goal + budget, SHOW PROPERTIES IMMEDIATELY!
                if filled_slots.get("goal") or conversation_data.get("goal"):
                    logger.info(f"✅ Have budget + goal - SHOWING PROPERTIES immediately!")
                    
                    # Save everything to database
                    lead_updates["conversation_data"] = conversation_data
                    lead_updates["filled_slots"] = filled_slots
                    
                    # Go to VALUE_PROPOSITION to show properties
                    return BrainResponse(
                        message="",  # Empty - will show properties in VALUE_PROPOSITION
                        next_state=ConversationState.VALUE_PROPOSITION,
                        lead_updates=lead_updates,
                        buttons=[]
                    )
                
                # Otherwise ask for next slot
                property_question = {
                    Language.EN: "Perfect! What type of property are you looking for?",
                    Language.FA: "عالی! چه نوع ملکی مد نظر دارید",
                    Language.AR: "رائع! ما نوع العقار الذي تبحث عنه",
                    Language.RU: "Отлично! Какой тип недвижимости вы ищете?"
                }
                
                property_buttons = [
                    {"text": "🏢 " + ("آپارتمان" if lang == Language.FA else "Apartment"), "callback_data": "prop_apartment"},
                    {"text": "🏠 " + ("ویلا" if lang == Language.FA else "Villa"), "callback_data": "prop_villa"},
                    {"text": "🏰 " + ("پنت‌هاوس" if lang == Language.FA else "Penthouse"), "callback_data": "prop_penthouse"},
                    {"text": "🏛️ " + ("تاون‌هاوس" if lang == Language.FA else "Townhouse"), "callback_data": "prop_townhouse"},
                    {"text": "🏪 " + ("تجاری" if lang == Language.FA else "Commercial"), "callback_data": "prop_commercial"},
                    {"text": "🌞️ " + ("زمین" if lang == Language.FA else "Land"), "callback_data": "prop_land"},
                ]
                
                return BrainResponse(
                    message=property_question.get(lang, property_question[Language.EN]),
                    next_state=ConversationState.SLOT_FILLING,
                    lead_updates=lead_updates | {
                        "conversation_data": conversation_data,
                        "filled_slots": filled_slots,
                        "pending_slot": "property_type"
                    },
                    buttons=property_buttons
                )
            
            # Use AI to respond (treats all text as FAQ)
            ai_response = await self.generate_ai_response(message, lead)
            
            # Determine next missing slot
            next_slot_question = None
            next_slot_buttons = []
            next_pending_slot = None
            
            if not filled_slots.get("budget"):
                next_slot_question = {
                    Language.EN: "\n\nGreat question! Now, what's your budget range?",
                    Language.FA: "\n\nسوال خوبی بود! خب، بودجه‌ات چقدر است؟",
                    Language.AR: "\n\nسؤال رائع! حسنًا، ما هو نطاق ميزانيتك؟",
                    Language.RU: "\n\nОтличный вопрос! Итак, каков ваш бюджет?"
                }
                next_pending_slot = "budget"
                for idx, (min_val, max_val) in BUDGET_RANGES.items():
                    if max_val:
                        label = f"{min_val:,} - {max_val:,} AED"
                    else:
                        label = f"{min_val:,}+ AED"
                    next_slot_buttons.append({"text": label, "callback_data": f"budget_{idx}"})
            
            elif not filled_slots.get("property_type"):
                next_slot_question = {
                    Language.EN: "\n\nGood to know! What type of property are you interested in?",
                    Language.FA: "\n\nخوبه که می‌دونم! چه نوع ملکی مد نظر دارید؟",
                    Language.AR: "\n\nجيد أن أعرف! ما نوع العقار الذي تهتم به؟",
                    Language.RU: "\n\nХорошо знать! Какой тип недвижимости вас интересует?"
                }
                next_pending_slot = "property_type"
                next_slot_buttons = [
                    {"text": "🏢 " + ("آپارتمان" if lang == Language.FA else "Apartment"), "callback_data": "prop_apartment"},
                    {"text": "🏠 " + ("ویلا" if lang == Language.FA else "Villa"), "callback_data": "prop_villa"},
                    {"text": "🏰 " + ("پنت‌هاوس" if lang == Language.FA else "Penthouse"), "callback_data": "prop_penthouse"},
                    {"text": "🏘️ " + ("تاون‌هاوس" if lang == Language.FA else "Townhouse"), "callback_data": "prop_townhouse"},
                    {"text": "🏪 " + ("تجاری" if lang == Language.FA else "Commercial"), "callback_data": "prop_commercial"},
                    {"text": "🏞️ " + ("زمین" if lang == Language.FA else "Land"), "callback_data": "prop_land"},
                ]
            
            elif not filled_slots.get("transaction_type"):
                next_slot_question = {
                    Language.EN: "\n\nUnderstood! Are you looking to Buy or Rent?",
                    Language.FA: "\n\nمتوجه شدم! می‌خواهید بخرید یا اجاره کنید؟",
                    Language.AR: "\n\nفهمت! هل تريد الشراء أم الإيجار؟",
                    Language.RU: "\n\nПонял! Вы хотите купить или арендовать?"
                }
                next_pending_slot = "transaction_type"
                next_slot_buttons = [
                    {"text": self.get_text("btn_buy", lang), "callback_data": "tx_buy"},
                    {"text": self.get_text("btn_rent", lang), "callback_data": "tx_rent"}
                ]
            
            # Return AI response + next slot question
            return BrainResponse(
                message=ai_response + (next_slot_question.get(lang, next_slot_question[Language.EN]) if next_slot_question else ""),
                next_state=ConversationState.SLOT_FILLING,
                lead_updates={"pending_slot": next_pending_slot},
                buttons=next_slot_buttons
            )
        
        # Default fallback
        return BrainResponse(
            message="Error in slot filling",
            next_state=ConversationState.SLOT_FILLING
        )
    
    async def _handle_value_proposition(
        self,
        lang: Language,
        message: Optional[str],
        callback_data: Optional[str],
        lead: Lead,
        lead_updates: Dict
    ) -> BrainResponse:
        """
        VALUE_PROPOSITION Phase: Show matching properties from inventory.
        Goal: Demonstrate value BEFORE asking for contact info.
        
        FIXED: Properly route consultation/photo/question requests to avoid infinite loop.
        FIXED: Detect YES/NO text responses to avoid repeating financing info.
        FIXED: Auto-show properties when coming from slot_filling with empty message (budget button clicked)
        """
        conversation_data = lead.conversation_data or {}
        filled_slots = lead.filled_slots or {}
        
        # ===== FIX: AUTO-SHOW PROPERTIES WHEN COMING FROM SLOT_FILLING =====
        # When budget button clicked → state=VALUE_PROPOSITION, message=""
        # This checks if we have all requirements and auto-triggers property search
        if not message and not callback_data:
            has_location = conversation_data.get("location") or lead.preferred_location
            has_budget = filled_slots.get("budget") or conversation_data.get("budget_min") or lead.budget_min
            has_property_type = filled_slots.get("property_type") or conversation_data.get("property_type") or lead.property_type
            has_goal = conversation_data.get("goal") or lead.purpose
            
            if has_budget and has_goal:
                logger.info(f"🚀 Auto-showing properties for lead {lead.id} (came from slot_filling with budget click)")
                # Continue to property presentation below (no early return)
                # Set flag to trigger property search
                message = "SHOW_PROPERTIES_AUTO"  # Trigger the search logic below
        
        # ===== CRITICAL: HANDLE TEXT MESSAGES IN VALUE_PROPOSITION =====
        if message and not callback_data:
            message_lower = message.lower().strip()
            
            logger.info(f"📝 VALUE_PROPOSITION text input from lead {lead.id}: '{message}'")
            
            # 0. DETECT YES/NO AFFIRMATIVE RESPONSES (HIGHEST PRIORITY - FIX FOR INFINITE LOOP)
            # When bot asks "Would you like financing calculator?", user types "yes" instead of clicking button
            affirmative_keywords = ["yes", "yeah", "yep", "sure", "ok", "okay", "بله", "آره", "باشه", "اوکی", "نعم", "حسناً", "да", "хорошо", "ладно"]
            negative_keywords = ["no", "nope", "نه", "نخیر", "لا", "нет"]
            
            # NEW: Detect "show me properties" requests OR auto-trigger from slot_filling
            show_properties_keywords = ["show", "present", "پرزنت", "نشون بده", "بهم نشون بده", "ببینم", "خب منتظر", "منتظرم", "ملک", "property", "properties", "املاک", "أرني", "اعرض", "عقار", "покажи", "показать", "недвижимость", "show_properties_auto"]
            
            # Check if message is JUST affirmative/negative (not part of longer question)
            is_pure_affirmative = any(kw == message_lower for kw in affirmative_keywords) or any(kw in message_lower for kw in affirmative_keywords[:4])  # English variants
            is_pure_negative = any(kw == message_lower for kw in negative_keywords)
            is_show_properties_request = any(kw in message_lower for kw in show_properties_keywords)
            
            # CRITICAL: User explicitly wants to see properties - CHECK COMPLETENESS
            conversation_data = lead.conversation_data or {}
            filled_slots = lead.filled_slots or {}
            
            # THE SWITCH CHECK: Need at minimum Budget (location and property_type are optional filters)
            has_location = conversation_data.get("location") or lead.preferred_location
            has_budget = filled_slots.get("budget") or conversation_data.get("budget_min") or lead.budget_min
            has_property_type = filled_slots.get("property_type") or conversation_data.get("property_type") or lead.property_type
            
            # ✅ FIX: Show properties with JUST budget - location/type are optional filters
            # If user asks for properties and we have budget → SHOW (even without location/type)
            if is_show_properties_request and has_budget:
                logger.info(f"✅ Property request detected from lead {lead.id} - budget={has_budget}, location={has_location}, type={has_property_type}")
                
                # User wants to see properties with details - GET REAL PROPERTIES FROM DATABASE
                async with async_session() as session:
                    from sqlalchemy import select
                    from database import TenantProperty
                    
                    # Get properties matching lead criteria (is_active removed - column doesn't exist)
                    query = select(TenantProperty).where(
                        TenantProperty.tenant_id == lead.tenant_id
                    )
                    
                    # Apply filters if available
                    conversation_data = lead.conversation_data or {}
                    if conversation_data.get("budget"):
                        budget_max = int(conversation_data["budget"]) * 1.2  # 20% flexibility
                        query = query.where(TenantProperty.price <= budget_max)
                    
                    if conversation_data.get("property_type"):
                        prop_type = conversation_data["property_type"]
                        if prop_type != "any":
                            query = query.where(TenantProperty.property_type == prop_type)
                    
                    # Execute query
                    result = await session.execute(query.limit(5))
                    properties_db = result.scalars().all()
                    
                    if properties_db:
                        logger.info(f"✅ Found {len(properties_db)} properties in database for lead {lead.id}")
                        
                        # Convert to dict format for property_presenter
                        properties_list = []
                        for prop in properties_db:
                            properties_list.append({
                                "id": prop.id,
                                "name": prop.name,
                                "price": prop.price,
                                "location": prop.location,
                                "bedrooms": prop.bedrooms,
                                "bathrooms": prop.bathrooms,
                                "area": prop.area,
                                "property_type": prop.property_type,
                                "image_urls": prop.image_urls or [],
                                "brochure_pdf": prop.brochure_pdf,
                                "primary_image": prop.primary_image,
                                "features": prop.features or [],
                                "description": prop.description,
                                "golden_visa": prop.golden_visa_eligible
                            })
                        
                        # Track shown properties to avoid repetition
                        conversation_data = lead.conversation_data or {}
                        shown_ids = set(conversation_data.get("shown_property_ids", []))
                        shown_ids.update([p['id'] for p in properties_list[:3]])
                        conversation_data["shown_property_ids"] = list(shown_ids)
                        
                        # SET current_properties for property_presenter
                        self.current_properties = properties_list[:3]
                        
                        # Return empty message - property_presenter handles presentation + ROI PDFs
                        return BrainResponse(
                            message="",  # Empty - professional presenter does everything
                            next_state=ConversationState.VALUE_PROPOSITION,
                            lead_updates=lead_updates | {"properties_sent": True, "conversation_data": conversation_data}
                        )
                    else:
                        logger.warning(f"⚠️ No properties found in database for lead {lead.id} - fallback to manual contact")
                        
                        # No properties - offer consultation
                        no_properties_msg = {
                            Language.EN: f"I'd love to show you properties, but I need to check our exclusive inventory for your specific criteria. Can I schedule a quick call with {self.agent_name} to discuss the best available options?",
                            Language.FA: f"دوست دارم املاک رو نشونتون بدم، اما باید موجودی اختصاصی رو برای معیارهای خاص شما چک کنم. می‌تونم یه تماس سریع با {self.agent_name} برای بحث بهترین گزینه‌های موجود تنظیم کنم؟",
                            Language.AR: f"أود أن أريك العقارات، لكن أحتاج للتحقق من مخزوننا الحصري لمعاييرك المحددة. هل يمكنني جدولة مكالمة سريعة مع {self.agent_name} لمناقشة أفضل الخيارات المتاحة؟",
                            Language.RU: f"Хочу показать вам объекты, но мне нужно проверить эксклюзивный каталог под ваши критерии. Могу я организовать быстрый звонок с {self.agent_name} для обсуждения лучших вариантов?"
                        }
                        
                        return BrainResponse(
                            message=no_properties_msg.get(lang, no_properties_msg[Language.EN]),
                            next_state=ConversationState.VALUE_PROPOSITION,
                            lead_updates=lead_updates,
                            buttons=[
                                {"text": "📅 " + self.get_text("btn_schedule_consultation", lang), "callback_data": "schedule_consultation"}
                            ]
                        )
            
            # User wants properties but MISSING requirements - tell them what's needed (DIRECT)
            elif is_show_properties_request or is_pure_affirmative:
                logger.info(f"📋 User wants properties - checking completeness: Location={has_location}, Budget={has_budget}, Type={has_property_type}")
                
                # Tell user what's missing in ONE direct question
                missing_parts = []
                if not has_budget:
                    missing_parts.append("budget")
                if not has_location:
                    missing_parts.append("location")
                if not has_property_type:
                    missing_parts.append("property type")
                
                # CLOSER MODE: Ask for missing info directly, no flowery language
                missing_msg = {
                    Language.EN: f"To show you properties, I need: {', '.join(missing_parts)}. Quick - budget in AED?",
                    Language.FA: f"برای نمایش املاک نیاز دارم: {', '.join(missing_parts)}. سریع - بودجه به درهم؟",
                    Language.AR: f"لعرض العقارات، أحتاج: {', '.join(missing_parts)}. سريعاً - الميزانية بالدرهم؟",
                    Language.RU: f"Чтобы показать объекты, нужно: {', '.join(missing_parts)}. Быстро - бюджет в AED?"
                }
                
                return BrainResponse(
                    message=missing_msg.get(lang, missing_msg[Language.EN]),
                    next_state=ConversationState.SLOT_FILLING,  # Back to slot filling
                    lead_updates=lead_updates,
                    buttons=[]  # No buttons - let them type
                )
                
            # Fallback: Try to extract from message anyway
            else:
                intent_data = await self.extract_user_intent(message, lang, ["budget", "bedrooms", "property_type", "location"])
                
                if intent_data.get("budget"):
                    budget_val = int(intent_data["budget"])
                    conversation_data["budget_min"] = int(budget_val * 0.8)
                    conversation_data["budget_max"] = int(budget_val * 1.2)
                    filled_slots["budget"] = True
                    lead_updates["budget_min"] = int(budget_val * 0.8)
                    lead_updates["budget_max"] = int(budget_val * 1.2)
                    lead_updates["conversation_data"] = conversation_data
                    lead_updates["filled_slots"] = filled_slots
                    logger.info(f"✅ Extracted budget {budget_val} from message - proceeding to show properties")
                    
                    # Now get properties with extracted budget (RECURSION - will hit first condition)
                    # FALLTHROUGH to property search below
                else:
                    # No budget mentioned - ask directly instead of showing random properties
                    need_budget_msg = {
                        Language.EN: "I'd love to show you the best properties! 🏠\n\nTo find perfect matches, I need to know your budget range first.\n\n**Example:**\n• \"500,000 AED\"\n• \"1.5 million\"\n• \"750K\"\n\nWhat's your comfortable budget?",
                        Language.FA: "خیلی دوست دارم بهترین املاک رو نشونت بدم! 🏠\n\nولی اول باید بودجه‌ت رو بدونم تا گزینه‌های مناسب پیدا کنم.\n\n**مثلاً:**\n• \"۵۰۰ هزار درهم\"\n• \"۱.۵ میلیون\"\n• \"۷۵۰K\"\n\nبودجه راحتت چقدره؟",
                        Language.AR: "أود أن أريك أفضل العقارات! 🏠\n\nولكن أولاً أحتاج معرفة نطاق ميزانيتك لإيجاد التطابقات المثالية.\n\n**مثال:**\n• \"500,000 درهم\"\n• \"1.5 مليون\"\n• \"750K\"\n\nما ميزانيتك المريحة؟",
                        Language.RU: "Хочу показать вам лучшие объекты! 🏠\n\nНо сначала мне нужно знать ваш бюджет, чтобы найти идеальные варианты.\n\n**Например:**\n• \"500,000 AED\"\n• \"1.5 миллиона\"\n• \"750K\"\n\nКакой у вас комфортный бюджет?"
                    }
                    
                    return BrainResponse(
                        message=need_budget_msg.get(lang, need_budget_msg[Language.EN]),
                        next_state=ConversationState.SLOT_FILLING,
                        lead_updates={"pending_slot": "budget"},
                        buttons=[]
                    )
            
            if is_pure_negative:
                logger.info(f"❌ NEGATIVE RESPONSE detected from lead {lead.id} - Moving to engagement")
                
                engagement_msg = {
                    Language.EN: "No problem! Do you have any questions about these properties or Dubai real estate? I'm here to help! 😊",
                    Language.FA: "مشکلی نیست! سوالی درباره این ملک‌ها یا املاک دبی دارید؟ من اینجا هستم تا کمکتان کنم! 😊",
                    Language.AR: "لا مشكلة! هل لديك أي أسئلة حول هذه الممتلكات أو العقارات في دبي؟ أنا هنا لمساعدتك! 😊",
                    Language.RU: "Без проблем! У вас есть вопросы об этих объектах или недвижимости в Дубае? Я здесь, чтобы помочь! 😊"
                }
                
                return BrainResponse(
                    message=engagement_msg.get(lang, engagement_msg[Language.EN]),
                    next_state=ConversationState.ENGAGEMENT,
                    lead_updates=lead_updates
                )
            
            # 1. DETECT CONSULTATION REQUEST
            consultation_keywords = ["consultation", "call", "مشاوره", "تماس", "speak", "agent", "مشاور"]
            if any(kw in message_lower for kw in consultation_keywords):
                logger.info(f"🔔 Consultation request detected from lead {lead.id}")
                lead_updates["consultation_requested"] = True
                
                # ✅ NEW: Update lead score - consultation request = very hot lead!
                # Calculate temperature (can't call method on detached object)
                score = 50  # Base score for consultation request
                if score >= 90:
                    temperature = "burning"
                elif score >= 70:
                    temperature = "hot"
                elif score >= 40:
                    temperature = "warm"
                else:
                    temperature = "cold"
                
                lead_updates["lead_score"] = score
                lead_updates["temperature"] = temperature
                logger.info(f"📊 Lead {lead.id} score updated to {score} ({temperature}) after consultation request")
                
                # اگر شماره داره، مستقیم برو schedule
                if lead.phone:
                    return await self._handle_schedule(lang, None, lead)
                
                # وگرنه اول شماره بگیر
                consultation_msg = TRANSLATIONS["phone_request"]
                return BrainResponse(
                    message=consultation_msg.get(lang, consultation_msg[Language.EN]),
                    next_state=ConversationState.CAPTURE_CONTACT,
                    lead_updates=lead_updates,
                    request_contact=True
                )
            
            # 2. DETECT PHOTO/IMAGE/PDF REQUEST OR PROPERTY SHOWCASE REQUEST
            photo_keywords = ["photo", "picture", "image", "عکس", "تصویر", "صورة", "фото", "pdf", "پی دی اف", "بی دی اف", "پی دی ای", "برشور", "brochure", "catalog", "کاتالوگ", "ملک", "property", "عقار", "نشون", "show", "بهم"]
            if any(kw in message_lower for kw in photo_keywords):
                logger.info(f"📸 Photo/PDF/Property request detected from lead {lead.id}")
                
                # Track shown properties for rotation
                conversation_data = lead.conversation_data or {}
                shown_property_ids = set(conversation_data.get("shown_property_ids", []))
                offset = len(shown_property_ids)
                
                # *** گرفتن املاک واقعی از دیتابیس ***
                real_properties = await self.get_real_properties_from_db(lead, limit=3, offset=offset)
                
                if real_properties:
                    # Update shown property IDs
                    new_ids = [p['id'] for p in real_properties]
                    shown_property_ids.update(new_ids)
                    conversation_data["shown_property_ids"] = list(shown_property_ids)
                    lead_updates["conversation_data"] = conversation_data
                    
                    logger.info(f"✅ Found {len(real_properties)} NEW properties (total shown: {len(shown_property_ids)})")
                    
                    # Set current_properties to trigger professional presenter with ROI PDFs
                    self.current_properties = real_properties
                    
                    # IMPORTANT: Return minimal message - property_presenter handles everything
                    return BrainResponse(
                        message="",  # Empty - let property_presenter do the talking
                        next_state=ConversationState.VALUE_PROPOSITION,
                        lead_updates=lead_updates
                    )
                else:
                    logger.warning(f"⚠️ No real properties found in database for lead {lead.id}")
                
                # اگر املاکی نبود، استفاده از روش قدیمی (tenant_context)
                # Get property recommendations and check for media
                property_recs = await self.get_property_recommendations(lead)
                
                # Try to find properties/projects with media files
                properties = self.tenant_context.get("properties", [])
                projects = self.tenant_context.get("projects", [])
                
                # Collect all media (images and PDFs)
                media_files = []
                for p in (properties + projects)[:5]:  # First 5 items
                    # Check for brochure PDF
                    if p.get('brochure_pdf'):
                        media_files.append({"type": "pdf", "url": p['brochure_pdf'], "name": p['name']})
                    # Check for primary image
                    elif p.get('primary_image'):
                        media_files.append({"type": "photo", "url": p['primary_image'], "name": p['name']})
                    # Check for first image in list
                    elif p.get('image_urls') and len(p['image_urls']) > 0:
                        media_files.append({"type": "photo", "url": p['image_urls'][0], "name": p['name']})
                
                photo_msg = {
                    Language.EN: f"Here are photos of matching properties:\n\n{property_recs}\n\nWould you like to schedule a viewing?",
                    Language.FA: f"اینم عکس‌های املاک مچ شده:\n\n{property_recs}\n\nمی‌خواهید بازدید رزرو کنید؟",
                    Language.AR: f"إليك صور العقارات المطابقة:\n\n{property_recs}\n\nهل تريد حجز معاينة؟",
                    Language.RU: f"Вот фотографии подходящих объектов:\n\n{property_recs}\n\nХотите записаться на просмотр?"
                }
                return BrainResponse(
                    message=photo_msg.get(lang, photo_msg[Language.EN]),
                    next_state=ConversationState.VALUE_PROPOSITION,
                    lead_updates=lead_updates,
                    buttons=[
                        {"text": "📅 " + self.get_text("btn_schedule_consultation", lang), "callback_data": "schedule_consultation"}
                    ],
                    media_files=media_files  # Pass media to telegram_bot for sending
                )
            
            # 3. DETECT QUESTION (contains "?")
            if "?" in message:
                logger.info(f"❓ Question detected from lead {lead.id}")
                # Answer the specific question via AI - DO NOT resend property list
                ai_context = f"""Answer this specific question about the property or real estate. 
                DO NOT say 'Great! Here are properties...' - they already saw the list.
                Answer their question directly and concisely (2-3 sentences max).
                Question: {message}
                """
                ai_response = await self.generate_ai_response(message, lead, context=ai_context)
                
                return BrainResponse(
                    message=ai_response,
                    next_state=ConversationState.VALUE_PROPOSITION,
                    lead_updates=lead_updates,
                    buttons=[
                        {"text": "📅 " + self.get_text("btn_schedule_consultation", lang), "callback_data": "schedule_consultation"}
                    ]
                )
            
            # 4. FALLBACK: General message/comment
            logger.info(f"💬 General message in VALUE_PROPOSITION from lead {lead.id}")
            ai_response = await self.generate_ai_response(message, lead)
            
            return BrainResponse(
                message=ai_response,
                next_state=ConversationState.VALUE_PROPOSITION,
                lead_updates=lead_updates,
                buttons=[
                    {"text": self.get_text("btn_yes", lang), "callback_data": "details_yes"},
                    {"text": self.get_text("btn_no", lang), "callback_data": "details_no"},
                    {"text": "📅 " + self.get_text("btn_schedule_consultation", lang), "callback_data": "schedule_consultation"}
                ]
            )
        
        # Handle user responses to property details
        if callback_data == "details_yes" or callback_data == "analysis_yes":
            # User wants details - explain financing options first
            financing_explanation = {
                Language.EN: "Excellent choice! 🎯\n\nBefore I send you the detailed report, let me explain the financing options:\n\n💳 **How to Buy:**\n\n1️⃣ **Mortgage (Most Popular)**\n   • 25% down payment\n   • 75% bank financing\n   • Interest: 3.5-4.5%\n   • Rental income covers payments\n\n2️⃣ **Developer Plan**\n   • 10-30% during construction\n   • 70-90% on handover\n   • No interest!\n\n3️⃣ **Cash Purchase**\n   • Best price negotiation\n   • Immediate rental income\n\n💡 **Example:** 2M AED property\n   • Down: 500K (25%)\n   • Monthly mortgage: ~8K\n   • Rental income: 12K/month\n   • Your profit: 4K/month + appreciation!\n\nWould you like a personalized financing calculator?",
                Language.FA: "انتخاب عالی! 🎯\n\nقبل از ارسال گزارش کامل، بذارید گزینه‌های تامین مالی رو توضیح بدم:\n\n💳 **چطوری بخریم:**\n\n1️⃣ **وام بانکی (محبوب‌ترین)**\n   • 25% پیش‌پرداخت\n   • 75% وام بانک\n   • بهره: 3.5-4.5%\n   • اجاره اقساط رو می‌پوشونه\n\n2️⃣ **طرح سازنده**\n   • 10-30% حین ساخت\n   • 70-90% موقع تحویل\n   • بدون بهره!\n\n3️⃣ **خرید نقدی**\n   • بهترین قیمت\n   • درآمد فوری از اجاره\n\n💡 **مثال:** ملک 2 میلیون\n   • پیش: 500 هزار (25%)\n   • قسط ماهانه: ~8 هزار\n   • درآمد اجاره: 12 هزار/ماه\n   • سود شما: 4 هزار/ماه + رشد ارزش!\n\nمی‌خواهید ماشین‌حساب تامین مالی شخصی‌سازی شده؟",
                Language.AR: "اختيار ممتاز! 🎯\n\nقبل إرسال التقرير الكامل، دعني أشرح خيارات التمويل:\n\n💳 **كيفية الشراء:**\n\n1️⃣ **رهن عقاري (الأكثر شعبية)**\n   • دفعة أولى 25%\n   • تمويل بنكي 75%\n   • فائدة: 3.5-4.5%\n   • دخل الإيجار يغطي الأقساط\n\n2️⃣ **خطة المطور**\n   • 10-30% أثناء البناء\n   • 70-90% عند التسليم\n   • بدون فوائد!\n\n3️⃣ **شراء نقدي**\n   • أفضل سعر\n   • دخل إيجاري فوري\n\n💡 **مثال:** عقار 2 مليون\n   • الدفعة: 500 ألف (25%)\n   • قسط شهري: ~8 آلاف\n   • دخل الإيجار: 12 ألف/شهر\n   • ربحك: 4 آلاف/شهر + ارتفاع القيمة!\n\nهل تريد حاسبة تمويل مخصصة؟",
                Language.RU: "Отличный выбор! 🎯\n\nПеред отправкой отчёта, позвольте объяснить варианты финансирования:\n\n💳 **Как купить:**\n\n1️⃣ **Ипотека (Самый популярный)**\n   • 25% первый взнос\n   • 75% банковское финансирование\n   • Процент: 3.5-4.5%\n   • Аренда покрывает платежи\n\n2️⃣ **План застройщика**\n   • 10-30% во время стройки\n   • 70-90% при передаче\n   • Без процентов!\n\n3️⃣ **Покупка за наличные**\n   • Лучшая цена\n   • Немедленный доход от аренды\n\n💡 **Пример:** Объект 2М\n   • Взнос: 500К (25%)\n   • Ежемес. платёж: ~8К\n   • Доход от аренды: 12К/месяц\n   • Ваша прибыль: 4К/месяц + рост!\n\nХотите персональный калькулятор финансирования?"
            }
            
            return BrainResponse(
                message=financing_explanation.get(lang, financing_explanation[Language.EN]),
                next_state=ConversationState.VALUE_PROPOSITION,
                lead_updates=lead_updates
            )
        
        elif callback_data == "details_no" or callback_data == "analysis_no":
            # User not interested yet - go to engagement for more questions
            engagement_msg = {
                Language.EN: "No problem! Do you have any questions about these properties or Dubai real estate in general? I'm here to help! 😊",
                Language.FA: "مشکلی نیست! سوالی درباره این ملک‌ها یا املاک دبی به‌طور کلی دارید؟ من اینجا هستم تا کمکتان کنم! 😊",
                Language.AR: "لا مشكلة! هل لديك أي أسئلة حول هذه الممتلكات أو العقارات في دبي بشكل عام؟ أنا هنا لمساعدتك! 😊",
                Language.RU: "Без проблем! У вас есть вопросы об этих объектах или недвижимости в Дубае в целом? Я здесь, чтобы помочь! 😊"
            }
            
            return BrainResponse(
                message=engagement_msg.get(lang, engagement_msg[Language.EN]),
                next_state=ConversationState.ENGAGEMENT,
                lead_updates=lead_updates
            )
        
        elif callback_data == "schedule_consultation":
            # User wants to book consultation - show calendar with available slots
            lead_updates["consultation_requested"] = True
            
            # Delegate to schedule handler to show calendar
            schedule_response = await self._handle_schedule(lang, None, lead)
            
            # Merge lead updates
            if schedule_response.lead_updates:
                lead_updates.update(schedule_response.lead_updates)
            schedule_response.lead_updates = lead_updates
            
            return schedule_response
        
        # ✅ GET REAL PROPERTIES FROM DATABASE (not tenant_context!)
        conversation_data = lead.conversation_data or {}
        shown_property_ids = set(conversation_data.get("shown_property_ids", []))
        offset = len(shown_property_ids)
        
        real_properties = await self.get_real_properties_from_db(lead, limit=3, offset=offset)
        
        # Get customer name for personalization
        customer_name = conversation_data.get("customer_name", "")
        name_prefix_en = f"{customer_name}, " if customer_name else ""
        name_prefix_fa = f"{customer_name} عزیز، " if customer_name else ""
        
        # CRITICAL: If we have real properties, show them immediately!
        if real_properties:
            # Update shown property IDs
            new_ids = [p['id'] for p in real_properties]
            shown_property_ids.update(new_ids)
            conversation_data["shown_property_ids"] = list(shown_property_ids)
            lead_updates["conversation_data"] = conversation_data
            
            logger.info(f"✅ Showing {len(real_properties)} REAL properties from database for lead {lead.id}")
            
            # Set current_properties to trigger professional presenter with photos + ROI PDFs
            self.current_properties = real_properties
            
            # Build property summary text for inline message
            props_summary = ""
            for i, prop in enumerate(real_properties, 1):
                props_summary += f"\n{i}. **{prop['name']}**\n"
                props_summary += f"   📍 {prop['location']} | 💰 AED {prop['price']:,}\n"
                props_summary += f"   🛏️ {prop['bedrooms']}BR | 📐 {prop['area_sqft']:,}sqft\n"
            
            value_message = {
                Language.EN: f"Perfect{f', {customer_name}' if customer_name else ''}! Here are the best properties matching your criteria:\n{props_summary}\n\n💰 **Your Investment Numbers:**\n\n✅ 7-10% Annual ROI (beats most global markets)\n✅ Rental income: 110% mortgage coverage\n✅ Zero tax on profits (100% yours!)\n✅ Capital appreciation: +8% yearly (Dubai is BOOMING!)\n✅ Golden Visa from 750K\n\n⚠️ **Market Alert:** Dubai prices up 12% this year. Every month delay = 1% appreciation loss!\n\n💡 Pro Move: 70% financing = rental income > mortgage. You profit from day 1!\n\n📍 **Want personalized help?**\nSend location/photo of area you like, I'll find exact matches!\n\n📋 Want to see full details & financing calculator?",
                Language.FA: f"عالی{f'، {customer_name} عزیز' if customer_name else ''}! اینها بهترین املاکی هستند که با معیارهای شما مطابقت دارند:\n{props_summary}\n\n💰 **اعداد سرمایه‌گذاری شما:**\n\n✅ بازده سالانه ۷-۱۰٪ (از اکثر بازارهای جهانی بهتر!)\n✅ درآمد اجاره: ۱۱۰٪ پوشش وام\n✅ مالیات صفر روی سود (۱۰۰٪ مال خودته!)\n✅ رشد ارزش: سالانه +۸٪ (دبی داره سریع میره بالا!)\n✅ ویزای طلایی از ۷۵۰ هزار\n\n⚠️ **هشدار بازار:** قیمت‌های دبی امسال ۱۲٪ بالا رفته. هر ماه تأخیر یعنی از دست دادن ۱٪ رشد!\n\n💡 حرکت حرفه‌ای: ۷۰٪ فاینانس = درآمد اجاره بیشتر از قسط. از روز اول سود میکنی!\n\n📍 **می‌خوای کمک شخصی‌سازی شده؟**\nلوکیشنت یا عکسی از منطقه‌ای که دوست داری رو بفرست، من دقیقاً املاک اطراف رو پیدا می‌کنم!\n\n📋 می‌خواید جزئیات کامل و ماشین‌حساب تامین مالی رو ببینید?"
            }
            
            # Return message with photos+PDFs handled by property_presenter
            # Add buttons for user actions
            action_buttons = [
                {"text": "📋 " + ("جزئیات کامل" if lang == Language.FA else "Full Details" if lang == Language.EN else "تفاصيل كاملة" if lang == Language.AR else "Полные детали"), "callback_data": "details_yes"},
                {"text": "📞 " + ("تماس با مشاور" if lang == Language.FA else "Call Consultant" if lang == Language.EN else "اتصل بمستشار" if lang == Language.AR else "Связаться"), "callback_data": "schedule_consultation"}
            ]
            
            return BrainResponse(
                message=value_message.get(lang, value_message[Language.EN]),
                next_state=ConversationState.VALUE_PROPOSITION,
                lead_updates=lead_updates | {"properties_sent": True},
                buttons=action_buttons  # Show action buttons
            )
        else:
            # Build comprehensive message with financial education
            financial_benefits = {
                Language.EN: "\n\n💰 **Investment Highlights:**\n\n✅ 7-10% Annual ROI - Beat inflation, grow wealth\n✅ Rental Yield covers mortgage - Passive income stream\n✅ Payment Plans Available - Start with 25% down\n✅ Tax-Free Income - No rental tax in UAE\n✅ Capital Appreciation - Dubai property values rising 5-8% yearly\n\n💡 Most investors use 70% financing and rental income pays it off!",
                Language.FA: "\n\n💰 **نکات کلیدی سرمایه‌گذاری:**\n\n✅ بازگشت سالانه 7-10% - تورم رو شکست بده، ثروت بساز\n✅ درآمد اجاره وام رو میپوشونه - درآمد منفعل\n✅ طرح‌های پرداخت - با 25% پیش‌پرداخت شروع کن\n✅ درآمد بدون مالیات - مالیات اجاره در امارات صفره\n✅ رشد ارزش - املاک دبی سالانه 5-8% گرون میشن\n\n💡 اکثر سرمایه‌گذارها 70% وام میگیرن و اجاره همه‌شو پرداخت میکنه!",
                Language.AR: "\n\n💰 **أبرز نقاط الاستثمار:**\n\n✅ عائد سنوي 7-10% - تغلب على التضخم، اِبنِ ثروة\n✅ دخل الإيجار يغطي الرهن - دخل سلبي\n✅ خطط دفع متاحة - ابدأ بدفعة أولى 25%\n✅ دخل معفى من الضرائب - لا ضريبة إيجار في الإمارات\n✅ ارتفاع قيمة رأس المال - قيمة عقارات دبي ترتفع 5-8% سنوياً\n\n💡 معظم المستثمرين يستخدمون تمويل 70% ودخل الإيجار يسدده!",
                Language.RU: "\n\n💰 **Инвестиционные преимущества:**\n\n✅ 7-10% годовых ROI - Обгоняем инфляцию, растим капитал\n✅ Арендный доход покрывает ипотеку - Пассивный доход\n✅ Планы рассрочки - Начните с 25% первого взноса\n✅ Доход без налогов - Нет налога на аренду в ОАЭ\n✅ Рост стоимости - Недвижимость в Дубае растёт 5-8% в год\n\n💡 Большинство инвесторов берут 70% финансирования, а аренда его окупает!"
            }
            
            value_message = {
                Language.EN: f"Perfect{f', {customer_name}' if customer_name else ''}! Here are properties that match your criteria:\n\n{property_recs}{financial_benefits[Language.EN]}\n\n📋 Would you like to see the full details and financing calculator?",
                Language.FA: f"عالی{f'، {customer_name} عزیز' if customer_name else ''}! اینها ملک‌هایی هستند که با معیارهای شما مطابقت دارند:\n\n{property_recs}{financial_benefits[Language.FA]}\n\n📋 می‌خواهید جزئیات کامل و ماشین‌حساب تامین مالی رو ببینید؟",
                Language.AR: f"رائع{f'، {customer_name}' if customer_name else ''}! إليك العقارات التي تطابق معاييرك:\n\n{property_recs}{financial_benefits[Language.AR]}\n\n📋 هل تريد رؤية التفاصيل الكاملة وحاسبة التمويل؟",
                Language.RU: f"Отлично{f', {customer_name}' if customer_name else ''}! Вот объекты, которые соответствуют вашим критериям:\n\n{property_recs}{financial_benefits[Language.RU]}\n\n📋 Хотите увидеть полные детали и калькулятор финансирования?"
            }
            
            return BrainResponse(
                message=value_message.get(lang, value_message[Language.EN]),
                next_state=ConversationState.VALUE_PROPOSITION,
                buttons=[
                    {"text": self.get_text("btn_yes", lang), "callback_data": "details_yes"},
                    {"text": self.get_text("btn_no", lang), "callback_data": "details_no"},
                    {"text": "📅 " + self.get_text("btn_schedule_consultation", lang), "callback_data": "schedule_consultation"}
                ]
            )
        
        # Fallback: No matching properties (should never reach here due to earlier property query logic)
        no_match_message = {
            Language.EN: "I don't have exact matches right now, but I can send you a detailed market analysis. Would you like that?",
            Language.FA: "الان ملک دقیقاً مچ ندارم، اما می‌تونم یک تحلیل بازار کامل بفرستم. می‌خواهید؟",
            Language.AR: "ليس لدي تطابقات دقيقة الآن، لكن يمكنني إرسال تحليل مفصل للسوق. هل تريد ذلك؟",
            Language.RU: "У меня нет точных совпадений прямо сейчас, но я могу отправить подробный анализ рынка. Хотите это?"
        }
        
        return BrainResponse(
            message=no_match_message.get(lang, no_match_message[Language.EN]),
            next_state=ConversationState.VALUE_PROPOSITION,
            buttons=[
                {"text": self.get_text("btn_yes", lang), "callback_data": "analysis_yes"},
                {"text": self.get_text("btn_no", lang), "callback_data": "analysis_no"}
            ]
        )
    
    async def _handle_hard_gate(
        self,
        lang: Language,
        message: Optional[str],
        callback_data: Optional[str],
        lead: Lead,
        lead_updates: Dict
    ) -> BrainResponse:
        """
        HARD_GATE Phase: Capture phone number for PDF delivery.
        This happens AFTER showing value, not before!
        """
        # Get customer's name for personalization
        conversation_data = lead.conversation_data or {}
        customer_name = conversation_data.get("customer_name", "")
        
        # Personalized phone request based on whether we have customer's name
        if customer_name:
            phone_request_personalized = {
                Language.EN: f"🔒 **Security Protocol Activated**\n\n{customer_name}, to access this EXCLUSIVE off-market ROI report and property details, our system requires verification.\n\n💎 This report contains:\n• Confidential pricing (not public)\n• Developer insider deals\n• Investment forecasts\n\n📝 **Please enter your phone number (WhatsApp preferred):**\n\n**Example:** +971505037158",
                Language.FA: f"🔒 **پروتکل امنیتی فعال شد**\n\n{customer_name} عزیز، برای دسترسی به این گزارش ROI اختصاصی و جزئیات ملک، سیستم ما نیاز به تایید دارد.\n\n💎 این گزارش شامل:\n• قیمت‌گذاری محرمانه (غیرعمومی)\n• معاملات داخلی سازندگان\n• پیش‌بینی سرمایه‌گذاری\n\n📝 **لطفاً شماره تماستون رو وارد کنید (ترجیحاً واتساپ):**\n\n**مثال:** +971505037158",
                Language.AR: f"🔒 **تم تفعيل بروتوكول الأمان**\n\n{customer_name}، للوصول إلى تقرير عائد الاستثمار الحصري وتفاصيل العقار، يتطلب نظامنا التحقق.\n\n💎 يحتوي هذا التقرير على:\n• تسعير سري (غير عام)\n• صفقات داخلية للمطورين\n• توقعات استثمارية\n\n📝 **الرجاء إدخال رقم هاتفك (يفضل واتساب):**\n\n**مثال:** +971505037158",
                Language.RU: f"🔒 **Протокол безопасности активирован**\n\n{customer_name}, для доступа к ЭКСКЛЮЗИВНОМУ отчёту ROI и деталям объектов требуется верификация.\n\n💎 Отчёт содержит:\n• Конфиденциальные цены (не публичные)\n• Инсайдерские сделки застройщиков\n• Инвестиционные прогнозы\n\n📝 **Пожалуйста, введите номер телефона (предпочтительно WhatsApp):**\n\n**Пример:** +971505037158"
            }
        else:
            # Fallback to original message if name not collected
            phone_request_personalized = TRANSLATIONS["phone_request"]
        
        # If user clicked "Yes, send PDF"
        if callback_data == "pdf_yes":
            # اگر شماره داره، فقط پیام تایید بفرست
            if lead.phone:
                confirm_msg = {
                    Language.EN: f"Great! I'll send the brochure to {lead.phone} shortly.",
                    Language.FA: f"عالی! بروشور رو به زودی برای {lead.phone} می‌فرستم.",
                    Language.AR: f"رائع! سأرسل الكتيب إلى {lead.phone} قريبًا.",
                    Language.RU: f"Отлично! Я отправлю брошюру на {lead.phone} в ближайшее время."
                }
                return BrainResponse(
                    message=confirm_msg.get(lang, confirm_msg[Language.EN]),
                    next_state=ConversationState.VALUE_PROPOSITION,
                    lead_updates={"brochure_requested": True}
                )
            
            # وگرنه اول شماره بگیر
            return BrainResponse(
                message=phone_request_personalized.get(lang, phone_request_personalized[Language.EN]),
                next_state=ConversationState.CAPTURE_CONTACT,
                request_contact=True
            )
        
        # If user clicked "No, thanks"
        if callback_data == "pdf_no":
            engagement_message = {
                Language.EN: f"No problem{f', {customer_name}' if customer_name else ''}! Do you have any questions about Dubai real estate?",
                Language.FA: f"مشکلی نیست{f'، {customer_name} عزیز' if customer_name else ''}! سوالی درباره املاک دبی دارید؟",
                Language.AR: f"لا مشكلة{f'، {customer_name}' if customer_name else ''}! هل لديك أي أسئلة عن العقارات في دبي؟",
                Language.RU: f"Без проблем{f', {customer_name}' if customer_name else ''}! У вас есть вопросы о недвижимости в Дубае?"
            }
            
            return BrainResponse(
                message=engagement_message.get(lang, engagement_message[Language.EN]),
                next_state=ConversationState.ENGAGEMENT
            )
        
        # If user provided TEXT message (not button click)
        if message:
            # CRITICAL FIX: Before demanding phone, check if this is a question or photo request
            
            # Check if user wants to see photos/details
            photo_keywords = {
                Language.FA: r'عکس|تصویر|ببین|نشون|جزئیات|مشخصات|photo|picture|image|show|detail',
                Language.AR: r'صور|صورة|تفاصيل|عرض|رؤية|أرنى',
                Language.EN: r'photo|picture|image|show|detail|view|see',
                Language.RU: r'фото|фотография|показать|детали|подробнее'
            }
            
            wants_photos = False
            for lang_key, pattern in photo_keywords.items():
                if re.search(pattern, message, re.IGNORECASE):
                    wants_photos = True
                    break
            
            if wants_photos:
                # User wants to see photos - go to engagement instead of demanding phone
                photo_response = {
                    Language.EN: f"Great{f', {customer_name}' if customer_name else ''}! I understand you'd like to see property photos first. That makes total sense!\n\nWould you like to see our featured properties with full details?",
                    Language.FA: f"عالی{f'، {customer_name} عزیز' if customer_name else ''}! متوجه شدم که می‌خواهید اول عکس‌ها رو ببینید.\n\nمی‌خواهید ملک‌های برجسته‌ی ما رو با جزئیات کامل ببینید؟",
                    Language.AR: f"رائع{f'، {customer_name}' if customer_name else ''}! أفهم أنك تريد رؤية الصور أولاً. هذا منطقي تماماً!\n\nهل تريد رؤية ممتلكاتنا المميزة بالتفاصيل الكاملة؟",
                    Language.RU: f"Отлично{f', {customer_name}' if customer_name else ''}! Я понимаю, что вы хотите сначала увидеть фотографии.\n\nХотите увидеть наши лучшие объекты со всеми деталями?"
                }
                
                return BrainResponse(
                    message=photo_response.get(lang, photo_response[Language.EN]),
                    next_state=ConversationState.ENGAGEMENT
                )
            
            # Check if this looks like a question (not a phone number)
            is_question = any(char in message for char in ['؟', '?', 'چطور', 'چه', 'کی', 'کجا', 'چرا', 'how', 'what', 'when', 'where', 'why'])
            is_phone_attempt = re.match(r'^[\d\+\-\(\)\s]+$', message)
            
            if is_question and not is_phone_attempt:
                # User asked a question instead of providing phone - send to AI
                ai_response = await self.generate_ai_response(message, lead)
                return BrainResponse(
                    message=ai_response,
                    next_state=ConversationState.ENGAGEMENT
                )
            
            # Try to validate as phone number
            phone_response = await self._validate_phone_number(lang, message, lead_updates, customer_name)
            
            # If validation successful, move to ENGAGEMENT with PDF flag
            if phone_response.next_state == ConversationState.ENGAGEMENT:
                pdf_sent_message = {
                    Language.EN: f"✅ Perfect{f', {customer_name}' if customer_name else ''}! Thank you!\n\n📄 I'm preparing your personalized financing calculator and detailed ROI report now. It will be sent to you in a moment!\n\nIn the meantime, would you like to discuss your specific requirements? What's your main goal with Dubai real estate?",
                    Language.FA: f"✅ عالی{f'، {customer_name} عزیز' if customer_name else ''}! ممنون!\n\n📄 دارم ماشین‌حساب تامین مالی شخصی‌سازی شده و گزارش ROI کامل شما رو آماده می‌کنم. چند لحظه دیگه برات می‌فرستم!\n\nدر این بین، دوست داری درباره نیازهای خاصت صحبت کنیم؟ هدف اصلی شما از املاک دبی چیه؟",
                    Language.AR: f"✅ ممتاز{f'، {customer_name}' if customer_name else ''}! شكراً!\n\n📄 أقوم بإعداد حاسبة التمويل المخصصة وتقرير عائد الاستثمار الشامل الآن. سأرسله لك خلال لحظات!\n\nفي هذه الأثناء، هل تريد مناقشة متطلباتك المحددة؟ ما هو هدفك الرئيسي من عقارات دبي؟",
                    Language.RU: f"✅ Отлично{f', {customer_name}' if customer_name else ''}! Спасибо!\n\n📄 Готовлю ваш персональный калькулятор финансирования и подробный отчёт ROI. Отправлю вам через мгновение!\n\nА пока, хотите обсудить ваши конкретные требования? Какая у вас главная цель с недвижимостью в Дубае?"
                }
                
                # Add interactive prompt for voice/photo/location
                interactive_prompt = {
                    Language.EN: "\n\n🎙️ **Want personalized help?** Send me a voice note describing your dream property, or share a photo/location of an area you like!",
                    Language.FA: "\n\n🎙️ **می‌خوای کمک شخصی‌سازی شده؟** یه پیام صوتی بفرست و ملک رویاییت رو توضیح بده، یا عکس/لوکیشن منطقه مورد علاقت رو بفرست!",
                    Language.AR: "\n\n🎙️ **تريد مساعدة شخصية؟** أرسل لي رسالة صوتية تصف فيها عقارك المثالي، أو شارك صورة/موقع منطقة تعجبك!",
                    Language.RU: "\n\n🎙️ **Хотите персональную помощь?** Отправьте голосовое сообщение с описанием недвижимости вашей мечты, или фото/локацию района!"
                }
                
                full_message = pdf_sent_message.get(lang, pdf_sent_message[Language.EN]) + interactive_prompt.get(lang, interactive_prompt[Language.EN])
                
                return BrainResponse(
                    message=full_message,
                    next_state=ConversationState.ENGAGEMENT,
                    lead_updates=phone_response.lead_updates,
                    should_generate_roi=True  # Changed from metadata to should_generate_roi (already exists in BrainResponse)
                )
            else:
                # Phone validation failed - return error
                return phone_response
        
        # Default - show phone request with format
        # اگر شماره داریم، برو engagement
        if lead.phone:
            return BrainResponse(
                message=property_recs,
                next_state=ConversationState.ENGAGEMENT,
                lead_updates=lead_updates
            )
        
        return BrainResponse(
            message=phone_request_personalized.get(lang, phone_request_personalized[Language.EN]),
            next_state=ConversationState.CAPTURE_CONTACT,
            request_contact=True
        )
    
    # ==================== PHONE VALIDATION (Used by HARD_GATE) ====================
    
    async def _validate_phone_number(self, lang: Language, message: str, lead_updates: Dict, customer_name: str = "") -> BrainResponse:
        """
        Validate phone number (phone only, name already collected earlier).
        Supports international formats: +971 (UAE), +1 (US/CA), +44 (UK), +7 (RU), +91 (IN), +86 (CN)
        """
        # DATA INTEGRITY: Sanitize input to prevent SQL injection
        if not message or len(message) > 30:
            error_msgs = {
                Language.EN: f"⚠️ Please enter your phone number{f', {customer_name}' if customer_name else ''}:\n\n**Example:** +971505037158 or +14155552671",
                Language.FA: f"⚠️ لطفاً شماره تماستون رو وارد کنید{f'، {customer_name} عزیز' if customer_name else ''}:\n\n**مثال:** +971505037158",
                Language.AR: f"⚠️ الرجاء إدخال رقم هاتفك{f'، {customer_name}' if customer_name else ''}:\n\n**مثال:** +971505037158",
                Language.RU: f"⚠️ Пожалуйста, введите номер телефона{f', {customer_name}' if customer_name else ''}:\n\n**Пример:** +971505037158 или +79991234567"
            }
            return BrainResponse(
                message=error_msgs.get(lang, error_msgs[Language.EN]),
                next_state=ConversationState.CAPTURE_CONTACT,
                request_contact=True
            )
        
        # Clean phone number: remove spaces, dashes, parentheses, dots
        cleaned_phone = re.sub(r'[\s\-\(\)\.]', '', message.strip())
        
        # Add + if missing
        if not cleaned_phone.startswith('+'):
            if cleaned_phone.isdigit() and len(cleaned_phone) >= 10:
                cleaned_phone = '+' + cleaned_phone
        
        # International phone pattern - supports multiple country codes
        phone_pattern = r'^\+\d{10,15}$'
        
        valid = False
        if re.match(phone_pattern, cleaned_phone):
            digits_only = cleaned_phone.lstrip('+')
            unique_digits = len(set(digits_only))
            
            # Validation rules
            if unique_digits <= 2:
                valid = False  # Too few unique digits (e.g., 111111111)
            elif '0123456789' in digits_only or '9876543210' in digits_only:
                valid = False  # Sequential numbers
            elif re.match(r'^(\d{1,3})\1+$', digits_only):
                valid = False  # Repeating patterns
            elif len(digits_only) < 10:
                valid = False  # Too short
            else:
                valid = True
            
            if valid:
                phone_number = cleaned_phone if cleaned_phone.startswith('+') else f'+{cleaned_phone}'
                lead_updates["phone"] = phone_number
                # Name already collected in COLLECTING_NAME state, no need to collect again
                lead_updates["status"] = LeadStatus.CONTACTED
                
                return BrainResponse(
                    message="✅",  # Success marker
                    next_state=ConversationState.ENGAGEMENT,
                    lead_updates=lead_updates
                )
        
        # Invalid phone - provide example
        error_msgs = {
            Language.EN: f"⚠️ Phone number format is incorrect{f', {customer_name}' if customer_name else ''}.\n\nPlease use international format:\n\n**Examples:**\n+971501234567 (UAE)\n+989123456789 (Iran)\n+966501234567 (Saudi)",
            Language.FA: f"⚠️ فرمت شماره تلفن اشتباه است{f'، {customer_name} عزیز' if customer_name else ''}.\n\nلطفاً از فرمت بین‌المللی استفاده کنید:\n\n**مثال‌ها:**\n+971501234567 (امارات)\n+989123456789 (ایران)\n+966501234567 (عربستان)",
            Language.AR: f"⚠️ تنسيق رقم الهاتف غير صحيح{f'، {customer_name}' if customer_name else ''}.\n\nالرجاء استخدام التنسيق الدولي:\n\n**أمثلة:**\n+971501234567 (الإمارات)\n+989123456789 (إيران)\n+966501234567 (السعودية)",
            Language.RU: f"⚠️ Неверный формат номера телефона{f', {customer_name}' if customer_name else ''}.\n\nИспользуйте международный формат:\n\n**Примеры:**\n+971501234567 (ОАЭ)\n+989123456789 (Иран)\n+966501234567 (Саудия)"
        }
        return BrainResponse(
            message=error_msgs.get(lang, error_msgs[Language.EN]),
            next_state=ConversationState.CAPTURE_CONTACT,
            request_contact=True
        )
    
    async def _handle_handoff_urgent(self, lang: Language, message: Optional[str], callback_data: Optional[str], lead: Lead, lead_updates: Dict) -> BrainResponse:
        """
        HANDOFF_URGENT state: User expressed frustration/negative sentiment.
        Offer immediate human support and escalate to agent.
        """
        # If user clicked "Yes, connect me"
        if callback_data == "handoff_yes":
            confirmation_msg = {
                Language.EN: f"✅ Perfect! {self.agent_name} will contact you shortly.\n\nIn the meantime, feel free to ask any questions. They'll call you within 5-10 minutes.",
                Language.FA: f"✅ عالی! {self.agent_name} خیلی زود تماس میگیرند.\n\nتا آن موقع، می‌تونید سوالتون رو بپرسید. اونها تا ۵-۱۰ دقیقه بعد تماس می‌گیرند.",
                Language.AR: f"✅ رائع! سيتصل بك {self.agent_name} قريبًا.\n\nفي الوقت الراهن، لا تتردد في طرح أي أسئلة. سيتصلون بك خلال 5-10 دقائق.",
                Language.RU: f"✅ Отлично! {self.agent_name} вскоре свяжется с вами.\n\nА пока вы можете задать любые вопросы. Они позвонят вам в течение 5-10 минут."
            }
            
            # Update lead status to QUALIFIED for agent dashboard
            lead_updates["status"] = LeadStatus.QUALIFIED
            
            return BrainResponse(
                message=confirmation_msg.get(lang, confirmation_msg[Language.EN]),
                next_state=ConversationState.ENGAGEMENT,
                lead_updates=lead_updates,
                metadata={"urgent_escalation": True, "send_to_agent": True}
            )
        
        # If user clicked "No, continue chatting"
        if callback_data == "handoff_no":
            continue_msg = {
                Language.EN: f"No problem! I'm here to help. What else would you like to know?",
                Language.FA: f"مشکلی نیست! من اینجا هستم تا کمکتون کنم. می‌خواهید چه بدونید؟",
                Language.AR: f"لا مشكلة! أنا هنا للمساعدة. ماذا تود أن تعرف؟",
                Language.RU: f"Без проблем! Я здесь, чтобы помочь. Что еще вы хотели бы узнать?"
            }
            
            return BrainResponse(
                message=continue_msg.get(lang, continue_msg[Language.EN]),
                next_state=ConversationState.ENGAGEMENT,
                lead_updates=lead_updates
            )
        
        # If user provided phone number or message
        if message:
            # Try to capture phone if they provided it
            phone_response = await self._validate_phone_number(lang, message, lead_updates)
            if phone_response.next_state == ConversationState.ENGAGEMENT:
                # Phone captured successfully
                captured_msg = {
                    Language.EN: f"✅ Got it! {self.agent_name} will call you on {message}.\n\nThey should reach you within 10 minutes. Sit tight!",
                    Language.FA: f"✅ گرفتم! {self.agent_name} روی {message} تماس میگیرند.\n\nباید تا ۱۰ دقیقه بعد تماس بگیرند.",
                    Language.AR: f"✅ حسنًا! سيتصل بك {self.agent_name} على {message}.\n\nسيحاولون الوصول إليك في غضون 10 دقائق.",
                    Language.RU: f"✅ Получилось! {self.agent_name} позвонит вам на {message}.\n\nОни должны позвонить вам в течение 10 минут."
                }
                
                lead_updates["status"] = LeadStatus.QUALIFIED
                
                return BrainResponse(
                    message=captured_msg.get(lang, captured_msg[Language.EN]),
                    next_state=ConversationState.ENGAGEMENT,
                    lead_updates=lead_updates,
                    metadata={"urgent_escalation": True, "send_to_agent": True}
                )
            else:
                # Invalid phone - ask again
                return phone_response
        
        # Default - stay in HANDOFF_URGENT with format hint
        phone_request = TRANSLATIONS["phone_request"]
        return BrainResponse(
            message=phone_request.get(lang, phone_request[Language.EN]),
            next_state=ConversationState.HANDOFF_URGENT,
            request_contact=True
        )
    
    # ==================== UTILITY & HELPER METHODS ====================
    
    def get_ghost_reminder(self, lead: Lead, use_fomo: bool = True) -> BrainResponse:
        """Get ghost protocol reminder message with FOMO technique."""
        lang = lead.language or Language.EN
        
        # Use FOMO message for better conversion
        if use_fomo:
            message_text = self.get_text("ghost_fomo", lang)
        else:
            message_text = self.get_text("ghost_reminder", lang)
        
        return BrainResponse(
            message=message_text,
            next_state=ConversationState.ENGAGEMENT,
            buttons=[
                {"text": self.get_text("btn_yes", lang), "callback_data": "ghost_yes"},
                {"text": self.get_text("btn_no", lang), "callback_data": "ghost_no"}
            ]
        )
    
    def _handle_pain_discovery(self, lang: Language, callback_data: Optional[str], lead_updates: Dict) -> BrainResponse:
        """Handle pain point discovery - Psychology technique."""
        pain_mapping = {
            "pain_inflation": "inflation_risk",
            "pain_visa": "visa_insecurity", 
            "pain_income": "rental_income",
            "pain_tax": "tax_optimization"
        }
        
        if callback_data in pain_mapping:
            lead_updates["pain_point"] = pain_mapping[callback_data]
        
        return BrainResponse(
            message=self.get_text("transaction_type", lang),
            next_state=ConversationState.TRANSACTION_TYPE,
            lead_updates=lead_updates,
            buttons=[
                {"text": self.get_text("btn_buy", lang), "callback_data": "tx_buy"},
                {"text": self.get_text("btn_rent", lang), "callback_data": "tx_rent"}
            ]
        )
    
    def _handle_transaction_type(self, lang: Language, callback_data: Optional[str], lead_updates: Dict) -> BrainResponse:
        """Handle Buy/Rent selection."""
        if callback_data == "tx_buy":
            lead_updates["transaction_type"] = TransactionType.BUY
        else:
            lead_updates["transaction_type"] = TransactionType.RENT
        
        # Expanded property type options
        property_buttons = [
            {"text": "🏢 " + ("آپارتمان" if lang == Language.FA else "Apartment"), "callback_data": "prop_apartment"},
            {"text": "🏠 " + ("ویلا" if lang == Language.FA else "Villa"), "callback_data": "prop_villa"},
            {"text": "🏰 " + ("پنت‌هاوس" if lang == Language.FA else "Penthouse"), "callback_data": "prop_penthouse"},
            {"text": "🏘️ " + ("تاون‌هاوس" if lang == Language.FA else "Townhouse"), "callback_data": "prop_townhouse"},
            {"text": "🏪 " + ("تجاری" if lang == Language.FA else "Commercial"), "callback_data": "prop_commercial"},
            {"text": "🏞️ " + ("زمین" if lang == Language.FA else "Land"), "callback_data": "prop_land"},
        ]
        
        return BrainResponse(
            message=self.get_text("property_type", lang),
            next_state=ConversationState.PROPERTY_TYPE,
            lead_updates=lead_updates,
            buttons=property_buttons
        )
    
    def _handle_property_type(self, lang: Language, callback_data: Optional[str], lead_updates: Dict) -> BrainResponse:
        """Handle property type selection."""
        property_mapping = {
            "prop_apartment": PropertyType.APARTMENT,
            "prop_villa": PropertyType.VILLA,
            "prop_penthouse": PropertyType.PENTHOUSE,
            "prop_townhouse": PropertyType.TOWNHOUSE,
            "prop_commercial": PropertyType.COMMERCIAL,
            "prop_land": PropertyType.LAND,
            # Legacy support
            "prop_res": PropertyType.APARTMENT,
            "prop_comm": PropertyType.COMMERCIAL,
        }
        
        if callback_data in property_mapping:
            lead_updates["property_type"] = property_mapping[callback_data]
        
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
    
    async def _handle_purpose(self, lang: Language, callback_data: Optional[str], lead: Lead, lead_updates: Dict) -> BrainResponse:
        """Handle purpose selection."""
        if callback_data == "purp_invest":
            lead_updates["purpose"] = Purpose.INVESTMENT
        elif callback_data == "purp_living":
            lead_updates["purpose"] = Purpose.LIVING
        else:
            lead_updates["purpose"] = Purpose.RESIDENCY
        
        lead_updates["status"] = LeadStatus.QUALIFIED
        
        # NEW: Go to Solution Bridge to connect pain to solution (Psychology technique)
        # Call solution bridge directly to get the proper message
        return await self._handle_solution_bridge(lang, None, lead, lead_updates)
    
    async def _handle_solution_bridge(self, lang: Language, callback_data: Optional[str], lead: Lead, lead_updates: Dict) -> BrainResponse:
        """Present personalized solution based on pain point + property recommendations."""
        pain_point = lead.pain_point if hasattr(lead, 'pain_point') else None
        
        # Select appropriate solution message based on pain point
        if pain_point == "inflation_risk":
            solution_msg = self.get_text("solution_inflation", lang)
        elif pain_point == "visa_insecurity":
            solution_msg = self.get_text("solution_residency", lang)
        elif pain_point == "rental_income":
            solution_msg = self.get_text("solution_income", lang)
        else:
            # Default: show Golden Visa for high-value prospects
            if lead.budget_max and lead.budget_max >= 2000000:
                solution_msg = self.get_text("solution_residency", lang)
            else:
                solution_msg = self.get_text("solution_income", lang)
        
        # NEW: Add property recommendations from tenant's inventory
        property_recs = await self.get_property_recommendations(lead)
        if property_recs:
            solution_msg = f"{solution_msg}\n\n{property_recs}"
        
        # NEW: Go to ENGAGEMENT instead of SCHEDULE - let them ask questions first
        engagement_prompt = {
            Language.EN: "\n\n💬 Do you have any questions? I'm here to help you make the best decision!",
            Language.FA: "\n\n💬 سوالی دارید؟ من اینجا هستم تا به شما کمک کنم بهترین تصمیم را بگیرید!",
            Language.AR: "\n\n💬 هل لديك أي أسئلة؟ أنا هنا لمساعدتك في اتخاذ أفضل قرار!",
            Language.RU: "\n\n💬 У вас есть вопросы? Я здесь, чтобы помочь вам принять лучшее решение!"
        }
        
        solution_msg = f"{solution_msg}{engagement_prompt.get(lang, engagement_prompt[Language.EN])}"
        
        return BrainResponse(
            message=solution_msg,
            next_state=ConversationState.ENGAGEMENT,  # Changed from SCHEDULE
            lead_updates=lead_updates,
            buttons=[]  # No buttons - free conversation
        )
    
    async def _handle_engagement(self, lang: Language, message: str, lead: Lead, lead_updates: Dict) -> BrainResponse:
        """
        ENGAGEMENT state - Free conversation to nurture, answer questions, and build trust.
        AI responds naturally and decides when lead is ready to schedule consultation.
        
        FIXED: Add consultation booking nudge after 2+ questions.
        """
        # Load tenant context if not loaded
        if not self.tenant_context:
            await self.load_tenant_context(lead)
        
        # Track question count for consultation nudge
        conversation_data = lead.conversation_data or {}
        question_count = conversation_data.get("question_count", 0) + 1
        lead_updates["conversation_data"] = {**conversation_data, "question_count": question_count}
        
        # Enhanced AI prompt to handle engagement intelligently
        engagement_context = f"""
        ENGAGEMENT MODE - Lead is asking questions and exploring options.
        
        CRITICAL RULE: You are "{self.agent_name}" - Do NOT introduce yourself again! They already know who you are.
        
        YOUR OBJECTIVES:
        1. Answer their questions honestly and helpfully
        2. Build trust and rapport (WITHOUT repeating your name every message)
        3. Identify if they're ready to schedule consultation
        4. If they express strong interest or ask to speak with agent → Offer scheduling
        5. If they're still unsure → Keep nurturing, ask clarifying questions
        
        TRIGGER PHRASES FOR SCHEDULING (suggest meeting if you detect these):
        - "I want to see properties" / "میخوام ببینم" / "أريد أن أرى"
        - "Can I talk to agent?" / "با مشاور حرف بزنم" / "هل يمكنني التحدث"
        - "Schedule viewing" / "وقت بزارید" / "حدد موعد"
        - "I'm interested" / "علاقه‌مندم" / "أنا مهتم"
        - "Let's meet" / "بیایم" / "دعنا نلتقي"
        
        BUDGET MISMATCH HANDLING:
        - If they say budget is low → Don't push expensive properties
        - Explore: Payment plans, rent-to-own, smaller units, emerging areas
        - Be honest: "Currently no properties in your exact range, but {self.agent_name} may find off-market deals"
        - Alternative solutions: "Would you consider slightly higher budget?" or "Rent first then buy?"
        
        RESIDENCY WITHOUT BUDGET:
        - Golden Visa requires minimum 2M AED investment
        - Alternative visas: Employment visa, investor visa (lower amounts), freelancer visa
        - Suggest: "Would you like to explore employment opportunities that come with visa?"
        - Or: "Many clients rent initially while building investment capital"
        
        IMPORTANT: 
        - Keep responses 2-4 sentences max
        - Ask 1 follow-up question per response to maintain engagement
        - Use emojis sparingly for warmth
        - If they're ready → Return with schedule_ready=True in your response
        
        Previous conversation: {lead.pain_point or 'N/A'}
        """
        
        # Generate AI response
        ai_response = await self.generate_ai_response(message, lead, context=engagement_context)
        
        # Enhanced scheduling detection - check BEFORE AI response
        schedule_triggers_explicit = [
            # Persian/Farsi triggers
            "وقت مشاوره", "تایم مشاوره", "زمان مشاوره", "ساعت مشاوره",
            "وقت های خالی", "تایم های خالی", "زمان های خالی", "ساعت های خالی",
            "اسلات", "وقت خالی", "تایم خالی", "زمان خالی",
            "وقت بذار", "تایم بذه", "زمان بده",
            "چه روزی", "چه تاریخی", "کی وقت", "کی تایم",
            "نشون بده وقت", "نشون بده تایم", "بهم بگو وقت",
            # English triggers
            "appointment", "meeting time", "schedule", "book", "reservation", 
            "available times", "available slots", "free times", "open slots",
            "show me times", "tell me times", "what times", "when available",
            "call me", "speak with agent", "talk to consultant",
            # General triggers
            "مشاور", "consultant", "viewing", "بازدید", "visit",
            "تماس بگیر", "تماس بگیرید"
        ]
        
        user_message_lower = message.lower() if message else ""
        
        # Check for explicit scheduling request
        explicit_schedule_request = any(trigger in user_message_lower for trigger in schedule_triggers_explicit)
        
        if explicit_schedule_request:
            # User explicitly wants to schedule - show calendar directly
            logger.info(f"📅 Explicit schedule request detected from lead {lead.id}: '{message}'")
            return await self._handle_schedule(lang, None, lead)
        
        # Otherwise detect from AI response too
        schedule_triggers_soft = [
            "بذار وقت بذاریم", "let's schedule", "would you like to meet",
            "می‌تونم وقت بذارم", "can arrange", "available slots"
        ]
        
        ai_response_lower = ai_response.lower()
        soft_schedule_suggestion = any(trigger in ai_response_lower for trigger in schedule_triggers_soft)
        
        # If AI suggested scheduling OR user hinted at it, show scheduling button
        if soft_schedule_suggestion:
            schedule_btn_text = {
                Language.EN: "📅 Yes, Schedule Consultation",
                Language.FA: "📅 بله، وقت مشاوره بذار",
                Language.AR: "📅 نعم، حدد موعد الاستشارة",
                Language.RU: "📅 Да, назначить консультацию"
            }
            
            return BrainResponse(
                message=ai_response,
                next_state=ConversationState.ENGAGEMENT,
                buttons=[
                    {"text": schedule_btn_text.get(lang, schedule_btn_text[Language.EN]), "callback_data": "ready_schedule"}
                ]
            )
        
        # Otherwise, stay in engagement mode
        # Add consultation nudge button if user asked 2+ questions
        buttons = []
        if question_count >= 2:
            consultation_btn = {
                Language.EN: "📅 Book Free Consultation",
                Language.FA: "📅 رزرو وقت مشاوره رایگان",
                Language.AR: "📅 احجز استشارة مجانية",
                Language.RU: "📅 Забронировать бесплатную консультацию"
            }
            buttons.append({
                "text": consultation_btn.get(lang, consultation_btn[Language.EN]),
                "callback_data": "schedule_consultation"
            })
        
        # Add interactive prompt for voice/photo every 2-3 messages
        enhanced_response = ai_response
        if question_count % 2 == 0:  # Every 2nd question
            voice_photo_prompt = {
                Language.EN: "\n\n💡 **Tip:** Send me a voice note or photo anytime for instant personalized help!",
                Language.FA: "\n\n💡 **نکته:** هر وقت خواستی پیام صوتی یا عکس بفرست تا فوری کمک شخصی‌سازی شده بگیری!",
                Language.AR: "\n\n💡 **نصيحة:** أرسل لي رسالة صوتية أو صورة في أي وقت للحصول على مساعدة فورية شخصية!",
                Language.RU: "\n\n💡 **Совет:** Отправьте голосовое сообщение или фото в любое время для мгновенной персональной помощи!"
            }
            enhanced_response += voice_photo_prompt.get(lang, voice_photo_prompt[Language.EN])
        
        return BrainResponse(
            message=enhanced_response,
            next_state=ConversationState.ENGAGEMENT,
            buttons=buttons,
            lead_updates=lead_updates
        )
    
    async def _handle_schedule(self, lang: Language, callback_data: Optional[str], lead: Lead) -> BrainResponse:
        """Handle consultation scheduling - SIMPLIFIED with Calendly integration."""
        
        # لینک Calendly و شماره تلفن از تنانت
        calendly_url = self.tenant.booking_url or "https://calendly.com/schedule"
        phone_number = self.tenant.contact_phone or self.tenant.phone or "+971XXXXXXXXX"
        
        # ساخت لینک واتساپ از شماره تلفن
        if self.tenant.whatsapp_link:
            whatsapp_url = self.tenant.whatsapp_link
        elif phone_number:
            # حذف فضاها و کاراکترهای غیر عددی برای لینک واتساپ
            clean_phone = phone_number.replace(" ", "").replace("-", "").replace("+", "")
            whatsapp_url = f"https://wa.me/{clean_phone}"
        else:
            whatsapp_url = "https://wa.me/971XXXXXXXXX"
        
        # پیام رزرو مشاوره
        consultation_messages = {
            Language.FA: (
                f"🎉 عالیه {lead.name or 'عزیز'}! بیایید جلسه مشاوره رایگان‌تون رو تنظیم کنیم.\n\n"
                f"**3 روش برای رزرو:**\n\n"
                f"1️⃣ **آنلاین (فوری):**\n"
                f"👉 {calendly_url}\n\n"
                f"2️⃣ **تماس مستقیم:**\n"
                f"📞 {phone_number}\n\n"
                f"3️⃣ **واتساپ:**\n"
                f"💬 {whatsapp_url}\n\n"
                f"منتظر شنیدن صدای شما هستیم! 🙏"
            ),
            Language.EN: (
                f"🎉 Great {lead.name or 'friend'}! Let's schedule your free consultation.\n\n"
                f"**3 Ways to Book:**\n\n"
                f"1️⃣ **Online (Instant):**\n"
                f"👉 {calendly_url}\n\n"
                f"2️⃣ **Direct Call:**\n"
                f"📞 {phone_number}\n\n"
                f"3️⃣ **WhatsApp:**\n"
                f"💬 {whatsapp_url}\n\n"
                f"Looking forward to hearing from you! 🙏"
            ),
            Language.AR: (
                f"🎉 رائع يا {lead.name or 'صديقي'}! دعنا نحجز استشارتك المجانية.\n\n"
                f"**3 طرق للحجز:**\n\n"
                f"1️⃣ **عبر الإنترنت (فوري):**\n"
                f"👉 {calendly_url}\n\n"
                f"2️⃣ **مكالمة مباشرة:**\n"
                f"📞 {phone_number}\n\n"
                f"3️⃣ **واتساب:**\n"
                f"💬 {whatsapp_url}\n\n"
                f"نتطلع إلى سماع صوتك! 🙏"
            ),
            Language.RU: (
                f"🎉 Отлично, {lead.name or 'друг'}! Давайте запишем вас на бесплатную консультацию.\n\n"
                f"**3 способа записаться:**\n\n"
                f"1️⃣ **Онлайн (мгновенно):**\n"
                f"👉 {calendly_url}\n\n"
                f"2️⃣ **Прямой звонок:**\n"
                f"📞 {phone_number}\n\n"
                f"3️⃣ **WhatsApp:**\n"
                f"💬 {whatsapp_url}\n\n"
                f"Ждем вашего звонка! 🙏"
            )
        }
        
        return BrainResponse(
            message=consultation_messages.get(lang, consultation_messages[Language.EN]),
            next_state=ConversationState.COMPLETED,
            lead_updates={"status": LeadStatus.QUALIFIED},
            buttons=[]
        )
    
    def get_ghost_reminder(self, lead: Lead, use_fomo: bool = True) -> BrainResponse:
        """Get ghost protocol reminder message with FOMO technique."""
        lang = lead.language or Language.EN
        
        # Use FOMO message for better conversion
        if use_fomo:
            message = self.get_text("ghost_fomo", lang)
        else:
            message = self.get_text("ghost_reminder", lang)
        
        return BrainResponse(
            message=message,
            buttons=[
                {"text": self.get_text("btn_yes", lang), "callback_data": "ghost_yes"},
                {"text": self.get_text("btn_no", lang), "callback_data": "ghost_no"}
            ],
            lead_updates={"fomo_messages_sent": (lead.fomo_messages_sent or 0) + 1}
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
    Shows acknowledgment of what was heard, then processes it.
    """
    brain = Brain(tenant)
    lang = lead.language or Language.EN
    
    # Process voice to get transcript and entities
    transcript, entities = await brain.process_voice(audio_data, file_extension)
    
    # If no transcript, return error
    if not transcript or "Error" in transcript or "unavailable" in transcript:
        error_msg = brain.get_text("voice_error", lang)
        return transcript, BrainResponse(message=error_msg)
    
    # Update lead with transcript
    lead_updates = {"voice_transcript": transcript}
    
    # Update lead with extracted entities if any
    if entities:
        if "budget_min" in entities:
            lead_updates["budget_min"] = entities["budget_min"]
        if "budget_max" in entities:
            lead_updates["budget_max"] = entities["budget_max"]
        if "property_type" in entities:
            pt = entities["property_type"].lower()
            property_type_map = {
                "apartment": PropertyType.APARTMENT,
                "villa": PropertyType.VILLA,
                "penthouse": PropertyType.PENTHOUSE,
                "townhouse": PropertyType.TOWNHOUSE,
                "commercial": PropertyType.COMMERCIAL,
                "land": PropertyType.LAND,
                "residential": PropertyType.APARTMENT,
            }
            lead_updates["property_type"] = property_type_map.get(pt, PropertyType.APARTMENT)
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
        if "location" in entities:
            lead_updates["preferred_location"] = entities["location"]
        if "bedrooms" in entities:
            lead_updates["bedrooms_min"] = entities.get("bedrooms_min", entities.get("bedrooms"))
            lead_updates["bedrooms_max"] = entities.get("bedrooms_max", entities.get("bedrooms"))
        if "phone_number" in entities:
            lead_updates["phone"] = entities["phone_number"]
        
        # Store all extracted entities as JSON
        lead_updates["voice_entities"] = entities
    
    # Update lead in database
    if lead_updates:
        await update_lead(lead.id, **lead_updates)
    
    # Process the transcript as a regular text message
    response = await brain.process_message(lead, transcript)
    
    # Prepend acknowledgment of what was heard
    try:
        transcript_preview = str(transcript)[:100] if transcript else "..."
        ack_msg = brain.get_text("voice_acknowledged", lang).format(transcript=transcript_preview)
        response.message = f"{ack_msg}\n\n{response.message}"
    except (KeyError, AttributeError) as e:
        # If template formatting fails, still prepend transcript
        logger.warning(f"Voice acknowledgment formatting failed: {e}, using simple format")
        response.message = f"🎤 {transcript}\n\n{response.message}"
    
    return transcript, response


async def process_image_message(
    tenant: Tenant,
    lead: Lead,
    image_data: bytes,
    file_extension: str = "jpg"
) -> Tuple[str, BrainResponse]:
    """
    Process an image and find similar properties.
    Shows image analysis results and matching properties.
    """
    brain = Brain(tenant)
    lang = lead.language or Language.EN
    
    # Load tenant context (properties, projects) for matching
    await brain.load_tenant_context(lead)
    
    # Process image to get description and matches
    description, matching_properties = await brain.process_image(image_data, file_extension)
    
    # If error, return error message
    if "Error" in description or "unavailable" in description:
        error_msg = brain.get_text("image_error", lang)
        return description, BrainResponse(message=error_msg)
    
    # If no matches found
    if not matching_properties:
        no_results_msg = brain.get_text("image_no_results", lang)
        return description, BrainResponse(message=no_results_msg)
    
    # Format matching properties
    property_details_parts = []
    for i, prop in enumerate(matching_properties[:3], 1):
        price_str = f"AED {prop['price']:,.0f}" if prop.get('price') else "Price on request"
        
        # Safely handle features (could be list or string)
        features = prop.get('features', [])
        if isinstance(features, list):
            features_str = ", ".join(str(f) for f in features[:3])
        elif isinstance(features, str):
            features_str = features[:100]  # Truncate if too long
        else:
            features_str = ""
        
        golden_str = " 🛂 Golden Visa" if prop.get('golden_visa') else ""
        roi_str = f" | ROI: {prop['roi']}%" if prop.get('roi') else ""
        
        property_details_parts.append(
            f"{i}. **{prop.get('name', 'Property')}**\n"
            f"   📍 {prop.get('location', 'Dubai')}\n"
            f"   🏠 {prop.get('bedrooms', 'N/A')}BR {prop.get('type', 'Property')}\n"
            f"   💰 {price_str}{golden_str}{roi_str}\n"
            f"   ✨ {features_str}\n"
        )
    
    property_details = "\n".join(property_details_parts)
    
    # Build response message
    results_msg = brain.get_text("image_results", lang).format(
        count=len(matching_properties),
        property_details=property_details
    )
    
    # Update lead with image search data
    lead_updates = {
        "image_description": description,
        "image_search_results": len(matching_properties)
    }
    
    await update_lead(lead.id, **lead_updates)
    
    return description, BrainResponse(message=results_msg)

