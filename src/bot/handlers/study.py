import asyncio
import random
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.bot.ui import (
    get_placement_start_keyboard,
    get_pomodoro_keyboard,
    get_test_options_keyboard,
)
from src.core.app_state import (
    pomodoro_sessions,
    practice_waiting_users,
    pronunciation_waiting_users,
    processed_callbacks,
    register_processed_callback,
    review_sessions,
    test_sessions,
)
from src.data.api_words import (
    COMMON_WORDS,
    _get_http_session,
    get_tutor_explanation_gemini,
    get_word_data,
)
from src.utils.audio import send_word_pronunciation, verify_pronunciation_with_ai
from src.database.models import (
    get_learned_words,
    get_seen_words,
    increment_daily,
    is_placement_done,
    record_answer,
)
from src.utils.bot_helpers import (
    _edit_review_flashcard,
    _grade_tag,
    maybe_promote_level,
    send_next_word_card,
    send_review_list,
)
from src.utils.utils import (
    is_unlimited_user,
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


@router.callback_query(F.data.startswith("word:"))
async def word_callback_handler(callback: CallbackQuery):
    if await reject_if_banned_callback(callback):
        return
    user_id = callback.from_user.id

    if callback.id in processed_callbacks:
        await callback.answer()
        return
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
        await callback.answer("Բացում եմ հաջորդ բառը 🚀")
        await send_next_word_card(callback.message, user_id, await maybe_promote_level(user_id))

    elif action == "practice":
        word = parts[2]
        practice_waiting_users[user_id] = word
        await callback.message.answer(f"🧠 **Interactive Task:**\nԿազմիր նախադասություն «**{word}**» բառով։\nԵս կստուգեմ այն և կտամ խորհուրդներ։")
        await callback.answer()

    elif action == "pronounce":
        word = parts[2]
        pronunciation_waiting_users[user_id] = word
        await callback.message.answer(f"🎙️ **Pronunciation Task:**\nԽնդրում եմ արտասանել «**{word}**» բառը ձայնային հաղորդագրությամբ (Voice)։\nԵս կվերլուծեմ քո արտասանությունը ELSA-ի նման։")
        await callback.answer()


@router.message(Command("pomodoro"))
async def pomodoro_command_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    user_id = message.from_user.id

    if user_id in pomodoro_sessions:
        # Show existing session instead of start screen
        elapsed = datetime.now() - pomodoro_sessions[user_id]
        remaining_seconds = max(0, int(25 * 60 - elapsed.total_seconds()))

        if remaining_seconds > 0:
            mins, secs = divmod(remaining_seconds, 60)
            time_str = f"{mins:02d}:{secs:02d}"
            await message.answer(
                f"🚀 **Դուք արդեն ունեք ակտիվ Focus Session:**\n\n"
                f"⏳ Մնացել է՝ `{time_str}`\n\n"
                "Շարունակիր սովորել 💪",
                reply_markup=get_pomodoro_keyboard(is_active=True)
            )
            return

    await message.answer(
        "⏱ **Pomodoro Timer**\n\n"
        "25 րոպեանոց ֆոկուս սեսիան կօգնի քեզ ավելի արդյունավետ սովորել առանց հոգնելու։\n"
        "Պատրա՞ստ ես սկսել։",
        reply_markup=get_pomodoro_keyboard()
    )


@router.callback_query(F.data.startswith("pomodoro:"))
async def pomodoro_callback_handler(callback: CallbackQuery):
    action = callback.data.split(":")[1]
    user_id = callback.from_user.id

    if action == "start":
        start_time = datetime.now()
        pomodoro_sessions[user_id] = start_time
        await safe_edit_text(
            callback.message,
            "🚀 **Focus Session-ը սկսվեց (25:00):**\n\n"
            "Այժմ կենտրոնացիր միայն բառեր սովորելու վրա։\n"
            "Սեղմիր «🔄 Թարմացնել», որպեսզի տեսնես մնացած ժամանակը։",
            reply_markup=get_pomodoro_keyboard(is_active=True)
        )
        await callback.answer()

        async def alert_after_focus():
            await asyncio.sleep(25 * 60)
            if user_id in pomodoro_sessions and pomodoro_sessions[user_id] == start_time:
                try:
                    await callback.bot.send_message(
                        user_id,
                        "🔔 **Ժամանակն ավարտվեց!**\n\n"
                        "Հիանալի աշխատանք։ Հիմա հանգստացիր 5 րոպե (Break), ապա կարող ես սկսել նորից։",
                        reply_markup=get_pomodoro_keyboard(is_active=False)
                    )
                    del pomodoro_sessions[user_id]
                except Exception:
                    pass
        asyncio.create_task(alert_after_focus())

    elif action == "refresh":
        if user_id not in pomodoro_sessions:
            await safe_edit_text(callback.message, "⏱ Session-ը ակտիվ չէ։", reply_markup=get_pomodoro_keyboard())
            await callback.answer()
            return

        elapsed = datetime.now() - pomodoro_sessions[user_id]
        remaining_seconds = max(0, int(25 * 60 - elapsed.total_seconds()))

        if remaining_seconds == 0:
            await callback.answer("⏳ Ժամանակը գրեթե սպառվել է։")
            return

        mins, secs = divmod(remaining_seconds, 60)
        time_str = f"{mins:02d}:{secs:02d}"

        await safe_edit_text(
            callback.message,
            f"🚀 **Focus Session-ը ընթացքի մեջ է:**\n\n"
            f"⏳ Մնացել է՝ `{time_str}`\n\n"
            "Շարունակիր սովորել 💪",
            reply_markup=get_pomodoro_keyboard(is_active=True)
        )
        await callback.answer(f"Մնացել է {time_str}")

    elif action == "stop":
        if user_id in pomodoro_sessions:
            del pomodoro_sessions[user_id]
        await safe_edit_text(callback.message, "⏹ Focus session-ը դադարեցված է։", reply_markup=get_pomodoro_keyboard())
        await callback.answer()


@router.message(F.text, lambda m: m.from_user.id in practice_waiting_users)
async def practice_message_handler(message: Message):
    user_id = message.from_user.id
    word = practice_waiting_users[user_id]
    del practice_waiting_users[user_id]

    msg = await message.answer("🧐 Վերլուծում եմ քո նախադասությունը...")

    prompt = (
        f"You are an expert English teacher. The student is practicing the word '{word}'. "
        f"They wrote this sentence: '{message.text}'. "
        f"Please:\n"
        f"1. Check if the usage of '{word}' is correct.\n"
        f"2. Correct any grammar mistakes.\n"
        f"3. Provide a more natural version if possible.\n"
        f"4. Give overall feedback and encouragement.\n"
        f"Respond in Armenian, but keep the English examples clearly visible."
    )

    session = await _get_http_session()
    response = await get_tutor_explanation_gemini(session, prompt)
    await msg.edit_text(f"📝 **Իմ վերլուծությունը:**\n\n{response}", parse_mode="Markdown")


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
    seen_words = await get_seen_words(user_id, limit=300)
    if len(seen_words) < 4:
        await message.answer("🧪 Test սկսելու համար պետք է առնվազն 4 անցած բառ։")
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
        await safe_edit_text(callback.message, f"🏁 Test ավարտվեց\n\nԱրդյունք՝ {score}/{total}")
    else:
        text, kb = await _build_test_question(user_id, session)
        await safe_edit_text(callback.message, text, reply_markup=kb)


@router.message(F.voice, lambda m: m.from_user.id in pronunciation_waiting_users)
async def pronunciation_voice_handler(message: Message):
    user_id = message.from_user.id
    word = pronunciation_waiting_users[user_id]
    del pronunciation_waiting_users[user_id]

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
