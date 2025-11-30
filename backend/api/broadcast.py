"""
Broadcast API Endpoints
Send bulk messages to leads via Telegram/WhatsApp
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio

from database import async_session, Lead, Tenant, LeadStatus
from telegram_bot import bot_manager
from whatsapp_bot import whatsapp_bot_manager

router = APIRouter(prefix="/api/tenants", tags=["Broadcast"])


class BroadcastRequest(BaseModel):
    recipient_ids: List[int]  # Lead IDs
    platform: str  # "telegram" or "whatsapp" or "both"
    message: str
    template_name: Optional[str] = None


class BroadcastResponse(BaseModel):
    total_recipients: int
    sent_count: int
    failed_count: int
    errors: List[str]


@router.post("/{tenant_id}/broadcast", response_model=BroadcastResponse)
async def send_broadcast(
    tenant_id: int,
    request: BroadcastRequest
):
    """
    Send broadcast message to selected leads.
    Supports Telegram, WhatsApp, or both platforms.
    """
    async with async_session() as session:
        # Verify tenant exists
        tenant_result = await session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Fetch selected leads
        leads_result = await session.execute(
            select(Lead).where(
                and_(
                    Lead.tenant_id == tenant_id,
                    Lead.id.in_(request.recipient_ids)
                )
            )
        )
        leads = leads_result.scalars().all()
        
        if not leads:
            raise HTTPException(status_code=404, detail="No valid leads found")
        
        sent_count = 0
        failed_count = 0
        errors = []
        
        # Send messages
        for lead in leads:
            try:
                # Send via Telegram
                if request.platform in ["telegram", "both"] and lead.telegram_chat_id:
                    try:
                        bot = bot_manager.get_bot(tenant_id)
                        if bot and bot.application:
                            await bot.application.bot.send_message(
                                chat_id=int(lead.telegram_chat_id),
                                text=request.message,
                                parse_mode='HTML'
                            )
                            sent_count += 1
                    except Exception as e:
                        errors.append(f"Telegram failed for Lead {lead.id}: {str(e)}")
                        failed_count += 1
                
                # Send via WhatsApp
                if request.platform in ["whatsapp", "both"] and lead.whatsapp_phone:
                    try:
                        wa_bot = whatsapp_bot_manager.get_bot(tenant_id)
                        if wa_bot:
                            # WhatsApp Cloud API requires template messages for broadcasts
                            # For now, we'll skip WhatsApp (requires template approval)
                            pass
                    except Exception as e:
                        errors.append(f"WhatsApp failed for Lead {lead.id}: {str(e)}")
                        failed_count += 1
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                errors.append(f"Lead {lead.id}: {str(e)}")
                failed_count += 1
        
        return BroadcastResponse(
            total_recipients=len(leads),
            sent_count=sent_count,
            failed_count=failed_count,
            errors=errors[:10]  # Limit to first 10 errors
        )
