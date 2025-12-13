"""
Unified Database Schema for ArtinSmartRealty
Merges LinkedIn Lead Scraper + Real Estate Bot into One Platform
"""

import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, Enum as SQLEnum, JSON, Float, DECIMAL,
    UniqueConstraint, Index
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship

# ✅ FIX: Import only enums and session factory, not Base/engine
from database import (
    Language, TransactionType, PropertyType, PaymentMethod, 
    Purpose, PainPoint, ConversationState, SubscriptionStatus,
    async_session, Base  # Use existing Base from database.py
)


# ==================== NEW ENUMS ====================

class LeadSource(str, Enum):
    """Source of the lead"""
    LINKEDIN = "linkedin"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    MANUAL = "manual"
    REFERRAL = "referral"


class LeadStatus(str, Enum):
    """Lead status in sales pipeline"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    VIEWING_SCHEDULED = "viewing_scheduled"
    NEGOTIATING = "negotiating"
    WON = "won"
    LOST = "lost"
    NURTURING = "nurturing"


class LeadGrade(str, Enum):
    """Lead grading based on score"""
    A = "A"  # Hot Lead (80-100)
    B = "B"  # Warm Lead (60-79)
    C = "C"  # Cold Lead (40-59)
    D = "D"  # Very Cold (0-39)


class CampaignStatus(str, Enum):
    """Follow-up campaign status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"


class InteractionChannel(str, Enum):
    """Communication channel"""
    LINKEDIN = "linkedin"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    PHONE = "phone"


