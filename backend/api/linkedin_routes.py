"""
LinkedIn Lead Scraper Integration Routes
Connects Chrome Extension to Unified System
⚠️ PRO PLAN ONLY - Requires subscription check
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import google.generativeai as genai
import os

from database import async_session, Tenant
from unified_database import (
    UnifiedLead, LeadSource, LeadStatus,
    find_or_create_lead, log_interaction,
    InteractionChannel, InteractionDirection
)
from followup_engine import schedule_linkedin_lead_followup
from subscription_guard import check_feature_access, check_subscription_active
from sqlalchemy import select, func, and_

router = APIRouter(prefix="/api/linkedin", tags=["LinkedIn Scraper"])

# Initialize Gemini AI (FREE API)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)  # type: ignore
    gemini_model = genai.GenerativeModel('gemini-pro')  # type: ignore
else:
    gemini_model = None


# ==================== HELPER FUNCTIONS ====================

def extract_email_from_text(text: str) -> Optional[str]:
    """Extract email from LinkedIn about section"""
    if not text:
        return None
    
    import re
    # Simple email regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    
    return matches[0] if matches else None


def extract_phone_from_text(text: str) -> Optional[str]:
    """Extract phone number from LinkedIn about section"""
    if not text:
        return None
    
    import re
    # Phone patterns (various formats)
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'  # US format
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Clean and return first match
            phone = matches[0].strip()
            # Remove common words that might match
            if len(phone) >= 10:  # Valid phone should be at least 10 digits
                return phone
    
    return None


# ==================== REQUEST/RESPONSE MODELS ====================

class Experience(BaseModel):
    """LinkedIn experience entry"""
    title: str = ""
    company: str = ""
    duration: str = ""


class RecentPost(BaseModel):
    """LinkedIn post"""
    text: str
    timestamp: str = ""


class ProfileData(BaseModel):
    """LinkedIn profile data from Chrome Extension"""
    name: str
    about: str = ""
    experience: List[Experience] = []
    recentPosts: List[RecentPost] = []
    profileUrl: str = ""


class GenerateMessageRequest(BaseModel):
    """Request for generating personalized LinkedIn message"""
    profileData: ProfileData
    productDescription: str
    tenantId: int = Field(default=1, ge=1)  # Multi-tenant support


class GenerateMessageResponse(BaseModel):
    """Response with generated message"""
    message: str
    tokensUsed: Optional[int] = None
    model: str = "gemini-pro"
    leadId: Optional[int] = None  # NEW: Return lead ID for tracking


class SaveLeadRequest(BaseModel):
    """Request to save LinkedIn lead"""
    profileData: ProfileData
    generatedMessage: Optional[str] = None
    tenantId: int = Field(default=1, ge=1)


class SaveLeadResponse(BaseModel):
    """Response after saving lead"""
    success: bool
    message: str
    leadId: int
    duplicate: bool = False


class LeadResponse(BaseModel):
    """LinkedIn lead response"""
    id: int
    name: str
    linkedin_url: Optional[str]
    job_title: Optional[str]
    company: Optional[str]
    lead_score: int
    grade: Optional[str]
    status: str
    created_at: datetime
    next_followup_at: Optional[datetime]


# ==================== ENDPOINTS ====================

@router.post("/generate-message", response_model=GenerateMessageResponse)
async def generate_linkedin_message(request: GenerateMessageRequest):
    """
    Generate personalized LinkedIn cold DM using Gemini AI.
    ⚠️ PRO PLAN ONLY - Requires active Pro subscription.
    """
    
    # ✅ STEP 1: Check Subscription & Feature Access
    async with async_session() as session:
        # Get tenant
        result = await session.execute(
            select(Tenant).where(Tenant.id == request.tenantId)
        )
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Check subscription active
        if not check_subscription_active(tenant):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "subscription_expired",
                    "message": "Your subscription has expired. Please renew to continue using LinkedIn Scraper.",
                    "message_fa": "اشتراک شما منقضی شده است. برای استفاده از اسکرپر لینکدین، لطفا اشتراک خود را تمدید کنید.",
                    "upgrade_url": "/subscription/pricing"
                }
            )
        
        # Check Pro plan access
        if not check_feature_access(tenant, "linkedin_scraper"):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "upgrade_required",
                    "feature": "linkedin_scraper",
                    "current_plan": tenant.subscription_plan.value if tenant.subscription_plan else "free",  # type: ignore
                    "required_plan": "pro",
                    "message": "LinkedIn Scraper is a Pro Plan feature. Upgrade to unlock lead generation!",
                    "message_fa": "اسکرپر لینکدین ویژگی پلن Pro است. برای دسترسی به لید جنریشن، ارتقا دهید!",
                    "upgrade_url": "/subscription/pricing"
                }
            )
    
    # ✅ STEP 2: Validate Gemini API
    if not GEMINI_API_KEY or not gemini_model:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key not configured. Get free key at: https://aistudio.google.com/app/apikey"
        )
    
    # ✅ Validate input
    if not request.profileData.name or not request.profileData.name.strip():
        raise HTTPException(status_code=400, detail="Profile name is required")
    
    if not request.productDescription or not request.productDescription.strip():
        raise HTTPException(status_code=400, detail="Product description is required")
    
    profile = request.profileData
    product = request.productDescription.strip()
    
    # ✅ Check if profile has real posts
    has_real_posts = (
        profile.recentPosts and 
        len(profile.recentPosts) > 0 and 
        profile.recentPosts[0].text != '[NO_POSTS_FOUND_USE_ABOUT]'
    )
    
    try:
        # Build context
        current_position = ""
        if profile.experience and len(profile.experience) > 0:
            exp = profile.experience[0]
            current_position = f"{exp.title} at {exp.company}".strip()
        
        # Different prompts based on data availability
        if has_real_posts:
            # Use recent post for personalization
            recent_post = profile.recentPosts[0].text[:300]
            
            prompt = f"""You are an expert copywriter specializing in cold outreach using the 'Pain-Agitate-Solution' framework.

