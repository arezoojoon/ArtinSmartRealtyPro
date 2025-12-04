# ==================== NEW STATE MACHINE HANDLERS ====================
# These handlers implement the 6-phase professional sales flow

async def _handle_warmup(
    self, 
    lang: Language, 
    message: Optional[str], 
    callback_data: Optional[str],
    lead: Lead,
    lead_updates: Dict
) -> BrainResponse:
    """
    WARMUP Phase: Quick rapport building (1-2 questions max)
    Goal: Identify primary objective (Investment, Living, or Residency)
    
    Flow Logic:
    - Living/Residency → Ask Buy/Rent → Budget
    - Investment → Auto-set Buy → Ask Budget directly
    """
    # Voice/Photo engagement hint (added to response messages)
    engagement_hint = {
        Language.EN: "\n\n🎙️ **Tip:** To help you better, you can send a **Voice Message** or upload a **Photo** of your dream property right now!",
        Language.FA: "\n\n🎙️ **نکته:** برای راهنمایی دقیق‌تر، می‌تونید همین الان **ویس** بفرستید یا **عکس** ملک مورد نظرتون رو آپلود کنید!",
        Language.AR: "\n\n🎙️ **نصيحة:** لمساعدتك بشكل أفضل، يمكنك إرسال **رسالة صوتية** أو تحميل **صورة** للعقار الذي تحلم به الآن!",
        Language.RU: "\n\n🎙️ **Совет:** Чтобы помочь вам лучше, вы можете отправить **голосовое сообщение** или загрузить **фото** желаемой недвижимости прямо сейчас!"
    }
    hint = engagement_hint.get(lang, engagement_hint[Language.EN])
    
    # If button clicked, capture goal and route based on selection
    if callback_data and callback_data.startswith("goal_"):
        goal = callback_data.replace("goal_", "")
        
        # Store in conversation_data
        conversation_data = lead.conversation_data or {}
        conversation_data["goal"] = goal
        
        # Mark filled_slots
        filled_slots = lead.filled_slots or {}
        filled_slots["goal"] = True
        
        lead_updates["conversation_data"] = conversation_data
        lead_updates["filled_slots"] = filled_slots
        
        # ===== CASE A: Living or Residency → Ask Buy/Rent =====
        if goal in ["living", "residency"]:
            transaction_question = {
                Language.EN: "Great choice! 🏡\n\nAre you looking to **Buy** or **Rent**?",
                Language.FA: "انتخاب عالی! 🏡\n\n**خرید** می‌خواید یا **اجاره**؟",
                Language.AR: "خيار رائع! 🏡\n\nهل تبحث عن **الشراء** أو **الإيجار**؟",
                Language.RU: "Отличный выбор! 🏡\n\nВы хотите **купить** или **арендовать**?"
            }
            
            transaction_buttons = [
                {"text": "🏠 " + ("خرید" if lang == Language.FA else "Buy"), "callback_data": "transaction_buy"},
                {"text": "🔑 " + ("اجاره" if lang == Language.FA else "Rent"), "callback_data": "transaction_rent"}
            ]
            
            return BrainResponse(
                message=transaction_question.get(lang, transaction_question[Language.EN]) + hint,
                next_state=ConversationState.SLOT_FILLING,
                lead_updates=lead_updates | {"pending_slot": "transaction_type"},
                buttons=transaction_buttons
            )
        
        # ===== CASE B: Investment → Auto-set Buy, Ask Budget =====
        elif goal == "investment":
            # Automatically set transaction_type to BUY for investment
            lead_updates["transaction_type"] = TransactionType.BUY
            conversation_data["transaction_type"] = "buy"
            filled_slots["transaction_type"] = True
            
            budget_question = {
                Language.EN: "Excellent! Let's find the best investment property for you. 💰\n\nWhat is your **budget range**?",
                Language.FA: "عالی! بیایید بهترین ملک سرمایه‌گذاری رو برات پیدا کنیم. 💰\n\n**بودجه‌ات** چقدر است؟",
                Language.AR: "ممتاز! دعنا نجد أفضل عقار استثماري لك. 💰\n\nما هو **نطاق ميزانيتك**؟",
                Language.RU: "Отлично! Давайте найдем лучшую инвестиционную недвижимость для вас. 💰\n\nКаков ваш **диапазон бюджета**?"
            }
            
            # Import BUDGET_RANGES from brain.py
            from brain import BUDGET_RANGES
            
            budget_buttons = []
            for idx, (min_val, max_val) in BUDGET_RANGES.items():
                label = f"{min_val:,} - {max_val:,} AED" if max_val else f"{min_val:,}+ AED"
                budget_buttons.append({"text": label, "callback_data": f"budget_{idx}"})
            
            return BrainResponse(
                message=budget_question.get(lang, budget_question[Language.EN]) + hint,
                next_state=ConversationState.SLOT_FILLING,
                lead_updates=lead_updates | {
                    "conversation_data": conversation_data,
                    "filled_slots": filled_slots,
                    "pending_slot": "budget"
                },
                buttons=budget_buttons
            )
    
    # If text message, use AI to answer FAQ but return to goal question
    if message and not callback_data:
        # Check if this is an FAQ or off-topic
        ai_response = await self.generate_ai_response(message, lead)
        
        # After answering, return to goal question
        goal_question = {
            Language.EN: "\n\nNow, are you looking for Investment, Living, or Residency?",
            Language.FA: "\n\nخب، به دنبال سرمایه‌گذاری، زندگی یا اقامت هستید؟",
            Language.AR: "\n\nحسنًا، هل تبحث عن الاستثمار أم العيش أم الإقامة؟",
            Language.RU: "\n\nИтак، вы ищете инвестиции, проживание или резиденцию?"
        }
        
        return BrainResponse(
            message=ai_response + goal_question.get(lang, goal_question[Language.EN]),
            next_state=ConversationState.WARMUP,
            buttons=[
                {"text": "💰 " + ("سرمایه‌گذاری" if lang == Language.FA else "Investment"), "callback_data": "goal_investment"},
                {"text": "🏠 " + ("زندگی" if lang == Language.FA else "Living"), "callback_data": "goal_living"},
                {"text": "🛂 " + ("اقامت" if lang == Language.FA else "Residency"), "callback_data": "goal_residency"}
            ]
        )
    
    # Default: Show goal buttons (initial entry to WARMUP)
    warmup_message = {
        Language.EN: "Great to meet you! 🎯\n\nAre you looking for Investment, Living, or Residency in Dubai?",
        Language.FA: "خوشحالم که با شما آشنا شدم! 🎯\n\nبه دنبال سرمایه‌گذاری، زندگی یا اقامت در دبی هستید؟",
        Language.AR: "سعيد بلقائك! 🎯\n\nهل تبحث عن الاستثمار أم العيش أم الإقامة في دبي؟",
        Language.RU: "Приятно познакомиться! 🎯\n\nВы ищете инвестиции, проживание или резиденцию в Дубае?"
    }
    
    return BrainResponse(
        message=warmup_message.get(lang, warmup_message[Language.EN]) + hint,
        next_state=ConversationState.WARMUP,
        buttons=[
            {"text": "💰 " + ("سرمایه‌گذاری" if lang == Language.FA else "Investment"), "callback_data": "goal_investment"},
            {"text": "🏠 " + ("زندگی" if lang == Language.FA else "Living"), "callback_data": "goal_living"},
            {"text": "🛂 " + ("اقامت" if lang == Language.FA else "Residency"), "callback_data": "goal_residency"}
        ]
    )


