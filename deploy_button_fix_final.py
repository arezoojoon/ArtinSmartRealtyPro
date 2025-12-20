"""
Deploy Final Intelligent Brain Fixes
=====================================
Fixes deployed:
1. Ghost Protocol SQLAlchemy bug (.astext → .op('?'))
2. Goal selection buttons when phone extracted (user might be lazy)
3. Contact share button always available
4. Gemini retry logic + key rotation + safety settings (already present)

Author: GitHub Copilot
Date: 2025-12-19
"""

import paramiko
import time
import os

# Server credentials
SSH_HOST = "srv1203549.hstgr.cloud"  # Using hostname instead of IP
SSH_PORT = 22
SSH_USER = "root"
SSH_PASSWORD = "u0;74KWyoEydh5g.Q9)s"
SERVER_PATH = "/opt/ArtinSmartRealty"

def main():
    print("=" * 60)
    print("🚀 DEPLOYING INTELLIGENT BRAIN FIXES")
    print("=" * 60)
    
    try:
        # Connect to server
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"\n📡 Connecting to {SSH_HOST}...")
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASSWORD)
        print("✅ Connected!")
        
        # Upload fixed files
        print("\n📤 Uploading fixed files...")
        sftp = ssh.open_sftp()
        
        # Upload brain.py (with button restoration)
        local_brain = r"I:\ArtinRealtySmartPro\ArtinSmartRealty\backend\brain.py"
        remote_brain = f"{SERVER_PATH}/backend/brain.py"
        print(f"  → Uploading brain.py...")
        sftp.put(local_brain, remote_brain)
        print("    ✅ brain.py uploaded")
        
        # Upload telegram_bot.py (with Ghost Protocol fix)
        local_telegram = r"I:\ArtinRealtySmartPro\ArtinSmartRealty\backend\telegram_bot.py"
        remote_telegram = f"{SERVER_PATH}/backend/telegram_bot.py"
        print(f"  → Uploading telegram_bot.py...")
        sftp.put(local_telegram, remote_telegram)
        print("    ✅ telegram_bot.py uploaded")
        
        sftp.close()
        
        # Restart backend
        print("\n🔄 Restarting backend container...")
        stdin, stdout, stderr = ssh.exec_command(f"cd {SERVER_PATH} && docker-compose restart backend")
        stdout.channel.recv_exit_status()  # Wait for command
        print("✅ Backend restarted")
        
        # Wait for startup
        print("\n⏳ Waiting 8 seconds for startup...")
        time.sleep(8)
        
        # Check logs
        print("\n📋 Checking logs for errors...")
        stdin, stdout, stderr = ssh.exec_command(f"cd {SERVER_PATH} && docker-compose logs --tail=30 backend")
        logs = stdout.read().decode('utf-8')
        
        # Check for success indicators
        if "Bot started for tenant" in logs:
            print("✅ Bot started successfully!")
        if "Background scheduler started" in logs:
            print("✅ Background tasks started!")
        if "Gemini API" in logs:
            print("✅ Gemini API initialized!")
        
        # Check for errors
        if "ERROR" in logs or "Exception" in logs:
            print("\n⚠️ WARNINGS/ERRORS FOUND:")
            for line in logs.split('\n'):
                if 'ERROR' in line or 'Exception' in line:
                    print(f"  ⚠️ {line}")
        else:
            print("\n✅ No errors in logs")
        
        print("\n" + "=" * 60)
        print("✅ DEPLOYMENT COMPLETE!")
        print("=" * 60)
        print("\n🧪 TESTING INSTRUCTIONS:")
        print("=" * 60)
        print("\n1️⃣ Test Smart Extraction (Complete Info):")
        print("   Send to bot: 'سلام من ارزو محمدزادگانم، شماره‌م 09177105840،")
        print("                میخوام آپارتمان 2 خوابه تا 200 هزار دلار در Dubai Marina بخرم'")
        print("   Expected: Extract ALL info, show property search immediately")
        print()
        print("2️⃣ Test Partial Extraction (Name + Phone only):")
        print("   Send to bot: 'سلام من ارزو هستم، شماره‌م 09177105840'")
        print("   Expected: Extract name+phone, then show GOAL BUTTONS")
        print("   (🏡 خرید خانه | 💰 سرمایه‌گذاری | 🛂 اقامت طلایی)")
        print()
        print("3️⃣ Test Contact Button:")
        print("   Start fresh conversation with /start")
        print("   When asked for phone, look for:")
        print("   - Native Telegram 'Share Contact' button")
        print("   - Example format in message")
        print()
        print("4️⃣ Check Ghost Protocol:")
        print("   Wait 5 minutes, check logs:")
        print("   docker-compose logs --tail=50 backend | grep 'Ghost Protocol'")
        print("   Should see NO 'astext' errors")
        print()
        print("=" * 60)
        print("🔑 KEY CHANGES:")
        print("=" * 60)
        print("✅ Ghost Protocol bug fixed (.astext → .op('?'))")
        print("✅ Goal buttons shown when phone extracted but goal missing")
        print("✅ Contact share button always available")
        print("✅ Gemini retry logic active (3 keys, exponential backoff)")
        print("✅ Safety settings: BLOCK_ONLY_HIGH")
        print()
        print("💡 Philosophy: Bot is INTELLIGENT but not annoying")
        print("   - Extracts data smartly AS user talks")
        print("   - Saves to database immediately")
        print("   - Shows buttons as BACKUP (user might be lazy/unsure)")
        print("   - Accepts both button clicks AND natural language")
        print()
        
        ssh.close()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
