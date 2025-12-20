#!/usr/bin/env python3
"""
Auto-deploy brain.py fix to production server
"""
import paramiko
import os
from pathlib import Path

# Server details
SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"
REMOTE_PATH = "/opt/ArtinSmartRealty/backend/brain.py"
LOCAL_PATH = r"I:\ArtinRealtySmartPro\ArtinSmartRealty\backend\brain.py"

print("🚀 Starting deployment...")

try:
    # Connect via SSH
    print(f"📡 Connecting to {SERVER}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    print("✅ Connected!")
    
    # Upload file via SFTP
    print(f"📤 Uploading {LOCAL_PATH} to {REMOTE_PATH}...")
    sftp = ssh.open_sftp()
    
    # Backup first
    print("💾 Creating backup...")
    stdin, stdout, stderr = ssh.exec_command(f"cp {REMOTE_PATH} {REMOTE_PATH}.backup")
    stdout.channel.recv_exit_status()
    
    # Upload new file
    sftp.put(LOCAL_PATH, REMOTE_PATH)
    print("✅ File uploaded!")
    
    # Rebuild backend
    print("🔨 Rebuilding backend container...")
    full_command = """
    cd /opt/ArtinSmartRealty && \
    docker-compose down && \
    docker-compose build --no-cache backend && \
    docker-compose up -d
    """
    
    print(f"   Running command...")
    stdin, stdout, stderr = ssh.exec_command(full_command, get_pty=True)
    
    # Read output in real-time
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            output = stdout.read().decode()
            print(output[:500] if len(output) > 500 else output)
    
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        error = stderr.read().decode()
        print(f"❌ Error: {error}")
    else:
        print("✅ Backend rebuilt successfully!")
    
    # Check logs
    print("\n📊 Checking backend logs...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose logs --tail=20 backend | grep -E '✅|❌|❓|Bot started|ERROR'"
    )
    logs = stdout.read().decode()
    print(logs)
    
    sftp.close()
    ssh.close()
    
    print("\n🎉 Deployment complete!")
    print("\n🧪 Test the bot:")
    print("1. Open Telegram: @TaranteenBot")
    print("2. Send: /start")
    print("3. Choose Persian")
    print("4. When asked for name, ask: 'ببین من چطوری میتونم اقامت بگیرم؟'")
    print("5. Bot should answer the question then ask for name again ✅")
    
except Exception as e:
    print(f"❌ Deployment failed: {e}")
    import traceback
    traceback.print_exc()
