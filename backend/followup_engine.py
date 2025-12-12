"""
Intelligent Follow-up System
Automatically sends personalized messages to leads across all channels
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import select, and_, or_
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.database import async_session
from backend.unified_database import (
    UnifiedLead, LeadInteraction, FollowupCampaign,
    LeadSource, LeadStatus, InteractionChannel, InteractionDirection,
    log_interaction
)
from backend.brain import RealEstateBrain
import os


class FollowupEngine:
    """
    Intelligent Follow-up Engine
    - Automatically contacts new LinkedIn leads
    - Re-engages cold leads
    - Sends property recommendations
    """
    
    def __init__(self):
        self.brain = RealEstateBrain()
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        """Start the follow-up scheduler"""
        # Run every hour
        self.scheduler.add_job(
            self.process_scheduled_followups,
            IntervalTrigger(hours=1),
            id='process_followups',
            name='Process Scheduled Follow-ups',
            replace_existing=True
        )
        
        self.scheduler.start()
        print("✅ Follow-up Engine Started!")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("⏹️  Follow-up Engine Stopped!")
    
    async def process_scheduled_followups(self):
        """
        Main follow-up processing loop
        Runs every hour to check which leads need follow-up
        """
        print(f"\n🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M')}] Processing Follow-ups...")
        
        try:
            async with async_session() as session:
                # ✅ FIX: Add FOR UPDATE SKIP LOCKED to prevent race conditions in multi-instance deployments
                query = select(UnifiedLead).where(
                    and_(
                        UnifiedLead.next_followup_at <= datetime.utcnow(),
                        UnifiedLead.next_followup_at.isnot(None),  # ✅ FIX: NULL check
                        UnifiedLead.status.in_([LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.NURTURING]),
                        UnifiedLead.followup_count < 5  # Max 5 follow-ups (prevents spam)
                    )
                ).limit(100).with_for_update(skip_locked=True)  # ✅ FIX: Prevent duplicate processing
                
                result = await session.execute(query)
                leads = result.scalars().all()
                
                print(f"   Found {len(leads)} leads needing follow-up")
                
                success_count = 0
                error_count = 0
                
                for lead in leads:
                    try:
                        await self.send_followup_message(session, lead)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"   ❌ Error following up with {lead.name}: {e}")
                        # ✅ FIX: Continue to next lead instead of failing all
                        continue
                
                await session.commit()
                print(f"   ✅ Success: {success_count} | ❌ Failed: {error_count}")
                
        except Exception as e:
            print(f"   ❌ Critical error in follow-up processing: {e}")
            # Don't crash the entire engine
    
    async def send_followup_message(self, session, lead: UnifiedLead, max_retries: int = 3):
        """
        Send a personalized follow-up message to a lead
        ✅ FIX: Added retry mechanism for failed sends
        """
        # ✅ FIX: Validate lead has required fields
        lead_name = getattr(lead, 'name', None)
        if not lead_name:
            lead_id = getattr(lead, 'id', 'Unknown')
            print(f"   ⚠️  Lead ID {lead_id} has no name, skipping")
            return
        
        # Generate personalized message
        try:
            message = await self.generate_followup_message(lead)
        except Exception as e:
            print(f"   ❌ Failed to generate message for {lead.name}: {e}")
            raise
        
        # ✅ FIX: Validate message was generated
        if not message or not message.strip():
            print(f"   ⚠️  Empty message generated for {lead.name}, skipping")
            return
        
        # ✅ FIX: Determine channel with retry mechanism
        channel = None
        message_sent = False
        
        for attempt in range(max_retries):
            try:
                telegram_id = getattr(lead, 'telegram_user_id', None)
                whatsapp_num = getattr(lead, 'whatsapp_number', None)
                
                if telegram_id:
                    channel = InteractionChannel.TELEGRAM
                    await self.send_telegram_message(int(telegram_id), message)
                    message_sent = True
                    break
                elif whatsapp_num:
                    channel = InteractionChannel.WHATSAPP
                    await self.send_whatsapp_message(str(whatsapp_num), message)
                    message_sent = True
                    break
                else:
                    print(f"   ⚠️  No contact method for {lead_name}")
                    return
            except Exception as e:
                print(f"   ⚠️  Attempt {attempt + 1}/{max_retries} failed for {lead.name}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                else:
                    print(f"   ❌ Failed to send message after {max_retries} attempts")
                    return  # Don't update follow-up if message wasn't sent
        
        # ✅ FIX: Only proceed if message was actually sent
        if not message_sent or not channel:
            return
        
        # Log interaction
        lead_id = int(getattr(lead, 'id', 0))
        await log_interaction(
            session=session,
            lead_id=lead_id,
            channel=channel,
            direction=InteractionDirection.OUTBOUND,
            message_text=message,
            ai_generated=True
        )
        
        # ✅ FIX: Update lead stats (only if message was sent)
        lead.last_contacted_at = datetime.utcnow()  # type: ignore
        lead.followup_count += 1  # type: ignore
        lead.next_followup_at = datetime.utcnow() + timedelta(days=3)  # type: ignore
        lead.update_score_and_grade()
        
        print(f"   ✅ Sent follow-up to {lead_name} via {channel.value}")
    
    async def generate_followup_message(self, lead: UnifiedLead) -> str:
        """
        Generate personalized follow-up message based on lead data and follow-up count
        """
        lead_lang = getattr(lead, 'language', None)
        language = lead_lang.value if lead_lang else 'en'
        
        # Different message templates based on follow-up count
        followup_count = int(getattr(lead, 'followup_count', 0) or 0)
        
        if followup_count == 0:
            # First contact - Introduction
            return await self.generate_introduction_message(lead, language)
        elif followup_count == 1:
            # Second follow-up - Value proposition
            return await self.generate_value_message(lead, language)
        elif followup_count == 2:
            # Third follow-up - Urgency
            return await self.generate_urgency_message(lead, language)
        elif followup_count == 3:
            # Fourth follow-up - Last chance
            return await self.generate_last_chance_message(lead, language)
        else:
            # Final follow-up - Graceful exit
            return await self.generate_graceful_exit_message(lead, language)
    
    async def generate_introduction_message(self, lead: UnifiedLead, language: str) -> str:
        """Generate first contact message"""
        
        templates = {
            'en': f"""
