"""
WhatsApp AI Sales Bot - Realty Flow State Machine
Defines conversation states and flow transitions for:
- Rent Flow
- Investment Flow
- Residency Flow
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class RealtyFlow(str, Enum):
    """Main intent flows"""
    RENT = "rent"
    INVESTMENT = "investment"
    RESIDENCY = "residency"
    NONE = "none"


class RealtyState(str, Enum):
    """Conversation states for the realty sales bot"""
    # Entry states
    ENTRY = "entry"
    LANGUAGE_SELECT = "language_select"
    INTENT_SELECT = "intent_select"
    
    # Rent Flow
    RENT_PROPERTY_TYPE = "rent_property_type"
    RENT_BUDGET = "rent_budget"
    RENT_AREA = "rent_area"
    RENT_RESULTS = "rent_results"
    
    # Investment Flow
    INVEST_TYPE = "invest_type"
    INVEST_BUDGET = "invest_budget"
    INVEST_RESULTS = "invest_results"
    
    # Residency Flow
    RESID_VISA_TYPE = "resid_visa_type"
    RESID_PROPERTY_TYPE = "resid_property_type"
    RESID_RESULTS = "resid_results"
    
    # Terminal states
    CONSULTATION = "consultation"
    COMPLETED = "completed"
    IGNORED = "ignored"


class PropertyCategory(str, Enum):
    """Property categories"""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    LAND = "land"


class VisaType(str, Enum):
    """UAE Visa types for residency"""
    TWO_YEAR = "2_year"           # 750,000 AED minimum
    GOLDEN_VISA = "golden_visa"    # 2,000,000 AED minimum


# ==================== BUDGET CONFIGURATIONS ====================

# Rent budget ranges (monthly AED)
RENT_BUDGET_RANGES = {
    0: (0, 5000, "Under 5,000 AED/month"),
    1: (5000, 10000, "5,000 - 10,000 AED/month"),
    2: (10000, 20000, "10,000 - 20,000 AED/month"),
    3: (20000, 50000, "20,000 - 50,000 AED/month"),
    4: (50000, None, "50,000+ AED/month"),
}

# Investment budget ranges (AED)
INVEST_BUDGET_RANGES = {
    0: (500000, 1000000, "500K - 1M AED"),
    1: (1000000, 2000000, "1M - 2M AED"),
    2: (2000000, 5000000, "2M - 5M AED"),
    3: (5000000, 10000000, "5M - 10M AED"),
    4: (10000000, None, "10M+ AED"),
}

# Residency minimum amounts
RESIDENCY_MINIMUMS = {
    VisaType.TWO_YEAR: 750000,
    VisaType.GOLDEN_VISA: 2000000,
}


# ==================== FLOW TRANSITIONS ====================

# State transitions map: current_state -> possible_next_states
STATE_TRANSITIONS = {
    RealtyState.ENTRY: [RealtyState.LANGUAGE_SELECT, RealtyState.IGNORED],
    RealtyState.LANGUAGE_SELECT: [RealtyState.INTENT_SELECT],
    RealtyState.INTENT_SELECT: [
        RealtyState.RENT_PROPERTY_TYPE,
        RealtyState.INVEST_TYPE,
        RealtyState.RESID_VISA_TYPE
    ],
    
    # Rent Flow
    RealtyState.RENT_PROPERTY_TYPE: [RealtyState.RENT_BUDGET, RealtyState.INTENT_SELECT],
    RealtyState.RENT_BUDGET: [RealtyState.RENT_AREA, RealtyState.INTENT_SELECT],
    RealtyState.RENT_AREA: [RealtyState.RENT_RESULTS, RealtyState.INTENT_SELECT],
    RealtyState.RENT_RESULTS: [RealtyState.CONSULTATION, RealtyState.INTENT_SELECT],
    
    # Investment Flow
    RealtyState.INVEST_TYPE: [RealtyState.INVEST_BUDGET, RealtyState.INTENT_SELECT],
    RealtyState.INVEST_BUDGET: [RealtyState.INVEST_RESULTS, RealtyState.INTENT_SELECT],
    RealtyState.INVEST_RESULTS: [RealtyState.CONSULTATION, RealtyState.INTENT_SELECT],
    
    # Residency Flow
    RealtyState.RESID_VISA_TYPE: [RealtyState.RESID_PROPERTY_TYPE, RealtyState.INTENT_SELECT],
    RealtyState.RESID_PROPERTY_TYPE: [RealtyState.RESID_RESULTS, RealtyState.INTENT_SELECT],
    RealtyState.RESID_RESULTS: [RealtyState.CONSULTATION, RealtyState.INTENT_SELECT],
    
    # Terminal
    RealtyState.CONSULTATION: [RealtyState.COMPLETED, RealtyState.INTENT_SELECT],
    RealtyState.COMPLETED: [RealtyState.INTENT_SELECT],
}


# ==================== SESSION DATA ====================

@dataclass
class RealtySession:
    """
    Session data structure for realty sales bot.
    Stored in Redis with 24h TTL.
    """
    phone: str
    profile_name: str
    entry_source: str = "deeplink"  # deeplink or direct
    language: str = "EN"
    current_state: str = RealtyState.ENTRY
    current_flow: Optional[str] = None
    
    # Collected preferences
    property_type: Optional[str] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    budget_index: Optional[int] = None
    location_preference: Optional[str] = None
    investment_type: Optional[str] = None
    visa_type: Optional[str] = None
    
    # Tracking
    created_at: Optional[str] = None
    last_activity: Optional[str] = None
    messages_count: int = 0
    properties_viewed: List[int] = None
    
    def __post_init__(self):
        if self.properties_viewed is None:
            self.properties_viewed = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        return {
            "phone": self.phone,
            "profile_name": self.profile_name,
            "entry_source": self.entry_source,
            "language": self.language,
            "current_state": self.current_state,
            "current_flow": self.current_flow or "",
            "property_type": self.property_type or "",
            "budget_min": str(self.budget_min) if self.budget_min else "",
            "budget_max": str(self.budget_max) if self.budget_max else "",
            "budget_index": str(self.budget_index) if self.budget_index is not None else "",
            "location_preference": self.location_preference or "",
            "investment_type": self.investment_type or "",
            "visa_type": self.visa_type or "",
            "created_at": self.created_at or "",
            "last_activity": self.last_activity or "",
            "messages_count": str(self.messages_count),
            "properties_viewed": ",".join(map(str, self.properties_viewed)),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "RealtySession":
        """Create from Redis hash data"""
        properties_viewed = []
        if data.get("properties_viewed"):
            properties_viewed = [int(x) for x in data["properties_viewed"].split(",") if x]
        
        return cls(
            phone=data.get("phone", ""),
            profile_name=data.get("profile_name", ""),
            entry_source=data.get("entry_source", "deeplink"),
            language=data.get("language", "EN"),
            current_state=data.get("current_state", RealtyState.ENTRY),
            current_flow=data.get("current_flow") or None,
            property_type=data.get("property_type") or None,
            budget_min=int(data["budget_min"]) if data.get("budget_min") else None,
            budget_max=int(data["budget_max"]) if data.get("budget_max") else None,
            budget_index=int(data["budget_index"]) if data.get("budget_index") else None,
            location_preference=data.get("location_preference") or None,
            investment_type=data.get("investment_type") or None,
            visa_type=data.get("visa_type") or None,
            created_at=data.get("created_at") or None,
            last_activity=data.get("last_activity") or None,
            messages_count=int(data.get("messages_count", 0)),
            properties_viewed=properties_viewed,
        )
    
    def reset_flow_data(self):
        """Reset collected data when returning to main menu"""
        self.current_flow = None
        self.property_type = None
        self.budget_min = None
        self.budget_max = None
        self.budget_index = None
        self.location_preference = None
        self.investment_type = None
        self.visa_type = None


# ==================== FLOW HANDLERS ====================

class FlowController:
    """
    Controls flow transitions and validates state changes.
    """
    
    @staticmethod
    def can_transition(from_state: RealtyState, to_state: RealtyState) -> bool:
        """Check if transition is allowed"""
        allowed = STATE_TRANSITIONS.get(from_state, [])
        return to_state in allowed or to_state == RealtyState.INTENT_SELECT
    
    @staticmethod
    def get_next_state(current_flow: RealtyFlow, current_state: RealtyState) -> RealtyState:
        """Get the next state in the current flow"""
        flow_sequences = {
            RealtyFlow.RENT: [
                RealtyState.RENT_PROPERTY_TYPE,
                RealtyState.RENT_BUDGET,
                RealtyState.RENT_AREA,
                RealtyState.RENT_RESULTS,
            ],
            RealtyFlow.INVESTMENT: [
                RealtyState.INVEST_TYPE,
                RealtyState.INVEST_BUDGET,
                RealtyState.INVEST_RESULTS,
            ],
            RealtyFlow.RESIDENCY: [
                RealtyState.RESID_VISA_TYPE,
                RealtyState.RESID_PROPERTY_TYPE,
                RealtyState.RESID_RESULTS,
            ],
        }
        
        sequence = flow_sequences.get(current_flow, [])
        if not sequence:
            return RealtyState.INTENT_SELECT
        
        try:
            current_index = sequence.index(current_state)
            if current_index < len(sequence) - 1:
                return sequence[current_index + 1]
            else:
                return RealtyState.CONSULTATION
        except ValueError:
            # Current state not in sequence, start from beginning
            return sequence[0] if sequence else RealtyState.INTENT_SELECT
    
    @staticmethod
    def get_flow_from_intent(intent: str) -> RealtyFlow:
        """Map intent selection to flow"""
        intent_lower = intent.lower()
        
        if "rent" in intent_lower or "اجاره" in intent_lower or "إيجار" in intent_lower or "аренд" in intent_lower:
            return RealtyFlow.RENT
        elif "invest" in intent_lower or "سرمایه" in intent_lower or "استثمار" in intent_lower or "инвест" in intent_lower:
            return RealtyFlow.INVESTMENT
        elif "resid" in intent_lower or "اقامت" in intent_lower or "إقامة" in intent_lower or "резидент" in intent_lower or "visa" in intent_lower or "ویزا" in intent_lower:
            return RealtyFlow.RESIDENCY
        
        return RealtyFlow.NONE
    
    @staticmethod
    def is_back_to_menu(message: str) -> bool:
        """Check if user wants to go back to main menu"""
        back_triggers = [
            "menu", "main", "back", "start",
            "منو", "منوی", "برگشت", "شروع",
            "قائمة", "رئيسية", "عودة",
            "меню", "назад", "начало",
            "MAIN_MENU", "0"
        ]
        message_lower = message.lower().strip()
        return any(trigger in message_lower for trigger in back_triggers)


# ==================== PROPERTY QUERY HELPERS ====================

def build_rent_query_filters(session: RealtySession) -> Dict[str, Any]:
    """Build database query filters for rent flow"""
    filters = {
        "for_rent": True,  # Or transaction_type == "rent"
    }
    
    if session.property_type:
        if session.property_type == PropertyCategory.RESIDENTIAL:
            filters["property_type_in"] = ["apartment", "villa", "studio", "penthouse", "townhouse"]
        elif session.property_type == PropertyCategory.COMMERCIAL:
            filters["property_type_in"] = ["commercial", "office", "retail"]
    
    if session.budget_max:
        filters["rent_price_max"] = session.budget_max
    if session.budget_min:
        filters["rent_price_min"] = session.budget_min
    
    if session.location_preference:
        filters["area_like"] = session.location_preference
    
    return filters


def build_investment_query_filters(session: RealtySession) -> Dict[str, Any]:
    """Build database query filters for investment flow"""
    filters = {
        "for_sale": True,  # Or transaction_type == "buy"
        "show_roi": True,
    }
    
    if session.investment_type:
        if session.investment_type == PropertyCategory.RESIDENTIAL:
            filters["property_type_in"] = ["apartment", "villa", "penthouse"]
        elif session.investment_type == PropertyCategory.COMMERCIAL:
            filters["property_type_in"] = ["commercial", "office", "retail"]
        elif session.investment_type == PropertyCategory.LAND:
            filters["property_type_in"] = ["land"]
    
    if session.budget_max:
        filters["price_max"] = session.budget_max
    if session.budget_min:
        filters["price_min"] = session.budget_min
    
    return filters


def build_residency_query_filters(session: RealtySession) -> Dict[str, Any]:
    """Build database query filters for residency flow"""
    min_price = RESIDENCY_MINIMUMS.get(
        VisaType(session.visa_type) if session.visa_type else VisaType.TWO_YEAR,
        750000
    )
    
    filters = {
        "for_sale": True,
        "price_min": min_price,
        "residency_eligible": True,
    }
    
    if session.property_type:
        if session.property_type == PropertyCategory.RESIDENTIAL:
            filters["property_type_in"] = ["apartment", "villa", "penthouse"]
        elif session.property_type == PropertyCategory.COMMERCIAL:
            filters["property_type_in"] = ["commercial", "office"]
        elif session.property_type == PropertyCategory.LAND:
            filters["property_type_in"] = ["land"]
    
    return filters


# ==================== DEEP LINK VALIDATION ====================

REALTY_DEEP_LINK_PATTERNS = [
    r"START[_\s-]?REAL[_\s-]?ESTATE",
    r"start[_\s-]?realty[_\s-]?sales",
    r"REALTY[_\s-]?BOT",
    r"DUBAI[_\s-]?PROPERTY",
]

def is_valid_realty_deep_link(message: str) -> bool:
    """Check if message contains a valid realty sales deep link keyword"""
    import re
    
    message_upper = message.upper().strip()
    
    for pattern in REALTY_DEEP_LINK_PATTERNS:
        if re.search(pattern, message_upper, re.IGNORECASE):
            return True
    
    return False


# ==================== EXPORT ====================

__all__ = [
    "RealtyFlow",
    "RealtyState",
    "PropertyCategory",
    "VisaType",
    "RealtySession",
    "FlowController",
    "RENT_BUDGET_RANGES",
    "INVEST_BUDGET_RANGES",
    "RESIDENCY_MINIMUMS",
    "build_rent_query_filters",
    "build_investment_query_filters",
    "build_residency_query_filters",
    "is_valid_realty_deep_link",
]
