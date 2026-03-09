import asyncio
from collections import deque

PROCESSED_CALLBACKS_MAX = 5000

processed_callbacks: set[str] = set()
processed_callbacks_order: deque[str] = deque()
user_locks: dict[int, asyncio.Lock] = {}
search_waiting_users: set[int] = set()
last_presented_words: dict[int, str] = {}
test_sessions: dict[int, dict] = {}
review_sessions: dict[int, dict] = {}
placement_sessions: dict[int, dict] = {}
# Per-user glossary overrides for Story/Palace output.
story_translation_overrides: dict[int, dict[str, str]] = {}


def register_processed_callback(callback_id: str):
    """Track callback id with bounded memory usage."""
    if callback_id in processed_callbacks:
        return
    processed_callbacks.add(callback_id)
    processed_callbacks_order.append(callback_id)
    while len(processed_callbacks_order) > PROCESSED_CALLBACKS_MAX:
        old = processed_callbacks_order.popleft()
        processed_callbacks.discard(old)