Hi {lead.name}! 👋

I noticed your LinkedIn profile where you work as {lead.job_title or 'professional'} at {lead.company or 'your company'}.

I'm the AI assistant for ArtinSmartRealty - we specialize in Dubai real estate investments.

{self._get_pain_hook(lead, language)}

Would you be interested in exploring investment opportunities in Dubai? 🏢

Reply YES if you'd like to learn more!
            """.strip(),
            
            'fa': f"""
سلام {lead.name} عزیز! 👋

پروفایل لینکدین شما رو دیدم که در {lead.company or 'شرکت'} به عنوان {lead.job_title or 'متخصص'} فعالیت می‌کنید.

من دستیار هوشمند ArtinSmartRealty هستم - متخصص سرمایه‌گذاری املاک در دبی.

{self._get_pain_hook(lead, language)}

آیا علاقه‌مند هستید که در مورد فرصت‌های سرمایه‌گذاری در دبی صحبت کنیم؟ 🏢

اگر مایلید، جواب بدید!
            """.strip(),
            
            'ar': f"""
مرحباً {lead.name}! 👋

لاحظت ملفك الشخصي على LinkedIn حيث تعمل كـ {lead.job_title or 'محترف'} في {lead.company or 'شركتك'}.

أنا المساعد الذكي لـ ArtinSmartRealty - متخصصون في الاستثمار العقاري في دبي.

{self._get_pain_hook(lead, language)}

هل تهتم باستكشاف فرص الاستثمار في دبي؟ 🏢

أجب بنعم إذا كنت ترغب في معرفة المزيد!
            """.strip()
        }
        
        return templates.get(language, templates['en'])
    
    async def generate_value_message(self, lead: UnifiedLead, language: str) -> str:
        """Generate second follow-up with value proposition"""
        
        templates = {
            'en': f"""
Hi {lead.name}! 🙂

I wanted to follow up on my previous message.

Dubai real estate offers:
• 📈 Average 8-10% annual ROI
• 🏖️ Golden Visa eligibility (invest 2M AED+)
• 💰 0% income tax
• 🌍 Strategic location (Asia-Europe-Africa hub)

Many of our clients are {lead.job_title or 'professionals'} like you who want to:
✅ Protect wealth from inflation
✅ Generate passive income
✅ Secure residency for family

Interested? Let me know!
            """.strip(),
            
            'fa': f"""
سلام {lead.name}! 🙂

می‌خواستم پیام قبلیم رو پیگیری کنم.

