"""
Artin Smart Realty - Scheduling API Routes
Calendar, availability, and appointments management
REAL DATABASE IMPLEMENTATION
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date, time, timedelta
import logging

from database import (
    async_session, AgentAvailability, Appointment, Lead, DayOfWeek, AppointmentType
)

router = APIRouter(prefix="/api/v1/scheduling", tags=["Scheduling"])

logger = logging.getLogger(__name__)


# ==================== PYDANTIC MODELS ====================

class AvailabilitySlot(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", example="09:00")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", example="17:00")

class SetAvailabilityRequest(BaseModel):
    slots: List[AvailabilitySlot]

class AvailabilityResponse(BaseModel):
    slots: List[dict]
    
class AppointmentCreate(BaseModel):
    lead_id: int
    property_id: Optional[int] = None
    scheduled_at: datetime
    type: str = Field(default="viewing", description="viewing, consultation, call")
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: int
    lead_id: int
    lead_name: Optional[str] = None
    property_id: Optional[int] = None
    scheduled_at: datetime
    type: str
    status: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Helper to convert int to DayOfWeek
DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def int_to_day_of_week(day_int: int) -> DayOfWeek:
    """Convert 0-6 integer to DayOfWeek enum"""
    return DayOfWeek(DAY_NAMES[day_int])


def day_of_week_to_int(day: DayOfWeek) -> int:
    """Convert DayOfWeek enum to 0-6 integer"""
    return DAY_NAMES.index(day.value)


# ==================== AVAILABILITY ENDPOINTS ====================

@router.get("/availability")
async def get_availability(
    tenant_id: int = Query(...),
):
    """Get agent availability slots for the tenant from database"""
    async with async_session() as session:
        result = await session.execute(
            select(AgentAvailability).where(
                AgentAvailability.tenant_id == tenant_id
            ).order_by(AgentAvailability.day_of_week)
        )
        slots = result.scalars().all()
        
        return {
            "slots": [
                {
                    "id": slot.id,
                    "day_of_week": day_of_week_to_int(slot.day_of_week),
                    "day_name": slot.day_of_week.value.capitalize(),
                    "start_time": slot.start_time.strftime("%H:%M") if slot.start_time else "09:00",
                    "end_time": slot.end_time.strftime("%H:%M") if slot.end_time else "17:00",
                    "is_booked": slot.is_booked
                }
                for slot in slots
            ]
        }


@router.post("/availability")
async def set_availability(
    request: SetAvailabilityRequest,
    tenant_id: int = Query(...),
):
    """Set agent availability slots - replaces existing slots"""
    async with async_session() as session:
        try:
            # Delete existing availability for this tenant
            await session.execute(
                delete(AgentAvailability).where(
                    AgentAvailability.tenant_id == tenant_id
                )
            )
            
            # Insert new slots
            for slot_data in request.slots:
                # Parse times
                start_parts = slot_data.start_time.split(":")
                end_parts = slot_data.end_time.split(":")
                
                slot = AgentAvailability(
                    tenant_id=tenant_id,
                    day_of_week=int_to_day_of_week(slot_data.day_of_week),
                    start_time=time(int(start_parts[0]), int(start_parts[1])),
                    end_time=time(int(end_parts[0]), int(end_parts[1])),
                    is_booked=False
                )
                session.add(slot)
            
            await session.commit()
            
            return {"message": "Availability updated successfully", "slots": len(request.slots)}
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error setting availability: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to set availability: {str(e)}")


# ==================== APPOINTMENTS ENDPOINTS ====================

@router.get("/appointments")
async def get_appointments(
    tenant_id: int = Query(...),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[dict]:
    """Get appointments within date range from database"""
    async with async_session() as session:
        # Build query joining Lead to get lead name
        query = (
            select(Appointment, Lead.name.label("lead_name"))
            .join(Lead, Appointment.lead_id == Lead.id)
            .where(Lead.tenant_id == tenant_id)
        )
        
        # Apply date filters if provided
        if start_date:
            start_datetime = datetime.combine(start_date, time.min)
            query = query.where(Appointment.scheduled_date >= start_datetime)
        
        if end_date:
            end_datetime = datetime.combine(end_date, time.max)
            query = query.where(Appointment.scheduled_date <= end_datetime)
        
        query = query.order_by(Appointment.scheduled_date)
        
        result = await session.execute(query)
        rows = result.all()
        
        appointments = []
        for row in rows:
            apt = row[0]  # Appointment object
            lead_name = row[1]  # Lead name
            
            # Determine status string
            if apt.is_cancelled:
                status = "cancelled"
            elif apt.is_confirmed:
                status = "confirmed"
            else:
                status = "pending"
            
            appointments.append({
                "id": apt.id,
                "lead_id": apt.lead_id,
                "lead_name": lead_name or f"Lead #{apt.lead_id}",
                "property_id": None,  # Not stored in current model
                "scheduled_at": apt.scheduled_date.isoformat(),
                "type": apt.appointment_type.value if apt.appointment_type else "viewing",
                "status": status,
                "notes": apt.notes,
                "location": apt.location,
                "meeting_link": apt.meeting_link,
                "created_at": apt.created_at.isoformat() if apt.created_at else None
            })
        
        return appointments


@router.post("/appointments")
async def create_appointment(
    appointment: AppointmentCreate,
    tenant_id: int = Query(...),
):
    """Create a new appointment in the database"""
    async with async_session() as session:
        try:
            # Verify lead belongs to this tenant
            lead_result = await session.execute(
                select(Lead).where(
                    and_(Lead.id == appointment.lead_id, Lead.tenant_id == tenant_id)
                )
            )
            lead = lead_result.scalar_one_or_none()
            
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found or access denied")
            
            # Map type string to AppointmentType enum
            type_map = {
                "viewing": AppointmentType.VIEWING,
                "consultation": AppointmentType.OFFICE,
                "call": AppointmentType.ONLINE,
                "online": AppointmentType.ONLINE,
                "office": AppointmentType.OFFICE,
            }
            apt_type = type_map.get(appointment.type.lower(), AppointmentType.VIEWING)
            
            # Create appointment
            new_apt = Appointment(
                lead_id=appointment.lead_id,
                appointment_type=apt_type,
                scheduled_date=appointment.scheduled_at,
                duration_minutes=60,
                notes=appointment.notes,
                is_confirmed=True,
                is_cancelled=False
            )
            session.add(new_apt)
            await session.commit()
            await session.refresh(new_apt)
            
            return {
                "id": new_apt.id,
                "lead_id": new_apt.lead_id,
                "scheduled_at": new_apt.scheduled_date.isoformat(),
                "type": appointment.type,
                "status": "confirmed",
                "message": "Appointment created successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating appointment: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create appointment: {str(e)}")


@router.put("/appointments/{appointment_id}")
async def update_appointment(
    appointment_id: int,
    status: str = Query(..., description="confirmed, cancelled, completed"),
    tenant_id: int = Query(...),
):
    """Update appointment status in database"""
    async with async_session() as session:
        try:
            # Get appointment with tenant verification via lead
            result = await session.execute(
                select(Appointment)
                .join(Lead, Appointment.lead_id == Lead.id)
                .where(
                    and_(Appointment.id == appointment_id, Lead.tenant_id == tenant_id)
                )
            )
            apt = result.scalar_one_or_none()
            
            if not apt:
                raise HTTPException(status_code=404, detail="Appointment not found")
            
            # Update status flags
            if status == "confirmed":
                apt.is_confirmed = True
                apt.is_cancelled = False
            elif status == "cancelled":
                apt.is_cancelled = True
            elif status == "completed":
                apt.is_confirmed = True
                apt.is_cancelled = False
                # Could add a completed flag if needed
            
            apt.updated_at = datetime.utcnow()
            await session.commit()
            
            return {"id": appointment_id, "status": status, "message": "Appointment updated"}
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating appointment: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update appointment: {str(e)}")


@router.delete("/appointments/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    tenant_id: int = Query(...),
):
    """Cancel an appointment (soft delete - sets is_cancelled=True)"""
    async with async_session() as session:
        try:
            result = await session.execute(
                select(Appointment)
                .join(Lead, Appointment.lead_id == Lead.id)
                .where(
                    and_(Appointment.id == appointment_id, Lead.tenant_id == tenant_id)
                )
            )
            apt = result.scalar_one_or_none()
            
            if not apt:
                raise HTTPException(status_code=404, detail="Appointment not found")
            
            apt.is_cancelled = True
            apt.updated_at = datetime.utcnow()
            await session.commit()
            
            return {"id": appointment_id, "status": "cancelled", "message": "Appointment cancelled"}
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error cancelling appointment: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to cancel appointment: {str(e)}")


# ==================== AVAILABLE SLOTS ENDPOINT ====================

@router.get("/available-slots")
async def get_available_slots(
    tenant_id: int = Query(...),
    target_date: date = Query(..., alias="date"),
):
    """Get available time slots for a specific date based on availability and booked appointments"""
    async with async_session() as session:
        # Get day of week for the target date (0=Monday, 6=Sunday)
        weekday = target_date.weekday()
        day_enum = int_to_day_of_week(weekday)
        
        # Get availability slots for this day of week
        avail_result = await session.execute(
            select(AgentAvailability).where(
                and_(
                    AgentAvailability.tenant_id == tenant_id,
                    AgentAvailability.day_of_week == day_enum
                )
            )
        )
        availability_slots = avail_result.scalars().all()
        
        # If no availability defined for this day, return empty
        if not availability_slots:
            return {"date": target_date.isoformat(), "slots": []}
        
        # Get all appointments for this date
        start_dt = datetime.combine(target_date, time.min)
        end_dt = datetime.combine(target_date, time.max)
        
        apt_result = await session.execute(
            select(Appointment)
            .join(Lead, Appointment.lead_id == Lead.id)
            .where(
                and_(
                    Lead.tenant_id == tenant_id,
                    Appointment.scheduled_date >= start_dt,
                    Appointment.scheduled_date <= end_dt,
                    Appointment.is_cancelled == False
                )
            )
        )
        booked_appointments = apt_result.scalars().all()
        
        # Extract booked hours
        booked_hours = set()
        for apt in booked_appointments:
            booked_hours.add(apt.scheduled_date.hour)
        
        # Generate all available hourly slots
        all_slots = []
        for avail in availability_slots:
            start_hour = avail.start_time.hour if avail.start_time else 9
            end_hour = avail.end_time.hour if avail.end_time else 17
            
            for hour in range(start_hour, end_hour):
                slot_time = f"{hour:02d}:00"
                all_slots.append({
                    "time": slot_time,
                    "available": hour not in booked_hours
                })
        
        # Sort by time
        all_slots.sort(key=lambda x: x["time"])
        
        return {
            "date": target_date.isoformat(),
            "slots": all_slots
        }
