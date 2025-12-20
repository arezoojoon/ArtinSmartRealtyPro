#!/usr/bin/env python3
"""
Update .env with new Gemini API keys and update brain.py with professional system instruction
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🔧 Step 1: Updating .env with new Gemini API keys...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Add new keys to .env
    commands = [
        "cd /opt/ArtinSmartRealty",
        # Backup old .env
        "cp .env .env.backup",
        # Remove old GEMINI_API_KEY line
        "sed -i '/^GEMINI_API_KEY=/d' .env",
        # Add new keys
        "echo 'GEMINI_KEY_1=AIzaSyD7H0oXK80-FE-wgBXyK-GxssrwwtgQtn0' >> .env",
        "echo 'GEMINI_KEY_2=AIzaSyDDJwP4_QNmUYz-AnxMtpQFPwD1alsb2AE' >> .env",
        "echo 'GEMINI_KEY_3=AIzaSyA6PYKu78XDthMXQL-3kK3c-GIna4mtcWs' >> .env",
        # Keep backward compatibility
        "echo 'GEMINI_API_KEY=AIzaSyD7H0oXK80-FE-wgBXyK-GxssrwwtgQtn0' >> .env"
    ]
    
    for cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdout.read()
    
    print("✅ .env updated with 3 new Gemini API keys!")
    
    # Verify
    stdin, stdout, stderr = ssh.exec_command("cat /opt/ArtinSmartRealty/.env | grep GEMINI")
    print("\n📋 New .env Gemini keys:")
    print(stdout.read().decode())
    
    ssh.close()
    print("\n✅ Step 1 Complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
