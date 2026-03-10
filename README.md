# 🇬🇧 English Word Learning Telegram Bot

Այս նախագիծը **Telegram բոտ** է, որը օգնում է օգտատերերին սովորել անգլերենի ամենաշատ օգտագործվող բառերը (A1-ից B2 մակարդակներ)՝ օգտագործելով **Spaced Repetition System (SRS)** և **Artificial Intelligence (Google Gemini)**:

Բոտը վերակազմավորվել է «Clean Architecture» սկզբունքով և ունի հզորացված ուսումնական ծրագիր։

## ✨ Հիմնական հնարավորություններ

- **🗺 Daily Roadmap:** Անհատականացված օրվա անելիքների ցանկ (Review, New Words, AI Tasks)։
- **🎓 Study Plans:** Ընտրեք ձեր ուսումնական տեմպը՝ **Steady Learner** կամ **Deep Focus**։
- **🧠 Smart Learning (SRS):** Բառերի կրկնության խելացի համակարգ (Again, Hard, Good, Easy), որը հաշվարկում է հաջորդ կրկնության օրը։
- **🤖 AI Integration (Gemini):**
  - **Interactive Practice:** Կազմեք նախադասություններ նոր բառերով, ստացեք AI վերլուծություն։
  - **AI Coach:** Ձեր առաջընթացի անհատական վերլուծություն և մոտիվացիա։
  - **Contextual Stories:** Կարճ պատմություններ օրվա բառերով։
  - **Memory Palace:** Մնեմոնիկ տեխնիկաներ բառերը հիշելու համար։
- **⏱ Pomodoro Timer:** 25 րոպեանոց կենտրոնացված աշխատանքի սեսիաներ։
- **📊 Dashboard:** Տեսողական վիճակագրություն (Progress bars), Streak և Accuracy։
- **🛡️ Admin Panel:** Օգտատերերի կառավարում, Daily activity tracking (time spent), Broadcast և Moderation։

## 🛠️ Տեխնոլոգիաներ

- **Python 3.11+**
- **Aiogram 3.x** (Asynchronous Telegram Bot Framework)
- **PostgreSQL** (Տվյալների բազա)
- **Google Gemini API** (AI գեներացիաների համար)
- **Docker & Docker Compose** (Հեշտ տեղադրման համար)

## 🚀 Տեղադրում և գործարկում (Docker)

### 1. Կարգավորեք Environment փոփոխականները

Ստեղծեք `.env` ֆայլ ծրագրի արմատում․

```env
BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_google_gemini_api_key
ADMIN_USER_IDS=123456789
DATABASE_URL=postgresql+asyncpg://bot_user:bot_password@db/english_bot_db
```

### 2. Գործարկեք Docker-ը

```bash
docker-compose up --build -d
```

## 📖 Օգտագործման ուղեցույց

### Հիմնական հրամաններ

| Հրաման | Նկարագրություն |
| :--- | :--- |
| `/start` | Սկսել բոտը, տեսնել հիմնական մենյուն |
| `/roadmap` | Ձեր օրվա անելիքների ցանկը (Գլխավոր էջ) |
| `/plan` | Ուսումնական պլանի ընտրություն |
| `/word` | Ստանալ նոր բառ |
| `/review` | Կրկնության ենթակա բառերը (Flashcards) |
| `/pomodoro` | Սկսել 25 րոպեանոց ֆոկուս սեսիա |
| `/coach` | AI մարզիչի վերլուծություն |
| `/stats` | Ձեր Dashboard-ը |

## 📂 Նախագծի կառուցվածքը

```text
📂 src/
├── 📂 bot/           # Handlers & UI logic
├── 📂 core/          # Config, Texts, State
├── 📂 database/      # PostgreSQL Models & Engine
├── 📂 data/          # Static data (Words, Questions)
└── 📂 utils/         # Helper functions
```

---
Made with ❤️ for English Learners.