async def _handle_capture_contact(
    self, 
    lang: Language, 
    message: Optional[str], 
    callback_data: Optional[str], 
    lead: Lead, 
    lead_updates: Dict
) -> BrainResponse:
    """
    CAPTURE_CONTACT Phase (NEW): Get phone number and name immediately after goal selection
    This happens BEFORE slot filling to ensure we can contact the lead early
    
    Success triggers admin notification with hot lead alert
    """
    voice_hint = {
        Language.EN: "\n\n🎙️ Feel free to explain details by Voice!",
        Language.FA: "\n\n🎙️ هر توضیحی دارید میتونید ویس بفرستید!",
        Language.AR: "\n\n🎙️ يمكنك إرسال رسالة صوتية!",
        Language.RU: "\n\n🎙️ Отправьте голосовое сообщение!"
    }
    hint = voice_hint.get(lang, voice_hint[Language.EN])
    
    # Check if contact was successfully shared via Telegram button
    if lead.phone and not message:
        valid_contact = True
    elif message:
        # Try to parse phone and name from text message (format: Name - Phone)
        valid_contact = False
        phone_validation = await self._validate_phone_number(lang, message, lead_updates)
        
        if phone_validation.get("valid", False):  # Assuming validate returns dict with valid key
            valid_contact = True
            # Extract name from message (simple parsing)
            parts = message.split('-')
            if len(parts) >= 2:
                name_part = parts[0].strip()
                if not any(char.isdigit() for char in name_part):
                    lead_updates["name"] = name_part
    else:
        valid_contact = False
    
    if valid_contact:
        # Phone number successfully captured
        conversation_data = lead.conversation_data or {}
        goal = conversation_data.get("goal")
        
        # Determine next question based on goal
        if goal == "rent":
            # For rent, ask about residential vs commercial
            rent_q = {
                Language.EN: "Great! For rent, do you need **Residential** or **Commercial**?",
                Language.FA: "عالی! ✅ شماره شما ذخیره شد.\n\nبرای اجاره، ملک **مسکونی** می‌خواید یا **تجاری**؟",
                Language.AR: "رائع! للإيجار، هل تريد سكني أم تجاري؟",
                Language.RU: "Отлично! Для аренды, вам нужна жилая или коммерческая недвижимость?"
            }
            
            return BrainResponse(
                message=rent_q.get(lang, rent_q[Language.EN]) + hint,
                next_state=ConversationState.SLOT_FILLING,
                lead_updates=lead_updates | {"pending_slot": "property_type"},
                buttons=[
                    {"text": "🏠 " + ("مسکونی" if lang == Language.FA else "Residential"), "callback_data": "prop_residential"},
                    {"text": "🏢 " + ("تجاری" if lang == Language.FA else "Commercial"), "callback_data": "prop_commercial"}
                ],
                metadata={
                    "notify_admin": True,
                    "admin_message": self._generate_admin_alert(lead, goal)
                }
            )
        else:
            # For buy/investment, ask about budget
            budget_q = {
                Language.EN: "Perfect! What is your **approximate budget**?",
                Language.FA: "عالی! ✅ شماره شما ذخیره شد.\n\nبودجه تقریبی شما چقدر است؟",
                Language.AR: "رائع! ما هي ميزانيتك التقريبية؟",
                Language.RU: "Отлично! Какой ваш приблизительный бюджет?"
            }
            
            budget_buttons = []
            for idx, (min_val, max_val) in BUDGET_RANGES.items():
                label = f"{min_val:,} - {max_val:,} AED" if max_val else f"{min_val:,}+ AED"
                budget_buttons.append({"text": label, "callback_data": f"budget_{idx}"})
            
            return BrainResponse(
                message=budget_q.get(lang, budget_q[Language.EN]) + hint,
                next_state=ConversationState.SLOT_FILLING,
                lead_updates=lead_updates | {"pending_slot": "budget"},
                buttons=budget_buttons,
                metadata={
                    "notify_admin": True,
                    "admin_message": self._generate_admin_alert(lead, goal)
                }
            )
    else:
        # Contact not valid, ask again
        retry_msg = {
            Language.EN: "⚠️ Please enter a valid format:\n\n**Name - Phone Number**\n\nExample: Ali - +971501234567\n\nOr use the button below to share your contact:",
            Language.FA: "⚠️ لطفاً فرمت صحیح وارد کنید:\n\n**نام - شماره تماس**\n\nمثال: علی - 09121234567\n\nیا از دکمه زیر استفاده کنید:",
            Language.AR: "⚠️ يرجى إدخال التنسيق الصحيح:\n\n**الاسم - رقم الهاتف**",
            Language.RU: "⚠️ Пожалуйста, введите правильный формат:\n\n**Имя - Номер телефона**"
        }
        
        return BrainResponse(
            message=retry_msg.get(lang, retry_msg[Language.EN]),
            next_state=ConversationState.CAPTURE_CONTACT,
            request_contact=True  # Show contact share button again
        )

    def _generate_admin_alert(self, lead: Lead, goal: str) -> str:
        """Generate admin notification message for hot lead"""
        from datetime import datetime
        now_time = datetime.now().strftime("%H:%M")
        
        admin_alert_msg = (
            f"🚨 <b>لید داغ (Hot Lead)!</b>\n\n"
            f"👤 نام: {lead.name or 'کاربر'}\n"
            f"📱 شماره: <code>{lead.phone or 'ثبت نشده'}</code>\n"
            f"🎯 هدف: {goal}\n"
            f"⏰ زمان: {now_time}\n\n"
            f"📞 <i>همین الان تماس بگیرید!</i>"
        )
        return admin_alert_msg


