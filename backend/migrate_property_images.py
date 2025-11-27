"""
Migration Script: Add Image Support to TenantProperty
Adds image_urls, image_files, primary_image, full_description, and is_urgent columns
"""

import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from database import DATABASE_URL

async def run_migration():
    """Run the migration to add image support columns"""
    # Convert to async URL if needed
    db_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://") if "asyncpg" not in DATABASE_URL else DATABASE_URL
    engine = create_async_engine(db_url)
    
    print("🔄 Starting migration: Add image support to tenant_properties table")
    
    migrations = [
        {
            "name": "Add image_urls column",
            "sql": """
                ALTER TABLE tenant_properties 
                ADD COLUMN IF NOT EXISTS image_urls JSON DEFAULT '[]'::json
            """
        },
        {
            "name": "Add image_files column",
            "sql": """
                ALTER TABLE tenant_properties 
                ADD COLUMN IF NOT EXISTS image_files JSON DEFAULT '[]'::json
            """
        },
        {
            "name": "Add primary_image column",
            "sql": """
                ALTER TABLE tenant_properties 
                ADD COLUMN IF NOT EXISTS primary_image VARCHAR(512)
            """
        },
        {
            "name": "Add full_description column",
            "sql": """
                ALTER TABLE tenant_properties 
                ADD COLUMN IF NOT EXISTS full_description TEXT
            """
        },
        {
            "name": "Add is_urgent column",
            "sql": """
                ALTER TABLE tenant_properties 
                ADD COLUMN IF NOT EXISTS is_urgent BOOLEAN DEFAULT FALSE
            """
        }
    ]
    
    try:
        async with engine.connect() as conn:
            for migration in migrations:
                print(f"  ➜ {migration['name']}...", end=" ")
                await conn.execute(text(migration['sql']))
                await conn.commit()
                print("✅")
        
        print("\n✅ Migration completed successfully!")
        print("\nNew columns added:")
        print("  - image_urls (JSON): Array of image URLs")
        print("  - image_files (JSON): Array of image metadata objects")
        print("  - primary_image (VARCHAR): Primary display image URL")
        print("  - full_description (TEXT): Rich formatted description with emojis")
        print("  - is_urgent (BOOLEAN): Urgent sale flag")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        await engine.dispose()
        return False

async def verify_migration():
    """Verify the migration was successful"""
    db_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://") if "asyncpg" not in DATABASE_URL else DATABASE_URL
    engine = create_async_engine(db_url)
    
    print("\n🔍 Verifying migration...")
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'tenant_properties' 
                AND column_name IN ('image_urls', 'image_files', 'primary_image', 'full_description', 'is_urgent')
                ORDER BY column_name
            """))
            
            columns = result.fetchall()
            
            if len(columns) == 5:
                print("✅ All columns present:")
                for col in columns:
                    print(f"  - {col[0]} ({col[1]})")
                await engine.dispose()
                return True
            else:
                print(f"⚠️  Expected 5 columns, found {len(columns)}")
                await engine.dispose()
                return False
                
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        await engine.dispose()
        return False

async def main():
    """Main migration function"""
    print("=" * 60)
    print("Property Images Migration Script")
    print("=" * 60)
    print()
    
    # Run migration
    if await run_migration():
        # Verify migration
        await verify_migration()
        return True
    return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
