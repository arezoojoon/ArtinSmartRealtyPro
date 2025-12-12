"""
System Health Check Endpoint
Monitors all critical services and database connectivity
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import os

from backend.database import async_session
from sqlalchemy import select, text

router = APIRouter(prefix="/api/health", tags=["Health Check"])


class ServiceStatus(BaseModel):
    """Status of a single service"""
    name: str
    status: str  # "healthy", "degraded", "down"
    response_time_ms: Optional[float] = None
    message: Optional[str] = None
    last_check: datetime


class HealthCheckResponse(BaseModel):
    """Overall system health"""
    status: str  # "healthy", "degraded", "down"
    timestamp: datetime
    services: Dict[str, ServiceStatus]
    version: str = "1.0.0"


async def check_database() -> ServiceStatus:
    """Check PostgreSQL database connectivity"""
    import time
    start = time.time()
    
    try:
        async with async_session() as session:
            # Simple query to check connection
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            
        response_time = (time.time() - start) * 1000
        
        return ServiceStatus(
            name="PostgreSQL Database",
            status="healthy" if response_time < 100 else "degraded",
            response_time_ms=round(response_time, 2),
            message=f"Connected in {response_time:.0f}ms",
            last_check=datetime.utcnow()
        )
    except Exception as e:
        return ServiceStatus(
            name="PostgreSQL Database",
            status="down",
            message=f"Connection failed: {str(e)}",
            last_check=datetime.utcnow()
        )


async def check_gemini_ai() -> ServiceStatus:
    """Check Gemini AI API availability"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return ServiceStatus(
            name="Gemini AI",
            status="down",
            message="API key not configured",
            last_check=datetime.utcnow()
        )
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)  # type: ignore
        
        # Just check if configured, don't actually call API
        return ServiceStatus(
            name="Gemini AI",
            status="healthy",
            message="API key configured",
            last_check=datetime.utcnow()
        )
    except Exception as e:
        return ServiceStatus(
            name="Gemini AI",
            status="degraded",
            message=f"Configuration issue: {str(e)}",
            last_check=datetime.utcnow()
        )


async def check_telegram_bot() -> ServiceStatus:
    """Check Telegram bot configuration"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        return ServiceStatus(
            name="Telegram Bot",
            status="down",
            message="Bot token not configured",
            last_check=datetime.utcnow()
        )
    
    return ServiceStatus(
        name="Telegram Bot",
        status="healthy",
        message="Token configured",
        last_check=datetime.utcnow()
    )


async def check_whatsapp() -> ServiceStatus:
    """Check WhatsApp Business API configuration"""
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    if not token or not phone_id:
        return ServiceStatus(
            name="WhatsApp Business",
            status="down",
            message="WhatsApp credentials not configured",
            last_check=datetime.utcnow()
        )
    
    return ServiceStatus(
        name="WhatsApp Business",
        status="healthy",
        message="Credentials configured",
        last_check=datetime.utcnow()
    )


@router.get("/", response_model=HealthCheckResponse)
async def health_check():
    """
    🏥 System Health Check
    
    Checks all critical services:
    - PostgreSQL Database
    - Gemini AI API
    - Telegram Bot
    - WhatsApp Business API
    
    Returns:
        - status: "healthy" (all green), "degraded" (some issues), "down" (critical failure)
        - services: Detailed status of each service
    """
    
    # Check all services in parallel
    import asyncio
    db_status, gemini_status, telegram_status, whatsapp_status = await asyncio.gather(
        check_database(),
        check_gemini_ai(),
        check_telegram_bot(),
        check_whatsapp()
    )
    
    services = {
        "database": db_status,
        "gemini_ai": gemini_status,
        "telegram": telegram_status,
        "whatsapp": whatsapp_status
    }
    
    # Determine overall status
    statuses = [s.status for s in services.values()]
    
    if all(s == "healthy" for s in statuses):
        overall_status = "healthy"
    elif any(s == "down" for s in statuses) and db_status.status == "down":
        overall_status = "down"  # Database down = system down
    else:
        overall_status = "degraded"
    
    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        services=services
    )


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for uptime monitoring
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "🚀 ArtinSmartRealty is running"
    }
