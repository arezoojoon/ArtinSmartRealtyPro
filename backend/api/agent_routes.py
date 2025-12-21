"""
Artin Smart Realty - Agent API Routes
Agent-specific endpoints for sales staff with restricted access
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import logging

router = APIRouter(prefix="/api/v1/agent", tags=["Agent"])

logger = logging.getLogger(__name__)


# ==================== PYDANTIC MODELS ====================

class TaskCreate(BaseModel):
    lead_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_time: Optional[str] = None
    priority: str = Field(default="medium", description="low, medium, high")

class TaskResponse(BaseModel):
    id: int
    lead_id: Optional[int]
    lead_name: Optional[str] = None
    title: str
    description: Optional[str]
    due_time: Optional[str]
    priority: str
    completed: bool = False
    created_at: datetime

class LeadNoteCreate(BaseModel):
    content: str = Field(..., min_length=1)

class SendPDFRequest(BaseModel):
    type: str = Field(default="property_brochure", description="property_brochure, roi_report, comparison")


# ==================== MY LEADS ENDPOINTS ====================

@router.get("/leads")
async def get_my_leads(
    # current_agent = Depends(get_current_agent),
    # db: AsyncSession = Depends(get_db),
):
    """Get leads assigned to the current agent"""
    # TODO: Filter leads by assigned_agent_id from current_agent
    # For now, return sample data
    return [
        {
            "id": 1,
            "name": "Sarah Jenkins",
            "phone": "+971501234567",
            "email": "sarah@email.com",
            "property_type": "Villa",
            "preferred_location": "Palm Jumeirah",
            "budget_min": 2000000,
            "budget_max": 5000000,
            "lead_score": 85,
            "status": "qualified",
            "last_contact": datetime.now().isoformat(),
        },
        {
            "id": 2,
            "name": "Michael Chen",
            "phone": "+971507654321",
            "email": "michael@email.com",
            "property_type": "Penthouse",
            "preferred_location": "Downtown",
            "budget_min": 3000000,
            "budget_max": 3500000,
            "lead_score": 72,
            "status": "negotiating",
            "last_contact": datetime.now().isoformat(),
        },
    ]


@router.get("/leads/{lead_id}")
async def get_lead_details(
    lead_id: int,
    # current_agent = Depends(get_current_agent),
    # db: AsyncSession = Depends(get_db),
):
    """Get detailed information about a specific lead"""
    # TODO: Verify lead is assigned to this agent
    return {
        "id": lead_id,
        "name": "Sarah Jenkins",
        "phone": "+971501234567",
        "email": "sarah@email.com",
        "property_type": "Villa",
        "preferred_location": "Palm Jumeirah",
        "budget_min": 2000000,
        "budget_max": 5000000,
        "lead_score": 85,
        "status": "qualified",
        "notes": [
            {"id": 1, "content": "Called on Monday, interested in beach view", "created_at": datetime.now().isoformat()},
            {"id": 2, "content": "Scheduled viewing for Palm Villa", "created_at": datetime.now().isoformat()},
        ],
        "activities": [
            {"type": "call", "description": "15 min call", "timestamp": datetime.now().isoformat()},
            {"type": "message", "description": "WhatsApp message sent", "timestamp": datetime.now().isoformat()},
        ]
    }


# ==================== TASKS ENDPOINTS ====================

@router.get("/tasks")
async def get_my_tasks(
    # current_agent = Depends(get_current_agent),
    # db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """Get tasks for the current agent"""
    return [
        {
            "id": 1,
            "lead_id": 1,
            "lead_name": "Ahmad Ahmadi",
            "title": "Call Mr. Ahmadi",
            "description": "Follow up on Palm Villa viewing",
            "dueTime": "4:00 PM Today",
            "priority": "high",
            "completed": False,
        },
        {
            "id": 2,
            "lead_id": 2,
            "lead_name": "Sarah Jenkins",
            "title": "Send Property Brochure",
            "description": "Email Marina Heights PDF",
            "dueTime": "5:30 PM Today",
            "priority": "medium",
            "completed": False,
        },
        {
            "id": 3,
            "lead_id": 3,
            "lead_name": "Michael Chen",
            "title": "Schedule Viewing",
            "description": "Book Downtown Penthouse tour",
            "dueTime": "Tomorrow 10:00 AM",
            "priority": "low",
            "completed": False,
        },
    ]


@router.post("/tasks")
async def create_task(
    task: TaskCreate,
    # current_agent = Depends(get_current_agent),
    # db: AsyncSession = Depends(get_db),
):
    """Create a new task"""
    return {
        "id": 999,
        "lead_id": task.lead_id,
        "title": task.title,
        "description": task.description,
        "dueTime": task.due_time or "Today",
        "priority": task.priority,
        "completed": False,
        "created_at": datetime.now().isoformat(),
    }


@router.put("/tasks/{task_id}/done")
async def mark_task_done(
    task_id: int,
    # current_agent = Depends(get_current_agent),
    # db: AsyncSession = Depends(get_db),
):
    """Mark a task as completed"""
    return {"id": task_id, "completed": True, "message": "Task marked as done"}


@router.post("/tasks/{task_id}/snooze")
async def snooze_task(
    task_id: int,
    hours: int = Query(default=1, ge=1, le=72),
    # current_agent = Depends(get_current_agent),
    # db: AsyncSession = Depends(get_db),
):
    """Snooze a task for specified hours"""
    new_due_time = datetime.now() + timedelta(hours=hours)
    return {
        "id": task_id,
        "dueTime": new_due_time.strftime("%I:%M %p"),
        "message": f"Task snoozed for {hours} hour(s)"
    }


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    # current_agent = Depends(get_current_agent),
    # db: AsyncSession = Depends(get_db),
):
    """Complete a task"""
    return {"id": task_id, "completed": True, "message": "Task completed"}


# ==================== QUICK ACTIONS ====================

@router.post("/leads/{lead_id}/whatsapp")
async def send_whatsapp(
    lead_id: int,
    message: str = Query(...),
    # current_agent = Depends(get_current_agent),
    # db: AsyncSession = Depends(get_db),
):
    """Send WhatsApp message to lead"""
    # TODO: Integrate with WhatsApp API
    return {
        "lead_id": lead_id,
        "message": message,
        "status": "sent",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/leads/{lead_id}/pdf")
async def send_pdf(
    lead_id: int,
    request: SendPDFRequest,
    # current_agent = Depends(get_current_agent),
    # db: AsyncSession = Depends(get_db),
):
    """Send PDF document to lead"""
    # TODO: Generate and send PDF
    return {
        "lead_id": lead_id,
        "pdf_type": request.type,
        "status": "sent",
        "message": f"PDF ({request.type}) sent successfully"
    }


@router.post("/leads/{lead_id}/note")
async def add_note(
    lead_id: int,
    note: LeadNoteCreate,
    # current_agent = Depends(get_current_agent),
    # db: AsyncSession = Depends(get_db),
):
    """Add a note to a lead"""
    return {
        "id": 999,
        "lead_id": lead_id,
        "content": note.content,
        "created_at": datetime.now().isoformat(),
        "message": "Note added successfully"
    }


# ==================== AGENT STATS ====================

@router.get("/stats")
async def get_agent_stats(
    # current_agent = Depends(get_current_agent),
    # db: AsyncSession = Depends(get_db),
):
    """Get agent performance statistics"""
    return {
        "total_leads": 15,
        "pending_tasks": 5,
        "completed_tasks_today": 8,
        "deals_closed_month": 3,
        "response_time_avg_minutes": 12,
        "lead_conversion_rate": 25.5,
    }
