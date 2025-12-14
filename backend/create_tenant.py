#!/usr/bin/env python3
"""
Create a tenant for ArtinSmartRealty
Run with: python create_tenant.py
"""

import asyncio
import sys
from database import async_session, Tenant
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_tenant():
    """Create the first tenant"""
    
    # Get bot token from environment or user input
    import os
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment")
        print("Please provide your Telegram bot token:")
        bot_token = input("Bot Token: ").strip()
    
    if not bot_token:
        print("❌ No bot token provided. Exiting.")
        sys.exit(1)
    
    async with async_session() as db:
        # Check if tenant already exists
        result = await db.execute(
            "SELECT id FROM tenants WHERE telegram_bot_token = :token",
            {"token": bot_token}
        )
        existing = result.first()
        
        if existing:
            print(f"✅ Tenant already exists with ID: {existing[0]}")
            return
        
        # Create new tenant
        tenant = Tenant(
            name="ArtinSmartRealty",
            company_name="Artin Smart Realty",
            telegram_bot_token=bot_token,
            email="admin@artinsmartrealty.com",
            password_hash=pwd_context.hash("admin123"),  # Change this!
            is_active=True,
            default_language="en",
            timezone="Asia/Dubai",
            subscription_status="ACTIVE"
        )
        
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        
        print(f"✅ Tenant created successfully!")
        print(f"   ID: {tenant.id}")
        print(f"   Name: {tenant.name}")
        print(f"   Bot Token: {bot_token[:20]}...")
        print(f"   Email: {tenant.email}")
        print(f"\n🔐 Default admin password: admin123 (CHANGE THIS!)")


if __name__ == "__main__":
    asyncio.run(create_tenant())
