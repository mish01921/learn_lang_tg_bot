from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from src.bot.ui import (
    get_coach_keyboard,
    get_daily_roadmap_keyboard,
    get_global_roadmap_keyboard,
    get_language_selector,
    get_level_keyboard,
    get_main_menu_keyboard,
    get_placement_start_keyboard,
    get_plan_selection_keyboard,
    get_search_keyboard,
)
from src.core.config import DAILY_LIMIT, WORD_LEVEL_CHOICES
from src.core.i18n import get_lang, t
from src.data.api_words import COMMON_WORDS
from src.data.placement_questions import CEFR_PLACEMENT_QUESTIONS
from src.data.level_words import chunk_text as _chunk_text
from src.data.level_words import load_levelled_words as _load_levelled_words
from src.database.models import (
    count_story_generations_today,
    get_daily_count,
    get_daily_limit,
    get_daily_pomodoro_count,
    get_daily_practice_count,
    get_stats,
    get_top_weak_words,
    get_user_level,
    get_user_plan,
    get_word_grade_map,
    is_placement_done,
    reset_progress,
    set_daily_goal,
    set_user_language_db,
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

from src.core.app_state import clear_user_waiting_states, plan_custom_waiting_users, user_language


def _build_start_text_i18n(name: str, total_words: int, daily_limit: int, is_admin: bool, lang: str) -> str:
    """Build localised start screen text."""
    daily_key = "daily_line_admin" if is_admin else "daily_line_normal"
    daily_line = t(daily_key, lang, daily_limit=daily_limit)
    greeting = t("start_greeting", lang, name=name)
    body = t("start_body", lang, total_words=total_words, daily_line=daily_line)
    return f"{greeting}\n\n{body}"


@router.message(CommandStart())
async def start_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return

    # Always select language first on /start
    await message.answer(
        "🌍 Please select your interface language\n"
        "🌍 Пожалуйста, выберите язык интерфейса\n"
        "🌍 Խնդրում ենք ընտրել ձեր ինտերֆեյսի լեզուն",
        reply_markup=get_language_selector()
    )


@router.callback_query(F.data.startswith("set_lang:"))
async def set_language_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    _, lang = callback.data.split(":")
    if lang not in {"hy", "ru", "en"}:
        await callback.answer("Unsupported language", show_alert=True)
        return
    user_language[user_id] = lang
    await set_user_language_db(user_id, lang)

    # Clean waiting states for clean start
    clear_user_waiting_states(user_id)

    lang_labels = {"hy": "🇦🇲 Հայերեն", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}
    await callback.answer(f"✅ {lang_labels[lang]}", show_alert=False)

    try:
        await callback.message.delete()
    except Exception:
        pass

    placement_done = await is_placement_done(user_id)
    name = callback.from_user.first_name or "Hello"
    is_unlimited = is_unlimited_user(user_id)
    await callback.message.answer(
        _build_start_text_i18n(name, len(COMMON_WORDS), DAILY_LIMIT, is_unlimited, lang),
        reply_markup=get_main_menu_keyboard(lang),
    )
    if not placement_done and not is_unlimited:
        await callback.message.answer(
            t("placement_prompt", lang),
            reply_markup=get_placement_start_keyboard(lang),
        )
    else:
        current_level = await get_user_level(user_id)
        await callback.message.answer(
            _build_levels_lock_text(current_level, True, unlock_all=is_unlimited, lang=lang),
            reply_markup=get_level_keyboard(current_level, True, unlock_all=is_unlimited, lang=lang),
        )


@router.message(Command("levels"))
async def levels_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    user_id = message.from_user.id
    lang = get_lang(user_id)
    is_unlimited = is_unlimited_user(user_id)
    placement_done = is_unlimited or await is_placement_done(user_id)
    current_level = await get_user_level(user_id)
    await message.answer(
        _build_levels_lock_text(current_level, placement_done, unlock_all=is_unlimited, lang=lang),
        reply_markup=get_level_keyboard(current_level, placement_done, unlock_all=is_unlimited, lang=lang),
    )

@router.callback_query(F.data.startswith("level:"))
async def level_select_handler(callback: CallbackQuery):
    if await reject_if_banned_callback(callback):
        return
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    is_unlimited = is_unlimited_user(user_id)
    if not is_unlimited and not await is_placement_done(user_id):
        await callback.answer(t("placement_required", lang), show_alert=True)
        return

    parts = callback.data.split(":")
    if callback.data == "level:choose":
        current_level = await get_user_level(user_id)
        placement_done = is_unlimited or await is_placement_done(user_id)
        await callback.message.answer(
            _build_levels_lock_text(current_level, placement_done, unlock_all=is_unlimited, lang=lang),
            reply_markup=get_level_keyboard(current_level, placement_done, unlock_all=is_unlimited, lang=lang),
        )
        await callback.answer()
        return

    if len(parts) < 3:
        await callback.answer("Error", show_alert=True)
        return

    level = parts[2].upper()
    if level not in WORD_LEVEL_CHOICES:
        await callback.answer("Error", show_alert=True)
        return

    current_level = await get_user_level(user_id)
    if not is_unlimited and level != current_level:
        from src.database.models import can_take_level_test
        if not await can_take_level_test(user_id, level):
            await callback.answer(t("level_test_failed_today", lang, level=level), show_alert=True)
            return

        pool = [q for q in CEFR_PLACEMENT_QUESTIONS if q["level"] == level]
        total = min(5, len(pool))
        if total > 0:
            passing = max(1, int(total * 0.8))
            from src.bot.ui import get_level_test_start_keyboard
            await callback.message.answer(
                t("level_test_intro", lang, level=level, total=total, passing=passing),
                reply_markup=get_level_test_start_keyboard(level, lang),
                parse_mode="Markdown"
            )
            await callback.answer()
            return
        # If no questions available for this level, just change it directly.

    await set_user_level(user_id, level)
    await callback.answer(t("level_changed", lang, level=level))
    await maybe_promote_level(user_id, callback.message)

@router.message(Command("stats"))
async def stats_handler(message: Message, user_id: int | None = None):
    if user_id is None:
        await touch_user_from_message(message)
        if await reject_if_banned_message(message):
            return
        user_id = message.from_user.id

    lang = get_lang(user_id)
    s = await get_stats(user_id, len(COMMON_WORDS))
    daily_count = await get_daily_count(user_id)
    daily_limit_label = "∞" if is_unlimited_user(user_id) else str(DAILY_LIMIT)

    bars = 15
    filled = round(s['progress_pct'] / 100 * bars)
    progress_bar = "🟢" * filled + "⚪" * (bars - filled)

    await message.answer(
        f"{t('stats_title', lang)}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{t('stats_progress', lang)}: `{s['progress_pct']}%`\n"
        f"{progress_bar}\n\n"
        f"{t('stats_learned', lang)}: `{s['learned']}/{s['total']}`\n"
        f"{t('stats_accuracy', lang)}: `{s['accuracy']}%`\n"
        f"{t('stats_streak', lang)}: `{s['streak']}`\n"
        f"{t('stats_today', lang)}: `{daily_count}/{daily_limit_label}`\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{t('stats_review_queue', lang)}: `{s['hard']}`"
    )

@router.message(Command("coach"))
async def coach_handler(message: Message, user_id: int | None = None):
    from src.data.api_words import get_coach_analysis_gemini
    if user_id is None:
        await touch_user_from_message(message)
        if await reject_if_banned_message(message):
            return
        user_id = message.from_user.id

    lang = get_lang(user_id)
    lang_names = {"hy": "Armenian", "ru": "Russian", "en": "English"}
    target_lang = lang_names.get(lang, "Armenian")

    msg = await message.answer(t("coach_thinking", lang))

    s = await get_stats(user_id, len(COMMON_WORDS))
    daily_count = await get_daily_count(user_id)
    level = await get_user_level(user_id)
    weak_words = await get_top_weak_words(user_id, limit=5)

    weak_list = ", ".join([w['word'] for w in weak_words]) if weak_words else "none"

    prompt = (
        f"You are a professional English Coach. Analyze this student's data and give a brief, "
        f"motivating and highly specific feedback in {target_lang}.\n"
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

    analysis = await get_coach_analysis_gemini(prompt)
    header = t("coach_header", lang)

    try:
        await msg.edit_text(
            f"{header}\n\n{analysis}",
            reply_markup=get_coach_keyboard(weak_words[0]['word'] if weak_words else None, lang=lang),
            parse_mode="Markdown"
        )
    except Exception:
        await msg.edit_text(
            f"{header}\n\n{analysis}",
            reply_markup=get_coach_keyboard(weak_words[0]['word'] if weak_words else None, lang=lang)
        )

@router.callback_query(F.data.startswith("coach:"))
async def coach_callback_handler(callback: CallbackQuery):
    from src.core.texts import format_searched_word
    from src.data.api_words import get_word_data
    from src.data.level_words import find_word_levels

    if await reject_if_banned_callback(callback):
        return
    user_id = callback.from_user.id
    lang = get_lang(user_id)

    data = callback.data or ""
    parts = data.split(":")
    if len(parts) < 2:
        await callback.answer("Error", show_alert=True)
        return

    action = parts[1]
    word = parts[2] if len(parts) > 2 else None

    if action == "refresh":
        await callback.answer("🔄 ...")
        await coach_handler(callback.message, user_id=user_id)
    elif action == "review":
        sent = await send_review_list(callback.message, user_id)
        await callback.answer()
    elif action == "new":
        level = await get_user_level(user_id)
        sent = await send_next_word_card(callback.message, user_id, level)
        await callback.answer()
    elif action == "focus" and word:
        word_data = await get_word_data(word)
        levels = await find_word_levels(word)
        await callback.message.answer(format_searched_word(word_data, levels), reply_markup=get_search_keyboard(word, lang=lang))
        await callback.answer()
    elif action == "full_stats":
        await callback.answer()
        await stats_handler(callback.message, user_id=user_id)
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
    user_id = message.from_user.id
    lang = get_lang(user_id)
    current_goal = await get_daily_limit(user_id)
    await message.answer(
        t("plan_choose", lang),
        reply_markup=get_plan_selection_keyboard(lang=lang, current_goal=current_goal),
        parse_mode="Markdown"
    )

@router.message(Command("daily"))
async def daily_plan_command_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    user_id = message.chat.id
    lang = get_lang(user_id)

    plan = await get_user_plan(user_id)
    daily_count = await get_daily_count(user_id)
    stats = await get_stats(user_id, 3000) # common words count
    stories_today = await count_story_generations_today(user_id)
    pomodoros_today = await get_daily_pomodoro_count(user_id)
    practice_today = await get_daily_practice_count(user_id)

    steps = []
    due = stats.get("due_today", 0)
    steps.append({
        "label": t("step_review", lang, count=due),
        "done": due == 0,
        "callback": "review:start"
    })

    target = await get_daily_limit(user_id)
    steps.append({
        "label": t("step_new_words", lang, count=daily_count, target=target),
        "done": daily_count >= target,
        "callback": "word:next"
    })

    if plan == "lite":
        # Lite: just new words + review, no extras
        pass
    elif plan == "deep":
        steps.append({
            "label": t("step_pomodoro", lang),
            "done": pomodoros_today >= 1,
            "callback": "pomodoro:start"
        })
        steps.append({
            "label": t("step_practice", lang),
            "done": practice_today >= 1,
            "callback": "word:next"
        })
    else:
        # steady or custom → story step
        steps.append({
            "label": t("step_story", lang),
            "done": stories_today > 0,
            "callback": "story:genre:reallife"
        })

    title_keys = {
        "lite":   "roadmap_title_lite",
        "deep":   "roadmap_title_deep",
        "custom": "roadmap_title_custom",
    }
    title_key = title_keys.get(plan, "roadmap_title_steady")
    await message.answer(
        t(title_key, lang),
        reply_markup=get_daily_roadmap_keyboard(steps)
    )

@router.callback_query(F.data.startswith("plan:"))
async def plan_callback_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    parts = callback.data.split(":")
    action = parts[1]

    PLAN_LABELS = {
        "hy": {"lite": "Lite", "steady": "Steady", "deep": "Deep", "custom": "Custom"},
        "ru": {"lite": "Lite", "steady": "Steady", "deep": "Deep", "custom": "Custom"},
        "en": {"lite": "Lite", "steady": "Steady", "deep": "Deep", "custom": "Custom"},
    }
    PLAN_GOALS = {"lite": 3, "steady": 5, "deep": 15}

    if action == "set":
        plan = parts[2] if len(parts) > 2 else "steady"
        if plan == "custom":
            # Ask user to type a number
            plan_custom_waiting_users[user_id] = True
            await callback.message.answer(t("plan_custom_ask", lang))
            await callback.answer()
            return
        await set_user_plan(user_id, plan)
        goal = PLAN_GOALS.get(plan, 5)
        label = PLAN_LABELS.get(lang, PLAN_LABELS["en"]).get(plan, plan.title())
        await callback.answer(
            t("plan_set_success", lang, plan_label=label, goal=goal),
            show_alert=True
        )
        await daily_plan_command_handler(callback.message)
    elif action == "roadmap":
        await daily_plan_command_handler(callback.message)
        await callback.answer()


@router.message(F.text & F.from_user.id.func(lambda uid: uid in plan_custom_waiting_users))
async def plan_custom_number_handler(message: Message):
    """Handles the numeric reply when user chose Custom daily goal."""
    user_id = message.from_user.id
    plan_custom_waiting_users.pop(user_id, None)
    lang = get_lang(user_id)
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(t("plan_custom_ask", lang))
        plan_custom_waiting_users[user_id] = True
        return
    goal = max(1, min(30, int(raw)))
    await set_daily_goal(user_id, goal)
    await message.answer(
        t("plan_set_success", lang, plan_label="Custom", goal=goal),
        parse_mode="Markdown"
    )
    await daily_plan_command_handler(message)

@router.message(Command("help"))
@router.message(F.text.in_({
    "❓ Օգնություն", "Օգնություն", "/help",
    "❓ Помощь", "Помощь",
    "❓ Help", "Help"
}))
@router.message(F.text.lower().contains("help"))
@router.message(F.text.lower().contains("օգնություն"))
@router.message(F.text.lower().contains("помощь"))
async def help_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    user_id = message.from_user.id
    lang = get_lang(user_id)
    await message.answer(t("help_text", lang), parse_mode="HTML")

@router.message(Command("language", "lang"))
@router.message(F.text.in_({
    "🌐 Փոխել լեզուն", "Փոխել լեզուն",
    "🌐 Сменить язык", "Сменить язык",
    "🌐 Change Language", "Change Language",
}))
async def language_command_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    user_id = message.from_user.id
    lang = get_lang(user_id)
    await message.answer(
        t("choose_language", lang),
        reply_markup=get_language_selector()
    )

# Daily Plan
@router.message(F.text.in_({
    "🎯 Daily Plan", "Daily Plan", "/daily",
    "🎯 Օրվա Պլան", "Օրվա Պլան",
    "🎯 План на день", "План на день",
}))
async def daily_plan_button_handler(message: Message):
    await daily_plan_command_handler(message)

# Global Progress Roadmap: hy=🗺 Ճանապարհ  ru=🗺 Прогресс  en=🗺 Roadmap
@router.message(F.text.in_({
    "🗺 Roadmap", "Roadmap", "/roadmap",
    "🗺 Ճանապարհ", "Ճանապարհ",
    "🗺 Прогресс", "Прогресс",
}))
async def global_progress_button_handler(message: Message):
    await touch_user_from_message(message)
    if await reject_if_banned_message(message):
        return
    user_id = message.from_user.id
    lang = get_lang(user_id)
    
    current_level = await get_user_level(user_id)
    s = await get_stats(user_id, len(COMMON_WORDS))
    
    levels = ["A1", "A2", "B1", "B2"]
    try:
        idx = levels.index(current_level)
        next_level = levels[idx + 1] if idx + 1 < len(levels) else "C1"
    except:
        next_level = "B1"

    # Mock total words for current level based on common knowledge
    # For A1 let's say 500, A2 1000, B1 2000, B2 3000.
    # But let's use the DB stats we have from get_stats or a static map.
    total_words_map = {"A1": 500, "A2": 800, "B1": 1500, "B2": 3000}
    level_total = total_words_map.get(current_level, len(COMMON_WORDS))
    
    learned = s.get("learned", 0)
    percent = min(100, int((learned / level_total) * 100)) if level_total > 0 else 0
    remaining = max(0, level_total - learned)
    
    bars = 14
    filled = round(percent / 100 * bars)
    progress_bar = "█" * filled + "░" * (bars - filled)
    
    await message.answer(
        t("global_progress_text", lang, 
          level=current_level, next_level=next_level, 
          learned=learned, total_words=level_total, 
          progress_bar=progress_bar, percent=percent,
          remaining=remaining, streak=s.get("streak", 0), 
          hard=s.get("hard", 0), accuracy=s.get("accuracy", 0)),
        reply_markup=get_global_roadmap_keyboard(lang),
        parse_mode="Markdown"
    )

# Coach: hy=👨‍🏫 Մարզիչ  ru=👨‍🏫 Тренер  en=👨‍🏫 Coach
@router.message(F.text.in_({
    "👨‍🏫 Coach", "Coach", "/coach",
    "👨‍🏫 Մարզիչ", "Մարզիչ",
    "👨‍🏫 Тренер", "Тренер",
}))
async def coach_button_handler(message: Message):
    await coach_handler(message)

# Stats: hy=📊 Վիճակագրություն  ru=📊 Статистика  en=📊 Stats
@router.message(F.text.in_({
    "📊 Stats", "Stats", "/stats",
    "📊 Վիճակագրություն", "Վիճակագրություն",
    "📊 Статистика", "Статистика",
}))
async def stats_button_handler(message: Message):
    await stats_handler(message)

# New Word: hy=🆕 Նոր բառ  ru=🆕 Новое слово  en=🆕 New Word
@router.message(F.text.in_({
    "🆕 New Word", "New Word", "/word",
    "🆕 Նոր բառ", "Նոր բառ",
    "🆕 Новое слово", "Новое слово",
}))
async def new_word_button_handler(message: Message):
    from src.bot.handlers.study import send_word_handler
    await send_word_handler(message)

# Pomodoro: hy=⏱ Պոմոդորո  ru=⏱ Помодоро  en=⏱ Pomodoro
@router.message(F.text.in_({
    "⏱ Pomodoro", "Pomodoro", "/pomodoro",
    "⏱ Պոմոդորո", "Պոմոդորո",
    "⏱ Помодоро", "Помодоро",
}))
async def pomodoro_button_handler(message: Message):
    from src.bot.handlers.study import pomodoro_command_handler
    await pomodoro_command_handler(message)

