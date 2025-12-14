"""
Property Presentation Module
Professional property presentation with photos and ROI for both Telegram and WhatsApp
"""

import logging
from typing import Dict, List, Optional
import io

from database import Tenant, Lead, Language, TenantProperty
from roi_engine import generate_roi_pdf

logger = logging.getLogger(__name__)


async def send_property_with_roi(
    bot_interface,  # telegram_bot or whatsapp_bot instance
    lead: Lead,
    tenant: Tenant,
    property_data: Dict,
    index: int = 1,
    platform: str = "telegram"  # "telegram" or "whatsapp"
):
    """
    🏆 ارسال حرفه‌ای ملک با عکس، مشخصات کامل و گزارش ROI
    
    این تابع مثل یک مشاور املاک واقعی عمل می‌کند:
    1. ابتدا عکس‌های ملک را می‌فرستد (Media Group)
    2. سپس یک پرزنتیشن کامل با تمام جزئیات
    3. در نهایت فایل PDF گزارش ROI اختصاصی
    
    Args:
        bot_interface: نمونه telegram_bot یا whatsapp_bot
        lead: اطلاعات کاربر
        tenant: اطلاعات تنانت
        property_data: اطلاعات کامل ملک از database
        index: شماره ملک (1، 2، 3...)
        platform: "telegram" یا "whatsapp"
    """
    lang = lead.language or Language.EN
    
    try:
        # 📸 Step 1: ارسال عکس‌های ملک
        images = property_data.get('image_urls', []) or property_data.get('images', [])
        
        if images and isinstance(images, list) and len(images) > 0:
            # ارسال به صورت Media Album (حداکثر 10 عکس)
            photos_to_send = images[:10]
            
            if platform == "telegram":
                # Telegram: ارسال Media Group
                if hasattr(bot_interface, 'application') and bot_interface.application:
                    chat_id = lead.telegram_chat_id
                    
                    # Caption برای اولین عکس
                    first_caption = {
                        Language.EN: f"🏠 Property #{index} Photos",
                        Language.FA: f"📸 تصاویر ملک شماره {index}",
                        Language.AR: f"📸 صور العقار رقم {index}",
                        Language.RU: f"📸 Фото объекта №{index}"
                    }.get(lang, f"🏠 Property #{index}")
                    
                    # ساخت لیست media
                    from telegram import InputMediaPhoto
                    media_group = []
                    
                    for idx, img_url in enumerate(photos_to_send):
                        if idx == 0:
                            media_group.append(InputMediaPhoto(media=img_url, caption=first_caption))
                        else:
                            media_group.append(InputMediaPhoto(media=img_url))
                    
                    await bot_interface.application.bot.send_media_group(
                        chat_id=chat_id,
                        media=media_group
                    )
                    logger.info(f"📸 Sent {len(photos_to_send)} photos for property {index}")
                    
            elif platform == "whatsapp":
                # WhatsApp: ارسال تک‌تک (WhatsApp فعلاً Media Group ندارد)
                for img_url in photos_to_send[:3]:  # فقط 3 عکس اول
                    await bot_interface.send_image(lead.whatsapp_phone, img_url)
                logger.info(f"📸 Sent {min(len(photos_to_send), 3)} photos for property {index}")
        
        # ⏳ کمی تاخیر برای بارگذاری عکس‌ها
        import asyncio
        await asyncio.sleep(1)
        
        # 📋 Step 2: ارسال پرزنتیشن کامل ملک
        from brain import Brain
        brain = Brain(tenant)
        presentation_text = brain.format_property_presentation(property_data, lang, index)
        
        # دکمه‌های اقدام
        action_buttons = []
        
        if platform == "telegram":
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            buttons_row1 = [
                InlineKeyboardButton(
                    {"en": "📅 Book Viewing", "fa": "رزرو بازدید", "ar": "حجز معاينة", "ru": "Записаться"}[lang[:2]], 
                    callback_data=f"book_viewing_{property_data.get('id')}"
                ),
                InlineKeyboardButton(
                    {"en": "📊 Full ROI PDF", "fa": "گزارش ROI کامل", "ar": "تقرير ROI", "ru": "Полный ROI"}[lang[:2]], 
                    callback_data=f"get_roi_{property_data.get('id')}"
                )
            ]
            
            buttons_row2 = [
                InlineKeyboardButton(
                    {"en": "💬 Ask Questions", "fa": "پرسش سوال", "ar": "طرح أسئلة", "ru": "Задать вопрос"}[lang[:2]], 
                    callback_data=f"ask_about_{property_data.get('id')}"
                ),
                InlineKeyboardButton(
                    {"en": "➡️ Next Property", "fa": "ملک بعدی", "ar": "العقار التالي", "ru": "Следующий"}[lang[:2]], 
                    callback_data="next_property"
                )
            ]
            
            keyboard = InlineKeyboardMarkup([buttons_row1, buttons_row2])
            
            await bot_interface.application.bot.send_message(
                chat_id=lead.telegram_chat_id,
                text=presentation_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
        elif platform == "whatsapp":
            # WhatsApp: پیام با دکمه‌ها
            await bot_interface.send_message(
                lead.whatsapp_phone,
                presentation_text,
                buttons=[
                    {"id": f"book_{property_data.get('id')}", "title": "📅 Book Viewing"},
                    {"id": f"roi_{property_data.get('id')}", "title": "📊 Get ROI PDF"},
                    {"id": "next", "title": "➡️ Next Property"}
                ]
            )
        
        logger.info(f"📋 Sent property presentation for property {index}")
        
        # ⏳ تاخیر کوتاه قبل از PDF
        await asyncio.sleep(2)
        
        # 📄 Step 3: ارسال خودکار فایل PDF گزارش ROI
        try:
            # ساخت PDF با اطلاعات ملک
            pdf_buffer = await generate_roi_pdf(
                tenant=tenant,
                lead=lead,
                property_value=property_data.get('price', 0)
            )
            
            # نام فایل
            property_name = property_data.get('name', 'Property').replace(' ', '_')
            pdf_filename = f"ROI_Report_{property_name}.pdf"
            
            # Caption برای PDF
            pdf_caption = {
                Language.EN: f"📊 **Personalized ROI Analysis**\n\nComplete investment breakdown for {property_data.get('name')}\n\n✅ 5-Year Projections\n✅ Rental Income Calculations\n✅ Tax Benefits\n✅ Golden Visa Info",
                Language.FA: f"📊 **تحلیل ROI اختصاصی**\n\nجزئیات کامل سرمایه‌گذاری برای {property_data.get('name')}\n\n✅ پیش‌بینی 5 ساله\n✅ محاسبات درآمد اجاره\n✅ مزایای مالیاتی\n✅ اطلاعات ویزای طلایی",
                Language.AR: f"📊 **تحليل ROI مخصص**\n\nتفاصيل كاملة للاستثمار في {property_data.get('name')}\n\n✅ توقعات 5 سنوات\n✅ حسابات دخل الإيجار\n✅ المزايا الضريبية\n✅ معلومات التأشيرة الذهبية",
                Language.RU: f"📊 **Персональный ROI анализ**\n\nПолная разбивка инвестиций для {property_data.get('name')}\n\n✅ Прогноз на 5 лет\n✅ Расчет арендного дохода\n✅ Налоговые льготы\n✅ Золотая виза"
            }.get(lang, f"📊 ROI Analysis for {property_data.get('name')}")
            
            if platform == "telegram":
                # Telegram: ارسال PDF
                await bot_interface.application.bot.send_document(
                    chat_id=lead.telegram_chat_id,
                    document=io.BytesIO(pdf_buffer),
                    filename=pdf_filename,
                    caption=pdf_caption,
                    parse_mode="Markdown"
                )
                
            elif platform == "whatsapp":
                # WhatsApp: ارسال PDF
                await bot_interface.send_document(
                    lead.whatsapp_phone,
                    pdf_buffer,
                    pdf_filename,
                    caption=pdf_caption
                )
            
            logger.info(f"📄 Sent ROI PDF for property {index}")
            
        except Exception as pdf_error:
            logger.error(f"❌ Failed to generate/send PDF: {pdf_error}")
            # اگر PDF ناموفق بود، یک پیام ساده بفرست
            fallback_msg = {
                Language.EN: "⚠️ ROI PDF will be sent shortly. Our team is preparing your personalized report.",
                Language.FA: "⚠️ PDF گزارش ROI به زودی ارسال می‌شود. تیم ما در حال آماده‌سازی گزارش اختصاصی شماست.",
                Language.AR: "⚠️ سيتم إرسال PDF ROI قريباً. فريقنا يحضر تقريرك المخصص.",
                Language.RU: "⚠️ PDF ROI будет отправлен в ближайшее время. Наша команда готовит ваш персональный отчет."
            }.get(lang, "ROI PDF coming soon")
            
            if platform == "telegram":
                await bot_interface.application.bot.send_message(
                    chat_id=lead.telegram_chat_id,
                    text=fallback_msg
                )
            elif platform == "whatsapp":
                await bot_interface.send_message(lead.whatsapp_phone, fallback_msg)
        
        logger.info(f"✅ Successfully presented property {index} to lead {lead.id}")
        
    except Exception as e:
        logger.error(f"❌ Error in send_property_with_roi: {e}")
        import traceback
        logger.error(traceback.format_exc())


async def present_all_properties(
    bot_interface,
    lead: Lead,
    tenant: Tenant,
    properties: List[Dict],
    platform: str = "telegram"
):
    """
    🏆 ارائه تمام املاک به صورت حرفه‌ای
    
    این تابع تمام املاک را یکی یکی با فاصله زمانی مناسب ارسال می‌کند
    تا کاربر بتواند هر کدام را به دقت بررسی کند
    """
    lang = lead.language or Language.EN
    
    # پیام مقدماتی
    intro = {
        Language.EN: f"🌟 **Excellent! I found {len(properties)} perfect properties for you.**\n\nI'll present each one professionally with:\n✅ Professional photos\n✅ Complete specifications\n✅ Personalized ROI analysis\n✅ Investment breakdown\n\nLet me show you...",
        Language.FA: f"🌟 **عالی! {len(properties)} ملک مناسب برای شما پیدا کردم.**\n\nهر کدوم رو به صورت حرفه‌ای با این موارد ارائه می‌کنم:\n✅ عکس‌های حرفه‌ای\n✅ مشخصات کامل\n✅ تحلیل ROI اختصاصی\n✅ جزئیات سرمایه‌گذاری\n\nبذار نشونت بدم...",
        Language.AR: f"🌟 **ممتاز! وجدت {len(properties)} عقارات مثالية لك.**\n\nسأقدم كل واحد بشكل احترافي مع:\n✅ صور احترافية\n✅ مواصفات كاملة\n✅ تحليل ROI مخصص\n✅ تفاصيل الاستثمار\n\nدعني أريك...",
        Language.RU: f"🌟 **Отлично! Я нашел {len(properties)} идеальных объектов для вас.**\n\nЯ представлю каждый профессионально с:\n✅ Профессиональные фото\n✅ Полные характеристики\n✅ Персональный ROI анализ\n✅ Детали инвестиций\n\nПозвольте показать..."
    }.get(lang, f"🌟 Found {len(properties)} properties")
    
    if platform == "telegram":
        await bot_interface.application.bot.send_message(
            chat_id=lead.telegram_chat_id,
            text=intro,
            parse_mode="Markdown"
        )
    elif platform == "whatsapp":
        await bot_interface.send_message(lead.whatsapp_phone, intro)
    
    # ارسال هر ملک با فاصله زمانی
    import asyncio
    for idx, prop in enumerate(properties, 1):
        await send_property_with_roi(
            bot_interface=bot_interface,
            lead=lead,
            tenant=tenant,
            property_data=prop,
            index=idx,
            platform=platform
        )
        
        # فاصله بین املاک (5 ثانیه)
        if idx < len(properties):
            await asyncio.sleep(5)
    
    # پیام پایانی
    outro = {
        Language.EN: "✨ **That's all the properties matching your criteria!**\n\nWhich one caught your eye? 🤔\n\nI can:\n📅 Schedule viewings\n📊 Send detailed comparisons\n💬 Answer any questions\n📞 Connect you with our specialist",
        Language.FA: "✨ **اینا تمام املاکی بود که با معیارهای شما مطابقت داشت!**\n\nکدومش نظرتو جلب کرد؟ 🤔\n\nمن می‌تونم:\n📅 بازدید تنظیم کنم\n📊 مقایسه دقیق بفرستم\n💬 به سوالات جواب بدم\n📞 شما رو به متخصصمون وصل کنم",
        Language.AR: "✨ **هذه كل العقارات التي تطابق معاييرك!**\n\nأيها لفت انتباهك؟ 🤔\n\nيمكنني:\n📅 جدولة المعاينات\n📊 إرسال مقارنات مفصلة\n💬 الإجابة على أي أسئلة\n📞 ربطك بمتخصصنا",
        Language.RU: "✨ **Это все объекты, соответствующие вашим критериям!**\n\nКакой привлек ваше внимание? 🤔\n\nЯ могу:\n📅 Назначить просмотры\n📊 Отправить детальное сравнение\n💬 Ответить на вопросы\n📞 Связать вас со специалистом"
    }.get(lang, "All properties presented!")
    
    if platform == "telegram":
        # دکمه‌های پایانی
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        buttons = [
            [InlineKeyboardButton(
                {"en": "📅 Schedule Viewings", "fa": "رزرو بازدید", "ar": "جدولة المعاينات", "ru": "Записаться"}[lang[:2]], 
                callback_data="schedule_viewings"
            )],
            [InlineKeyboardButton(
                {"en": "📊 Compare Properties", "fa": "مقایسه املاک", "ar": "مقارنة العقارات", "ru": "Сравнить"}[lang[:2]], 
                callback_data="compare_properties"
            )],
            [InlineKeyboardButton(
                {"en": "💬 Talk to Specialist", "fa": "تماس با متخصص", "ar": "التحدث إلى متخصص", "ru": "Связаться"}[lang[:2]], 
                callback_data="contact_specialist"
            )]
        ]
        
        await bot_interface.application.bot.send_message(
            chat_id=lead.telegram_chat_id,
            text=outro,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif platform == "whatsapp":
        await bot_interface.send_message(
            lead.whatsapp_phone,
            outro,
            buttons=[
                {"id": "schedule", "title": "📅 Schedule"},
                {"id": "compare", "title": "📊 Compare"},
                {"id": "contact", "title": "💬 Contact"}
            ]
        )
    
    logger.info(f"✅ Presented all {len(properties)} properties to lead {lead.id}")
