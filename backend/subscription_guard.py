"""
Feature Access Control Middleware
Controls feature access based on subscription plan
"""

from fastapi import HTTPException
from typing import Optional
from datetime import datetime

from backend.database import Tenant, SubscriptionPlan, SubscriptionStatus


# Feature to Plan mapping
FEATURE_ACCESS = {
    "linkedin_scraper": [SubscriptionPlan.PRO],  # Only Pro
    "lead_generation": [SubscriptionPlan.PRO],  # Only Pro
    "bot": [SubscriptionPlan.BASIC, SubscriptionPlan.PRO],  # Both
    "followup": [SubscriptionPlan.BASIC, SubscriptionPlan.PRO],  # Both
    "whatsapp": [SubscriptionPlan.BASIC, SubscriptionPlan.PRO],  # Both
    "telegram": [SubscriptionPlan.BASIC, SubscriptionPlan.PRO],  # Both
    "analytics": [SubscriptionPlan.BASIC, SubscriptionPlan.PRO],  # Both
    "advanced_analytics": [SubscriptionPlan.PRO],  # Only Pro
    "crm_export": [SubscriptionPlan.PRO],  # Only Pro
    "white_label": [SubscriptionPlan.PRO],  # Only Pro
}


def check_subscription_active(tenant: Tenant) -> bool:
    """Check if tenant's subscription is active"""
    # Trial period
    if tenant.subscription_status == SubscriptionStatus.TRIAL:  # type: ignore
        if tenant.trial_ends_at:  # type: ignore
            return datetime.utcnow() < tenant.trial_ends_at  # type: ignore
        return True
    
    # Active subscription
    if tenant.subscription_status == SubscriptionStatus.ACTIVE:  # type: ignore
        if tenant.subscription_ends_at:  # type: ignore
            return datetime.utcnow() < tenant.subscription_ends_at  # type: ignore
        return True
    
    # Cancelled but still in valid period
    if tenant.subscription_status == SubscriptionStatus.CANCELLED:  # type: ignore
        if tenant.subscription_ends_at:  # type: ignore
            return datetime.utcnow() < tenant.subscription_ends_at  # type: ignore
    
    return False


def check_feature_access(tenant: Tenant, feature: str) -> bool:
    """
    Check if tenant has access to a specific feature.
    Returns True if tenant can use the feature, False otherwise.
    """
    # Check if subscription is active
    if not check_subscription_active(tenant):
        return False
    
    # Check if feature exists in access control
    if feature not in FEATURE_ACCESS:
        return True  # Unknown features are allowed by default
    
    # Check if tenant's plan allows this feature
    allowed_plans = FEATURE_ACCESS[feature]
    return tenant.subscription_plan in allowed_plans  # type: ignore


def require_feature(feature: str):
    """
    Decorator to require specific feature access.
    Usage:
        @require_feature("linkedin_scraper")
        async def scrape_linkedin(...):
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract tenant from kwargs or function call
            tenant = kwargs.get("tenant") or kwargs.get("current_tenant")
            
            if not tenant:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            # Check subscription active
            if not check_subscription_active(tenant):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "subscription_expired",
                        "message": "Your subscription has expired. Please renew to continue.",
                        "message_fa": "اشتراک شما منقضی شده است. لطفا برای ادامه تمدید کنید."
                    }
                )
            
            # Check feature access
            if not check_feature_access(tenant, feature):
                # Get required plan
                required_plans = FEATURE_ACCESS.get(feature, [])
                plan_names = [p.value for p in required_plans]
                
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "upgrade_required",
                        "feature": feature,
                        "required_plans": plan_names,
                        "current_plan": tenant.subscription_plan.value if tenant.subscription_plan else "free",  # type: ignore
                        "message": f"This feature requires {' or '.join(plan_names)} plan. Please upgrade.",
                        "message_fa": f"این امکان نیاز به پلن {' یا '.join(plan_names)} دارد. لطفا ارتقا دهید."
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_plan_limits(tenant: Tenant) -> dict:
    """Get usage limits for tenant's plan"""
    plan = tenant.subscription_plan.value if tenant.subscription_plan else "free"  # type: ignore
    
    if plan == "basic":
        return {
            "max_leads": 1000,
            "max_messages_per_month": 10000,
            "max_bot_instances": 2,
            "max_followup_campaigns": 10,
            "linkedin_scraper": False,
            "advanced_analytics": False
        }
    elif plan == "pro":
        return {
            "max_leads": 10000,
            "max_messages_per_month": 100000,
            "max_bot_instances": 10,
            "max_followup_campaigns": 100,
            "linkedin_scraper": True,
            "advanced_analytics": True
        }
    else:  # free/trial
        return {
            "max_leads": 100,
            "max_messages_per_month": 1000,
            "max_bot_instances": 1,
            "max_followup_campaigns": 3,
            "linkedin_scraper": False,
            "advanced_analytics": False
        }


async def check_usage_limit(tenant: Tenant, resource_type: str, current_count: int) -> bool:
    """
    Check if tenant has reached usage limit for a resource.
    Returns True if within limit, False if exceeded.
    """
    limits = get_plan_limits(tenant)
    
    if resource_type == "leads":
        return current_count < limits["max_leads"]
    elif resource_type == "messages":
        return current_count < limits["max_messages_per_month"]
    elif resource_type == "bots":
        return current_count < limits["max_bot_instances"]
    elif resource_type == "campaigns":
        return current_count < limits["max_followup_campaigns"]
    
    return True  # Unknown resource types are allowed
