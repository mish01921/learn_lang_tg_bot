from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_word_keyboard(word: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Again", callback_data=f"again:{word}"),
                InlineKeyboardButton(text="🟠 Hard", callback_data=f"hard:{word}"),
            ],
            [
                InlineKeyboardButton(text="✅ Good", callback_data=f"good:{word}"),
                InlineKeyboardButton(text="🚀 Easy", callback_data=f"easy:{word}"),
            ],
            [InlineKeyboardButton(text="🔊 Արտասանություն", callback_data=f"pronounce:{word}")],
            [InlineKeyboardButton(text="⏭️ Հաջորդ բառը", callback_data=f"next:{word}")],
        ]
    )


def get_search_keyboard(word: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔊 Արտասանություն", callback_data=f"pronounce:{word}")],
        ]
    )


def get_level_keyboard(
    unlocked_level: str | None = None,
    placement_done: bool = False,
    unlock_all: bool = False,
) -> InlineKeyboardMarkup:
    unlocked_level = (unlocked_level or "").upper()

    def _label(level: str) -> str:
        if not placement_done:
            return f"🔒 {level}"
        if unlock_all:
            return f"🔓 {level}"
        return (f"🔓 {level}") if level == unlocked_level else (f"🔒 {level}")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_label("A1"), callback_data="level:A1"),
                InlineKeyboardButton(text=_label("A2"), callback_data="level:A2"),
            ],
            [
                InlineKeyboardButton(text=_label("B1"), callback_data="level:B1"),
                InlineKeyboardButton(text=_label("B2"), callback_data="level:B2"),
            ],
        ]
    )


def get_coach_keyboard(focus_word: str | None = None) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="🔁 Start Review", callback_data="coach:review"),
            InlineKeyboardButton(text="📚 Start New Words", callback_data="coach:new"),
        ]
    ]
    if focus_word:
        rows.append(
            [InlineKeyboardButton(text=f"🎯 Focus: {focus_word}", callback_data=f"coach:focus:{focus_word}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_review_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Կրկնել (Flashcards)", callback_data="rvc:start")]
        ]
    )


def get_review_flashcard_keyboard(
    word: str,
    *,
    show_translation: bool,
    show_example: bool,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="📖 Show Translate" if not show_translation else "✅ Translation Shown",
                callback_data=f"rvc:show_tr:{word}",
            ),
            InlineKeyboardButton(
                text="💬 Show Example" if not show_example else "✅ Example Shown",
                callback_data=f"rvc:show_ex:{word}",
            ),
        ],
        [
            InlineKeyboardButton(text="🔊 Արտասանություն", callback_data=f"rvc:pron:{word}"),
            InlineKeyboardButton(text="✅ Learned", callback_data=f"rvc:master:{word}"),
        ],
        [InlineKeyboardButton(text="⏭️ Next", callback_data=f"rvc:next:{word}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_test_options_keyboard(options: list[str], session_id: int) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(options), 2):
        chunk = options[i : i + 2]
        row = [
            InlineKeyboardButton(text=opt, callback_data=f"testans:{session_id}:{opt}")
            for opt in chunk
        ]
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Overview", callback_data="adminui:overview"),
                InlineKeyboardButton(text="👥 Users", callback_data="adminui:users:30"),
            ],
            [
                InlineKeyboardButton(text="🏆 Top", callback_data="adminui:top:10"),
                InlineKeyboardButton(text="📣 Broadcast Help", callback_data="adminui:broadcast_help"),
            ],
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="adminui:refresh")],
        ]
    )


def get_admin_users_keyboard(users: list[dict], limit: int) -> InlineKeyboardMarkup:
    rows = []
    safe_limit = max(1, min(int(limit or 20), 50))
    for u in users:
        uid = int(u.get("user_id") or 0)
        banned = int(u.get("banned") or 0) == 1
        if uid <= 0:
            continue
        row_label = (u.get("_row_label") or f"id={uid}")[:64]
        action_text = "✅" if banned else "🚫"
        action_cb = f"adminmod:{'unban' if banned else 'ban'}:{uid}:{safe_limit}"
        rows.append(
            [
                InlineKeyboardButton(text=row_label, callback_data=f"adminmod:user:{uid}:{safe_limit}"),
                InlineKeyboardButton(text=action_text, callback_data=action_cb),
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data=f"adminmod:refresh:{safe_limit}"),
            InlineKeyboardButton(text="⬅️ Dashboard", callback_data="adminmod:back"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_placement_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📝 Start Placement Test", callback_data="placement:start")]]
    )


def get_placement_options_keyboard(options: list[str], session_id: int) -> InlineKeyboardMarkup:
    rows = []
    letters = ["A", "B", "C", "D"]
    for idx, opt in enumerate(options):
        label = letters[idx] if idx < len(letters) else str(idx + 1)
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{label}) {opt}",
                    callback_data=f"placement:ans:{session_id}:{idx}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_story_genre_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌆 Cyberpunk", callback_data="story:genre:cyberpunk"),
                InlineKeyboardButton(text="🕵️ Detective", callback_data="story:genre:detective"),
            ],
            [
                InlineKeyboardButton(text="🐉 Fantasy", callback_data="story:genre:fantasy"),
                InlineKeyboardButton(text="😂 Comedy", callback_data="story:genre:comedy"),
            ],
            [InlineKeyboardButton(text="💬 Real-life", callback_data="story:genre:reallife")],
        ]
    )


def get_palace_theme_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏛️ Ancient Room", callback_data="palace:theme:ancient"),
                InlineKeyboardButton(text="🌆 Cyber Loft", callback_data="palace:theme:cyber"),
            ],
            [
                InlineKeyboardButton(text="🕵️ Detective Office", callback_data="palace:theme:detective"),
                InlineKeyboardButton(text="🐉 Fantasy Tower", callback_data="palace:theme:fantasy"),
            ],
            [InlineKeyboardButton(text="🏠 Cozy Home", callback_data="palace:theme:cozy")],
        ]
    )
