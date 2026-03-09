# Project Structure

## Overview
Այս նախագիծը Telegram բոտ է (`aiogram`), որը օգնում է անգլերեն բառեր սովորել մակարդակներով (A1-B2), պահում է առաջընթացը SQLite-ում և ցուցադրում է բառի թարգմանություն/սահմանում/արտասանություն։ Բացի ուսուցման հոսքից, ավելացված է admin dashboard, broadcast, leaderboard և moderation (ban/unban) համակարգ։

## Main Files
- `bot.py`
  - Բոտի մուտքի կետը։
  - Գրանցում է բոլոր message/callback handler-ները։
  - Կապում է UI, text formatting, DB և API layer-ները։

- `database.py`
  - SQLite շերտ (`aiosqlite`)։
  - Users, word_progress, sessions աղյուսակներ։
  - Users աղյուսակում կան նաև moderation դաշտեր՝ `banned`, `ban_reason`։
  - Users աղյուսակում կան նաև placement դաշտեր՝ `placement_done`, `placement_score`, `placement_taken_at`։
  - `word_progress` աղյուսակում ավելացված է SRS v1 state՝ `ease_factor`, `interval_days`, `repetitions`, `last_reviewed_at`։
  - `story_history` աղյուսակում պահվում են contextual պատմությունները (`genre`, `words_json`, `story_text`, `story_date`)։
  - `memory_palace_history` աղյուսակում պահվում են textual memory palace պատասխանները (`theme`, `words_json`, `palace_text`, `palace_date`)։
  - Առաջընթաց, daily limit, streak, user level, հաջորդ բառի ընտրություն։
  - Admin query-ներ՝ users list, leaderboard, broadcast recipients, ban/unban lookup։

- `api_words.py`
  - Բառի արտաքին տվյալներ։
  - Dictionary API-ից բերում է transcription/definition/example/audio URL։
  - Google Translate API-ից բերում է հայերեն թարգմանություն (բառ + example sentence), fallback՝ Gemini։
  - Gemini-ով ստեղծում է contextual stories (`generate_contextual_story`)՝ օրվա բառերով և ընտրված ժանրով։
  - Gemini-ով ստեղծում է textual memory palace (`generate_memory_palace_text`)՝ տեսողական route-ով։
  - Ունի in-memory cache (`get_word_data`)՝ կրկնվող API կանչերը նվազեցնելու համար։

## Supporting Modules
- `ui.py`
  - Inline keyboard-ների ֆունկցիաներ։
  - Օրինակ՝ word action buttons (`Again/Hard/Good/Easy`), level lock map (`🔓/🔒`), search button, admin dashboard keyboard, placement keyboard։

- `texts.py`
  - Message formatting helper-ներ։
  - Start text, word card text, search result text, date formatting։

- `level_words.py`
  - `common_words_700.txt` parser/cache։
  - Oxford-format տողից headword extraction։
  - Level mapping (`A1..C2`), chunking երկար տեքստերի համար։

- `app_state.py`
  - Runtime in-memory state։
  - Callback dedup (`processed_callbacks`)։
  - Per-user locks։
  - Search flow state (`search_waiting_users`)։
  - Sessions for test/review/placement (`test_sessions`, `review_sessions`, `placement_sessions`)։

- `placement_questions.py`
  - CEFR-aligned placement հարցերի բանկ (`A1..B2`)։
  - Օգտագործվում է մեկնարկային մակարդակի որոշման համար։

- `config.py`
  - Secret/config values (`TOKEN`, API keys)։

- `common_words_700.txt`
  - Բառերի աղբյուրը՝ մակարդակներով։

## Tests
- `tests/test_bot_and_database.py`
  - Parser-ի և DB word selection logic-ի հիմնական unit tests։
  - Ստուգում է headword extraction, level loading, due/hard առաջնահերթություն, unseen բառերի ընտրություն։
  - Ներառում է admin helper-ներ, users/leaderboard query-ներ, username update logic, ban/unban և username lookup test-եր։
  - Ներառում է SRS progression/failure test-եր (`interval_days`, `repetitions`, `ease_factor`)։

