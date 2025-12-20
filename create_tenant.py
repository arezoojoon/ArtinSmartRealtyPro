#!/usr/bin/env python3
"""
Create Hamidreza Damroodi tenant in database
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

# Hamidreza's bot token (از لاگ‌های قبلی)
BOT_TOKEN = "7750551672:AAHaVtzQAo0WqAZ8YqFJLp2IldXq2MNDkSs"

print("👤 Creating Hamidreza Damroodi tenant...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Create tenant via Python script in container
    create_script = f"""
import asyncio
import sys
sys.path.insert(0, '/app')
from database import async_session, Tenant
from auth import hash_password
from datetime import datetime, timedelta

async def create_tenant():
    async with async_session() as session:
        # Check if already exists
        from sqlalchemy import select
        result = await session.execute(
            select(Tenant).where(Tenant.email == 'hamidreza@example.com')
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f'✅ Tenant already exists: {{existing.name}}')
            return
        
        # Create new tenant
        tenant = Tenant(
            name='Hamidreza Damroodi',
            email='hamidreza@example.com',
            password_hash=hash_password('ArtinRealty2024!'),
            company_name='Hamidreza Damroodi Real Estate',
            phone='+971501234567',
            telegram_bot_token='{BOT_TOKEN}',
            is_active=True,
            subscription_plan='professional',
            subscription_status='active',
            trial_ends_at=datetime.now() + timedelta(days=30),
            default_language='fa'
        )
        
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
        
        print(f'✅ Created tenant: {{tenant.name}} (ID: {{tenant.id}})')
        print(f'   Email: {{tenant.email}}')
        print(f'   Bot token: {{tenant.telegram_bot_token[:20]}}...')
        print(f'   Active: {{tenant.is_active}}')

asyncio.run(create_tenant())
"""
    
    # Write script to file
    stdin, stdout, stderr = ssh.exec_command(
        f"docker exec artinrealty-backend python3 -c '{create_script}'"
    )
    
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if output:
        print(output)
    if error and 'warning' not in error.lower():
        print(f"⚠️ Error: {error}")
    
    # Verify creation
    print("\n🔍 Verifying tenant creation:")
    stdin, stdout, stderr = ssh.exec_command(
        """docker exec artinrealty-db psql -U postgres -d artinrealty -c "SELECT id, name, email, is_active FROM tenants;" """
    )
    print(stdout.read().decode())
    
    # Restart backend to initialize bot
    print("\n🔄 Restarting backend to initialize Telegram bot...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose restart backend"
    )
    output = stdout.read().decode()
    if output:
        print(output)
    
    print("\n✅ Done! Now bot should work. Send /start to test!")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
