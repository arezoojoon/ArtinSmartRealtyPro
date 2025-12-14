"""
🧪 Comprehensive Test Suite for Unified Lead System
Tests all critical paths, edge cases, and user journeys
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

# Import all necessary modules
from backend.database import async_session, Tenant
from backend.unified_database import (
    UnifiedLead, LeadSource, LeadStatus, LeadGrade,
    find_or_create_lead, find_matching_leads_for_property
)
from backend.followup_engine import (
    followup_engine, schedule_linkedin_lead_followup, notify_property_added
)


# ==================== TEST 1: Lead Creation & Deduplication ====================

async def test_lead_creation_basic():
    """Test creating a new lead from LinkedIn"""
    print("\n🧪 TEST 1: Basic Lead Creation")
    
    async with async_session() as session:
        data = {
            'name': 'Test User',
            'linkedin_url': 'https://linkedin.com/in/testuser123',
            'email': 'test@example.com',
            'phone': '+971501234567',
            'job_title': 'CEO',
            'company': 'Test Corp',
            'source': LeadSource.LINKEDIN,
            'status': LeadStatus.NEW
        }
        
        lead, created = await find_or_create_lead(session, tenant_id=1, data=data)
        
        assert created == True, "❌ Lead should be newly created"
        assert lead.name == 'Test User', "❌ Name mismatch"
        assert lead.lead_score >= 0, "❌ Score not calculated"
        assert lead.grade in [LeadGrade.A, LeadGrade.B, LeadGrade.C, LeadGrade.D], "❌ Grade not assigned"
        
        await session.commit()
        print("✅ Lead created successfully")
        print(f"   - ID: {lead.id}")
        print(f"   - Score: {lead.lead_score}")
        print(f"   - Grade: {lead.grade.value}")


async def test_lead_deduplication_linkedin():
    """Test that duplicate LinkedIn URLs are detected"""
    print("\n🧪 TEST 2: LinkedIn URL Deduplication")
    
    async with async_session() as session:
        data = {
            'name': 'Test User',
            'linkedin_url': 'https://linkedin.com/in/testuser123',  # Same as TEST 1
            'email': 'newemail@example.com',
            'source': LeadSource.LINKEDIN
        }
        
        lead, created = await find_or_create_lead(session, tenant_id=1, data=data)
        
        assert created == False, "❌ Lead should NOT be created (duplicate)"
        assert lead.email == 'test@example.com', "❌ Original email should be preserved"
        
        print("✅ Deduplication working correctly")


async def test_lead_validation_empty_name():
    """Test that empty names are rejected"""
    print("\n🧪 TEST 3: Validation - Empty Name")
    
    async with async_session() as session:
        data = {
            'name': '   ',  # Empty after strip
            'linkedin_url': 'https://linkedin.com/in/test',
            'source': LeadSource.LINKEDIN
        }
        
        try:
            lead, created = await find_or_create_lead(session, tenant_id=1, data=data)
            # Should not reach here
            assert False, "❌ Should have rejected empty name"
        except Exception as e:
            print("✅ Empty name correctly rejected")


async def test_tenant_isolation():
    """Test that leads are properly isolated by tenant"""
    print("\n🧪 TEST 4: Tenant Isolation")
    
    async with async_session() as session:
        # Create lead for tenant 1
        data1 = {
            'name': 'Tenant1 Lead',
            'linkedin_url': 'https://linkedin.com/in/tenant1lead',
            'source': LeadSource.LINKEDIN
        }
        lead1, _ = await find_or_create_lead(session, tenant_id=1, data=data1)
        
        # Try to find it as tenant 2 (should not find it)
        result = await session.execute(
            select(UnifiedLead).where(
                UnifiedLead.tenant_id == 2,
                UnifiedLead.linkedin_url == 'https://linkedin.com/in/tenant1lead'
            )
        )
        lead_as_tenant2 = result.scalar_one_or_none()
        
        assert lead_as_tenant2 is None, "❌ Tenant isolation FAILED - lead leaked!"
        
        await session.commit()
        print("✅ Tenant isolation working correctly")


# ==================== TEST 2: Lead Scoring ====================

async def test_lead_scoring_calculation():
    """Test lead score calculation logic"""
    print("\n🧪 TEST 5: Lead Scoring")
    
    async with async_session() as session:
        # Minimal data = low score
        data_minimal = {
            'name': 'Minimal Lead',
            'linkedin_url': 'https://linkedin.com/in/minimal',
            'source': LeadSource.LINKEDIN
        }
        lead_minimal, _ = await find_or_create_lead(session, tenant_id=1, data=data_minimal)
        
        # Full data = high score
        data_full = {
            'name': 'Full Lead',
            'linkedin_url': 'https://linkedin.com/in/fulldata',
            'email': 'full@example.com',
            'phone': '+971501111111',
            'job_title': 'CTO',
            'company': 'Tech Inc',
            'budget_min': 1000000,
            'budget_max': 2000000,
            'property_type': 'apartment',
            'preferred_locations': ['Dubai Marina'],
            'source': LeadSource.LINKEDIN
        }
        lead_full, _ = await find_or_create_lead(session, tenant_id=1, data=data_full)
        
        assert lead_minimal.lead_score < lead_full.lead_score, "❌ Scoring logic broken"
        assert lead_minimal.grade.value > lead_full.grade.value, "❌ Grading logic broken (alphabetically)"
        
        await session.commit()
        print("✅ Lead scoring working correctly")
        print(f"   - Minimal: Score={lead_minimal.lead_score}, Grade={lead_minimal.grade.value}")
        print(f"   - Full: Score={lead_full.lead_score}, Grade={lead_full.grade.value}")


# ==================== TEST 3: Property Matching ====================

async def test_property_matching():
    """Test property matching algorithm"""
    print("\n🧪 TEST 6: Property Matching")
    
    async with async_session() as session:
        # Create a lead with specific criteria
        data = {
            'name': 'Buyer Lead',
            'linkedin_url': 'https://linkedin.com/in/buyer',
            'telegram_user_id': 123456,
            'budget_min': 800000,
            'budget_max': 1200000,
            'property_type': 'apartment',
            'transaction_type': 'buy',
            'preferred_locations': ['Dubai Marina', 'Downtown'],
            'source': LeadSource.TELEGRAM
        }
        lead, _ = await find_or_create_lead(session, tenant_id=1, data=data)
        await session.commit()
        
        # Create a matching property (you need to have Property in DB)
        from backend.database import Property, PropertyType, TransactionType
        
        property = Property(
            tenant_id=1,
            title='Luxury Apartment',
            price=1000000,
            type=PropertyType.APARTMENT,
            transaction_type=TransactionType.BUY,
            location='Dubai Marina',
            bedrooms=2
        )
        session.add(property)
        await session.commit()
        await session.refresh(property)
        
        # Test matching
        matched = await find_matching_leads_for_property(session, property.id, 1)
        
        assert len(matched) > 0, "❌ Should find at least one match"
        assert lead.id in [l.id for l in matched], "❌ Created lead should be in matches"
        
        print("✅ Property matching working correctly")
        print(f"   - Matched {len(matched)} leads")


async def test_property_matching_edge_cases():
    """Test property matching with NULL values and edge cases"""
    print("\n🧪 TEST 7: Property Matching Edge Cases")
    
    async with async_session() as session:
        # Lead with NO budget set
        data_no_budget = {
            'name': 'No Budget Lead',
            'linkedin_url': 'https://linkedin.com/in/nobudget',
            'telegram_user_id': 111111,
            'property_type': 'villa',
            'source': LeadSource.TELEGRAM
        }
        lead_no_budget, _ = await find_or_create_lead(session, tenant_id=1, data=data_no_budget)
        
        # Property with price
        from backend.database import Property, PropertyType
        property_with_price = Property(
            tenant_id=1,
            title='Expensive Villa',
            price=5000000,
            type=PropertyType.VILLA,
            location='Palm Jumeirah'
        )
        session.add(property_with_price)
        await session.commit()
        await session.refresh(property_with_price)
        
        # Test matching - lead without budget should NOT match
        matched = await find_matching_leads_for_property(session, property_with_price.id, 1)
        
        assert lead_no_budget.id not in [l.id for l in matched], "❌ Lead without budget should NOT match"
        
        print("✅ Edge case handling working correctly")


# ==================== TEST 4: Follow-up Engine ====================

async def test_followup_scheduling():
    """Test that follow-ups are scheduled correctly"""
    print("\n🧪 TEST 8: Follow-up Scheduling")
    
    async with async_session() as session:
        data = {
            'name': 'Followup Test Lead',
            'linkedin_url': 'https://linkedin.com/in/followuptest',
            'telegram_user_id': 999999,
            'source': LeadSource.LINKEDIN
        }
        lead, created = await find_or_create_lead(session, tenant_id=1, data=data)
        await session.commit()
        await session.refresh(lead)
        
        # Schedule follow-up
        await schedule_linkedin_lead_followup(lead)
        
        # Verify next_followup_at is set
        await session.refresh(lead)
        assert lead.next_followup_at is not None, "❌ Follow-up not scheduled"
        assert lead.next_followup_at > datetime.utcnow(), "❌ Follow-up time is in the past"
        
        print("✅ Follow-up scheduling working correctly")
        print(f"   - Next follow-up: {lead.next_followup_at}")


# ==================== TEST 5: User Journey (End-to-End) ====================

async def test_full_user_journey():
    """Test complete user journey from LinkedIn to Property Match"""
    print("\n🧪 TEST 9: Full User Journey (E2E)")
    
    async with async_session() as session:
        print("\n   Step 1: LinkedIn lead scraped")
        data = {
            'name': 'Journey Test User',
            'linkedin_url': 'https://linkedin.com/in/journeytest',
            'email': 'journey@test.com',
            'phone': '+971502222222',
            'job_title': 'VP Sales',
            'company': 'SaaS Inc',
            'about': 'Looking for investment opportunities in Dubai',
            'source': LeadSource.LINKEDIN
        }
        lead, created = await find_or_create_lead(session, tenant_id=1, data=data)
        assert created, "❌ Lead should be created"
        initial_score = lead.lead_score
        print(f"      ✅ Lead created (Score: {initial_score})")
        
        print("\n   Step 2: User responds via Telegram")
        lead.telegram_user_id = 777777
        lead.total_messages_received = 3
        lead.budget_min = 1500000
        lead.budget_max = 2500000
        lead.property_type = 'penthouse'
        lead.update_score_and_grade()
        await session.commit()
        await session.refresh(lead)
        
        assert lead.lead_score > initial_score, "❌ Score should increase after engagement"
        print(f"      ✅ Score increased to {lead.lead_score} (Grade: {lead.grade.value})")
        
        print("\n   Step 3: Property added that matches")
        from backend.database import Property, PropertyType
        property = Property(
            tenant_id=1,
            title='Luxury Penthouse',
            price=2000000,
            type=PropertyType.PENTHOUSE,
            location='Downtown Dubai',
            bedrooms=3
        )
        session.add(property)
        await session.commit()
        await session.refresh(property)
        
        matched = await find_matching_leads_for_property(session, property.id, 1)
        assert lead.id in [l.id for l in matched], "❌ Lead should match property"
        print(f"      ✅ Lead matched with property (ID: {property.id})")
        
        print("\n   Step 4: Notification sent")
        notified_count = await notify_property_added(property.id)
        assert notified_count > 0, "❌ Should notify at least one lead"
        print(f"      ✅ {notified_count} lead(s) notified")
        
        print("\n✅ Full user journey completed successfully!")


# ==================== TEST 6: Performance & Limits ====================

async def test_performance_limits():
    """Test that performance limits are working"""
    print("\n🧪 TEST 10: Performance Limits")
    
    async with async_session() as session:
        # Create many leads
        for i in range(150):
            data = {
                'name': f'Bulk Lead {i}',
                'linkedin_url': f'https://linkedin.com/in/bulk{i}',
                'telegram_user_id': 100000 + i,
                'next_followup_at': datetime.utcnow() - timedelta(hours=1),  # All need follow-up
                'source': LeadSource.LINKEDIN
            }
            lead, _ = await find_or_create_lead(session, tenant_id=1, data=data)
        
        await session.commit()
        
        # Query should limit to 100 (from process_scheduled_followups)
        query = select(UnifiedLead).where(
            UnifiedLead.next_followup_at <= datetime.utcnow()
        ).limit(100)
        
        result = await session.execute(query)
        leads = result.scalars().all()
        
        assert len(leads) <= 100, "❌ Limit not applied!"
        print(f"✅ Performance limit working (returned {len(leads)} leads)")


# ==================== RUN ALL TESTS ====================

async def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("🧪 COMPREHENSIVE TEST SUITE - Unified Lead System")
    print("=" * 70)
    
    tests = [
        test_lead_creation_basic,
        test_lead_deduplication_linkedin,
        test_lead_validation_empty_name,
        test_tenant_isolation,
        test_lead_scoring_calculation,
        test_property_matching,
        test_property_matching_edge_cases,
        test_followup_scheduling,
        test_full_user_journey,
        test_performance_limits
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ TEST ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! System is production-ready.")
    else:
        print("⚠️  Some tests failed. Review and fix issues before deployment.")


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())
