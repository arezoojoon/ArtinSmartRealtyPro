"""
Subscription & Registration API
Handles tenant registration, payment, and plan management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import secrets
import hashlib

from backend.database import (
    async_session, Tenant, SubscriptionPlan, SubscriptionStatus,
    Language
)
from backend.auth_config import hash_password
from sqlalchemy import select

router = APIRouter(prefix="/api/subscription", tags=["Subscription"])


# ==================== PRICING CONFIGURATION ====================

PRICING = {
    "basic": {
        "name": "Basic Plan",
        "name_fa": "پلن پایه",
        "description": "AI Bot + Follow-up Automation",
        "description_fa": "ربات هوشمند + فالو‌آپ خودکار",
        "features": [
            "WhatsApp & Telegram Bot",
            "AI-powered conversations",
            "Automated follow-ups",
            "Lead scoring & grading",
            "Appointment scheduling",
            "Multi-language support"
        ],
        "features_fa": [
            "ربات واتساپ و تلگرام",
            "مکالمات هوش مصنوعی",
            "فالوآپ خودکار",
            "امتیازدهی به لیدها",
            "زمان‌بندی قرار ملاقات",
            "پشتیبانی چند زبانه"
        ],
        "price_monthly": 99,  # USD
        "price_yearly": 999,  # USD (2 months free)
        "currency": "USD",
        "trial_days": 7,
        "max_leads": 1000,
        "max_messages_per_month": 10000
    },
    "pro": {
        "name": "Pro Plan",
        "name_fa": "پلن حرفه‌ای",
        "description": "Everything in Basic + Lead Generation",
        "description_fa": "همه امکانات پایه + لید جنریشن",
        "features": [
            "✅ All Basic features",
            "LinkedIn Lead Scraper",
            "Automated outreach campaigns",
            "Advanced analytics",
            "CRM integration",
            "White-label branding",
            "Priority support"
        ],
        "features_fa": [
            "✅ همه امکانات پلن پایه",
            "اسکرپ لید از لینکدین",
            "کمپین‌های خودکار",
            "تحلیل‌های پیشرفته",
            "یکپارچگی CRM",
            "برندینگ اختصاصی",
            "پشتیبانی اولویت‌دار"
        ],
        "price_monthly": 199,  # USD
        "price_yearly": 1999,  # USD (2 months free)
        "currency": "USD",
        "trial_days": 14,
        "max_leads": 10000,
        "max_messages_per_month": 100000
    }
}


# ==================== REQUEST/RESPONSE MODELS ====================

class RegisterRequest(BaseModel):
    """Tenant registration request"""
    name: str
    email: EmailStr
    password: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    plan: str = "basic"  # "basic" or "pro"
    billing_cycle: str = "monthly"  # "monthly" or "yearly"
    language: str = "en"


class RegisterResponse(BaseModel):
    """Tenant registration response"""
    tenant_id: int
    email: str
    plan: str
    status: str
    trial_ends_at: Optional[datetime]
    message: str
    message_fa: str


class PricingResponse(BaseModel):
    """Pricing information response"""
    plans: dict


class PaymentRequest(BaseModel):
    """Payment confirmation request"""
    tenant_id: int
    plan: str
    billing_cycle: str
    payment_method: str
    transaction_id: str


# ==================== ENDPOINTS ====================

@router.get("/pricing", response_model=PricingResponse)
async def get_pricing():
    """
    Get pricing information for all plans.
    Public endpoint - no authentication required.
    """
    return PricingResponse(plans=PRICING)


@router.post("/register", response_model=RegisterResponse)
async def register_tenant(data: RegisterRequest):
    """
    Register new tenant with selected plan.
    Starts trial period automatically.
    """
    # Validate plan
    if data.plan not in ["basic", "pro"]:
        raise HTTPException(status_code=400, detail="Invalid plan. Choose 'basic' or 'pro'")
    
    # Validate billing cycle
    if data.billing_cycle not in ["monthly", "yearly"]:
        raise HTTPException(status_code=400, detail="Invalid billing cycle")
    
    async with async_session() as session:
        # Check if email already exists
        result = await session.execute(
            select(Tenant).where(Tenant.email == data.email)
        )
        existing_tenant = result.scalar_one_or_none()
        
        if existing_tenant:
            raise HTTPException(
                status_code=400,
                detail="Email already registered. Please login instead."
            )
        
        # Calculate trial end date
        trial_days = PRICING[data.plan]["trial_days"]
        trial_ends_at = datetime.utcnow() + timedelta(days=trial_days)
        
        # Hash password
        password_hash = hash_password(data.password)
        
        # Create new tenant
        new_tenant = Tenant(
            name=data.name,
            email=data.email,
            password_hash=password_hash,
            company_name=data.company_name,
            phone=data.phone,
            subscription_plan=SubscriptionPlan.BASIC if data.plan == "basic" else SubscriptionPlan.PRO,
            subscription_status=SubscriptionStatus.TRIAL,
            trial_ends_at=trial_ends_at,
            billing_cycle=data.billing_cycle,
            default_language=Language(data.language) if data.language in ["en", "fa", "ar", "ru"] else Language.EN,
            is_active=True
        )
        
        session.add(new_tenant)
        await session.commit()
        await session.refresh(new_tenant)
        
        return RegisterResponse(
            tenant_id=int(new_tenant.id),  # type: ignore
            email=str(new_tenant.email),  # type: ignore
            plan=data.plan,
            status="trial",
            trial_ends_at=trial_ends_at,
            message=f"Registration successful! Your {trial_days}-day trial has started.",
            message_fa=f"ثبت‌نام موفق! دوره آزمایشی {trial_days} روزه شما شروع شد."
        )


@router.post("/payment/confirm")
async def confirm_payment(data: PaymentRequest):
    """
    Confirm payment and activate subscription.
    Called after successful payment via payment gateway.
    """
    async with async_session() as session:
        # Get tenant
        result = await session.execute(
            select(Tenant).where(Tenant.id == data.tenant_id)
        )
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Validate plan
        if data.plan not in ["basic", "pro"]:
            raise HTTPException(status_code=400, detail="Invalid plan")
        
        # Calculate subscription dates
        now = datetime.utcnow()
        if data.billing_cycle == "monthly":
            subscription_ends_at = now + timedelta(days=30)
            next_payment = now + timedelta(days=30)
        else:  # yearly
            subscription_ends_at = now + timedelta(days=365)
            next_payment = now + timedelta(days=365)
        
        # Update tenant subscription
        tenant.subscription_plan = SubscriptionPlan.BASIC if data.plan == "basic" else SubscriptionPlan.PRO  # type: ignore
        tenant.subscription_status = SubscriptionStatus.ACTIVE  # type: ignore
        tenant.subscription_starts_at = now  # type: ignore
        tenant.subscription_ends_at = subscription_ends_at  # type: ignore
        tenant.billing_cycle = data.billing_cycle  # type: ignore
        tenant.payment_method = data.payment_method  # type: ignore
        tenant.last_payment_date = now  # type: ignore
        tenant.next_payment_date = next_payment  # type: ignore
        
        await session.commit()
        
        return {
            "status": "success",
            "message": "Payment confirmed. Subscription activated!",
            "message_fa": "پرداخت تایید شد. اشتراک فعال شد!",
            "subscription_ends_at": subscription_ends_at.isoformat(),
            "next_payment_date": next_payment.isoformat()
        }


@router.post("/upgrade")
async def upgrade_plan(tenant_id: int, new_plan: str = "pro"):
    """
    Upgrade tenant from Basic to Pro plan.
    Pro-rates the payment.
    """
    if new_plan != "pro":
        raise HTTPException(status_code=400, detail="Can only upgrade to Pro plan")
    
    async with async_session() as session:
        result = await session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        if tenant.subscription_plan == SubscriptionPlan.PRO:  # type: ignore
            raise HTTPException(status_code=400, detail="Already on Pro plan")
        
        # Calculate pro-rated cost
        # (This is simplified - in production, calculate based on remaining days)
        
        tenant.subscription_plan = SubscriptionPlan.PRO  # type: ignore
        await session.commit()
        
        return {
            "status": "success",
            "message": "Upgraded to Pro plan!",
            "message_fa": "به پلن Pro ارتقا یافتید!",
            "plan": "pro"
        }


@router.get("/status/{tenant_id}")
async def get_subscription_status(tenant_id: int):
    """
    Get current subscription status for a tenant.
    """
    async with async_session() as session:
        result = await session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Check if trial expired
        is_trial_expired = False
        if tenant.trial_ends_at and tenant.subscription_status == SubscriptionStatus.TRIAL:  # type: ignore
            is_trial_expired = datetime.utcnow() > tenant.trial_ends_at  # type: ignore
        
        # Check if subscription expired
        is_subscription_expired = False
        if tenant.subscription_ends_at and tenant.subscription_status == SubscriptionStatus.ACTIVE:  # type: ignore
            is_subscription_expired = datetime.utcnow() > tenant.subscription_ends_at  # type: ignore
        
        plan_str = tenant.subscription_plan.value if tenant.subscription_plan else "free"  # type: ignore
        plan_info = PRICING.get(plan_str, PRICING["basic"])
        
        return {
            "tenant_id": tenant.id,
            "email": tenant.email,
            "plan": plan_str,
            "status": tenant.subscription_status.value if tenant.subscription_status else "trial",  # type: ignore
            "is_active": tenant.is_active,  # type: ignore
            "trial_ends_at": tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,  # type: ignore
            "subscription_starts_at": tenant.subscription_starts_at.isoformat() if tenant.subscription_starts_at else None,  # type: ignore
            "subscription_ends_at": tenant.subscription_ends_at.isoformat() if tenant.subscription_ends_at else None,  # type: ignore
            "next_payment_date": tenant.next_payment_date.isoformat() if tenant.next_payment_date else None,  # type: ignore
            "is_trial_expired": is_trial_expired,
            "is_subscription_expired": is_subscription_expired,
            "plan_info": plan_info
        }


@router.post("/cancel/{tenant_id}")
async def cancel_subscription(tenant_id: int):
    """
    Cancel tenant subscription.
    Access continues until end of billing period.
    """
    async with async_session() as session:
        result = await session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant.subscription_status = SubscriptionStatus.CANCELLED  # type: ignore
        await session.commit()
        
        return {
            "status": "cancelled",
            "message": "Subscription cancelled. Access continues until end of billing period.",
            "message_fa": "اشتراک لغو شد. دسترسی تا پایان دوره فعلی ادامه دارد.",
            "ends_at": tenant.subscription_ends_at.isoformat() if tenant.subscription_ends_at else None  # type: ignore
        }
