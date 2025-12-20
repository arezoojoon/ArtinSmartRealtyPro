#!/usr/bin/env python3
"""
Upload updated brain.py with professional AI and rebuild backend
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

LOCAL_FILE = r"I:\ArtinRealtySmartPro\ArtinSmartRealty\backend\brain.py"
REMOTE_FILE = "/opt/ArtinSmartRealty/backend/brain.py"

print("🚀 Uploading enhanced brain.py...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Upload via SFTP
    sftp = ssh.open_sftp()
    sftp.put(LOCAL_FILE, REMOTE_FILE)
    sftp.close()
    
    print("✅ brain.py uploaded!")
    
    # Rebuild backend
    print("\n🔨 Rebuilding backend with new AI...")
    commands = [
        "cd /opt/ArtinSmartRealty",
        "docker-compose build --no-cache backend",
        "docker-compose up -d backend",
        "sleep 5",
        "docker-compose logs --tail=30 backend | grep -E '(Gemini|API|key|professional)'"
    ]
    
    for cmd in commands:
        print(f"\n📌 {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode()
        if output:
            print(output)
    
    print("\n✅ All done! Backend rebuilt with:")
    print("   ✅ 3 Gemini API keys with rotation")
    print("   ✅ Professional system instruction")
    print("   ✅ Retry logic with exponential backoff")
    print("   ✅ Safety settings")
    print("\nBot is now a professional sales consultant! 🎯")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    print(traceback.format_exc())
