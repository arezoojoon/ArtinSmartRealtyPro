"""
Unified API Routes for Lead Management
Connects LinkedIn Scraper + Bot into one system
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.database import async_session
from backend.unified_database import (
    UnifiedLead, LeadInteraction, FollowupCampaign,
    LeadSource, LeadStatus, LeadGrade,
    InteractionChannel, InteractionDirection,
    find_or_create_lead, log_interaction
)
from backend.followup_engine import schedule_linkedin_lead_followup, notify_property_added
from sqlalchemy import select, func, and_

router = APIRouter(prefix="/api/unified", tags=["Unified Leads"])


# ==================== REQUEST/RESPONSE MODELS ====================

class LinkedInLeadCreate(BaseModel):
    """Request model for adding LinkedIn lead"""
    name: str
    linkedin_url: str
    email: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    about: Optional[str] = None
    location: Optional[str] = None
    experience: Optional[List[Dict]] = None
    recent_posts: Optional[List[Dict]] = None
    generated_message: Optional[str] = None


class LeadResponse(BaseModel):
    """Response model for lead data"""
    id: int
    name: str
    source: str
    status: str
    lead_score: int
    grade: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    linkedin_url: Optional[str]
    job_title: Optional[str]
    company: Optional[str]
    created_at: datetime
    last_contacted_at: Optional[datetime]
    next_followup_at: Optional[datetime]
    followup_count: int
    
    class Config:
        from_attributes = True


class LeadStatsResponse(BaseModel):
    """Dashboard statistics"""
    total_leads: int
    by_source: Dict[str, int]
    by_status: Dict[str, int]
    by_grade: Dict[str, int]
    pending_followups: int


# ==================== LINKEDIN SCRAPER INTEGRATION ====================

@router.post("/linkedin/add-lead", response_model=LeadResponse)
async def add_linkedin_lead(lead_data: LinkedInLeadCreate, tenant_id: int = 1):
    """
    Add a new lead from LinkedIn Scraper
    This replaces the old /api/save-lead endpoint
    """
    # ✅ FIX: Validate input data
    if not lead_data.name or not lead_data.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    
    if not lead_data.linkedin_url or not lead_data.linkedin_url.strip():
        raise HTTPException(status_code=400, detail="LinkedIn URL is required")
    
    # ✅ FIX: Validate tenant_id
    if tenant_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid tenant_id")
    
    try:
        async with async_session() as session:
            # Prepare data
            data = {
                'name': lead_data.name.strip(),
                'linkedin_url': lead_data.linkedin_url.strip(),
                'email': lead_data.email.strip() if lead_data.email else None,
                'phone': lead_data.phone.strip() if lead_data.phone else None,
                'job_title': lead_data.job_title.strip() if lead_data.job_title else None,
                'company': lead_data.company.strip() if lead_data.company else None,
                'about': lead_data.about.strip() if lead_data.about else None,
                'location': lead_data.location.strip() if lead_data.location else None,
                'linkedin_experience': lead_data.experience,
                'linkedin_posts': lead_data.recent_posts,
                'source': LeadSource.LINKEDIN,
                'status': LeadStatus.NEW,
                'last_message': lead_data.generated_message.strip() if lead_data.generated_message else None,
            }
            
            # Find or create lead
            lead, created = await find_or_create_lead(session, tenant_id, data)
        
        # If new lead, schedule follow-up
        if created:
            await schedule_linkedin_lead_followup(lead)
            
            # Log the initial interaction (LinkedIn message generation)
            if lead_data.generated_message:
                await log_interaction(
                    session=session,
                    lead_id=lead.id,
                    channel=InteractionChannel.LINKEDIN,
                    direction=InteractionDirection.OUTBOUND,
                    message_text=lead_data.generated_message,
                    ai_generated=True
                )
        
        await session.commit()
        await session.refresh(lead)
        
        return lead


@router.get("/leads", response_model=List[LeadResponse])
async def get_all_leads(
    tenant_id: int = 1,
    source: Optional[str] = None,
    status: Optional[str] = None,
    grade: Optional[str] = None,
    limit: int = 100
):
    """
    Get all leads with optional filtering
    """
    async with async_session() as session:
        query = select(UnifiedLead).where(UnifiedLead.tenant_id == tenant_id)
        
        if source:
            query = query.where(UnifiedLead.source == source)
        if status:
            query = query.where(UnifiedLead.status == status)
        if grade:
            query = query.where(UnifiedLead.grade == grade)
        
        query = query.order_by(UnifiedLead.created_at.desc()).limit(limit)
        
        result = await session.execute(query)
        leads = result.scalars().all()
        
        return leads


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int):
    """Get a single lead by ID"""
    async with async_session() as session:
        result = await session.execute(
            select(UnifiedLead).where(UnifiedLead.id == lead_id)
        )
        lead = result.scalar_one_or_none()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return lead


@router.get("/stats", response_model=LeadStatsResponse)
async def get_lead_stats(tenant_id: int = 1):
    """
    Get dashboard statistics
    """
    async with async_session() as session:
        # Total leads
        result = await session.execute(
            select(func.count(UnifiedLead.id)).where(UnifiedLead.tenant_id == tenant_id)
        )
        total_leads = result.scalar()
        
        # By source
        result = await session.execute(
            select(
                UnifiedLead.source,
                func.count(UnifiedLead.id)
            ).where(
                UnifiedLead.tenant_id == tenant_id
            ).group_by(UnifiedLead.source)
        )
        by_source = {row[0].value: row[1] for row in result.all()}
        
        # By status
        result = await session.execute(
            select(
                UnifiedLead.status,
                func.count(UnifiedLead.id)
            ).where(
                UnifiedLead.tenant_id == tenant_id
            ).group_by(UnifiedLead.status)
        )
        by_status = {row[0].value: row[1] for row in result.all()}
        
        # By grade
        result = await session.execute(
            select(
                UnifiedLead.grade,
                func.count(UnifiedLead.id)
            ).where(
                UnifiedLead.tenant_id == tenant_id,
                UnifiedLead.grade.isnot(None)
            ).group_by(UnifiedLead.grade)
        )
        by_grade = {row[0].value: row[1] for row in result.all()}
        
        # Pending followups
        result = await session.execute(
            select(func.count(UnifiedLead.id)).where(
                and_(
                    UnifiedLead.tenant_id == tenant_id,
                    UnifiedLead.next_followup_at <= datetime.utcnow(),
                    UnifiedLead.status.in_([LeadStatus.NEW, LeadStatus.CONTACTED])
                )
            )
        )
        pending_followups = result.scalar()
        
        return LeadStatsResponse(
            total_leads=total_leads,
            by_source=by_source,
            by_status=by_status,
            by_grade=by_grade,
            pending_followups=pending_followups
        )


@router.put("/leads/{lead_id}/status")
async def update_lead_status(lead_id: int, status: str):
    """Update lead status"""
    async with async_session() as session:
        result = await session.execute(
            select(UnifiedLead).where(UnifiedLead.id == lead_id)
        )
        lead = result.scalar_one_or_none()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Validate status
        try:
            new_status = LeadStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        lead.status = new_status
        lead.update_score_and_grade()
        
        await session.commit()
        
        return {"success": True, "new_status": status}


@router.post("/leads/{lead_id}/note")
async def add_lead_note(lead_id: int, note: str):
    """Add a note to a lead"""
    async with async_session() as session:
        result = await session.execute(
            select(UnifiedLead).where(UnifiedLead.id == lead_id)
        )
        lead = result.scalar_one_or_none()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Append note with timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        new_note = f"[{timestamp}] {note}"
        
        if lead.notes:
            lead.notes += f"\n{new_note}"
        else:
            lead.notes = new_note
        
        await session.commit()
        
        return {"success": True, "note": new_note}


# ==================== PROPERTY MATCHING ====================

@router.post("/properties/{property_id}/notify-matches")
async def notify_property_matches(property_id: int, tenant_id: int = 1):
    """
    Called when a new property is added
    Finds and notifies all matching leads
    """
    # ✅ FIX: Validate property_id
    if property_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid property_id")
    
    try:
        # ✅ FIX: Verify property exists before notifying
        from backend.database import Property
        async with async_session() as session:
            result = await session.execute(
                select(Property).where(Property.id == property_id)
            )
            property = result.scalar_one_or_none()
            
            if not property:
                raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
            
            # ✅ FIX: Verify tenant ownership
            if property.tenant_id != tenant_id:
                raise HTTPException(status_code=403, detail="Access denied to this property")
        
        # Now notify
        matched_count = await notify_property_added(property_id)
        return {
            "success": True, 
            "message": f"Notified {matched_count} matched leads",
            "matched_count": matched_count
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in notify_property_matches: {e}")
        raise HTTPException(status_code=500, detail="Failed to notify matched leads")


@router.get("/leads/{lead_id}/matched-properties")
async def get_matched_properties(lead_id: int):
    """Get all properties matched to a lead"""
    async with async_session() as session:
        result = await session.execute(
            select(UnifiedLead).where(UnifiedLead.id == lead_id)
        )
        lead = result.scalar_one_or_none()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return {
            "lead_id": lead_id,
            "matched_properties": lead.matched_properties or [],
            "viewed_properties": lead.viewed_properties or [],
            "favorited_properties": lead.favorited_properties or []
        }


# ==================== FOLLOW-UP CAMPAIGNS ====================

class CampaignCreate(BaseModel):
    """Create a follow-up campaign"""
    name: str
    description: Optional[str] = None
    message_template: str
    target_status: Optional[List[str]] = None
    min_score: Optional[int] = None
    channels: List[str] = ["telegram", "whatsapp"]


@router.post("/campaigns", response_model=Dict)
async def create_followup_campaign(campaign_data: CampaignCreate, tenant_id: int = 1):
    """Create a new follow-up campaign"""
    async with async_session() as session:
        campaign = FollowupCampaign(
            tenant_id=tenant_id,
            name=campaign_data.name,
            description=campaign_data.description,
            message_template=campaign_data.message_template,
            target_status=campaign_data.target_status,
            min_score=campaign_data.min_score,
            channels=campaign_data.channels,
            trigger_type='manual'
        )
        
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)
        
        return {
            "success": True,
            "campaign_id": campaign.id,
            "name": campaign.name
        }


@router.get("/campaigns")
async def get_campaigns(tenant_id: int = 1):
    """Get all follow-up campaigns"""
    async with async_session() as session:
        result = await session.execute(
            select(FollowupCampaign).where(
                FollowupCampaign.tenant_id == tenant_id
            ).order_by(FollowupCampaign.created_at.desc())
        )
        campaigns = result.scalars().all()
        
        return [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status.value,
                "total_sent": c.total_sent,
                "total_replied": c.total_replied,
                "created_at": c.created_at
            }
            for c in campaigns
        ]


# ==================== INTERACTIONS ====================

@router.get("/leads/{lead_id}/interactions")
async def get_lead_interactions(lead_id: int, limit: int = 50):
    """Get all interactions for a lead"""
    async with async_session() as session:
        result = await session.execute(
            select(LeadInteraction).where(
                LeadInteraction.lead_id == lead_id
            ).order_by(LeadInteraction.created_at.desc()).limit(limit)
        )
        interactions = result.scalars().all()
        
        return [
            {
                "id": i.id,
                "channel": i.channel.value,
                "direction": i.direction.value,
                "message_text": i.message_text,
                "ai_generated": i.ai_generated,
                "created_at": i.created_at
            }
            for i in interactions
        ]


# ==================== EXPORT ====================

@router.get("/export/excel")
async def export_leads_to_excel(tenant_id: int = 1):
    """Export all leads to Excel"""
    import pandas as pd
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    async with async_session() as session:
        result = await session.execute(
            select(UnifiedLead).where(UnifiedLead.tenant_id == tenant_id)
        )
        leads = result.scalars().all()
        
        # Convert to DataFrame
        data = []
        for lead in leads:
            data.append({
                'ID': lead.id,
                'Name': lead.name,
                'Phone': lead.phone,
                'Email': lead.email,
                'LinkedIn': lead.linkedin_url,
                'Source': lead.source.value,
                'Status': lead.status.value,
                'Score': lead.lead_score,
                'Grade': lead.grade.value if lead.grade else '',
                'Job Title': lead.job_title,
                'Company': lead.company,
                'Budget Min': lead.budget_min,
                'Budget Max': lead.budget_max,
                'Property Type': lead.property_type.value if lead.property_type else '',
                'Created At': lead.created_at,
                'Last Contacted': lead.last_contacted_at,
                'Follow-up Count': lead.followup_count,
                'Notes': lead.notes
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Leads')
        
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename=leads_export_{datetime.now().strftime("%Y%m%d")}.xlsx'}
        )


# Export router
__all__ = ['router']
