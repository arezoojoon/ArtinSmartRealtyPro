"""
ArtinSmartRealty V2 - Main API
FastAPI Application with Scheduling, Excel Export, and Background Tasks
"""

import os
import io
import asyncio
from datetime import datetime, time, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, delete
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from database import (
    init_db, async_session,
    Tenant, Lead, AgentAvailability, Appointment,
    LeadStatus, TransactionType, PropertyType, PaymentMethod, Purpose,
    AppointmentType, DayOfWeek, Language, ConversationState,
    get_leads_needing_reminder, get_appointments_needing_reminder,
    get_available_slots, book_slot, create_appointment, update_lead
)
from telegram_bot import bot_manager, handle_telegram_webhook
from whatsapp_bot import whatsapp_bot_manager, verify_webhook as verify_whatsapp_webhook
from roi_engine import generate_roi_pdf


# ==================== PYDANTIC MODELS ====================

class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    telegram_bot_token: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=512)
    primary_color: Optional[str] = Field("#D4AF37", max_length=20)
    # WhatsApp Business API fields
    whatsapp_phone_number_id: Optional[str] = Field(None, max_length=100)
    whatsapp_access_token: Optional[str] = Field(None, max_length=512)
    whatsapp_business_account_id: Optional[str] = Field(None, max_length=100)
    whatsapp_verify_token: Optional[str] = Field(None, max_length=255)


class TenantResponse(BaseModel):
    id: int
    name: str
    company_name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    telegram_bot_token: Optional[str]
    logo_url: Optional[str]
    primary_color: Optional[str]
    subscription_status: Optional[str]
    trial_ends_at: Optional[datetime]
    whatsapp_phone_number_id: Optional[str]
    whatsapp_business_account_id: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LeadResponse(BaseModel):
    id: int
    tenant_id: int
    name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    telegram_username: Optional[str]
    language: Optional[Language]
    status: Optional[LeadStatus]
    transaction_type: Optional[TransactionType]
    property_type: Optional[PropertyType]
    budget_min: Optional[float]
    budget_max: Optional[float]
    budget_currency: str
    payment_method: Optional[PaymentMethod]
    purpose: Optional[Purpose]
    bedrooms_min: Optional[int]
    bedrooms_max: Optional[int]
    preferred_location: Optional[str]
    taste_tags: List[str]
    voice_transcript: Optional[str]
    voice_entities: Optional[dict]
    conversation_state: Optional[ConversationState]
    source: str
    last_interaction: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class LeadUpdate(BaseModel):
    """Validated lead update model - only allow specific fields to be updated."""
    name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    status: Optional[LeadStatus] = None
    transaction_type: Optional[TransactionType] = None
    property_type: Optional[PropertyType] = None
    budget_min: Optional[float] = Field(None, ge=0)
    budget_max: Optional[float] = Field(None, ge=0)
    payment_method: Optional[PaymentMethod] = None
    purpose: Optional[Purpose] = None
    taste_tags: Optional[List[str]] = None
    notes: Optional[str] = None


class ScheduleSlotCreate(BaseModel):
    day_of_week: DayOfWeek
    start_time: str = Field(..., description="Time in HH:MM format")
    end_time: str = Field(..., description="Time in HH:MM format")


class ScheduleSlotResponse(BaseModel):
    id: int
    day_of_week: DayOfWeek
    start_time: str
    end_time: str
    is_booked: bool

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    lead_id: int
    appointment_type: AppointmentType
    scheduled_date: datetime
    duration_minutes: int = 60
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    property_reference: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    lead_id: int
    appointment_type: AppointmentType
    scheduled_date: datetime
    duration_minutes: int
    location: Optional[str]
    meeting_link: Optional[str]
    is_confirmed: bool
    is_cancelled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_leads: int
    active_deals: int
    qualified_leads: int
    scheduled_viewings: int
    conversion_rate: float
    leads_by_status: dict
    leads_by_purpose: dict


