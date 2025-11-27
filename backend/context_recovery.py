"""
Example: Context Recovery Implementation
Shows how bot resumes conversation after user returns
"""

from typing import Optional
from database import Lead, ConversationState, Language
from redis_manager import redis_manager


async def handle_user_message_with_recovery(
    lead: Lead,
    message_text: str,
    telegram_id: int,
    tenant_id: int
) -> dict:
    """
    Handle incoming message with context recovery.
    
    Flow:
    1. Check Redis for existing context
    2. If found and different from DB state, offer to resume
    3. If user confirms, restore context and continue
    4. Save context after each interaction
    """
    
    # 1. Get context from Redis
    redis_context = await redis_manager.get_context(telegram_id, tenant_id)
    
    # 2. Check if context differs from current DB state
    if redis_context and redis_context.get("conversation_state") != lead.conversation_state.value:
        # User left mid-conversation and returned
        saved_state = ConversationState(redis_context["conversation_state"])
        filled_slots = redis_context.get("filled_slots", {})
        
        # Build resume message
        resume_msg = build_resume_message(saved_state, filled_slots, lead.language)
        
        return {
            "type": "resume_prompt",
            "message": resume_msg,
            "saved_context": redis_context
        }
    
    # 3. Normal flow - process message and save context
    # (This will be handled by Brain.process_message)
    
    return {"type": "continue"}


def build_resume_message(
    state: ConversationState,
    filled_slots: dict,
    lang: Language
) -> str:
    """
    Build a personalized resume message based on saved context.
    
    Examples:
    - FA: "سلام دوباره! 👋 آخرین بار داشتی می‌گفتی بودجه‌ت ۱ میلیون درهمه و دنبال آپارتمان هستی. ادامه بدیم؟"
    - EN: "Welcome back! 👋 Last time you mentioned budget of 1M AED for an apartment. Shall we continue?"
    """
    
    # Extract filled slots for personalization
    goal = filled_slots.get("goal", "")
    budget_min = filled_slots.get("budget_min", 0)
    budget_max = filled_slots.get("budget_max", 0)
    property_type = filled_slots.get("property_type", "")
    
    # Build context summary
    context_parts = []
    
    if goal:
        goal_text = {
            Language.FA: f"هدفت {goal} بود",
            Language.EN: f"your goal was {goal}",
            Language.AR: f"كان هدفك {goal}",
            Language.RU: f"ваша цель была {goal}"
        }
        context_parts.append(goal_text.get(lang, goal_text[Language.EN]))
    
    if budget_min and budget_max:
        budget_text = {
            Language.FA: f"بودجه‌ات {budget_min:,} تا {budget_max:,} درهم",
            Language.EN: f"budget {budget_min:,} - {budget_max:,} AED",
            Language.AR: f"ميزانية {budget_min:,} - {budget_max:,} درهم",
            Language.RU: f"бюджет {budget_min:,} - {budget_max:,} AED"
        }
        context_parts.append(budget_text.get(lang, budget_text[Language.EN]))
    elif budget_min:
        budget_text = {
            Language.FA: f"بودجه‌ات {budget_min:,}+ درهم",
            Language.EN: f"budget {budget_min:,}+ AED",
            Language.AR: f"ميزانية {budget_min:,}+ درهم",
            Language.RU: f"бюджет {budget_min:,}+ AED"
        }
        context_parts.append(budget_text.get(lang, budget_text[Language.EN]))
    
    if property_type:
        prop_text = {
            Language.FA: f"دنبال {property_type}",
            Language.EN: f"looking for {property_type}",
            Language.AR: f"تبحث عن {property_type}",
            Language.RU: f"ищете {property_type}"
        }
        context_parts.append(prop_text.get(lang, prop_text[Language.EN]))
    
    # Combine context
    context_summary = " و ".join(context_parts) if lang == Language.FA else ", ".join(context_parts)
    
    # Build full message
    if state == ConversationState.SLOT_FILLING:
        messages = {
            Language.FA: f"سلام دوباره! 👋\n\nآخرین بار داشتی می‌گفتی {context_summary}.\n\nادامه بدیم؟",
            Language.EN: f"Welcome back! 👋\n\nLast time you mentioned {context_summary}.\n\nShall we continue?",
            Language.AR: f"مرحبًا بعودتك! 👋\n\nآخر مرة ذكرت {context_summary}.\n\nهل نكمل؟",
            Language.RU: f"С возвращением! 👋\n\nВ прошлый раз вы упомянули {context_summary}.\n\nПродолжим?"
        }
    elif state == ConversationState.HARD_GATE:
        messages = {
            Language.FA: "سلام! 👋\n\nگزارش PDF آماده ارساله. فقط شماره‌تو بده تا بفرستم.\n\nادامه بدیم؟",
            Language.EN: "Hello! 👋\n\nYour PDF report is ready. Just share your number and I'll send it.\n\nContinue?",
            Language.AR: "مرحبًا! 👋\n\nتقرير PDF جاهز. فقط شارك رقمك وسأرسله.\n\nهل نكمل؟",
            Language.RU: "Привет! 👋\n\nВаш PDF-отчет готов. Просто поделитесь номером, и я отправлю его.\n\nПродолжим?"
        }
    else:
        messages = {
            Language.FA: "سلام دوباره! 👋\n\nمی‌خوای از جایی که موندیم ادامه بدیم؟",
            Language.EN: "Welcome back! 👋\n\nWant to continue where we left off?",
            Language.AR: "مرحبًا بعودتك! 👋\n\nهل تريد المتابعة من حيث توقفنا؟",
            Language.RU: "С возвращением! 👋\n\nХотите продолжить с того места, где остановились?"
        }
    
    return messages.get(lang, messages[Language.EN])


async def save_context_to_redis(lead: Lead):
    """
    Save current conversation context to Redis.
    Call this after every state transition.
    """
    context = {
        "conversation_state": lead.conversation_state.value,
        "filled_slots": lead.filled_slots or {},
        "pending_slot": lead.pending_slot,
        "conversation_data": lead.conversation_data or {},
        "language": lead.language.value if lead.language else "fa"
    }
    
    await redis_manager.save_context(
        telegram_id=lead.telegram_id,
        tenant_id=lead.tenant_id,
        context=context
    )
