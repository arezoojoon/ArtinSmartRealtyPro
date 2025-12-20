#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import paramiko

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("72.62.93.116", username="root", password="u0;74KWyoEydh5g.Q9)s")

print("=== Checking Gemini initialization ===\n")
stdin, stdout, stderr = ssh.exec_command("cd /opt/ArtinSmartRealty && docker-compose logs backend | grep -i 'gemini\\|api.*key\\|professional\\|tenant.*bot\\|Failed to start' | tail -30")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
