"""
Verify Deployment - Live Server Check
"""
import paramiko

SSH_HOST = "srv1203549.hstgr.cloud"
SSH_USER = "root"
SSH_PASSWORD = "u0;74KWyoEydh5g.Q9)s"

def check_deployment():
    print("🔍 Checking LIVE server status...\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASSWORD)
    
    # Check 1: Is backend running?
    print("1️⃣ Checking backend container status...")
    stdin, stdout, stderr = ssh.exec_command("cd /opt/ArtinSmartRealty && docker-compose ps backend")
    output = stdout.read().decode('utf-8')
    if "Up" in output:
        print("   ✅ Backend container is UP and RUNNING\n")
    else:
        print("   ❌ Backend container is NOT running!\n")
    
    # Check 2: Recent logs (last 50 lines)
    print("2️⃣ Checking recent logs for errors...")
    stdin, stdout, stderr = ssh.exec_command("cd /opt/ArtinSmartRealty && docker-compose logs --tail=50 backend")
    logs = stdout.read().decode('utf-8')
    
    # Check for success indicators
    if "Bot started for tenant" in logs:
        print("   ✅ Bot initialized successfully")
    if "Background scheduler started" in logs:
        print("   ✅ Background tasks running")
    if "Gemini API" in logs:
        print("   ✅ Gemini API connected")
    
    # Check for Ghost Protocol error
    if "astext" in logs:
        print("   ❌ Ghost Protocol bug STILL EXISTS!")
    else:
        print("   ✅ No 'astext' error found")
    
    # Check for recent errors
    error_lines = [line for line in logs.split('\n') if 'ERROR' in line or 'Exception' in line]
    if error_lines:
        print(f"\n   ⚠️ Found {len(error_lines)} error lines:")
        for line in error_lines[-3:]:  # Show last 3 errors
            print(f"     {line[:100]}")
    else:
        print("   ✅ No errors in recent logs")
    
    # Check 3: Verify files on server
    print("\n3️⃣ Checking file timestamps on server...")
    stdin, stdout, stderr = ssh.exec_command("ls -lh /opt/ArtinSmartRealty/backend/brain.py /opt/ArtinSmartRealty/backend/telegram_bot.py")
    output = stdout.read().decode('utf-8')
    print(output)
    
    # Check 4: Check if smart extraction code exists
    print("4️⃣ Verifying smart extraction code exists...")
    stdin, stdout, stderr = ssh.exec_command("grep -c 'extract_user_info_smart' /opt/ArtinSmartRealty/backend/brain.py")
    count = stdout.read().decode('utf-8').strip()
    if int(count) > 0:
        print(f"   ✅ Smart extraction function found ({count} occurrences)\n")
    else:
        print("   ❌ Smart extraction NOT found!\n")
    
    # Check 5: Check if goal_buttons exists
    print("5️⃣ Verifying goal buttons code exists...")
    stdin, stdout, stderr = ssh.exec_command("grep -c 'goal_buttons' /opt/ArtinSmartRealty/backend/brain.py")
    count = stdout.read().decode('utf-8').strip()
    if int(count) > 0:
        print(f"   ✅ Goal buttons found ({count} occurrences)\n")
    else:
        print("   ❌ Goal buttons NOT found!\n")
    
    # Check 6: Check if Ghost Protocol fix exists
    print("6️⃣ Verifying Ghost Protocol fix...")
    stdin, stdout, stderr = ssh.exec_command("grep -c \".op('?')\" /opt/ArtinSmartRealty/backend/telegram_bot.py")
    count = stdout.read().decode('utf-8').strip()
    if int(count) > 0:
        print(f"   ✅ Ghost Protocol fix found (JSONB operator)\n")
    else:
        print("   ⚠️ Ghost Protocol fix NOT found - checking old syntax...")
        stdin, stdout, stderr = ssh.exec_command("grep -c 'astext' /opt/ArtinSmartRealty/backend/telegram_bot.py")
        old_count = stdout.read().decode('utf-8').strip()
        if int(old_count) > 0:
            print(f"   ❌ Old buggy code STILL EXISTS ({old_count} occurrences)\n")
    
    print("\n" + "="*60)
    print("📊 VERDICT:")
    print("="*60)
    
    # Final check - test with actual bot interaction
    print("\n🤖 To CONFIRM functionality, test with bot:")
    print("   1. Open Telegram: @TaranteenrealstateBot")
    print("   2. Send: /start")
    print("   3. Send message with name+phone:")
    print("      'سلام من ارزو هستم، شماره‌م 09177105840'")
    print("   4. Should see GOAL BUTTONS appear!")
    
    ssh.close()

if __name__ == "__main__":
    check_deployment()
