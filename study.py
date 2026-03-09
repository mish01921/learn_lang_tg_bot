import asyncio
import random
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import (
    is_placement_done,
    get_seen_words,
    get_learned_words,
    get_hard_words,
    record_answer,
    increment_daily,
    mark_word_learned,
)
from utils import (
    touch_user_from_message,
    reject_if_banned_message,
    reject_if_banned_callback,
    is_unlimited_user,
    safe_edit_text,
)
from app_state import (
    processed_callbacks,
    user_locks,
    test_sessions,
    review_sessions,
    register_processed_callback,
)
from ui import get_test_options_keyboard, get_review_start_keyboard, get_review_flashcard_keyboard, get_placement_start_keyboard
from api_words import get_word_data, COMMON_WORDS, get_ai_example_sentences
from bot_helpers import (
    maybe_promote_level,
    send_next_word_card,
    send_review_list,
    _build_review_flashcard_text,
    _edit_review_flashcard,
    _grade_tag,
)
from level_words import find_word_levels

router = Router()


async def _build_test_question(user_id: int, session: dict) -> tuple[str, object]:
    idx = session["index"]
    words = session["words"]
    total = session["total"]
    correct_word = words[idx]
    correct_data = await get_word_data(correct_word)
    translation = correct_data.get("translation", "—") or "—"

    pool = [w for w in words if w != correct_word]
    if len(pool) >= 3:
        distractors = random.sample(pool, 3)
    else:
        fallback_pool = [w for w in COMMON_WORDS if w != correct_word and w not in pool]
        need = 3 - len(pool)
        distractors = pool + random.sample(fallback_pool, min(need, len(fallback_pool)))

    options = [correct_word, *distractors[:3]]
    random.shuffle(options)
    session["current_correct"] = correct_word
    text = (
        f"🧪 Test [{idx + 1}/{total}]\n\n"
        f"Ընտրիր ճիշտ անգլերեն բառը այս թարգմանության համար.\n"
        f"🇦🇲 {translation}"
    )
    return text, get_test_options_keyboard(options, session["id"])


@router.message(Command("word"))
async def send_word_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    user_id = message.from_user.id
    if not is_unlimited_user(user_id) and not await is_placement_done(user_id):
        await message.answer("📝 Սկզբում պետք է անցնել placement test-ը։", reply_markup=get_placement_start_keyboard())
        return

    level = await maybe_promote_level(user_id, message)
    sent = await send_next_word_card(message, user_id, level)
    if not sent:
        await message.answer("✨ Հիանալի առաջընթաց։ Այս պահին նոր քարտ չի գտնվել, փորձիր քիչ հետո։")


@router.callback_query(F.data.startswith(("again:", "hard:", "good:", "easy:", "next:", "pronounce:", "master:")))
async def srs_callback_handler(callback: CallbackQuery):
    from ui import get_story_genre_keyboard
    if await reject_if_banned_callback(callback): return
    user_id = callback.from_user.id

    if callback.id in processed_callbacks:
        await callback.answer("Խնդրում եմ մի սեղմեք բազմիցս։", show_alert=False)
        return
    register_processed_callback(callback.id)

    lock = user_locks.setdefault(user_id, asyncio.Lock())
    async with lock:
        data = callback.data or ""
        action, _, word_from_cb = data.partition(":")
        current_word = word_from_cb.strip()

        if action in {"again", "hard", "good", "easy"}:
            await record_answer(user_id, current_word, correct=(action in {"hard", "good", "easy"}), grade=action)
            await increment_daily(user_id, current_word)
            await callback.answer(f"Գրանցվեց որպես {action.title()} ✅")
            await maybe_promote_level(user_id, callback.message)
            await send_next_word_card(callback.message, user_id, await maybe_promote_level(user_id))

        elif action == "next":
            await callback.answer("Բացում եմ հաջորդ բառը 🚀")
            await send_next_word_card(callback.message, user_id, await maybe_promote_level(user_id))

        elif action == "pronounce":
            levels = find_word_levels(current_word)
            level = levels[0] if levels else ""
            word_data = await get_word_data(current_word, level=level)
            audio_url = (word_data.get("audio_url") or "").strip()
            if audio_url:
                await callback.message.answer_voice(voice=audio_url, caption=f"🔊 {current_word}")
                await callback.answer("Արտասանությունը ուղարկվեց 🔊")
            else:
                await callback.answer("Այս բառի համար ձայնային արտասանություն չի գտնվել։", show_alert=True)

        elif action == "master":
            if await mark_word_learned(user_id, current_word):
                await safe_edit_text(callback.message, f"✅ '{current_word}' տեղափոխվեց /learned։")
                await callback.answer("Սուպեր, տեղափոխվեց սովորած բառեր ✅")
            else:
                await callback.answer("Չհաջողվեց տեղափոխել բառը։", show_alert=True)


