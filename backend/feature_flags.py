"""
Feature Flags System
Centralized feature access control for multi-tenant platform
"""

from sqlalchemy import select
from database import async_session, TenantFeature, FeatureFlag
from typing import Optional


async def has_feature(tenant_id: int, feature: FeatureFlag) -> bool:
    """
    Check if a tenant has access to a specific feature.
    
    Args:
        tenant_id: The tenant ID
        feature: The feature to check
    
    Returns:
        True if feature is enabled, False otherwise
    """
    async with async_session() as session:
        result = await session.execute(
            select(TenantFeature).where(
                TenantFeature.tenant_id == tenant_id,
                TenantFeature.feature == feature,
                TenantFeature.is_enabled == True
            )
        )
        tenant_feature = result.scalar_one_or_none()
        return tenant_feature is not None


async def require_feature(tenant_id: int, feature: FeatureFlag, error_message: Optional[str] = None):
    """
    Require a feature to be enabled, raise exception if not.
    
    Args:
        tenant_id: The tenant ID
        feature: The feature to check
        error_message: Custom error message (optional)
    
    Raises:
        HTTPException: If feature is not enabled
    """
    from fastapi import HTTPException
    
    if not await has_feature(tenant_id, feature):
        message = error_message or f"This feature requires '{feature.value}' to be enabled. Please contact support."
        raise HTTPException(status_code=403, detail=message)


async def get_enabled_features(tenant_id: int) -> list[FeatureFlag]:
    """
    Get list of all enabled features for a tenant.
    
    Args:
        tenant_id: The tenant ID
    
    Returns:
        List of enabled FeatureFlag enums
    """
    async with async_session() as session:
        result = await session.execute(
            select(TenantFeature).where(
                TenantFeature.tenant_id == tenant_id,
                TenantFeature.is_enabled == True
            )
        )
        features = result.scalars().all()
        return [f.feature for f in features]


# Usage Examples:
"""
# In your endpoint:
from feature_flags import has_feature, require_feature
from database import FeatureFlag

# Check if feature is enabled
if await has_feature(tenant_id, FeatureFlag.RAG_SYSTEM):
    # Use RAG system
    pass

# Require feature (raises exception if not enabled)
await require_feature(tenant_id, FeatureFlag.VOICE_AI)

# Get all enabled features
features = await get_enabled_features(tenant_id)
"""
