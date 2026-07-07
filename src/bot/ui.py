from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from src.core.i18n import t


def get_language_selector() -> InlineKeyboardMarkup:
    """Keyboard for choosing interface language."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇦🇲 Հայերեն", callback_data="set_lang:hy"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang:en"),
            ]
        ]
    )


def get_start_new_word_keyboard(lang: str = "hy") -> InlineKeyboardMarkup:
    """Inline CTA keyboard offering instant action to start new words."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_new_word", lang), callback_data="word:next")]
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗺 Roadmap"), KeyboardButton(text="👨‍🏫 Coach")],
            [KeyboardButton(text="🆕 New Word"), KeyboardButton(text="⏱ Pomodoro")],
            [KeyboardButton(text="📊 Stats"), KeyboardButton(text="❓ Help")],
        ],
        resize_keyboard=True,
        persistent=True
    )


def get_plan_selection_keyboard(lang: str = "hy", current_goal: int = 5) -> InlineKeyboardMarkup:
    labels = {
        "hy": {
            "lite":   f"🌱 Lite — 3 բառ/օր",
            "steady": f"🐢 Steady — 5 բառ/օր",
            "deep":   f"🔥 Deep — 15 բառ/օր",
            "custom": f"⚙️ Custom — {current_goal} բառ/օր",
        },
        "ru": {
            "lite":   f"🌱 Lite — 3 слова/день",
            "steady": f"🐢 Steady — 5 слов/день",
            "deep":   f"🔥 Deep — 15 слов/день",
            "custom": f"⚙️ Custom — {current_goal} слов/день",
        },
        "en": {
            "lite":   f"🌱 Lite — 3 words/day",
            "steady": f"🐢 Steady — 5 words/day",
            "deep":   f"🔥 Deep — 15 words/day",
            "custom": f"⚙️ Custom — {current_goal} words/day",
        },
    }.get(lang, {
        "lite":   f"🌱 Lite — 3 words/day",
        "steady": f"🐢 Steady — 5 words/day",
        "deep":   f"🔥 Deep — 15 words/day",
        "custom": f"⚙️ Custom — {current_goal} words/day",
    })
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=labels["lite"],   callback_data="plan:set:lite")],
            [InlineKeyboardButton(text=labels["steady"], callback_data="plan:set:steady")],
            [InlineKeyboardButton(text=labels["deep"],   callback_data="plan:set:deep")],
            [InlineKeyboardButton(text=labels["custom"], callback_data="plan:set:custom")],
        ]
    )


def get_daily_roadmap_keyboard(steps: list[dict], lang: str = "hy") -> InlineKeyboardMarkup:
    rows = []
    for step in steps:
        status = "✅" if step["done"] else "⏳"
        rows.append([InlineKeyboardButton(text=f"{status} {step['label']}", callback_data=step["callback"])])
    refresh_text = {"hy": "🔄 Թարմացնել Roadmap-ը", "ru": "🔄 Обновить Roadmap", "en": "🔄 Refresh Roadmap"}.get(lang, "🔄 Refresh Roadmap")
    rows.append([InlineKeyboardButton(text=refresh_text, callback_data="plan:roadmap")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_word_keyboard(word: str, has_back: bool = False, lang: str = "hy") -> InlineKeyboardMarkup:
    nav_row = []
    if has_back:
        nav_row.append(InlineKeyboardButton(text=t("btn_back_word", lang), callback_data="word:back"))
    nav_row.append(InlineKeyboardButton(text=t("btn_practice", lang), callback_data=f"word:practice:{word}"))
    nav_row.append(InlineKeyboardButton(text=t("btn_next_word", lang), callback_data="word:next"))

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_listen_us", lang), callback_data=f"audio:us:{word}"),
                InlineKeyboardButton(text=t("btn_listen_uk", lang), callback_data=f"audio:uk:{word}"),
                InlineKeyboardButton(text=t("btn_test_voice", lang), callback_data=f"word:pronounce:{word}"),
            ],
            nav_row,
            [
                InlineKeyboardButton(text=t("btn_again", lang), callback_data=f"word:again:{word}"),
                InlineKeyboardButton(text=t("btn_hard", lang), callback_data=f"word:hard:{word}"),
                InlineKeyboardButton(text=t("btn_good", lang), callback_data=f"word:good:{word}"),
                InlineKeyboardButton(text=t("btn_easy", lang), callback_data=f"word:easy:{word}"),
            ],
        ]
    )


