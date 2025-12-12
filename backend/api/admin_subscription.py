"""
Super Admin Subscription Management API
Allows platform owner to manage all tenant subscriptions
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from backend.database import get_db, Tenant, SubscriptionPlan, SubscriptionStatus
from backend.auth_config import verify_super_admin

router = APIRouter(prefix="/api/admin/subscriptions", tags=["Admin - Subscriptions"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class TenantSubscriptionInfo(BaseModel):
    """Complete subscription info for a tenant"""
    tenant_id: int
    name: str
    email: EmailStr
    company_name: Optional[str]
    phone: Optional[str]
    
    # Subscription details
    subscription_plan: str
    subscription_status: str
    trial_ends_at: Optional[datetime]
    subscription_starts_at: Optional[datetime]
    subscription_ends_at: Optional[datetime]
    billing_cycle: Optional[str]
    payment_method: Optional[str]
    last_payment_date: Optional[datetime]
    next_payment_date: Optional[datetime]
    
    # Account status
    is_active: bool
    created_at: datetime
    
    # Calculated fields
    days_remaining: Optional[int]
    is_trial: bool
    is_expired: bool


class UpdatePlanRequest(BaseModel):
    """Request to change tenant's plan"""
    tenant_id: int
    new_plan: SubscriptionPlan
    billing_cycle: str = "monthly"  # monthly or yearly
    extend_days: Optional[int] = None  # Optional: extend subscription by X days


class ExtendTrialRequest(BaseModel):
    """Request to extend trial period"""
    tenant_id: int
    days: int = 7  # Default 7 days extension


class ActivateSubscriptionRequest(BaseModel):
    """Manually activate a subscription"""
    tenant_id: int
    plan: SubscriptionPlan
    billing_cycle: str = "monthly"
    duration_days: int = 30  # Default 30 days


class SuspendTenantRequest(BaseModel):
    """Suspend or reactivate tenant"""
    tenant_id: int
    reason: Optional[str] = None


class SubscriptionStats(BaseModel):
    """Overall subscription statistics"""
    total_tenants: int
    active_subscriptions: int
    trial_subscriptions: int
    expired_subscriptions: int
    cancelled_subscriptions: int
    suspended_subscriptions: int
    
    # By plan
    free_plan_count: int
    basic_plan_count: int
    pro_plan_count: int
    
    # Revenue estimates (monthly)
    monthly_revenue_basic: float
    monthly_revenue_pro: float
    total_monthly_revenue: float


# ============================================
# HELPER FUNCTIONS
# ============================================

def calculate_days_remaining(subscription_ends_at: Optional[datetime], trial_ends_at: Optional[datetime]) -> Optional[int]:
    """Calculate days remaining in subscription/trial"""
    now = datetime.utcnow()
    
    if subscription_ends_at and subscription_ends_at > now:
        return (subscription_ends_at - now).days
    elif trial_ends_at and trial_ends_at > now:
        return (trial_ends_at - now).days
    
    return None


# ============================================
# API ENDPOINTS
# ============================================

