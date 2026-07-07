"""
Internationalization (i18n) module.
All bot interface strings in Armenian (hy), Russian (ru) and English (en).

Usage:
    from src.core.i18n import t, get_lang
    lang = get_lang(user_id)
    text = t("start_greeting", lang, name="Anna")
"""

from src.core.app_state import user_language

# ---------------------------------------------------------------------------
# Translation table
# ---------------------------------------------------------------------------

TRANSLATIONS: dict[str, dict[str, str]] = {

    # ── Language selector ──────────────────────────────────────────────────
    "choose_language": {
        "hy": "🌍 Խնդրում ենք ընտրել ինտերֆեյսի լեզուն․",
        "ru": "🌍 Выберите язык интерфейса:",
        "en": "🌍 Please choose your interface language:",
    },

    # ── Start ──────────────────────────────────────────────────────────────
    "start_greeting": {
        "hy": "Բարև, {name} 👋",
        "ru": "Привет, {name} 👋",
        "en": "Hello, {name} 👋",
    },
    "start_body": {
        "hy": (
            "Ես անգլերեն բառերի ուսուցման բոտն եմ 📚\n"
            "Կօգնեմ սովորել անգլերենի {total_words} ամենաօգտագործվող բառերը։\n\n"
            "━━━━━━━━━━━━━━━\n"
            "{daily_line}\n"
            "❌ «Again» — կկրկնվի կարճ ինտերվալով\n"
            "🟠 «Hard» — բարդ էր, բայց ճիշտ պատասխանեցիր\n"
            "✅ «Good» — լավ հիշեցիր\n"
            "🚀 «Easy» — հեշտ էր, ինտերվալը կմեծանա\n"
            "⏭️ «Հաջորդ բառը» — անցնել հաջորդին\n"
            "━━━━━━━━━━━━━━━\n\n"
            "📌 Հիմնական հրամաններ՝\n"
            "/word — նոր բառ\n"
            "/stats — վիճակագրություն\n"
            "/review — կրկնության ենթակա բառեր 📘\n"
            "/coach — AI մարզիչ 🧠\n"
            "/test — թեստ 🧪\n"
            "/story — պատմություն 📖\n"
            "/placement — մակարդակի թեստ 📝\n"
            "/language — փոխել լեզուն 🌐\n\n"
            "Պատրա՞ստ ես սկսել։ Սեղմիր /word 👇"
        ),
        "ru": (
            "Я бот для изучения английских слов 📚\n"
            "Помогу выучить {total_words} самых употребляемых слов.\n\n"
            "━━━━━━━━━━━━━━━\n"
            "{daily_line}\n"
            "❌ «Again» — повторится через короткий интервал\n"
            "🟠 «Hard» — сложно, но ответ был верным\n"
            "✅ «Good» — нормально запомнил\n"
            "🚀 «Easy» — легко, интервал растёт\n"
            "⏭️ «Следующее» — просто пропустить\n"
            "━━━━━━━━━━━━━━━\n\n"
            "📌 Команды:\n"
            "/word — новое слово\n"
            "/stats — статистика\n"
            "/review — слова на повторение 📘\n"
            "/coach — AI-тренер 🧠\n"
            "/test — тест 🧪\n"
            "/story — история 📖\n"
            "/placement — тест уровня 📝\n"
            "/language — сменить язык 🌐\n\n"
            "Готов начать? Нажми /word 👇"
        ),
        "en": (
            "I'm an English vocabulary learning bot 📚\n"
            "I'll help you learn the {total_words} most essential English words.\n\n"
            "━━━━━━━━━━━━━━━\n"
            "{daily_line}\n"
            "❌ «Again» — will repeat soon\n"
            "🟠 «Hard» — difficult but correct\n"
            "✅ «Good» — remembered well\n"
            "🚀 «Easy» — easy, interval grows\n"
            "⏭️ «Next» — skip for now\n"
            "━━━━━━━━━━━━━━━\n\n"
            "📌 Commands:\n"
            "/word — new word\n"
            "/stats — statistics\n"
            "/review — words to review 📘\n"
            "/coach — AI coach 🧠\n"
            "/test — quiz 🧪\n"
            "/story — story 📖\n"
            "/placement — level test 📝\n"
            "/language — change language 🌐\n\n"
            "Ready? Press /word 👇"
        ),
    },
    "daily_line_normal": {
        "hy": "🗓 Ամեն օր {daily_limit} նոր բառ",
        "ru": "🗓 Каждый день {daily_limit} новых слов",
        "en": "🗓 {daily_limit} new words every day",
    },
    "daily_line_admin": {
        "hy": "🗓 Ամեն օր {daily_limit} նոր բառ (ադմին — անսահմանափակ)",
        "ru": "🗓 Каждый день {daily_limit} новых слов (админ — без лимита)",
        "en": "🗓 {daily_limit} new words every day (admin — unlimited)",
    },

    # ── Placement prompt ───────────────────────────────────────────────────
    "placement_prompt": {
        "hy": (
            "🎯 Նախքան բառերն սկսելը, անցիր placement test-ը։\n"
            "Սա կորոշի քո CEFR մակարդակը և կփակի մնացած մակարդակները մինչև առաջընթաց գրանցելը։"
        ),
        "ru": (
            "🎯 Перед началом изучения слов пройди тест на уровень.\n"
            "Он определит твой уровень CEFR и заблокирует другие уровни до достижения прогресса."
        ),
        "en": (
            "🎯 Before starting with words, take the placement test.\n"
            "It will determine your CEFR level and lock other levels until you progress."
        ),
    },
    "placement_already_done": {
        "hy": "✅ Placement test-ը արդեն ավարտել եք։ Ձեր մակարդակը՝ {level}։ Շարունակենք առաջ 🚀",
        "ru": "✅ Вы уже прошли тест на уровень. Ваш уровень: {level}. Продолжаем! 🚀",
        "en": "✅ You have already completed the placement test. Your level: {level}. Let's continue! 🚀",
    },
    "placement_intro": {
        "hy": "📝 Placement test-ը կօգնի որոշել ձեր մեկնարկային մակարդակը (A1-B2):",
        "ru": "📝 Тест уровня поможет определить ваш начальный уровень (A1-B2):",
        "en": "📝 The placement test will help determine your starting level (A1-B2):",
    },
    "placement_completed": {
        "hy": (
            "✅ Placement test-ը ավարտվեց\n\n"
            "Արդյունք: {score}/{total}\n"
            "Ձեր մեկնարկային մակարդակը՝ {level}\n\n"
            "Այժմ կարող եք սկսել `/word` հրամանով։"
        ),
        "ru": (
            "✅ Тест уровня завершён\n\n"
            "Результат: {score}/{total}\n"
            "Ваш начальный уровень: {level}\n\n"
            "Теперь вы можете начать с помощью команды /word."
        ),
        "en": (
            "✅ Placement test completed\n\n"
            "Score: {score}/{total}\n"
            "Your starting level: {level}\n\n"
            "You can now start using the /word command."
        ),
    },

    # ── Main menu buttons ──────────────────────────────────────────────────
    "btn_roadmap": {
        "hy": "🗺 Ճանապարհ",
        "ru": "🗺 Прогресс",
        "en": "🗺 Roadmap",
    },
    "btn_daily_plan": {
        "hy": "🎯 Օրվա Պլան",
        "ru": "🎯 План на день",
        "en": "🎯 Daily Plan",
    },
    "btn_coach": {
        "hy": "👨‍🏫 Մարզիչ",
        "ru": "👨‍🏫 Тренер",
        "en": "👨‍🏫 Coach",
    },
    "btn_new_word": {
        "hy": "🆕 Նոր բառ",
        "ru": "🆕 Новое слово",
        "en": "🆕 New Word",
    },
    "btn_pomodoro": {
        "hy": "⏱ Պոմոդորո",
        "ru": "⏱ Помодоро",
        "en": "⏱ Pomodoro",
    },
    "btn_stats": {
        "hy": "📊 Վիճակագրություն",
        "ru": "📊 Статистика",
        "en": "📊 Stats",
    },
    "btn_help": {
        "hy": "❓ Օգնություն",
        "ru": "❓ Помощь",
        "en": "❓ Help",
    },
    "btn_language": {
        "hy": "🌐 Փոխել լեզուն",
        "ru": "🌐 Сменить язык",
        "en": "🌐 Change Language",
    },

    # ── Word card ──────────────────────────────────────────────────────────
    "word_level_label": {
        "hy": "🏷️ Մակարդակ",
        "ru": "🏷️ Уровень",
        "en": "🏷️ Level",
    },
    "word_label": {
        "hy": "📖 Բառ",
        "ru": "📖 Слово",
        "en": "📖 Word",
    },
    "word_coach_label": {
        "hy": "🧠 Մարզիչ",
        "ru": "🧠 Тренер",
        "en": "🧠 Coach",
    },
    "word_transcription_label": {
        "hy": "🔊 Արտասանություն",
        "ru": "🔊 Транскрипция",
        "en": "🔊 Transcription",
    },
    "word_translation_label": {
        "hy": "🇦🇲 Թարգմանություն",
        "ru": "🇷🇺 Перевод",
        "en": "🇬🇧 Translation",
    },
    "word_definition_label": {
        "hy": "📝 Սահմանում",
        "ru": "📝 Определение",
        "en": "📝 Definition",
    },
    "word_example_label": {
        "hy": "💬 Օրինակ",
        "ru": "💬 Пример",
        "en": "💬 Example",
    },
    "word_example_tr_label": {
        "hy": "🇦🇲 Թարգմանություն",
        "ru": "🇷🇺 Перевод",
        "en": "🇬🇧 Translation",
    },
    "word_coach_default": {
        "hy": "Պլանային առաջընթաց",
        "ru": "Плановый прогресс",
        "en": "Planned progress",
    },

    # ── Word keyboard buttons ──────────────────────────────────────────────
    "btn_listen_us": {
        "hy": "🔊 US",
        "ru": "🔊 US",
        "en": "🔊 US",
    },
    "btn_listen_uk": {
        "hy": "🔊 UK",
        "ru": "🔊 UK",
        "en": "🔊 UK",
    },
    "btn_test_voice": {
        "hy": "🎙️ Ձայն",
        "ru": "🎙️ Голос",
        "en": "🎙️ Voice",
    },
    "btn_again": {
        "hy": "❌ Կրկնել",
        "ru": "❌ Снова",
        "en": "❌ Again",
    },
    "btn_hard": {
        "hy": "🟠 Դժվար",
        "ru": "🟠 Сложно",
        "en": "🟠 Hard",
    },
    "btn_good": {
        "hy": "✅ Լավ",
        "ru": "✅ Хорошо",
        "en": "✅ Good",
    },
    "btn_easy": {
        "hy": "🚀 Հեշտ",
        "ru": "🚀 Легко",
        "en": "🚀 Easy",
    },
    "btn_practice": {
        "hy": "🧠 Կիրառել",
        "ru": "🧠 Практика",
        "en": "🧠 Practice",
    },
    "btn_next_word": {
        "hy": "⏭️ Հաջորդը",
        "ru": "⏭️ Следующее",
        "en": "⏭️ Next",
    },
    "btn_back_word": {
        "hy": "⬅️ Վերադառնալ",
        "ru": "⬅️ Назад",
        "en": "⬅️ Back",
    },

    # ── Placement button ───────────────────────────────────────────────────
    "btn_start_placement": {
        "hy": "📝 Սկսել Placement Test-ը",
        "ru": "📝 Начать тест уровня",
        "en": "📝 Start Placement Test",
    },
    "btn_start_level_test": {
        "hy": "📝 Սկսել Մակարդակի Թեստը",
        "ru": "📝 Начать тест уровня",
        "en": "📝 Start Level Test",
    },
    "level_test_intro": {
        "hy": "Դուք պատրաստվում եք անցնել նոր մակարդակ **{level}**:\nԴրա համար պետք է հանձնել թեստ:\nՊատասխանեք {total} հարցերից առնվազն {passing}-ին ճիշտ:\nԵթե ձախողեք, կկարողանաք կրկին փորձել վաղը:",
        "ru": "Вы собираетесь перейти на новый уровень **{level}**:\nДля этого необходимо пройти тест.\nОтветьте правильно как минимум на {passing} из {total} вопросов.\nЕсли не пройдете, сможете попробовать снова завтра.",
        "en": "You are about to move to a new level **{level}**:\nTo do so, you must pass a test.\nAnswer at least {passing} out of {total} questions correctly.\nIf you fail, you can try again tomorrow.",
    },
    "level_test_failed_today": {
        "hy": "❗ Դուք արդեն ձախողել եք **{level}** մակարդակի թեստը այսօր: Խնդրում ենք փորձել վաղը:",
        "ru": "❗ Вы уже не сдали тест на уровень **{level}** сегодня. Пожалуйста, попробуйте завтра.",
        "en": "❗ You already failed the **{level}** level test today. Please try again tomorrow.",
    },
    "level_test_passed": {
        "hy": "🎉 Շնորհավորում ենք: Դուք բարեհաջող հանձնեցիք թեստը և անցաք **{level}** մակարդակ:\nՃիշտ պատասխաններ՝ {score}/{total}",
        "ru": "🎉 Поздравляем! Вы успешно сдали тест и перешли на уровень **{level}**:\nПравильных ответов: {score}/{total}",
        "en": "🎉 Congratulations! You passed the test and moved to level **{level}**:\nCorrect answers: {score}/{total}",
    },
    "level_test_failed": {
        "hy": "😔 Ցավոք, դուք չհանձնեցիք թեստը:\nՃիշտ պատասխաններ՝ {score}/{total} (անհրաժեշտ էր {passing}):\nԽնդրում ենք շարունակել պարապել և փորձել վաղը:",
        "ru": "😔 К сожалению, вы не сдали тест.\nПравильных ответов: {score}/{total} (нужно {passing}).\nПродолжайте заниматься и попробуйте завтра.",
        "en": "😔 Unfortunately, you failed the test.\nCorrect answers: {score}/{total} (needed {passing}).\nPlease keep practicing and try again tomorrow.",
    },

    # ── Review buttons & guide ─────────────────────────────────────────────
    "btn_review_start": {
        "hy": "🔁 Կրկնել (Flashcards)",
        "ru": "🔁 Повторить (Flashcards)",
        "en": "🔁 Review (Flashcards)",
    },
    "btn_show_translate": {
        "hy": "👁️ Ցույց տալ թարգմանությունը",
        "ru": "👁️ Показать перевод",
        "en": "👁️ Show Translation",
    },
    "btn_show_example": {
        "hy": "💡 Ցույց տալ օրինակը",
        "ru": "💡 Показать пример",
        "en": "💡 Show Example",
    },
    "btn_skip": {
        "hy": "⏭️ Անցնել",
        "ru": "⏭️ Пропустить",
        "en": "⏭️ Skip",
    },
    "review_list_header": {
        "hy": "📘 **Review բառերի ցանկ**",
        "ru": "📘 **Список слов для повторения**",
        "en": "📘 **Review word list**",
    },
    "review_guide": {
        "hy": "💡 **Ինչպե՞ս գնահատել.**\n❌ **Again**: Չհիշեցի (կրկնել շուտով)\n🟠 **Hard**: Դժվարությամբ (1-2 օրից)\n✅ **Good**: Լավ հիշում եմ (3-4 օրից)\n🚀 **Easy**: Շատ հեշտ էր (7-10 օրից)",
        "ru": "💡 **Как оценивать:**\n❌ **Again**: Не вспомнил (повторить вскоре)\n🟠 **Hard**: С трудом (через 1-2 дня)\n✅ **Good**: Хорошо помню (через 3-4 дня)\n🚀 **Easy**: Очень легко (через 7-10 дней)",
        "en": "💡 **How to grade:**\n❌ **Again**: Couldn't recall (repeat soon)\n🟠 **Hard**: With difficulty (in 1-2 days)\n✅ **Good**: Remember well (in 3-4 days)\n🚀 **Easy**: Very easy (in 7-10 days)",
    },
    "review_press_start": {
        "hy": "Սեղմեք «🔁 Կրկնել (Flashcards)»։",
        "ru": "Нажмите «🔁 Повторить (Flashcards)».",
        "en": "Click «🔁 Review (Flashcards)».",
    },

    # ── Coach buttons ──────────────────────────────────────────────────────
    "btn_coach_refresh": {
        "hy": "🔄 Թարմացնել",
        "ru": "🔄 Обновить",
        "en": "🔄 Refresh",
    },
    "btn_coach_review": {
        "hy": "📘 Review հիմա",
        "ru": "📘 Повторить сейчас",
        "en": "📘 Review now",
    },
    "btn_coach_stats": {
        "hy": "📊 Մանրամասն վիճակագրություն",
        "ru": "📊 Подробная статистика",
        "en": "📊 Detailed statistics",
    },

    # ── Stats messages ─────────────────────────────────────────────────────
    "stats_header": {
        "hy": "📊 **Ուսումնական վիճակագրություն**",
        "ru": "📊 **Учебная статистика**",
        "en": "📊 **Learning Dashboard**",
    },
    "stats_progress": {
        "hy": "🏆 Առաջընթաց",
        "ru": "🏆 Прогресс",
        "en": "🏆 Progress",
    },
    "stats_learned": {
        "hy": "✅ Սովորած",
        "ru": "✅ Изучено",
        "en": "✅ Learned",
    },
    "stats_accuracy": {
        "hy": "🎯 Ճշտություն",
        "ru": "🎯 Точность",
        "en": "🎯 Accuracy",
    },
    "stats_streak": {
        "hy": "🔥 Անընդմեջ օրեր",
        "ru": "🔥 Серия дней",
        "en": "🔥 Streak",
    },
    "stats_today": {
        "hy": "📅 Այսօր",
        "ru": "📅 Сегодня",
        "en": "📅 Today",
    },
    "stats_review_queue": {
        "hy": "📘 Կրկնության հերթ",
        "ru": "📘 Очередь повторения",
        "en": "📘 Review queue",
    },

    # ── Search ─────────────────────────────────────────────────────────────
    "search_prompt": {
        "hy": "🔎 Գրիր այն բառը, որը ցանկանում ես փնտրել (անգլերենով)․\nՉեղարկելու համար գրիր՝ cancel",
        "ru": "🔎 Напиши слово для поиска (на английском):\nДля отмены напиши: cancel",
        "en": "🔎 Type the word you want to search (in English):\nTo cancel type: cancel",
    },
    "search_cancelled": {
        "hy": "❌ Որոնումը չեղարկվեց։",
        "ru": "❌ Поиск отменен.",
        "en": "❌ Search cancelled.",
    },
    "searching": {
        "hy": "🔎 Փնտրում եմ՝ {query}...",
        "ru": "🔎 Ищу: {query}...",
        "en": "🔎 Searching: {query}...",
    },
    "search_not_found": {
        "hy": "❌ «{word}» բառը չգտնվեց տվյալների բազայում։",
        "ru": "❌ Слово «{word}» не найдено в базе.",
        "en": "❌ Word «{word}» not found in the database.",
    },
    "search_result_header": {
        "hy": "🔎 Որոնման արդյունք",
        "ru": "🔎 Результат поиска",
        "en": "🔎 Search result",
    },

    # ── Story ──────────────────────────────────────────────────────────────
    "story_limit_reached": {
        "hy": "📖 Այսօրվա Story limit-ը լրացել է։",
        "ru": "📖 Дневной лимит историй исчерпан.",
        "en": "📖 Daily Story limit reached.",
    },
    "story_need_words": {
        "hy": "📖 Story mode-ի համար այսօրվա առնվազն 3 բառ պետք է անցած լինի։",
        "ru": "📖 Для режима Story нужно выучить хотя бы 3 слова за сегодня.",
        "en": "📖 You need at least 3 learned words today for Story mode.",
    },
    "story_generating": {
        "hy": "Պատմությունը գեներացվում է... ⏳",
        "ru": "История генерируется... ⏳",
        "en": "Generating story... ⏳",
    },
    "story_intro": {
        "hy": "📖 **Պատմությունների ռեժիմ (Story Mode)**\n\nԸնտրիր ժանրը, և ես կստեղծեմ կարճ պատմություն այսօրվա բառերով։\nԹիրախային բառեր: {words}",
        "ru": "📖 **Режим историй (Story Mode)**\n\nВыберите жанр, и я создам короткую историю с сегодняшними словами.\nЦелевые слова: {words}",
        "en": "📖 **Story Mode**\n\nChoose a genre and I will create a short story with today's words.\nTarget words: {words}",
    },

    # ── Palace ─────────────────────────────────────────────────────────────
    "palace_limit_reached": {
        "hy": "🧠 Այսօրվա Palace limit-ը լրացել է։",
        "ru": "🧠 Дневной лимит Memory Palace исчерпан.",
        "en": "🧠 Daily Memory Palace limit reached.",
    },
    "palace_need_words": {
        "hy": "🧠 Memory Palace-ի համար այսօրվա առնվազն 3 բառ պետք է անցած լինի։",
        "ru": "🧠 Для Memory Palace нужно выучить хотя бы 3 слова за сегодня.",
        "en": "🧠 You need at least 3 learned words today for Memory Palace.",
    },
    "palace_generating": {
        "hy": "Memory Palace-ը գեներացվում է... ⏳",
        "ru": "Memory Palace генерируется... ⏳",
        "en": "Generating Memory Palace... ⏳",
    },
    "palace_intro": {
        "hy": "🧠 **Անձնական «Հիշողության պալատ» (Memory Palace)**\n\nԸնտրիր թեման, և ես կստեղծեմ տեսողական հիշողության «սենյակ» հենց այսօրվա բառերով։\nԹիրախային բառեր: {words}",
        "ru": "🧠 **Личный «Дворец памяти» (Memory Palace)**\n\nВыберите тему, и я создам «комнату» памяти с сегодняшними словами.\nЦелевые слова: {words}",
        "en": "🧠 **Personal Memory Palace**\n\nChoose a theme and I will build a visual room with today's words.\nTarget words: {words}",
    },

    # ── Explain ────────────────────────────────────────────────────────────
    "explain_prompt": {
        "hy": "🧐 Ի՞նչն եք ցանկանում բացատրել (բառ, արտահայտություն կամ քերականություն)։\nՕրինակ՝ 'make vs do' կամ 'get used to':\nՉեղարկելու համար գրիր՝ cancel",
        "ru": "🧐 Что вы хотите объяснить (слово, фразу или грамматику)?\nПример: 'make vs do' или 'get used to':\nДля отмены напишите: cancel",
        "en": "🧐 What would you like explained (word, phrase or grammar)?\nExample: 'make vs do' or 'get used to':\nTo cancel type: cancel",
    },
    "explain_cancelled": {
        "hy": "❌ Բացատրությունը չեղարկվեց։",
        "ru": "❌ Объяснение отменено.",
        "en": "❌ Explanation cancelled.",
    },
    "explain_thinking": {
        "hy": "🧐 Մտածում եմ «{query}»-ի մասին... ⏳",
        "ru": "🧐 Думаю над «{query}»... ⏳",
        "en": "🧐 Thinking about «{query}»... ⏳",
    },

    # ── Test ───────────────────────────────────────────────────────────────
    "test_need_words": {
        "hy": "🧪 Թեստ սկսելու համար պետք է առնվազն 4 անցած բառ։ Սեղմիր կոճակը սկսելու համար👇",
        "ru": "🧪 Для начала теста нужно выучить хотя бы 4 слова. Нажми кнопку ниже👇",
        "en": "🧪 You need to learn at least 4 words before starting a quiz. Click below👇",
    },
    "test_question": {
        "hy": "🧪 **Թեստ [{index}/{total}]**\n\nԸնտրիր ճիշտ անգլերեն բառը այս թարգմանության համար․\n🇦🇲 {translation}",
        "ru": "🧪 **Тест [{index}/{total}]**\n\nВыберите правильное английское слово для перевода:\n🇷🇺 {translation}",
        "en": "🧪 **Quiz [{index}/{total}]**\n\nChoose the correct English word for this definition/translation:\n🇬🇧 {translation}",
    },
    "test_completed": {
        "hy": "🎉 Թեստը ավարտվեց\n\nԱրդյունք: {score}/{total} ճիշտ պատասխան 🎯",
        "ru": "🎉 Тест завершён\n\nРезультат: {score}/{total} правильных ответов 🎯",
        "en": "🎉 Quiz completed\n\nResult: {score}/{total} correct answers 🎯",
    },

    # ── Level messages ─────────────────────────────────────────────────────
    "placement_required": {
        "hy": "Սկզբում անցիր placement test-ը։",
        "ru": "Сначала пройдите тест на уровень.",
        "en": "Please complete the placement test first.",
    },
    "level_changed": {
        "hy": "Մակարդակը փոխվեց՝ {level}։ Սեղմիր /word շարունակելու համար։",
        "ru": "Уровень изменён: {level}. Нажмите /word.",
        "en": "Level changed to {level}. Press /word.",
    },
    "level_locked": {
        "hy": "🔒 Այս պահին բաց է միայն {level} մակարդակը։",
        "ru": "🔒 Сейчас открыт только уровень {level}.",
        "en": "🔒 Only level {level} is unlocked right now.",
    },

    # ── Reset ──────────────────────────────────────────────────────────────
    "reset_done": {
        "hy": "♻️ Առաջընթացը զրոյացվեց։ Սովորած բառերը պահպանվել են։",
        "ru": "♻️ Прогресс сброшен. Изученные слова сохранены.",
        "en": "♻️ Progress reset. Learned words were preserved.",
    },
    "reset_all_done": {
        "hy": "⚠️ Ամբողջ պատմությունը ջնջվեց։",
        "ru": "⚠️ Вся история удалена.",
        "en": "⚠️ All history deleted.",
    },

    # ── Banned ─────────────────────────────────────────────────────────────
    "banned_message": {
        "hy": "🚫 Դուք արգելափակված եք։",
        "ru": "🚫 Вы заблокированы.",
        "en": "🚫 Вы заблокированы.",
    },

    # ── No word / daily limit ──────────────────────────────────────────────
    "no_words_available": {
        "hy": "🎉 Բոլոր բառերը սովորել ես, շարունակիր կրկնել /review",
        "ru": "🎉 Все доступные слова изучены! Попробуй /review.",
        "en": "🎉 Words done, keep going! Try /review.",
    },
    "daily_limit_reached": {
        "hy": "📅 Այսօր սովորել ես {limit} բառ։ Վերադարձիր վաղը կամ կրկնիր՝ /review",
        "ru": "📅 Сегодня изучено {limit} слов. Вернитесь завтра или повторите: /review",
        "en": "📅 You've learned {limit} words today. Come back tomorrow or review: /review",
    },

    # ── Coach ──────────────────────────────────────────────────────────────
    "coach_thinking": {
        "hy": "🧠 Մարզիչը վերլուծում է քո առաջընթացը... ⏳",
        "ru": "🧠 Тренер анализирует твой прогресс... ⏳",
        "en": "🧠 Coach is analyzing your progress... ⏳",
    },
    "coach_header": {
        "hy": "👨‍🏫 **Մարզիչի վերլուծություն**",
        "ru": "👨‍🏫 **Анализ от Тренера**",
        "en": "👨‍🏫 **Coach Analysis**",
    },
    "pronunciation_analyzing": {
        "hy": "🎙️ Վերլուծում եմ արտասանությունը... ⏳",
        "ru": "🎙️ Анализирую произношение... ⏳",
        "en": "🎙️ Analyzing pronunciation... ⏳",
    },
    "pronunciation_header": {
        "hy": "🎙️ Արտասանության վերլուծություն՝ {word}",
        "ru": "🎙️ Анализ произношения: {word}",
        "en": "🎙️ Pronunciation Analysis: {word}",
    },
    "practice_intro": {
        "hy": "🧠 **Ինտերակտիվ Պրակտիկա՝ «{word}»**\n\n✍️ Գրիր **ցանկացած անգլերեն նախադասություն** կամ նույնիսկ կարճ միտք, որտեղ օգտագործում ես **{word}** բառը։\n\n🤖 *Իմ AI ուսուցիչը՝*\n1️⃣ Կստուգի քո քերականությունը և բառի ճիշտ կիրառությունը\n2️⃣ Կառաջարկի ավելի բնական ու գրագետ տարբերակներ\n3️⃣ Կտա կարևոր խորհուրդներ և նրբություններ",
        "ru": "🧠 **Интерактивная практика: «{word}»**\n\n✍️ Напиши **любое английское предложение** или короткую мысль с использованием слова **{word}**.\n\n🤖 *Мой AI-учитель:*\n1️⃣ Проверит грамматику и правильность использования слова\n2️⃣ Предложит более естественные варианты\n3️⃣ Даст полезные советы и нюансы",
        "en": "🧠 **Interactive Practice: «{word}»**\n\n✍️ Write **any English sentence** or short phrase using the word **{word}**.\n\n🤖 *My AI Tutor:*\n1️⃣ Will check your grammar and correct usage\n2️⃣ Will suggest more natural & native alternatives\n3️⃣ Will provide valuable tips and nuances",
    },
    "pronounce_intro": {
        "hy": "🎙️ **Արտասանության Առաջադրանք՝ «{word}»**\n\nԽնդրում եմ արտասանել «**{word}**» բառը ձայնային հաղորդագրությամբ (Voice)։\nԵս կվերլուծեմ քո արտասանությունը ELSA-ի նման։",
        "ru": "🎙️ **Задание по произношению: «{word}»**\n\nПожалуйста, произнесите слово «**{word}**» голосовым сообщением (Voice).\nЯ проанализирую ваше произношение как ELSA.",
        "en": "🎙️ **Pronunciation Task: «{word}»**\n\nPlease pronounce the word «**{word}**» using a voice message.\nI will analyze your pronunciation like ELSA.",
    },
    "toast_next_word": {
        "hy": "Բացում եմ հաջորդ բառը 🚀",
        "ru": "Открываю следующее слово 🚀",
        "en": "Opening next word 🚀",
    },
    "toast_prev_word": {
        "hy": "Վերադառնում ենք նախորդ բառին ⬅️",
        "ru": "Возвращаемся к предыдущему слову ⬅️",
        "en": "Returning to previous word ⬅️",
    },
    "practice_analyzing": {
        "hy": "🧐 **Վերլուծում եմ քո նախադասությունը «{word}» բառով...**\n⏳ *Խնդրում եմ սպասել մի քանի վայրկյան*",
        "ru": "🧐 **Анализирую твоё предложение со словом «{word}»...**\n⏳ *Пожалуйста, подождите несколько секунд*",
        "en": "🧐 **Analyzing your sentence with «{word}»...**\n⏳ *Please wait a few seconds*",
    },
    "practice_header": {
        "hy": "🧠 **AI Ուսուցչի Վերլուծությունը՝ «{word}»**",
        "ru": "🧠 **Анализ от AI Учителя: «{word}»**",
        "en": "🧠 **AI Teacher Analysis: «{word}»**",
    },

    # ── Stats ──────────────────────────────────────────────────────────────
    "stats_title": {
        "hy": "📊 **Ուսումնական Վիճակագրություն**",
        "ru": "📊 **Учебная Статистика**",
        "en": "📊 **Learning Dashboard**",
    },

    # ── Roadmap & Plan ─────────────────────────────────────────────────────
    "plan_choose": {
        "hy": (
            "🎓 **Ընտրիր քո ուսումնական պլանը:**\n\n"
            "🌱 **Lite (3/օր):** Արագ լոկ, հարմար ծանր ու կտրուկ օրերի համար\n"
            "🐢 **Steady (5/օր):** Բնական ռիթմ (default)\n"
            "🔥 **Deep (15/օր):** Ինտենսիվ + AI Tutor + Pomodoro\n"
            "⚙️ **Custom:** Ինքդ ֆիքսիր 1-30 բառ/օր\n\n"
            "↕️ Ներքև ընտրիր թե ինչ պլան կուզես:"
        ),
        "ru": (
            "🎓 **Выберите учебный план:**\n\n"
            "🌱 **Lite (3/день):** Лёгкий темп для занятых дней\n"
            "🐢 **Steady (5/день):** Стабильный ритм (default)\n"
            "🔥 **Deep (15/день):** Интенсив + AI Tutor + Pomodoro\n"
            "⚙️ **Custom:** Сами укажите кол-во (1-30)\n\n"
            "↕️ Выберите удобный вариант:"
        ),
        "en": (
            "🎓 **Choose your study plan:**\n\n"
            "🌱 **Lite (3/day):** Easy pace for busy days\n"
            "🐢 **Steady (5/day):** Balanced rhythm (default)\n"
            "🔥 **Deep (15/day):** Intensive + AI Tutor + Pomodoro\n"
            "⚙️ **Custom:** Set your own goal (1-30)\n\n"
            "↕️ Pick the plan that fits you:"
        ),
    },
    "plan_set_success": {
        "hy": "✅ Պլանը փոխվեց — **{plan_label}** ({goal} բառ/օր):",
        "ru": "✅ План изменён — **{plan_label}** ({goal} слов/день).",
        "en": "✅ Plan updated — **{plan_label}** ({goal} words/day).",
    },
    "plan_custom_ask": {
        "hy": "⚙️ Ուղարկիր թիվ 1-30 — քո օրական բառի նպատակը:",
        "ru": "⚙️ Отправьте число от 1 до 30 — ваша дневная цель:",
        "en": "⚙️ Send a number from 1 to 30 — your daily word goal:",
    },
    "global_progress_text": {
        "hy": (
            "🗺 **Քո Ճանապարհը (Global Progress)**\n\n"
            "📍 Ներկայիս մակարդակը՝ **{level}**\n"
            "🎯 Հաջորդ թիրախը՝ **{next_level}**\n\n"
            "📚 Սովորած բառեր՝ **{learned} / {total_words}**\n"
            "`{progress_bar}` {percent}%\n"
            "📈 Մինչև {next_level} մնացել է ևս **{remaining} բառ**\n\n"
            "🔥 Անընդմեջ օրեր՝ **{streak} օր**\n"
            "🧠 Դժվար բառեր՝ **{hard} բառ**\n"
            "⚖️ Ճշգրտություն՝ **{accuracy}%**"
        ),
        "ru": (
            "🗺 **Ваш Прогресс (Global Progress)**\n\n"
            "📍 Текущий уровень: **{level}**\n"
            "🎯 Следующая цель: **{next_level}**\n\n"
            "📚 Изучено слов: **{learned} / {total_words}**\n"
            "`{progress_bar}` {percent}%\n"
            "📈 До {next_level} осталось **{remaining} слов**\n\n"
            "🔥 Дней подряд: **{streak} дней**\n"
            "🧠 Сложных слов: **{hard} слов**\n"
            "⚖️ Точность: **{accuracy}%**"
        ),
        "en": (
            "🗺 **Your Roadmap (Global Progress)**\n\n"
            "📍 Current Level: **{level}**\n"
            "🎯 Next Target: **{next_level}**\n\n"
            "📚 Learned Words: **{learned} / {total_words}**\n"
            "`{progress_bar}` {percent}%\n"
            "📈 Words left until {next_level}: **{remaining} words**\n\n"
            "🔥 Current Streak: **{streak} days**\n"
            "🧠 Hard Words: **{hard} words**\n"
            "⚖️ Accuracy: **{accuracy}%**"
        ),
    },
    "roadmap_title_deep": {
        "hy": "🎯 **Քո օրվա պլանը (🔥 Deep):**\nՀետևիր այս քայլերին լավագույն արդյունքի համար:",
        "ru": "🎯 **Ваш план на день (🔥 Deep):**\nСледуйте этим шагам для наилучшего результата:",
        "en": "🎯 **Your Daily Plan (🔥 Deep Focus):**\nFollow these steps for best results:",
    },
    "roadmap_title_steady": {
        "hy": "🎯 **Քո օրվա պլանը (🐢 Steady):**\nՀետևիր այս քայլերին լավագույն արդյունքի համար:",
        "ru": "🎯 **Ваш план на день (🐢 Steady):**\nСледуйте этим шагам для наилучшего результата:",
        "en": "🎯 **Your Daily Plan (🐢 Steady Learner):**\nFollow these steps for best results:",
    },
    "roadmap_title_lite": {
        "hy": "🎯 **Քո օրվա պլանը (🌱 Lite):**\nՀետևիր այս քայլերին լավագույն արդյունքի համար:",
        "ru": "🎯 **Ваш план на день (🌱 Lite):**\nСледуйте этим шагам для наилучшего результата:",
        "en": "🎯 **Your Daily Plan (🌱 Lite):**\nFollow these steps for best results:",
    },
    "roadmap_title_custom": {
        "hy": "🎯 **Քո օրվա պլանը (⚙️ Custom):**\nՀետևիր այս քայլերին լավագույն արդյունքի համար:",
        "ru": "🎯 **Ваш план на день (⚙️ Custom):**\nСледуйте этим шагам для наилучшего результата:",
        "en": "🎯 **Your Daily Plan (⚙️ Custom):**\nFollow these steps for best results:",
    },
    "step_review": {
        "hy": "Կրկնություն ({count} բառ)",
        "ru": "Повторение ({count} слов)",
        "en": "Review ({count} words)",
    },
    "step_new_words": {
        "hy": "Նոր բառեր ({count}/{target})",
        "ru": "Новые слова ({count}/{target})",
        "en": "New words ({count}/{target})",
    },
    "step_story": {
        "hy": "Օրվա պատմությունը",
        "ru": "История дня",
        "en": "Daily story",
    },
    "step_pomodoro": {
        "hy": "Pomodoro Focus Session",
        "ru": "Pomodoro Focus Session",
        "en": "Pomodoro Focus Session",
    },
    "step_practice": {
        "hy": "AI Practice (նախադասություններ)",
        "ru": "AI Практика (предложения)",
        "en": "AI Practice (sentences)",
    },

    # ── Pomodoro ───────────────────────────────────────────────────────────
    "pomo_active": {
        "hy": "🚀 **Դուք արդեն ունեք ակտիվ Focus Session:**\n\n⏳ Մնացել է՝ `{time_str}`\n\nՇարունակիր սովորել 💪",
        "ru": "🚀 **У вас уже есть активная фокус-сессия:**\n\n⏳ Осталось: `{time_str}`\n\nПродолжайте учиться 💪",
        "en": "🚀 **You already have an active Focus Session:**\n\n⏳ Remaining: `{time_str}`\n\nKeep learning 💪",
    },
    "pomo_active_progress": {
        "hy": "⏱ **Focus Session-ը ակտիվ է**\n\n⏳ Մնացել է՝ `{time_str}`\n\n{bar} `{pct}%`\n\nԿենտրոնացիր ուսման վրա 📚",
        "ru": "⏱ **Фокус-сессия активна**\n\n⏳ Осталось: `{time_str}`\n\n{bar} `{pct}%`\n\nСосредоточьтесь на учебе 📚",
        "en": "⏱ **Focus Session Active**\n\n⏳ Remaining: `{time_str}`\n\n{bar} `{pct}%`\n\nFocus on your studies 📚",
    },
    "pomo_intro": {
        "hy": "⏱ **Pomodoro Timer**\n\n25 րոպեանոց ֆոկուս սեսիան կօգնի քեզ ավելի արդյունավետ սովորել առանց հոգնելու։\nՊատրա՞ստ ես սկսել։",
        "ru": "⏱ **Pomodoro Timer**\n\n25-минутная фокус-сессия поможет вам учиться эффективнее без усталости.\nГотовы начать?",
        "en": "⏱ **Pomodoro Timer**\n\nA 25-minute focus session will help you study more effectively without getting tired.\nReady to start?",
    },
    "pomo_started": {
        "hy": "🚀 **Focus Session-ը սկսվեց (25:00):**\n\nԱյժմ կենտրոնացիր միայն բառեր սովորելու վրա։\nՍեղմիր «🔄 Թարմացնել», որպեսզի տեսնես մնացած ժամանակը։",
        "ru": "🚀 **Фокус-сессия началась (25:00):**\n\nСейчас сосредоточьтесь только на изучении слов.\nНажмите «🔄 Обновить», чтобы увидеть оставшееся время.",
        "en": "🚀 **Focus Session started (25:00):**\n\nNow focus solely on learning words.\nClick «🔄 Refresh» to see remaining time.",
    },
    "pomo_finished": {
        "hy": "🔔 **Ժամանակն ավարտվեց!**\n\nՀիանալի աշխատանք։ Հիմա հանգստացիր 5 րոպե (Break), ապա կարող ես սկսել նորից։",
        "ru": "🔔 **Время вышло!**\n\nОтличная работа! Отдохните 5 минут (перерыв), затем можете начать снова.",
        "en": "🔔 **Time is up!**\n\nGreat job! Take a 5 minute break, then you can start again.",
    },
    "pomo_stopped": {
        "hy": "⏹ Focus session-ը դադարեցված է։",
        "ru": "⏹ Фокус-сессия остановлена.",
        "en": "⏹ Focus session stopped.",
    },
    "pomo_not_active": {
        "hy": "⏱ Session-ը ակտիվ չէ։",
        "ru": "⏱ Сессия не активна.",
        "en": "⏱ Session is not active.",
    },

    # ── Help Text ──────────────────────────────────────────────────────────
    "help_text": {
        "hy": """❓ <b>Ինչպե՞ս օգտվել բոտից:</b>

Ահա հիմնական հրամանները և դրանց օգտագործման <b>օրինակները</b>․

📖 <b>Ուսումնական հրամաններ:</b>
• /word — Ստանալ նոր բառ
• /review — Կրկնել անցած բառերը (Flashcards)
• /test — Ստուգել գիտելիքները թեստի միջոցով
• /learned — Տեսնել ձեր բոլոր սովորած բառերը

🤖 <b>AI Հնարավորություններ:</b>
• /coach — AI մարզիչի վերլուծություն և խորհուրդներ
• /story — Ստեղծել պատմություն ձեր սովորած բառերով
• /palace — Ստեղծել «Հիշողության պալատ» (Memory Palace)

🌐 <b>Լեզվի ընտրություն:</b>
• /language — Փոխել ինտերֆեյսի լեզուն (Հայերեն, Ռուսերեն, Անգլերեն)

🎙️ <b>Արտասանության ստուգում:</b>
Յուրաքանչյուր բառի տակ սեղմեք <b>🎙️ Test my Voice</b> կոճակը և ուղարկեք ձայնային հաղորդագրություն (Voice)։

🧠 <b>Ինտերակտիվ Պրակտիկա (Practice):</b>
Բառի քարտի վրա սեղմեք <b>🧠 Կիրառել (Practice)</b> կոճակը և գրեք նախադասություն այդ բառով։

📈 <b>Պլան և Dashboard:</b>
• /roadmap — Տեսնել օրվա անելիքները
• /stats — Ձեր առաջընթացը և Streak-ը
• /plan — Փոխել ուսումնական տեմպը (Steady/Deep)

💡 <i>Հուշում: Օգտագործեք /help հրամանը ցանկացած պահի այս ուղեցույցը տեսնելու համար:</i>""",

        "ru": """❓ <b>Как пользоваться ботом:</b>

Основные команды и <b>примеры</b> использования:

📖 <b>Учебные команды:</b>
• /word — Получить новое слово
• /review — Повторить изученные слова (Flashcards)
• /test — Проверить знания через тест
• /learned — Посмотреть все изученные слова

🤖 <b>AI Возможности:</b>
• /coach — Анализ и советы от AI-тренера
• /story — Создать историю со словарным запасом
• /palace — Создать «Дворец памяти» (Memory Palace)

🌐 <b>Выбор языка:</b>
• /language — Сменить язык интерфейса

🎙️ <b>Проверка произношения:</b>
Нажмите <b>🎙️ Проверить голос</b> под картой слова и отправьте голосовое сообщение.

🧠 <b>Практика (Practice):</b>
Нажмите <b>🧠 Практиковать</b> и составьте предложение с этим словом.

📈 <b>План и Статистика:</b>
• /roadmap — План на день
• /stats — Ваш прогресс и Серия дней (Streak)
• /plan — Сменить темп (Steady/Deep)

💡 <i>Используйте команду /help в любой момент для вызова этой справки.</i>""",

        "en": """❓ <b>How to use the bot:</b>

Main commands and usage <b>examples</b>:

📖 <b>Study Commands:</b>
• /word — Get a new word
• /review — Review learned words (Flashcards)
• /test — Test your knowledge with a quiz
• /learned — View all your learned words

🤖 <b>AI Features:</b>
• /coach — AI coach analysis and tips
• /story — Generate a story with your words
• /palace — Create a Memory Palace

🌐 <b>Language Settings:</b>
• /language — Change interface language

🎙️ <b>Pronunciation Check:</b>
Press <b>🎙️ Test my Voice</b> under any word card and send a voice message.

🧠 <b>Interactive Practice:</b>
Press <b>🧠 Practice</b> on a word card and write a sentence using that word.

📈 <b>Plan & Dashboard:</b>
• /roadmap — View today's tasks
• /stats — Your progress and streak
• /plan — Change study pace (Steady/Deep)

💡 <i>Use the /help command anytime to view this guide.</i>""",
    },

    # ── Roadmap ────────────────────────────────────────────────────────────
    "roadmap_header_steady": {
        "hy": "🗺 **Քո օրվա պլանը (Հանգիստ):**",
        "ru": "🗺 **Твой план на день (Спокойный):**",
        "en": "🗺 **Your daily plan (Steady):**",
    },
    "roadmap_header_deep": {
        "hy": "🗺 **Քո օրվա պլանը (Ինտենսիվ):**",
        "ru": "🗺 **Твой план на день (Intensive):**",
        "en": "🗺 **Your daily plan (Intensive):**",
    },
    "roadmap_follow": {
        "hy": "Հետևիր այս քայլերին լավագույն արդյունքի համար․",
        "ru": "Следуй этим шагам для лучшего результата:",
        "en": "Follow these steps for the best result:",
    },

    # ── Story ──────────────────────────────────────────────────────────────
    "story_header": {
        "hy": "📖 Քո օրվա պատմությունը․",
        "ru": "📖 Твоя история на сегодня:",
        "en": "📖 Your story for today:",
    },
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_lang(user_id: int) -> str:
    """Return the user's selected language code (default: 'hy')."""
    return user_language.get(user_id, "hy")


def t(key: str, lang: str, **kwargs) -> str:
    """
    Return the translated string for *key* in *lang*.
    Falls back to 'en', then the raw key if nothing is found.
    Formats the string with any **kwargs placeholders.
    """
    entry = TRANSLATIONS.get(key, {})
    text = entry.get(lang) or entry.get("en") or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