Your task is to write highly personalized LinkedIn cold DMs that feel genuine, not salesy.

CRITICAL RULES:
1. ALWAYS start by referencing their recent post - prove you actually read it
2. Keep the message under 75 words (this is strict)
3. Use casual, professional tone - no corporate jargon
4. End with a low-friction question, NOT a hard pitch
5. Never use phrases like "I noticed", "I came across", "reaching out"
6. Be specific about their post topic, don't be generic

FRAMEWORK:
- Hook: Mention their recent post genuinely
- Bridge: Connect it to a pain point your product solves
- Soft CTA: Ask a question worth responding to

---

Generate a personalized cold DM for this person:

NAME: {profile.name}
CURRENT ROLE: {current_position or 'Not specified'}
RECENT POST TOPIC: {recent_post}

MY PRODUCT/SERVICE: {product}

Write the cold DM now. Remember: Under 75 words, start with their post, end with a question.

OUTPUT ONLY THE MESSAGE - NO EXPLANATIONS OR EXTRA TEXT."""
        
        else:
            # Use About section for personalization
            about = profile.about[:500] if profile.about else ""
            
            prompt = f"""You are an expert copywriter specializing in personalized cold outreach.

Your task is to write a genuine LinkedIn cold DM based on their profile.

CRITICAL RULES:
1. Reference their role/background to show you read their profile
2. Keep the message under 75 words
3. Use casual, professional tone
4. End with a low-friction question
5. Don't be salesy - be helpful

Generate a personalized cold DM for this person:

NAME: {profile.name}
CURRENT ROLE: {current_position or 'Professional'}
ABOUT: {about or 'No bio available'}

MY PRODUCT/SERVICE: {product}

Write the cold DM now. Remember: Under 75 words, reference their background, end with a question.

