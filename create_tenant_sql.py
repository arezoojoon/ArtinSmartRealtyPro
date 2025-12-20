#!/usr/bin/env python3
"""
Create tenant using SQL directly
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

BOT_TOKEN = "7750551672:AAHaVtzQAo0WqAZ8YqFJLp2IldXq2MNDkSs"

print("👤 Creating Hamidreza Damroodi tenant with SQL...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Create a SQL file on the server
    sql = f"""
INSERT INTO tenants (
    name, 
    email, 
    password_hash,
    company_name,
    phone,
    telegram_bot_token,
    is_active,
    subscription_plan,
    subscription_status,
    default_language,
    created_at,
    updated_at
) VALUES (
    'Hamidreza Damroodi',
    'hamidreza@example.com',
    'pbkdf2_sha256_600000_placeholder',
    'Hamidreza Damroodi Real Estate',
    '+971501234567',
    '{BOT_TOKEN}',
    true,
    'professional',
    'active',
    'fa',
    NOW(),
    NOW()
) ON CONFLICT (email) DO NOTHING;
"""
    
    # Write SQL to temp file
    stdin, stdout, stderr = ssh.exec_command(
        f"echo \"{sql}\" > /tmp/create_tenant.sql"
    )
    stdout.read()
    
    # Execute SQL
    print("📝 Executing SQL...")
    stdin, stdout, stderr = ssh.exec_command(
        "docker exec artinrealty-db psql -U postgres -d artinrealty -f /tmp/create_tenant.sql"
    )
    
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if output:
        print(output)
    if error:
        print(f"Error: {error}")
    
    # Verify
    print("\n🔍 Verifying tenant:")
    stdin, stdout, stderr = ssh.exec_command(
        """docker exec artinrealty-db psql -U postgres -d artinrealty -c "SELECT id, name, email, telegram_bot_token IS NOT NULL as has_token FROM tenants;" """
    )
    print(stdout.read().decode())
    
    # Restart backend
    print("\n🔄 Restarting backend...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose restart backend"
    )
    stdout.read()
    
    print("\n✅ Done! Test bot with /start")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
