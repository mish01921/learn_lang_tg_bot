import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import (
    get_today_answered_words,
    count_story_generations_today,
    count_palace_generations_today,
    get_story_history,
    get_memory_palace_history,
    save_story_history,
    save_memory_palace_history,
)
from utils import (
    touch_user_from_message,
    reject_if_banned_message,
    reject_if_banned_callback,
    is_unlimited_user,
    parse_positive_int_arg,
)
from api_words import (
    get_word_data,
    get_ai_example_sentences,
    generate_contextual_story,
    generate_memory_palace_text,
    extract_headword,
)
from app_state import (
    search_waiting_users,
    story_translation_overrides,
    processed_callbacks,
    register_processed_callback,
)
from ui import get_search_keyboard, get_story_genre_keyboard, get_palace_theme_keyboard
from texts import format_searched_word
from level_words import chunk_text as _chunk_text, find_word_levels
from config import (
    DAILY_STORY_LIMIT,
    DAILY_PALACE_LIMIT,
    STORY_GENRES,
    PALACE_THEMES,
)
from bot_helpers import (
    _build_story_intro_text,
    _build_palace_intro_text,
    _parse_story_translation_pairs,
    _build_story_glossary_text,
)

router = Router()

@router.message(Command("search"))
async def search_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message): return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) > 1 and parts[1].strip():
        query = extract_headword(parts[1].strip())
        levels = find_word_levels(query)
        level = levels[0] if levels else ""
        word_data = await get_word_data(query, level=level)
        await message.answer(format_searched_word(word_data, levels), reply_markup=get_search_keyboard(query))
    else:
        search_waiting_users.add(message.from_user.id)
        await message.answer("Գրեք փնտրվող բառը։\nՉեղարկելու համար գրեք՝ cancel")

@router.message(F.from_user.id.in_(search_waiting_users) & F.text & ~F.text.startswith('/'))
async def search_text_handler(message: Message):
    if await reject_if_banned_message(message): return
    user_id = message.from_user.id
    search_waiting_users.discard(user_id)

    text = (message.text or "").strip()
    if text.lower() in ("cancel", "exit", "չեղարկել"):
        await message.answer("❌ Որոնումը չեղարկվեց։")
        return

    query = extract_headword(text)
    await message.answer(f"🔎 Փնտրում եմ՝ {query}...")
    levels = find_word_levels(query)
    level = levels[0] if levels else ""
    word_data = await get_word_data(query, level=level)
    await message.answer(format_searched_word(word_data, levels), reply_markup=get_search_keyboard(query))

@router.message(Command("example"))
async def example_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message): return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Օգտագործում՝ /example achieve")
        return

    query = extract_headword(parts[1].strip())
    levels = find_word_levels(query)
    level = levels[0] if levels else "B1"
    examples = await get_ai_example_sentences(query, count=3, level=level)
    lines = "\n".join(f"{i}. {s}" for i, s in enumerate(examples, 1))
    await message.answer(f"🧠 AI Example sentences for: {query}\n\n{lines}")

@router.message(Command("story"))
async def story_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message): return
    user_id = message.from_user.id
    is_unlimited = is_unlimited_user(user_id)
    if not is_unlimited and await count_story_generations_today(user_id) >= DAILY_STORY_LIMIT:
        await message.answer(f"📖 Այսօրվա Story limit-ը լրացել է։")
        return
    words = await get_today_answered_words(user_id, limit=10)
    if not is_unlimited and len(words) < 3:
        await message.answer("📖 Story mode-ի համար այսօրվա առնվազն 3 բառ պետք է անցած լինի։")
        return
    await message.answer(_build_story_intro_text(words), reply_markup=get_story_genre_keyboard())

@router.callback_query(F.data.startswith("story:genre:"))
async def story_callback_handler(callback: CallbackQuery):
    from database import get_user_level # circular
    if await reject_if_banned_callback(callback): return
    user_id = callback.from_user.id

    genre_key = (callback.data or "").split(":")[-1]
    genre_name = STORY_GENRES.get(genre_key)
    if not genre_name:
        await callback.answer("Սխալ ժանր", show_alert=True)
        return

    words = await get_today_answered_words(user_id, limit=10)
    await callback.answer("Պատմությունը գեներացվում է... ⏳")
    level = await get_user_level(user_id)
    story_text = await generate_contextual_story(words, genre_name, level)
    glossary_text = await _build_story_glossary_text(words, user_id=user_id)
    await save_story_history(user_id, genre_name, words, story_text)
    final_text = f"📚 Genre: {genre_name}\n🎯 Level: {level}\n\n{story_text}\n\n{glossary_text}"
    for chunk in _chunk_text(final_text):
        await callback.message.answer(chunk)