def get_pomodoro_keyboard(is_active: bool = False, lang: str = "hy") -> InlineKeyboardMarkup:
    if not is_active:
        start_txt = {"hy": "🚀 Սկսել Focus Session (25ր)", "ru": "🚀 Начать фокус-сессию (25м)", "en": "🚀 Start Focus Session (25m)"}.get(lang, "🚀 Start Focus Session (25m)")
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=start_txt, callback_data="pomodoro:start")]
            ]
        )
    ref_txt = {"hy": "🔄 Թարմացնել ժամանակը", "ru": "🔄 Обновить время", "en": "🔄 Refresh timer"}.get(lang, "🔄 Refresh timer")
    stop_txt = {"hy": "⏹️ Կանգնեցնել", "ru": "⏹️ Остановить", "en": "⏹️ Stop"}.get(lang, "⏹️ Stop")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=ref_txt, callback_data="pomodoro:refresh")],
            [InlineKeyboardButton(text=stop_txt, callback_data="pomodoro:stop")]
        ]
    )


def get_test_options_keyboard(options: list[str], session_id: int) -> InlineKeyboardMarkup:
    rows = []
    for opt in options:
        rows.append([InlineKeyboardButton(text=opt, callback_data=f"test:ans:{session_id}:{opt}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_review_start_keyboard(lang: str = "hy") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_review_start", lang), callback_data="review:start")]
        ]
    )


def get_level_test_start_keyboard(target_level: str, lang: str = "hy") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_start_level_test", lang), callback_data=f"leveltest:start:{target_level}")]
        ]
    )

def get_review_flashcard_keyboard(word: str, show_translation: bool, show_example: bool, lang: str = "hy") -> InlineKeyboardMarkup:
    rows = []

    if show_translation:
        rows.append([
            InlineKeyboardButton(text=t("btn_listen_us", lang), callback_data=f"audio:us:{word}"),
            InlineKeyboardButton(text=t("btn_listen_uk", lang), callback_data=f"audio:uk:{word}"),
            InlineKeyboardButton(text=t("btn_test_voice", lang), callback_data=f"word:pronounce:{word}"),
        ])
        rows.append([
            InlineKeyboardButton(text=t("btn_again", lang), callback_data=f"review:again:{word}"),
            InlineKeyboardButton(text=t("btn_hard", lang), callback_data=f"review:hard:{word}"),
        ])
        rows.append([
            InlineKeyboardButton(text=t("btn_good", lang), callback_data=f"review:good:{word}"),
            InlineKeyboardButton(text=t("btn_easy", lang), callback_data=f"review:easy:{word}"),
        ])
    else:
        rows.append([
            InlineKeyboardButton(text=t("btn_listen_us", lang), callback_data=f"audio:us:{word}"),
            InlineKeyboardButton(text=t("btn_listen_uk", lang), callback_data=f"audio:uk:{word}"),
            InlineKeyboardButton(text=t("btn_test_voice", lang), callback_data=f"word:pronounce:{word}"),
        ])
        rows.append([
            InlineKeyboardButton(text=t("btn_show_translate", lang), callback_data=f"review:show_tr:{word}"),
        ])

    if not show_example:
        rows.append([InlineKeyboardButton(text=t("btn_show_example", lang), callback_data=f"review:show_ex:{word}")])

    rows.append([InlineKeyboardButton(text=t("btn_skip", lang), callback_data=f"review:next:{word}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_placement_start_keyboard(lang: str = "hy") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_start_placement", lang), callback_data="placement:start")]
        ]
    )


