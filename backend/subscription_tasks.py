"""
Background Tasks for Subscription Management
Checks for trial expiry, sends reminders, handles auto-renewals
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, and_

from database import async_session, Tenant, SubscriptionStatus
from email_service import (
    send_trial_ending_email,
    send_trial_expired_email
)


async def check_trial_expiry():
    """
    Check for trials ending soon and send reminder emails
    Runs daily
    """
    print("[TRIAL CHECK] Checking for expiring trials...")
    
    async with async_session() as session:
        now = datetime.utcnow()
        three_days_from_now = now + timedelta(days=3)
        
        # Find trials ending in 3 days
        result = await session.execute(
            select(Tenant).where(
                and_(
                    Tenant.subscription_status == SubscriptionStatus.TRIAL,
                    Tenant.trial_ends_at <= three_days_from_now,
                    Tenant.trial_ends_at > now
                )
            )
        )
        
        expiring_soon = result.scalars().all()
        
        for tenant in expiring_soon:
            days_left = (tenant.trial_ends_at - now).days  # type: ignore
            
            if days_left <= 3 and days_left > 0:
                try:
                    await send_trial_ending_email(
                        name=tenant.name,  # type: ignore
                        email=tenant.email,  # type: ignore
                        plan=tenant.subscription_plan.value,  # type: ignore
                        days_left=days_left,
                        trial_ends_at=tenant.trial_ends_at  # type: ignore
                    )
                    print(f"[TRIAL REMINDER] Sent to {tenant.email} ({days_left} days left)")
                except Exception as e:
                    print(f"[TRIAL REMINDER ERROR] Failed for {tenant.email}: {e}")


async def expire_trials():
    """
    Mark expired trials as EXPIRED
    Runs daily
    """
    print("[TRIAL EXPIRY] Checking for expired trials...")
    
    async with async_session() as session:
        now = datetime.utcnow()
        
        # Find expired trials
        result = await session.execute(
            select(Tenant).where(
                and_(
                    Tenant.subscription_status == SubscriptionStatus.TRIAL,
                    Tenant.trial_ends_at <= now
                )
            )
        )
        
        expired_trials = result.scalars().all()
        
        for tenant in expired_trials:
            # Update status to EXPIRED
            tenant.subscription_status = SubscriptionStatus.EXPIRED  # type: ignore
            
            try:
                await send_trial_expired_email(
                    name=tenant.name,  # type: ignore
                    email=tenant.email,  # type: ignore
                    plan=tenant.subscription_plan.value  # type: ignore
                )
                print(f"[TRIAL EXPIRED] {tenant.email} marked as expired")
            except Exception as e:
                print(f"[TRIAL EXPIRED ERROR] Failed for {tenant.email}: {e}")
        
        if expired_trials:
            await session.commit()
            print(f"[TRIAL EXPIRY] Expired {len(expired_trials)} trials")


async def check_subscription_expiry():
    """
    Check for expiring paid subscriptions
    Runs daily
    """
    print("[SUBSCRIPTION CHECK] Checking for expiring subscriptions...")
    
    async with async_session() as session:
        now = datetime.utcnow()
        
        # Find expired subscriptions
        result = await session.execute(
            select(Tenant).where(
                and_(
                    Tenant.subscription_status == SubscriptionStatus.ACTIVE,
                    Tenant.subscription_ends_at <= now
                )
            )
        )
        
        expired_subscriptions = result.scalars().all()
        
        for tenant in expired_subscriptions:
            # Mark as EXPIRED (user needs to renew)
            tenant.subscription_status = SubscriptionStatus.EXPIRED  # type: ignore
            print(f"[SUBSCRIPTION EXPIRED] {tenant.email}")
        
        if expired_subscriptions:
            await session.commit()
            print(f"[SUBSCRIPTION EXPIRY] Expired {len(expired_subscriptions)} subscriptions")


async def subscription_background_tasks():
    """
    Run all subscription background tasks
    Should be scheduled to run daily (e.g., via APScheduler)
    """
    print("[BACKGROUND TASKS] Starting subscription checks...")
    
    try:
        await check_trial_expiry()
        await expire_trials()
        await check_subscription_expiry()
        print("[BACKGROUND TASKS] Completed successfully")
    except Exception as e:
        print(f"[BACKGROUND TASKS ERROR] {e}")


# ==================== SCHEDULER SETUP ====================

def schedule_subscription_tasks(scheduler):
    """
    Add subscription tasks to APScheduler
    
    Args:
        scheduler: AsyncIOScheduler instance from main.py
    """
    
    # Run daily at 9 AM
    scheduler.add_job(
        subscription_background_tasks,
        'cron',
        hour=9,
        minute=0,
        id='subscription_tasks',
        replace_existing=True
    )
    
    print("[SCHEDULER] Subscription tasks scheduled (daily at 9 AM)")


if __name__ == "__main__":
    # For testing
    asyncio.run(subscription_background_tasks())
