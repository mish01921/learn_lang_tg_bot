import asyncio
import random
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.bot.ui import (
    get_placement_start_keyboard,
    get_pomodoro_keyboard,
    get_start_new_word_keyboard,
    get_test_options_keyboard,
)
from src.core.app_state import (
    clear_user_waiting_states,
    get_user_lock,
    pomodoro_sessions,
    practice_waiting_users,
    processed_callbacks,
    pronunciation_waiting_users,
    record_temp_message,
    record_word_action,
    register_processed_callback,
    review_sessions,
    test_sessions,
)
from src.core.i18n import get_lang, t
from src.data.api_words import (
    COMMON_WORDS,
    get_practice_analysis_gemini,
    get_word_data,
)
from src.database.models import (
    get_learned_words,
    get_seen_words,
    get_user_level,
    increment_daily,
    increment_daily_pomodoro,
    increment_daily_practice,
    is_placement_done,
    record_answer,
)
from src.utils.audio import send_word_pronunciation, verify_pronunciation_with_ai
from src.utils.bot_helpers import (
    _edit_review_flashcard,
    _grade_tag,
    maybe_promote_level,
    send_next_word_card,
    send_previous_word_card,
    send_review_list,
)
from src.utils.utils import (
    reject_if_banned_callback,
    reject_if_banned_message,
    safe_edit_text,
    touch_user_from_message,
)

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
    lang = get_lang(user_id)
    text = t("test_question", lang, index=idx + 1, total=total, translation=translation)
    return text, get_test_options_keyboard(options, session["id"])


@router.message(Command("study"))
async def study_command_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    user_id = message.from_user.id
    level = await get_user_level(user_id)
    if not await is_placement_done(user_id):
        await message.answer(
            "👋 Բարի գալուստ։ Նախքան սովորելը անցիր արագ թեստ՝ մակարդակդ որոշելու համար, կամ ընտրիր ինքդ։",
            reply_markup=get_placement_start_keyboard(),
        )
        return

    sent = await send_next_word_card(message, user_id, level)
    if not sent:
        await message.answer("✨ Այս պահին նոր բառ չկա, կամ օրական լիմիտը սպառված է։ Փորձիր /review կամ /learned 🚀")


@router.message(Command("word"))
async def send_word_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    user_id = message.from_user.id
    if not await is_placement_done(user_id):
        await message.answer(
            "👋 Բարի գալուստ։ Նախքան սովորելը անցիր արագ թեստ՝ մակարդակդ որոշելու համար, կամ ընտրիր ինքդ։",
            reply_markup=get_placement_start_keyboard(),
        )
        return

    level = await maybe_promote_level(user_id, message)
    sent = await send_next_word_card(message, user_id, level)
    if not sent:
        await message.answer("✨ Հիանալի առաջընթաց։ Այս պահին նոր քարտ չի գտնվել, փորձիր քիչ հետո։")


@router.callback_query(F.data.startswith("word:"))
async def word_callback_handler(callback: CallbackQuery):
    import logging; logging.info(f"Callback received: {callback.data} from user {callback.from_user.id}")
    if await reject_if_banned_callback(callback):
        return
    user_id = callback.from_user.id
    lang = get_lang(user_id)

    if callback.id in processed_callbacks:
        await callback.answer()
        return

    lock = get_user_lock(user_id)
    if lock.locked():
        await callback.answer()
        return

    async with lock:
        register_processed_callback(callback.id)

        parts = callback.data.split(":")
        action = parts[1]

        if action in {"again", "hard", "good", "easy"}:
            word = parts[2]
            await record_answer(user_id, word, correct=(action in {"hard", "good", "easy"}), grade=action)
            await increment_daily(user_id, word)
            await callback.answer(f"Գրանցվեց որպես {action.title()} ✅")
            await send_next_word_card(callback.message, user_id, await maybe_promote_level(user_id))

        elif action == "next":
            await callback.answer(t("toast_next_word", lang))
            await send_next_word_card(callback.message, user_id, await maybe_promote_level(user_id))

        elif action == "back":
            await callback.answer(t("toast_prev_word", lang))
            await send_previous_word_card(callback.message, user_id)

        elif action == "practice":
            word = parts[2]
            clear_user_waiting_states(user_id)
            practice_waiting_users[user_id] = word
            logging.info(f"Set practice_waiting_users for user {user_id} to word '{word}'")
            sent = await callback.message.answer(
                t("practice_intro", lang, word=word),
                parse_mode="Markdown"
            )
            record_temp_message(user_id, sent.message_id)
            await callback.answer()

        elif action == "pronounce":
            word = parts[2]
            clear_user_waiting_states(user_id)
            pronunciation_waiting_users[user_id] = word
            sent = await callback.message.answer(
                t("pronounce_intro", lang, word=word),
                parse_mode="Markdown"
            )
            record_temp_message(user_id, sent.message_id)
            await callback.answer()