async def _handle_slot_filling(
    self,
    lang: Language,
    message: Optional[str],
    callback_data: Optional[str],
    lead: Lead,
    lead_updates: Dict
) -> BrainResponse:
    """
    SLOT_FILLING Phase: Intelligent qualification with FAQ tolerance
    Required slots: budget, property_type, transaction_type
    Optional slots: location, bedrooms, payment_method
    
    KEY FEATURE: If user asks FAQ mid-filling, answer it and return to slot collection
    """
    conversation_data = lead.conversation_data or {}
    filled_slots = lead.filled_slots or {}
    pending_slot = lead.pending_slot
    
    # === HANDLE BUTTON RESPONSES (Slot Filling) ===
    if callback_data:
        # Transaction type selection (from WARMUP for Living/Residency)
        if callback_data.startswith("transaction_"):
            transaction_type_str = callback_data.replace("transaction_", "")  # "buy" or "rent"
            transaction_type_map = {
                "buy": TransactionType.BUY,
                "rent": TransactionType.RENT
            }
            
            conversation_data["transaction_type"] = transaction_type_str
            filled_slots["transaction_type"] = True
            lead_updates["transaction_type"] = transaction_type_map.get(transaction_type_str)
            
            # Voice/Photo engagement hint
            engagement_hint = {
                Language.EN: "\n\n🎙️ **Tip:** To help you better, you can send a **Voice Message** or upload a **Photo** of your dream property right now!",
                Language.FA: "\n\n🎙️ **نکته:** برای راهنمایی دقیق‌تر، می‌تونید همین الان **ویس** بفرستید یا **عکس** ملک مورد نظرتون رو آپلود کنید!",
                Language.AR: "\n\n🎙️ **نصيحة:** لمساعدتك بشكل أفضل، يمكنك إرسال **رسالة صوتية** أو تحميل **صورة** للعقار الذي تحلم به الآن!",
                Language.RU: "\n\n🎙️ **Совет:** Чтобы помочь вам лучше, вы можете отправить **голосовое сообщание** или загрузить **фото** желаемой недвижимости прямо сейчас!"
            }
            hint = engagement_hint.get(lang, engagement_hint[Language.EN])
            
            # Next: Ask budget
            budget_question = {
                Language.EN: "Perfect! What is your **budget range**?",
                Language.FA: "عالی! **بودجه‌ات** چقدر است؟",
                Language.AR: "ممتاز! ما هو **نطاق ميزانيتك**؟",
                Language.RU: "Отлично! Каков ваш **диапазон бюджета**?"
            }
            
            # Import BUDGET_RANGES from brain.py
            from brain import BUDGET_RANGES
            
            budget_buttons = []
            for idx, (min_val, max_val) in BUDGET_RANGES.items():
                label = f"{min_val:,} - {max_val:,} AED" if max_val else f"{min_val:,}+ AED"
                budget_buttons.append({"text": label, "callback_data": f"budget_{idx}"})
            
            return BrainResponse(
                message=budget_question.get(lang, budget_question[Language.EN]) + hint,
                next_state=ConversationState.SLOT_FILLING,
                lead_updates=lead_updates | {
                    "conversation_data": conversation_data,
                    "filled_slots": filled_slots,
                    "pending_slot": "budget"
                },
                buttons=budget_buttons
            )
        
        # Budget selection
        elif callback_data.startswith("budget_"):
            idx = int(callback_data.replace("budget_", ""))
            from brain import BUDGET_RANGES
            min_val, max_val = BUDGET_RANGES[idx]
            
            conversation_data["budget_min"] = min_val
            conversation_data["budget_max"] = max_val
            filled_slots["budget"] = True
            lead_updates["budget_min"] = min_val
            lead_updates["budget_max"] = max_val
            
            # Next: Ask property type
            property_question = {
                Language.EN: "Perfect! What type of property are you looking for?",
                Language.FA: "عالی! چه نوع ملکی مد نظر دارید؟",
                Language.AR: "رائع! ما نوع العقار الذي تبحث عنه؟",
                Language.RU: "Отлично! Какой тип недвижимости вы ищете?"
            }
            
            property_buttons = [
                {"text": "🏢 " + ("آپارتمان" if lang == Language.FA else "Apartment"), "callback_data": "prop_apartment"},
                {"text": "🏠 " + ("ویلا" if lang == Language.FA else "Villa"), "callback_data": "prop_villa"},
                {"text": "🏰 " + ("پنت‌هاوس" if lang == Language.FA else "Penthouse"), "callback_data": "prop_penthouse"},
                {"text": "🏘️ " + ("تاون‌هاوس" if lang == Language.FA else "Townhouse"), "callback_data": "prop_townhouse"},
                {"text": "🏪 " + ("تجاری" if lang == Language.FA else "Commercial"), "callback_data": "prop_commercial"},
                {"text": "🏞️ " + ("زمین" if lang == Language.FA else "Land"), "callback_data": "prop_land"},
            ]
            
            return BrainResponse(
                message=property_question.get(lang, property_question[Language.EN]),
                next_state=ConversationState.SLOT_FILLING,
                lead_updates=lead_updates | {
                    "conversation_data": conversation_data,
                    "filled_slots": filled_slots,
                    "pending_slot": "property_type"
                },
                buttons=property_buttons
            )
        
        # Property type selection
        elif callback_data.startswith("prop_"):
            property_type_str = callback_data.replace("prop_", "")
            property_type_map = {
                "apartment": PropertyType.APARTMENT,
                "villa": PropertyType.VILLA,
                "penthouse": PropertyType.PENTHOUSE,
                "townhouse": PropertyType.TOWNHOUSE,
                "commercial": PropertyType.COMMERCIAL,
                "land": PropertyType.LAND
            }
            
            conversation_data["property_type"] = property_type_str
            filled_slots["property_type"] = True
            lead_updates["property_type"] = property_type_map.get(property_type_str)
            
            # Next: Ask transaction type (buy/rent)
            transaction_question = {
                Language.EN: "Got it! Are you looking to Buy or Rent?",
                Language.FA: "فهمیدم! می‌خواهید بخرید یا اجاره کنید؟",
                Language.AR: "فهمت! هل تريد الشراء أم الإيجار؟",
                Language.RU: "Понял! Вы хотите купить или арендовать?"
            }
            
            return BrainResponse(
                message=transaction_question.get(lang, transaction_question[Language.EN]),
                next_state=ConversationState.SLOT_FILLING,
                lead_updates=lead_updates | {
                    "conversation_data": conversation_data,
                    "filled_slots": filled_slots,
                    "pending_slot": "transaction_type"
                },
                buttons=[
                    {"text": self.get_text("btn_buy", lang), "callback_data": "tx_buy"},
                    {"text": self.get_text("btn_rent", lang), "callback_data": "tx_rent"}
                ]
            )
        
        # Transaction type selection
        elif callback_data.startswith("tx_"):
            transaction_type_str = callback_data.replace("tx_", "")
            transaction_type_map = {
                "buy": TransactionType.BUY,
                "rent": TransactionType.RENT
            }
            
            conversation_data["transaction_type"] = transaction_type_str
            filled_slots["transaction_type"] = True
            lead_updates["transaction_type"] = transaction_type_map.get(transaction_type_str)
            
            # Check if all REQUIRED slots are filled
            required_slots = ["budget", "property_type", "transaction_type"]
            all_filled = all(filled_slots.get(slot, False) for slot in required_slots)
            
            if all_filled:
                # Move to VALUE_PROPOSITION
                transition_message = {
                    Language.EN: "Perfect! Let me show you some amazing properties that match your criteria...",
                    Language.FA: "عالی! بذار چند ملک فوق‌العاده که با معیارهات مچ میشه رو نشونت بدم...",
                    Language.AR: "رائع! دعني أريك بعض العقارات المذهلة التي تتناسب مع معاييرك...",
                    Language.RU: "Отлично! Позвольте показать вам несколько потрясающих объектов, соответствующих вашим критериям..."
                }
                
                return BrainResponse(
                    message=transition_message.get(lang, transition_message[Language.EN]),
                    next_state=ConversationState.VALUE_PROPOSITION,
                    lead_updates=lead_updates | {
                        "conversation_data": conversation_data,
                        "filled_slots": filled_slots,
                        "pending_slot": None
                    }
                )
    
    # === HANDLE TEXT MESSAGES (FAQ Detection) ===
    if message and not callback_data:
        # Check if this is answering the pending slot OR an FAQ
        # For now, treat all text as FAQ and use AI to respond
        ai_response = await self.generate_ai_response(message, lead)
        
        # Determine next missing slot
        next_slot_question = None
        next_slot_buttons = []
        next_pending_slot = None
        
        if not filled_slots.get("budget"):
            next_slot_question = {
                Language.EN: "\n\nGreat question! Now, what's your budget range?",
                Language.FA: "\n\nسوال خوبی بود! خب، بودجه‌ات چقدر است؟",
                Language.AR: "\n\nسؤال رائع! حسنًا، ما هو نطاق ميزانيتك؟",
                Language.RU: "\n\nОтличный вопрос! Итак, каков ваш бюджет?"
            }
            next_pending_slot = "budget"
            for idx, (min_val, max_val) in BUDGET_RANGES.items():
                if max_val:
                    label = f"{min_val:,} - {max_val:,} AED"
                else:
                    label = f"{min_val:,}+ AED"
                next_slot_buttons.append({"text": label, "callback_data": f"budget_{idx}"})
        
        elif not filled_slots.get("property_type"):
            next_slot_question = {
                Language.EN: "\n\nGood to know! What type of property are you interested in?",
                Language.FA: "\n\nخوبه که می‌دونم! چه نوع ملکی مد نظر دارید؟",
                Language.AR: "\n\nجيد أن أعرف! ما نوع العقار الذي تهتم به؟",
                Language.RU: "\n\nХорошо знать! Какой тип недвижимости вас интересует?"
            }
            next_pending_slot = "property_type"
            next_slot_buttons = [
                {"text": "🏢 " + ("آپارتمان" if lang == Language.FA else "Apartment"), "callback_data": "prop_apartment"},
                {"text": "🏠 " + ("ویلا" if lang == Language.FA else "Villa"), "callback_data": "prop_villa"},
                {"text": "🏰 " + ("پنت‌هاوس" if lang == Language.FA else "Penthouse"), "callback_data": "prop_penthouse"},
                {"text": "🏘️ " + ("تاون‌هاوس" if lang == Language.FA else "Townhouse"), "callback_data": "prop_townhouse"},
                {"text": "🏪 " + ("تجاری" if lang == Language.FA else "Commercial"), "callback_data": "prop_commercial"},
                {"text": "🏞️ " + ("زمین" if lang == Language.FA else "Land"), "callback_data": "prop_land"},
            ]
        
        elif not filled_slots.get("transaction_type"):
            next_slot_question = {
                Language.EN: "\n\nUnderstood! Are you looking to Buy or Rent?",
                Language.FA: "\n\nمتوجه شدم! می‌خواهید بخرید یا اجاره کنید؟",
                Language.AR: "\n\nفهمت! هل تريد الشراء أم الإيجار؟",
                Language.RU: "\n\nПонял! Вы хотите купить или арендовать?"
            }
            next_pending_slot = "transaction_type"
            next_slot_buttons = [
                {"text": self.get_text("btn_buy", lang), "callback_data": "tx_buy"},
                {"text": self.get_text("btn_rent", lang), "callback_data": "tx_rent"}
            ]
        
        # Return AI response + next slot question
        return BrainResponse(
            message=ai_response + (next_slot_question.get(lang, next_slot_question[Language.EN]) if next_slot_question else ""),
            next_state=ConversationState.SLOT_FILLING,
            lead_updates={"pending_slot": next_pending_slot},
            buttons=next_slot_buttons
        )
    
    # Default: Should not reach here
    return BrainResponse(
        message="Error in slot filling",
        next_state=ConversationState.SLOT_FILLING
    )


