"""
Admin API Endpoints - Super Admin (God Mode)
Requires super_admin role for all endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import secrets
import jwt
import hashlib
import os

from database import (
    async_session, Tenant, Lead, ConversationState,
    LeadStatus, SubscriptionStatus
)

router = APIRouter(prefix="/admin", tags=["Admin - God Mode"])
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"

# Pydantic models for request bodies
class CreateTenantRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    company_name: str

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256."""
    salt = os.getenv("PASSWORD_SALT", "artinsmartrealty_salt_v2")
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

def decode_jwt_token(token: str) -> dict:
    """Decode and verify JWT token."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_super_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """Verify that the current user is a Super Admin (tenant_id=0)."""
    payload = decode_jwt_token(credentials.credentials)
    tenant_id = payload.get("tenant_id")
    
    if tenant_id != 0:
        raise HTTPException(
            status_code=403, 
            detail="Super Admin access required"
        )
    
    return tenant_id


# ==================== TENANT MANAGEMENT ====================

@router.post("/tenants")
async def create_tenant(
    request: CreateTenantRequest,
    current_admin: int = Depends(get_current_super_admin)
):
    """Create a new tenant (Super Admin only)"""
    async with async_session() as session:
        # Check if email already exists
        result = await session.execute(select(Tenant).where(Tenant.email == request.email))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        password_hash = hash_password(request.password)
        
        # Create new tenant
        new_tenant = Tenant(
            name=request.name,
            email=request.email,
            password_hash=password_hash,
            company_name=request.company_name,
            subscription_status=SubscriptionStatus.TRIAL,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        session.add(new_tenant)
        await session.commit()
        await session.refresh(new_tenant)
        
        return {
            "message": "✅ Tenant created successfully",
            "tenant": {
                "id": new_tenant.id,
                "name": new_tenant.name,
                "email": new_tenant.email,
                "company_name": new_tenant.company_name,
                "subscription_status": new_tenant.subscription_status.value
            }
        }


@router.get("/tenants")
async def get_all_tenants(
    current_admin: int = Depends(get_current_super_admin)
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
            
            # Agents count - simplified (no User table, set to 0 for now)
            agents_count = 0  # TODO: Implement agents table if needed
            
            tenant_list.append({
                "id": tenant.id,
                "name": tenant.name or tenant.company_name,
                "email": tenant.email,
                "company_name": tenant.company_name,
                "subscription_status": tenant.subscription_status.value if tenant.subscription_status else "trial",
                "total_leads": leads_count,
                "agents_count": agents_count,
                "created_at": tenant.created_at.isoformat()
            })
        
        return tenant_list


@router.get("/tenants/{tenant_id}")
async def get_tenant_details(
    tenant_id: int,
    current_admin: int = Depends(get_current_super_admin)
):
    """Get detailed tenant information"""
    async with async_session() as session:
        # Get tenant
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        # Get conversion stats
        total_leads = await session.execute(
            select(func.count(Lead.id)).where(Lead.tenant_id == tenant_id)
        )
        qualified_leads = await session.execute(
            select(func.count(Lead.id)).where(
                and_(Lead.tenant_id == tenant_id, Lead.status == LeadStatus.QUALIFIED)
            )
        )
        
        total_leads_count = total_leads.scalar()
        qualified_leads_count = qualified_leads.scalar()
        
        return {
            "id": tenant.id,
            "name": tenant.name or tenant.company_name,
            "email": tenant.email,
            "company_name": tenant.company_name,
            "subscription_status": tenant.subscription_status.value if tenant.subscription_status else "trial",
            "total_leads": total_leads_count,
            "qualified_leads": qualified_leads_count,
            "conversion_rate": (qualified_leads_count / total_leads_count * 100) if total_leads_count > 0 else 0,
            "created_at": tenant.created_at.isoformat()
        }


@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: int,
    current_admin: int = Depends(get_current_super_admin)
):
    """🔴 KILL SWITCH - Suspend a tenant immediately"""
    async with async_session() as session:
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant.subscription_status = SubscriptionStatus.SUSPENDED
        tenant.is_active = False
        await session.commit()
        
        tenant_name = tenant.name or tenant.company_name
        return {"message": f"✅ Tenant {tenant_name} suspended", "tenant_id": tenant_id}


@router.post("/tenants/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: int,
    current_admin: int = Depends(get_current_super_admin)
):
    """Activate a suspended tenant"""
    async with async_session() as session:
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant.subscription_status = SubscriptionStatus.ACTIVE
        tenant.is_active = True
        await session.commit()
        
        tenant_name = tenant.name or tenant.company_name
        return {"message": f"✅ Tenant {tenant_name} activated", "tenant_id": tenant_id}


class UpdateSubscriptionRequest(BaseModel):
    status: str

class UpdateTenantCredentialsRequest(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    name: Optional[str] = None
    company_name: Optional[str] = None

@router.put("/tenants/{tenant_id}/subscription")
async def update_tenant_subscription(
    tenant_id: int,
    request: UpdateSubscriptionRequest,
    current_admin: int = Depends(get_current_super_admin)
):
    """Update tenant subscription status"""
    status = request.status
    valid_statuses = ["trial", "active", "suspended", "expired"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    async with async_session() as session:
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant.subscription_status = SubscriptionStatus[status.upper()]
        await session.commit()
        
        return {"message": f"✅ Subscription updated to {status}", "tenant_id": tenant_id}


@router.put("/tenants/{tenant_id}/credentials")
async def update_tenant_credentials(
    tenant_id: int,
    request: UpdateTenantCredentialsRequest,
    current_admin: int = Depends(get_current_super_admin)
):
    """Update tenant email, password, name, or company name"""
    async with async_session() as session:
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Update fields if provided
        if request.email:
            # Check if email already exists for another tenant
            existing = await session.execute(
                select(Tenant).where(Tenant.email == request.email, Tenant.id != tenant_id)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Email already in use by another tenant")
            tenant.email = request.email
        
        if request.password:
            # Hash the password
            tenant.password_hash = hashlib.sha256(request.password.encode()).hexdigest()
        
        if request.name:
            tenant.name = request.name
        
        if request.company_name:
            tenant.company_name = request.company_name
        
        tenant.updated_at = datetime.utcnow()
        await session.commit()
        
        return {
            "message": "✅ Tenant credentials updated successfully",
            "tenant_id": tenant_id,
            "email": tenant.email,
            "name": tenant.name,
            "company_name": tenant.company_name
        }


@router.post("/tenants/{tenant_id}/impersonate")
async def impersonate_tenant(
    tenant_id: int,
    current_admin: int = Depends(get_current_super_admin)
):
    """Impersonate tenant for debugging/support"""
    async with async_session() as session:
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Extract tenant data before session closes
        tenant_name = tenant.name or tenant.company_name or tenant.email
    
    # Generate temporary impersonation token
    impersonate_token = secrets.token_urlsafe(32)
    
    # TODO: Store impersonation session in Redis with TTL
    
    return {
        "message": f"✅ Impersonating {tenant_name}",
        "tenant_id": tenant_id,
        "tenant_name": tenant_name,
        "impersonate_token": impersonate_token
    }


# ==================== MONITORING ====================

@router.get("/monitoring/tokens/{tenant_id}")
async def get_token_usage(
    tenant_id: int,
    period: str = "30d",
    current_admin: int = Depends(get_current_super_admin)
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
    current_admin: int = Depends(get_current_super_admin)
):
    """Get system errors and exceptions"""
    # TODO: Implement error logging table
    return {"errors": [], "message": "Error tracking not yet implemented"}


@router.get("/monitoring/servers")
async def get_server_status(
    current_admin: int = Depends(get_current_super_admin)
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
    current_admin: int = Depends(get_current_super_admin)
):
    """Get MRR (Monthly Recurring Revenue) analytics"""
    async with async_session() as session:
        # Count active tenants by subscription status
        result = await session.execute(
            select(Tenant.subscription_status, func.count(Tenant.id))
            .where(Tenant.subscription_status == SubscriptionStatus.ACTIVE)
            .group_by(Tenant.subscription_status)
        )
        status_counts = dict(result.fetchall())
        
        # Calculate MRR (mock pricing - $299/month per active tenant)
        active_count = sum(status_counts.values())
        total_mrr = active_count * 299
        
        # Mock monthly data for chart
        monthly_data = [
            {"month": "Oct", "revenue": total_mrr - 2000},
            {"month": "Nov", "revenue": total_mrr - 1000},
            {"month": "Dec", "revenue": total_mrr}
        ]
        
        return {
            "total_mrr": total_mrr,
            "active_tenants": active_count,
            "monthly_data": monthly_data
        }


@router.get("/billing/invoices")
async def get_invoices(
    page: int = 1,
    current_admin: int = Depends(get_current_super_admin)
):
    """Get billing invoices"""
    # TODO: Implement Invoice table
    return {"invoices": [], "message": "Invoice system not yet implemented"}


@router.post("/billing/license")
async def generate_license_key(
    tenant_id: int,
    plan: str,
    current_admin: int = Depends(get_current_super_admin)
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
