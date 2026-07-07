import random

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from src.bot.ui import get_test_options_keyboard
from src.core.app_state import level_test_sessions
from src.core.i18n import get_lang, t
from src.data.placement_questions import CEFR_PLACEMENT_QUESTIONS
from src.database.models import get_user_level, set_user_level, record_failed_level_test, can_take_level_test
from src.utils.utils import (
    reject_if_banned_callback,
    safe_edit_text,
)

router = Router()

def _build_level_test_question_text(question: dict, index: int, total: int, target_level: str) -> str:
    lines = [f"📝 Level Test ({target_level}) [{index}/{total}]", "", question["prompt"]]
    options = question.get("options") or []
    letters = ["A", "B", "C", "D"]
    for i, opt in enumerate(options):
        label = letters[i] if i < len(letters) else str(i + 1)
        lines.append(f"{label}) {opt}")
    return "\n".join(lines)

def get_level_test_options_keyboard(options: list[str], session_id: int):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    rows = []
    for opt in options:
        rows.append([InlineKeyboardButton(text=opt, callback_data=f"lvltest:ans:{session_id}:{opt}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.callback_query(F.data.startswith("leveltest:start:"))
async def level_test_start_handler(callback: CallbackQuery):
    if await reject_if_banned_callback(callback):
        return
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Error", show_alert=True)
        return
    
    target_level = parts[2]
    
    if not await can_take_level_test(user_id, target_level):
        await callback.answer(t("level_test_failed_today", lang, level=target_level), show_alert=True)
        return

    # Filter questions for this level
    pool = [q for q in CEFR_PLACEMENT_QUESTIONS if q["level"] == target_level]
    if not pool:
        # Fallback if there are no questions for this level
        await set_user_level(user_id, target_level)
        await callback.answer(t("level_changed", lang, level=target_level), show_alert=True)
        from src.bot.handlers.general import maybe_promote_level
        await maybe_promote_level(user_id, callback.message)
        return

    # Shuffle and limit
    random.shuffle(pool)
    questions = pool[:5]  # use up to 5 questions
    
    level_test_sessions[user_id] = {
        "target_level": target_level,
        "questions": questions,
        "current_idx": 0,
        "score": 0,
    }

    q = questions[0]
    opts = ["A", "B", "C", "D"][: len(q["options"])]
    text = _build_level_test_question_text(q, 1, len(questions), target_level)
    markup = get_level_test_options_keyboard(opts, user_id)

    await safe_edit_text(callback.message, text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("lvltest:ans:"))
async def level_test_answer_handler(callback: CallbackQuery):
    if await reject_if_banned_callback(callback):
        return
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("Error")
        return
        
    session_id = int(parts[2])
    ans_str = parts[3]
    
    session = level_test_sessions.get(session_id)
    if not session:
        await callback.answer("Test session expired or invalid.", show_alert=True)
        return

    # Check if the click is from the user who started it
    if user_id != session_id:
        await callback.answer("Not your session", show_alert=True)
        return

    idx = session["current_idx"]
    questions = session["questions"]
    q = questions[idx]

    letters = ["A", "B", "C", "D"]
    try:
        ans_idx = letters.index(ans_str)
    except ValueError:
        ans_idx = -1

    if ans_idx == q["answer"]:
        session["score"] += 1

    session["current_idx"] += 1
    idx = session["current_idx"]

    if idx >= len(questions):
        # Finish
        score = session["score"]
        total = len(questions)
        target_level = session["target_level"]
        passing_score = max(1, int(total * 0.8)) # 80% passing

        level_test_sessions.pop(session_id, None)

        if score >= passing_score:
            await set_user_level(user_id, target_level)
            await safe_edit_text(
                callback.message, 
                t("level_test_passed", lang, level=target_level, score=score, total=total)
            )
            from src.bot.handlers.general import maybe_promote_level
            await maybe_promote_level(user_id, callback.message)
        else:
            await record_failed_level_test(user_id, target_level)
            await safe_edit_text(
                callback.message,
                t("level_test_failed", lang, score=score, total=total, passing=passing_score)
            )
        await callback.answer()
        return

    # Next question
    next_q = questions[idx]
    opts = letters[: len(next_q["options"])]
    text = _build_level_test_question_text(next_q, idx + 1, len(questions), session["target_level"])
    markup = get_level_test_options_keyboard(opts, session_id)

    await safe_edit_text(callback.message, text, reply_markup=markup)
    await callback.answer()