@router.get("/stats", response_model=SubscriptionStats)
async def get_subscription_stats(
    admin_verified: bool = Depends(verify_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall subscription statistics
    Requires: Super Admin authentication
    """
    
    # Count total tenants
    total_result = await db.execute(select(func.count(Tenant.id)))
    total_tenants = total_result.scalar() or 0
    
    # Count by status
    active_result = await db.execute(
        select(func.count(Tenant.id)).where(Tenant.subscription_status == SubscriptionStatus.ACTIVE)
    )
    active_count = active_result.scalar() or 0
    
    trial_result = await db.execute(
        select(func.count(Tenant.id)).where(Tenant.subscription_status == SubscriptionStatus.TRIAL)
    )
    trial_count = trial_result.scalar() or 0
    
    expired_result = await db.execute(
        select(func.count(Tenant.id)).where(Tenant.subscription_status == SubscriptionStatus.EXPIRED)
    )
    expired_count = expired_result.scalar() or 0
    
    cancelled_result = await db.execute(
        select(func.count(Tenant.id)).where(Tenant.subscription_status == SubscriptionStatus.CANCELLED)
    )
    cancelled_count = cancelled_result.scalar() or 0
    
    suspended_result = await db.execute(
        select(func.count(Tenant.id)).where(Tenant.subscription_status == SubscriptionStatus.SUSPENDED)
    )
    suspended_count = suspended_result.scalar() or 0
    
    # Count by plan
    free_result = await db.execute(
        select(func.count(Tenant.id)).where(Tenant.subscription_plan == SubscriptionPlan.FREE)
    )
    free_count = free_result.scalar() or 0
    
    basic_result = await db.execute(
        select(func.count(Tenant.id)).where(Tenant.subscription_plan == SubscriptionPlan.BASIC)
    )
    basic_count = basic_result.scalar() or 0
    
    pro_result = await db.execute(
        select(func.count(Tenant.id)).where(Tenant.subscription_plan == SubscriptionPlan.PRO)
    )
    pro_count = pro_result.scalar() or 0
    
    # Calculate revenue (active subscriptions only)
    basic_monthly_result = await db.execute(
        select(func.count(Tenant.id)).where(
            and_(
                Tenant.subscription_plan == SubscriptionPlan.BASIC,
                Tenant.subscription_status == SubscriptionStatus.ACTIVE,
                Tenant.billing_cycle == "monthly"
            )
        )
    )
    basic_monthly = basic_monthly_result.scalar() or 0
    
    basic_yearly_result = await db.execute(
        select(func.count(Tenant.id)).where(
            and_(
                Tenant.subscription_plan == SubscriptionPlan.BASIC,
                Tenant.subscription_status == SubscriptionStatus.ACTIVE,
                Tenant.billing_cycle == "yearly"
            )
        )
    )
    basic_yearly = basic_yearly_result.scalar() or 0
    
    pro_monthly_result = await db.execute(
        select(func.count(Tenant.id)).where(
            and_(
                Tenant.subscription_plan == SubscriptionPlan.PRO,
                Tenant.subscription_status == SubscriptionStatus.ACTIVE,
                Tenant.billing_cycle == "monthly"
            )
        )
    )
    pro_monthly = pro_monthly_result.scalar() or 0
    
    pro_yearly_result = await db.execute(
        select(func.count(Tenant.id)).where(
            and_(
                Tenant.subscription_plan == SubscriptionPlan.PRO,
                Tenant.subscription_status == SubscriptionStatus.ACTIVE,
                Tenant.billing_cycle == "yearly"
            )
        )
    )
    pro_yearly = pro_yearly_result.scalar() or 0
    
    # Revenue calculation
    basic_revenue = (basic_monthly * 99) + (basic_yearly * 999 / 12)
    pro_revenue = (pro_monthly * 199) + (pro_yearly * 1999 / 12)
    total_revenue = basic_revenue + pro_revenue
    
    return SubscriptionStats(
        total_tenants=total_tenants,
        active_subscriptions=active_count,
        trial_subscriptions=trial_count,
        expired_subscriptions=expired_count,
        cancelled_subscriptions=cancelled_count,
        suspended_subscriptions=suspended_count,
        free_plan_count=free_count,
        basic_plan_count=basic_count,
        pro_plan_count=pro_count,
        monthly_revenue_basic=round(basic_revenue, 2),
        monthly_revenue_pro=round(pro_revenue, 2),
        total_monthly_revenue=round(total_revenue, 2)
    )


@router.get("/tenants", response_model=List[TenantSubscriptionInfo])
async def list_all_tenants(
    admin_verified: bool = Depends(verify_super_admin),
    plan: Optional[SubscriptionPlan] = None,
    status: Optional[SubscriptionStatus] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all tenants with subscription details
    Requires: Super Admin authentication
    
    Filters:
    - plan: Filter by subscription plan (free, basic, pro)
    - status: Filter by subscription status (trial, active, expired, etc.)
    - search: Search by name, email, or company
    """
    
    # Build query
    query = select(Tenant)
    
    # Apply filters
    if plan:
        query = query.where(Tenant.subscription_plan == plan)
    
    if status:
        query = query.where(Tenant.subscription_status == status)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Tenant.name.ilike(search_pattern),
                Tenant.email.ilike(search_pattern),
                Tenant.company_name.ilike(search_pattern)
            )
        )
    
    # Order by created_at desc
    query = query.order_by(Tenant.created_at.desc())
    
    # Pagination
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    tenants = result.scalars().all()
    
    # Convert to response model
    tenant_list = []
    now = datetime.utcnow()
    
    for tenant in tenants:
        is_trial = tenant.subscription_status == SubscriptionStatus.TRIAL
        is_expired = False
        
        if tenant.trial_ends_at and tenant.trial_ends_at < now:
            is_expired = True
        elif tenant.subscription_ends_at and tenant.subscription_ends_at < now:
            is_expired = True
        
        days_remaining = calculate_days_remaining(tenant.subscription_ends_at, tenant.trial_ends_at)
        
        tenant_list.append(TenantSubscriptionInfo(
            tenant_id=tenant.id,
            name=tenant.name,
            email=tenant.email,
            company_name=tenant.company_name,
            phone=tenant.phone,
            subscription_plan=tenant.subscription_plan.value,
            subscription_status=tenant.subscription_status.value,
            trial_ends_at=tenant.trial_ends_at,
            subscription_starts_at=tenant.subscription_starts_at,
            subscription_ends_at=tenant.subscription_ends_at,
            billing_cycle=tenant.billing_cycle,
            payment_method=tenant.payment_method,
            last_payment_date=tenant.last_payment_date,
            next_payment_date=tenant.next_payment_date,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
            days_remaining=days_remaining,
            is_trial=is_trial,
            is_expired=is_expired
        ))
    
    return tenant_list