املاک دبی این مزایا رو داره:
• 📈 بازدهی سالانه 8-10%
• 🏖️ گلدن ویزا (سرمایه‌گذاری 2 میلیون درهم+)
• 💰 مالیات صفر
• 🌍 لوکیشن استراتژیک

خیلی از مشتری‌های ما {lead.job_title or 'حرفه‌ای‌هایی'} مثل شما هستند که می‌خوان:
✅ ثروتشون رو از تورم حفظ کنن
✅ درآمد غیرفعال داشته باشن
✅ اقامت برای خانواده تامین کنن

علاقه‌مندی؟ بهم خبر بده!
            """.strip(),
            
            'ar': f"""
مرحباً {lead.name}! 🙂

أردت المتابعة على رسالتي السابقة.

العقارات في دبي توفر:
• 📈 عائد استثمار سنوي 8-10%
• 🏖️ التأشيرة الذهبية (استثمار 2 مليون درهم+)
• 💰 ضريبة دخل 0%
• 🌍 موقع استراتيجي

كثير من عملائنا {lead.job_title or 'محترفون'} مثلك يريدون:
✅ حماية الثروة من التضخم
✅ توليد دخل سلبي
✅ تأمين الإقامة للعائلة

مهتم؟ اخبرني!
            """.strip()
        }
        
        return templates.get(language, templates['en'])
    
    async def generate_urgency_message(self, lead: UnifiedLead, language: str) -> str:
        """Generate third follow-up with urgency"""
        
        templates = {
            'en': f"""
{lead.name}, quick update! ⚡

We just added new properties that match professionals in {lead.company or 'your industry'}:

🏢 Prime locations: Dubai Marina, Downtown, Palm Jumeirah
💰 Starting from 800K AED
🔥 Limited availability

Many are selling fast in this market. Want to see what's available before they're gone?
            """.strip(),
            
            'fa': f"""
{lead.name}، خبر فوری! ⚡

تازه املاک جدیدی اضافه کردیم که مناسب حرفه‌ای‌های {lead.company or 'صنعت شما'} هستند:

🏢 لوکیشن‌های عالی: دبی مارینا، داون‌تاون، پالم جمیرا
💰 شروع از 800 هزار درهم
🔥 موجودی محدود

خیلی‌ها تو این بازار سریع فروش می‌رن. می‌خوای ببینی چی موجوده قبل از اینکه تموم بشه؟
            """.strip(),
            
            'ar': f"""
{lead.name}، تحديث سريع! ⚡

أضفنا للتو عقارات جديدة تناسب المحترفين في {lead.company or 'مجالك'}:

🏢 مواقع رئيسية: دبي مارينا، داون تاون، نخلة جميرا
💰 تبدأ من 800 ألف درهم
🔥 توافر محدود

كثير منها تُباع بسرعة في هذا السوق. تريد أن ترى ما هو متاح قبل نفادها؟
            """.strip()
        }
        
        return templates.get(language, templates['en'])
    
    async def generate_last_chance_message(self, lead: UnifiedLead, language: str) -> str:
        """Generate fourth follow-up - last push"""
        
        templates = {
            'en': f"""
{lead.name}, this is my last message 📩

I don't want to spam you, but I genuinely believe Dubai real estate could be perfect for someone in your position.

If now isn't the right time, totally understand! But if you ever want to explore:
• Investment opportunities
• Golden Visa options
• Portfolio diversification

Just say "INFO" and I'll send you details. No pressure! 😊
            """.strip(),
            
            'fa': f"""
{lead.name}، این آخرین پیام منه 📩

نمی‌خوام اسپم کنم، اما واقعا فکر می‌کنم املاک دبی برای کسی تو موقعیت شما عالیه.

اگه الان زمان مناسبی نیست، کاملا درک می‌کنم! اما اگه روزی خواستی درباره اینا بدونی:
• فرصت‌های سرمایه‌گذاری
• گزینه‌های گلدن ویزا
• متنوع‌سازی سبد سرمایه

فقط بگو "اطلاعات" و براتون می‌فرستم. فشاری نیست! 😊
            """.strip(),
            
            'ar': f"""
{lead.name}، هذه رسالتي الأخيرة 📩

لا أريد إزعاجك، لكنني أعتقد حقًا أن العقارات في دبي قد تكون مثالية لشخص في موقعك.

إذا لم يكن الآن الوقت المناسب، أفهم تمامًا! ولكن إذا أردت يومًا الاستكشاف:
• فرص الاستثمار
• خيارات التأشيرة الذهبية
• تنويع المحفظة

