#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import paramiko

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("72.62.93.116", username="root", password="u0;74KWyoEydh5g.Q9)s")

print("=== Last 100 lines of backend logs ===\n")
stdin, stdout, stderr = ssh.exec_command("cd /opt/ArtinSmartRealty && docker-compose logs --tail=100 backend")
logs = stdout.read().decode('utf-8', errors='replace')

# Print only important lines
for line in logs.split('\n'):
    if any(keyword in line.lower() for keyword in ['gemini', 'api', 'key', 'bot', 'failed', 'error', 'started', 'professional', 'tenant']):
        print(line)

ssh.close()
