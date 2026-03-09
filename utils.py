from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from config import ADMIN_USER_IDS
from database import ensure_user, is_banned

async def safe_edit_text(message: Message, text: str, reply_markup=None) -> bool:
    """Edit message safely; ignore Telegram 'message is not modified' noise."""
    try:
        await message.edit_text(text, reply_markup=reply_markup)
        return True
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            return False
        raise

def is_unlimited_user(user_id: int) -> bool:
    return user_id in ADMIN_USER_IDS

async def touch_user_from_message(message: Message):
    if not message.from_user:
        return
    await ensure_user(message.from_user.id, message.from_user.username or "")

async def reject_if_banned_message(message: Message) -> bool:
    user = message.from_user
    if not user:
        return False
    if await is_banned(user.id):
        await message.answer("❌ You are blocked from using this bot.")
        return True
    return False

async def reject_if_banned_callback(callback: CallbackQuery) -> bool:
    user = callback.from_user
    if not user:
        return False
    await ensure_user(user.id, user.username or "")
    if await is_banned(user.id):
        await callback.answer("❌ You are blocked from using this bot.", show_alert=True)
        return True
    return False

def parse_positive_int_arg(text: str, default: int, min_value: int, max_value: int) -> int:
    parts = (text or "").strip().split(maxsplit=1)
    if len(parts) < 2:
        return default
    try:
        value = int(parts[1].strip())
    except ValueError:
        return default
    return max(min_value, min(value, max_value))