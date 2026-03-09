from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery

from database import (
    get_stats,
    get_daily_count,
    reset_progress,
    is_placement_done,
    get_user_level,
    set_user_level,
    get_top_weak_words,
    get_hard_words,
    get_recent_accuracy,
    get_recent_accuracy_window,
    get_word_grade_map,
)
from utils import (
    touch_user_from_message,
    reject_if_banned_message,
    reject_if_banned_callback,
    is_unlimited_user,
    parse_positive_int_arg,
)
from config import ADMIN_USER_IDS
from api_words import COMMON_WORDS
from level_words import load_levelled_words as _load_levelled_words, chunk_text as _chunk_text
from texts import build_start_text, build_coach_text
from ui import get_placement_start_keyboard, get_level_keyboard, get_coach_keyboard, get_search_keyboard
from bot_helpers import _build_levels_lock_text, _grade_tag, send_review_list, send_next_word_card, maybe_promote_level
from config import DAILY_LIMIT, WORD_LEVEL_CHOICES

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    placement_done = await is_placement_done(message.from_user.id)
    name = message.from_user.first_name or "Բարև"
    is_unlimited = is_unlimited_user(message.from_user.id)
    await message.answer(
        build_start_text(
            name,
            len(COMMON_WORDS),
            DAILY_LIMIT,
            is_admin=is_unlimited,
        )
    )
    if not placement_done and not is_unlimited:
        await message.answer(
            "🎯 Նախքան բառերը սկսելը, անցիր placement test-ը։\n"
            "Սա կընտրի քո CEFR մակարդակը և կփակի մնացած մակարդակները մինչև առաջընթաց։",
            reply_markup=get_placement_start_keyboard(),
        )
    else:
        current_level = await get_user_level(message.from_user.id)
        await message.answer(
            _build_levels_lock_text(current_level, True, unlock_all=is_unlimited),
            reply_markup=get_level_keyboard(current_level, True, unlock_all=is_unlimited),
        )

@router.message(Command("levels"))
async def levels_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    user_id = message.from_user.id
    is_unlimited = is_unlimited_user(user_id)
    placement_done = is_unlimited or await is_placement_done(user_id)
    current_level = await get_user_level(user_id)
    await message.answer(
        _build_levels_lock_text(current_level, placement_done, unlock_all=is_unlimited),
        reply_markup=get_level_keyboard(current_level, placement_done, unlock_all=is_unlimited),
    )

@router.callback_query(F.data.startswith("level:"))
async def level_select_handler(callback: CallbackQuery):
    from utils import safe_edit_text
    if await reject_if_banned_callback(callback):
        return
    user_id = callback.from_user.id
    is_unlimited = is_unlimited_user(user_id)
    if not is_unlimited and not await is_placement_done(user_id):
        await callback.answer("Սկզբում անցեք placement test-ը։", show_alert=True)
        return
    _, _, level = (callback.data or "").partition(":")
    level = (level or "A1").upper()
    if level not in WORD_LEVEL_CHOICES:
        await callback.answer("Սխալ մակարդակ", show_alert=True)
        return

    current_level = await get_user_level(user_id)
    if not is_unlimited and level != current_level:
        await callback.answer(
            f"🔒 Այս պահին բաց է միայն {current_level} մակարդակը։",
            show_alert=True,
        )
        return

    await set_user_level(user_id, level)
    await callback.answer(f"Մակարդակը փոխվեց՝ {level}։ Շարունակելու համար սեղմեք /word։")
    await maybe_promote_level(user_id, callback.message)

@router.message(Command("stats"))
async def stats_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    user_id = message.from_user.id
    s = await get_stats(user_id, len(COMMON_WORDS))
    daily_count = await get_daily_count(user_id)
    daily_limit_label = "∞" if is_unlimited_user(user_id) else str(DAILY_LIMIT)

    await message.answer(
        f"📊 Վիճակագրություն\n\n"
        f"✅ Սովորած՝ {s['learned']}/{s['total']} ({s['progress_pct']}%)\n"
        f"👀 Տեսած՝ {s['seen']} բառ\n"
        f"🆕 Չտեսած՝ {s['unseen']} բառ\n"
        f"📅 Այսօր՝ {daily_count}/{daily_limit_label} բառ\n"
        f"📘 Սովորելու ցուցակ՝ {s['hard']} բառ\n"
        f"🎯 Ճշտություն՝ {s['accuracy']}%\n"
        f"📆 Streak՝ {s['streak']} օր"
    )