OUTPUT ONLY THE MESSAGE - NO EXPLANATIONS OR EXTRA TEXT."""
        
        # Generate message using Gemini
        response = gemini_model.generate_content(prompt)
        generated_message = response.text.strip()
        
        # ✅ Save lead to unified system
        async with async_session() as session:
            # Find or create lead
            lead_data = {
                'source': LeadSource.LINKEDIN,
                'name': profile.name.strip(),
                'linkedin_url': profile.profileUrl.strip() if profile.profileUrl else None,
                'email': None,  # Will be extracted if available
                'phone': None,
                'job_title': current_position or None,
                'company': profile.experience[0].company if profile.experience else None,
                'about': profile.about[:1000] if profile.about else None,
                'location': None,
                'linkedin_data': {
                    'experience': [exp.dict() for exp in profile.experience],
                    'recent_posts': [post.dict() for post in profile.recentPosts]
                }
            }
            
            lead, created = await find_or_create_lead(
                session=session,
                tenant_id=request.tenantId,
                data=lead_data
            )
            
            # ✅ Log interaction (message generated)
            lead_id = int(getattr(lead, 'id', 0))
            await log_interaction(
                session=session,
                lead_id=lead_id,
                channel=InteractionChannel.LINKEDIN,
                direction=InteractionDirection.OUTBOUND,
                message_text=generated_message,
                metadata={'generated_by': 'gemini-pro', 'has_posts': has_real_posts}
            )
            
            # ✅ Schedule follow-up (if lead has contact info)
            telegram_id = getattr(lead, 'telegram_user_id', None)
            whatsapp_num = getattr(lead, 'whatsapp_number', None)
            if telegram_id or whatsapp_num:
                await schedule_linkedin_lead_followup(lead_id)
            
            await session.commit()
            
            return GenerateMessageResponse(
                message=generated_message,
                tokensUsed=None,  # Gemini doesn't provide this easily
                model="gemini-pro",
                leadId=lead_id
            )
    
    except Exception as e:
        error_msg = str(e)
        
        # Handle common Gemini errors
        if "API_KEY_INVALID" in error_msg or "invalid api key" in error_msg.lower():
            raise HTTPException(
                status_code=401,
                detail="Invalid Gemini API key. Get free key at: https://aistudio.google.com/app/apikey"
            )
        elif "quota" in error_msg.lower() or "rate" in error_msg.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini rate limit exceeded. Please wait a minute and try again."
            )
        else:
            print(f"❌ Error generating LinkedIn message: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate message: {error_msg}"
            )


@router.post("/add-lead", response_model=SaveLeadResponse)
async def add_linkedin_lead(request: SaveLeadRequest):
    """
    Save LinkedIn lead to unified system
    This replaces the old /api/save-lead endpoint
    """
    
    # ✅ Validate input
    if not request.profileData.name or not request.profileData.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    
    if not request.profileData.profileUrl or not request.profileData.profileUrl.strip():
        raise HTTPException(status_code=400, detail="LinkedIn URL is required")
    
    profile = request.profileData
    
    try:
        async with async_session() as session:
            # Extract job title and company
            job_title = None
            company = None
            if profile.experience and len(profile.experience) > 0:
                job_title = profile.experience[0].title.strip() if profile.experience[0].title else None
                company = profile.experience[0].company.strip() if profile.experience[0].company else None
            
            # ✅ FIX: Extract email and phone from about section
            email = extract_email_from_text(profile.about) if profile.about else None
            phone = extract_phone_from_text(profile.about) if profile.about else None
            
            # ✅ Find or create lead
            lead_data = {
                'source': LeadSource.LINKEDIN,
                'name': profile.name.strip(),
                'linkedin_url': profile.profileUrl.strip(),
                'email': email,  # ✅ Extracted from about
                'phone': phone,  # ✅ Extracted from about
                'job_title': job_title,
                'company': company,
                'about': profile.about[:1000] if profile.about else None,
                'location': None,
                'linkedin_data': {
                    'experience': [exp.dict() for exp in profile.experience],
                    'recent_posts': [post.dict() for post in profile.recentPosts]
                }
            }
            
            lead, created = await find_or_create_lead(
                session=session,
                tenant_id=request.tenantId,
                data=lead_data
            )
            
            # ✅ Save generated message if provided
            lead_id = int(getattr(lead, 'id', 0))
            if request.generatedMessage and request.generatedMessage.strip():
                await log_interaction(
                    session=session,
                    lead_id=lead_id,
                    channel=InteractionChannel.LINKEDIN,
                    direction=InteractionDirection.OUTBOUND,
                    message_text=request.generatedMessage.strip(),
                    metadata={'source': 'chrome_extension'}
                )
            
            await session.commit()
            
            # Check if it was a duplicate
            lead_created_at = getattr(lead, 'created_at', datetime.utcnow())
            was_existing = lead_created_at < datetime.utcnow() - timedelta(seconds=5)
            
            # Schedule follow-up if new lead has contact info
            telegram_id = getattr(lead, 'telegram_user_id', None)
            whatsapp_num = getattr(lead, 'whatsapp_number', None)
            if telegram_id or whatsapp_num:
                await schedule_linkedin_lead_followup(lead_id)
            
            return SaveLeadResponse(
                success=True,
                message='Lead added successfully' if not was_existing else 'Lead already exists',
                leadId=lead_id,
                duplicate=was_existing
            )
    
    except Exception as e:
        print(f"❌ Error saving LinkedIn lead: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save lead: {str(e)}"
        )


@router.get("/leads", response_model=List[LeadResponse])
async def get_linkedin_leads(
    tenant_id: int = 1,
    limit: int = 100,
    status: Optional[str] = None
):
    """
    Get all LinkedIn leads for a tenant
    """
    
    if limit > 1000:
        limit = 1000  # Safety limit
    
    try:
        async with async_session() as session:
            # Build query
            query = select(UnifiedLead).where(
                and_(
                    UnifiedLead.tenant_id == tenant_id,
                    UnifiedLead.source == LeadSource.LINKEDIN
                )
            )
            
            # Filter by status if provided
            if status:
                try:
                    lead_status = LeadStatus(status)
                    query = query.where(UnifiedLead.status == lead_status)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
            
            # Order by created date descending
            query = query.order_by(UnifiedLead.created_at.desc()).limit(limit)
            
            result = await session.execute(query)
            leads = result.scalars().all()
            
            return [
                LeadResponse(
                    id=lead.id,
                    name=lead.name,
                    linkedin_url=lead.linkedin_url,
                    job_title=lead.job_title,
                    company=lead.company,
                    lead_score=lead.lead_score or 0,
                    grade=lead.grade.value if lead.grade else None,
                    status=lead.status.value,
                    created_at=lead.created_at,
                    next_followup_at=lead.next_followup_at
                )
                for lead in leads
            ]
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching LinkedIn leads: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch leads: {str(e)}"
        )


@router.get("/stats")
async def get_linkedin_stats(tenant_id: int = 1):
    """
    Get LinkedIn lead statistics
    """
    
    try:
        async with async_session() as session:
            # Total LinkedIn leads
            total_query = select(func.count(UnifiedLead.id)).where(
                and_(
                    UnifiedLead.tenant_id == tenant_id,
                    UnifiedLead.source == LeadSource.LINKEDIN
                )
            )
            total_result = await session.execute(total_query)
            total_leads = total_result.scalar() or 0
            
            # By status
            status_query = select(
                UnifiedLead.status,
                func.count(UnifiedLead.id)
            ).where(
                and_(
                    UnifiedLead.tenant_id == tenant_id,
                    UnifiedLead.source == LeadSource.LINKEDIN
                )
            ).group_by(UnifiedLead.status)
            
            status_result = await session.execute(status_query)
            by_status = {row[0].value: row[1] for row in status_result.fetchall()}
            
            # By grade
            grade_query = select(
                UnifiedLead.grade,
                func.count(UnifiedLead.id)
            ).where(
                and_(
                    UnifiedLead.tenant_id == tenant_id,
                    UnifiedLead.source == LeadSource.LINKEDIN,
                    UnifiedLead.grade.isnot(None)
                )
            ).group_by(UnifiedLead.grade)
            
            grade_result = await session.execute(grade_query)
            by_grade = {row[0].value: row[1] for row in grade_result.fetchall() if row[0]}
            
            # Pending follow-ups
            followup_query = select(func.count(UnifiedLead.id)).where(
                and_(
                    UnifiedLead.tenant_id == tenant_id,
                    UnifiedLead.source == LeadSource.LINKEDIN,
                    UnifiedLead.next_followup_at.isnot(None),
                    UnifiedLead.next_followup_at <= datetime.utcnow()
                )
            )
            followup_result = await session.execute(followup_query)
            pending_followups = followup_result.scalar() or 0
            
            return {
                'total_leads': total_leads,
                'by_status': by_status,
                'by_grade': by_grade,
                'pending_followups': pending_followups,
                'source': 'linkedin'
            }
    
    except Exception as e:
        print(f"❌ Error fetching LinkedIn stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats: {str(e)}"
        )


@router.get("/health")
async def linkedin_health():
    """Health check for LinkedIn integration"""
    return {
        "status": "healthy",
        "gemini_configured": bool(GEMINI_API_KEY and gemini_model),
        "model": "gemini-pro (FREE)",
        "endpoints": [
            "/api/linkedin/generate-message",
            "/api/linkedin/add-lead",
            "/api/linkedin/leads",
            "/api/linkedin/stats"
        ]
    }
