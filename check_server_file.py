#!/usr/bin/env python3
"""
Check if brain.py on server has the fix
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🔍 Checking server brain.py file...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Check if fix exists in the file
    print("📋 Searching for the fix code in brain.py...")
    stdin, stdout, stderr = ssh.exec_command(
        "grep -n 'CRITICAL FIX: Check if this looks like a QUESTION' /opt/ArtinSmartRealty/backend/brain.py"
    )
    
    result = stdout.read().decode()
    
    if result:
        print(f"✅ Fix found in file at line:")
        print(result)
    else:
        print("❌ Fix NOT found in file!")
        print("\nLet me check what's actually in the file around line 2790...")
        
        stdin, stdout, stderr = ssh.exec_command(
            "sed -n '2785,2810p' /opt/ArtinSmartRealty/backend/brain.py"
        )
        print(stdout.read().decode())
    
    # Also check the container's file
    print("\n🐳 Checking file INSIDE the running container...")
    stdin, stdout, stderr = ssh.exec_command(
        "docker exec artinrealty-backend grep -n 'CRITICAL FIX: Check if this looks like a QUESTION' /app/brain.py || echo 'NOT FOUND IN CONTAINER'"
    )
    container_result = stdout.read().decode()
    print(container_result)
    
    if "NOT FOUND IN CONTAINER" in container_result:
        print("\n⚠️ PROBLEM: Container is using OLD code!")
        print("   The file was updated on host but container wasn't rebuilt properly.")
        print("\n💡 Solution: Need to force rebuild with volume removal")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