## Current Command Set
- `/start`
- `/word`
- `/stats`
- `/review`
- `/learned`
- `/search`
- `/example`
- `/story`
- `/story_history [limit]`
- `/palace`
- `/palace_history [limit]`
- `/placement`
- `/levels`
- `/coach`
- `/test`
- `/all_words`
- `/all_words_A1`, `/all_words_A2`, `/all_words_B1`, `/all_words_B2`, `/all_words_C1`, `/all_words_C2`
- `/reset`
- `/reset_all`
- `/admin`
- `/users [limit]`
- `/broadcast <text>` կամ reply + `/broadcast` (rich mode)
- `/top [limit]`
- `/ban <user_id|@username> [reason]`
- `/unban <user_id|@username>`

## Admin Features
- `/admin` բացում է admin dashboard-ը inline կոճակներով (`Overview`, `Users`, `Top`, `Broadcast Help`, `Refresh`)։
- `/users` ցուցակում յուրաքանչյուր օգտատերի համար ցույց է տալիս՝ `id`, `username`, `level`, `streak`, active status և ban status։
- Active status-ը նշվում է emoji-ով։
  - `🟢`՝ վերջին ակտիվությունը եղել է վերջին 5 րոպեում
  - `🔴`՝ վերջին ակտիվությունը հին է (պասիվ)
- Ban status-ը նույնպես ցուցադրվում է (`✅` կամ `🚫`) և, եթե կա, նաև ban reason-ը։
- `/broadcast` ունի 2 ռեժիմ։
  - Text mode՝ `/broadcast Ձեր տեքստը`
  - Rich mode՝ reply to message + `/broadcast` (copy_message՝ media/text պահպանելով)
- `/top` ցույց է տալիս leaderboard ըստ learned count, հետո correct answers, հետո streak։

## Moderation (Ban System)
- DB schema-ում ավելացված է `users.banned` (`0/1`) և `users.ban_reason` (`TEXT`)։
- Ban check արվում է message/callback հոսքերի սկզբում։
  - Եթե user-ը ban է, ստանում է `❌ You are blocked from using this bot.`
- Admin command-ներ moderation-ի համար։
  - `/ban <user_id|@username> [reason]`
  - `/unban <user_id|@username>`
- Admin-ին ban անել չի թույլատրվում (պաշտպանական կանոն)։

## SRS v1
- Բազային spaced repetition ավելացված է `record_answer()` logic-ում։
- Հիմնական state.
  - `ease_factor` (սկսում է `2.5`-ից, թուլանում է սխալի դեպքում)
  - `interval_days` (հաջորդ review-ի օրերի քանակ)
  - `repetitions` (հաջող հիշողության շարունակական փուլեր)
  - `last_reviewed_at` (վերջին review timestamp)
- Outcome mapping.
  - `Again` → interval reset (1 օր), repetitions reset
  - `Hard` → կարճ interval, փոքր ease penalty
  - `Good` → interval աճ ease_factor-ով
  - `Easy` → ավելի երկար interval, ավելի լավ ease աճ
- Word card UI-ում օգտագործվում են grading կոճակներ՝ `❌ Again`, `🟠 Hard`, `✅ Good`, `🚀 Easy`։
- `review`, `learned`, և `all_words_*` ցուցակներում յուրաքանչյուր բառի կողքին ցույց է տրվում վերջին grading tag-ը։
- `get_next_word()`-ում due selection-ը հաշվի է առնում նաև learned (ոչ միայն ոչ-learned) due բառերը, որպեսզի իրական repetition լինի։

## Placement + Level Lock
- `/start`-ից հետո user-ին առաջարկվում է CEFR-aligned placement test (`A1..B2`)։
- Test-ի արդյունքով ավտոմատ ֆիքսվում է մեկնարկային մակարդակը (`user_level`)։
- Մինչ placement test-ը չի անցել, `/word` չի սկսում ուսուցումը։
- Բաց է միայն ընթացիկ մակարդակը, մնացած մակարդակները lock են։
- Երբ user-ը տվյալ մակարդակի բառերը ամբողջությամբ սովորում է (և accuracy threshold-ը անցնում է), ավտոմատ բացվում է հաջորդ մակարդակը։
- `/levels` հրամանը ցույց է տալիս level map-ը (`🔓` բաց, `🔒` փակ)։