class InteractionDirection(str, Enum):
    """Message direction"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


# ==================== UNIFIED LEAD MODEL ====================

class UnifiedLead(Base):
    """
    Unified Lead Model - Merges LinkedIn Scraper + Bot Leads
    Single source of truth for all leads across all channels
    """
    __tablename__ = "unified_leads"
    
    # === Primary Key ===
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # === Multi-Tenant ===
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    # === Contact Information ===
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    
    # === Channel-Specific IDs (for deduplication) ===
    linkedin_url = Column(String(500), nullable=True, unique=True)
    telegram_user_id = Column(Integer, nullable=True, unique=True)
    whatsapp_number = Column(String(50), nullable=True, unique=True)
    
    # === Lead Source & Status ===
    source = Column(SQLEnum(LeadSource), nullable=False, default=LeadSource.LINKEDIN)
    status = Column(SQLEnum(LeadStatus), nullable=False, default=LeadStatus.NEW)
    
    # === Lead Scoring & Grading ===
    lead_score = Column(Integer, default=0)  # 0-100
    grade = Column(SQLEnum(LeadGrade), nullable=True)  # A, B, C, D
    
    # === Professional Info (from LinkedIn) ===
    job_title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    about = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    linkedin_experience = Column(JSON, nullable=True)  # Full experience history
    linkedin_posts = Column(JSON, nullable=True)  # Recent posts
    
    # === Language & Preferences ===
    language = Column(SQLEnum(Language), default=Language.EN)
    
    # === Real Estate Needs (from qualification) ===
    transaction_type = Column(SQLEnum(TransactionType), nullable=True)  # buy/rent
    property_type = Column(SQLEnum(PropertyType), nullable=True)
    budget_min = Column(DECIMAL(15, 2), nullable=True)
    budget_max = Column(DECIMAL(15, 2), nullable=True)
    bedrooms = Column(Integer, nullable=True)
    preferred_locations = Column(JSON, nullable=True)  # ["Dubai Marina", "Downtown"]
    purpose = Column(SQLEnum(Purpose), nullable=True)  # investment/living/residency
    payment_method = Column(SQLEnum(PaymentMethod), nullable=True)
    
    # === Pain Points & Psychology ===
    pain_points = Column(JSON, nullable=True)  # [PainPoint.INFLATION_RISK, ...]
    qualification_data = Column(JSON, nullable=True)  # Full conversation data
    
    # === Follow-up Management ===
    last_contacted_at = Column(DateTime, nullable=True)
    last_message = Column(Text, nullable=True)
    next_followup_at = Column(DateTime, nullable=True)
    followup_count = Column(Integer, default=0)
    conversation_state = Column(SQLEnum(ConversationState), nullable=True)
    
    # === Property Matching ===
    matched_properties = Column(JSON, nullable=True)  # [property_id1, property_id2, ...]
    viewed_properties = Column(JSON, nullable=True)  # [property_id1, ...]
    favorited_properties = Column(JSON, nullable=True)  # [property_id1, ...]
    
    # === Engagement Tracking ===
    total_messages_sent = Column(Integer, default=0)
    total_messages_received = Column(Integer, default=0)
    last_active_at = Column(DateTime, nullable=True)
    
    # === Appointment & Sales ===
    scheduled_viewing_at = Column(DateTime, nullable=True)
    scheduled_viewing_property_id = Column(Integer, nullable=True)
    
    # === Notes & Tags ===
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # ["hot", "investor", "golden_visa"]
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === Relationships ===
    tenant = relationship("Tenant", back_populates="unified_leads")
    interactions = relationship("LeadInteraction", back_populates="lead", cascade="all, delete-orphan")
    
    # === Indexes for Performance ===
    __table_args__ = (
        Index('idx_unified_leads_status', 'status'),
        Index('idx_unified_leads_score', 'lead_score'),
        Index('idx_unified_leads_source', 'source'),
        Index('idx_unified_leads_next_followup', 'next_followup_at'),
        Index('idx_unified_leads_tenant_status', 'tenant_id', 'status'),
    )
    
    def calculate_score(self) -> int:
        """
        Auto-calculate lead score based on multiple factors
        Returns score between 0-100
        ✅ FIX: Use getattr to avoid SQLAlchemy Column type errors
        """
        score = 0
        
        # 1. Contact Information Completeness (20 points)
        phone = getattr(self, 'phone', None)
        email = getattr(self, 'email', None)
        linkedin = getattr(self, 'linkedin_url', None)
        job = getattr(self, 'job_title', None)
        
        if phone and str(phone).strip(): score += 5
        if email and str(email).strip(): score += 5
        if linkedin and str(linkedin).strip(): score += 5
        if job and str(job).strip(): score += 5
        
        # 2. Engagement Level (30 points)
        followup_count = getattr(self, 'followup_count', 0) or 0
        total_received = getattr(self, 'total_messages_received', 0) or 0
        last_active = getattr(self, 'last_active_at', None)
        
        if followup_count > 0: score += 5
        if total_received > 0: score += 10
        if total_received >= 3: score += 10
        if last_active and (datetime.utcnow() - last_active).days < 7:
            score += 5
        
        # 3. Qualification Level (30 points)
        budget_min = getattr(self, 'budget_min', None)
        budget_max = getattr(self, 'budget_max', None)
        prop_type = getattr(self, 'property_type', None)
        locations = getattr(self, 'preferred_locations', None)
        trans_type = getattr(self, 'transaction_type', None)
        purpose = getattr(self, 'purpose', None)
        
        if budget_min and budget_max: score += 10
        if prop_type: score += 5
        if locations: score += 5
        if trans_type: score += 5
        if purpose: score += 5
        
        # 4. Action & Intent (20 points)
        viewed = getattr(self, 'viewed_properties', None)
        favorited = getattr(self, 'favorited_properties', None)
        
        if viewed: score += 5
        if favorited: score += 5
        if last_active: score += 10  # Active engagement
        
        return min(score, 100)  # Cap at 100
    
    def assign_grade(self) -> LeadGrade:
        """Assign grade based on score"""
        # ✅ FIX: Handle None/NULL scores safely + use plain int comparison
        score = getattr(self, 'lead_score', None)
        if score is None:
            score = 0
        
        # Plain int comparison (not Column)
        if int(score) >= 80:
            return LeadGrade.A
        elif int(score) >= 60:
            return LeadGrade.B
        elif int(score) >= 40:
            return LeadGrade.C
        else:
            return LeadGrade.D
    
    def update_score_and_grade(self):
        """Convenience method to update both score and grade"""
        self.lead_score = self.calculate_score()
        self.grade = self.assign_grade()


# ==================== LEAD INTERACTIONS ====================

class LeadInteraction(Base):
    """
    Track all interactions with leads across all channels
    """
    __tablename__ = "lead_interactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey('unified_leads.id', ondelete='CASCADE'), nullable=False)
    
    # === Interaction Details ===
    channel = Column(SQLEnum(InteractionChannel), nullable=False)
    direction = Column(SQLEnum(InteractionDirection), nullable=False)
    message_text = Column(Text, nullable=True)
    
    # === AI & Automation ===
    ai_generated = Column(Boolean, default=False)
    campaign_id = Column(Integer, ForeignKey('followup_campaigns.id'), nullable=True)
    
    # === Metadata ===
    interaction_metadata = Column(JSON, nullable=True)  # Store raw message data, attachments, etc.
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # === Relationships ===
    lead = relationship("UnifiedLead", back_populates="interactions")
    campaign = relationship("FollowupCampaign", back_populates="interactions")
    
    # === Indexes ===
    __table_args__ = (
        Index('idx_interactions_lead', 'lead_id'),
        Index('idx_interactions_created', 'created_at'),
    )


# ==================== FOLLOW-UP CAMPAIGNS ====================

class FollowupCampaign(Base):
    """
    Automated follow-up campaigns for leads
    """
    __tablename__ = "followup_campaigns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    # === Campaign Details ===
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # === Trigger Configuration ===
    trigger_type = Column(String(50), nullable=False)  # 'new_property', 'scheduled', 'manual'
    trigger_config = Column(JSON, nullable=True)  # Additional trigger parameters
    
    # === Target Filters ===
    target_status = Column(JSON, nullable=True)  # [LeadStatus.NEW, LeadStatus.CONTACTED]
    min_score = Column(Integer, nullable=True)
    max_score = Column(Integer, nullable=True)
    target_sources = Column(JSON, nullable=True)  # [LeadSource.LINKEDIN, ...]
    
    # === Message Configuration ===
    message_template = Column(Text, nullable=False)
    personalization_enabled = Column(Boolean, default=True)
    
    # === Channel Selection ===
    channels = Column(JSON, nullable=False)  # ["telegram", "whatsapp"]
    
    # === Schedule ===
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT)
    scheduled_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    
    # === Statistics ===
    total_targeted = Column(Integer, default=0)
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_replied = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    
    # === Settings ===
    active = Column(Boolean, default=True)
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === Relationships ===
    tenant = relationship("Tenant", back_populates="followup_campaigns")
    interactions = relationship("LeadInteraction", back_populates="campaign")


# ==================== PROPERTY MATCHING CACHE ====================

class PropertyLeadMatch(Base):
    """
    Cache of property-lead matches for fast querying
    """
    __tablename__ = "property_lead_matches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Integer, ForeignKey('properties.id'), nullable=False)
    lead_id = Column(Integer, ForeignKey('unified_leads.id'), nullable=False)
    
    # === Match Score ===
    match_score = Column(Float, nullable=True)  # 0.0 - 1.0
    match_reasons = Column(JSON, nullable=True)  # ["budget_match", "location_match", ...]
    
    # === Status ===
    notified = Column(Boolean, default=False)
    notified_at = Column(DateTime, nullable=True)
    
    # === Timestamps ===
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # === Unique Constraint ===
    __table_args__ = (
        UniqueConstraint('property_id', 'lead_id', name='unique_property_lead'),
        Index('idx_matches_property', 'property_id'),
        Index('idx_matches_lead', 'lead_id'),
        Index('idx_matches_notified', 'notified'),
    )


# ==================== UPDATE TENANT MODEL ====================

# Add relationships to existing Tenant model (in database.py)
# This will be done via migration


# ==================== HELPER FUNCTIONS ====================

async def find_or_create_lead(
    session: AsyncSession,
    tenant_id: int,
    data: Dict[str, Any]
) -> tuple[UnifiedLead, bool]:
    """
    Find existing lead or create new one
    Uses multiple deduplication strategies
    
    Returns: (lead, created)
    """
    # ✅ FIX: Validate tenant_id
    if not tenant_id or tenant_id <= 0:
        raise ValueError(f"Invalid tenant_id: {tenant_id}")
    
    # ✅ FIX: Sanitize and validate LinkedIn URL
    linkedin_url = data.get('linkedin_url', '').strip() if data.get('linkedin_url') else None
    
    # Strategy 1: Check LinkedIn URL
    if linkedin_url:
        result = await session.execute(
            select(UnifiedLead).where(
                UnifiedLead.tenant_id == tenant_id,  # ✅ FIX: Add tenant isolation
                UnifiedLead.linkedin_url == linkedin_url
            )
        )
        lead = result.scalar_one_or_none()
        if lead:
            # Update with new data (only non-empty values)
            for key, value in data.items():
                if value and (isinstance(value, (int, float, bool)) or value.strip()):
                    current_val = getattr(lead, key, None)
                    if not current_val:
                        setattr(lead, key, value)
            lead.updated_at = datetime.utcnow()  # type: ignore
            return lead, False
    
    # Strategy 2: Check Telegram User ID
    if data.get('telegram_user_id'):
        result = await session.execute(
            select(UnifiedLead).where(
                UnifiedLead.telegram_user_id == data['telegram_user_id']
            )
        )
        lead = result.scalar_one_or_none()
        if lead:
            for key, value in data.items():
                if value and not getattr(lead, key):
                    setattr(lead, key, value)
            lead.updated_at = datetime.utcnow()  # type: ignore
            return lead, False
    
    # Strategy 3: Check WhatsApp Number
    if data.get('whatsapp_number'):
        result = await session.execute(
            select(UnifiedLead).where(
                UnifiedLead.whatsapp_number == data['whatsapp_number']
            )
        )
        lead = result.scalar_one_or_none()
        if lead:
            for key, value in data.items():
                if value and not getattr(lead, key):
                    setattr(lead, key, value)
            lead.updated_at = datetime.utcnow()  # type: ignore
            return lead, False
    
    # Strategy 4: Check phone number
    if data.get('phone'):
        result = await session.execute(
            select(UnifiedLead).where(
                UnifiedLead.phone == data['phone'],
                UnifiedLead.tenant_id == tenant_id
            )
        )
        lead = result.scalar_one_or_none()
        if lead:
            for key, value in data.items():
                if value and not getattr(lead, key):
                    setattr(lead, key, value)
            lead.updated_at = datetime.utcnow()  # type: ignore
            return lead, False
    
    # Not found - create new lead
    lead = UnifiedLead(tenant_id=tenant_id, **data)
    lead.update_score_and_grade()
    session.add(lead)
    await session.commit()
    await session.refresh(lead)
    
    return lead, True


async def log_interaction(
    session: AsyncSession,
    lead_id: int,
    channel: InteractionChannel,
    direction: InteractionDirection,
    message_text: str,
    ai_generated: bool = False,
    campaign_id: Optional[int] = None,  # ✅ FIX: Optional type
    metadata: Optional[Dict] = None  # ✅ FIX: Optional type
):
    """Log an interaction with a lead"""
    interaction = LeadInteraction(
        lead_id=lead_id,
        channel=channel,
        direction=direction,
        message_text=message_text,
        ai_generated=ai_generated,
        campaign_id=campaign_id,
        interaction_metadata=metadata
    )
    session.add(interaction)
    
    # Update lead stats
    result = await session.execute(
        select(UnifiedLead).where(UnifiedLead.id == lead_id)
    )
    lead = result.scalar_one()
    
    if direction == InteractionDirection.OUTBOUND:
        lead.total_messages_sent += 1  # type: ignore
        lead.last_contacted_at = datetime.utcnow()  # type: ignore
        lead.last_message = message_text  # type: ignore
    else:
        lead.total_messages_received += 1  # type: ignore
        lead.last_active_at = datetime.utcnow()  # type: ignore
    
    lead.update_score_and_grade()
    
    await session.commit()


async def find_matching_leads_for_property(
    session: AsyncSession,
    property_id: int,
    tenant_id: int
) -> List[UnifiedLead]:
    """
    Find all leads that match a property's criteria
    ✅ FIXED: Better validation, NULL handling, and performance
    """
    # ✅ FIX: Validate inputs
    if not property_id or property_id <= 0:
        raise ValueError(f"Invalid property_id: {property_id}")
    if not tenant_id or tenant_id <= 0:
        raise ValueError(f"Invalid tenant_id: {tenant_id}")
    
    # Get property details
    from backend.database import TenantProperty
    result = await session.execute(
        select(TenantProperty).where(
            TenantProperty.id == property_id,
            TenantProperty.tenant_id == tenant_id  # ✅ FIX: Ensure tenant isolation
        )
    )
    property = result.scalar_one_or_none()
    
    # ✅ FIX: Handle property not found
    if not property:
        return []
    
    # Build query with proper NULL handling
    query = select(UnifiedLead).where(
        UnifiedLead.tenant_id == tenant_id,
        UnifiedLead.status.not_in([LeadStatus.WON, LeadStatus.LOST])
    )
    
    # ✅ FIX: Filter by budget with NULL checks
    prop_price = getattr(property, 'price', None)
    if prop_price and prop_price > 0:
        query = query.where(
            UnifiedLead.budget_min.isnot(None),
            UnifiedLead.budget_max.isnot(None),
            UnifiedLead.budget_min <= prop_price,
            UnifiedLead.budget_max >= prop_price
        )
    
    # ✅ FIX: Filter by property type with NULL check
    prop_type = getattr(property, 'type', None)
    if prop_type:
        query = query.where(
            UnifiedLead.property_type == prop_type
        )
    
    # ✅ FIX: Filter by transaction type with NULL check
    prop_trans_type = getattr(property, 'transaction_type', None)
    if prop_trans_type:
        query = query.where(
            UnifiedLead.transaction_type == prop_trans_type
        )
    
    # ✅ FIX: Add limit to prevent performance issues
    query = query.limit(500)
    
    result = await session.execute(query)
    leads = result.scalars().all()
    
    # ✅ FIX: Better location matching with NULL checks
    matched_leads = []
    for lead in leads:
        # Check if lead has contact method (Telegram or WhatsApp)
        telegram_id = getattr(lead, 'telegram_user_id', None)
        whatsapp_num = getattr(lead, 'whatsapp_number', None)
        
        if not telegram_id and not whatsapp_num:
            continue  # Skip leads we can't contact
        
        # Check preferred locations
        prop_location = getattr(property, 'location', None)
        lead_locations = getattr(lead, 'preferred_locations', None)
        
        if prop_location:
            if lead_locations:
                # Normalize for comparison (case-insensitive)
                property_location_lower = str(prop_location).lower().strip()
                preferred_lower = [str(loc).lower().strip() for loc in lead_locations]
                if property_location_lower in preferred_lower:
                    matched_leads.append(lead)
            else:
                # No location preference = interested in all locations
                matched_leads.append(lead)
        else:
            # Property has no location, still match
            matched_leads.append(lead)
    
    return matched_leads


# ==================== EXPORT ====================

__all__ = [
    'UnifiedLead',
    'LeadInteraction',
    'FollowupCampaign',
    'PropertyLeadMatch',
    'LeadSource',
    'LeadStatus',
    'LeadGrade',
    'CampaignStatus',
    'InteractionChannel',
    'InteractionDirection',
    'find_or_create_lead',
    'log_interaction',
    'find_matching_leads_for_property',
]
