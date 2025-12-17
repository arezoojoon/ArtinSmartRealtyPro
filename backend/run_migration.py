"""
Migration script to add booking fields to tenants table
Executes SQL statements separately to avoid asyncpg prepared statement limitation
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/artinrealty")

# Parse asyncpg URL to standard URL
if "asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


async def run_migration():
    """Add booking_url, contact_phone, whatsapp_link columns to tenants table"""
    print("🔧 Connecting to database...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Step 1: Add booking_url column
        print("📝 Adding booking_url column...")
        await conn.execute(
            "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS booking_url VARCHAR(512)"
        )
        print("✅ booking_url column added")
        
        # Step 2: Add contact_phone column
        print("📝 Adding contact_phone column...")
        await conn.execute(
            "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50)"
        )
        print("✅ contact_phone column added")
        
        # Step 3: Add whatsapp_link column
        print("📝 Adding whatsapp_link column...")
        await conn.execute(
            "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS whatsapp_link VARCHAR(512)"
        )
        print("✅ whatsapp_link column added")
        
        # Step 4: Update taranteen tenant with current values
        print("📝 Updating taranteen tenant with booking information...")
        result = await conn.execute("""
            UPDATE tenants 
            SET booking_url = 'https://calendly.com/taranteen-realty/consultation',
                contact_phone = '+971 50 503 7158',
                whatsapp_link = 'https://wa.me/971505037158'
            WHERE name = 'taranteen'
        """)
        print(f"✅ Updated tenant (result: {result})")
        
        # Step 5: Verify migration
        print("\n📊 Verifying migration...")
        rows = await conn.fetch("""
            SELECT name, booking_url, contact_phone, whatsapp_link 
            FROM tenants 
            WHERE name = 'taranteen'
        """)
        
        if rows:
            for row in rows:
                print(f"\n📋 Tenant: {row['name']}")
                print(f"   Booking URL: {row['booking_url']}")
                print(f"   Contact Phone: {row['contact_phone']}")
                print(f"   WhatsApp Link: {row['whatsapp_link']}")
        
        print("\n🎉 Migration completed successfully!")
    
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    
    finally:
        await conn.close()
        print("🔌 Database connection closed")


if __name__ == "__main__":
    asyncio.run(run_migration())
