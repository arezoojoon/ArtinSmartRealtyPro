#!/usr/bin/env python3
"""
Force complete rebuild and restart
"""
import paramiko
import time

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🔨 Force rebuilding backend...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    commands = [
        ("Stopping all services", "cd /opt/ArtinSmartRealty && docker-compose down"),
        ("Removing old backend image", "docker rmi artinsmartrealty-backend -f || echo 'Image not found'"),
        ("Building backend (no cache)", "cd /opt/ArtinSmartRealty && docker-compose build --no-cache backend"),
        ("Starting all services", "cd /opt/ArtinSmartRealty && docker-compose up -d"),
        ("Waiting for startup", "sleep 15"),
        ("Checking logs", "cd /opt/ArtinSmartRealty && docker-compose logs --tail=50 backend | grep -E '(Gemini|professional|key rotation|API)'"),
    ]
    
    for desc, cmd in commands:
        print(f"\n📌 {desc}...")
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=300)
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if "Building" in desc or "Starting" in desc:
            # Show progress for long commands
            if output:
                # Show last 10 lines
                lines = output.split('\n')
                for line in lines[-10:]:
                    if line.strip():
                        print(f"  {line}")
        else:
            if output:
                print(output)
        
        if error and "warning" not in error.lower():
            print(f"⚠️ {error[:500]}")
    
    print("\n✅ Rebuild complete!")
    print("\n🧪 Now test the bot with /start")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    print(traceback.format_exc())
