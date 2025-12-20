#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("72.62.93.116", username="root", password="u0;74KWyoEydh5g.Q9)s")

sql_cmd = """docker exec artinrealty-db psql -U postgres -d artinrealty -c "INSERT INTO tenants (name, email, password_hash, company_name, phone, telegram_bot_token, is_active, created_at, updated_at) VALUES ('Hamidreza Damroodi', 'hamidreza@example.com', 'pbkdf2_sha256', 'Hamidreza Real Estate', '+971501234567', '7750551672:AAHaVtzQAo0WqAZ8YqFJLp2IldXq2MNDkSs', true, NOW(), NOW());" """

stdin, stdout, stderr = ssh.exec_command(sql_cmd)
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("Error:", err)

# Verify
stdin, stdout, stderr = ssh.exec_command("""docker exec artinrealty-db psql -U postgres -d artinrealty -c "SELECT id, name, email FROM tenants;" """)
print("\nTenants:")
print(stdout.read().decode())

# Restart backend
print("\nRestarting backend...")
stdin, stdout, stderr = ssh.exec_command("cd /opt/ArtinSmartRealty && docker-compose restart backend")
print(stdout.read().decode())

ssh.close()
print("\n✅ Done! Test the bot now!")
