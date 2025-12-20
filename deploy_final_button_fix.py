#!/usr/bin/env python3
"""
🚀 Final Button Fix Deployment Script
Fixes the WARMUP state to show goal buttons when phone extracted but goal missing

BUG FOUND:
- Line 3435 brain.py was returning buttons=[] in WARMUP state
- This violated user requirement: "show buttons as backup for lazy/confused users"
- Smart extraction worked but buttons didn't appear when asking for goal

FIX APPLIED:
- Added goal buttons to WARMUP state clarification message (line 3435)
- Now shows 3 buttons: خرید خانه | سرمایه‌گذاری | اقامت طلایی
- User can EITHER type naturally OR click buttons
"""

import paramiko
import time
from pathlib import Path

# Server credentials
HOST = "srv1203549.hstgr.cloud"
USER = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"
PROJECT_PATH = "/opt/ArtinSmartRealty"

def deploy():
    print("🚀 FINAL BUTTON FIX DEPLOYMENT\n")
    print("=" * 60)
    
    # Connect to server
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"📡 Connecting to {HOST}...")
    ssh.connect(HOST, username=USER, password=PASSWORD)
    print("✅ Connected!\n")
    
    # Upload fixed brain.py
    sftp = ssh.open_sftp()
    local_file = Path(__file__).parent / "ArtinSmartRealty" / "backend" / "brain.py"
    remote_file = f"{PROJECT_PATH}/backend/brain.py"
    
    print(f"📤 Uploading brain.py...")
    sftp.put(str(local_file), remote_file)
    file_size = local_file.stat().st_size / 1024  # KB
    print(f"✅ Uploaded brain.py ({file_size:.0f}KB)\n")
    sftp.close()
    
    # Restart backend container
    print("🔄 Restarting backend container...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {PROJECT_PATH} && docker-compose restart backend")
    stdout.channel.recv_exit_status()  # Wait for command
    time.sleep(3)
    print("✅ Backend restarted\n")
    
    # Verify logs
    print("🔍 Checking startup logs...")
    stdin, stdout, stderr = ssh.exec_command(
        f"cd {PROJECT_PATH} && docker-compose logs --tail=30 backend | grep -E '(Started|Error|WARNING)'"
    )
    logs = stdout.read().decode()
    print(logs)
    
    # Check for specific fix verification
    print("\n🔍 Verifying fix in code...")
    stdin, stdout, stderr = ssh.exec_command(
        f"grep -n 'buttons=goal_buttons.*# ✅ Show buttons as backup!' {PROJECT_PATH}/backend/brain.py"
    )
    verification = stdout.read().decode()
    
    if verification:
        print("✅ Fix verified in code:")
        print(verification)
    else:
        print("⚠️ Warning: Verification pattern not found (file may have different formatting)")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT COMPLETE")
    print("=" * 60)
    print("\n🧪 TEST PLAN:")
    print("1. Open Telegram: @TaranteenrealstateBot")
    print("2. Send: /start")
    print("3. Send: سلام من ارزو هستم، شماره‌م 09177105840")
    print("")
    print("✅ EXPECTED BEHAVIOR:")
    print("   - Bot extracts: name='ارزو', phone='+989177105840'")
    print("   - Bot responds: 'عالی! اطلاعات تماست رو دارم ✅'")
    print("   - Bot asks: 'حالا، هدفت از املاک دبی چیه؟'")
    print("   - Bot shows 3 BUTTONS:")
    print("     🏡 خرید خانه")
    print("     💰 سرمایه‌گذاری")
    print("     🛂 اقامت طلایی")
    print("")
    print("👤 USER CAN NOW:")
    print("   • Click a button (easy) ✅")
    print("   • OR type 'میخوام سرمایه‌گذاری کنم' (flexible) ✅")
    print("")
    print("🐛 ROOT CAUSE:")
    print("   - brain.py line 3435 was returning buttons=[] in WARMUP state")
    print("   - This happened when smart extraction saved phone but no goal")
    print("   - Bot asked for goal but showed NO buttons")
    print("")
    print("✨ FIX:")
    print("   - Added goal_buttons to WARMUP clarification message")
    print("   - Now shows buttons as backup for lazy/confused users")
    print("   - Maintains conversational intelligence while being user-friendly")

if __name__ == "__main__":
    deploy()
