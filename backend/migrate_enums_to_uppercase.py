"""
Migration script to convert all enum values from lowercase to UPPERCASE in the database.
This needs to be run ONCE after deploying the UPPERCASE enum changes.
"""

import asyncio
from sqlalchemy import text
from database import get_db

async def migrate_enums_to_uppercase():
    """Convert all existing enum values from lowercase to UPPERCASE."""
    
    async for db in get_db():
        try:
            print("Starting enum migration to UPPERCASE...")
            
            # Update Language enum in leads table
            await db.execute(text("""
                UPDATE leads 
                SET language = UPPER(language)
                WHERE language IN ('en', 'fa', 'ar', 'ru')
            """))
            print("✓ Updated Language enum in leads table")
            
            # Update ConversationState enum in leads table
            await db.execute(text("""
                UPDATE leads 
                SET conversation_state = UPPER(conversation_state)
                WHERE conversation_state IN (
                    'start', 'language_select', 'collecting_name', 'warmup',
                    'capture_contact', 'slot_filling', 'value_proposition',
                    'hard_gate', 'engagement', 'handoff_schedule',
                    'handoff_urgent', 'completed'
                )
            """))
            print("✓ Updated ConversationState enum in leads table")
            
            # Update LeadStatus enum in leads table
            await db.execute(text("""
                UPDATE leads 
                SET status = UPPER(status)
                WHERE status IN (
                    'new', 'contacted', 'qualified', 'viewing_scheduled',
                    'negotiating', 'closed_won', 'closed_lost'
                )
            """))
            print("✓ Updated LeadStatus enum in leads table")
            
            # Update PaymentMethod enum in leads table
            await db.execute(text("""
                UPDATE leads 
                SET payment_method = UPPER(payment_method)
                WHERE payment_method IN ('cash', 'installment', 'mortgage')
            """))
            print("✓ Updated PaymentMethod enum in leads table")
            
            # Update Purpose enum in leads table
            await db.execute(text("""
                UPDATE leads 
                SET purpose = UPPER(purpose)
                WHERE purpose IN ('investment', 'living', 'residency')
            """))
            print("✓ Updated Purpose enum in leads table")
            
            # Update PainPoint enum in leads table
            await db.execute(text("""
                UPDATE leads 
                SET pain_point = UPPER(pain_point)
                WHERE pain_point IN (
                    'inflation_risk', 'visa_insecurity', 'rental_instability',
                    'fomo_market', 'family_pressure', 'future_uncertainty'
                )
            """))
            print("✓ Updated PainPoint enum in leads table")
            
            # Update AppointmentType enum in appointments table
            await db.execute(text("""
                UPDATE appointments 
                SET appointment_type = UPPER(appointment_type)
                WHERE appointment_type IN ('online', 'office', 'viewing')
            """))
            print("✓ Updated AppointmentType enum in appointments table")
            
            # Update DayOfWeek enum in schedule_slots table
            await db.execute(text("""
                UPDATE schedule_slots 
                SET day_of_week = UPPER(day_of_week)
                WHERE day_of_week IN (
                    'monday', 'tuesday', 'wednesday', 'thursday',
                    'friday', 'saturday', 'sunday'
                )
            """))
            print("✓ Updated DayOfWeek enum in schedule_slots table")
            
            # Update SubscriptionStatus enum in tenants table
            await db.execute(text("""
                UPDATE tenants 
                SET subscription_status = UPPER(subscription_status)
                WHERE subscription_status IN ('trial', 'active', 'suspended', 'cancelled')
            """))
            print("✓ Updated SubscriptionStatus enum in tenants table")
            
            # Update Language enum in tenants table
            await db.execute(text("""
                UPDATE tenants 
                SET default_language = UPPER(default_language)
                WHERE default_language IN ('en', 'fa', 'ar', 'ru')
            """))
            print("✓ Updated Language enum in tenants table")
            
            # Commit all changes
            await db.commit()
            print("\n✅ All enum values successfully migrated to UPPERCASE!")
            print("Migration completed successfully.")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Migration failed: {e}")
            raise
        finally:
            break  # Only need one db session

if __name__ == "__main__":
    print("=" * 60)
    print("ENUM MIGRATION TO UPPERCASE")
    print("=" * 60)
    print("\nThis script will update all enum values in the database")
    print("from lowercase to UPPERCASE to match the new schema.\n")
    
    asyncio.run(migrate_enums_to_uppercase())
