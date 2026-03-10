# Project Structure (Updated Clean Architecture)

## Overview
Այս նախագիծը վերակազմավորվել է «Clean Architecture» սկզբունքով։ Հիմնական կոդը տեղափոխվել է `src/` թղթապանակ, իսկ ֆայլերը բաժանվել են ըստ իրենց պատասխանատվության ոլորտների (Core, Bot, Database, Data, Utils)։

## 📂 Directory Structure

### `src/`
Ծրագրի հիմնական աղբյուրը։
- `main.py` (նախկին `bot.py`)
  - Բոտի մուտքի կետը։ Ինիցիալիզացնում է Dispatcher-ը և գրանցում բոլոր router-ները։

### `src/core/`
Համակարգի հիմնական կարգավորումներն ու վիճակը։
- `config.py`: Կարգավորումների և `.env` ֆայլի բեռնում։
- `app_state.py`: Runtime in-memory պահոց (sessions, locks, waiting users)։
- `texts.py`: Տեքստային template-ներ և ձևաչափում (Formatting)։

### `src/bot/`
Բոտի տրամաբանությունը և ինտերֆեյսը։
- `ui.py`: Բոլոր Inline և Reply ստեղնաշարերի (Keyboards) կենտրոնացված կառավարում։ Ներառում է **Persistent Main Menu**։
- `handlers/` (Package):
  - `general.py`: Հիմնական հրամաններ (`/start`, `/stats`, `/coach`, `/roadmap`, `/plan`) և մենյուի կոճակների մշակում։
  - `study.py`: Ուսուցման հիմնական հոսքը (`/word`, `/test`, `/review`, `/learned`), **Pomodoro Timer** և **Interactive Practice (AI Task)**։
  - `placement.py`: Մակարդակի որոշման թեստի տրամաբանությունը։
  - `features.py`: AI հնարավորություններ (`/story`, `/palace`, `/search`, `/explain`)։
  - `admin.py`: Ադմինիստրատորի վահանակ և օգտատերերի մանրամասն վիճակագրություն։

### `src/database/`
Տվյալների պահպանում։
- `models.py` (նախկին `database.py`): PostgreSQL/asyncpg շերտ, աղյուսակների սխեմաներ և CRUD գործողություններ։ Ներառում է ավտոմատ սյունակների միգրացիա։
- `engine.py`: Տվյալների բազայի միացման կարգավորումներ։

### `src/data/`
Ստատիկ տվյալներ և բառերի ցանկեր։
- `common_words.txt`: 3000+ բառերի Oxford ցանկ։
- `level_words.py`: Բառերի բեռնում և մակարդակավորում։
- `api_words.py`: Արտաքին API-ների հետ կապ (Dictionary, Gemini, Google Translate)։
- `placement_questions.py`: Placement թեստի հարցաշար։

### `src/utils/`
Օժանդակ գործիքներ։
- `utils.py`: Ընդհանուր օգտագործման ֆունկցիաներ (safe edit, validation)։
- `bot_helpers.py`: Բոտին սպեցիֆիկ helper-ներ (word card generation, review flow)։

---

## ✨ Նոր և Թարմացված Ֆունկցիաներ

### 1. Daily Roadmap (`/roadmap`)
Օգտատիրոջ համար ստեղծվում է անհատականացված օրվա անելիքների ցանկ (Steps)։ Այն ցույց է տալիս կատարված և մնացած առաջադրանքները ✅/⏳ նշաններով։

### 2. Study Plans (`/plan`)
Օգտատերը կարող է ընտրել երկու ուսումնական ճանապարհից մեկը․
- **Steady Learner**: Օրական 5 բառ, թեթև ծանրաբեռնվածություն։
- **Deep Focus**: Օրական 10 բառ, Pomodoro, AI Practice։

### 3. Interactive AI Practice
Բառի քարտի վրա ավելացվել է «🧠 Կիրառել» կոճակը։ Օգտատերը գրում է նախադասություն, իսկ Gemini AI-ը վերլուծում է քերականությունն ու բնական լինելը։

### 4. Pomodoro Timer (`/pomodoro`)
25 րոպեանոց ֆոկուս սեսիաներ՝ մնացած ժամանակի իրական (refreshable) ցուցադրմամբ։ Ինտեգրված է հիմնական մենյուի մեջ։

### 5. AI Coach (`/coach`)
Մարզիչը այժմ օգտագործում է Gemini՝ օգտատիրոջ ուսումնական տվյալները վերլուծելու և հայերենով անհատականացված խորհուրդներ ու մոտիվացիա տալու համար։

### 6. Հզորացված Dashboard (`/stats`)
Վիճակագրությունը դարձել է տեսողական (Progress bars) և ավելի տեղեկատվական։

### 7. Ադմինիստրատիվ թարմացումներ
Ադմինը կարող է տեսնել յուրաքանչյուր օգտատիրոջ օրական ծախսած ժամանակը (րոպեներով) և այսօրվա սովորած բառերի քանակը։

---

## 🛠 Maintenance & Deployment
- **Docker**: Թարմացվել է `Dockerfile`-ը՝ նոր `src/main.py` entrypoint-ով և `PYTHONPATH` կարգավորմամբ։
- **Migrations**: Բազան ավտոմատ թարմացնում է իր սխեման (օրինակ՝ `study_plan` սյունակի ավելացում) առանց տվյալների կորստի։
- **Environment**: `.env` ֆայլը փնտրվում է մի քանի վայրերում (root, src) ավելի ճկուն լինելու համար։
