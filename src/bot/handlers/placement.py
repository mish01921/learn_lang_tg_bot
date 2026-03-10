import random
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from src.database.models import is_placement_done, get_user_level, set_placement_result
from src.bot.ui import get_placement_start_keyboard, get_placement_options_keyboard
from src.core.app_state import placement_sessions
from src.data.placement_questions import CEFR_PLACEMENT_QUESTIONS
from src.utils.utils import (
    touch_user_from_message,
    reject_if_banned_message,
    reject_if_banned_callback,
    safe_edit_text
)

router = Router()

def _placement_level_from_score(score: int, total: int) -> str:
    if total <= 0:
        return "A1"
    pct = score * 100 / total
    if pct < 35:
        return "A1"
    if pct < 55:
        return "A2"
    if pct < 75:
        return "B1"
    return "B2"

def _build_placement_question_text(question: dict, index: int, total: int) -> str:
    lines = [f"📝 Placement Test [{index}/{total}] (CEFR aligned)", "", question["prompt"]]
    options = question.get("options") or []
    letters = ["A", "B", "C", "D"]
    for i, opt in enumerate(options):
        label = letters[i] if i < len(letters) else str(i + 1)
        lines.append(f"{label}) {opt}")
    return "\n".join(lines)

@router.message(Command("placement"))
async def placement_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    if await is_placement_done(message.from_user.id):
        level = await get_user_level(message.from_user.id)
        await message.answer(f"✅ Placement test-ը արդեն ավարտել եք։ Ձեր մակարդակը՝ {level}։ Շարունակենք առաջ 🚀")
        return
    await message.answer(
        "📝 Placement test-ը կօգնի որոշել ձեր մեկնարկային մակարդակը (A1-B2):",
        reply_markup=get_placement_start_keyboard(),
    )

@router.callback_query(F.data.startswith("placement:"))
async def placement_callback_handler(callback: CallbackQuery):
    if await reject_if_banned_callback(callback):
        return
    user_id = callback.from_user.id
    data = callback.data or ""
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "start":
        if await is_placement_done(user_id):
            await callback.answer("Placement test-ն արդեն ավարտել եք։")
            return
        qset = list(CEFR_PLACEMENT_QUESTIONS)
        random.shuffle(qset)
        session_id = random.randint(1000, 999999)
        placement_sessions[user_id] = {
            "id": session_id,
            "index": 0,
            "score": 0,
            "questions": qset,
            "total": len(qset),
        }
        q = qset[0]
        await safe_edit_text(
            callback.message,
            _build_placement_question_text(q, 1, len(qset)),
            reply_markup=get_placement_options_keyboard(q.get("options") or [], session_id),
        )
        await callback.answer("Placement սկսվեց")
        return

    if action == "ans":
        if len(parts) < 4:
            await callback.answer("Սխալ պատասխան", show_alert=True)
            return
        session = placement_sessions.get(user_id)
        if not session:
            await callback.answer("Placement session չկա։", show_alert=True)
            return
        try:
            sid = int(parts[2])
            selected = int(parts[3])
        except ValueError:
            await callback.answer("Սխալ տվյալ", show_alert=True)
            return
        if sid != int(session["id"]):
            await callback.answer("Այս հարցը ժամկետանց է։", show_alert=True)
            return

        idx = int(session["index"])
        questions = session["questions"]
        total = int(session["total"])
        if idx >= total:
            await callback.answer("Placement-ը արդեն ավարտված է։")
            return

        current_q = questions[idx]
        if selected == int(current_q.get("answer", -1)):
            session["score"] = int(session["score"]) + 1

        idx += 1
        session["index"] = idx
        if idx >= total:
            score = int(session["score"])
            level = _placement_level_from_score(score, total)
            await set_placement_result(user_id, level, score)
            placement_sessions.pop(user_id, None)
            await safe_edit_text(
                callback.message,
                "✅ Placement test ավարտվեց\n\n"
                f"Արդյունք: {score}/{total}\n"
                f"Ձեր մեկնարկային մակարդակը՝ {level}\n\n"
                "Այժմ կարող եք սկսել `/word` հրամանով։",
            )
            await callback.answer("Placement ավարտվեց")
            return

        next_q = questions[idx]
        await safe_edit_text(
            callback.message,
            _build_placement_question_text(next_q, idx + 1, total),
            reply_markup=get_placement_options_keyboard(next_q.get("options") or [], int(session["id"])),
        )
        await callback.answer()
        return

    await callback.answer("Անհայտ placement գործողություն", show_alert=True)