#!/usr/bin/env python3
"""
Force rebuild backend with new brain.py
"""
import paramiko
import time

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🔥 Force rebuilding backend...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    print("✅ Connected!")
    
    # Stop everything first
    print("🛑 Stopping all containers...")
    stdin, stdout, stderr = ssh.exec_command("cd /opt/ArtinSmartRealty && docker-compose down", get_pty=True)
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())
    
    time.sleep(2)
    
    # Remove old backend image
    print("🗑️ Removing old backend image...")
    stdin, stdout, stderr = ssh.exec_command("docker rmi artinsmartrealty-backend || true", get_pty=True)
    stdout.channel.recv_exit_status()
    
    time.sleep(1)
    
    # Rebuild with no cache
    print("🔨 Building backend (this may take 1-2 minutes)...")
    print("   Please wait...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose build --no-cache backend",
        get_pty=True
    )
    
    # Wait for completion
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        print("✅ Build complete!")
    else:
        print("❌ Build failed!")
        error_output = stderr.read().decode('utf-8', errors='ignore')
        print(error_output[-500:])  # Last 500 chars
    
    time.sleep(2)
    
    # Start everything
    print("🚀 Starting all services...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose up -d",
        get_pty=True
    )
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())
    
    time.sleep(5)
    
    # Check logs for the fix
    print("\n📊 Checking if fix is loaded...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose logs --tail=30 backend | grep -E '❓|✅ Bot|User asked question'"
    )
    logs = stdout.read().decode()
    
    if logs:
        print("Logs found:")
        print(logs)
    else:
        print("No specific logs yet (normal on fresh start)")
    
    # Show last 20 lines
    print("\n📝 Last 20 lines of backend logs:")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose logs --tail=20 backend"
    )
    print(stdout.read().decode())
    
    ssh.close()
    
    print("\n" + "="*60)
    print("🎉 Backend rebuilt and restarted!")
    print("="*60)
    print("\n🧪 Now test again in Telegram:")
    print("1. Send: /start")
    print("2. Select Persian 🇮🇷")
    print("3. When asked for name, send: 'ببین من چطوری میتونم اقامت بگیرم؟'")
    print("\n✅ Expected: Bot should answer the question, then ask for name")
    print("❌ If still broken: Bot will save the question as your name")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
