from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from src.bot.ui import (
    get_coach_keyboard,
    get_daily_roadmap_keyboard,
    get_level_keyboard,
    get_main_menu_keyboard,
    get_placement_start_keyboard,
    get_plan_selection_keyboard,
    get_search_keyboard,
)
from src.core.config import DAILY_LIMIT, WORD_LEVEL_CHOICES
from src.core.texts import build_start_text, HELP_TEXT
from src.data.api_words import COMMON_WORDS
from src.data.level_words import chunk_text as _chunk_text
from src.data.level_words import load_levelled_words as _load_levelled_words
from src.database.models import (
    count_story_generations_today,
    get_daily_count,
    get_stats,
    get_top_weak_words,
    get_user_level,
    get_user_plan,
    get_word_grade_map,
    is_placement_done,
    reset_progress,
    set_user_level,
    set_user_plan,
)
from src.utils.bot_helpers import (
    _build_levels_lock_text,
    _grade_tag,
    maybe_promote_level,
    send_next_word_card,
    send_review_list,
)
from src.utils.utils import (
    is_unlimited_user,
    reject_if_banned_callback,
    reject_if_banned_message,
    touch_user_from_message,
)

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
        ),
        reply_markup=get_main_menu_keyboard()
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
    if await reject_if_banned_callback(callback):
        return
    user_id = callback.from_user.id
    is_unlimited = is_unlimited_user(user_id)
    if not is_unlimited and not await is_placement_done(user_id):
        await callback.answer("Սկզբում անցեք placement test-ը։", show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Սխալ տվյալ", show_alert=True)
        return

    level = parts[2].upper()
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

    bars = 15
    filled = round(s['progress_pct'] / 100 * bars)
    progress_bar = "🟢" * filled + "⚪" * (bars - filled)

    await message.answer(
        f"📊 **Learning Dashboard**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏆 Progress: `{s['progress_pct']}%`\n"
        f"{progress_bar}\n\n"
        f"✅ Learned: `{s['learned']}/{s['total']}`\n"
        f"🎯 Accuracy: `{s['accuracy']}%`\n"
        f"🔥 Streak: `{s['streak']} days`\n"
        f"📅 Today: `{daily_count}/{daily_limit_label}`\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📘 Review queue: `{s['hard']}` words"
    )

@router.message(Command("coach"))
async def coach_handler(message: Message):
    from src.data.api_words import _get_http_session, get_tutor_explanation_gemini
    user_id = message.from_user.id
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return

    msg = await message.answer("🧠 Մարզիչը վերլուծում է քո առաջընթացը... ⏳")

    s = await get_stats(user_id, len(COMMON_WORDS))
    daily_count = await get_daily_count(user_id)
    level = await get_user_level(user_id)
    weak_words = await get_top_weak_words(user_id, limit=5)

    weak_list = ", ".join([w['word'] for w in weak_words]) if weak_words else "none"

    prompt = (
        f"You are a professional English Coach. Analyze this student's data and give a brief, "
        f"motivating and highly specific feedback in Armenian.\n"
        f"Data:\n"
        f"- Level: {level}\n"
        f"- Overall Accuracy: {s['accuracy']}%\n"
        f"- Words learned today: {daily_count}\n"
        f"- Streak: {s['streak']} days\n"
        f"- Weak words (most errors): {weak_list}\n"
        f"- Total learned: {s['learned']}/{s['total']}\n\n"
        f"Guidelines:\n"
        f"1. Be direct and encouraging.\n"
        f"2. If they have weak words, suggest a specific tip for remembering them.\n"
        f"3. Mention their streak to keep them motivated.\n"
        f"4. Keep it concise (under 150 words)."
    )

    session = await _get_http_session()
    analysis = await get_tutor_explanation_gemini(session, prompt)

    await msg.edit_text(
        f"👨‍🏫 **Coach Analysis**\n\n{analysis}",
        reply_markup=get_coach_keyboard(weak_words[0]['word'] if weak_words else None),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("coach:"))
async def coach_callback_handler(callback: CallbackQuery):
    from src.core.texts import format_searched_word
    from src.data.api_words import get_word_data
    from src.data.level_words import find_word_levels

    if await reject_if_banned_callback(callback):
        return
    user_id = callback.from_user.id

    data = callback.data or ""
    parts = data.split(":")
    if len(parts) < 2:
        await callback.answer("Սխալ տվյալ", show_alert=True)
        return

    action = parts[1]
    word = parts[2] if len(parts) > 2 else None

    if action == "refresh":
        await callback.answer("🔄 Թարմացվում է...")
        await coach_handler(callback.message)
    elif action == "review":
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
    elif action == "full_stats":
        await callback.answer("📊 Բացում եմ վիճակագրությունը...")
        await stats_handler(callback.message)
    else:
        await callback.answer(f"Անհայտ գործողություն: {action}", show_alert=True)


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
    if await reject_if_banned_message(message):
        return
    level = (message.text or "").strip().split("_")[-1].upper()
    await _send_words_by_level(message, level)

@router.message(Command("reset"))
async def reset_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    await reset_progress(message.from_user.id, preserve_history=True)
    await message.answer("♻️ Reset արվեց։ Ձեր learned/seen բառերը պահպանվել են։")

@router.message(Command("reset_all"))
async def reset_all_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    await reset_progress(message.from_user.id, preserve_history=False)
    await message.answer("⚠️ Ձեր ամբողջ history-ն ջնջվեց։")

@router.message(Command("plan"))
async def plan_command_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    await message.answer(
        "🎓 **Ընտրիր քո ուսումնական պլանը:**\n\n"
        "**🐢 Steady Learner:** Օրական 5 նոր բառ + Կրկնություն + Պատմություն։\n"
        "**🔥 Deep Focus:** Օրական 10 նոր բառ + Pomodoro + Գործնական նախադասություններ + AI Tutor։",
        reply_markup=get_plan_selection_keyboard()
    )

@router.message(Command("roadmap"))
async def roadmap_command_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    user_id = message.from_user.id

    plan = await get_user_plan(user_id)
    daily_count = await get_daily_count(user_id)
    stats = await get_stats(user_id, 3000) # common words count
    stories_today = await count_story_generations_today(user_id)

    steps = []
    due = stats.get("due_today", 0)
    steps.append({
        "label": f"Կրկնություն ({due} բառ)",
        "done": due == 0,
        "callback": "review:start"
    })

    target = 5 if plan == "steady" else 10
    steps.append({
        "label": f"Նոր բառեր ({daily_count}/{target})",
        "done": daily_count >= target,
        "callback": "word:next"
    })

    if plan == "steady":
        steps.append({
            "label": "Օրվա պատմությունը",
            "done": stories_today > 0,
            "callback": "story:genre:reallife"
        })
    else:
        steps.append({
            "label": "Pomodoro Session",
            "done": False,
            "callback": "pomodoro:start"
        })
        steps.append({
            "label": "AI Practice (նախադասություններ)",
            "done": False,
            "callback": "word:next"
        })

    await message.answer(
        f"🗺 **Քո օրվա պլանը ({'Ինտենսիվ' if plan=='deep' else 'Հանգիստ'}):**\n"
        "Հետևիր այս քայլերին լավագույն արդյունքի համար:",
        reply_markup=get_daily_roadmap_keyboard(steps)
    )

@router.callback_query(F.data.startswith("plan:"))
async def plan_callback_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.split(":")[1]

    if action == "set":
        plan = callback.data.split(":")[2]
        await set_user_plan(user_id, plan)
        await callback.answer(f"Պլանը փոխվեց՝ {plan.upper()} ✅")
        await roadmap_command_handler(callback.message)
    elif action == "roadmap":
        await roadmap_command_handler(callback.message)
        await callback.answer()

@router.message(Command("help"))
@router.message(F.text.lower().contains("help"))
async def help_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    await message.answer(HELP_TEXT, parse_mode="HTML")

@router.message(F.text.in_({"🗺 Roadmap", "Roadmap", "/roadmap"}))
async def roadmap_button_handler(message: Message):
    await roadmap_command_handler(message)

@router.message(F.text.in_({"👨‍🏫 Coach", "Coach", "/coach"}))
async def coach_button_handler(message: Message):
    await coach_handler(message)

@router.message(F.text.in_({"📊 Stats", "Stats", "/stats"}))
async def stats_button_handler(message: Message):
    await stats_handler(message)

@router.message(F.text.in_({"🆕 New Word", "New Word", "/word"}))
async def new_word_button_handler(message: Message):
    from src.bot.handlers.study import send_word_handler
    await send_word_handler(message)

@router.message(F.text.in_({"⏱ Pomodoro", "Pomodoro", "/pomodoro"}))
async def pomodoro_button_handler(message: Message):
    from src.bot.handlers.study import pomodoro_command_handler
    await pomodoro_command_handler(message)
