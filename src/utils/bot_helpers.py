import asyncio

from aiogram.types import CallbackQuery, Message

from src.bot.ui import (
    get_review_flashcard_keyboard,
    get_review_start_keyboard,
    get_start_new_word_keyboard,
    get_story_genre_keyboard,
    get_word_keyboard,
)
from src.core.app_state import (
    cleanup_user_temp_messages,
    clear_user_waiting_states,
    current_word_session,
    last_presented_words,
    record_temp_message,
    review_sessions,
    story_translation_overrides,
    user_language,
    user_word_history,
)
from src.core.config import DAILY_LIMIT
from src.core.i18n import get_lang
from src.core.texts import format_date, format_word
from src.data.api_words import COMMON_WORDS, get_word_data
from src.data.level_words import extract_headword as _extract_headword
from src.data.level_words import load_levelled_words as _load_levelled_words
from src.database.models import (
    get_daily_count,
    get_hard_words,
    get_next_word,
    get_user_level,
    get_word_reason,
    get_wordset_progress,
    set_user_level,
)
from src.utils.utils import is_unlimited_user, safe_edit_text


def _next_level(level: str) -> str | None:
    level = (level or "").upper()
    order = ("A1", "A2", "B1", "B2")
    if level not in order:
        return None
    idx = order.index(level)
    if idx >= len(order) - 1:
        return None
    return order[idx + 1]


def _build_levels_lock_text(current_level: str, placement_done: bool, unlock_all: bool = False, lang: str = "hy") -> str:
    levels = ("A1", "A2", "B1", "B2")
    title = {"hy": "📚 Level Map", "ru": "📚 Карта уровней", "en": "📚 Level Map"}.get(lang, "📚 Level Map")
    lines = [title, ""]
    if not placement_done:
        not_done = {"hy": "Placement test-ը դեռ ավարտված չէ։", "ru": "Placement test ещё не пройден.", "en": "Placement test not completed yet."}.get(lang, "Placement test not completed yet.")
        start_hint = {"hy": "Սկսելու համար՝ /placement", "ru": "Чтобы начать: /placement", "en": "To start: /placement"}.get(lang, "To start: /placement")
        lines.append(not_done)
        for lvl in levels:
            lines.append(f"🔒 {lvl}")
        lines.append("")
        lines.append(start_hint)
        return "\n".join(lines)

    cur_label = {"hy": "Ընթացիկ բացված մակարդակ", "ru": "Текущий открытый уровень", "en": "Current unlocked level"}.get(lang, "Current unlocked level")
    if unlock_all:
        lines.append(f"{cur_label}: ALL (admin)")
    else:
        lines.append(f"{cur_label}: {current_level}")
    for lvl in levels:
        badge = "🔓" if unlock_all or lvl == current_level else "🔒"
        lines.append(f"{badge} {lvl}")
    return "\n".join(lines)


def _grade_tag(grade: str | None) -> str:
    g = (grade or "").strip().lower()
    if g == "again":
        return "❌ Again"
    if g == "hard":
        return "🟠 Hard"
    if g == "good":
        return "✅ Good"
    if g == "easy":
        return "🚀 Easy"
    return "⚪ New"


from src.core.i18n import get_lang, t


def _build_story_intro_text(words: list[str], lang: str = "hy") -> str:
    words_line = ", ".join(words[:10]) if words else "—"
    return t("story_intro", lang, words=words_line)


def _build_palace_intro_text(words: list[str], lang: str = "hy") -> str:
    words_line = ", ".join(words[:10]) if words else "—"
    return t("palace_intro", lang, words=words_line)


def _parse_story_translation_pairs(raw: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if not raw:
        return result
    chunks = [c.strip() for c in raw.replace("\n", ";").split(";") if c.strip()]
    for chunk in chunks:
        key, value = "", ""
        if "=" in chunk:
            key, value = chunk.split("=", 1)
        elif ":" in chunk:
            key, value = chunk.split(":", 1)
        else:
            continue
        word = _extract_headword(key.strip())
        tr = value.strip()
        if not word or not tr:
            continue
        result[word] = tr
    return result


async def _build_story_glossary_text(words: list[str], user_id: int | None = None) -> str:
    uniq_words = list(dict.fromkeys((w or "").strip().lower() for w in words if (w or "").strip()))[:10]
    if not uniq_words:
        return "📘 Glossary\n- —"

    overrides = story_translation_overrides.get(int(user_id or 0), {}) if user_id else {}

    async def _safe_get(w: str):
        try:
            return await get_word_data(w)
        except Exception as e:
            return e

    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(_safe_get(w)) for w in uniq_words]
    rows = [t.result() for t in tasks]

    lines = ["📘 Glossary"]
    for w, row in zip(uniq_words, rows, strict=False):
        custom = (overrides.get(w) or "").strip()
        if custom:
            tr = custom
        elif isinstance(row, Exception):
            tr = "—"
        else:
            tr = ((row or {}).get("translation") or "—").strip()
        lines.append(f"- {w}: {tr}")
    return "\n".join(lines)