فقط قل "معلومات" وسأرسل لك التفاصيل. بدون ضغط! 😊
            """.strip()
        }
        
        return templates.get(language, templates['en'])
    
    async def generate_graceful_exit_message(self, lead: UnifiedLead, language: str) -> str:
        """Generate final follow-up - graceful exit"""
        
        templates = {
            'en': f"""
{lead.name}, no worries at all! 👋

I'll stop reaching out now. But if you ever need anything related to Dubai real estate, I'm here!

Wishing you all the best in your career at {lead.company or 'your company'} 🚀

- ArtinSmartRealty Team
            """.strip(),
            
            'fa': f"""
{lead.name}، هیچ مشکلی نیست! 👋

دیگه پیام نمی‌فرستم. اما اگه روزی نیاز به هر چیزی راجع به املاک دبی داشتی، اینجام!

بهترین‌ها رو برات در {lead.company or 'شرکتت'} آرزو می‌کنم 🚀

- تیم ArtinSmartRealty
            """.strip(),
            
            'ar': f"""
{lead.name}، لا قلق على الإطلاق! 👋

سأتوقف عن التواصل الآن. ولكن إذا احتجت يومًا أي شيء متعلق بعقارات دبي، أنا هنا!

أتمنى لك كل التوفيق في مسيرتك في {lead.company or 'شركتك'} 🚀

- فريق ArtinSmartRealty
            """.strip()
        }
        
        return templates.get(language, templates['en'])
    
    def _get_pain_hook(self, lead: UnifiedLead, language: str) -> str:
        """Generate pain point hook based on lead data"""
        
        # Default hooks by language
        hooks = {
            'en': "Worried about inflation eating your savings? Dubai offers a tax-free hedge against currency devaluation.",
            'fa': "نگران تورمی که پس‌اندازتون رو کم می‌کنه؟ دبی یه سپر بدون مالیات در مقابل کاهش ارزش پول ارائه می‌ده.",
            'ar': "قلق من التضخم الذي يأكل مدخراتك؟ دبي توفر حماية خالية من الضرائب ضد انخفاض قيمة العملة."
        }
        
        # If we know their pain points, customize
        pain_points = getattr(lead, 'pain_points', None)
        if pain_points:
            # Customize based on first pain point
            # (This is simplified - in production, you'd have more sophisticated logic)
            pass
        
        return hooks.get(language, hooks['en'])
    
    async def send_telegram_message(self, user_id: int, message: str):
        """Send message via Telegram"""
        from backend.telegram_bot import send_message
        try:
            await send_message(user_id, message)
        except Exception as e:
            print(f"   ❌ Telegram send failed: {e}")
    
    async def send_whatsapp_message(self, phone: str, message: str):
        """Send message via WhatsApp"""
        from backend.whatsapp_bot import send_message
        try:
            await send_message(phone, message)
        except Exception as e:
            print(f"   ❌ WhatsApp send failed: {e}")
    
    async def notify_new_linkedin_lead(self, lead: UnifiedLead):
        """
        Called when a new LinkedIn lead is added
        Schedules first follow-up
        """
        async with async_session() as session:
            # Schedule first follow-up in 1 hour
            lead.next_followup_at = datetime.utcnow() + timedelta(hours=1)  # type: ignore
            lead.status = LeadStatus.NEW  # type: ignore
            
            await session.commit()
            
            print(f"   ✅ Scheduled follow-up for LinkedIn lead: {lead.name}")
    
    async def notify_property_match(self, property_id: int, matched_leads: List[UnifiedLead]):
        """
        Called when a new property is added that matches existing leads
        Sends immediate notification to matched leads
        """
        from backend.database import TenantProperty
        
        async with async_session() as session:
            # Get property details
            result = await session.execute(
                select(TenantProperty).where(TenantProperty.id == property_id)
            )
            property = result.scalar_one()
            
            for lead in matched_leads:
                message = self._generate_property_notification(lead, property)
                
                # Send immediately (not scheduled)
                try:
                    telegram_id = getattr(lead, 'telegram_user_id', None)
                    whatsapp_num = getattr(lead, 'whatsapp_number', None)
                    lead_id = int(getattr(lead, 'id', 0))
                    lead_name = getattr(lead, 'name', 'Unknown')
                    
                    if telegram_id:
                        await self.send_telegram_message(int(telegram_id), message)
                        channel = InteractionChannel.TELEGRAM
                    elif whatsapp_num:
                        await self.send_whatsapp_message(str(whatsapp_num), message)
                        channel = InteractionChannel.WHATSAPP
                    else:
                        continue
                    
                    # Log interaction
                    await log_interaction(
                        session=session,
                        lead_id=lead_id,
                        channel=channel,
                        direction=InteractionDirection.OUTBOUND,
                        message_text=message,
                        ai_generated=True
                    )
                    
                    # Update matched_properties
                    matched_props = getattr(lead, 'matched_properties', None)
                    if not matched_props:
                        lead.matched_properties = []  # type: ignore
                    if property_id not in matched_props:
                        lead.matched_properties.append(property_id)  # type: ignore
                    
                    print(f"   ✅ Notified {lead_name} about new property match")
                    
                except Exception as e:
                    print(f"   ❌ Failed to notify {lead_name}: {e}")
            
            await session.commit()
    
    def _generate_property_notification(self, lead: UnifiedLead, property) -> str:
        """Generate property match notification message"""
        lead_lang = getattr(lead, 'language', None)
        lead_name = getattr(lead, 'name', 'there')
        language = lead_lang.value if lead_lang else 'en'
        
        templates = {
            'en': f"""
