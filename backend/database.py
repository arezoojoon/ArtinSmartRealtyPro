"""
ArtinSmartRealty V2 - Database Schema
Multi-Tenant Real Estate SaaS with Strict Data Isolation
"""

import os
from datetime import datetime, timedelta, time
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Time, Boolean, 
    ForeignKey, Enum as SQLEnum, JSON, Float, create_engine,
    UniqueConstraint
)
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.future import select
from sqlalchemy.pool import NullPool

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/artinrealty"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    poolclass=NullPool
)

# Async session factory
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()


# ==================== ENUMS ====================

class Language(str, Enum):
    EN = "en"
    FA = "fa"
    AR = "ar"
    RU = "ru"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    VIEWING_SCHEDULED = "viewing_scheduled"
    NEGOTIATING = "negotiating"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class TransactionType(str, Enum):
    BUY = "buy"
    RENT = "rent"


class PropertyType(str, Enum):
    APARTMENT = "apartment"
    VILLA = "villa"
    PENTHOUSE = "penthouse"
    TOWNHOUSE = "townhouse"
    STUDIO = "studio"
    COMMERCIAL = "commercial"
    LAND = "land"


class PaymentMethod(str, Enum):
    CASH = "cash"
    INSTALLMENT = "installment"
    MORTGAGE = "mortgage"


class Purpose(str, Enum):
    INVESTMENT = "investment"
    LIVING = "living"
    RESIDENCY = "residency"  # Golden Visa


class AppointmentType(str, Enum):
    ONLINE = "online"
    OFFICE = "office"
    VIEWING = "viewing"


