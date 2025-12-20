#!/usr/bin/env python3
"""
Clear Python cache and restart backend
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🧹 Clearing Python cache and restarting...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    commands = [
        "find /opt/ArtinSmartRealty/backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; echo '✅ Host cache cleared'",
        "docker exec artinrealty-backend find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; echo '✅ Container cache cleared'",
        "docker exec artinrealty-backend find /app -name '*.pyc' -delete; echo '✅ .pyc files deleted'",
        "cd /opt/ArtinSmartRealty && docker-compose restart backend"
    ]
    
    for cmd in commands:
        print(f"\n📌 Running: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if output:
            print(output)
        if error and "cannot delete" not in error.lower():
            print(f"⚠️ {error}")
    
    print("\n✅ Done! Testing bot now...")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
