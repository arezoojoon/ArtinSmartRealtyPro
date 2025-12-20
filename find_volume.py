#!/usr/bin/env python3
"""
Check EXACTLY which service has the volume mount
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🔍 Checking which service has ./backend volume mount...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Get full docker-compose.yml
    stdin, stdout, stderr = ssh.exec_command(
        "cat /opt/ArtinSmartRealty/docker-compose.yml"
    )
    
    content = stdout.read().decode()
    
    # Find the service with ./backend:/app
    lines = content.split('\n')
    current_service = None
    
    for i, line in enumerate(lines):
        if line.strip().endswith(':') and not line.strip().startswith('#') and not line.strip().startswith('-'):
            # This might be a service name
            if '  ' + line.strip() == line[:2] + line.strip():  # Top level service
                current_service = line.strip().rstrip(':')
        
        if './backend:/app' in line:
            print(f"🎯 Found './backend:/app' in service: {current_service}")
            print(f"   Line {i+1}: {line}")
            
            # Print context
            start = max(0, i-10)
            end = min(len(lines), i+5)
            print(f"\n📋 Context (lines {start+1}-{end+1}):")
            for j in range(start, end):
                marker = " >>> " if j == i else "     "
                print(f"{marker}{lines[j]}")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