## Typical Flow
1. User-ը սեղմում է `/word`
2. Ընտրում է level (`A1..B2`)
3. Բոտը DB-ից որոշում է next word-ը ընտրված pool-ից
4. API layer-ը բերում է word data
5. User-ը կատարում է SRS action (`again`, `hard`, `good`, `easy`, `next`, `pronounce`)
6. DB-ը թարմացնում է progress-ը, բոտը ցույց է տալիս հաջորդ բառը

## Reset Policy
- `/reset` → soft reset (չի ջնջում learned/seen/history բառերը)
  - զրոյացնում է streak/daily counters-ը, բայց պահում է vocabulary պատմությունը
- `/reset_all` → hard reset
  - ջնջում է ամբողջ history-ն (`word_progress`, `sessions`)

## Personal Coach (MVP)
- `🧠 Coach` բացատրություն բառի քարտում (`ինչու է այս բառը հիմա ցույց տրվում`)
- `/coach` հրաման
  - ցույց է տալիս user-ի ընթացիկ մակարդակը
  - today progress / daily limit
  - overall accuracy + վերջին 20 պատասխանի accuracy
  - accuracy trend (վերջին 20 vs նախորդ 20)
  - due/hard վիճակ և top weak words
  - focus words (weak + hard բառերից)
  - այսօրվա կոնկրետ action plan (քայլերով)
  - inline actions (մեկ սեղմումով)
    - `🔁 Start Review`
    - `📚 Start New Words`
    - `🎯 Focus Word`

## Mixed Test
- `/test` հրամանը կազմում է 5-հարցանոց խառը թեստ user-ի արդեն անցած (`seen`) բառերից
- Յուրաքանչյուր հարցում տրվում է հայերեն թարգմանություն, և պետք է ընտրել ճիշտ անգլերեն բառը

## Contextual Stories
- `/story` հրամանը առաջարկում է ժանր (Cyberpunk / Detective / Fantasy / Comedy / Real-life)։
- Բոտը վերցնում է user-ի այսօրվա անցած բառերը (մինչև 10) և Gemini-ով գեներացնում է կարճ պատմություն՝ ըստ user-ի մակարդակի։
- Պատմության մեջ target բառերը նշվում են տեսանելի ձևով (`⟦word⟧`)։
- Daily limit-ը փակելուց հետո բոտը նաև ավտոմատ առաջարկում է Story Mode։
- Գեներացված պատմությունները պահվում են `story_history` աղյուսակում։
- Glossary-ն գեներացվում է բոտի թարգմանության շերտից (`get_word_data`), ոչ թե ազատ AI թարգմանությամբ։
- Daily rate-limit կա (`DAILY_STORY_LIMIT`), և `/story_history`-ով կարելի է տեսնել վերջին պատմությունները։

## Personal Memory Palace (v1, textual)
- `/palace` հրամանը առաջարկում է թեմա (Ancient Room / Cyber Loft / Detective Office / Fantasy Tower / Cozy Home)։
- Բոտը վերցնում է այսօրվա target բառերը (մինչև 10) և Gemini-ով ստեղծում է տեսողական հիշողության «սենյակի route»։
- Target բառերը ընդգծվում են `⟦word⟧` ձևաչափով։
- Memory Palace output-ը պահվում է `memory_palace_history` աղյուսակում։
- Daily rate-limit կա (`DAILY_PALACE_LIMIT`), և `/palace_history`-ով կարելի է տեսնել վերջին palace-ները։

## Maintenance Notes
- Եթե փոխում եք բառերի source file-ը, parser-ը աշխատում է headword extraction-ով (Oxford-style տողերից)։
- Եթե project-ը մեծանա, հաջորդ քայլը handler-ները առանձին մոդուլների բաժանելն է (`handlers/` փաթեթ)։