def get_placement_options_keyboard(options: list[str], session_id: int) -> InlineKeyboardMarkup:
    rows = []
    for i, opt in enumerate(options):
        rows.append([InlineKeyboardButton(text=opt, callback_data=f"placement:ans:{session_id}:{i}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_level_keyboard(current_level: str = "A1", placement_done: bool = False, unlock_all: bool = False, lang: str = "hy") -> InlineKeyboardMarkup:
    labels = {
        "hy": {"A1": "Սկսնակ", "A2": "Տարրական", "B1": "Միջին", "B2": "Բարձր միջին"},
        "ru": {"A1": "Начинающий", "A2": "Элементарный", "B1": "Средний", "B2": "Выше среднего"},
        "en": {"A1": "Beginner", "A2": "Elementary", "B1": "Intermediate", "B2": "Upper-Int"}
    }.get(lang, {"A1": "Beginner", "A2": "Elementary", "B1": "Intermediate", "B2": "Upper-Int"})

    levels = [
        ("A1", labels["A1"]),
        ("A2", labels["A2"]),
        ("B1", labels["B1"]),
        ("B2", labels["B2"]),
    ]
    rows = []
    for i in range(0, len(levels), 2):
        row = []
        for lvl_code, label in levels[i:i+2]:
            is_current = (lvl_code == current_level)
            is_locked = not unlock_all and placement_done and lvl_code != current_level

            prefix = "✅ " if is_current else ("🔒 " if is_locked else "")
            btn_text = f"{prefix}{lvl_code} ({label})"
            row.append(InlineKeyboardButton(text=btn_text, callback_data=f"level:set:{lvl_code}"))
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_coach_keyboard(focus_word: str | None = None, lang: str = "hy") -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=t("btn_coach_refresh", lang), callback_data="coach:refresh"),
            InlineKeyboardButton(text=t("btn_coach_review", lang), callback_data="coach:review"),
        ]
    ]
    if focus_word:
        rows.append([InlineKeyboardButton(text=f"🎯 Focus: {focus_word}", callback_data=f"coach:focus:{focus_word}")])

    rows.append([InlineKeyboardButton(text=t("btn_coach_stats", lang), callback_data="coach:full_stats")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_search_keyboard(word: str, lang: str = "hy") -> InlineKeyboardMarkup:
    explain_txt = {"hy": "🧠 AI Բացատրություն (Tutor)", "ru": "🧠 AI Объяснение (Tutor)", "en": "🧠 Explain with AI (Tutor)"}.get(lang, "🧠 Explain with AI (Tutor)")
    audio_txt = {"hy": "🔊 Լսել արտասանությունը", "ru": "🔊 Прослушать произношение", "en": "🔊 Listen to pronunciation"}.get(lang, "🔊 Listen to pronunciation")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=explain_txt, callback_data=f"explain:{word}")],
            [InlineKeyboardButton(text=audio_txt, callback_data=f"audio:{word}")],
        ]
    )


def get_story_genre_keyboard(lang: str = "hy") -> InlineKeyboardMarkup:
    genres = {
        "hy": {"cyber": "🌆 Կիբեռպանկ", "det": "🔍 Դետեկտիվ", "fan": "🧙 Ֆենտեզի", "com": "😂 Կատակերգություն", "real": "🏠 Իրական կյանք"},
        "ru": {"cyber": "🌆 Киберпанк", "det": "🔍 Детектив", "fan": "🧙 Фэнтези", "com": "😂 Комедия", "real": "🏠 Реальная жизнь"},
        "en": {"cyber": "🌆 Cyberpunk", "det": "🔍 Detective", "fan": "🧙 Fantasy", "com": "😂 Comedy", "real": "🏠 Real-life"}
    }.get(lang, {"cyber": "🌆 Cyberpunk", "det": "🔍 Detective", "fan": "🧙 Fantasy", "com": "😂 Comedy", "real": "🏠 Real-life"})

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=genres["cyber"], callback_data="story:genre:cyberpunk"),
                InlineKeyboardButton(text=genres["det"], callback_data="story:genre:detective"),
            ],
            [
                InlineKeyboardButton(text=genres["fan"], callback_data="story:genre:fantasy"),
                InlineKeyboardButton(text=genres["com"], callback_data="story:genre:comedy"),
            ],
            [InlineKeyboardButton(text=genres["real"], callback_data="story:genre:reallife")],
        ]
    )


