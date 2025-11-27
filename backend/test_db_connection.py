"""
Database Connection Test
بررسی اتصال به دیتابیس
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_connection():
    """Test database connection"""
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    print()
    
    try:
        from database import DATABASE_URL, engine
        from sqlalchemy import text
        
        print(f"📍 Database URL: {DATABASE_URL}")
        print()
        print("🔄 Testing connection...")
        
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print("✅ Connection successful!")
            print(f"📊 PostgreSQL version: {version}")
            print()
            
            # Check if tenant_properties table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'tenant_properties'
                );
            """))
            exists = result.fetchone()[0]
            
            if exists:
                print("✅ Table 'tenant_properties' exists")
                
                # Check for image columns
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'tenant_properties' 
                    AND column_name IN ('image_urls', 'image_files', 'primary_image', 'full_description', 'is_urgent')
                    ORDER BY column_name;
                """))
                
                columns = [row[0] for row in result.fetchall()]
                
                if len(columns) == 5:
                    print("✅ All image columns exist:")
                    for col in columns:
                        print(f"   - {col}")
                    print()
                    print("🎉 Database is ready! No migration needed.")
                else:
                    print(f"⚠️  Found {len(columns)} of 5 required columns")
                    print("📝 Need to run migration:")
                    print("   python migrate_property_images.py")
            else:
                print("⚠️  Table 'tenant_properties' does not exist")
                print("📝 Need to initialize database first:")
                print("   python -c \"from database import init_db; import asyncio; asyncio.run(init_db())\"")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print()
        print("💡 Troubleshooting:")
        print("   1. Is PostgreSQL running?")
        print("      Docker: docker-compose up -d db")
        print("      Local:  net start postgresql-x64-15")
        print()
        print("   2. Is DATABASE_URL correct in .env?")
        print("      postgresql+asyncpg://postgres:PASSWORD@localhost:5432/artinrealty")
        print()
        print("   3. Does database 'artinrealty' exist?")
        print("      psql -U postgres -c \"CREATE DATABASE artinrealty;\"")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
