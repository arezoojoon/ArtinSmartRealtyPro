#!/usr/bin/env python3
"""
Check backend logs to see what's happening
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("📋 Checking backend logs...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Get last 50 lines of logs
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose logs --tail=100 backend | grep -E '(میخوام|اقامت|COLLECTING_NAME|handle_collecting_name|User asked question|CRITICAL FIX)'"
    )
    
    logs = stdout.read().decode()
    
    if logs:
        print("🔍 Found relevant logs:")
        print(logs)
    else:
        print("❌ No relevant logs found!")
        print("\n📋 Showing last 50 lines of all logs:")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /opt/ArtinSmartRealty && docker-compose logs --tail=50 backend"
        )
        print(stdout.read().decode())
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
