"""
Database migration to add image fields to leads table
Run this script after deploying the new code
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def migrate():
    """Add image_description, image_search_results, image_file_url to leads table."""
    
    # Database connection
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in environment")
        return
    
    # Parse DATABASE_URL
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
        print("\n📋 Checking if migration is needed...")
        
        # Check if columns already exist
        existing_columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'leads' 
            AND column_name IN ('image_description', 'image_search_results', 'image_file_url')
        """)
        
        existing_column_names = [row['column_name'] for row in existing_columns]
        
        if len(existing_column_names) == 3:
            print("✅ All image columns already exist. No migration needed.")
            return
        
        print(f"\n🔧 Adding image fields to leads table...")
        
        # Add columns if they don't exist
        if 'image_description' not in existing_column_names:
            await conn.execute("""
                ALTER TABLE leads 
                ADD COLUMN IF NOT EXISTS image_description TEXT
            """)
            print("  ✅ Added image_description column")
        
        if 'image_search_results' not in existing_column_names:
            await conn.execute("""
                ALTER TABLE leads 
                ADD COLUMN IF NOT EXISTS image_search_results INTEGER DEFAULT 0
            """)
            print("  ✅ Added image_search_results column")
        
        if 'image_file_url' not in existing_column_names:
            await conn.execute("""
                ALTER TABLE leads 
                ADD COLUMN IF NOT EXISTS image_file_url VARCHAR(512)
            """)
            print("  ✅ Added image_file_url column")
        
        print("\n✅ Migration completed successfully!")
        
        # Show current schema
        all_columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'leads'
            AND column_name IN ('voice_transcript', 'voice_entities', 'image_description', 'image_search_results', 'image_file_url')
            ORDER BY column_name
        """)
        
        print("\n📊 Media-related columns in leads table:")
        for col in all_columns:
            print(f"  • {col['column_name']}: {col['data_type']}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await conn.close()


if __name__ == "__main__":
    print("🚀 Starting database migration for image features...\n")
    asyncio.run(migrate())