# ==================== SCHEDULER ====================

scheduler = AsyncIOScheduler()


async def ghost_protocol_job():
    """Background job for Ghost Protocol - send reminders to inactive leads."""
    try:
        await bot_manager.send_ghost_reminders()
    except Exception as e:
        print(f"Ghost protocol job error: {e}")


async def appointment_reminder_job():
    """Background job for appointment reminders."""
    try:
        await bot_manager.send_appointment_reminders()
    except Exception as e:
        print(f"Appointment reminder job error: {e}")


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    print("🚀 Starting ArtinSmartRealty V2...")
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    # Start Telegram bots for all active tenants
    async with async_session() as session:
        result = await session.execute(
            select(Tenant).where(
                Tenant.is_active == True,
                Tenant.telegram_bot_token.isnot(None)
            )
        )
        tenants = result.scalars().all()
        
        for tenant in tenants:
            try:
                await bot_manager.start_bot_for_tenant(tenant)
            except Exception as e:
                print(f"Failed to start bot for tenant {tenant.id}: {e}")
    
    # Start scheduler
    scheduler.add_job(
        ghost_protocol_job,
        trigger=IntervalTrigger(hours=1),
        id="ghost_protocol",
        replace_existing=True
    )
    scheduler.add_job(
        appointment_reminder_job,
        trigger=IntervalTrigger(hours=1),
        id="appointment_reminders",
        replace_existing=True
    )
    scheduler.start()
    print("✅ Background scheduler started")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    scheduler.shutdown()
    await bot_manager.stop_all_bots()
    print("✅ Shutdown complete")


# ==================== FASTAPI APP ====================

