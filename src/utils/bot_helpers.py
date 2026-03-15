import asyncio

from aiogram.types import CallbackQuery, Message

from src.bot.ui import (
    get_review_flashcard_keyboard,
    get_review_start_keyboard,
    get_story_genre_keyboard,
    get_word_keyboard,
)
from src.core.app_state import last_presented_words, review_sessions, story_translation_overrides
from src.core.config import DAILY_LIMIT
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
from src.utils.utils import safe_edit_text


def _next_level(level: str) -> str | None:
    level = (level or "").upper()
    order = ("A1", "A2", "B1", "B2")
    if level not in order:
        return None
    idx = order.index(level)
    if idx >= len(order) - 1:
        return None
    return order[idx + 1]


def _build_levels_lock_text(current_level: str, placement_done: bool, unlock_all: bool = False) -> str:
    levels = ("A1", "A2", "B1", "B2")
    lines = ["📚 Level Map", ""]
    if not placement_done:
        lines.append("Placement test-ը դեռ ավարտված չէ։")
        for lvl in levels:
            lines.append(f"🔒 {lvl}")
        lines.append("")
        lines.append("Սկսելու համար՝ /placement")
        return "\n".join(lines)

    if unlock_all:
        lines.append("Current unlocked level: ALL (admin)")
    else:
        lines.append(f"Current unlocked level: {current_level}")
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


def _build_story_intro_text(words: list[str]) -> str:
    words_line = ", ".join(words[:10]) if words else "—"
    return (
        "📖 Contextual Story Mode\n\n"
        "Ընտրիր ժանրը, և ես կստեղծեմ կարճ պատմություն այսօրվա բառերով։\n"
        f"Target words: {words_line}"
    )


def _build_palace_intro_text(words: list[str]) -> str:
    words_line = ", ".join(words[:10]) if words else "—"
    return (
        "🧠 Personal Memory Palace\n\n"
        "Ընտրիր թեման, և ես կստեղծեմ տեսողական հիշողության «սենյակ» հենց այսօրվա բառերով։\n"
        f"Target words: {words_line}"
    )


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
    tasks = [get_word_data(w) for w in uniq_words]
    rows = await asyncio.gather(*tasks, return_exceptions=True)
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
    from src.utils.utils import is_unlimited_user  # circular
    msg_target = message.message if isinstance(message, CallbackQuery) else message

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

    word_data = await get_word_data(word, level=level)
    reason = await get_word_reason(user_id, word)
    daily_limit_display = DAILY_LIMIT if not is_unlimited_user(user_id) else max(DAILY_LIMIT, daily_count + 1)
    text = format_word(word_data, daily_count + 1, daily_limit_display, level, reason)
    markup = get_word_keyboard(word)
    if msg_target.from_user and msg_target.from_user.is_bot:
        await safe_edit_text(msg_target, text, reply_markup=markup)
    else:
        await msg_target.answer(text, reply_markup=markup)
    last_presented_words[user_id] = word
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
    if not words:
        review_sessions.pop(user_id, None)
        await message.answer("✨ Հիանալի աշխատանք․ սովորելու բառ չունես։ /word 🚀")
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
