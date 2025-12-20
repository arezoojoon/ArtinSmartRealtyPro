#!/usr/bin/env python3
"""
Check current API keys
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🔑 Checking current API keys...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Check .env file
    stdin, stdout, stderr = ssh.exec_command(
        "cat /opt/ArtinSmartRealty/.env | grep -E '(GEMINI_API_KEY|BOT_TOKEN)'"
    )
    
    print("📋 Current .env values:")
    print(stdout.read().decode())
    
    # Check what bot is actually running
    print("\n🤖 Checking for any python-telegram-bot processes:")
    stdin, stdout, stderr = ssh.exec_command(
        "ps aux | grep -E '(telegram|bot)' | grep -v grep"
    )
    print(stdout.read().decode())
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
