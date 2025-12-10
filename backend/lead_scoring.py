"""
Lead Scoring Engine - Sales Intelligence System
Calculates lead score (0-100) and temperature (burning/hot/warm/cold)
Based on engagement metrics + qualification data
"""

from typing import Dict, Tuple
from database import Lead, ConversationState


def calculate_lead_score(lead: Lead) -> int:
    """
    Calculate lead score from 0-100 based on:
    1. Engagement (40 points max)
    2. Qualification (40 points max)
    3. Recency (20 points max)
    
    Returns:
        int: Score from 0-100
    """
    score = 0
    
    # ===== ENGAGEMENT SCORING (40 points) =====
    engagement_score = 0
    
    # QR scans (worth 3 points each, max 15)
    engagement_score += min(lead.qr_scan_count * 3, 15)
    
    # Catalog views (worth 2 points each, max 10)
    engagement_score += min(lead.catalog_views * 2, 10)
    
    # Messages (worth 1 point each, max 10)
    engagement_score += min(lead.messages_count, 10)
    
    # Voice message sent (5 bonus points)
    if lead.voice_transcript:
        engagement_score += 5
    
    score += min(engagement_score, 40)
    
    # ===== QUALIFICATION SCORING (40 points) =====
    qualification_score = 0
    
    # Has phone number (10 points - highest intent)
    if lead.phone:
        qualification_score += 10
    
    # Has budget defined (10 points)
    if lead.budget_max or lead.budget_min:
        qualification_score += 10
    
    # Transaction type selected (5 points)
    if lead.transaction_type:
        qualification_score += 5
    
    # Property type selected (5 points)
    if lead.property_type:
        qualification_score += 5
    
    # Location specified (5 points)
    if lead.preferred_location or lead.preferred_locations:
        qualification_score += 5
    
    # Payment method defined (5 points)
    if lead.payment_method:
        qualification_score += 5
    
    score += min(qualification_score, 40)
    
    # ===== RECENCY SCORING (20 points) =====
    if lead.last_interaction:
        from datetime import datetime, timedelta
        hours_since_interaction = (datetime.utcnow() - lead.last_interaction).total_seconds() / 3600
        
        if hours_since_interaction < 1:
            score += 20  # Last hour = HOT
        elif hours_since_interaction < 6:
            score += 15  # Last 6 hours
        elif hours_since_interaction < 24:
            score += 10  # Last 24 hours
        elif hours_since_interaction < 72:
            score += 5   # Last 3 days
        # else: 0 points for older leads
    
    return min(score, 100)


def get_temperature(score: int) -> str:
    """
    Convert lead score to temperature category.
    
    Args:
        score: Lead score (0-100)
    
    Returns:
        str: "burning", "hot", "warm", or "cold"
    """
    if score >= 70:
        return "burning"  # 🔥 Immediate action needed
    elif score >= 50:
        return "hot"      # 🌶️ High priority
    elif score >= 25:
        return "warm"     # ☀️ Follow up soon
    else:
        return "cold"     # ❄️ Low priority


def update_lead_score(lead: Lead) -> Tuple[int, str]:
    """
    Update lead's score and temperature fields.
    
    Args:
        lead: Lead object to update
    
    Returns:
        Tuple[int, str]: (score, temperature)
    """
    score = calculate_lead_score(lead)
    temperature = get_temperature(score)
    
    lead.lead_score = score
    lead.temperature = temperature
    
    return score, temperature


def increment_engagement(lead: Lead, activity: str) -> None:
    """
    Increment engagement counter and recalculate score.
    
    Args:
        lead: Lead object
        activity: "qr_scan", "catalog_view", or "message"
    """
    if activity == "qr_scan":
        lead.qr_scan_count += 1
    elif activity == "catalog_view":
        lead.catalog_views += 1
    elif activity == "message":
        lead.messages_count += 1
    
    # Update total interactions
    lead.total_interactions = (
        lead.qr_scan_count + 
        lead.catalog_views + 
        lead.messages_count
    )
    
    # Recalculate score
    update_lead_score(lead)


def get_scoring_breakdown(lead: Lead) -> Dict[str, any]:
    """
    Get detailed breakdown of how score was calculated.
    Useful for debugging/transparency.
    
    Returns:
        dict: Breakdown of scoring components
    """
    engagement = min(
        (lead.qr_scan_count * 3) +
        (lead.catalog_views * 2) +
        lead.messages_count +
        (5 if lead.voice_transcript else 0),
        40
    )
    
    qualification = 0
    if lead.phone:
        qualification += 10
    if lead.budget_max or lead.budget_min:
        qualification += 10
    if lead.transaction_type:
        qualification += 5
    if lead.property_type:
        qualification += 5
    if lead.preferred_location or lead.preferred_locations:
        qualification += 5
    if lead.payment_method:
        qualification += 5
    
    recency = 0
    if lead.last_interaction:
        from datetime import datetime
        hours = (datetime.utcnow() - lead.last_interaction).total_seconds() / 3600
        if hours < 1:
            recency = 20
        elif hours < 6:
            recency = 15
        elif hours < 24:
            recency = 10
        elif hours < 72:
            recency = 5
    
    return {
        "total_score": lead.lead_score,
        "temperature": lead.temperature,
        "breakdown": {
            "engagement": engagement,
            "qualification": qualification,
            "recency": recency
        },
        "metrics": {
            "qr_scans": lead.qr_scan_count,
            "catalog_views": lead.catalog_views,
            "messages": lead.messages_count,
            "has_phone": bool(lead.phone),
            "has_budget": bool(lead.budget_max or lead.budget_min),
            "has_voice": bool(lead.voice_transcript)
        }
    }
