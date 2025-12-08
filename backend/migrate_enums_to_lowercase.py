"""
Migration script to convert all UPPERCASE enum values to lowercase in database.
This ensures consistency with the enum definitions (which use lowercase values).
"""
import asyncio
from sqlalchemy import text
from database import async_session

async def migrate_enums_to_lowercase():
    """Convert all UPPERCASE enum values to lowercase"""
    
    async with async_session() as session:
        print("🔧 Starting enum migration to lowercase...")
        
        # Fix conversation_state
        print("\n📝 Fixing conversation_state...")
        result = await session.execute(text("""
            UPDATE leads 
            SET conversation_state = LOWER(conversation_state)
            WHERE conversation_state IS NOT NULL
        """))
        print(f"✅ Updated {result.rowcount} conversation_state rows")
        
        # Fix language
        print("\n📝 Fixing language...")
        result = await session.execute(text("""
            UPDATE leads 
            SET language = LOWER(language)
            WHERE language IS NOT NULL
        """))
        print(f"✅ Updated {result.rowcount} language rows")
        
        # Fix purpose
        print("\n📝 Fixing purpose...")
        result = await session.execute(text("""
            UPDATE leads 
            SET purpose = LOWER(purpose)
            WHERE purpose IS NOT NULL
        """))
        print(f"✅ Updated {result.rowcount} purpose rows")
        
        # Fix transaction_type
        print("\n📝 Fixing transaction_type...")
        result = await session.execute(text("""
            UPDATE leads 
            SET transaction_type = LOWER(transaction_type)
            WHERE transaction_type IS NOT NULL
        """))
        print(f"✅ Updated {result.rowcount} transaction_type rows")
        
        # Fix property_type
        print("\n📝 Fixing property_type...")
        result = await session.execute(text("""
            UPDATE leads 
            SET property_type = LOWER(property_type)
            WHERE property_type IS NOT NULL
        """))
        print(f"✅ Updated {result.rowcount} property_type rows")
        
        # Fix status
        print("\n📝 Fixing status...")
        result = await session.execute(text("""
            UPDATE leads 
            SET status = LOWER(status)
            WHERE status IS NOT NULL
        """))
        print(f"✅ Updated {result.rowcount} status rows")
        
        # Fix payment_method
        print("\n📝 Fixing payment_method...")
        result = await session.execute(text("""
            UPDATE leads 
            SET payment_method = LOWER(payment_method)
            WHERE payment_method IS NOT NULL
        """))
        print(f"✅ Updated {result.rowcount} payment_method rows")
        
        await session.commit()
        
        print("\n🎉 Migration completed successfully!")
        
        # Verify the fix
        print("\n🔍 Verifying migration...")
        result = await session.execute(text("""
            SELECT id, conversation_state, language, status
            FROM leads 
            LIMIT 5
        """))
        rows = result.fetchall()
        for row in rows:
            print(f"Lead {row[0]}: state={row[1]}, lang={row[2]}, status={row[3]}")

if __name__ == "__main__":
    asyncio.run(migrate_enums_to_lowercase())