async def _handle_value_proposition(
    self,
    lang: Language,
    message: Optional[str],
    callback_data: Optional[str],
    lead: Lead,
    lead_updates: Dict
) -> BrainResponse:
    """
    VALUE_PROPOSITION Phase: Show matching properties from inventory
    Goal: Demonstrate value BEFORE asking for contact info
    """
    # Get property recommendations based on filled slots
    recommendations = await get_property_recommendations(
        tenant_id=lead.tenant_id,
        budget_min=lead.budget_min,
        budget_max=lead.budget_max,
        property_type=lead.property_type,
        transaction_type=lead.transaction_type,
        limit=3
    )
    
    if recommendations:
        # Format recommendations
        properties_text = "\n\n".join([
            f"🏠 {prop.title}\n💰 {prop.price:,} AED\n📍 {prop.location}\n🛏️ {prop.bedrooms} bedrooms"
            for prop in recommendations
        ])
        
        # === FEATURE 2: SCARCITY & URGENCY TACTICS ===
        # Add FOMO message to create urgency
        scarcity_messages = {
            Language.EN: "\n\n⚠️ Only 3 units left at this price!",
            Language.FA: "\n\n⚠️ فقط ۳ واحد با این قیمت باقی مانده است!",
            Language.AR: "\n\n⚠️ بقي 3 وحدات فقط بهذا السعر!",
            Language.RU: "\n\n⚠️ Осталось только 3 единицы по этой цене!"
        }
        
        scarcity_msg = scarcity_messages.get(lang, scarcity_messages[Language.EN])
        
        value_message = {
            Language.EN: f"Here are some perfect matches for you:\n\n{properties_text}{scarcity_msg}\n\nWould you like to receive a detailed PDF report with ROI projections?",
            Language.FA: f"اینها چند تا ملک عالی برای شما هستند:\n\n{properties_text}{scarcity_msg}\n\nمایل هستید یک گزارش کامل PDF با پیش‌بینی ROI دریافت کنید؟",
            Language.AR: f"إليك بعض الخيارات المثالية لك:\n\n{properties_text}{scarcity_msg}\n\nهل ترغب في تلقي تقرير PDF مفصل مع توقعات عائد الاستثمار؟",
            Language.RU: f"Вот несколько идеальных вариантов для вас:\n\n{properties_text}{scarcity_msg}\n\nХотите получить подробный PDF-отчет с прогнозами ROI?"
        }
        
        # Track urgency engagement
        lead_updates["urgency_score"] = min(10, (lead.urgency_score or 0) + 1)
        lead_updates["fomo_messages_sent"] = (lead.fomo_messages_sent or 0) + 1
        
        return BrainResponse(
            message=value_message.get(lang, value_message[Language.EN]),
            next_state=ConversationState.HARD_GATE,
            buttons=[
                {"text": self.get_text("btn_yes", lang), "callback_data": "pdf_yes"},
                {"text": self.get_text("btn_no", lang), "callback_data": "pdf_no"}
            ]
        )
    else:
        # No matching properties - still move to HARD_GATE
        # === FEATURE 2: HOT MARKET URGENCY MESSAGE ===
        no_match_message = {
            Language.EN: "⚠️ Market is very hot and units sell fast! I'll send you exclusive off-market deals. Share your contact?",
            Language.FA: "⚠️ بازار خیلی داغ است و فایل‌ها سریع فروش می‌روند! من برای شما فایل‌های حصری ارسال می‌کنم. شماره‌تون رو به اشتراک می‌گذارید؟",
            Language.AR: "⚠️ السوق ساخن جداً والوحدات تباع بسرعة! سأرسل لك صفقات حصرية. هل تشارك معلومات الاتصال الخاصة بك؟",
            Language.RU: "⚠️ Рынок очень активен, объекты уходят быстро! Я отправлю вам эксклюзивные предложения. Поделитесь контактом?"
        }
        
        # Track urgency engagement
        lead_updates["urgency_score"] = min(10, (lead.urgency_score or 0) + 2)  # Higher urgency for no matches
        lead_updates["fomo_messages_sent"] = (lead.fomo_messages_sent or 0) + 1
        
        return BrainResponse(
            message=no_match_message.get(lang, no_match_message[Language.EN]),
            next_state=ConversationState.HARD_GATE,
            lead_updates=lead_updates
        )