app = FastAPI(
    title="ArtinSmartRealty V2 API",
    description="Multi-Tenant Real Estate SaaS Platform",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware - Use environment variable for allowed origins in production
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== DEPENDENCY ====================

async def get_db() -> AsyncSession:
    """Get database session."""
    async with async_session() as session:
        yield session


# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ==================== TENANT ENDPOINTS ====================

@app.post("/api/tenants", response_model=TenantResponse)
async def create_tenant(tenant_data: TenantCreate, db: AsyncSession = Depends(get_db)):
    """Create a new tenant (agent)."""
    tenant = Tenant(**tenant_data.model_dump())
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    
    # Start bot if token provided
    if tenant.telegram_bot_token:
        try:
            await bot_manager.start_bot_for_tenant(tenant)
        except Exception as e:
            print(f"Failed to start bot: {e}")
    
    return tenant


@app.get("/api/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: int, db: AsyncSession = Depends(get_db)):
    """Get tenant by ID."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return tenant


@app.get("/api/tenants", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all tenants."""
    result = await db.execute(
        select(Tenant).offset(skip).limit(limit)
    )
    return result.scalars().all()


# ==================== LEAD ENDPOINTS ====================

@app.get("/api/tenants/{tenant_id}/leads", response_model=List[LeadResponse])
async def list_leads(
    tenant_id: int,
    status: Optional[LeadStatus] = None,
    purpose: Optional[Purpose] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List leads for a tenant with optional filtering."""
    query = select(Lead).where(Lead.tenant_id == tenant_id)
    
    if status:
        query = query.where(Lead.status == status)
    if purpose:
        query = query.where(Lead.purpose == purpose)
    
    query = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/api/tenants/{tenant_id}/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(tenant_id: int, lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific lead."""
    result = await db.execute(
        select(Lead).where(
            Lead.tenant_id == tenant_id,
            Lead.id == lead_id
        )
    )
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return lead


@app.patch("/api/tenants/{tenant_id}/leads/{lead_id}")
async def update_lead_endpoint(
    tenant_id: int,
    lead_id: int,
    updates: LeadUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a lead with validated fields only."""
    result = await db.execute(
        select(Lead).where(
            Lead.tenant_id == tenant_id,
            Lead.id == lead_id
        )
    )
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Apply only non-None updates from validated model
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None and hasattr(lead, key):
            setattr(lead, key, value)
    
    lead.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(lead)
    
    return {"status": "updated", "lead_id": lead.id}


# ==================== SCHEDULING ENDPOINTS ====================

@app.post("/api/tenants/{tenant_id}/schedule", response_model=ScheduleSlotResponse)
async def create_schedule_slot(
    tenant_id: int,
    slot_data: ScheduleSlotCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new availability slot for an agent."""
    # Parse times
    try:
        start = datetime.strptime(slot_data.start_time, "%H:%M").time()
        end = datetime.strptime(slot_data.end_time, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")
    
    if start >= end:
        raise HTTPException(status_code=400, detail="Start time must be before end time")
    
    # Check for overlapping slots
    result = await db.execute(
        select(AgentAvailability).where(
            AgentAvailability.tenant_id == tenant_id,
            AgentAvailability.day_of_week == slot_data.day_of_week
        )
    )
    existing_slots = result.scalars().all()
    
    for existing in existing_slots:
        # Check for overlap
        if not (end <= existing.start_time or start >= existing.end_time):
            raise HTTPException(
                status_code=409,
                detail=f"Slot overlaps with existing slot: {existing.start_time} - {existing.end_time}"
            )
    
    # Create slot
    slot = AgentAvailability(
        tenant_id=tenant_id,
        day_of_week=slot_data.day_of_week,
        start_time=start,
        end_time=end
    )
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    
    return ScheduleSlotResponse(
        id=slot.id,
        day_of_week=slot.day_of_week,
        start_time=slot.start_time.strftime("%H:%M"),
        end_time=slot.end_time.strftime("%H:%M"),
        is_booked=slot.is_booked
    )


@app.get("/api/tenants/{tenant_id}/schedule", response_model=List[ScheduleSlotResponse])
async def list_schedule_slots(
    tenant_id: int,
    day_of_week: Optional[DayOfWeek] = None,
    available_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List schedule slots for a tenant."""
    query = select(AgentAvailability).where(AgentAvailability.tenant_id == tenant_id)
    
    if day_of_week:
        query = query.where(AgentAvailability.day_of_week == day_of_week)
    if available_only:
        query = query.where(AgentAvailability.is_booked == False)
    
    result = await db.execute(query)
    slots = result.scalars().all()
    
    return [
        ScheduleSlotResponse(
            id=s.id,
            day_of_week=s.day_of_week,
            start_time=s.start_time.strftime("%H:%M"),
            end_time=s.end_time.strftime("%H:%M"),
            is_booked=s.is_booked
        )
        for s in slots
    ]


@app.delete("/api/tenants/{tenant_id}/schedule/{slot_id}")
async def delete_schedule_slot(
    tenant_id: int,
    slot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a schedule slot."""
    result = await db.execute(
        select(AgentAvailability).where(
            AgentAvailability.tenant_id == tenant_id,
            AgentAvailability.id == slot_id
        )
    )
    slot = result.scalar_one_or_none()
    
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    if slot.is_booked:
        raise HTTPException(status_code=400, detail="Cannot delete a booked slot")
    
    await db.execute(
        delete(AgentAvailability).where(AgentAvailability.id == slot_id)
    )
    await db.commit()
    
    return {"status": "deleted", "slot_id": slot_id}


# ==================== APPOINTMENT ENDPOINTS ====================

@app.post("/api/tenants/{tenant_id}/appointments", response_model=AppointmentResponse)
async def create_appointment_endpoint(
    tenant_id: int,
    appointment_data: AppointmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create an appointment."""
    # Verify lead belongs to tenant
    result = await db.execute(
        select(Lead).where(
            Lead.tenant_id == tenant_id,
            Lead.id == appointment_data.lead_id
        )
    )
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Create appointment
    appointment = Appointment(
        lead_id=appointment_data.lead_id,
        appointment_type=appointment_data.appointment_type,
        scheduled_date=appointment_data.scheduled_date,
        duration_minutes=appointment_data.duration_minutes,
        location=appointment_data.location,
        meeting_link=appointment_data.meeting_link,
        property_reference=appointment_data.property_reference,
        notes=appointment_data.notes
    )
    db.add(appointment)
    
    # Update lead status
    lead.status = LeadStatus.VIEWING_SCHEDULED
    
    await db.commit()
    await db.refresh(appointment)
    
    return appointment


@app.get("/api/tenants/{tenant_id}/appointments", response_model=List[AppointmentResponse])
async def list_appointments(
    tenant_id: int,
    upcoming_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List appointments for a tenant."""
    # Get lead IDs for tenant
    lead_result = await db.execute(
        select(Lead.id).where(Lead.tenant_id == tenant_id)
    )
    lead_ids = [lid for (lid,) in lead_result.fetchall()]
    
    if not lead_ids:
        return []
    
    query = select(Appointment).where(Appointment.lead_id.in_(lead_ids))
    
    if upcoming_only:
        query = query.where(
            Appointment.scheduled_date >= datetime.utcnow(),
            Appointment.is_cancelled == False
        )
    
    query = query.order_by(Appointment.scheduled_date)
    
    result = await db.execute(query)
    return result.scalars().all()


# ==================== EXCEL EXPORT ====================

@app.get("/api/tenants/{tenant_id}/leads/export")
async def export_leads_excel(
    tenant_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Export all leads to Excel (.xlsx) file."""
    # Get all leads for tenant
    result = await db.execute(
        select(Lead).where(Lead.tenant_id == tenant_id).order_by(Lead.created_at.desc())
    )
    leads = result.scalars().all()
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Leads"
    
    # Define headers
    headers = [
        "ID", "Name", "Phone", "Telegram Username", "Language", "Status",
        "Transaction Type", "Property Type", "Budget Min", "Budget Max",
        "Payment Method", "Purpose", "Residency Need", "Taste Tags",
        "Voice Transcript", "Source", "Created At", "Last Interaction"
    ]
    
    # Style definitions
    header_fill = PatternFill(start_color="0f1729", end_color="0f1729", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    gold_border = Border(
        left=Side(style='thin', color='D4AF37'),
        right=Side(style='thin', color='D4AF37'),
        top=Side(style='thin', color='D4AF37'),
        bottom=Side(style='thin', color='D4AF37')
    )
    
    # Write headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = gold_border
    
    # Write data
    for row, lead in enumerate(leads, 2):
        data = [
            lead.id,
            lead.name or "",
            lead.phone or "",
            lead.telegram_username or "",
            lead.language.value if lead.language else "",
            lead.status.value if lead.status else "",
            lead.transaction_type.value if lead.transaction_type else "",
            lead.property_type.value if lead.property_type else "",
            lead.budget_min or "",
            lead.budget_max or "",
            lead.payment_method.value if lead.payment_method else "",
            lead.purpose.value if lead.purpose else "",
            "Yes" if lead.purpose == Purpose.RESIDENCY else "No",
            ", ".join(lead.taste_tags) if lead.taste_tags else "",
            lead.voice_transcript or "",
            lead.source or "",
            lead.created_at.strftime("%Y-%m-%d %H:%M") if lead.created_at else "",
            lead.last_interaction.strftime("%Y-%m-%d %H:%M") if lead.last_interaction else ""
        ]
        
        for col, value in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.border = gold_border
            cell.alignment = Alignment(wrap_text=True)
    
    # Adjust column widths
    column_widths = [8, 20, 15, 20, 10, 15, 15, 15, 12, 12, 15, 15, 15, 30, 40, 12, 18, 18]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = width
    
    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Return as download
    filename = f"leads_export_{tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==================== DASHBOARD STATS ====================

@app.get("/api/tenants/{tenant_id}/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(tenant_id: int, db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics for a tenant."""
    # Get all leads
    result = await db.execute(
        select(Lead).where(Lead.tenant_id == tenant_id)
    )
    leads = result.scalars().all()
    
    # Calculate stats
    total_leads = len(leads)
    active_deals = sum(1 for l in leads if l.status in [LeadStatus.NEGOTIATING, LeadStatus.VIEWING_SCHEDULED])
    qualified_leads = sum(1 for l in leads if l.status == LeadStatus.QUALIFIED)
    scheduled_viewings = sum(1 for l in leads if l.status == LeadStatus.VIEWING_SCHEDULED)
    closed_won = sum(1 for l in leads if l.status == LeadStatus.CLOSED_WON)
    
    conversion_rate = (closed_won / total_leads * 100) if total_leads > 0 else 0
    
    # Status breakdown
    leads_by_status = {}
    for status in LeadStatus:
        count = sum(1 for l in leads if l.status == status)
        if count > 0:
            leads_by_status[status.value] = count
    
    # Purpose breakdown
    leads_by_purpose = {}
    for purpose in Purpose:
        count = sum(1 for l in leads if l.purpose == purpose)
        if count > 0:
            leads_by_purpose[purpose.value] = count
    
    return DashboardStats(
        total_leads=total_leads,
        active_deals=active_deals,
        qualified_leads=qualified_leads,
        scheduled_viewings=scheduled_viewings,
        conversion_rate=round(conversion_rate, 1),
        leads_by_status=leads_by_status,
        leads_by_purpose=leads_by_purpose
    )


# ==================== ROI PDF ENDPOINT ====================

@app.get("/api/tenants/{tenant_id}/leads/{lead_id}/roi-pdf")
async def generate_roi_pdf_endpoint(
    tenant_id: int,
    lead_id: int,
    property_value: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    """Generate ROI PDF report for a lead."""
    # Get tenant
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Get lead
    result = await db.execute(
        select(Lead).where(Lead.tenant_id == tenant_id, Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Generate PDF
    pdf_bytes = await generate_roi_pdf(tenant, lead, property_value)
    
    # Return as download
    filename = f"roi_analysis_{lead.name or lead_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==================== TELEGRAM WEBHOOK ====================

@app.post("/webhook/telegram/{bot_token}")
async def telegram_webhook(bot_token: str, update: dict, background_tasks: BackgroundTasks):
    """Handle incoming Telegram webhook updates."""
    background_tasks.add_task(handle_telegram_webhook, bot_token, update)
    return {"status": "ok"}


# ==================== WHATSAPP WEBHOOK ====================

@app.get("/webhook/whatsapp")
async def whatsapp_webhook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    db: AsyncSession = Depends(get_db)
):
    """
    WhatsApp webhook verification endpoint.
    Called by Meta when registering the webhook.
    Verifies against any tenant's verify_token in the database.
    """
    if hub_mode != "subscribe":
        raise HTTPException(status_code=403, detail="Invalid mode")
    
    # Check if any tenant has this verify token
    result = await db.execute(
        select(Tenant).where(Tenant.whatsapp_verify_token == hub_token)
    )
    tenant = result.scalar_one_or_none()
    
    if tenant:
        return Response(content=hub_challenge, media_type="text/plain")
    
    # Fallback to environment variable for initial setup
    env_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    if env_token and hub_token == env_token:
        return Response(content=hub_challenge, media_type="text/plain")
    
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: dict, background_tasks: BackgroundTasks):
    """
    Handle incoming WhatsApp webhook updates.
    Routes to appropriate tenant handler based on phone_number_id.
    """
    async def process_webhook():
        await whatsapp_bot_manager.handle_webhook(payload)
    
    background_tasks.add_task(process_webhook)
    return {"status": "ok"}


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
