import asyncio
from collections import deque
from datetime import datetime

PROCESSED_CALLBACKS_MAX = 5000

processed_callbacks: set[str] = set()
processed_callbacks_order: deque[str] = deque()
user_locks: dict[int, asyncio.Lock] = {}
user_language: dict[int, str] = {}  # language code per user ("hy", "ru", "en")
explain_waiting_users:set[int] = set()
practice_waiting_users: dict[int, str] = {} # user_id -> word being practiced
pronunciation_waiting_users: dict[int, str] = {} # user_id -> word being practiced for pronunciation
search_waiting_users: set[int] = set()  # users waiting for a search query
pomodoro_sessions: dict[int, datetime] = {} # user_id -> start_time
plan_custom_waiting_users: dict[int, bool] = {}  # user_id -> True when waiting for custom goal input
level_test_sessions: dict[int, dict] = {} # user_id -> state

last_presented_words: dict[int, str] = {}
test_sessions: dict[int, dict] = {}
review_sessions: dict[int, dict] = {}
placement_sessions: dict[int, dict] = {}
# Per-user glossary overrides for Story/Palace output.
story_translation_overrides: dict[int, dict[str, str]] = {}

# --- Session & Clean Field Tracking ---
current_word_session: dict[int, dict] = {} # user_id -> {"word": str, "level": str, "actions": list[dict]}
user_word_history: dict[int, list[dict]] = {} # user_id -> list of past sessions
user_temp_messages: dict[int, list[int]] = {} # user_id -> list of message_ids to clean up


def record_temp_message(user_id: int, message_id: int):
    """Record a temporary message ID (audio, prompt, AI analysis) for later cleanup."""
    if user_id not in user_temp_messages:
        user_temp_messages[user_id] = []
    user_temp_messages[user_id].append(message_id)


def record_word_action(user_id: int, action: dict):
    """Record an action (audio, practice analysis, pronunciation feedback) performed on the current word."""
    if user_id in current_word_session:
        current_word_session[user_id].setdefault("actions", []).append(action)


async def cleanup_user_temp_messages(bot, chat_id: int, user_id: int):
    """Delete all temporary messages associated with the previous word to keep chat clean."""
    msg_ids = user_temp_messages.get(user_id, [])
    if not msg_ids:
        return
    for msg_id in msg_ids:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
    user_temp_messages[user_id] = []


def register_processed_callback(callback_id: str):
    """Track callback id with bounded memory usage."""
    if callback_id in processed_callbacks:
        return
    processed_callbacks.add(callback_id)
    processed_callbacks_order.append(callback_id)
    while len(processed_callbacks_order) > PROCESSED_CALLBACKS_MAX:
        old = processed_callbacks_order.popleft()
        processed_callbacks.discard(old)


def clear_user_waiting_states(user_id: int):
    """Clear any active waiting states for a user when switching tasks or starting new actions."""
    explain_waiting_users.discard(user_id)
    practice_waiting_users.pop(user_id, None)
    pronunciation_waiting_users.pop(user_id, None)
    search_waiting_users.discard(user_id)
    plan_custom_waiting_users.pop(user_id, None)
    level_test_sessions.pop(user_id, None)


def get_user_lock(user_id: int) -> asyncio.Lock:
    """Get or create per-user asyncio.Lock for serializing callback handling and preventing double-clicks."""
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    return user_locks[user_id]
