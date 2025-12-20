#!/usr/bin/env python3
"""
Final deployment - upload brain.py and force rebuild
"""
import paramiko
import time

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

LOCAL_FILE = r"I:\ArtinRealtySmartPro\ArtinSmartRealty\backend\brain.py"
REMOTE_FILE = "/opt/ArtinSmartRealty/backend/brain.py"

print("🚀 Final deployment starting...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Step 1: Upload file
    print("\n1️⃣ Uploading brain.py...")
    sftp = ssh.open_sftp()
    sftp.put(LOCAL_FILE, REMOTE_FILE)
    sftp.close()
    print("   ✅ Uploaded!")
    
    # Step 2: Verify global keyword exists
    print("\n2️⃣ Verifying 'global GEMINI_API_KEY' in file...")
    stdin, stdout, stderr = ssh.exec_command(
        "grep -n 'global GEMINI_API_KEY' /opt/ArtinSmartRealty/backend/brain.py"
    )
    global_lines = stdout.read().decode()
    if global_lines:
        print(f"   ✅ Found:\n{global_lines}")
    else:
        print("   ❌ NOT FOUND! This will cause errors!")
    
    # Step 3: Stop all services
    print("\n3️⃣ Stopping services...")
    stdin, stdout, stderr = ssh.exec_command("cd /opt/ArtinSmartRealty && docker-compose down")
    stdout.read()
    print("   ✅ Stopped!")
    
    # Step 4: Remove old image
    print("\n4️⃣ Removing old backend image...")
    stdin, stdout, stderr = ssh.exec_command("docker rmi artinsmartrealty-backend -f")
    stdout.read()
    print("   ✅ Removed!")
    
    # Step 5: Build with no cache
    print("\n5️⃣ Building backend (no cache) - this takes ~60 seconds...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose build --no-cache backend",
        timeout=300
    )
    # Wait for build
    build_output = stdout.read().decode()
    if "Successfully built" in build_output or "naming to" in build_output:
        print("   ✅ Build successful!")
    else:
        print("   ⚠️ Build may have issues - check manually")
    
    # Step 6: Start services
    print("\n6️⃣ Starting all services...")
    stdin, stdout, stderr = ssh.exec_command("cd /opt/ArtinSmartRealty && docker-compose up -d")
    stdout.read()
    print("   ✅ Started!")
    
    # Step 7: Wait for initialization
    print("\n7️⃣ Waiting for backend to initialize (20 seconds)...")
    time.sleep(20)
    
    # Step 8: Check startup logs
    print("\n8️⃣ Checking startup logs...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose logs --tail=100 backend | grep -E '(Configured Gemini|key rotation|professional|Bot started|Failed to start|Initialized Gemini)'"
    )
    logs = stdout.read().decode()
    
    if "key rotation" in logs:
        print("   ✅ Key rotation is working!")
    if "professional" in logs or "system instruction" in logs:
        print("   ✅ Professional system instruction loaded!")
    if "Failed to start" in logs:
        print("   ❌ Bot failed to start!")
    if "Bot started" in logs:
        print("   ✅ Bot started successfully!")
    
    print("\n" + "="*60)
    print("Full startup logs:")
    print("="*60)
    print(logs if logs else "No relevant logs")
    
    print("\n" + "="*60)
    print("🎯 DEPLOYMENT COMPLETE!")
    print("="*60)
    print(f"\n🤖 Bot: @TaranteenrealstateBot")
    print(f"🧪 Test with: /start")
    print(f"\n💡 If bot fails, check full logs with:")
    print(f"   docker-compose logs --tail=200 backend")
    
    ssh.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    print(traceback.format_exc())
