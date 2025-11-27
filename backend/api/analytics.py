"""
Tenant Analytics API Endpoints
Sales funnel, agent performance, and lead export
"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional
import io
import pandas as pd

from database import (
    async_session, Lead, User, LeadStatus, ConversationState
)
from auth import get_current_user, get_current_tenant_id

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ==================== SALES FUNNEL ====================

@router.get("/funnel")
async def get_sales_funnel(
    period: str = "30d",
    tenant_id: int = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Get sales funnel data showing conversion at each stage
    
    Funnel Stages:
    1. Started (all leads)
    2. Qualified (filled slots)
    3. Phone Captured (provided contact)
    4. Closed (status = closed_won)
    """
    # Calculate date range
    days = int(period.replace('d', ''))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    async with async_session() as session:
        # Total started
        started_result = await session.execute(
            select(func.count(Lead.id))
            .where(and_(
                Lead.tenant_id == tenant_id,
                Lead.created_at >= start_date
            ))
        )
        started = started_result.scalar() or 0
        
        # Qualified (has filled_slots with at least budget, property_type, transaction_type)
        qualified_result = await session.execute(
            select(func.count(Lead.id))
            .where(and_(
                Lead.tenant_id == tenant_id,
                Lead.created_at >= start_date,
                Lead.budget_min.isnot(None),
                Lead.property_type.isnot(None)
            ))
        )
        qualified = qualified_result.scalar() or 0
        
        # Phone captured
        phone_result = await session.execute(
            select(func.count(Lead.id))
            .where(and_(
                Lead.tenant_id == tenant_id,
                Lead.created_at >= start_date,
                Lead.phone_number.isnot(None)
            ))
        )
        phone_captured = phone_result.scalar() or 0
        
        # Closed won
        closed_result = await session.execute(
            select(func.count(Lead.id))
            .where(and_(
                Lead.tenant_id == tenant_id,
                Lead.created_at >= start_date,
                Lead.status == LeadStatus.CLOSED_WON
            ))
        )
        closed = closed_result.scalar() or 0
        
        return {
            "funnel": [
                {
                    "name": "Started",
                    "value": started,
                    "description": "Total leads who initiated conversation",
                    "fill": "#3B82F6"
                },
                {
                    "name": "Qualified",
                    "value": qualified,
                    "description": "Leads who provided budget & preferences",
                    "fill": "#10B981"
                },
                {
                    "name": "Phone Captured",
                    "value": phone_captured,
                    "description": "Leads who shared contact information",
                    "fill": "#F59E0B"
                },
                {
                    "name": "Closed Won",
                    "value": closed,
                    "description": "Successfully converted deals",
                    "fill": "#EF4444"
                }
            ],
            "conversion_rates": {
                "start_to_qualified": (qualified / started * 100) if started > 0 else 0,
                "qualified_to_phone": (phone_captured / qualified * 100) if qualified > 0 else 0,
                "phone_to_closed": (closed / phone_captured * 100) if phone_captured > 0 else 0,
                "overall": (closed / started * 100) if started > 0 else 0
            }
        }


# ==================== AGENT PERFORMANCE ====================

@router.get("/agents")
async def get_agent_performance(
    period: str = "30d",
    tenant_id: int = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Get agent leaderboard with performance metrics"""
    days = int(period.replace('d', ''))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    async with async_session() as session:
        # Get agents
        agents_result = await session.execute(
            select(User).where(and_(
                User.tenant_id == tenant_id,
                User.role == "agent"
            ))
        )
        agents = agents_result.scalars().all()
        
        agent_stats = []
        for agent in agents:
            # Count closed deals
            closed_result = await session.execute(
                select(func.count(Lead.id), func.sum(Lead.budget_max))
                .where(and_(
                    Lead.tenant_id == tenant_id,
                    Lead.assigned_to == agent.id,
                    Lead.status == LeadStatus.CLOSED_WON,
                    Lead.updated_at >= start_date
                ))
            )
            closed_count, total_value = closed_result.first()
            closed_count = closed_count or 0
            total_value = total_value or 0
            
            # Count total assigned leads
            total_result = await session.execute(
                select(func.count(Lead.id))
                .where(and_(
                    Lead.tenant_id == tenant_id,
                    Lead.assigned_to == agent.id,
                    Lead.created_at >= start_date
                ))
            )
            total_assigned = total_result.scalar() or 0
            
            # Calculate conversion rate
            conversion_rate = (closed_count / total_assigned * 100) if total_assigned > 0 else 0
            
            # Mock response time (TODO: implement actual response time tracking)
            avg_response_time = "2.5m"
            
            agent_stats.append({
                "id": agent.id,
                "name": agent.name or f"Agent {agent.id}",
                "email": agent.email,
                "closed_deals": closed_count,
                "total_value": total_value,
                "conversion_rate": round(conversion_rate, 1),
                "avg_response_time": avg_response_time
            })
        
        # Sort by closed deals
        agent_stats.sort(key=lambda x: x["closed_deals"], reverse=True)
        
        return {"agents": agent_stats}


# ==================== EXPORT TO EXCEL ====================

@router.get("/export")
async def export_leads(
    period: str = "30d",
    status: Optional[str] = None,
    tenant_id: int = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Export leads to Excel file
    CRITICAL: This is essential for agency's internal reporting
    """
    days = int(period.replace('d', ''))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    async with async_session() as session:
        # Build query
        query = select(Lead).where(and_(
            Lead.tenant_id == tenant_id,
            Lead.created_at >= start_date
        ))
        
        if status:
            query = query.where(Lead.status == status)
        
        result = await session.execute(query)
        leads = result.scalars().all()
        
        # Convert to DataFrame
        data = []
        for lead in leads:
            data.append({
                "ID": lead.id,
                "Name": lead.name or "N/A",
                "Phone": lead.phone_number or "N/A",
                "Email": lead.email or "N/A",
                "Language": lead.language.value if lead.language else "N/A",
                "Status": lead.status.value if lead.status else "new",
                "Property Type": lead.property_type.value if lead.property_type else "N/A",
                "Transaction Type": lead.transaction_type.value if lead.transaction_type else "N/A",
                "Budget Min": lead.budget_min or 0,
                "Budget Max": lead.budget_max or 0,
                "Purpose": lead.purpose.value if lead.purpose else "N/A",
                "Conversation State": lead.conversation_state.value if lead.conversation_state else "start",
                "Created At": lead.created_at.strftime("%Y-%m-%d %H:%M"),
                "Last Message At": lead.last_message_at.strftime("%Y-%m-%d %H:%M") if lead.last_message_at else "N/A"
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Leads')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Leads']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=leads_export_{datetime.now().strftime('%Y%m%d')}.xlsx"
            }
        )
