"""
Direct database migration to add UPPERCASE enum values and update data.
This bypasses the ORM enum validation and works directly with PostgreSQL.
"""

import asyncio
import asyncpg
import os

async def migrate_enums():
    """Migrate enum values from lowercase to UPPERCASE by adding new values and updating data."""
    
    # Get database connection string from environment
    db_user = os.getenv("POSTGRES_USER", "artinrealty_user")
    db_pass = os.getenv("POSTGRES_PASSWORD", "your_secure_password_here")
    db_name = os.getenv("POSTGRES_DB", "artinrealty_db")
    db_host = os.getenv("DATABASE_HOST", "db")
    
    conn = await asyncpg.connect(
        user=db_user,
        password=db_pass,
        database=db_name,
        host=db_host
    )
    
    try:
        print("=" * 60)
        print("ENUM MIGRATION TO UPPERCASE")
        print("=" * 60)
        print("\nConnected to database successfully!")
        print("Starting migration...\n")
        
        # Start transaction
        async with conn.transaction():
            
            # 1. Add UPPERCASE values to Language enum
            print("Adding UPPERCASE values to Language enum...")
            await conn.execute("""
                DO $$ BEGIN
                    ALTER TYPE language ADD VALUE IF NOT EXISTS 'EN';
                    ALTER TYPE language ADD VALUE IF NOT EXISTS 'FA';
                    ALTER TYPE language ADD VALUE IF NOT EXISTS 'AR';
                    ALTER TYPE language ADD VALUE IF NOT EXISTS 'RU';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """)
            print("✓ UPPERCASE values added to Language enum")
            
            # 2. Add UPPERCASE values to ConversationState enum
            print("\nAdding UPPERCASE values to ConversationState enum...")
            await conn.execute("""
                DO $$ BEGIN
                    ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'START';
                    ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'LANGUAGE_SELECT';
                    ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'COLLECTING_NAME';
                    ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'WARMUP';
                    ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'CAPTURE_CONTACT';
                    ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'SLOT_FILLING';
                    ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'VALUE_PROPOSITION';
                    ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'HARD_GATE';
                    ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'ENGAGEMENT';
                    ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'HANDOFF_SCHEDULE';
                    ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'HANDOFF_URGENT';
                    ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'COMPLETED';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """)
            print("✓ UPPERCASE values added to ConversationState enum")
            
            # 3. Add UPPERCASE values to LeadStatus enum
            print("\nAdding UPPERCASE values to LeadStatus enum...")
            await conn.execute("""
                DO $$ BEGIN
                    ALTER TYPE leadstatus ADD VALUE IF NOT EXISTS 'NEW';
                    ALTER TYPE leadstatus ADD VALUE IF NOT EXISTS 'CONTACTED';
                    ALTER TYPE leadstatus ADD VALUE IF NOT EXISTS 'QUALIFIED';
                    ALTER TYPE leadstatus ADD VALUE IF NOT EXISTS 'VIEWING_SCHEDULED';
                    ALTER TYPE leadstatus ADD VALUE IF NOT EXISTS 'NEGOTIATING';
                    ALTER TYPE leadstatus ADD VALUE IF NOT EXISTS 'CLOSED_WON';
                    ALTER TYPE leadstatus ADD VALUE IF NOT EXISTS 'CLOSED_LOST';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """)
            print("✓ UPPERCASE values added to LeadStatus enum")
            
            # 4. Add UPPERCASE values to PaymentMethod enum
            print("\nAdding UPPERCASE values to PaymentMethod enum...")
            await conn.execute("""
                DO $$ BEGIN
                    ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'CASH';
                    ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'INSTALLMENT';
                    ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'MORTGAGE';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """)
            print("✓ UPPERCASE values added to PaymentMethod enum")
            
            # 5. Add UPPERCASE values to Purpose enum
            print("\nAdding UPPERCASE values to Purpose enum...")
            await conn.execute("""
                DO $$ BEGIN
                    ALTER TYPE purpose ADD VALUE IF NOT EXISTS 'INVESTMENT';
                    ALTER TYPE purpose ADD VALUE IF NOT EXISTS 'LIVING';
                    ALTER TYPE purpose ADD VALUE IF NOT EXISTS 'RESIDENCY';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """)
            print("✓ UPPERCASE values added to Purpose enum")
            
            # 6. Add UPPERCASE values to AppointmentType enum
            print("\nAdding UPPERCASE values to AppointmentType enum...")
            await conn.execute("""
                DO $$ BEGIN
                    ALTER TYPE appointmenttype ADD VALUE IF NOT EXISTS 'ONLINE';
                    ALTER TYPE appointmenttype ADD VALUE IF NOT EXISTS 'OFFICE';
                    ALTER TYPE appointmenttype ADD VALUE IF NOT EXISTS 'VIEWING';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """)
            print("✓ UPPERCASE values added to AppointmentType enum")
            
            # 7. Add UPPERCASE values to DayOfWeek enum
            print("\nAdding UPPERCASE values to DayOfWeek enum...")
            await conn.execute("""
                DO $$ BEGIN
                    ALTER TYPE dayofweek ADD VALUE IF NOT EXISTS 'MONDAY';
                    ALTER TYPE dayofweek ADD VALUE IF NOT EXISTS 'TUESDAY';
                    ALTER TYPE dayofweek ADD VALUE IF NOT EXISTS 'WEDNESDAY';
                    ALTER TYPE dayofweek ADD VALUE IF NOT EXISTS 'THURSDAY';
                    ALTER TYPE dayofweek ADD VALUE IF NOT EXISTS 'FRIDAY';
                    ALTER TYPE dayofweek ADD VALUE IF NOT EXISTS 'SATURDAY';
                    ALTER TYPE dayofweek ADD VALUE IF NOT EXISTS 'SUNDAY';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """)
            print("✓ UPPERCASE values added to DayOfWeek enum")
            
            # 8. Add UPPERCASE values to SubscriptionStatus enum
            print("\nAdding UPPERCASE values to SubscriptionStatus enum...")
            await conn.execute("""
                DO $$ BEGIN
                    ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'TRIAL';
                    ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'ACTIVE';
                    ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'SUSPENDED';
                    ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'CANCELLED';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """)
            print("✓ UPPERCASE values added to SubscriptionStatus enum")
            
            # 9. Add UPPERCASE values to PainPoint enum
            print("\nAdding UPPERCASE values to PainPoint enum...")
            await conn.execute("""
                DO $$ BEGIN
                    ALTER TYPE painpoint ADD VALUE IF NOT EXISTS 'INFLATION_RISK';
                    ALTER TYPE painpoint ADD VALUE IF NOT EXISTS 'VISA_INSECURITY';
                    ALTER TYPE painpoint ADD VALUE IF NOT EXISTS 'RENTAL_INSTABILITY';
                    ALTER TYPE painpoint ADD VALUE IF NOT EXISTS 'FOMO_MARKET';
                    ALTER TYPE painpoint ADD VALUE IF NOT EXISTS 'FAMILY_PRESSURE';
                    ALTER TYPE painpoint ADD VALUE IF NOT EXISTS 'FUTURE_UNCERTAINTY';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """)
            print("✓ UPPERCASE values added to PainPoint enum")
            
            print("\n" + "=" * 60)
            print("Now updating data to use UPPERCASE values...")
            print("=" * 60 + "\n")
            
            # Update Language in leads
            result = await conn.execute("""
                UPDATE leads SET language = UPPER(language::text)::language
                WHERE language::text IN ('en', 'fa', 'ar', 'ru')
            """)
            print(f"✓ Updated {result.split()[-1]} Language values in leads")
            
            # Update ConversationState in leads
            result = await conn.execute("""
                UPDATE leads SET conversation_state = UPPER(conversation_state::text)::conversationstate
                WHERE conversation_state::text IN (
                    'start', 'language_select', 'collecting_name', 'warmup',
                    'capture_contact', 'slot_filling', 'value_proposition',
                    'hard_gate', 'engagement', 'handoff_schedule',
                    'handoff_urgent', 'completed'
                )
            """)
            print(f"✓ Updated {result.split()[-1]} ConversationState values in leads")
            
            # Update LeadStatus in leads
            result = await conn.execute("""
                UPDATE leads SET status = UPPER(status::text)::leadstatus
                WHERE status::text IN (
                    'new', 'contacted', 'qualified', 'viewing_scheduled',
                    'negotiating', 'closed_won', 'closed_lost'
                )
            """)
            print(f"✓ Updated {result.split()[-1]} LeadStatus values in leads")
            
            # Update PaymentMethod in leads
            result = await conn.execute("""
                UPDATE leads SET payment_method = UPPER(payment_method::text)::paymentmethod
                WHERE payment_method::text IN ('cash', 'installment', 'mortgage')
            """)
            print(f"✓ Updated {result.split()[-1]} PaymentMethod values in leads")
            
            # Update Purpose in leads
            result = await conn.execute("""
                UPDATE leads SET purpose = UPPER(purpose::text)::purpose
                WHERE purpose::text IN ('investment', 'living', 'residency')
            """)
            print(f"✓ Updated {result.split()[-1]} Purpose values in leads")
            
            # Update PainPoint in leads
            result = await conn.execute("""
                UPDATE leads SET pain_point = UPPER(pain_point::text)::painpoint
                WHERE pain_point::text IN (
                    'inflation_risk', 'visa_insecurity', 'rental_instability',
                    'fomo_market', 'family_pressure', 'future_uncertainty'
                )
            """)
            print(f"✓ Updated {result.split()[-1]} PainPoint values in leads")
            
            # Update AppointmentType in appointments
            result = await conn.execute("""
                UPDATE appointments SET appointment_type = UPPER(appointment_type::text)::appointmenttype
                WHERE appointment_type::text IN ('online', 'office', 'viewing')
            """)
            print(f"✓ Updated {result.split()[-1]} AppointmentType values in appointments")
            
            # Update DayOfWeek in schedule_slots
            result = await conn.execute("""
                UPDATE schedule_slots SET day_of_week = UPPER(day_of_week::text)::dayofweek
                WHERE day_of_week::text IN (
                    'monday', 'tuesday', 'wednesday', 'thursday',
                    'friday', 'saturday', 'sunday'
                )
            """)
            print(f"✓ Updated {result.split()[-1]} DayOfWeek values in schedule_slots")
            
            # Update SubscriptionStatus in tenants
            result = await conn.execute("""
                UPDATE tenants SET subscription_status = UPPER(subscription_status::text)::subscriptionstatus
                WHERE subscription_status::text IN ('trial', 'active', 'suspended', 'cancelled')
            """)
            print(f"✓ Updated {result.split()[-1]} SubscriptionStatus values in tenants")
            
            # Update Language in tenants
            result = await conn.execute("""
                UPDATE tenants SET default_language = UPPER(default_language::text)::language
                WHERE default_language::text IN ('en', 'fa', 'ar', 'ru')
            """)
            print(f"✓ Updated {result.split()[-1]} Language values in tenants")
            
        print("\n" + "=" * 60)
        print("✅ ALL ENUM VALUES SUCCESSFULLY MIGRATED TO UPPERCASE!")
        print("=" * 60)
        print("\nMigration completed successfully. All changes committed.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    asyncio.run(migrate_enums())