def get_palace_theme_keyboard(lang: str = "hy") -> InlineKeyboardMarkup:
    themes = {
        "hy": {"ancient": "🏛 Հնագույն սենյակ", "cyber": "💻 Կիբեռ լոֆթ", "cozy": "🏠 Հարմարավետ տուն"},
        "ru": {"ancient": "🏛 Древняя комната", "cyber": "💻 Кибер-лофт", "cozy": "🏠 Уютный дом"},
        "en": {"ancient": "🏛 Ancient Room", "cyber": "💻 Cyber Loft", "cozy": "🏠 Cozy Home"}
    }.get(lang, {"ancient": "🏛 Ancient Room", "cyber": "💻 Cyber Loft", "cozy": "🏠 Cozy Home"})

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=themes["ancient"], callback_data="palace:theme:ancient"),
                InlineKeyboardButton(text=themes["cyber"], callback_data="palace:theme:cyber"),
            ],
            [
                InlineKeyboardButton(text=themes["cozy"], callback_data="palace:theme:cozy"),
            ]
        ]
    )


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Overview", callback_data="adminui:overview"),
                InlineKeyboardButton(text="👥 Users", callback_data="adminui:users"),
            ],
            [
                InlineKeyboardButton(text="🏆 Top", callback_data="adminui:top"),
                InlineKeyboardButton(text="📣 Broadcast", callback_data="adminui:broadcast_help"),
            ],
            [
                InlineKeyboardButton(text="♻️ Reset Account", callback_data="adminui:reset_self"),
                InlineKeyboardButton(text="🔄 Refresh", callback_data="adminui:refresh"),
            ],
        ]
    )


def get_admin_users_keyboard(users: list[dict], limit: int = 30) -> InlineKeyboardMarkup:
    rows = []
    for u in users:
        username = f"@{u['username']}" if u.get("username") else str(u['user_id'])
        ban_status = "🚫" if int(u.get('banned') or 0) == 1 else "✅"
        rows.append(
            [
                InlineKeyboardButton(text=f"{username} ({u.get('user_level','A1')})", callback_data=f"adminui:user_profile:{u['user_id']}"),
                InlineKeyboardButton(text=ban_status, callback_data=f"adminmod:{'unban' if ban_status=='🚫' else 'ban'}:{u['user_id']}:{limit}"),
            ]
        )
    rows.append([InlineKeyboardButton(text="🔙 Back", callback_data="adminui:refresh")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_pronunciation_feedback_keyboard(word: str, score: int) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="🔄 Try Again", callback_data=f"word:pronounce:{word}"),
    ]
    # Add YouGlish button for visual aid
    buttons.append(InlineKeyboardButton(text="📺 See Video", url=f"https://youglish.com/pronounce/{word}/english"))

    # Show "Next Word" only if score is 85 or higher
    if score >= 85:
        buttons.append(InlineKeyboardButton(text="⏭️ Next Word", callback_data="word:next"))

    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def get_global_roadmap_keyboard(lang: str = "hy") -> InlineKeyboardMarkup:
    """Keyboard under the Global Progress text."""
    labels = {
        "hy": {"level": "🔄 Փոխել Մակարդակը", "weak": "🧠 Դժվար Բառեր", "stats": "📊 Վիճակագրություն"},
        "ru": {"level": "🔄 Сменить уровень", "weak": "🧠 Сложные слова", "stats": "📊 Статистика"},
        "en": {"level": "🔄 Change Level", "weak": "🧠 Hard Words", "stats": "📊 Statistics"},
    }
    texts = labels.get(lang, labels["en"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts["level"], callback_data="level:choose")],
            [InlineKeyboardButton(text=texts["weak"], callback_data="review:weak")],
            [InlineKeyboardButton(text=texts["stats"], callback_data="stats:show")],
        ]
    )

def get_main_menu_keyboard(lang: str = "hy") -> ReplyKeyboardMarkup:
    """Main persistent menu used after /start. Language-aware."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_daily_plan", lang)), KeyboardButton(text=t("btn_coach", lang))],
            [KeyboardButton(text=t("btn_new_word", lang)), KeyboardButton(text=t("btn_roadmap", lang))],
            [KeyboardButton(text=t("btn_stats", lang)), KeyboardButton(text=t("btn_help", lang))],
            [KeyboardButton(text=t("btn_language", lang))],
        ],
        resize_keyboard=True,
        persistent=True,
    )
