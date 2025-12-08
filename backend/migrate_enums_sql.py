"""
SQL-based enum migration using raw SQL commands.
Run this script to add UPPERCASE enum values and migrate existing data.
"""

import asyncio
from sqlalchemy import text
from database import engine

async def add_enum_values():
    """Step 1: Add UPPERCASE enum values to PostgreSQL enums"""
    
    print("=" * 60)
    print("ENUM MIGRATION TO UPPERCASE - STEP 1")
    print("=" * 60)
    print("\nAdding UPPERCASE enum values to database...\n")
    
    async with engine.connect() as conn:
        enum_updates = [
            ("Language", "language", ["EN", "FA", "AR", "RU"]),
            ("ConversationState", "conversationstate", [
                "START", "LANGUAGE_SELECT", "COLLECTING_NAME", "WARMUP",
                "CAPTURE_CONTACT", "SLOT_FILLING", "VALUE_PROPOSITION",
                "HARD_GATE", "ENGAGEMENT", "HANDOFF_SCHEDULE",
                "HANDOFF_URGENT", "COMPLETED"
            ]),
            ("LeadStatus", "leadstatus", [
                "NEW", "CONTACTED", "QUALIFIED", "VIEWING_SCHEDULED",
                "NEGOTIATING", "CLOSED_WON", "CLOSED_LOST"
            ]),
            ("PaymentMethod", "paymentmethod", ["CASH", "INSTALLMENT", "MORTGAGE"]),
            ("Purpose", "purpose", ["INVESTMENT", "LIVING", "RESIDENCY"]),
            ("AppointmentType", "appointmenttype", ["ONLINE", "OFFICE", "VIEWING"]),
            ("DayOfWeek", "dayofweek", [
                "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY",
                "FRIDAY", "SATURDAY", "SUNDAY"
            ]),
            ("SubscriptionStatus", "subscriptionstatus", ["TRIAL", "ACTIVE", "SUSPENDED", "CANCELLED"]),
        ]
        
        for enum_name, enum_type, values in enum_updates:
            print(f"Adding UPPERCASE values to {enum_name} enum...")
            for value in values:
                try:
                    await conn.execute(text(f"ALTER TYPE {enum_type} ADD VALUE IF NOT EXISTS '{value}'"))
                    await conn.commit()
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        print(f"  Warning for {value}: {e}")
            print(f"✓ {enum_name} enum updated")
    
    print("\n✅ Step 1 completed: All UPPERCASE enum values added!\n")

