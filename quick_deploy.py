#!/usr/bin/env python3
import paramiko

print("Uploading and rebuilding...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("72.62.93.116", username="root", password="u0;74KWyoEydh5g.Q9)s")

# Upload
print("1. Uploading...")
sftp = ssh.open_sftp()
sftp.put(r"I:\ArtinRealtySmartPro\ArtinSmartRealty\backend\brain.py", "/opt/ArtinSmartRealty/backend/brain.py")
sftp.close()
print("   Done!")

# Quick rebuild
print("2. Restarting backend...")
stdin, stdout, stderr = ssh.exec_command("cd /opt/ArtinSmartRealty && docker-compose restart backend", timeout=120)
stdout.read()
print("   Done!")

# Check logs
print("3. Checking logs...")
import time
time.sleep(10)

stdin, stdout, stderr = ssh.exec_command("cd /opt/ArtinSmartRealty && docker-compose logs --tail=50 backend | grep -E '(SyntaxError|Gemini|Bot.*started|Failed|professional)'")
logs = stdout.read().decode('utf-8', errors='replace')
print(logs if logs else "No relevant logs")

ssh.close()
print("\nDone! Test @TaranteenrealstateBot now!")
