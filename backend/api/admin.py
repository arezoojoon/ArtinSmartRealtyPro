"""
Admin API Endpoints - Super Admin (God Mode)
Requires super_admin role for all endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
import secrets

from database import (
    async_session, Tenant, Lead, User, ConversationState,
    LeadStatus, get_tenant_by_id
)
from auth import get_current_user, require_role

router = APIRouter(prefix="/admin", tags=["Admin - God Mode"])


# ==================== TENANT MANAGEMENT ====================

@router.get("/tenants")
async def get_all_tenants(
    current_user: User = Depends(require_role("super_admin"))
):
    """Get list of all tenants with stats"""
    async with async_session() as session:
        # Get tenants
        result = await session.execute(select(Tenant))
        tenants = result.scalars().all()
        
        tenant_list = []
        for tenant in tenants:
            # Count leads
            leads_result = await session.execute(
                select(func.count(Lead.id)).where(Lead.tenant_id == tenant.id)
            )
            leads_count = leads_result.scalar()
            
            # Count agents
            agents_result = await session.execute(
                select(func.count(User.id)).where(
                    and_(User.tenant_id == tenant.id, User.role == "agent")
                )
            )
            agents_count = agents_result.scalar()
            
            # Token usage (mock - implement actual tracking)
            token_usage = 0  # TODO: Implement from usage tracking table
            
            tenant_list.append({
                "id": tenant.id,
                "name": tenant.name,
                "domain": tenant.domain,
                "status": tenant.status,
                "plan": tenant.plan,
                "leads_count": leads_count,
                "agents_count": agents_count,
                "token_usage": token_usage,
                "created_at": tenant.created_at.isoformat()
            })
        
        return tenant_list


@router.get("/tenants/{tenant_id}")
async def get_tenant_details(
    tenant_id: int,
    current_user: User = Depends(require_role("super_admin"))
):
    """Get detailed tenant information"""
    tenant = await get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    async with async_session() as session:
        # Get conversion stats
        total_leads = await session.execute(
            select(func.count(Lead.id)).where(Lead.tenant_id == tenant_id)
        )
        qualified_leads = await session.execute(
            select(func.count(Lead.id)).where(
                and_(Lead.tenant_id == tenant_id, Lead.status == LeadStatus.QUALIFIED)
            )
        )
        
        return {
            "id": tenant.id,
            "name": tenant.name,
            "domain": tenant.domain,
            "status": tenant.status,
            "plan": tenant.plan,
            "total_leads": total_leads.scalar(),
            "qualified_leads": qualified_leads.scalar(),
            "conversion_rate": (qualified_leads.scalar() / total_leads.scalar() * 100) if total_leads.scalar() > 0 else 0,
            "created_at": tenant.created_at.isoformat()
        }


@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: int,
    current_user: User = Depends(require_role("super_admin"))
):
    """🔴 KILL SWITCH - Suspend a tenant immediately"""
    async with async_session() as session:
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant.status = "suspended"
        await session.commit()
        
        return {"message": f"✅ Tenant {tenant.name} suspended", "tenant_id": tenant_id}


@router.post("/tenants/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: int,
    current_user: User = Depends(require_role("super_admin"))
):
    """Activate a suspended tenant"""
    async with async_session() as session:
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant.status = "active"
        await session.commit()
        
        return {"message": f"✅ Tenant {tenant.name} activated", "tenant_id": tenant_id}


@router.put("/tenants/{tenant_id}/plan")
async def update_tenant_plan(
    tenant_id: int,
    plan: str,
    current_user: User = Depends(require_role("super_admin"))
):
    """Update tenant subscription plan"""
    if plan not in ["bronze", "silver", "gold", "platinum"]:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    async with async_session() as session:
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant.plan = plan
        await session.commit()
        
        return {"message": f"✅ Plan updated to {plan}", "tenant_id": tenant_id}


@router.post("/tenants/{tenant_id}/impersonate")
async def impersonate_tenant(
    tenant_id: int,
    current_user: User = Depends(require_role("super_admin"))
):
    """Impersonate tenant for debugging/support"""
    tenant = await get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Generate temporary impersonation token
    impersonate_token = secrets.token_urlsafe(32)
    
    # TODO: Store impersonation session in Redis with TTL
    
    return {
        "message": f"✅ Impersonating {tenant.name}",
        "tenant_id": tenant_id,
        "tenant_name": tenant.name,
        "impersonate_token": impersonate_token
    }


# ==================== MONITORING ====================

@router.get("/monitoring/tokens/{tenant_id}")
async def get_token_usage(
    tenant_id: int,
    period: str = "30d",
    current_user: User = Depends(require_role("super_admin"))
):
    """Get AI token usage for a tenant"""
    # TODO: Implement actual token usage tracking
    # This should query a TokenUsage table with daily aggregates
    
    mock_data = [
        {"date": "2024-01-01", "tokens": 125000, "cost": 2.5},
        {"date": "2024-01-02", "tokens": 142000, "cost": 2.84},
        {"date": "2024-01-03", "tokens": 138000, "cost": 2.76},
    ]
    
    return {
        "tenant_id": tenant_id,
        "period": period,
        "total_tokens": sum(d["tokens"] for d in mock_data),
        "total_cost": sum(d["cost"] for d in mock_data),
        "daily_data": mock_data
    }


@router.get("/monitoring/errors")
async def get_system_errors(
    limit: int = 100,
    current_user: User = Depends(require_role("super_admin"))
):
    """Get system errors and exceptions"""
    # TODO: Implement error logging table
    return {"errors": [], "message": "Error tracking not yet implemented"}


@router.get("/monitoring/servers")
async def get_server_status(
    current_user: User = Depends(require_role("super_admin"))
):
    """Get server health metrics"""
    # TODO: Implement actual server monitoring
    import psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "status": "healthy"
    }


# ==================== BILLING ====================

@router.get("/billing/mrr")
async def get_monthly_recurring_revenue(
    current_user: User = Depends(require_role("super_admin"))
):
    """Get MRR (Monthly Recurring Revenue) analytics"""
    async with async_session() as session:
        # Count active tenants by plan
        result = await session.execute(
            select(Tenant.plan, func.count(Tenant.id))
            .where(Tenant.status == "active")
            .group_by(Tenant.plan)
        )
        plan_counts = dict(result.fetchall())
        
        # Calculate MRR (mock pricing)
        plan_prices = {"bronze": 99, "silver": 299, "gold": 599, "platinum": 1299}
        total_mrr = sum(plan_counts.get(plan, 0) * price for plan, price in plan_prices.items())
        
        # Mock monthly data for chart
        monthly_data = [
            {"month": "Oct", "revenue": total_mrr - 2000},
            {"month": "Nov", "revenue": total_mrr - 1000},
            {"month": "Dec", "revenue": total_mrr}
        ]
        
        return {
            "total_mrr": total_mrr,
            "plan_breakdown": {plan: count * plan_prices.get(plan, 0) for plan, count in plan_counts.items()},
            "monthly_data": monthly_data
        }


@router.get("/billing/invoices")
async def get_invoices(
    page: int = 1,
    current_user: User = Depends(require_role("super_admin"))
):
    """Get billing invoices"""
    # TODO: Implement Invoice table
    return {"invoices": [], "message": "Invoice system not yet implemented"}


@router.post("/billing/license")
async def generate_license_key(
    tenant_id: int,
    plan: str,
    current_user: User = Depends(require_role("super_admin"))
):
    """Generate lifetime license key for a tenant"""
    license_key = f"ARTIN-{plan.upper()}-{secrets.token_hex(8).upper()}"
    
    # TODO: Store license key in database
    
    return {
        "license_key": license_key,
        "tenant_id": tenant_id,
        "plan": plan,
        "type": "lifetime"
    }
