#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import paramiko

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("72.62.93.116", username="root", password="u0;74KWyoEydh5g.Q9)s")

print("=== Checking contact handling logs ===\n")
stdin, stdout, stderr = ssh.exec_command("cd /opt/ArtinSmartRealty && docker-compose logs --tail=100 backend | grep -E '(arezoo|917|contact|phone|CAPTURE|الو)' -i")
logs = stdout.read().decode('utf-8', errors='replace')
print(logs if logs else "No logs found!")

ssh.close()