@router.message(Command("coach"))
async def coach_handler(message: Message):
    user_id = message.from_user.id
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return

    s = await get_stats(user_id, len(COMMON_WORDS))
    daily_count = await get_daily_count(user_id)
    level = await get_user_level(user_id)
    recent_accuracy = await get_recent_accuracy(user_id, limit=20)
    prev_accuracy = await get_recent_accuracy_window(user_id, limit=20, offset=20)
    weak_words = await get_top_weak_words(user_id, limit=3)
    hard_words = await get_hard_words(user_id)

    if prev_accuracy is None:
        trend_text = "բավարար տվյալ չկա"
    else:
        delta = recent_accuracy - prev_accuracy
        if delta > 5: trend_text = f"📈 աճ {delta}%"
        elif delta < -5: trend_text = f"📉 անկում {abs(delta)}%"
        else: trend_text = "➡️ կայուն"

    focus_words = [w["word"] for w in weak_words[:2]]
    for w in hard_words:
        word = w.get("word")
        if word and word not in focus_words:
            focus_words.append(word)
        if len(focus_words) >= 3:
            break

    is_unlimited = is_unlimited_user(user_id)
    remaining_new = max(0, DAILY_LIMIT - daily_count) if not is_unlimited else None
    plan_steps: list[str] = []
    if s["due_today"] > 0 or s["hard"] > 0:
        plan_steps.append("Սկսեք /review-ով և անցեք առնվազն 3 սովորելու բառ")
    if remaining_new and remaining_new > 0:
        plan_steps.append(f"Անցեք /word և վերցրեք ևս {remaining_new} նոր բառ")
    elif is_unlimited:
        plan_steps.append("Դուք ադմին եք, /word-ը անսահմանափակ է այսօր")
    if not plan_steps:
        plan_steps.append("Այսօրվա նպատակը կատարված է, պահեք streak-ը վաղը /word-ով")

    await message.answer(
        build_coach_text(
            level=level, today_count=daily_count, daily_limit=DAILY_LIMIT if not is_unlimited else daily_count + 1,
            overall_accuracy=s["accuracy"], recent_accuracy=recent_accuracy, trend_text=trend_text,
            due_today=s["due_today"], hard_count=s["hard"], weak_words=weak_words,
            focus_words=focus_words, plan_steps=plan_steps,
        ),
        reply_markup=get_coach_keyboard(focus_words[0] if focus_words else None),
    )

@router.callback_query(F.data.startswith("coach:"))
async def coach_callback_handler(callback: CallbackQuery):
    from api_words import get_word_data
    from level_words import find_word_levels
    from texts import format_searched_word

    if await reject_if_banned_callback(callback): return
    user_id = callback.from_user.id

    data = callback.data or ""
    _, _, payload = data.partition(":")
    action, _, word = payload.partition(":")

    if action == "review":
        sent = await send_review_list(callback.message, user_id)
        await callback.answer("Բացվեց սովորելու ցուցակը 🚀" if sent else "Դեռ սովորելու բառ չկա, շարունակիր /word ✨")
    elif action == "new":
        level = await get_user_level(user_id)
        sent = await send_next_word_card(callback.message, user_id, level)
        await callback.answer("Ուղարկվեց հաջորդ բառը 🚀" if sent else "Նոր բառ հիմա հասանելի չէ")
    elif action == "focus" and word:
        word_data = await get_word_data(word)
        levels = await find_word_levels(word)
        await callback.message.answer(format_searched_word(word_data, levels), reply_markup=get_search_keyboard(word))
        await callback.answer("Focus բառը բացվեց ✅")
    else:
        await callback.answer("Անհայտ գործողություն", show_alert=True)


async def _send_words_by_level(message: Message, level: str):
    user_id = message.from_user.id
    levels = _load_levelled_words()
    words = levels.get(level.upper()) or []
    if not words:
        await message.answer(f"❗ '{level}' մակարդակի բառեր չկան ֆայլում։")
        return

    grade_map = await get_word_grade_map(user_id, words)
    header = f"📚 Բառերի ցանկ՝ {level}\n\n"
    lines = [f"{i}. {w}  [{_grade_tag(grade_map.get(w.lower()))}]" for i, w in enumerate(words, 1)]
    full_text = header + "\n".join(lines)
    for chunk in _chunk_text(full_text):
        await message.answer(chunk)

@router.message(Command("all_words_A1", "all_words_A2", "all_words_B1", "all_words_B2"))
async def all_words_level_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message): return
    level = (message.text or "").strip().split("_")[-1].upper()
    await _send_words_by_level(message, level)

@router.message(Command("reset"))
async def reset_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message): return
    await reset_progress(message.from_user.id, preserve_history=True)
    await message.answer("♻️ Reset արվեց։ Ձեր learned/seen բառերը պահպանվել են։")

@router.message(Command("reset_all"))
async def reset_all_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message): return
    await reset_progress(message.from_user.id, preserve_history=False)
    await message.answer("⚠️ Ձեր ամբողջ history-ն ջնջվեց։")