class DayOfWeek(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class FeatureFlag(str, Enum):
    """Available features that can be enabled/disabled per tenant"""
    RAG_SYSTEM = "rag_system"  # Retrieval-Augmented Generation (Knowledge Base)
    VOICE_AI = "voice_ai"  # Voice call automation
    ADVANCED_ANALYTICS = "advanced_analytics"  # Advanced reporting & insights
    WHATSAPP_BOT = "whatsapp_bot"  # WhatsApp integration
    TELEGRAM_BOT = "telegram_bot"  # Telegram integration
    BROADCAST_MESSAGES = "broadcast_messages"  # Mass messaging
    LOTTERY_SYSTEM = "lottery_system"  # Gamification - lottery
    CALENDAR_BOOKING = "calendar_booking"  # Appointment scheduling
    LEAD_EXPORT = "lead_export"  # Export leads to CSV/Excel
    API_ACCESS = "api_access"  # REST API access
    CUSTOM_BRANDING = "custom_branding"  # White-label branding
    MULTI_LANGUAGE = "multi_language"  # 4 language support (FA/EN/AR/RU)


class PainPoint(str, Enum):
    """Pain points for Pain & Solution technique"""
    INFLATION_RISK = "inflation_risk"  # Currency devaluation fear
    VISA_INSECURITY = "visa_insecurity"  # Residency instability
    ASSET_PROTECTION = "asset_protection"  # Want to protect wealth
    RENTAL_INCOME = "rental_income"  # Want passive income
    FAMILY_FUTURE = "family_future"  # Children's education/future
    TAX_OPTIMIZATION = "tax_optimization"  # Tax-free benefits


class ConversationState(str, Enum):
    """Optimized State Machine for High-Ticket Real Estate Sales"""
    START = "start"
    LANGUAGE_SELECT = "language_select"
    COLLECTING_NAME = "collecting_name"  # Ask for customer's name after language
    
    # Phase 1: Warmup & Profiling (1-2 questions max)
    WARMUP = "warmup"  # Goal: Investment/Living/Residency
    
    # Phase 1.5: Capture Contact (Get phone number immediately after warmup)
    CAPTURE_CONTACT = "capture_contact"  # گرفتن شماره بلافاصله
    
    # Phase 2: Slot Filling (Qualify with context retention)
    SLOT_FILLING = "slot_filling"  # Collect: budget, property_type, location
    
    # Phase 3: Value Proposition (Show matching properties)
    VALUE_PROPOSITION = "value_proposition"  # Present solutions based on slots
    
    # Phase 4: Hard Gate (Capture contact)
    HARD_GATE = "hard_gate"  # Get phone for PDF/Follow-up
    
    # Phase 5: Engagement (Free conversation with context)
    ENGAGEMENT = "engagement"  # Answer questions, handle objections
    
    # Phase 6: Handoff (Schedule or Urgent Alert)
    HANDOFF_SCHEDULE = "handoff_schedule"  # Book appointment
    HANDOFF_URGENT = "handoff_urgent"  # Hot lead - immediate notification
    
    COMPLETED = "completed"


# ==================== MODELS ====================

class Tenant(Base):
    """
    Tenant represents an Agent/Company using the SaaS platform.
    All data is strictly isolated by tenant_id.
    """
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    logo_url = Column(String(512), nullable=True)
    phone = Column(String(50), nullable=True)
    company_name = Column(String(255), nullable=True)
    telegram_bot_token = Column(String(255), nullable=True, unique=True)
    email = Column(String(255), nullable=True, unique=True)
    
    # Authentication
    password_hash = Column(String(255), nullable=True)  # For login
    reset_token = Column(String(255), nullable=True)  # For password reset
    reset_token_expires = Column(DateTime, nullable=True)
    
    # WhatsApp Business API Settings
    whatsapp_phone_number_id = Column(String(100), nullable=True, unique=True)
    whatsapp_access_token = Column(String(512), nullable=True)
    whatsapp_business_account_id = Column(String(100), nullable=True)
    whatsapp_verify_token = Column(String(255), nullable=True)  # For webhook verification
    
    # Branding
    primary_color = Column(String(20), default="#D4AF37")  # Gold by default
    
    # Admin Settings
    admin_chat_id = Column(String(100), nullable=True)  # Telegram chat ID for admin notifications
    
    # Subscription
    subscription_status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
    trial_ends_at = Column(DateTime, nullable=True)
    
    # Settings
    default_language = Column(SQLEnum(Language), default=Language.EN)
    timezone = Column(String(50), default="Asia/Dubai")
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    leads = relationship("Lead", back_populates="tenant", cascade="all, delete-orphan")
    availabilities = relationship("AgentAvailability", back_populates="tenant", cascade="all, delete-orphan")
    features = relationship("TenantFeature", back_populates="tenant", cascade="all, delete-orphan")


class TenantFeature(Base):
    """
    Feature flags for each tenant - controls access to specific features.
    Super Admin can enable/disable features per tenant.
    """
    __tablename__ = "tenant_features"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    feature = Column(SQLEnum(FeatureFlag), nullable=False)
    is_enabled = Column(Boolean, default=True)
    
    # Metadata
    enabled_at = Column(DateTime, default=datetime.utcnow)
    enabled_by = Column(Integer, nullable=True)  # Admin user ID who enabled it
    notes = Column(String(500), nullable=True)  # Admin notes
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="features")
    
    # Unique constraint: one entry per tenant per feature
    __table_args__ = (
        UniqueConstraint('tenant_id', 'feature', name='uix_tenant_feature'),
    )


