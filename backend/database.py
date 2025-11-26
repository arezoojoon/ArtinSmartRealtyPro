"""
ArtinSmartRealty V2 - Database Schema
Multi-Tenant Real Estate SaaS with Strict Data Isolation
"""

import os
from datetime import datetime, time
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Time, Boolean, 
    ForeignKey, Enum as SQLEnum, JSON, Float, create_engine
)
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
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"


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


class ConversationState(str, Enum):
    """State machine for Turbo Qualification Flow"""
    START = "start"
    WELCOME = "welcome"
    HOOK = "hook"  # ROI Offer
    PHONE_GATE = "phone_gate"  # Hard Gate
    TRANSACTION_TYPE = "transaction_type"  # Buy/Rent
    PROPERTY_TYPE = "property_type"  # Residential/Commercial
    BUDGET = "budget"
    PAYMENT_METHOD = "payment_method"  # Cash/Credit
    PURPOSE = "purpose"  # Residency/Investment/Living
    SCHEDULE = "schedule"
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
    email = Column(String(255), nullable=True)
    
    # WhatsApp Business API Settings
    whatsapp_phone_number_id = Column(String(100), nullable=True, unique=True)
    whatsapp_access_token = Column(String(512), nullable=True)
    whatsapp_business_account_id = Column(String(100), nullable=True)
    whatsapp_verify_token = Column(String(255), nullable=True)  # For webhook verification
    
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
    telegram_chat_id = Column(String(100), nullable=True, index=True)
    telegram_username = Column(String(100), nullable=True)
    whatsapp_phone = Column(String(50), nullable=True, index=True)  # WhatsApp phone number
    language = Column(SQLEnum(Language), default=Language.EN)
    
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
    
    # Tags and Preferences
    taste_tags = Column(JSON, default=list)  # e.g., ["Sea View", "High Floor", "Golf View"]
    preferred_locations = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    
    # Voice Data
    voice_transcript = Column(Text, nullable=True)
    voice_file_url = Column(String(512), nullable=True)
    
    # Conversation State (for state machine)
    conversation_state = Column(SQLEnum(ConversationState), default=ConversationState.START)
    conversation_data = Column(JSON, default=dict)  # Temporary data during qualification
    
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
                conversation_state=ConversationState.START
            )
            session.add(lead)
            await session.commit()
            await session.refresh(lead)
        
        return lead


async def update_lead(lead_id: int, **kwargs) -> Lead:
    """Update lead fields."""
    async with async_session() as session:
        result = await session.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        lead = result.scalar_one_or_none()
        
        if lead:
            for key, value in kwargs.items():
                if hasattr(lead, key):
                    setattr(lead, key, value)
            lead.updated_at = datetime.utcnow()
            lead.last_interaction = datetime.utcnow()
            await session.commit()
            await session.refresh(lead)
        
        return lead


async def get_available_slots(tenant_id: int, day_of_week: Optional[DayOfWeek] = None) -> List[AgentAvailability]:
    """Get available (not booked) slots for a tenant."""
    async with async_session() as session:
        query = select(AgentAvailability).where(
            AgentAvailability.tenant_id == tenant_id,
            AgentAvailability.is_booked == False
        )
        if day_of_week:
            query = query.where(AgentAvailability.day_of_week == day_of_week)
        
        result = await session.execute(query)
        return result.scalars().all()


async def book_slot(slot_id: int, lead_id: int) -> bool:
    """Book an available slot."""
    async with async_session() as session:
        result = await session.execute(
            select(AgentAvailability).where(
                AgentAvailability.id == slot_id,
                AgentAvailability.is_booked == False
            )
        )
        slot = result.scalar_one_or_none()
        
        if slot:
            slot.is_booked = True
            slot.booked_by_lead_id = lead_id
            await session.commit()
            return True
        return False


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
