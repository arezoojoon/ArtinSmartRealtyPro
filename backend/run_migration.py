"""
Run database migrations manually
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
    """Run the context fields migration."""
    print("🔧 Connecting to database...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("📝 Reading migration SQL...")
        with open("migrations/003_add_context_fields.sql", "r") as f:
            sql = f.read()
        
        print("⚙️ Executing migration...")
        await conn.execute(sql)
        
        print("✅ Migration completed successfully!")
        
        # Verify
        print("\n📊 Verifying columns...")
        rows = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'lead' 
            AND column_name IN ('filled_slots', 'pending_slot')
        """)
        
        for row in rows:
            print(f"  ✓ {row['column_name']}: {row['data_type']} (default: {row['column_default']})")
    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    
    finally:
        await conn.close()
        print("\n🔌 Database connection closed")


if __name__ == "__main__":
    asyncio.run(run_migration())
