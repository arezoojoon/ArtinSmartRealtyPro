#!/usr/bin/env python3
"""
Check docker-compose.yml for volume mounts
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🔍 Checking docker-compose.yml...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Get the backend service definition
    print("📋 Backend service configuration:")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && grep -A30 'backend:' docker-compose.yml"
    )
    
    output = stdout.read().decode()
    print(output)
    
    # Check for volume mounts specifically
    print("\n🔎 Looking for volume mounts...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && grep -A30 'backend:' docker-compose.yml | grep -E 'volumes:|./backend'"
    )
    
    volumes = stdout.read().decode()
    if volumes:
        print("⚠️ FOUND VOLUME MOUNTS:")
        print(volumes)
        print("\n💡 This is the problem! Volume mount overrides the built image.")
    else:
        print("✅ No volume mounts found")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
