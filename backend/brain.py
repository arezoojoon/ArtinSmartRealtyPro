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

from database import (
    Lead, Tenant, ConversationState, Language,
    TransactionType, PropertyType, PaymentMethod, Purpose,
    LeadStatus, update_lead, get_available_slots, DayOfWeek,
    PainPoint, get_tenant_context_for_ai
)

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Retry configuration for API calls
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1  # seconds


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
        Language.EN: "👋 Wonderful! I'm so excited to help you discover amazing investment opportunities in Dubai!\n\nDid you know Dubai real estate offers 7-10% rental yields? Let me show you how you can grow your wealth here! 🚀",
        Language.FA: "👋 عالیه! من خیلی هیجان‌زده‌ام که به شما کمک کنم فرصت‌های سرمایه‌گذاری شگفت‌انگیز در دبی را کشف کنید!\n\nمیدونستید املاک دبی ۷-۱۰٪ بازده اجاره دارد؟ بذار بهتون نشون بدم چطور میتونید ثروتتون رو اینجا رشد بدید! 🚀",
        Language.AR: "👋 رائع! أنا متحمس جدًا لمساعدتك في اكتشاف فرص استثمارية مذهلة في دبي!\n\nهل تعلم أن العقارات في دبي توفر عوائد إيجارية 7-10%؟ دعني أريك كيف يمكنك تنمية ثروتك هنا! 🚀",
        Language.RU: "👋 Замечательно! Я так рад помочь вам открыть потрясающие инвестиционные возможности в Дубае!\n\nЗнаете ли вы, что недвижимость в Дубае приносит 7-10% арендной доходности? Позвольте показать, как вы можете приумножить капитал здесь! 🚀"
    },
    "hook_roi": {
        Language.EN: "🏠 Get a FREE ROI Analysis!\n\nSee how much you could earn from Dubai Real Estate investment.\n\nWould you like to receive your personalized report?",
        Language.FA: "🏠 تحلیل بازگشت سرمایه رایگان!\n\nببینید چقدر می‌توانید از سرمایه‌گذاری در املاک دبی درآمد کسب کنید.\n\nآیا می‌خواهید گزارش شخصی‌سازی شده خود را دریافت کنید؟",
        Language.AR: "🏠 احصل على تحليل عائد الاستثمار مجانًا!\n\nاكتشف كم يمكنك أن تكسب من الاستثمار العقاري في دبي.\n\nهل تريد استلام تقريرك المخصص؟",
        Language.RU: "🏠 Получите БЕСПЛАТНЫЙ анализ ROI!\n\nУзнайте, сколько вы можете заработать на недвижимости в Дубае.\n\nХотите получить персональный отчёт?"
    },
    "phone_request": {
        Language.EN: "📱 Great! To send you the personalized ROI report, I'll need your phone number.\n\nPlease share your WhatsApp number:\n\nExample: +971501234567 or +989121234567",
        Language.FA: "📱 عالی! برای ارسال گزارش ROI شخصی‌سازی شده، به شماره تلفن شما نیاز دارم.\n\nلطفاً شماره واتساپ خود را ارسال کنید:\n\nمثال: +971501234567 یا +989121234567",
        Language.AR: "📱 رائع! لإرسال تقرير العائد على الاستثمار المخصص لك، أحتاج إلى رقم هاتفك.\n\nيرجى مشاركة رقم الواتساب الخاص بك:\n\nمثال: +971501234567 أو +989121234567",
        Language.RU: "📱 Отлично! Чтобы отправить вам персональный отчёт ROI, мне нужен ваш номер телефона.\n\nПожалуйста, поделитесь вашим номером WhatsApp:\n\nПример: +971501234567 или +989121234567"
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
    # Pain point buttons
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
        Language.RU: "🛂 Резidency/Виза"
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

BUDGET_RANGES = {
    0: (0, 500000),
    1: (500000, 1000000),
    2: (1000000, 2000000),
    3: (2000000, 5000000),
    4: (5000000, None)
}

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
    schedule_slots: Optional[List[Dict]] = None
    metadata: Optional[Dict[str, Any]] = None  # For PDF delivery, etc.


# ==================== BRAIN CLASS ====================

class Brain:
    """
    The Super Brain - AI Core for ArtinSmartRealty
    Handles all conversation logic, language detection, voice processing,
    and state machine for Turbo Qualification Flow.
    
    NEW: Uses tenant-specific data (properties, projects, knowledge) for personalized responses.
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.agent_name = tenant.name or "ArtinSmartRealty"
        self.tenant_context = None  # Will be loaded on demand
        
        # Initialize Gemini model - use STABLE gemini-1.5-flash (NOT unstable gemini-2.0-flash-exp)
        if GEMINI_API_KEY:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ Initialized Gemini model: gemini-1.5-flash (stable)")
            
            # FIX #11: Validate API access at startup
            try:
                # Test simple generation to ensure API is working
                test_response = self.model.generate_content("Test connection")
                logger.info("✅ Gemini API validation successful - model is accessible")
            except Exception as e:
                logger.error(f"❌ GEMINI API VALIDATION FAILED: {type(e).__name__}: {str(e)}")
                logger.error("⚠️ Bot will fail to generate AI responses - check API key and quotas!")
        else:
            self.model = None
            logger.error("❌ GEMINI_API_KEY not set!")
    
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
                f"  Q: {k['title']}\n  A: {k['content'][:200]}..."
                for k in knowledge[:5]  # Limit to 5 FAQs
            ])
            context_parts.append(f"""
AGENT'S FAQ & POLICIES:
{kb_text}
""")
        
        return "\n".join(context_parts)
    
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
        Process voice message using Gemini's multimodal capabilities.
        Returns transcript and extracted entities.
        """
        if not self.model:
            return "Voice processing unavailable (Gemini API not configured)", {}
        
        try:
            # Save audio temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as temp_audio:
                temp_audio.write(audio_data)
                temp_audio_path = temp_audio.name
            
            try:
                # Upload audio file to Gemini
                audio_file = genai.upload_file(path=temp_audio_path)
                
                # Wait for processing with timeout
                import time
                max_wait = 30  # 30 seconds timeout
                elapsed = 0
                while audio_file.state.name == "PROCESSING" and elapsed < max_wait:
                    time.sleep(1)
                    elapsed += 1
                    audio_file = genai.get_file(audio_file.name)
                
                if audio_file.state.name == "PROCESSING":
                    genai.delete_file(audio_file.name)
                    return "Audio processing timeout - file too large or complex", {}
                
                if audio_file.state.name == "FAILED":
                    genai.delete_file(audio_file.name)
                    return "Could not process audio file", {}
                
                # Generate transcript and extract entities with retry logic
                async def call_gemini_voice():
                    return self.model.generate_content([audio_file, prompt])
                
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
                
                Extract any mentioned budget, location, property preferences, or contact information.
                Return ONLY valid JSON.
                """
                
                try:
                    response = await retry_with_backoff(call_gemini_voice)
                except Exception as e:
                    logger.error(f"❌ Gemini voice API failed after retries: {e}")
                    genai.delete_file(audio_file.name)
                    return "Voice processing temporarily unavailable. Please try again or type your message.", {}
                
                # Clean up
                genai.delete_file(audio_file.name)
                
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
                # Clean up temp file
                import os
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass
                    
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
                # Upload image to Gemini
                image_file = genai.upload_file(path=temp_image_path)
                
                # Wait for processing with timeout
                import time
                max_wait = 30  # 30 seconds timeout
                elapsed = 0
                while image_file.state.name == "PROCESSING" and elapsed < max_wait:
                    time.sleep(1)
                    elapsed += 1
                    image_file = genai.get_file(image_file.name)
                
                if image_file.state.name == "PROCESSING":
                    genai.delete_file(image_file.name)
                    return "Image processing timeout - file too large or complex", []
                
                if image_file.state.name == "FAILED":
                    genai.delete_file(image_file.name)
                    return "Could not process image file", []
                
                # Analyze image and extract features
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
                
                response = self.model.generate_content([image_file, prompt])
                
                # Clean up
                genai.delete_file(image_file.name)
                
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
                except:
                    pass
                    
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
        Uses tenant-specific data (properties, projects, knowledge) for personalized responses.
        
        FIX #10d: Track questions and suggest consultation after 3+ questions
        """
        if not self.model:
            return self.get_text("welcome", lead.language or Language.EN)
        
        try:
            # Load tenant context if not already loaded
            if not self.tenant_context:
                await self.load_tenant_context(lead)
            
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
            
            system_prompt = f"""
            You are an expert AI real estate consultant representing {self.agent_name} from Dubai real estate market.
            
            YOUR NAME: Use ONLY "{self.agent_name}" - NEVER variations like "حامد رضا" if name is "حمیدرضا"
            
            CRITICAL ENGAGEMENT RULES:
            1. ALWAYS respond in {lead.language.value.upper()} language
            2. **NEVER rush to end conversation** - Your goal is to engage, qualify, and nurture the lead
            3. **Ask qualifying questions** to understand their TRUE needs and pain points
            4. **Listen actively** - if they express concerns about budget, NEVER push expensive options
            5. **Adapt your approach** based on their responses:
               - If they say "no money" → Explore payment plans, rent-to-own, or smaller units
               - If they want residency but low budget → Explain minimum investment for Golden Visa (2M AED) and alternative visa options
               - If they're hesitant → Build trust, share success stories, offer free consultation
            6. **Only schedule call when:**
               - Lead is genuinely interested and engaged
               - You've identified their budget, purpose, and location preferences
               - They explicitly ask to speak with agent or need detailed property tour
            
            VISA & RESIDENCY KNOWLEDGE BASE:
            **CRITICAL**: When user asks about residency or visa options, provide these EXACT amounts:
            - 🛂 GOLDEN VISA (10 years): Requires minimum 2,000,000 AED investment in real estate
            - 👨‍💼 2-YEAR INVESTOR VISA: Requires minimum 750,000 AED investment in real estate (POPULAR for budget-conscious investors!)
            - 💼 EMPLOYMENT VISA: Can come with residence sponsorship if user has job offer
            - 👨‍💻 FREELANCER VISA: Available for independent professionals
            - 📊 INVESTMENT PORTFOLIO: Mix of properties + stocks = easier approval path
            
            If user says "I have only 500K-1M AED for residency", respond with:
            "Great! The 2-Year Investor Visa is perfect for you - it requires only 750,000 AED minimum. Plus, you'll earn rental income while building wealth!"
            
            PROPERTY RECOMMENDATIONS:
            7. **Use ONLY actual properties from agent's inventory below**
            8. **Match recommendations to budget** - NEVER suggest 2M AED property to 500K budget lead
            9. If no matching properties in budget:
               - Acknowledge honestly: "Currently we don't have properties in your exact budget range"
               - Offer alternatives: "Would you like to explore payment plans or slightly higher budget options?"
               - Suggest agent can source: "{self.agent_name} can search for off-market deals in your range"
            10. When recommending properties, mention:
                - Name, location, price
                - Key features matching their needs
                - Investment potential (ROI) if purpose is investment
                - Golden Visa eligibility if purpose is residency
            
            ==== AGENT'S INVENTORY (USE ONLY THESE!) ====
            {tenant_data_prompt}
            =============================================
            
            LEAD PROFILE (ONLY USE IF VALUES EXIST - DON'T HALLUCINATE!):
            - Status: {lead.status.value if lead.status else 'new lead'}
            - Budget: {f"{lead.budget_min:,.0f} - {lead.budget_max:,.0f} {lead.budget_currency or 'AED'}" if lead.budget_min and lead.budget_max else 'NOT YET ASKED - Do not assume!'}
            - Purpose: {lead.purpose.value if lead.purpose else 'NOT YET ASKED - Do not assume!'}
            - Property Type: {lead.property_type.value if lead.property_type else 'NOT YET ASKED - Do not assume!'}
            - Location: {lead.preferred_location if lead.preferred_location else 'NOT YET ASKED - Do not assume!'}
            - Pain Point: {lead.pain_point if lead.pain_point else 'NOT YET IDENTIFIED'}
            
            CRITICAL: If a field says "NOT YET ASKED", DO NOT make assumptions or invent data!
            
            CONVERSATION CONTEXT: {context}
            
            RESPONSE STYLE:
            - Warm, consultative, and patient (NOT pushy sales)
            - Acknowledge their concerns before presenting solutions
            - Ask 1-2 follow-up questions per response to keep conversation flowing
            - Use emojis moderately for friendliness
            - Keep responses 2-4 sentences max unless explaining complex topic
            - NEVER say "click on buttons above" or "select one of the options" - This is FREE conversation mode!
            - NEVER repeat the same message - Always respond uniquely to each question
            
            SCHEDULING TRIGGERS (when to suggest meeting):
            - User asks: "وقت مشاوره", "schedule", "meeting", "appointment", "call me", "تماس", "موعد"
            - User shows strong buying intent: "I want to buy", "میخوام بخرم", "ready to invest"
            - User asks for viewing: "can I see", "می‌تونم ببینم", "visit"
            
            When you detect these triggers, offer to schedule immediately!
            """.strip()
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                [system_prompt, f"User says: {user_message}"]
            )
            
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
            # No inventory - generic message
            messages = {
                Language.EN: f"📋 Based on your requirements, {self.agent_name} will prepare a personalized selection of properties for you!",
                Language.FA: f"📋 بر اساس نیازهای شما، {self.agent_name} یک لیست شخصی‌سازی شده از ملک‌ها برای شما آماده خواهد کرد!",
                Language.AR: f"📋 بناءً على متطلباتك، سيقوم {self.agent_name} بإعداد مجموعة مخصصة من العقارات لك!",
                Language.RU: f"📋 На основе ваших требований {self.agent_name} подготовит персональную подборку объектов для вас!"
            }
            return messages.get(lang, messages[Language.EN])
        
        # Build recommendations message
        rec_parts = []
        
        # Recommend matching properties
        if properties:
            if lang == Language.FA:
                rec_parts.append("🏠 **ملک‌های پیشنهادی برای شما:**\n")
            elif lang == Language.AR:
                rec_parts.append("🏠 **العقارات المقترحة لك:**\n")
            elif lang == Language.RU:
                rec_parts.append("🏠 **Рекомендуемые объекты для вас:**\n")
            else:
                rec_parts.append("🏠 **Recommended Properties for You:**\n")
            
            for i, p in enumerate(properties[:3], 1):
                price_str = f"AED {p['price']:,.0f}" if p['price'] else "Price on request"
                features_str = ", ".join(p['features'][:3]) if p['features'] else ""
                golden_str = " 🛂 Golden Visa" if p['golden_visa'] else ""
                
                rec_parts.append(
                    f"{i}. **{p['name']}** - {p['location']}\n"
                    f"   {p['bedrooms']}BR {p['type']} | {price_str}{golden_str}\n"
                    f"   ✨ {features_str}\n"
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
        current_state = lead.conversation_state or ConversationState.START
        
        # ===== SENTIMENT DETECTION - CHECK FOR NEGATIVE TONE =====
        # If user expresses frustration/anger, immediately offer human support
        if message and not callback_data:
            negative_sentiment_keywords = {
                Language.FA: r'کلافه|دیونه|خری|زیادی|اذیت|خسته|بدم|چقدر حرف|دور تا دور|حالم بد',
                Language.AR: r'مسخوط|غاضب|زعلان|تعبت|ملل|بطيء|قاسي|سيئ',
                Language.RU: r'раздосадовано|злой|устал|ужасно|помогите|недовольны|усталь',
                Language.EN: r'annoyed|frustrated|angry|angry|stupid|terrible|help|tired|awful|enough|stop'
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
                    lead_updates={"status": LeadStatus.URGENT},
                    buttons=[
                        {"text": self.get_text("btn_yes", lang), "callback_data": "handoff_yes"},
                        {"text": self.get_text("btn_no", lang), "callback_data": "handoff_no"}
                    ]
                )
        
        # DEBUG LOGGING
        logger.info(f"🔍 process_message - Lead {lead.id}: state={current_state}, message='{message}', callback={callback_data}, lead.lang={lead.language}")
        
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
        
        elif current_state == ConversationState.SCHEDULE or current_state == ConversationState.HANDOFF_SCHEDULE:
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
        
        # After language selection, go directly to WARMUP (new flow)
        warmup_message = {
            Language.EN: f"Great to meet you, {self.agent_name} here! 🎯\n\nAre you looking for Investment, Living, or Residency in Dubai?",
            Language.FA: f"خوشحالم که با شما آشنا شدم، {self.agent_name} هستم! 🎯\n\nبه دنبال سرمایه‌گذاری، زندگی یا اقامت در دبی هستید؟",
            Language.AR: f"سعيد بلقائك، أنا {self.agent_name}! 🎯\n\nهل تبحث عن الاستثمار أم العيش أم الإقامة في دبي؟",
            Language.RU: f"Приятно познакомиться, я {self.agent_name}! 🎯\n\nВы ищете инвестиции, проживание или резиденцию в Дубае?"
        }
        
        return BrainResponse(
            message=warmup_message.get(lang, warmup_message[Language.EN]),
            next_state=ConversationState.WARMUP,
            lead_updates=lead_updates,
            buttons=[
                {"text": "💰 " + ("سرمایه‌گذاری" if lang == Language.FA else "Investment"), "callback_data": "goal_investment"},
                {"text": "🏠 " + ("زندگی" if lang == Language.FA else "Living"), "callback_data": "goal_living"},
                {"text": "🛂 " + ("اقامت" if lang == Language.FA else "Residency"), "callback_data": "goal_residency"}
            ]
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
        WARMUP Phase: Quick rapport building (1-2 questions max)
        Goal: Identify primary objective (Investment, Living, or Residency)
        """
        # If button clicked, capture goal and move to SLOT_FILLING
        if callback_data and callback_data.startswith("goal_"):
            goal = callback_data.replace("goal_", "")
            
            # Store in conversation_data
            conversation_data = lead.conversation_data or {}
            conversation_data["goal"] = goal
            
            # Mark filled_slots
            filled_slots = lead.filled_slots or {}
            filled_slots["goal"] = True
            
            lead_updates["conversation_data"] = conversation_data
            lead_updates["filled_slots"] = filled_slots
            
            # Move to SLOT_FILLING with first question
            next_question = {
                Language.EN: f"Great! Let's find the perfect property for {goal}.\n\nWhat's your budget range?",
                Language.FA: f"عالی! بیایید بهترین ملک را برای {goal} پیدا کنیم.\n\nبودجه‌ات چقدر است؟",
                Language.AR: f"رائع! دعنا نجد العقار المثالي لـ {goal}.\n\nما هو نطاق ميزانيتك؟",
                Language.RU: f"Отлично! Давайте найдем идеальную недвижимость для {goal}.\n\nКаков ваш بюджет?"
            }
            
            # Show budget buttons
            budget_buttons = []
            for idx, (min_val, max_val) in BUDGET_RANGES.items():
                if max_val:
                    label = f"{min_val:,} - {max_val:,} AED"
                else:
                    label = f"{min_val:,}+ AED"
                budget_buttons.append({
                    "text": label,
                    "callback_data": f"budget_{idx}"
                })
            
            return BrainResponse(
                message=next_question.get(lang, next_question[Language.EN]),
                next_state=ConversationState.SLOT_FILLING,
                lead_updates=lead_updates | {"pending_slot": "budget"},
                buttons=budget_buttons
            )
        
        # If text message, use AI to answer FAQ - but DON'T re-ask the goal question
        # They'll click the button when ready
        if message and not callback_data:
            # User sent a text message instead of clicking button
            # Could be: FAQ question, changing language, expressing interest, etc.
            
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
            goal_keywords = {
                "investment": ["سرمایه‌گذاری", "investment", "invest", "استثمار", "инвестиция"],
                "living": ["زندگی", "living", "live", "سكن", "жилье"],
                "residency": ["اقامت", "residency", "visa", "visa", "виза", "تأشيرة"]
            }
            
            message_lower = message.lower()
            for goal, keywords in goal_keywords.items():
                if any(kw.lower() in message_lower or kw in message for kw in keywords):
                    # User specified goal in text - treat as button click
                    return await self._handle_warmup(lang, None, f"goal_{goal}", lead, lead_updates)
            
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
        SLOT_FILLING Phase: Intelligent qualification with FAQ tolerance.
        Required slots: budget, property_type, transaction_type
        KEY FEATURE: If user asks FAQ mid-filling, answer it and return to slot collection.
        VOICE SUPPORT: Extracts entities from voice_entities field (populated by process_voice).
        """
        conversation_data = lead.conversation_data or {}
        filled_slots = lead.filled_slots or {}
        
        # === PRE-FILL FROM VOICE ENTITIES (if available) ===
        voice_entities = lead.voice_entities or {}
        if voice_entities and isinstance(voice_entities, dict):
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
            if callback_data.startswith("budget_"):
                idx = int(callback_data.replace("budget_", ""))
                min_val, max_val = BUDGET_RANGES[idx]
                
                conversation_data["budget_min"] = min_val
                conversation_data["budget_max"] = max_val
                filled_slots["budget"] = True
                lead_updates["budget_min"] = min_val
                lead_updates["budget_max"] = max_val
                
                # Next: Ask property type
                property_question = {
                    Language.EN: "Perfect! What type of property are you looking for?",
                    Language.FA: "عالی! چه نوع ملکی مد نظر دارید؟",
                    Language.AR: "رائع! ما نوع العقار الذي تبحث عنه؟",
                    Language.RU: "Отлично! Какой тип недвижимости вы ищете?"
                }
                
                property_buttons = [
                    {"text": "🏢 " + ("آپارتمان" if lang == Language.FA else "Apartment"), "callback_data": "prop_apartment"},
                    {"text": "🏠 " + ("ویلا" if lang == Language.FA else "Villa"), "callback_data": "prop_villa"},
                    {"text": "🏰 " + ("پنت‌هاوس" if lang == Language.FA else "Penthouse"), "callback_data": "prop_penthouse"},
                    {"text": "🏘️ " + ("تاون‌هاوس" if lang == Language.FA else "Townhouse"), "callback_data": "prop_townhouse"},
                    {"text": "🏪 " + ("تجاری" if lang == Language.FA else "Commercial"), "callback_data": "prop_commercial"},
                    {"text": "🏞️ " + ("زمین" if lang == Language.FA else "Land"), "callback_data": "prop_land"},
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
                
                # Next: Ask transaction type (buy/rent)
                transaction_question = {
                    Language.EN: "Got it! Are you looking to Buy or Rent?",
                    Language.FA: "فهمیدم! می‌خواهید بخرید یا اجاره کنید؟",
                    Language.AR: "فهمت! هل تريد الشراء أم الإيجار؟",
                    Language.RU: "Понял! Вы хотите купить или арендовать?"
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
                        {"text": self.get_text("btn_buy", lang), "callback_data": "tx_buy"},
                        {"text": self.get_text("btn_rent", lang), "callback_data": "tx_rent"}
                    ]
                )
            
            # Transaction type selection
            elif callback_data.startswith("tx_"):
                transaction_type_str = callback_data.replace("tx_", "")
                transaction_type_map = {
                    "buy": TransactionType.BUY,
                    "rent": TransactionType.RENT
                }
                
                conversation_data["transaction_type"] = transaction_type_str
                filled_slots["transaction_type"] = True
                lead_updates["transaction_type"] = transaction_type_map.get(transaction_type_str)
                
                # Check if all REQUIRED slots are filled
                required_slots = ["budget", "property_type", "transaction_type"]
                all_filled = all(filled_slots.get(slot, False) for slot in required_slots)
                
                if all_filled:
                    # Move to VALUE_PROPOSITION
                    transition_message = {
                        Language.EN: "Perfect! Let me show you some amazing properties that match your criteria...",
                        Language.FA: "عالی! بذار چند ملک فوق‌العاده که با معیارهات مچ میشه رو نشونت بدم...",
                        Language.AR: "رائع! دعني أريك بعض العقارات المذهلة التي تتناسب مع معاييرك...",
                        Language.RU: "Отлично! Позвольте показать вам несколько потрясающих объектов..."
                    }
                    
                    return BrainResponse(
                        message=transition_message.get(lang, transition_message[Language.EN]),
                        next_state=ConversationState.VALUE_PROPOSITION,
                        lead_updates=lead_updates | {
                            "conversation_data": conversation_data,
                            "filled_slots": filled_slots,
                            "pending_slot": None
                        }
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
                
                # Move to next slot
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
        
        CRITICAL FIX #10a: If user sends TEXT message (question), answer it via AI
        instead of looping the same property list response!
        """
        # ===== FIX #10a: HANDLE TEXT MESSAGES IN VALUE_PROPOSITION =====
        if message and not callback_data:
            # User typed a message instead of clicking button
            # This might be a question, objection, or request for info
            
            logger.info(f"📝 VALUE_PROPOSITION text input from lead {lead.id}: '{message}'")
            
            # Use AI to answer the question
            ai_response = await self.generate_ai_response(message, lead)
            
            # After answering, still show the property buttons (don't break the flow)
            return BrainResponse(
                message=ai_response + "\n\n" + self.get_text("btn_need_help", lang),
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
            # User wants details - move to HARD_GATE for PDF
            pdf_offer = {
                Language.EN: "Perfect! 📊 I'll prepare a comprehensive PDF report with:\n  • Property details & images\n  • ROI projections\n  • Market analysis\n  • Investment highlights\n\nTo send it to you, may I have your phone number?",
                Language.FA: "عالی! 📊 من یک گزارش PDF جامع با موارد زیر آماده خواهم کرد:\n  • جزئیات و تصاویر ملک\n  • پیش‌بینی ROI\n  • تحلیل بازار\n  • نکات سرمایه‌گذاری\n\nبرای ارسال آن به شما، شماره تلفن شما را می‌دهید؟",
                Language.AR: "رائع! 📊 سأعد تقريرًا شاملاً يتضمن:\n  • تفاصيل ممتلكات وصور\n  • توقعات العائد على الاستثمار\n  • تحليل السوق\n  • نقاط الاستثمار\n\nللإرسال إليك، هل أستطيع الحصول على رقم هاتفك؟",
                Language.RU: "Отлично! 📊 Я подготовлю полный PDF-отчет с:\n  • Детали объектов и фото\n  • Прогнозы ROI\n  • Анализ рынка\n  • Ключевые моменты инвестиций\n\nДля отправки вам, могу ли я получить ваш номер телефона?"
            }
            
            return BrainResponse(
                message=pdf_offer.get(lang, pdf_offer[Language.EN]),
                next_state=ConversationState.HARD_GATE,
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
            # FIX #5: User wants to book consultation - proactive CTA
            consultation_msg = {
                Language.EN: "Excellent! 📅 I'd like to connect you with our expert consultant.\n\nWhat's your phone number so they can reach you?",
                Language.FA: "عالی! 📅 من می‌خواهم شما را با مشاور متخصص خود متصل کنم.\n\nشماره تلفن شما چیست تا به شما تماس بگیرم؟",
                Language.AR: "ممتاز! 📅 أود أن أتواصل معك مع استشاريتنا الخبيرة.\n\nما رقم هاتفك ليتمكنوا من الاتصال بك؟",
                Language.RU: "Отлично! 📅 Я хотел бы связать вас с нашим экспертом.\n\nКакой ваш номер телефона, чтобы они могли с вами связаться?"
            }
            
            lead_updates["consultation_requested"] = True
            return BrainResponse(
                message=consultation_msg.get(lang, consultation_msg[Language.EN]),
                next_state=ConversationState.HARD_GATE,
                lead_updates=lead_updates
            )
        
        # Get property recommendations
        property_recs = await self.get_property_recommendations(lead)
        
        # Parse recommendations (simplified)
        if property_recs and "no properties" not in property_recs.lower():
            # CRITICAL FIX: Show value FIRST, don't ask for phone immediately!
            # Instead, show properties and ask if they want details/more info
            value_message = {
                Language.EN: f"Perfect! Here are properties that match your criteria:\n\n{property_recs}\n\n📋 Would you like to see the full details and market analysis for any of these?",
                Language.FA: f"عالی! اینها ملک‌هایی هستند که با معیارهای شما مطابقت دارند:\n\n{property_recs}\n\n📋 می‌خواهید جزئیات کامل و تحلیل بازار برای هر یک از اینها را ببینید؟",
                Language.AR: f"رائع! إليك العقارات التي تطابق معاييرك:\n\n{property_recs}\n\n📋 هل تريد رؤية التفاصيل الكاملة وتحليل السوق لأي من هذه؟",
                Language.RU: f"Отлично! Вот объекты, которые соответствуют вашим критериям:\n\n{property_recs}\n\n📋 Хотите увидеть полные детали и рыночный анализ для любого из них?"
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
        else:
            # No matching properties
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
        # If user clicked "Yes, send PDF"
        if callback_data == "pdf_yes":
            phone_request = {
                Language.EN: "Perfect! To send you the PDF report, I need your phone number.\n\nPlease share your contact or type your number:",
                Language.FA: "عالی! برای ارسال گزارش PDF، به شماره تماس شما نیاز دارم.\n\nلطفاً شماره خود را به اشتراک بگذارید یا تایپ کنید:",
                Language.AR: "رائع! لإرسال تقرير PDF لك، أحتاج رقم هاتفك.\n\nيرجى مشاركة جهة الاتصال الخاصة بك أو كتابة رقمك:",
                Language.RU: "Отлично! Чтобы отправить вам PDF-отчет, мне нужен ваш номер телефона.\n\nПожалуйста, поделитесь контактом или введите номер:"
            }
            
            return BrainResponse(
                message=phone_request.get(lang, phone_request[Language.EN]),
                next_state=ConversationState.HARD_GATE
            )
        
        # If user clicked "No, thanks"
        if callback_data == "pdf_no":
            engagement_message = {
                Language.EN: "No problem! Do you have any questions about Dubai real estate?",
                Language.FA: "مشکلی نیست! سوالی درباره املاک دبی دارید؟",
                Language.AR: "لا مشكلة! هل لديك أي أسئلة عن العقارات في دبي؟",
                Language.RU: "Без проблем! У вас есть вопросы о недвижимости в Дубае?"
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
                    Language.EN: "Great! I understand you'd like to see property photos first. That makes total sense!\n\nWould you like to see our featured properties with full details?",
                    Language.FA: "عالی! متوجه شدم که می‌خواهید اول عکس‌ها رو ببینید.\n\nمی‌خواهید ملک‌های برجسته‌ی ما رو با جزئیات کامل ببینید؟",
                    Language.AR: "رائع! أفهم أنك تريد رؤية الصور أولاً. هذا منطقي تماماً!\n\nهل تريد رؤية ممتلكاتنا المميزة بالتفاصيل الكاملة؟",
                    Language.RU: "Отлично! Я понимаю, что вы хотите сначала увидеть фотографии.\n\nХотите увидеть наши лучшие объекты со всеми деталями?"
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
            phone_response = await self._validate_phone_number(lang, message, lead_updates)
            
            # If validation successful, move to ENGAGEMENT with PDF flag
            if phone_response.next_state == ConversationState.ENGAGEMENT:
                pdf_sent_message = {
                    Language.EN: "📄 Preparing your detailed ROI report...\n\nIt will be sent to you shortly!",
                    Language.FA: "📄 گزارش ROI شما در حال آماده‌سازی است...\n\nبه زودی برایتان ارسال می‌شود!",
                    Language.AR: "📄 جاري إعداد تقرير عائد الاستثمار المفصل...\n\nسيتم إرساله إليك قريبًا!",
                    Language.RU: "📄 Готовлю ваш подробный отчет ROI...\n\nОн скоро будет отправлен!"
                }
                
                return BrainResponse(
                    message=pdf_sent_message.get(lang, pdf_sent_message[Language.EN]),
                    next_state=ConversationState.ENGAGEMENT,
                    lead_updates=phone_response.lead_updates,
                    metadata={"send_pdf": True}
                )
            else:
                # Phone validation failed - return error
                return phone_response
        
        # Default
        return BrainResponse(
            message="Please provide your phone number",
            next_state=ConversationState.HARD_GATE
        )
    
    # ==================== PHONE VALIDATION (Used by HARD_GATE) ====================
    
    async def _validate_phone_number(self, lang: Language, message: str, lead_updates: Dict) -> BrainResponse:
        """Validate phone number with STRICT international validation and SQL injection protection."""
        # DATA INTEGRITY: Sanitize input to prevent SQL injection
        if not message or len(message) > 50:
            error_msgs = {
                Language.EN: "⚠️ Please provide a valid phone number (max 50 characters).",
                Language.FA: "⚠️ لطفاً شماره تلفن معتبر وارد کنید (حداکثر 50 کاراکتر).",
                Language.AR: "⚠️ يرجى إدخال رقم هاتف صالح (حد أقصى 50 حرفاً).",
                Language.RU: "⚠️ Пожалуйста, укажите корректный номер (макс 50 символов)."
            }
            return BrainResponse(
                message=error_msgs.get(lang, error_msgs[Language.EN]),
                next_state=ConversationState.HARD_GATE
            )
        
        # Clean message: remove spaces, dashes, parentheses, dots
        cleaned_message = re.sub(r'[\s\-\(\)\.]', '', message.strip())
        
        # Add + if missing
        if not cleaned_message.startswith('+'):
            if cleaned_message.isdigit() and len(cleaned_message) >= 10:
                cleaned_message = '+' + cleaned_message
        
        # International phone pattern
        phone_pattern = r'^\+\d{10,15}$'
        
        valid = False
        if re.match(phone_pattern, cleaned_message):
            digits_only = cleaned_message.lstrip('+')
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
                phone_number = cleaned_message if cleaned_message.startswith('+') else f'+{cleaned_message}'
                lead_updates["phone"] = phone_number
                lead_updates["status"] = LeadStatus.CONTACTED
                
                return BrainResponse(
                    message="✅",  # Success marker
                    next_state=ConversationState.ENGAGEMENT,
                    lead_updates=lead_updates
                )
        
        # Invalid phone - ONE example only
        error_msgs = {
            Language.EN: "⚠️ Please provide a valid international phone number.\n\nExample: +971501234567",
            Language.FA: "⚠️ لطفاً شماره تلفن بین‌المللی معتبر وارد کنید.\n\nمثال: +971501234567",
            Language.AR: "⚠️ يرجى إدخال رقم هاتف دولي صالح.\n\nمثال: +971501234567",
            Language.RU: "⚠️ Пожалуйста, укажите корректный международный номер.\n\nПример: +971501234567"
        }
        return BrainResponse(
            message=error_msgs.get(lang, error_msgs[Language.EN]),
            next_state=ConversationState.HARD_GATE
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
            
            # Update lead status to URGENT for agent dashboard
            lead_updates["status"] = LeadStatus.URGENT
            
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
                
                lead_updates["status"] = LeadStatus.URGENT
                
                return BrainResponse(
                    message=captured_msg.get(lang, captured_msg[Language.EN]),
                    next_state=ConversationState.ENGAGEMENT,
                    lead_updates=lead_updates,
                    metadata={"urgent_escalation": True, "send_to_agent": True}
                )
            else:
                # Invalid phone - ask again
                return phone_response
        
        # Default - stay in HANDOFF_URGENT
        return BrainResponse(
            message=self.get_text("phone_request", lang),
            next_state=ConversationState.HANDOFF_URGENT
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
        """
        # Load tenant context if not loaded
        if not self.tenant_context:
            await self.load_tenant_context(lead)
        
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
            "وقت مشاوره", "تایم مشاوره", "زمان مشاوره", "appointment", "meeting time",
            "schedule", "book", "reservation", "تماس بگیر", "call me", "speak with agent",
            "مشاور", "consultant", "viewing", "بازدید", "visit"
        ]
        
        user_message_lower = message.lower() if message else ""
        
        # Check for explicit scheduling request
        explicit_schedule_request = any(trigger in user_message_lower for trigger in schedule_triggers_explicit)
        
        if explicit_schedule_request:
            # User explicitly wants to schedule - go directly to SCHEDULE state
            confirming_msgs = {
                Language.EN: "Great! Let me check available consultation times with {agent_name}. When works best for you?",
                Language.FA: "عالی! بذارید زمان‌های مشاوره با {agent_name} را چک کنم. چه زمانی براتون مناسبه؟",
                Language.AR: "رائع! دعني أتحقق من أوقات الاستشارة مع {agent_name}. متى يناسبك؟",
                Language.RU: "Отлично! Давайте проверим доступное время консультации с {agent_name}. Когда вам удобно?"
            }
            
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
        
        # Otherwise, stay in engagement mode with no buttons (free conversation)
        return BrainResponse(
            message=ai_response,
            next_state=ConversationState.ENGAGEMENT,
            buttons=[]
        )
    
    async def _handle_schedule(self, lang: Language, callback_data: Optional[str], lead: Lead) -> BrainResponse:
        """Handle scheduling selection with SCARCITY technique."""
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
            # SCARCITY: Limit to only 3-4 slots to create urgency
            limited_slots = slots[:4]
            slot_count = len(limited_slots)
            
            # Format slots for display
            slot_buttons = []
            slot_texts = []
            for slot in limited_slots:
                day = slot.day_of_week.value.capitalize()
                time_str = slot.start_time.strftime("%H:%M")
                slot_buttons.append({
                    "text": f"🔥 {day} {time_str}",
                    "callback_data": f"slot_{slot.id}"
                })
                slot_texts.append(f"• {day} at {time_str}")
            
            # Use scarcity message instead of plain schedule
            scarcity_msg = self.get_text("schedule_scarcity", lang).format(
                agent_name=self.agent_name,
                slot_count=slot_count,
                slots="\n".join(slot_texts)
            )
            
            return BrainResponse(
                message=scarcity_msg,
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
    ack_msg = brain.get_text("voice_acknowledged", lang).format(transcript=transcript[:100])
    response.message = f"{ack_msg}\n\n{response.message}"
    
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

