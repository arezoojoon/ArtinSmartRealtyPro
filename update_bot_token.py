#!/usr/bin/env python3
"""
Update tenant with new bot token and restart
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

NEW_BOT_TOKEN = "8541904612:AAFxZ_nOW8HHHfCgORGSHwH9E00Qt83EBgw"

print("🤖 Updating bot token in database...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Update token in database
    update_sql = f"""UPDATE tenants SET telegram_bot_token = '{NEW_BOT_TOKEN}' WHERE id = 1;"""
    
    stdin, stdout, stderr = ssh.exec_command(
        f'docker exec artinrealty-db psql -U postgres -d artinrealty -c "{update_sql}"'
    )
    
    result = stdout.read().decode()
    error = stderr.read().decode()
    
    if result:
        print(f"✅ Database updated: {result}")
    if error and "UPDATE" not in error:
        print(f"⚠️ {error}")
    
    # Verify
    print("\n🔍 Verifying update:")
    stdin, stdout, stderr = ssh.exec_command(
        'docker exec artinrealty-db psql -U postgres -d artinrealty -c "SELECT id, name, substring(telegram_bot_token, 1, 20) as token_preview FROM tenants WHERE id = 1;"'
    )
    print(stdout.read().decode())
    
    # Restart backend to reload bot
    print("\n🔄 Restarting backend to initialize new bot...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose restart backend"
    )
    stdout.read()
    
    # Wait and check logs
    print("\n⏳ Waiting for bot to start (15 seconds)...")
    import time
    time.sleep(15)
    
    print("\n📋 Checking bot startup:")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/ArtinSmartRealty && docker-compose logs --tail=50 backend | grep -E '(Bot started|Gemini|professional|key rotation|Failed)'"
    )
    logs = stdout.read().decode()
    print(logs if logs else "No relevant logs found")
    
    print("\n✅ Done! Bot token updated!")
    print(f"\n🤖 Your new bot: @TaranteenrealstateBot")
    print(f"🧪 Test it now with /start")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    print(traceback.format_exc())