🏠 NEW PROPERTY MATCH FOR YOU!

Hi {lead_name}!

A new property just became available that matches your preferences:

📍 Location: {property.location or 'Dubai'}
💰 Price: {property.price:,.0f} AED
🛏️ Bedrooms: {property.bedrooms or 'N/A'}
🏢 Type: {property.type.value if property.type else 'N/A'}

This is exactly what you were looking for!

Want to see photos and full details? Reply YES!
            """.strip(),
            
            'fa': f"""
🏠 ملک جدید مطابق سلیقه شما!

سلام {lead.name}!

یه ملک جدید اضافه شد که دقیقا با نیازهای شما مچ می‌کنه:

📍 لوکیشن: {property.location or 'دبی'}
💰 قیمت: {property.price:,.0f} درهم
🛏️ تعداد خواب: {property.bedrooms or 'نامشخص'}
🏢 نوع: {property.type.value if property.type else 'نامشخص'}

دقیقا همونیه که دنبالش بودی!

می‌خوای عکس‌ها و جزئیات کامل رو ببینی؟ جواب بده!
            """.strip()
        }
        
        return templates.get(language, templates['en'])


# Global instance
followup_engine = FollowupEngine()


# ==================== API Functions ====================

async def start_followup_engine():
    """Start the follow-up engine (called from main.py)"""
    followup_engine.start()


async def stop_followup_engine():
    """Stop the follow-up engine"""
    followup_engine.stop()


async def schedule_linkedin_lead_followup(lead_id: int):
    """Schedule follow-up for a new LinkedIn lead"""
    async with async_session() as session:
        result = await session.execute(
            select(UnifiedLead).where(UnifiedLead.id == lead_id)
        )
        lead = result.scalar_one_or_none()
        if lead:
            await followup_engine.notify_new_linkedin_lead(lead)



async def notify_property_added(property_id: int) -> int:
    """
    Notify matched leads about a new property
    Returns: number of leads notified
    """
    from backend.unified_database import find_matching_leads_for_property
    from backend.database import TenantProperty
    
    try:
        async with async_session() as session:
            # ✅ FIX: Verify property exists
            result = await session.execute(
                select(TenantProperty).where(TenantProperty.id == property_id)
            )
            property = result.scalar_one_or_none()
            
            if not property:
                print(f"   ⚠️  Property {property_id} not found")
                return 0
            
            # Find all matching leads
            matched_leads = await find_matching_leads_for_property(
                session, property_id, property.tenant_id
            )
            
            if not matched_leads:
                print(f"   ℹ️  No matching leads found for property {property_id}")
                return 0
            
            notified_count = 0
            
            for lead in matched_leads:
                try:
                    await followup_engine.notify_property_match(property_id, [lead])
                    notified_count += 1
                except Exception as e:
                    print(f"   ❌ Failed to notify {lead.name}: {e}")
                    continue
            
            return notified_count
            
    except Exception as e:
        print(f"   ❌ Error in notify_property_added: {e}")
        return 0


if __name__ == "__main__":
    # Test the engine
    async def test():
        await start_followup_engine()
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            await stop_followup_engine()
    
    asyncio.run(test())
