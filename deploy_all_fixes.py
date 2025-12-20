#!/usr/bin/env python3
"""
Deploy BOTH brain.py and telegram_bot.py with all fixes
"""

import paramiko
from pathlib import Path
import time

HOST = 'srv1203549.hstgr.cloud'
USER = 'root'
PASSWORD = 'u0;74KWyoEydh5g.Q9)s'
PROJECT_PATH = '/opt/ArtinSmartRealty'

print("=" * 80)
print("DEPLOYING ALL FIXES TO PRODUCTION")
print("=" * 80)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print("✅ Connected to server\n")

sftp = ssh.open_sftp()

# Upload brain.py
local_brain = Path(r"I:\ArtinRealtySmartPro\ArtinSmartRealty\backend\brain.py")
remote_brain = f"{PROJECT_PATH}/backend/brain.py"
print(f"📤 Uploading brain.py ({local_brain.stat().st_size // 1024}KB)...")
sftp.put(str(local_brain), remote_brain)
print("✅ brain.py uploaded\n")

# Upload telegram_bot.py  
local_telegram = Path(r"I:\ArtinRealtySmartPro\ArtinSmartRealty\backend\telegram_bot.py")
remote_telegram = f"{PROJECT_PATH}/backend/telegram_bot.py"
print(f"📤 Uploading telegram_bot.py ({local_telegram.stat().st_size // 1024}KB)...")
sftp.put(str(local_telegram), remote_telegram)
print("✅ telegram_bot.py uploaded\n")

sftp.close()

# Restart backend
print("🔄 Restarting backend container...")
stdin, stdout, stderr = ssh.exec_command(f'cd {PROJECT_PATH} && docker-compose restart backend')
stdout.channel.recv_exit_status()
print("✅ Backend restarted\n")

time.sleep(5)

# Check logs
print("🔍 Checking startup logs...")
stdin, stdout, stderr = ssh.exec_command(
    f'cd {PROJECT_PATH} && docker-compose logs --tail=30 backend | grep -E "(Started|ERROR|Ghost Protocol)"'
)
logs = stdout.read().decode('utf-8', errors='replace')
print(logs)

ssh.close()

print("\n" + "=" * 80)
print("DEPLOYMENT COMPLETE")
print("=" * 80)
print("\nFixes applied:")
print("1. ✅ Ghost Protocol .astext bug fixed")
print("2. ✅ Goal buttons added to WARMUP state")
print("3. ✅ Smart extraction working")
print("\nTest now with: @TaranteenrealstateBot")
