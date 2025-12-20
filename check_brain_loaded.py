#!/usr/bin/env python3
"""
Check backend logs to see if new system instruction loaded
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🔍 Checking if new AI brain loaded...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Check startup logs for Gemini initialization
    print("1️⃣ Checking Gemini initialization:")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose logs backend | grep -E '(Gemini|professional|system instruction|key rotation|API key)' | tail -20"
    )
    logs = stdout.read().decode()
    if logs:
        print(logs)
    else:
        print("❌ No Gemini logs found!")
    
    # Check recent conversation
    print("\n2️⃣ Checking recent conversation logs:")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose logs --tail=100 backend | grep -E '(اقامت|معیار|qualification|qualifying)'"
    )
    conv_logs = stdout.read().decode()
    if conv_logs:
        print(conv_logs)
    else:
        print("❌ No conversation logs!")
    
    # Check if backend actually restarted
    print("\n3️⃣ Checking backend container uptime:")
    stdin, stdout, stderr = ssh.exec_command(
        "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep backend"
    )
    print(stdout.read().decode())
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
