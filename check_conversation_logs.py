#!/usr/bin/env python3
"""
Check logs for the recent conversation
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("📋 Checking recent bot logs...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Get logs from last 5 minutes
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose logs --tail=200 backend | grep -A2 -B2 -E '(اقامت|علی|COLLECTING_NAME|handle_collecting|User asked question|CRITICAL FIX|میخوام)'"
    )
    
    logs = stdout.read().decode()
    
    if logs:
        print("🔍 Found relevant logs:")
        print(logs)
    else:
        print("❌ No relevant logs found!")
        print("\n📋 Let me check all recent logs:")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /opt/ArtinSmartRealty && docker-compose logs --tail=100 backend"
        )
        print(stdout.read().decode())
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