@router.message(Command("pomodoro"))
async def pomodoro_command_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    user_id = message.from_user.id
    lang = get_lang(user_id)

    if user_id in pomodoro_sessions:
        elapsed = datetime.now() - pomodoro_sessions[user_id]
        remaining_seconds = max(0, int(25 * 60 - elapsed.total_seconds()))

        if remaining_seconds > 0:
            mins, secs = divmod(remaining_seconds, 60)
            time_str = f"{mins:02d}:{secs:02d}"

            total_seconds = 25 * 60
            progress_pct = int((elapsed.total_seconds() / total_seconds) * 100)
            bar_len = 10
            filled_len = int(bar_len * progress_pct / 100)
            bar = "■" * filled_len + "□" * (bar_len - filled_len)

            await message.answer(
                t("pomo_active_progress", lang, time_str=time_str, bar=bar, pct=progress_pct),
                reply_markup=get_pomodoro_keyboard(is_active=True, lang=lang)
            )
            return

    await message.answer(
        t("pomo_intro", lang),
        reply_markup=get_pomodoro_keyboard(lang=lang)
    )


@router.callback_query(F.data.startswith("pomodoro:"))
async def pomodoro_callback_handler(callback: CallbackQuery):
    action = callback.data.split(":")[1]
    user_id = callback.from_user.id
    lang = get_lang(user_id)

    if action == "start":
        start_time = datetime.now()
        pomodoro_sessions[user_id] = start_time

        # Calculate initial progress bar
        bar = "□" * 10
        await safe_edit_text(
            callback.message,
            t("pomo_active_progress", lang, time_str="25:00", bar=bar, pct=0),
            reply_markup=get_pomodoro_keyboard(is_active=True, lang=lang)
        )
        await callback.answer()

        async def alert_after_focus():
            total_seconds = 25 * 60
            update_interval = 5
            steps = total_seconds // update_interval
            chat_id = callback.message.chat.id
            message_id = callback.message.message_id

            for _ in range(steps):
                await asyncio.sleep(update_interval)

                # Check if session was stopped or restarted
                if user_id not in pomodoro_sessions or pomodoro_sessions[user_id] != start_time:
                    return

                elapsed = datetime.now() - start_time
                remaining = int(total_seconds - elapsed.total_seconds())
                if remaining <= 0:
                    break

                # Calculate progress bar
                progress_pct = int((elapsed.total_seconds() / total_seconds) * 100)
                bar_len = 10
                filled_len = int(bar_len * progress_pct / 100)
                bar = "■" * filled_len + "□" * (bar_len - filled_len)

                mins, secs = divmod(remaining, 60)
                time_str = f"{mins:02d}:{secs:02d}"

                try:
                    await callback.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=t("pomo_active_progress", lang, time_str=time_str, bar=bar, pct=progress_pct),
                        reply_markup=get_pomodoro_keyboard(is_active=True, lang=lang)
                    )
                except Exception:
                    pass

            if user_id in pomodoro_sessions and pomodoro_sessions[user_id] == start_time:
                try:
                    await increment_daily_pomodoro(user_id)
                    await callback.bot.send_message(
                        user_id,
                        t("pomo_finished", lang),
                        reply_markup=get_pomodoro_keyboard(is_active=False, lang=lang),
                        disable_notification=False
                    )
                except Exception:
                    pass
                finally:
                    pomodoro_sessions.pop(user_id, None)

        asyncio.create_task(alert_after_focus())

    elif action == "refresh":
        if user_id not in pomodoro_sessions:
            await safe_edit_text(callback.message, t("pomo_not_active", lang), reply_markup=get_pomodoro_keyboard(lang=lang))
            await callback.answer()
            return

        elapsed = datetime.now() - pomodoro_sessions[user_id]
        remaining_seconds = max(0, int(25 * 60 - elapsed.total_seconds()))

        if remaining_seconds == 0:
            await callback.answer("⏳ 00:00")
            return

        mins, secs = divmod(remaining_seconds, 60)
        time_str = f"{mins:02d}:{secs:02d}"

        total_seconds = 25 * 60
        progress_pct = int((elapsed.total_seconds() / total_seconds) * 100)
        bar_len = 10
        filled_len = int(bar_len * progress_pct / 100)
        bar = "■" * filled_len + "□" * (bar_len - filled_len)

        await safe_edit_text(
            callback.message,
            t("pomo_active_progress", lang, time_str=time_str, bar=bar, pct=progress_pct),
            reply_markup=get_pomodoro_keyboard(is_active=True, lang=lang)
        )
        await callback.answer(f"{time_str}")

    elif action == "stop":
        if user_id in pomodoro_sessions:
            del pomodoro_sessions[user_id]
        await safe_edit_text(callback.message, t("pomo_stopped", lang), reply_markup=get_pomodoro_keyboard(lang=lang))
        await callback.answer()


