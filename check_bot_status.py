#!/usr/bin/env python3
"""
Check if Telegram bot is actually running
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🤖 Checking Telegram bot status...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Check if bot is mentioned in startup logs
    print("1️⃣ Searching for bot startup in logs:")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose logs backend | grep -E '(Bot started|telegram|Telegram bot)' | tail -20"
    )
    
    logs = stdout.read().decode()
    if logs:
        print(logs)
    else:
        print("❌ No bot startup logs found!")
    
    # Check Python processes
    print("\n2️⃣ Checking Python processes in container:")
    stdin, stdout, stderr = ssh.exec_command(
        "docker exec artinrealty-backend ps aux | grep -E '(python|uvicorn)'"
    )
    print(stdout.read().decode())
    
    # Check if Telegram webhook is set
    print("\n3️⃣ Checking Telegram bot configuration:")
    stdin, stdout, stderr = ssh.exec_command(
        """docker exec artinrealty-backend python3 -c "
import asyncio
from database import async_session, select, Tenant

async def check():
    async with async_session() as session:
        result = await session.execute(
            select(Tenant).where(Tenant.telegram_bot_token.isnot(None))
        )
        tenants = result.scalars().all()
        for t in tenants:
            print(f'Tenant: {t.name}')
            print(f'  Bot token: {t.telegram_bot_token[:20]}...')
            print(f'  Active: {t.is_active}')

asyncio.run(check())
"
"""
    )
    print(stdout.read().decode())
    
    # Most importantly: trigger a test message manually
    print("\n4️⃣ Triggering a test with /start command:")
    print("    Please send /start to the bot NOW and check logs...")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
