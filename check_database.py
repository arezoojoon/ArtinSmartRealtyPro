#!/usr/bin/env python3
"""
Check database for tenants
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🗄️ Checking database for tenants...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Direct PostgreSQL query
    stdin, stdout, stderr = ssh.exec_command(
        """docker exec artinrealty-db psql -U postgres -d artinrealty -c "SELECT id, name, is_active, telegram_bot_token IS NOT NULL as has_bot_token FROM tenants;" """
    )
    
    result = stdout.read().decode()
    error = stderr.read().decode()
    
    if result:
        print("📋 Tenants in database:")
        print(result)
    
    if error:
        print(f"⚠️ Error: {error}")
    
    # Count tenants
    stdin, stdout, stderr = ssh.exec_command(
        """docker exec artinrealty-db psql -U postgres -d artinrealty -c "SELECT COUNT(*) as total_tenants FROM tenants;" """
    )
    
    count = stdout.read().decode()
    print(f"\n📊 Total tenants:")
    print(count)
    
    # Check if any have bot tokens
    stdin, stdout, stderr = ssh.exec_command(
        """docker exec artinrealty-db psql -U postgres -d artinrealty -c "SELECT COUNT(*) as tenants_with_bot FROM tenants WHERE telegram_bot_token IS NOT NULL;" """
    )
    
    with_bot = stdout.read().decode()
    print(f"\n🤖 Tenants with bot token:")
    print(with_bot)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