class Lead(Base):
    """
    Lead represents a potential client captured through Telegram, WhatsApp or other channels.
    Contains qualification data and voice transcripts.
    """
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic Info
    name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    telegram_chat_id = Column(String(100), nullable=True, index=True)  # Also used as telegram_user_id
    telegram_username = Column(String(100), nullable=True)
    whatsapp_phone = Column(String(50), nullable=True, index=True)  # WhatsApp phone number
    language = Column(String(10), default="en")  # Store as string to avoid enum uppercase issue
    
    # Lead Status
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW)
    
    # Qualification Fields
    transaction_type = Column(SQLEnum(TransactionType), nullable=True)
    property_type = Column(SQLEnum(PropertyType), nullable=True)
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    budget_currency = Column(String(10), default="AED")
    payment_method = Column(SQLEnum(PaymentMethod), nullable=True)
    purpose = Column(SQLEnum(Purpose), nullable=True)
    
    # Property Preferences
    bedrooms_min = Column(Integer, nullable=True)
    bedrooms_max = Column(Integer, nullable=True)
    preferred_location = Column(String(255), nullable=True)  # Primary location
    preferred_locations = Column(JSON, default=list)  # Multiple locations
    taste_tags = Column(JSON, default=list)  # e.g., ["Sea View", "High Floor", "Golf View"]
    notes = Column(Text, nullable=True)
    
    # Voice Data
    voice_transcript = Column(Text, nullable=True)
    voice_file_url = Column(String(512), nullable=True)
    voice_entities = Column(JSON, default=dict)  # Extracted entities from voice: {budget, location, etc.}
    
    # Image Data
    image_description = Column(Text, nullable=True)  # Gemini Vision description of uploaded image
    image_search_results = Column(Integer, default=0)  # Number of matching properties found
    image_file_url = Column(String(512), nullable=True)  # Optional: store image URL
    
    # Sales Psychology - Pain Points (Pain & Solution technique)
    pain_point = Column(String(50), nullable=True)  # Primary pain point
    pain_points = Column(JSON, default=list)  # Multiple pain points
    urgency_score = Column(Integer, default=0)  # 0-10 scale for FOMO tracking
    fomo_messages_sent = Column(Integer, default=0)  # Track FOMO messages sent
    
    # Conversation State (for state machine)
    conversation_state = Column(String(50), default="start")  # Store as string to avoid enum uppercase issue
    conversation_data = Column(JSON, default=dict)  # Temporary data during qualification
    filled_slots = Column(JSON, default=dict)  # Tracks which slots are filled: {goal: True, budget: True, ...}
    pending_slot = Column(String(50), nullable=True)  # Current slot being filled (for context retention)
    
    # Tracking
    source = Column(String(100), default="telegram")  # "telegram" or "whatsapp"
    last_interaction = Column(DateTime, default=datetime.utcnow)
    ghost_reminder_sent = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="leads")
    appointments = relationship("Appointment", back_populates="lead", cascade="all, delete-orphan")
    
    @property
    def state(self) -> ConversationState:
        """Get conversation_state as ConversationState enum."""
        if isinstance(self.conversation_state, ConversationState):
            return self.conversation_state
        # Convert string to enum
        try:
            return ConversationState(self.conversation_state)
        except (ValueError, KeyError):
            return ConversationState.START
    
    @property
    def lang(self) -> Language:
        """Get language as Language enum."""
        if isinstance(self.language, Language):
            return self.language
        # Convert string to enum
        try:
            return Language(self.language)
        except (ValueError, KeyError):
            return Language.EN


