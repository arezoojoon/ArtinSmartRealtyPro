"""
SQL-based enum migration using raw SQL commands.
Run this script to add UPPERCASE enum values and migrate existing data.
"""

import asyncio
from sqlalchemy import text
from database import engine

async def migrate_enums():
    """Migrate enum values from lowercase to UPPERCASE by adding new values and updating data."""
    
    async with engine.begin() as conn:
        try:
            print("=" * 60)
            print("ENUM MIGRATION TO UPPERCASE")
            print("=" * 60)
            print("\nConnected to database successfully!")
            print("Starting migration...\n")
            
            # We need to use a separate connection for each ALTER TYPE because
            # PostgreSQL doesn't allow ALTER TYPE in transactions
            print("Step 1: Adding UPPERCASE enum values (this may take a moment)...\n")
            
            # For each enum type, we'll add the UPPERCASE values
            # Note: We use DO blocks to handle "already exists" errors gracefully
            
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
                ("PainPoint", "painpoint", [
                    "INFLATION_RISK", "VISA_INSECURITY", "RENTAL_INSTABILITY",
                    "FOMO_MARKET", "FAMILY_PRESSURE", "FUTURE_UNCERTAINTY"
                ]),
            ]
            
            for enum_name, enum_type, values in enum_updates:
                print(f"Adding UPPERCASE values to {enum_name} enum...")
                for value in values:
                    try:
                        # We need to execute each ALTER TYPE outside of a transaction
                        await conn.execute(text(f"ALTER TYPE {enum_type} ADD VALUE IF NOT EXISTS '{value}'"))
                        await conn.commit()
                    except Exception as e:
                        if "already exists" not in str(e):
                            print(f"  Warning for {value}: {e}")
                        await conn.rollback()
                print(f"✓ {enum_name} enum updated")
        
        # Step 2: Update data with a fresh connection
        print("\n" + "=" * 60)
        print("Step 2: Updating data to use UPPERCASE values...")
        print("=" * 60 + "\n")
        
        async with engine.begin() as conn:
            
            # Now update the data - these need to be done carefully
            data_updates = [
                ("leads.language", "Language", """
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
                ("leads.conversation_state", "ConversationState", """
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
                ("leads.status", "LeadStatus", """
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
                ("leads.payment_method", "PaymentMethod", """
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
                ("leads.purpose", "Purpose", """
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
                ("leads.pain_point", "PainPoint", """
                    UPDATE leads 
                    SET pain_point = CASE pain_point::text
                        WHEN 'inflation_risk' THEN 'INFLATION_RISK'
                        WHEN 'visa_insecurity' THEN 'VISA_INSECURITY'
                        WHEN 'rental_instability' THEN 'RENTAL_INSTABILITY'
                        WHEN 'fomo_market' THEN 'FOMO_MARKET'
                        WHEN 'family_pressure' THEN 'FAMILY_PRESSURE'
                        WHEN 'future_uncertainty' THEN 'FUTURE_UNCERTAINTY'
                        ELSE pain_point::text
                    END::painpoint
                    WHERE pain_point IS NOT NULL
                    AND pain_point::text IN (
                        'inflation_risk', 'visa_insecurity', 'rental_instability',
                        'fomo_market', 'family_pressure', 'future_uncertainty'
                    )
                """),
                ("appointments.appointment_type", "AppointmentType", """
                    UPDATE appointments 
                    SET appointment_type = CASE appointment_type::text
                        WHEN 'online' THEN 'ONLINE'
                        WHEN 'office' THEN 'OFFICE'
                        WHEN 'viewing' THEN 'VIEWING'
                        ELSE appointment_type::text
                    END::appointmenttype
                    WHERE appointment_type::text IN ('online', 'office', 'viewing')
                """),
                ("schedule_slots.day_of_week", "DayOfWeek", """
                    UPDATE schedule_slots 
                    SET day_of_week = CASE day_of_week::text
                        WHEN 'monday' THEN 'MONDAY'
                        WHEN 'tuesday' THEN 'TUESDAY'
                        WHEN 'wednesday' THEN 'WEDNESDAY'
                        WHEN 'thursday' THEN 'THURSDAY'
                        WHEN 'friday' THEN 'FRIDAY'
                        WHEN 'saturday' THEN 'SATURDAY'
                        WHEN 'sunday' THEN 'SUNDAY'
                        ELSE day_of_week::text
                    END::dayofweek
                    WHERE day_of_week::text IN (
                        'monday', 'tuesday', 'wednesday', 'thursday',
                        'friday', 'saturday', 'sunday'
                    )
                """),
                ("tenants.subscription_status", "SubscriptionStatus", """
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
                ("tenants.default_language", "Language", """
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
            
            for field, enum_name, update_sql in data_updates:
                result = await conn.execute(text(update_sql))
                rows_updated = result.rowcount if hasattr(result, 'rowcount') else 0
                print(f"✓ Updated {rows_updated} {field} values to {enum_name}")
            
            print("\n" + "=" * 60)
            print("✅ ALL ENUM VALUES SUCCESSFULLY MIGRATED TO UPPERCASE!")
            print("=" * 60)
            print("\nMigration completed successfully. All changes committed.")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(migrate_enums())