async def _handle_hard_gate(
    self,
    lang: Language,
    message: Optional[str],
    callback_data: Optional[str],
    lead: Lead,
    lead_updates: Dict
) -> BrainResponse:
    """
    HARD_GATE Phase: Capture phone number for PDF delivery
    This happens AFTER showing value, not before!
    """
    # If user clicked "Yes, send PDF"
    if callback_data == "pdf_yes":
        phone_request = {
            Language.EN: "Perfect! To send you the PDF report, I need your phone number.\n\nPlease share your contact or type your number:",
            Language.FA: "عالی! برای ارسال گزارش PDF، به شماره تماس شما نیاز دارم.\n\nلطفاً شماره خود را به اشتراک بگذارید یا تایپ کنید:",
            Language.AR: "رائع! لإرسال تقرير PDF لك، أحتاج رقم هاتفك.\n\nيرجى مشاركة جهة الاتصال الخاصة بك أو كتابة رقمك:",
            Language.RU: "Отлично! Чтобы отправить вам PDF-отчет, мне нужен ваш номер телефона.\n\nПожалуйста, поделитесь контактом или введите номер:"
        }
        
        return BrainResponse(
            message=phone_request.get(lang, phone_request[Language.EN]),
            next_state=ConversationState.HARD_GATE
        )
    
    # If user clicked "No, thanks"
    if callback_data == "pdf_no":
        # Still try to engage
        engagement_message = {
            Language.EN: "No problem! Do you have any questions about Dubai real estate?",
            Language.FA: "مشکلی نیست! سوالی درباره املاک دبی دارید؟",
            Language.AR: "لا مشكلة! هل لديك أي أسئلة عن العقارات في دبي؟",
            Language.RU: "Без проблем! У вас есть вопросы о недвижимости в Дубае?"
        }
        
        return BrainResponse(
            message=engagement_message.get(lang, engagement_message[Language.EN]),
            next_state=ConversationState.ENGAGEMENT
        )
    
    # If user provided phone number (text message)
    if message:
        # Validate phone number
        phone = await self._handle_phone_gate(lang, message, lead_updates)
        
        # If validation successful, generate PDF
        if phone.next_state == ConversationState.ENGAGEMENT:
            # Phone captured successfully - send PDF
            pdf_sent_message = {
                Language.EN: "📄 Preparing your detailed ROI report...\n\nIt will be sent to you shortly!",
                Language.FA: "📄 گزارش ROI شما در حال آماده‌سازی است...\n\nبه زودی برایتان ارسال می‌شود!",
                Language.AR: "📄 جاري إعداد تقرير عائد الاستثمار المفصل...\n\nسيتم إرساله إليك قريبًا!",
                Language.RU: "📄 Готовлю ваш подробный отчет ROI...\n\nОн скоро будет отправлен!"
            }
            
            return BrainResponse(
                message=pdf_sent_message.get(lang, pdf_sent_message[Language.EN]),
                next_state=ConversationState.ENGAGEMENT,
                lead_updates=phone.lead_updates,
                metadata={"send_pdf": True}
            )
        else:
            # Phone validation failed - return error
            return phone
    
    # Default: Should not reach here
    return BrainResponse(
        message="Please provide your phone number",
        next_state=ConversationState.HARD_GATE
    )