class AgentAvailability(Base):
    """
    Agent's available time slots for scheduling appointments.
    """
    __tablename__ = "agent_availability"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Day and Time
    day_of_week = Column(SQLEnum(DayOfWeek), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    # Status
    is_booked = Column(Boolean, default=False)
    booked_by_lead_id = Column(Integer, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="availabilities")


class TenantProperty(Base):
    """
    Properties listed by tenant (agent's inventory).
    AI uses this data to provide personalized recommendations.
    """
    __tablename__ = "tenant_properties"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Property Details
    name = Column(String(255), nullable=False)  # e.g., "Marina Heights Tower"
    property_type = Column(SQLEnum(PropertyType), nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=True)  # Buy/Rent/Both
    
    # Location
    location = Column(String(255), nullable=False)  # e.g., "Dubai Marina"
    address = Column(Text, nullable=True)
    
    # Pricing
    price = Column(Float, nullable=True)
    price_per_sqft = Column(Float, nullable=True)
    currency = Column(String(10), default="AED")
    
    # Details
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    area_sqft = Column(Float, nullable=True)
    
    # Features (for AI matching)
    features = Column(JSON, default=list)  # ["Sea View", "High Floor", "Gym", "Pool"]
    description = Column(Text, nullable=True)
    
    # ROI Data
    expected_roi = Column(Float, nullable=True)  # Annual ROI %
    rental_yield = Column(Float, nullable=True)  # Annual rental yield %
    
    # Golden Visa Eligible
    golden_visa_eligible = Column(Boolean, default=False)
    
    # Media
    images = Column(JSON, default=list)  # List of image URLs/paths
    image_urls = Column(JSON, default=list)  # Full URLs for display
    image_files = Column(JSON, default=list)  # File metadata: [{filename, size, uploaded_at, url}]
    primary_image = Column(String(512), nullable=True)  # Main display image
    brochure_pdf = Column(String(512), nullable=True)  # Property brochure/flyer PDF URL
    
    # Full Description (formatted text from agent)
    full_description = Column(Text, nullable=True)  # Rich text description with emojis
    
    # Status
    is_available = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_urgent = Column(Boolean, default=False)  # For "Urgent Sale" properties
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", backref="properties")


class TenantProject(Base):
    """
    Off-plan projects that the tenant is selling.
    Contains project-specific payment plans and ROI data for AI to use.
    """
    __tablename__ = "tenant_projects"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Project Details
    name = Column(String(255), nullable=False)  # e.g., "The Royal Atlantis"
    developer = Column(String(255), nullable=True)  # e.g., "Emaar"
    location = Column(String(255), nullable=False)
    
    # Pricing
    starting_price = Column(Float, nullable=True)
    price_per_sqft = Column(Float, nullable=True)
    currency = Column(String(10), default="AED")
    
    # Payment Plan (for AI to mention)
    payment_plan = Column(String(255), nullable=True)  # e.g., "60/40", "1% monthly"
    down_payment_percent = Column(Float, nullable=True)
    
    # Handover
    handover_date = Column(DateTime, nullable=True)
    completion_percent = Column(Float, nullable=True)
    
    # ROI Projection (Agent's data for AI)
    projected_roi = Column(Float, nullable=True)  # Expected annual appreciation %
    projected_rental_yield = Column(Float, nullable=True)
    
    # Golden Visa
    golden_visa_eligible = Column(Boolean, default=False)
    
    # Features
    amenities = Column(JSON, default=list)  # ["Beach Access", "Private Pool", "Concierge"]
    unit_types = Column(JSON, default=list)  # ["1BR", "2BR", "3BR", "Penthouse"]
    
    # Description for AI context
    description = Column(Text, nullable=True)
    selling_points = Column(JSON, default=list)  # Key points for AI to highlight
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", backref="projects")


class TenantKnowledge(Base):
    """
    Custom knowledge base entries for the AI.
    Tenant can add FAQs, policies, and custom responses.
    """
    __tablename__ = "tenant_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Knowledge Entry
    category = Column(String(100), nullable=False)  # "faq", "policy", "service", "location_info"
    title = Column(String(255), nullable=False)  # Question or topic
    content = Column(Text, nullable=False)  # Answer or information
    
    # Language
    language = Column(SQLEnum(Language), default=Language.EN)
    
    # Keywords for matching
    keywords = Column(JSON, default=list)  # For AI context matching
    
    # Priority (higher = more important)
    priority = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", backref="knowledge_base")


class Appointment(Base):
    """
    Scheduled appointments between agents and leads.
    """
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Appointment Details
    appointment_type = Column(SQLEnum(AppointmentType), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    
    # Location/Link
    location = Column(String(512), nullable=True)  # Office address or property address
    meeting_link = Column(String(512), nullable=True)  # For online meetings
    
    # Property (for viewings)
    property_reference = Column(String(100), nullable=True)
    property_address = Column(String(512), nullable=True)
    
    # Status
    is_confirmed = Column(Boolean, default=False)
    is_cancelled = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lead = relationship("Lead", back_populates="appointments")


# ==================== DATABASE FUNCTIONS ====================

async def init_db():
    """Initialize database - create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get a new async session."""
    async with async_session() as session:
        yield session


async def get_tenant_by_bot_token(token: str) -> Optional[Tenant]:
    """Get tenant by Telegram bot token."""
    async with async_session() as session:
        result = await session.execute(
            select(Tenant).where(Tenant.telegram_bot_token == token)
        )
        return result.scalar_one_or_none()


async def get_tenant_by_whatsapp_phone_id(phone_number_id: str) -> Optional[Tenant]:
    """Get tenant by WhatsApp phone number ID."""
    async with async_session() as session:
        result = await session.execute(
            select(Tenant).where(Tenant.whatsapp_phone_number_id == phone_number_id)
        )
        return result.scalar_one_or_none()


async def get_or_create_lead(
    tenant_id: int, 
    telegram_chat_id: str = None,
    telegram_username: Optional[str] = None,
    whatsapp_phone: str = None,
    source: str = "telegram"
) -> Lead:
    """Get existing lead or create new one (supports Telegram and WhatsApp)."""
    async with async_session() as session:
        # Try to find existing lead
        if telegram_chat_id:
            result = await session.execute(
                select(Lead).where(
                    Lead.tenant_id == tenant_id,
                    Lead.telegram_chat_id == telegram_chat_id
                )
            )
        elif whatsapp_phone:
            result = await session.execute(
                select(Lead).where(
                    Lead.tenant_id == tenant_id,
                    Lead.whatsapp_phone == whatsapp_phone
                )
            )
        else:
            raise ValueError("Either telegram_chat_id or whatsapp_phone is required")
        
        lead = result.scalar_one_or_none()
        
        if not lead:
            # Create new lead
            lead = Lead(
                tenant_id=tenant_id,
                telegram_chat_id=telegram_chat_id,
                telegram_username=telegram_username,
                whatsapp_phone=whatsapp_phone,
                source=source,
                conversation_state="start"  # Use string instead of enum
            )
            session.add(lead)
            await session.commit()
            await session.refresh(lead)
        
        return lead


async def update_lead(lead_id: int, **kwargs) -> Lead:
    """Update lead fields. Enums are stored as-is (lowercase values matching enum definitions)."""
    async with async_session() as session:
        result = await session.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        lead = result.scalar_one_or_none()
        
        if lead:
            for key, value in kwargs.items():
                if hasattr(lead, key):
                    # Convert enum to its string value if needed
                    if isinstance(value, Enum):
                        value = value.value
                    setattr(lead, key, value)
            lead.updated_at = datetime.utcnow()
            lead.last_interaction = datetime.utcnow()
            await session.commit()
            await session.refresh(lead)
        
        return lead


async def get_available_slots(tenant_id: int, day_of_week: Optional[DayOfWeek] = None) -> List[AgentAvailability]:
    """
    Get availability slots for a tenant.
    Returns all recurring slot templates (AgentAvailability records).
    Note: Actual booking status is checked against Appointment table, not is_booked flag.
    """
    async with async_session() as session:
        query = select(AgentAvailability).where(
            AgentAvailability.tenant_id == tenant_id
        )
        if day_of_week:
            query = query.where(AgentAvailability.day_of_week == day_of_week)
        
        result = await session.execute(query)
        slots = result.scalars().all()
        
        # For each slot, check if next occurrence is booked in Appointment table
        now = datetime.now()
        current_weekday = now.weekday()
        
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for slot in slots:
            target_weekday = day_mapping.get(slot.day_of_week.value.lower(), 0)
            days_ahead = (target_weekday - current_weekday) % 7
            
            if days_ahead == 0:
                days_ahead = 7
            
            next_occurrence = now + timedelta(days=days_ahead)
            scheduled_datetime = datetime.combine(next_occurrence.date(), slot.start_time)
            
            # Check if this date/time has an appointment
            appointment_check = await session.execute(
                select(Appointment).where(
                    Appointment.lead_id.in_(
                        select(Lead.id).where(Lead.tenant_id == tenant_id)
                    ),
                    Appointment.scheduled_date == scheduled_datetime,
                    Appointment.is_cancelled == False
                )
            )
            
            # Dynamically set is_booked for this week's occurrence
            # Use first() instead of scalar_one_or_none() to handle multiple bookings
            slot.is_booked = appointment_check.first() is not None
        
        return slots


async def book_slot(slot_id: int, lead_id: int) -> bool:
    """
    Book an available slot for a specific week.
    Creates an Appointment record instead of marking the recurring slot as permanently booked.
    """
    async with async_session() as session:
        # Get the slot template
        result = await session.execute(
            select(AgentAvailability).where(AgentAvailability.id == slot_id)
        )
        slot = result.scalar_one_or_none()
        
        if not slot:
            return False
        
        # Calculate the next occurrence of this day/time
        now = datetime.now()
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        # Map day_of_week enum to weekday number
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekday = day_mapping.get(slot.day_of_week.value.lower(), 0)
        days_ahead = (target_weekday - current_weekday) % 7
        
        if days_ahead == 0:
            days_ahead = 7  # Book for next week if same day
        
        next_occurrence = now + timedelta(days=days_ahead)
        
        # Combine date with slot time
        scheduled_datetime = datetime.combine(
            next_occurrence.date(),
            slot.start_time
        )
        
        # Check if this specific date/time is already booked
        existing_appointment = await session.execute(
            select(Appointment).where(
                Appointment.lead_id.in_(
                    select(Lead.id).where(Lead.tenant_id == slot.tenant_id)
                ),
                Appointment.scheduled_date == scheduled_datetime,
                Appointment.is_cancelled == False
            )
        )
        
        if existing_appointment.scalar_one_or_none():
            return False  # This specific date/time is already booked
        
        # Create Appointment record
        appointment = Appointment(
            lead_id=lead_id,
            appointment_type=AppointmentType.ONLINE,  # Consultation appointments are online
            scheduled_date=scheduled_datetime,
            duration_minutes=60,
            is_confirmed=True,
            notes=f"Booked via automated slot booking (Slot ID: {slot_id})"
        )
        
        session.add(appointment)
        await session.commit()
        return True


async def create_appointment(
    lead_id: int,
    appointment_type: AppointmentType,
    scheduled_date: datetime,
    **kwargs
) -> Appointment:
    """Create a new appointment."""
    async with async_session() as session:
        appointment = Appointment(
            lead_id=lead_id,
            appointment_type=appointment_type,
            scheduled_date=scheduled_date,
            **kwargs
        )
        session.add(appointment)
        await session.commit()
        await session.refresh(appointment)
        return appointment


async def get_leads_needing_reminder(hours: int = 2) -> List[Lead]:
    """Get leads that haven't responded in the specified hours (Ghost Protocol)."""
    from datetime import timedelta
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    async with async_session() as session:
        result = await session.execute(
            select(Lead).where(
                Lead.last_interaction < cutoff_time,
                Lead.ghost_reminder_sent == False,
                Lead.status.in_([LeadStatus.NEW, LeadStatus.CONTACTED])
            )
        )
        return result.scalars().all()


async def get_appointments_needing_reminder(hours_before: int = 24) -> List[Appointment]:
    """Get appointments that need 24h reminder."""
    from datetime import timedelta
    
    reminder_window_start = datetime.utcnow()
    reminder_window_end = reminder_window_start + timedelta(hours=hours_before)
    
    async with async_session() as session:
        result = await session.execute(
            select(Appointment).where(
                Appointment.scheduled_date >= reminder_window_start,
                Appointment.scheduled_date <= reminder_window_end,
                Appointment.reminder_sent == False,
                Appointment.is_cancelled == False
            )
        )
        return result.scalars().all()


# ==================== TENANT DATA FUNCTIONS ====================

async def get_tenant_properties(
    tenant_id: int, 
    property_type: Optional[PropertyType] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    location: Optional[str] = None,
    bedrooms: Optional[int] = None,
    golden_visa_only: bool = False,
    limit: int = 10
) -> List["TenantProperty"]:
    """Get tenant's properties matching criteria for AI recommendations."""
    async with async_session() as session:
        query = select(TenantProperty).where(
            TenantProperty.tenant_id == tenant_id,
            TenantProperty.is_available == True
        )
        
        if property_type:
            # Handle both enum and string property_type values
            if isinstance(property_type, str):
                # Convert string to PropertyType enum (case-insensitive)
                property_type = PropertyType[property_type.upper()]
            query = query.where(TenantProperty.property_type == property_type)
        if min_price:
            query = query.where(TenantProperty.price >= min_price)
        if max_price:
            query = query.where(TenantProperty.price <= max_price)
        if location:
            query = query.where(TenantProperty.location.ilike(f"%{location}%"))
        if bedrooms:
            query = query.where(TenantProperty.bedrooms == bedrooms)
        if golden_visa_only:
            query = query.where(TenantProperty.golden_visa_eligible == True)
        
        # Prioritize featured properties
        query = query.order_by(TenantProperty.is_featured.desc(), TenantProperty.created_at.desc())
        query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()


async def get_tenant_projects(
    tenant_id: int,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    location: Optional[str] = None,
    golden_visa_only: bool = False,
    limit: int = 5
) -> List["TenantProject"]:
    """Get tenant's off-plan projects for AI recommendations."""
    async with async_session() as session:
        query = select(TenantProject).where(
            TenantProject.tenant_id == tenant_id,
            TenantProject.is_active == True
        )
        
        if min_price:
            query = query.where(TenantProject.starting_price >= min_price)
        if max_price:
            query = query.where(TenantProject.starting_price <= max_price)
        if location:
            query = query.where(TenantProject.location.ilike(f"%{location}%"))
        if golden_visa_only:
            query = query.where(TenantProject.golden_visa_eligible == True)
        
        query = query.order_by(TenantProject.is_featured.desc(), TenantProject.created_at.desc())
        query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()


async def get_tenant_knowledge(
    tenant_id: int,
    category: Optional[str] = None,
    language: Optional[Language] = None,
    keywords: Optional[List[str]] = None
) -> List["TenantKnowledge"]:
    """Get tenant's knowledge base entries for AI context."""
    async with async_session() as session:
        query = select(TenantKnowledge).where(
            TenantKnowledge.tenant_id == tenant_id,
            TenantKnowledge.is_active == True
        )
        
        if category:
            query = query.where(TenantKnowledge.category == category)
        if language:
            query = query.where(TenantKnowledge.language == language)
        
        query = query.order_by(TenantKnowledge.priority.desc())
        
        result = await session.execute(query)
        return result.scalars().all()


async def get_tenant_context_for_ai(tenant_id: int, lead: Optional["Lead"] = None) -> Dict[str, Any]:
    """
    Build a complete context object with all tenant data for AI.
    This is the main function that Brain uses to get tenant-specific info.
    """
    async with async_session() as session:
        # Get tenant info
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            return {}
        
        # Build filters based on lead preferences
        property_filters = {}
        if lead:
            if lead.budget_min:
                property_filters["min_price"] = lead.budget_min
            if lead.budget_max:
                property_filters["max_price"] = lead.budget_max
            if lead.property_type:
                property_filters["property_type"] = lead.property_type
            if lead.preferred_location:
                property_filters["location"] = lead.preferred_location
            if lead.bedrooms_min:
                property_filters["bedrooms"] = lead.bedrooms_min
            if lead.purpose and lead.purpose == Purpose.RESIDENCY:
                property_filters["golden_visa_only"] = True
        
        # Fetch matching properties
        properties = await get_tenant_properties(tenant_id, **property_filters)
        
        # Fetch matching projects
        project_filters = {k: v for k, v in property_filters.items() 
                         if k in ["min_price", "max_price", "location", "golden_visa_only"]}
        projects = await get_tenant_projects(tenant_id, **project_filters)
        
        # Fetch knowledge base
        knowledge = await get_tenant_knowledge(
            tenant_id, 
            language=lead.language if lead else None
        )
        
        # Build context dictionary
        context = {
            "tenant": {
                "name": tenant.name,
                "company": tenant.company_name,
                "phone": tenant.phone,
                "email": tenant.email,
            },
            "properties": [
                {
                    "name": p.name,
                    "type": p.property_type.value if p.property_type else None,
                    "location": p.location,
                    "price": p.price,
                    "bedrooms": p.bedrooms,
                    "features": p.features,
                    "roi": p.expected_roi,
                    "rental_yield": p.rental_yield,
                    "golden_visa": p.golden_visa_eligible,
                    "description": p.description,
                }
                for p in properties
            ],
            "projects": [
                {
                    "name": proj.name,
                    "developer": proj.developer,
                    "location": proj.location,
                    "starting_price": proj.starting_price,
                    "payment_plan": proj.payment_plan,
                    "handover": proj.handover_date.strftime("%Y-%m") if proj.handover_date else None,
                    "roi": proj.projected_roi,
                    "rental_yield": proj.projected_rental_yield,
                    "golden_visa": proj.golden_visa_eligible,
                    "amenities": proj.amenities,
                    "selling_points": proj.selling_points,
                }
                for proj in projects
            ],
            "knowledge": [
                {
                    "category": k.category,
                    "title": k.title,
                    "content": k.content,
                    "keywords": k.keywords,
                    "language": k.language,
                    "priority": k.priority,
                }
                for k in knowledge
            ]
        }
        
        return context


# ==================== DEPENDENCY ====================

async def get_db() -> AsyncSession:
    """Get database session for FastAPI dependency injection."""
    async with async_session() as session:
        yield session
