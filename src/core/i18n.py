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
        "hy": "🗺 Ճանապարհային քարտեզ",
        "ru": "🗺 Маршрут",
        "en": "🗺 Roadmap",
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
        "hy": "🇺🇸 Լսել (US)",
        "ru": "🇺🇸 Слушать (US)",
        "en": "🇺🇸 Listen (US)",
    },
    "btn_listen_uk": {
        "hy": "🇬🇧 Լսել (UK)",
        "ru": "🇬🇧 Слушать (UK)",
        "en": "🇬🇧 Listen (UK)",
    },
    "btn_test_voice": {
        "hy": "🎙️ Ստուգել արտասանությունը",
        "ru": "🎙️ Проверить голос",
        "en": "🎙️ Test my Voice",
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
        "hy": "🧠 Կիրառել (Practice)",
        "ru": "🧠 Практиковать",
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

    # ── Review buttons ─────────────────────────────────────────────────────
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
        "hy": "🔥 Ստրիկ (օրեր)",
        "ru": "🔥 Стрик (дней)",
        "en": "🔥 Streak (days)",
    },
    "stats_today": {
        "hy": "📅 Այսօր",
        "ru": "📅 Сегодня",
        "en": "📅 Today",
    },
    "stats_review_queue": {
        "hy": "📘 Կրկնության սպասող բառեր",
        "ru": "📘 Очередь на повторение",
        "en": "📘 Review queue",
    },

    # ── Roadmap & Plan ─────────────────────────────────────────────────────
    "plan_choose": {
        "hy": "🎓 **Ընտրիր քո ուսումնական պլանը:**\n\n**🐢 Steady Learner:** Օրական 5 նոր բառ + Կրկնություն + Պատմություն։\n**🔥 Deep Focus:** Օրական 10 նոր բառ + Pomodoro + Գործնական նախադասություններ + AI Tutor։",
        "ru": "🎓 **Выберите учебный план:**\n\n**🐢 Steady Learner:** 5 новых слов в день + Повторение + История.\n**🔥 Deep Focus:** 10 новых слов в день + Pomodoro + Практические предложения + AI Tutor.",
        "en": "🎓 **Choose your study plan:**\n\n**🐢 Steady Learner:** 5 new words/day + Review + Story.\n**🔥 Deep Focus:** 10 new words/day + Pomodoro + Practice sentences + AI Tutor.",
    },
    "roadmap_title_deep": {
        "hy": "🗺 **Քո օրվա պլանը (Ինտենսիվ):**\nՀետևիր այս քայլերին լավագույն արդյունքի համար:",
        "ru": "🗺 **Ваш план на день (Интенсивный):**\nСледуйте этим шагам для наилучшего результата:",
        "en": "🗺 **Your Daily Plan (Deep Focus):**\nFollow these steps for best results:",
    },
    "roadmap_title_steady": {
        "hy": "🗺 **Քո օրվա պլանը (Հանգիստ):**\nՀետևիր այս քայլերին լավագույն արդյունքի համար:",
        "ru": "🗺 **Ваш план на день (Обычный):**\nСледуйте этим шагам для наилучшего результата:",
        "en": "🗺 **Your Daily Plan (Steady Learner):**\nFollow these steps for best results:",
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
