"""
Inline Keyboard Helpers for Telegram Bot
Handles inline keyboards with edit + checkmark after selection
"""

from typing import List, Dict, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)


def create_inline_keyboard(buttons: List[Dict[str, str]], columns: int = 1) -> InlineKeyboardMarkup:
    """
    Create inline keyboard from button list.
    
    Args:
        buttons: List of dicts with 'text' and 'callback_data'
        columns: Number of buttons per row
    
    Returns:
        InlineKeyboardMarkup ready to send
    """
    keyboard = []
    row = []
    
    for btn in buttons:
        row.append(InlineKeyboardButton(
            text=btn["text"],
            callback_data=btn["callback_data"]
        ))
        
        if len(row) >= columns:
            keyboard.append(row)
            row = []
    
    # Add remaining buttons
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


async def edit_message_with_checkmark(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    selected_text: str,
    new_message: Optional[str] = None
) -> bool:
    """
    Edit the message to show checkmark on selected button.
    Prevents user from clicking again (anti-loop).
    
    Args:
        update: Telegram update object
        context: Telegram context
        selected_text: Text of the button that was clicked
        new_message: Optional new message text (if None, keeps original)
    
    Returns:
        True if edited successfully
    """
    query = update.callback_query
    
    try:
        # Get original message and keyboard
        original_message = query.message.text
        original_keyboard = query.message.reply_markup
        
        if not original_keyboard:
            return False
        
        # Edit keyboard to add checkmark
        new_keyboard = []
        for row in original_keyboard.inline_keyboard:
            new_row = []
            for button in row:
                if button.text == selected_text:
                    # Add checkmark to selected button
                    new_button = InlineKeyboardButton(
                        text=f"✅ {button.text}",
                        callback_data="selected"  # Disable re-clicking
                    )
                else:
                    # Keep other buttons as-is but disable them
                    new_button = InlineKeyboardButton(
                        text=button.text,
                        callback_data="disabled"  # Disable all buttons
                    )
                new_row.append(new_button)
            new_keyboard.append(new_row)
        
        # Edit message
        await query.edit_message_text(
            text=new_message if new_message else original_message,
            reply_markup=InlineKeyboardMarkup(new_keyboard)
        )
        
        await query.answer()  # Acknowledge callback
        logger.info(f"✅ Message edited with checkmark: {selected_text}")
        return True
    
    except Exception as e:
        logger.error(f"❌ Failed to edit message: {e}")
        # Try to at least answer the callback
        try:
            await query.answer()
        except Exception as callback_err:
            logger.debug(f"Could not answer callback query: {callback_err}")
        return False


async def remove_keyboard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    new_message: Optional[str] = None
) -> bool:
    """
    Remove inline keyboard from message (after selection complete).
    
    Args:
        update: Telegram update object
        context: Telegram context
        new_message: Optional new message text
    
    Returns:
        True if removed successfully
    """
    query = update.callback_query
    
    try:
        original_message = query.message.text
        
        await query.edit_message_text(
            text=new_message if new_message else original_message,
            reply_markup=None  # Remove keyboard
        )
        
        await query.answer()
        logger.info("✅ Keyboard removed")
        return True
    
    except Exception as e:
        logger.error(f"❌ Failed to remove keyboard: {e}")
        try:
            await query.answer()
        except Exception as callback_err:
            logger.debug(f"Could not answer callback query: {callback_err}")
        return False


def create_goal_keyboard(lang: str = "fa") -> InlineKeyboardMarkup:
    """Create WARMUP goal selection keyboard."""
    buttons = [
        {"text": "💰 " + ("سرمایه‌گذاری" if lang == "fa" else "Investment"), "callback_data": "goal_investment"},
        {"text": "🏠 " + ("زندگی" if lang == "fa" else "Living"), "callback_data": "goal_living"},
        {"text": "🛂 " + ("اقامت" if lang == "fa" else "Residency"), "callback_data": "goal_residency"}
    ]
    return create_inline_keyboard(buttons, columns=3)


def create_budget_keyboard(budget_ranges: Dict[int, tuple]) -> InlineKeyboardMarkup:
    """Create budget selection keyboard."""
    buttons = []
    for idx, (min_val, max_val) in budget_ranges.items():
        if max_val:
            label = f"{min_val:,} - {max_val:,} AED"
        else:
            label = f"{min_val:,}+ AED"
        buttons.append({
            "text": label,
            "callback_data": f"budget_{idx}"
        })
    return create_inline_keyboard(buttons, columns=1)


def create_property_type_keyboard(lang: str = "fa") -> InlineKeyboardMarkup:
    """Create property type selection keyboard."""
    buttons = [
        {"text": "🏢 " + ("آپارتمان" if lang == "fa" else "Apartment"), "callback_data": "prop_apartment"},
        {"text": "🏠 " + ("ویلا" if lang == "fa" else "Villa"), "callback_data": "prop_villa"},
        {"text": "🏰 " + ("پنت‌هاوس" if lang == "fa" else "Penthouse"), "callback_data": "prop_penthouse"},
        {"text": "🏘️ " + ("تاون‌هاوس" if lang == "fa" else "Townhouse"), "callback_data": "prop_townhouse"},
        {"text": "🏪 " + ("تجاری" if lang == "fa" else "Commercial"), "callback_data": "prop_commercial"},
        {"text": "🏞️ " + ("زمین" if lang == "fa" else "Land"), "callback_data": "prop_land"},
    ]
    return create_inline_keyboard(buttons, columns=2)


def create_transaction_type_keyboard(lang: str = "fa") -> InlineKeyboardMarkup:
    """Create buy/rent selection keyboard."""
    buttons = [
        {"text": "🛒 " + ("خرید" if lang == "fa" else "Buy"), "callback_data": "tx_buy"},
        {"text": "🏠 " + ("اجاره" if lang == "fa" else "Rent"), "callback_data": "tx_rent"}
    ]
    return create_inline_keyboard(buttons, columns=2)


def create_yes_no_keyboard(lang: str = "fa") -> InlineKeyboardMarkup:
    """Create Yes/No keyboard."""
    buttons = [
        {"text": "✅ " + ("بله" if lang == "fa" else "Yes"), "callback_data": "yes"},
        {"text": "❌ " + ("خیر" if lang == "fa" else "No"), "callback_data": "no"}
    ]
    return create_inline_keyboard(buttons, columns=2)
