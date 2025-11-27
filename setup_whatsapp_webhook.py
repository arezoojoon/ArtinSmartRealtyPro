"""
Setup WhatsApp webhook for Meta Business API
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def setup_whatsapp():
    """Setup WhatsApp webhook configuration."""
    
    # Database connection
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in environment")
        return
    
    # Parse DATABASE_URL
    # postgresql://user:password@host:port/database
    db_url = db_url.replace("postgresql://", "").replace("postgresql+asyncpg://", "")
    user_pass, host_db = db_url.split("@")
    user, password = user_pass.split(":")
    host_port, database = host_db.split("/")
    
    if ":" in host_port:
        host, port = host_port.split(":")
    else:
        host = host_port
        port = "5432"
    
    print(f"🔌 Connecting to database: {host}:{port}/{database}")
    
    conn = await asyncpg.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database
    )
    
    try:
        # Get tenants with WhatsApp credentials
        tenants = await conn.fetch(
            """
            SELECT id, name, email, whatsapp_phone_number_id, whatsapp_access_token, whatsapp_verify_token
            FROM tenants
            WHERE whatsapp_phone_number_id IS NOT NULL AND whatsapp_access_token IS NOT NULL
            """
        )
        
        if not tenants:
            print("\n⚠️  No tenants with WhatsApp credentials found")
            print("\nTo setup WhatsApp:")
            print("1. Go to https://business.facebook.com/")
            print("2. Create WhatsApp Business Account")
            print("3. Get Phone Number ID and Access Token")
            print("4. Update tenant settings in the admin dashboard")
            return
        
        print(f"\n✅ Found {len(tenants)} tenant(s) with WhatsApp credentials:\n")
        
        for tenant in tenants:
            print(f"📱 {tenant['name']} ({tenant['email']})")
            print(f"   Phone Number ID: {tenant['whatsapp_phone_number_id']}")
            print(f"   Access Token: {tenant['whatsapp_access_token'][:20]}...")
            print(f"   Verify Token: {tenant['whatsapp_verify_token'] or 'Not set'}")
        
        # Get domain
        domain = input("\n🌐 Enter your domain (e.g., realty.artinsmartagent.com): ").strip()
        
        if not domain:
            print("❌ Domain is required")
            return
        
        webhook_url = f"https://{domain}/webhook/whatsapp"
        
        print(f"\n📋 WhatsApp Webhook Setup Instructions:\n")
        print(f"1. Go to https://developers.facebook.com/apps")
        print(f"2. Select your app → WhatsApp → Configuration")
        print(f"3. Click 'Edit' on Webhook")
        print(f"4. Enter:")
        print(f"   Callback URL: {webhook_url}")
        
        # Get verify token from first tenant or generate one
        verify_token = tenants[0]['whatsapp_verify_token']
        if not verify_token:
            import secrets
            verify_token = secrets.token_urlsafe(32)
            print(f"\n🔐 Generated new verify token: {verify_token}")
            print(f"\n⚠️  Save this token! You'll need to update the tenant settings.")
            
            # Update tenant with verify token
            await conn.execute(
                "UPDATE tenants SET whatsapp_verify_token = $1 WHERE id = $2",
                verify_token,
                tenants[0]['id']
            )
            print(f"✅ Updated tenant {tenants[0]['name']} with verify token")
        
        print(f"   Verify Token: {verify_token}")
        print(f"5. Click 'Verify and Save'")
        print(f"6. Subscribe to these webhook fields:")
        print(f"   ✅ messages")
        print(f"   ✅ message_status (optional)")
        
        print(f"\n🎯 Webhook URL: {webhook_url}")
        print(f"🔑 Verify Token: {verify_token}")
        
        # Test instructions
        print(f"\n🧪 To test:")
        print(f"1. Send a message to your WhatsApp Business number")
        print(f"2. Check backend logs: docker compose logs -f backend")
        print(f"3. Look for 'WhatsApp webhook' messages")
        
        print("\n✅ WhatsApp webhook setup guide complete!")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(setup_whatsapp())