@router.post("/update-plan")
async def update_tenant_plan(
    request: UpdatePlanRequest,
    admin_verified: bool = Depends(verify_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually change a tenant's subscription plan
    Requires: Super Admin authentication
    """
    
    # Get tenant
    result = await db.execute(select(Tenant).where(Tenant.id == request.tenant_id))
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Update plan
    old_plan = tenant.subscription_plan
    tenant.subscription_plan = request.new_plan
    tenant.billing_cycle = request.billing_cycle
    
    # If extending subscription
    if request.extend_days:
        if tenant.subscription_ends_at:
            tenant.subscription_ends_at += timedelta(days=request.extend_days)
        else:
            tenant.subscription_ends_at = datetime.utcnow() + timedelta(days=request.extend_days)
        
        tenant.next_payment_date = tenant.subscription_ends_at
    
    await db.commit()
    await db.refresh(tenant)
    
    return {
        "status": "success",
        "message": f"Updated plan from {old_plan.value} to {request.new_plan.value}",
        "tenant_id": tenant.id,
        "new_plan": tenant.subscription_plan.value,
        "subscription_ends_at": tenant.subscription_ends_at
    }


@router.post("/extend-trial")
async def extend_trial_period(
    request: ExtendTrialRequest,
    admin_verified: bool = Depends(verify_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Extend a tenant's trial period
    Requires: Super Admin authentication
    """
    
    # Get tenant
    result = await db.execute(select(Tenant).where(Tenant.id == request.tenant_id))
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Extend trial
    if tenant.trial_ends_at:
        tenant.trial_ends_at += timedelta(days=request.days)
    else:
        tenant.trial_ends_at = datetime.utcnow() + timedelta(days=request.days)
    
    # Set status to trial if not already
    if tenant.subscription_status != SubscriptionStatus.TRIAL:
        tenant.subscription_status = SubscriptionStatus.TRIAL
    
    await db.commit()
    await db.refresh(tenant)
    
    return {
        "status": "success",
        "message": f"Extended trial by {request.days} days",
        "tenant_id": tenant.id,
        "trial_ends_at": tenant.trial_ends_at
    }


@router.post("/activate")
async def manually_activate_subscription(
    request: ActivateSubscriptionRequest,
    admin_verified: bool = Depends(verify_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually activate a subscription (bypass payment)
    Requires: Super Admin authentication
    """
    
    # Get tenant
    result = await db.execute(select(Tenant).where(Tenant.id == request.tenant_id))
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Activate subscription
    now = datetime.utcnow()
    tenant.subscription_plan = request.plan
    tenant.subscription_status = SubscriptionStatus.ACTIVE
    tenant.subscription_starts_at = now
    tenant.subscription_ends_at = now + timedelta(days=request.duration_days)
    tenant.billing_cycle = request.billing_cycle
    tenant.next_payment_date = tenant.subscription_ends_at
    tenant.payment_method = "admin_activated"
    tenant.last_payment_date = now
    
    await db.commit()
    await db.refresh(tenant)
    
    return {
        "status": "success",
        "message": f"Activated {request.plan.value} subscription for {request.duration_days} days",
        "tenant_id": tenant.id,
        "plan": tenant.subscription_plan.value,
        "subscription_ends_at": tenant.subscription_ends_at
    }


@router.post("/suspend")
async def suspend_tenant(
    request: SuspendTenantRequest,
    admin_verified: bool = Depends(verify_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Suspend or reactivate a tenant
    Requires: Super Admin authentication
    """
    
    # Get tenant
    result = await db.execute(select(Tenant).where(Tenant.id == request.tenant_id))
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Toggle suspension
    if tenant.subscription_status == SubscriptionStatus.SUSPENDED:
        # Reactivate
        tenant.subscription_status = SubscriptionStatus.ACTIVE
        message = "Tenant reactivated"
    else:
        # Suspend
        tenant.subscription_status = SubscriptionStatus.SUSPENDED
        message = f"Tenant suspended. Reason: {request.reason or 'Admin action'}"
    
    await db.commit()
    await db.refresh(tenant)
    
    return {
        "status": "success",
        "message": message,
        "tenant_id": tenant.id,
        "new_status": tenant.subscription_status.value
    }


@router.delete("/tenant/{tenant_id}")
async def delete_tenant(
    tenant_id: int,
    admin_verified: bool = Depends(verify_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a tenant (USE WITH CAUTION!)
    Requires: Super Admin authentication
    """
    
    # Get tenant
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    tenant_email = tenant.email
    
    # Delete
    await db.delete(tenant)
    await db.commit()
    
    return {
        "status": "success",
        "message": f"Deleted tenant: {tenant_email}",
        "tenant_id": tenant_id
    }