async def update_data():
    """Step 2: Update existing data to use UPPERCASE enum values"""
    
    print("=" * 60)
    print("ENUM MIGRATION TO UPPERCASE - STEP 2")
    print("=" * 60)
    print("\nUpdating existing data to use UPPERCASE values...\n")
    
    async with engine.begin() as conn:
        data_updates = [
            ("leads.language", """
                UPDATE leads 
                SET language = CASE language::text
                    WHEN 'en' THEN 'EN'
                    WHEN 'fa' THEN 'FA'
                    WHEN 'ar' THEN 'AR'
                    WHEN 'ru' THEN 'RU'
                    ELSE language::text
                END::language
                WHERE language::text IN ('en', 'fa', 'ar', 'ru')
            """),
            ("leads.conversation_state", """
                UPDATE leads 
                SET conversation_state = CASE conversation_state::text
                    WHEN 'start' THEN 'START'
                    WHEN 'language_select' THEN 'LANGUAGE_SELECT'
                    WHEN 'collecting_name' THEN 'COLLECTING_NAME'
                    WHEN 'warmup' THEN 'WARMUP'
                    WHEN 'capture_contact' THEN 'CAPTURE_CONTACT'
                    WHEN 'slot_filling' THEN 'SLOT_FILLING'
                    WHEN 'value_proposition' THEN 'VALUE_PROPOSITION'
                    WHEN 'hard_gate' THEN 'HARD_GATE'
                    WHEN 'engagement' THEN 'ENGAGEMENT'
                    WHEN 'handoff_schedule' THEN 'HANDOFF_SCHEDULE'
                    WHEN 'handoff_urgent' THEN 'HANDOFF_URGENT'
                    WHEN 'completed' THEN 'COMPLETED'
                    ELSE conversation_state::text
                END::conversationstate
                WHERE conversation_state::text IN (
                    'start', 'language_select', 'collecting_name', 'warmup',
                    'capture_contact', 'slot_filling', 'value_proposition',
                    'hard_gate', 'engagement', 'handoff_schedule',
                    'handoff_urgent', 'completed'
                )
            """),
            ("leads.status", """
                UPDATE leads 
                SET status = CASE status::text
                    WHEN 'new' THEN 'NEW'
                    WHEN 'contacted' THEN 'CONTACTED'
                    WHEN 'qualified' THEN 'QUALIFIED'
                    WHEN 'viewing_scheduled' THEN 'VIEWING_SCHEDULED'
                    WHEN 'negotiating' THEN 'NEGOTIATING'
                    WHEN 'closed_won' THEN 'CLOSED_WON'
                    WHEN 'closed_lost' THEN 'CLOSED_LOST'
                    ELSE status::text
                END::leadstatus
                WHERE status::text IN (
                    'new', 'contacted', 'qualified', 'viewing_scheduled',
                    'negotiating', 'closed_won', 'closed_lost'
                )
            """),
            ("leads.payment_method", """
                UPDATE leads 
                SET payment_method = CASE payment_method::text
                    WHEN 'cash' THEN 'CASH'
                    WHEN 'installment' THEN 'INSTALLMENT'
                    WHEN 'mortgage' THEN 'MORTGAGE'
                    ELSE payment_method::text
                END::paymentmethod
                WHERE payment_method IS NOT NULL 
                AND payment_method::text IN ('cash', 'installment', 'mortgage')
            """),
            ("leads.purpose", """
                UPDATE leads 
                SET purpose = CASE purpose::text
                    WHEN 'investment' THEN 'INVESTMENT'
                    WHEN 'living' THEN 'LIVING'
                    WHEN 'residency' THEN 'RESIDENCY'
                    ELSE purpose::text
                END::purpose
                WHERE purpose IS NOT NULL
                AND purpose::text IN ('investment', 'living', 'residency')
            """),
            ("leads.pain_point", """
                UPDATE leads 
                SET pain_point = UPPER(pain_point)
                WHERE pain_point IS NOT NULL
            """),
            ("appointments.appointment_type", """
                UPDATE appointments 
                SET appointment_type = CASE appointment_type::text
                    WHEN 'online' THEN 'ONLINE'
                    WHEN 'office' THEN 'OFFICE'
                    WHEN 'viewing' THEN 'VIEWING'
                    ELSE appointment_type::text
                END::appointmenttype
                WHERE appointment_type::text IN ('online', 'office', 'viewing')
            """),
            ("tenants.subscription_status", """
                UPDATE tenants 
                SET subscription_status = CASE subscription_status::text
                    WHEN 'trial' THEN 'TRIAL'
                    WHEN 'active' THEN 'ACTIVE'
                    WHEN 'suspended' THEN 'SUSPENDED'
                    WHEN 'cancelled' THEN 'CANCELLED'
                    ELSE subscription_status::text
                END::subscriptionstatus
                WHERE subscription_status::text IN ('trial', 'active', 'suspended', 'cancelled')
            """),
            ("tenants.default_language", """
                UPDATE tenants 
                SET default_language = CASE default_language::text
                    WHEN 'en' THEN 'EN'
                    WHEN 'fa' THEN 'FA'
                    WHEN 'ar' THEN 'AR'
                    WHEN 'ru' THEN 'RU'
                    ELSE default_language::text
                END::language
                WHERE default_language::text IN ('en', 'fa', 'ar', 'ru')
            """),
        ]
        
        for field, update_sql in data_updates:
            try:
                result = await conn.execute(text(update_sql))
                rows_updated = result.rowcount if hasattr(result, 'rowcount') else 0
                print(f"✓ Updated {rows_updated} {field} values")
            except Exception as e:
                if "does not exist" in str(e):
                    print(f"⚠ Skipped {field} (table/column not found)")
                else:
                    raise
    
    print("\n✅ Step 2 completed: All data updated to UPPERCASE!\n")

async def migrate_enums():
    """Main migration function"""
    try:
        print("\n" + "=" * 60)
        print("STARTING ENUM MIGRATION TO UPPERCASE")
        print("=" * 60 + "\n")
        
        await add_enum_values()
        await update_data()
        
        print("=" * 60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nAll enum values have been migrated to UPPERCASE.")
        print("Your database is now ready to use with the updated schema.\n")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(migrate_enums())