async def send_next_word_card(message: Message | CallbackQuery, user_id: int, level: str) -> bool:
    msg_target = message.message if isinstance(message, CallbackQuery) else message
    chat_id = msg_target.chat.id

    # 1. Clean up temporary messages from previous word and reset waiting states
    clear_user_waiting_states(user_id)
    await cleanup_user_temp_messages(msg_target.bot, chat_id, user_id)

    daily_count = await get_daily_count(user_id)
    if not is_unlimited_user(user_id) and daily_count >= DAILY_LIMIT:
        await msg_target.answer(
            f"🎉 Այսօրվա {DAILY_LIMIT} բառը կատարեցիր։\n\n"
            f"Վաղը կշարունակենք 💪\n"
            f"📘 Սովորելու բառեր — /review\n"
            f"✅ Սովորած բառեր — /learned\n"
            f"📖 Պատմություն բառերով — /story",
            reply_markup=get_story_genre_keyboard(),
        )
        return False

    levels = _load_levelled_words()
    words_pool = levels.get(level) or COMMON_WORDS
    if not words_pool:
        await msg_target.answer("❗ Այս պահին ընտրված մակարդակի համար բառեր չեն գտնվել։")
        return False

    word = await get_next_word(user_id, words_pool, include_hard_due=False)
    if not word:
        await msg_target.answer("❗ Այս պահին հաջորդ բառ չի գտնվել։ Փորձեք կրկին քիչ հետո։")
        return False

    # 2. Save previous session to history
    if user_id in current_word_session and current_word_session[user_id].get("word"):
        if user_id not in user_word_history:
            user_word_history[user_id] = []
        user_word_history[user_id].append(current_word_session[user_id])
        if len(user_word_history[user_id]) > 20:
            user_word_history[user_id].pop(0)

    # 3. Set new current session
    current_word_session[user_id] = {"word": word, "level": level, "actions": []}

    word_data = await get_word_data(word, level=level)
    reason = await get_word_reason(user_id, word)
    daily_limit_display = DAILY_LIMIT if not is_unlimited_user(user_id) else max(DAILY_LIMIT, daily_count + 1)
    text = format_word(word_data, daily_count + 1, daily_limit_display, level, reason)
    has_back = bool(user_word_history.get(user_id))
    lang = get_lang(user_id)
    markup = get_word_keyboard(word, has_back=has_back, lang=lang)
    if msg_target.from_user and msg_target.from_user.is_bot:
        await safe_edit_text(msg_target, text, reply_markup=markup)
    else:
        await msg_target.answer(text, reply_markup=markup)
    last_presented_words[user_id] = word
    return True


async def send_previous_word_card(message: Message | CallbackQuery, user_id: int) -> bool:
    msg_target = message.message if isinstance(message, CallbackQuery) else message
    chat_id = msg_target.chat.id

    # 1. Clean up current word's temp messages
    await cleanup_user_temp_messages(msg_target.bot, chat_id, user_id)

    # 2. Get previous word session from history
    history = user_word_history.get(user_id, [])
    if not history:
        await msg_target.answer("❗ Նախորդ բառ չի գտնվել։")
        return False

    prev_session = history.pop()
    word = prev_session["word"]
    level = prev_session["level"]
    saved_actions = prev_session.get("actions", [])

    # Set as current session
    current_word_session[user_id] = {
        "word": word,
        "level": level,
        "actions": list(saved_actions),
    }

    # 3. Present previous word card
    daily_count = await get_daily_count(user_id)
    daily_limit_display = DAILY_LIMIT if not is_unlimited_user(user_id) else max(DAILY_LIMIT, daily_count + 1)
    word_data = await get_word_data(word, level=level)
    reason = await get_word_reason(user_id, word)
    text = format_word(word_data, daily_count, daily_limit_display, level, reason)

    markup = get_word_keyboard(word, has_back=len(history) > 0)
    if msg_target.from_user and msg_target.from_user.is_bot:
        await safe_edit_text(msg_target, text, reply_markup=markup)
    else:
        await msg_target.answer(text, reply_markup=markup)
    last_presented_words[user_id] = word

    # 4. Restore saved actions!
    for action in saved_actions:
        try:
            if action.get("type") == "text":
                sent = await msg_target.answer(action["text"], parse_mode=action.get("parse_mode"))
                record_temp_message(user_id, sent.message_id)
            elif action.get("type") == "audio" and action.get("file_id"):
                sent = await msg_target.bot.send_voice(chat_id, action["file_id"])
                record_temp_message(user_id, sent.message_id)
        except Exception as e:
            logging.warning(f"Failed to restore action {action}: {e}")

    return True