@router.message(F.text & ~F.text.startswith('/') & F.from_user.id.func(lambda uid: uid in practice_waiting_users))
async def practice_message_handler(message: Message):
    import logging; logging.info(f"Practice message handler triggered for user {message.from_user.id}")
    user_id = message.from_user.id
    word = practice_waiting_users.pop(user_id, None)
    if not word:
        return
    record_temp_message(user_id, message.message_id)

    lang = get_lang(user_id)
    msg = await message.answer(t("practice_analyzing", lang, word=word))
    record_temp_message(user_id, msg.message_id)

    level = await get_user_level(user_id)
    response = await get_practice_analysis_gemini(word, message.text or "", level=level, lang=lang)
    # Increment daily practice count in database
    await increment_daily_practice(user_id)
    header = t("practice_header", lang, word=word)
    try:
        await msg.edit_text(f"{header}\n\n{response}", parse_mode="Markdown")
        record_word_action(user_id, {"type": "text", "text": f"{header}\n\n{response}", "parse_mode": "Markdown"})
    except Exception:
        await msg.edit_text(f"{header}\n\n{response}")
        record_word_action(user_id, {"type": "text", "text": f"{header}\n\n{response}"})


@router.message(Command("review"))
async def review_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    await send_review_list(message, message.from_user.id)


@router.message(Command("learned"))
async def learned_handler(message: Message):
    from src.core.texts import format_date
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    words = await get_learned_words(message.from_user.id)
    if not words:
        await message.answer("📚 Դեռ սովորած բառեր չկան։ Սկսիր /word ✨")
        return
    lines = [f"{i}. {w['word']}  [{_grade_tag(w.get('last_grade'))}] ({format_date(w.get('learned_at'))})" for i, w in enumerate(words, 1)]
    await message.answer("✅ Սովորած բառեր\n\n" + "\n".join(lines))


@router.callback_query(F.data.startswith("review:"))
async def review_flashcard_handler(callback: CallbackQuery):
    if await reject_if_banned_callback(callback):
        return
    user_id = callback.from_user.id
    if callback.id in processed_callbacks:
        await callback.answer()
        return
    register_processed_callback(callback.id)

    parts = callback.data.split(":")
    action = parts[1]
    session = review_sessions.get(user_id)

    if action == "start":
        if not session:
            await send_review_list(callback.message, user_id)
            await callback.answer()
            return
        session.update({"index": 0, "show_translation": False, "show_example": False})
        await _edit_review_flashcard(callback.message, user_id)
        await callback.answer()
        return

    # Handle show_tr, show_ex, next
    if not session:
        await callback.answer("Session չկա։", show_alert=True)
        return

    if action == "show_tr":
        session["show_translation"] = True
    elif action == "show_ex":
        session["show_example"] = True
    elif action in {"again", "hard", "good", "easy"}:
        word = parts[2]
        await record_answer(user_id, word, correct=(action in {"hard", "good", "easy"}), grade=action)
        # Auto-move to next
        session["index"] += 1
        session["show_translation"] = False
        session["show_example"] = False
    elif action == "next":
        session["index"] += 1
        session["show_translation"] = False
        session["show_example"] = False

    await _edit_review_flashcard(callback.message, user_id)
    await callback.answer()