@router.message(Command("palace"))
async def palace_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message): return
    user_id = message.from_user.id
    is_unlimited = is_unlimited_user(user_id)
    if not is_unlimited and await count_palace_generations_today(user_id) >= DAILY_PALACE_LIMIT:
        await message.answer(f"🧠 Այսօրվա Palace limit-ը լրացել է։")
        return
    words = await get_today_answered_words(user_id, limit=10)
    if not is_unlimited and len(words) < 3:
        await message.answer("🧠 Memory Palace-ի համար այսօրվա առնվազն 3 բառ պետք է անցած լինի։")
        return
    await message.answer(_build_palace_intro_text(words), reply_markup=get_palace_theme_keyboard())

@router.callback_query(F.data.startswith("palace:theme:"))
async def palace_callback_handler(callback: CallbackQuery):
    from database import get_user_level # circular
    if await reject_if_banned_callback(callback): return
    user_id = callback.from_user.id

    theme_key = (callback.data or "").split(":")[-1]
    theme_name = PALACE_THEMES.get(theme_key)
    if not theme_name:
        await callback.answer("Սխալ թեմա", show_alert=True)
        return

    words = await get_today_answered_words(user_id, limit=10)
    await callback.answer("Memory Palace-ը գեներացվում է... ⏳")
    level = await get_user_level(user_id)
    palace_text = await generate_memory_palace_text(words, theme_name, level)
    glossary_text = await _build_story_glossary_text(words, user_id=user_id)
    await save_memory_palace_history(user_id, theme_name, words, palace_text)
    final_text = f"🧠 Theme: {theme_name}\n🎯 Level: {level}\n\n{palace_text}\n\n{glossary_text}"
    for chunk in _chunk_text(final_text):
        await callback.message.answer(chunk)

@router.message(Command("story_history", "palace_history"))
async def history_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message): return

    is_story = "story" in (message.text or "")
    limit = parse_positive_int_arg(message.text or "", default=5, min_value=1, max_value=20)
    rows = await get_story_history(message.from_user.id, limit=limit) if is_story else await get_memory_palace_history(message.from_user.id, limit=limit)

    if not rows:
        await message.answer(f"📖 {'Story' if is_story else 'Palace'} history դեռ դատարկ է։")
        return

    for i, row in enumerate(rows, 1):
        words = ", ".join((row.get("words") or [])[:10])
        text = (
            f"📖 {'Story' if is_story else 'Palace'} #{i}\n"
            f"🗓 Date: {row.get('story_date' if is_story else 'palace_date') or ''}\n"
            f"🎭 {'Genre' if is_story else 'Theme'}: {row.get('genre' if is_story else 'theme') or '—'}\n"
            f"🧩 Words: {words or '—'}\n\n"
            f"{row.get('story_text' if is_story else 'palace_text') or ''}"
        )
        for chunk in _chunk_text(text):
            await message.answer(chunk)

@router.message(Command("story_tr"))
async def story_translation_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message): return
    user_id = message.from_user.id
    parts = (message.text or "").split(maxsplit=1)
    arg = parts[1].strip() if len(parts) > 1 else ""

    if not arg or arg.lower() in {"list", "show"}:
        current = story_translation_overrides.get(user_id, {})
        rows = [f"- {w}: {t}" for w, t in sorted(current.items())] if current else ["- Դեռ չկան"]
        await message.answer("📘 Custom translations\n" + "\n".join(rows))
    elif arg.lower() in {"clear", "reset"}:
        story_translation_overrides.pop(user_id, None)
        await message.answer("🧹 Custom թարգմանությունները մաքրվեցին։")
    else:
        pairs = _parse_story_translation_pairs(arg)
        if not pairs:
            await message.answer("❗ Ֆորմատը սխալ է։\nՕրինակ՝ /story_tr desk=գրասեղան")
            return
        story_translation_overrides.setdefault(user_id, {}).update(pairs)
        await message.answer("✅ Glossary թարմացվեց։")