async def maybe_promote_level(user_id: int, message: Message | None = None) -> str:
    current = await get_user_level(user_id)
    levels = _load_levelled_words()
    words = levels.get(current) or []
    if not words:
        return current

    progress = await get_wordset_progress(user_id, words)
    if (progress.get("learned", 0) < progress.get("total", 1)) or (progress.get("accuracy", 0) < 70):
        return current

    nxt = _next_level(current)
    if not nxt:
        return current

    await set_user_level(user_id, nxt)
    if message:
        await message.answer(
            f"🎉 Գերազանց արդյունք․ դու ավարտեցիր {current} մակարդակը։\n"
            f"🚀 Բացվեց հաջորդ մակարդակը՝ {nxt}։"
        )
    return nxt


async def send_review_list(message: Message, user_id: int) -> bool:
    words = await get_hard_words(user_id)
    lang = get_lang(user_id)
    if not words:
        review_sessions.pop(user_id, None)
        await message.answer(
            t("no_words_available", lang),
            reply_markup=get_start_new_word_keyboard(lang)
        )
        return False

    words_only = [w["word"] for w in words if w.get("word")]
    review_sessions[user_id] = {"words": words_only, "index": 0, "show_translation": False, "show_example": False}

    lines = [f"{i}. {w['word']}  [{_grade_tag(w.get('last_grade') or 'hard')}] ({format_date(w.get('added_at', ''))})" for i, w in enumerate(words, 1)]

    guide = (
        "💡 **Ինչպե՞ս գնահատել.**\n"
        "❌ **Again**: Չհիշեցի (կրկնել շուտով)\n"
        "🟠 **Hard**: Դժվարությամբ (1-2 օրից)\n"
        "✅ **Good**: Լավ հիշում եմ (3-4 օրից)\n"
        "🚀 **Easy**: Շատ հեշտ էր (7-10 օրից)\n"
    )

    lines_text = "\n".join(lines)
    await message.answer(
        f"📘 **Review բառերի ցանկ**\n\n"
        f"{lines_text}\n\n"
        f"{guide}\n"
        f"Սեղմեք «🔁 Կրկնել (Flashcards)»։",
        reply_markup=get_review_start_keyboard(),
        parse_mode="Markdown"
    )
    return True


def _build_review_flashcard_text(word: str, index: int, total: int, word_data: dict, *, show_translation: bool, show_example: bool) -> str:
    translation = (word_data.get("translation") or "—").strip()
    transcription = (word_data.get("transcription") or "—").strip()
    example = (word_data.get("example") or "—").strip()
    example_tr = (word_data.get("example_translation") or "—").strip()
    text = f"🃏 Flashcard [{index}/{total}]\n\n🔤 Word: {word}\n"
    text += f"\n🇦🇲 Translation: {translation}\n🔊 Transcription: {transcription}" if show_translation else "\n💡 Սեղմեք «Show Translate»։"
    has_example = example != "—" or example_tr != "—"
    if show_example and has_example:
        text += f"\n\n💬 Example: {example}\n🇦🇲 Օրինակի թարգմանություն: {example_tr}"
    elif has_example:
        text += "\n\n💡 Սեղմեք «Show Example»։"
    return text


async def _edit_review_flashcard(message: Message, user_id: int) -> bool:
    session = review_sessions.get(user_id)
    if not session:
        return False

    words, index0 = session.get("words", []), int(session.get("index", 0))
    if not words or index0 >= len(words):
        review_sessions.pop(user_id, None)
        await safe_edit_text(message, "🎉 Գերազանց աշխատանք․ review-ը ավարտեցիր։")
        return False

    word = words[index0]
    word_data = await get_word_data(word) # Review uses cached data mostly, or generic
    await safe_edit_text(
        message,
        _build_review_flashcard_text(word, index0 + 1, len(words), word_data, show_translation=bool(session.get("show_translation")), show_example=bool(session.get("show_example"))),
        reply_markup=get_review_flashcard_keyboard(word, show_translation=bool(session.get("show_translation")), show_example=bool(session.get("show_example"))),
    )
    return True
