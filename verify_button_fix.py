#!/usr/bin/env python3
"""
🔍 Verify Final Button Fix on Production Server
Checks if goal buttons now appear in WARMUP state
"""

import paramiko

HOST = "srv1203549.hstgr.cloud"
USER = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"
PROJECT_PATH = "/opt/ArtinSmartRealty"

print("🔍 VERIFYING FINAL BUTTON FIX ON PRODUCTION\n")
print("=" * 70)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

print("1️⃣ Checking backend container status...")
stdin, stdout, stderr = ssh.exec_command(
    f"cd {PROJECT_PATH} && docker-compose ps backend | grep artinrealty-backend"
)
status = stdout.read().decode()
if "Up" in status:
    print("   ✅ Backend container is UP and RUNNING\n")
else:
    print("   ⚠️ Backend container status unknown:")
    print(status)

print("2️⃣ Checking for the specific fix in code...")
stdin, stdout, stderr = ssh.exec_command(
    f"grep -A 3 'buttons=goal_buttons.*# ✅ Show buttons as backup!' {PROJECT_PATH}/backend/brain.py"
)
fix_code = stdout.read().decode()

if "buttons=goal_buttons" in fix_code:
    print("   ✅ Fix code found in brain.py")
    print("   " + fix_code.replace("\n", "\n   "))
else:
    print("   ⚠️ Fix pattern not found - checking alternate pattern...")
    stdin, stdout, stderr = ssh.exec_command(
        f"grep -B 2 -A 2 'buttons=goal_buttons' {PROJECT_PATH}/backend/brain.py | tail -15"
    )
    alt_code = stdout.read().decode()
    print(alt_code)

print("\n3️⃣ Checking recent logs for errors...")
stdin, stdout, stderr = ssh.exec_command(
    f"cd {PROJECT_PATH} && docker-compose logs --tail=50 backend | grep -E '(ERROR|Exception|Traceback)'"
)
errors = stdout.read().decode().strip()

if errors:
    print("   ⚠️ Errors found in logs:")
    print(errors)
else:
    print("   ✅ No errors in recent logs\n")

print("4️⃣ Checking file timestamp...")
stdin, stdout, stderr = ssh.exec_command(
    f"ls -lh {PROJECT_PATH}/backend/brain.py | awk '{{print $6, $7, $8, $9}}'"
)
timestamp = stdout.read().decode().strip()
print(f"   📅 brain.py: {timestamp}\n")

print("5️⃣ Counting goal button occurrences...")
stdin, stdout, stderr = ssh.exec_command(
    f"grep -c 'goal_buttons = \\[' {PROJECT_PATH}/backend/brain.py"
)
count = stdout.read().decode().strip()
print(f"   📊 Goal button definitions found: {count} occurrences\n")

ssh.close()

print("=" * 70)
print("📊 VERIFICATION COMPLETE")
print("=" * 70)
print("\n🧪 NEXT STEP: Test with bot")
print("Send to @TaranteenrealstateBot:")
print("   'سلام من ارزو هستم، شماره‌م 09177105840'")
print("")
print("Expected: See 3 goal buttons (🏡 خرید خانه | 💰 سرمایه‌گذاری | 🛂 اقامت طلایی)")
