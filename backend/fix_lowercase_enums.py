"""
Migration script to convert all lowercase enum values to UPPERCASE in database.
This fixes the issue where update_lead was storing enums as lowercase.
"""
import asyncio
from sqlalchemy import text
from database import async_engine, async_session

async def fix_lowercase_enums():
    """Convert all lowercase enum values to UPPERCASE"""
    
    async with async_session() as session:
        print("🔧 Starting enum migration to UPPERCASE...")
        
        # Fix conversation_state
        print("\n📝 Fixing conversation_state...")
        result = await session.execute(text("""
            UPDATE leads 
            SET conversation_state = UPPER(conversation_state)
            WHERE conversation_state IS NOT NULL
        """))
        print(f"✅ Updated {result.rowcount} conversation_state rows")
        
        # Fix language
        print("\n📝 Fixing language...")
        result = await session.execute(text("""
            UPDATE leads 
            SET language = UPPER(language)
            WHERE language IS NOT NULL
        """))
        print(f"✅ Updated {result.rowcount} language rows")
        
        # Fix purpose
        print("\n📝 Fixing purpose...")
        result = await session.execute(text("""
            UPDATE leads 
            SET purpose = UPPER(purpose)
            WHERE purpose IS NOT NULL
        """))
        print(f"✅ Updated {result.rowcount} purpose rows")
        
        # Fix transaction_type
        print("\n📝 Fixing transaction_type...")
        result = await session.execute(text("""
            UPDATE leads 
            SET transaction_type = UPPER(transaction_type)
            WHERE transaction_type IS NOT NULL
        """))
        print(f"✅ Updated {result.rowcount} transaction_type rows")
        
        # Fix property_type
        print("\n📝 Fixing property_type...")
        result = await session.execute(text("""
            UPDATE leads 
            SET property_type = UPPER(property_type)
            WHERE property_type IS NOT NULL
        """))
        print(f"✅ Updated {result.rowcount} property_type rows")
        
        await session.commit()
        
        print("\n🎉 Migration completed successfully!")
        
        # Verify the fix
        print("\n🔍 Verifying migration...")
        result = await session.execute(text("""
            SELECT id, conversation_state, language 
            FROM leads 
            LIMIT 5
        """))
        rows = result.fetchall()
        for row in rows:
            print(f"Lead {row[0]}: state={row[1]}, lang={row[2]}")

if __name__ == "__main__":
    asyncio.run(fix_lowercase_enums())
