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
    LeadStatus, update_lead, get_available_slots, DayOfWeek,
    PainPoint, get_tenant_context_for_ai
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
    
    NEW: Uses tenant-specific data (properties, projects, knowledge) for personalized responses.
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.agent_name = tenant.name or "ArtinSmartRealty"
        self.tenant_context = None  # Will be loaded on demand
        
        # Initialize Gemini model
        if GEMINI_API_KEY:
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None
    
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
                
                # Wait for processing
                import time
                while audio_file.state.name == "PROCESSING":
                    time.sleep(1)
                    audio_file = genai.get_file(audio_file.name)
                
                if audio_file.state.name == "FAILED":
                    return "Could not process audio file", {}
                
                # Generate transcript and extract entities
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
                
                response = self.model.generate_content([audio_file, prompt])
                
                # Clean up
                genai.delete_file(audio_file.name)
                
                # Parse JSON response
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                response_text = re.sub(r'^```json\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)
                
                result = json.loads(response_text)
                
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
            print(f"Voice processing error: {e}")
            import traceback
            traceback.print_exc()
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
                
                # Wait for processing
                import time
                while image_file.state.name == "PROCESSING":
                    time.sleep(1)
                    image_file = genai.get_file(image_file.name)
                
                if image_file.state.name == "FAILED":
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
                
                result = json.loads(response_text)
                
                # Get image description
                description = result.get("description", "property image")
                property_type = result.get("property_type", "apartment")
                features = result.get("features", [])
                style = result.get("style", "")
                
                # Search for similar properties in tenant's inventory
                properties = self.tenant_context.get("properties", [])
                
                # Simple matching algorithm based on extracted features
                matching_properties = []
                for prop in properties:
                    score = 0
                    
                    # Match property type
                    if prop.get("type", "").lower() == property_type.lower():
                        score += 5
                    
                    # Match features
                    prop_features_lower = [f.lower() for f in prop.get("features", [])]
                    for feature in features:
                        if any(feature.lower() in pf for pf in prop_features_lower):
                            score += 2
                    
                    # Match style
                    if style and style.lower() in prop.get("description", "").lower():
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
            print(f"Image processing error: {e}")
            import traceback
            traceback.print_exc()
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
        """
        if not self.model:
            return self.get_text("welcome", lead.language or Language.EN)
        
        try:
            # Load tenant context if not already loaded
            if not self.tenant_context:
                await self.load_tenant_context(lead)
            
            # Build tenant data context
            tenant_data_prompt = self._build_tenant_context_prompt()
            
            system_prompt = f"""
            You are {self.agent_name}'s professional AI assistant for Dubai Real Estate.
            
            CRITICAL RULES:
            1. ALWAYS respond in {lead.language.value.upper()} language
            2. Be helpful, professional, and knowledgeable about Dubai real estate
            3. **IMPORTANT: Use ONLY the agent's actual properties and projects listed below when making recommendations**
            4. Do NOT make up property names or prices - use only what's in the agent's inventory
            5. If asked about properties not in the list, say "{self.agent_name} can provide more options matching your needs"
            6. Mention Golden Visa opportunities when relevant (minimum 2M AED investment)
            7. Keep responses concise and actionable
            8. When recommending properties, mention specific ones from the agent's inventory
            
            ==== AGENT'S DATA (USE THIS!) ====
            {tenant_data_prompt}
            ==================================
            
            CURRENT LEAD PROFILE:
            - Status: {lead.status.value if lead.status else 'new'}
            - Budget: {lead.budget_min:,.0f if lead.budget_min else 'Not set'} - {lead.budget_max:,.0f if lead.budget_max else 'Not set'} {lead.budget_currency or 'AED'}
            - Purpose: {lead.purpose.value if lead.purpose else 'not specified'}
            - Property Type: {lead.property_type.value if lead.property_type else 'not specified'}
            - Location Interest: {lead.preferred_location or 'not specified'}
            - Pain Point: {lead.pain_point or 'not identified'}
            
            Additional Context: {context}
            """.strip()
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                [system_prompt, f"User says: {user_message}"]
            )
            
            return response.text.strip()
        except Exception as e:
            print(f"AI response error: {e}")
            return self.get_text("welcome", lead.language or Language.EN)
    
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
        lang = lead.language or self.detect_language(message)
        current_state = lead.conversation_state or ConversationState.START
        
        # Update lead language if detected differently
        lead_updates = {"language": lang}
        
        # State Machine Logic
        if current_state == ConversationState.START:
            return self._handle_start(lang)
        
        elif current_state == ConversationState.LANGUAGE_SELECT:
            return self._handle_language_select(lang, callback_data, lead_updates)
        
        elif current_state == ConversationState.WELCOME:
            return self._handle_welcome_response(lang, callback_data)
        
        elif current_state == ConversationState.HOOK:
            return self._handle_hook_response(lang, callback_data)
        
        elif current_state == ConversationState.PHONE_GATE:
            return await self._handle_phone_gate(lang, message, lead_updates)
        
        elif current_state == ConversationState.PAIN_DISCOVERY:
            return self._handle_pain_discovery(lang, callback_data, lead_updates)
        
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
        
        elif current_state == ConversationState.SOLUTION_BRIDGE:
            return await self._handle_solution_bridge(lang, callback_data, lead, lead_updates)
        
        elif current_state == ConversationState.SCHEDULE:
            return await self._handle_schedule(lang, callback_data, lead)
        
        elif current_state == ConversationState.COMPLETED:
            # For completed leads, use AI for free-form conversation
            ai_response = await self.generate_ai_response(message, lead)
            return BrainResponse(message=ai_response)
        
        # Default: restart flow
        return self._handle_start(lang)
    
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
    
    def _handle_language_select(self, lang: Language, callback_data: Optional[str], lead_updates: Dict) -> BrainResponse:
        """Handle language selection - update lead language and proceed to welcome."""
        lang_map = {
            "lang_en": Language.EN,
            "lang_fa": Language.FA,
            "lang_ar": Language.AR,
            "lang_ru": Language.RU
        }
        
        if callback_data in lang_map:
            lang = lang_map[callback_data]
            lead_updates["language"] = lang
        
        return BrainResponse(
            message=self.get_text("welcome", lang).format(agent_name=self.agent_name),
            next_state=ConversationState.WELCOME,
            lead_updates=lead_updates,
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
            
            # NEW: Go to Pain Discovery first (Psychology technique)
            return BrainResponse(
                message=self.get_text("pain_discovery", lang),
                next_state=ConversationState.PAIN_DISCOVERY,
                lead_updates=lead_updates,
                buttons=[
                    {"text": self.get_text("btn_inflation", lang), "callback_data": "pain_inflation"},
                    {"text": self.get_text("btn_visa", lang), "callback_data": "pain_visa"},
                    {"text": self.get_text("btn_income", lang), "callback_data": "pain_income"},
                    {"text": self.get_text("btn_tax", lang), "callback_data": "pain_tax"}
                ]
            )
        else:
            # Invalid phone - ask again
            return BrainResponse(
                message=self.get_text("phone_request", lang),
                next_state=ConversationState.PHONE_GATE
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
    
    def _handle_purpose(self, lang: Language, callback_data: Optional[str], lead_updates: Dict) -> BrainResponse:
        """Handle purpose selection."""
        if callback_data == "purp_invest":
            lead_updates["purpose"] = Purpose.INVESTMENT
        elif callback_data == "purp_living":
            lead_updates["purpose"] = Purpose.LIVING
        else:
            lead_updates["purpose"] = Purpose.RESIDENCY
        
        lead_updates["status"] = LeadStatus.QUALIFIED
        
        # NEW: Go to Solution Bridge to connect pain to solution (Psychology technique)
        return BrainResponse(
            message="",  # Will be set in solution bridge based on pain point
            next_state=ConversationState.SOLUTION_BRIDGE,
            lead_updates=lead_updates
        )
    
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
        
        return BrainResponse(
            message=solution_msg,
            next_state=ConversationState.SCHEDULE,
            lead_updates=lead_updates,
            buttons=[
                {"text": self.get_text("btn_yes", lang), "callback_data": "solution_yes"}
            ]
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
        features_str = ", ".join(prop.get('features', [])[:3])
        golden_str = " 🛂 Golden Visa" if prop.get('golden_visa') else ""
        roi_str = f" | ROI: {prop['roi']}%" if prop.get('roi') else ""
        
        property_details_parts.append(
            f"{i}. **{prop['name']}**\n"
            f"   📍 {prop['location']}\n"
            f"   🏠 {prop['bedrooms']}BR {prop['type']}\n"
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

