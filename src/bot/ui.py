
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗺 Roadmap"), KeyboardButton(text="👨‍🏫 Coach")],
            [KeyboardButton(text="🆕 New Word"), KeyboardButton(text="⏱ Pomodoro")],
            [KeyboardButton(text="📊 Stats"), KeyboardButton(text="❓ Help")],
        ],
        resize_keyboard=True,
        persistent=True
    )


def get_plan_selection_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🐢 Steady Learner (Հավասարակշռված)", callback_data="plan:set:steady")],
            [InlineKeyboardButton(text="🔥 Deep Focus (Ինտենսիվ)", callback_data="plan:set:deep")],
        ]
    )


def get_daily_roadmap_keyboard(steps: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for step in steps:
        status = "✅" if step["done"] else "⏳"
        rows.append([InlineKeyboardButton(text=f"{status} {step['label']}", callback_data=step["callback"])])
    rows.append([InlineKeyboardButton(text="🔄 Refresh Roadmap", callback_data="plan:roadmap")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_word_keyboard(word: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇸 Listen (US)", callback_data=f"audio:us:{word}"),
                InlineKeyboardButton(text="🇬🇧 Listen (UK)", callback_data=f"audio:uk:{word}"),
            ],
            [
                InlineKeyboardButton(text="🎙️ Test my Voice", callback_data=f"word:pronounce:{word}"),
            ],
            [
                InlineKeyboardButton(text="❌ Again", callback_data=f"word:again:{word}"),
                InlineKeyboardButton(text="🟠 Hard", callback_data=f"word:hard:{word}"),
            ],
            [
                InlineKeyboardButton(text="✅ Good", callback_data=f"word:good:{word}"),
                InlineKeyboardButton(text="🚀 Easy", callback_data=f"word:easy:{word}"),
            ],
            [
                InlineKeyboardButton(text="🧠 Կիրառել (Practice)", callback_data=f"word:practice:{word}"),
                InlineKeyboardButton(text="⏭️ Հաջորդը", callback_data="word:next"),
            ],
        ]
    )


def get_pomodoro_keyboard(is_active: bool = False) -> InlineKeyboardMarkup:
    if not is_active:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Սկսել Focus Session (25ր)", callback_data="pomodoro:start")]
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Թարմացնել ժամանակը", callback_data="pomodoro:refresh")],
            [InlineKeyboardButton(text="⏹️ Կանգնեցնել", callback_data="pomodoro:stop")]
        ]
    )


def get_test_options_keyboard(options: list[str], session_id: int) -> InlineKeyboardMarkup:
    rows = []
    for opt in options:
        # We send the option string directly
        rows.append([InlineKeyboardButton(text=opt, callback_data=f"test:ans:{session_id}:{opt}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_review_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Կրկնել (Flashcards)", callback_data="review:start")]
        ]
    )


def get_review_flashcard_keyboard(word: str, show_translation: bool, show_example: bool) -> InlineKeyboardMarkup:
    rows = []

    # If translation is shown, show rating buttons
    if show_translation:
        rows.append([
            InlineKeyboardButton(text="🇺🇸 US", callback_data=f"audio:us:{word}"),
            InlineKeyboardButton(text="🇬🇧 UK", callback_data=f"audio:uk:{word}"),
            InlineKeyboardButton(text="🎙️ Test", callback_data=f"word:pronounce:{word}"),
        ])
        rows.append([
            InlineKeyboardButton(text="❌ Again", callback_data=f"review:again:{word}"),
            InlineKeyboardButton(text="🟠 Hard", callback_data=f"review:hard:{word}"),
        ])
        rows.append([
            InlineKeyboardButton(text="✅ Good", callback_data=f"review:good:{word}"),
            InlineKeyboardButton(text="🚀 Easy", callback_data=f"review:easy:{word}"),
        ])
    else:
        rows.append([
            InlineKeyboardButton(text="🇺🇸 US", callback_data=f"audio:us:{word}"),
            InlineKeyboardButton(text="🇬🇧 UK", callback_data=f"audio:uk:{word}"),
            InlineKeyboardButton(text="🎙️ Test", callback_data=f"word:pronounce:{word}"),
        ])
        rows.append([
            InlineKeyboardButton(text="👁️ Show Translate", callback_data=f"review:show_tr:{word}"),
        ])

    if not show_example:
        rows.append([InlineKeyboardButton(text="💡 Show Example", callback_data=f"review:show_ex:{word}")])

    rows.append([InlineKeyboardButton(text="⏭️ Skip", callback_data=f"review:next:{word}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_placement_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Սկսել Placement Test", callback_data="placement:start")]
        ]
    )


def get_placement_options_keyboard(options: list[str], session_id: int) -> InlineKeyboardMarkup:
    rows = []
    for i, opt in enumerate(options):
        # We send the index i so it can be parsed as int in placement.py
        rows.append([InlineKeyboardButton(text=opt, callback_data=f"placement:ans:{session_id}:{i}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_level_keyboard(current_level: str = "A1", placement_done: bool = False, unlock_all: bool = False) -> InlineKeyboardMarkup:
    levels = [
        ("A1", "Beginner"),
        ("A2", "Elementary"),
        ("B1", "Intermediate"),
        ("B2", "Upper-Int"),
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


def get_coach_keyboard(focus_word: str | None = None) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="🔄 Թարմացնել", callback_data="coach:refresh"),
            InlineKeyboardButton(text="📘 Review հիմա", callback_data="coach:review"),
        ]
    ]
    if focus_word:
        rows.append([InlineKeyboardButton(text=f"🎯 Focus: {focus_word}", callback_data=f"coach:focus:{focus_word}")])

    rows.append([InlineKeyboardButton(text="📊 Մանրամասն վիճակագրություն", callback_data="coach:full_stats")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_search_keyboard(word: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧠 Explain with AI (Tutor)", callback_data=f"explain:{word}")],
            [InlineKeyboardButton(text="🔊 Լսել արտասանությունը", callback_data=f"audio:{word}")],
        ]
    )


def get_story_genre_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌆 Cyberpunk", callback_data="story:genre:cyberpunk"),
                InlineKeyboardButton(text="🔍 Detective", callback_data="story:genre:detective"),
            ],
            [
                InlineKeyboardButton(text="🧙 Fantasy", callback_data="story:genre:fantasy"),
                InlineKeyboardButton(text="😂 Comedy", callback_data="story:genre:comedy"),
            ],
            [InlineKeyboardButton(text="🏠 Real-life", callback_data="story:genre:reallife")],
        ]
    )


def get_palace_theme_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏛 Ancient Room", callback_data="palace:theme:ancient"),
                InlineKeyboardButton(text="💻 Cyber Loft", callback_data="palace:theme:cyber"),
            ],
            [
                InlineKeyboardButton(text="🕵️ Detective Office", callback_data="palace:theme:detective"),
                InlineKeyboardButton(text="🐉 Fantasy Tower", callback_data="palace:theme:fantasy"),
            ],
            [InlineKeyboardButton(text="🏠 Cozy Home", callback_data="palace:theme:cozy")],
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
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="adminui:refresh")],
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
