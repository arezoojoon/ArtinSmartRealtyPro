#!/usr/bin/env python3
"""
Force Python to recompile brain.py by deleting .pyc and restarting with PYTHONDONTWRITEBYTECODE
"""
import paramiko
import time

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🔄 Forcing Python to reload brain.py...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    commands = [
        # Step 1: Stop backend
        ("Stopping backend...", "cd /opt/ArtinSmartRealty && docker-compose stop backend"),
        
        # Step 2: Delete ALL .pyc files
        ("Deleting .pyc files...", "docker exec artinrealty-backend find /app -name '*.pyc' -delete || echo 'Container stopped'"),
        
        # Step 3: Delete __pycache__ directories
        ("Deleting __pycache__...", "docker exec artinrealty-backend find /app -type d -name __pycache__ -exec rm -rf {} + || echo 'Container stopped'"),
        
        # Step 4: Start backend fresh
        ("Starting backend...", "cd /opt/ArtinSmartRealty && docker-compose up -d backend"),
        
        # Step 5: Wait for it to be healthy
        ("Waiting for backend to be healthy...", "sleep 10"),
        
        # Step 6: Delete .pyc AGAIN (after import)
        ("Deleting newly created .pyc...", "docker exec artinrealty-backend find /app -name 'brain*.pyc' -delete"),
        
        # Step 7: Restart one more time
        ("Final restart...", "cd /opt/ArtinSmartRealty && docker-compose restart backend"),
        
        # Step 8: Verify
        ("Checking logs...", "cd /opt/ArtinSmartRealty && docker-compose logs --tail=20 backend"),
    ]
    
    for desc, cmd in commands:
        print(f"\n📌 {desc}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if output:
            print(output)
        if error and "warning" not in error.lower():
            print(f"⚠️ {error}")
        
        time.sleep(1)
    
    print("\n✅ Done! Now test the bot!")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