@router.message(Command("review"))
async def review_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message): return
    await send_review_list(message, message.from_user.id)


@router.message(Command("learned"))
async def learned_handler(message: Message):
    from texts import format_date
    await touch_user_from_message(message)
    if await reject_if_banned_message(message): return
    words = await get_learned_words(message.from_user.id)
    if not words:
        await message.answer("📚 Դեռ սովորած բառեր չկան։ Սկսիր /word ✨")
        return

    lines = [f"{i}. {w['word']}  [{_grade_tag(w.get('last_grade'))}] ({format_date(w.get('learned_at'))})" for i, w in enumerate(words, 1)]
    await message.answer("✅ Սովորած բառեր\n\n" + "\n".join(lines))


@router.callback_query(F.data.startswith("rvc:"))
async def review_flashcard_handler(callback: CallbackQuery):
    if await reject_if_banned_callback(callback): return
    user_id = callback.from_user.id
    if callback.id in processed_callbacks:
        await callback.answer("Խնդրում եմ մի սեղմեք բազմիցս։", show_alert=False)
        return
    register_processed_callback(callback.id)

    data = callback.data or ""
    parts = data.split(":", 2)
    action = parts[1] if len(parts) > 1 else ""
    word_from_cb = parts[2].strip() if len(parts) > 2 else ""

    session = review_sessions.get(user_id)
    if action == "start":
        if not session:
            await send_review_list(callback.message, user_id)
            await callback.answer("Review ցանկը թարմացվեց ✅")
            return
        session.update({"index": 0, "show_translation": False, "show_example": False})
        await _edit_review_flashcard(callback.message, user_id)
        await callback.answer("Սկսեցինք flashcards 🚀")
        return

    if not session:
        await callback.answer("Session չկա։ Սկսեք /review-ով։", show_alert=True)
        return

    words, idx = session.get("words", []), session.get("index", 0)
    if not words or idx >= len(words):
        await _edit_review_flashcard(callback.message, user_id) # Will show completion message
        return

    if word_from_cb and word_from_cb != words[idx]:
        await callback.answer("Այս քարտը արդեն թարմացված է։", show_alert=False)
        return

    if action == "show_tr": session["show_translation"] = True
    elif action == "show_ex": session["show_example"] = True
    elif action == "next":
        session["index"] += 1
        session.update({"show_translation": False, "show_example": False})
    elif action == "master":
        if await mark_word_learned(user_id, words[idx]):
            words.pop(idx)
            session.update({"show_translation": False, "show_example": False})

    await _edit_review_flashcard(callback.message, user_id)
    await callback.answer()


@router.message(Command("test"))
async def test_handler(message: Message):
    user_id = message.from_user.id
    await touch_user_from_message(message)
    if await reject_if_banned_message(message): return

    seen_words = await get_seen_words(user_id, limit=300)
    if len(seen_words) < 4:
        await message.answer("🧪 Test սկսելու համար պետք է առնվազն 4 անցած բառ։")
        return

    chosen = random.sample(seen_words, min(5, len(seen_words)))
    session = {"id": random.randint(1000, 999999), "words": chosen, "index": 0, "total": len(chosen), "score": 0}
    test_sessions[user_id] = session
    text, kb = await _build_test_question(user_id, session)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("testans:"))
async def test_answer_handler(callback: CallbackQuery):
    if await reject_if_banned_callback(callback): return
    user_id = callback.from_user.id
    session = test_sessions.get(user_id)
    if not session:
        await callback.answer("Test-ը ավարտված է։", show_alert=True)
        return

    _, sid_raw, selected_word = (callback.data or "").split(":", 2)
    if str(session["id"]) != sid_raw:
        await callback.answer("Այս հարցը այլևս ակտիվ չէ։", show_alert=True)
        return

    if selected_word == session.get("current_correct"):
        session["score"] += 1
        await callback.answer("Ճիշտ է ✅")
    else:
        await callback.answer(f"Սխալ է ❌ Ճիշտը՝ {session.get('current_correct')}")

    session["index"] += 1
    if session["index"] >= session["total"]:
        score, total = session["score"], session["total"]
        test_sessions.pop(user_id, None)
        await safe_edit_text(callback.message, f"🏁 Test ավարտվեց\n\nԱրդյունք՝ {score}/{total}")
    else:
        text, kb = await _build_test_question(user_id, session)
        await safe_edit_text(callback.message, text, reply_markup=kb)