@router.message(Command("test"))
async def test_handler(message: Message):
    user_id = message.from_user.id
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    lang = get_lang(user_id)
    seen_words = await get_seen_words(user_id, limit=300)
    if len(seen_words) < 4:
        await message.answer(
            t("test_need_words", lang),
            reply_markup=get_start_new_word_keyboard(lang)
        )
        return
    chosen = random.sample(seen_words, min(5, len(seen_words)))
    session = {"id": random.randint(1000, 999999), "words": chosen, "index": 0, "total": len(chosen), "score": 0}
    test_sessions[user_id] = session
    text, kb = await _build_test_question(user_id, session)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("test:ans:"))
async def test_answer_handler(callback: CallbackQuery):
    if await reject_if_banned_callback(callback):
        return
    user_id = callback.from_user.id
    session = test_sessions.get(user_id)
    if not session:
        await callback.answer("Test-ը ավարտված է։", show_alert=True)
        return
    parts = callback.data.split(":")
    # test:ans:session_id:word
    if str(session["id"]) != parts[2]:
        await callback.answer("Այս հարցը ակտիվ չէ։", show_alert=True)
        return
    if parts[3] == session.get("current_correct"):
        session["score"] += 1
        await callback.answer("Ճիշտ է ✅")
    else:
        await callback.answer("Սխալ է ❌")
    session["index"] += 1
    if session["index"] >= session["total"]:
        score, total = session["score"], session["total"]
        test_sessions.pop(user_id, None)
        lang = get_lang(user_id)
        await safe_edit_text(callback.message, t("test_completed", lang, score=score, total=total))
    else:
        text, kb = await _build_test_question(user_id, session)
        await safe_edit_text(callback.message, text, reply_markup=kb)


@router.message(F.voice & F.from_user.id.func(lambda uid: uid in pronunciation_waiting_users))
async def pronunciation_voice_handler(message: Message):
    user_id = message.from_user.id
    word = pronunciation_waiting_users.pop(user_id, None)
    if word:
        await verify_pronunciation_with_ai(message.bot, message, word)


@router.message(F.audio & F.from_user.id.func(lambda uid: uid in pronunciation_waiting_users))
async def pronunciation_audio_handler(message: Message):
    user_id = message.from_user.id
    word = pronunciation_waiting_users.pop(user_id, None)
    if word:
        await verify_pronunciation_with_ai(message.bot, message, word)


@router.message(
    F.document
    & F.from_user.id.func(lambda uid: uid in pronunciation_waiting_users)
    & F.document.mime_type.startswith("audio/")
)
async def pronunciation_document_handler(message: Message):
    user_id = message.from_user.id
    word = pronunciation_waiting_users.pop(user_id, None)
    if word:
        await verify_pronunciation_with_ai(message.bot, message, word)


@router.callback_query(F.data.startswith("audio:"))
async def audio_callback_handler(callback: CallbackQuery):
    if await reject_if_banned_callback(callback):
        return
    parts = callback.data.split(":")
    # Expected formats:
    # audio:<accent>:<word> (e.g. audio:us:hello)
    # audio:<word> (legacy fallback)

    if len(parts) >= 3:
        accent = parts[1]
        word = parts[2]
    elif len(parts) == 2:
        accent = "us"
        word = parts[1]
    else:
        await callback.answer()
        return

    await send_word_pronunciation(callback.bot, callback.message.chat.id, word, accent=accent)
    await callback.answer(f"Լսում ենք {accent.upper()} տարբերակը 🔊")
