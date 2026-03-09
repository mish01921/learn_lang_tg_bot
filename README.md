# 🇬🇧 English Word Learning Telegram Bot

Այս նախագիծը **Telegram բոտ** է, որը օգնում է օգտատերերին սովորել անգլերենի ամենաշատ օգտագործվող բառերը (A1-ից C2 մակարդակներ)՝ օգտագործելով **Spaced Repetition System (SRS)** և **Artificial Intelligence (Google Gemini)**:

Բոտը պահում է օգտատիրոջ առաջընթացը, տրամադրում է վիճակագրություն, առաջարկում է կոնտեքստային պատմություններ և ունի հզոր ադմինիստրատիվ վահանակ։

## ✨ Հիմնական հնարավորություններ

- **📚 Բառապաշար:** 3000+ ամենահաճախ օգտագործվող բառեր (Oxford list)՝ բաժանված ըստ CEFR մակարդակների (A1, A2, B1, B2, C1, C2):
- **🧠 Smart Learning (SRS):** Բառերի կրկնության խելացի համակարգ (Again, Hard, Good, Easy), որը հաշվարկում է հաջորդ կրկնության օրը։
- **🤖 AI Integration (Gemini):**
  - **Contextual Stories:** Ստեղծում է կարճ պատմություններ՝ օգտագործելով օրվա սովորած բառերը։
  - **Memory Palace:** Ստեղծում է մնեմոնիկ տեխնիկայով տեքստեր՝ բառերը հիշելու համար։
  - **Translations & Examples:** Ճշգրիտ թարգմանություններ և օրինակներ։
- **📊 Վիճակագրություն:** Leaderboard, Daily Streak, սովորած բառերի քանակ և ճշգրտություն։
- **🛡️ Admin Panel:** Օգտատերերի կառավարում, Broadcast (զանգվածային նամակներ), Ban/Unban համակարգ, առողջության ստուգում (Health check):
- **🔐 Level System:** Մակարդակների ավտոմատ բացում (Unlock)՝ հիմնված առաջընթացի վրա, կամ Placement Test-ի միջոցով։

## 🛠️ Տեխնոլոգիաներ

- **Python 3.9+**
- **Aiogram 3.x** (Asynchronous Telegram Bot Framework)
- **PostgreSQL** (Տվյալների բազա)
- **Google Gemini API** (AI գեներացիաների համար)
- **Dictionary API** (Արտասանության և սահմանումների համար)

## 🚀 Տեղադրում և գործարկում

### 1. Clone արեք ռեպոզիտորիան

```bash
git clone https://github.com/yourusername/english-bot.git
cd english-bot
```

### 2. Ստեղծեք վիրտուալ միջավայր (Virtual Environment)

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Տեղադրեք անհրաժեշտ գրադարանները

```bash
pip install -r requirements.txt
```

### 4. Կարգավորեք Environment փոփոխականները

Ստեղծեք `.env` ֆայլ ծրագրի արմատում և լրացրեք հետևյալ տվյալները.

```env
BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_google_gemini_api_key
ADMIN_USER_IDS=123456789,987654321
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
```

### 5. Գործարկեք բոտը

```bash
python bot.py
```

## 📖 Օգտագործման ուղեցույց

### Հիմնական հրամաններ

| Հրաման | Նկարագրություն |
| :--- | :--- |
| `/start` | Սկսել բոտը, տեսնել մենյուն |
| `/word` | Ստանալ նոր բառ կամ կրկնել հինը |
| `/review` | Տեսնել կրկնության ենթակա բառերը (Flashcards) |
| `/learned` | Տեսնել արդեն սովորած բառերի ցանկը |
| `/stats` | Ձեր անձնական վիճակագրությունը |
| `/coach` | AI մարզիչ՝ խորհուրդներ և օրվա պլան |
| `/search <word>` | Փնտրել բառ բառարանում |

### AI Features

| Հրաման | Նկարագրություն |
| :--- | :--- |
| `/story` | Գեներացնել պատմություն օրվա բառերով |
| `/palace` | Ստեղծել Memory Palace (հիշողության սենյակ) |
| `/example <word>` | Ստանալ AI օրինակներ բառի համար |

### Admin Commands (միայն ադմինների համար)

| Հրաման | Նկարագրություն |
| :--- | :--- |
| `/admin` | Բացել ադմին վահանակը |
| `/users` | Տեսնել օգտատերերի ցանկը |
| `/broadcast` | Ուղարկել հաղորդագրություն բոլորին |
| `/ban <id>` | Արգելափակել օգտատիրոջը |
| `/health` | Ստուգել բազայի և բոտի կարգավիճակը |

## 📂 Նախագծի կառուցվածքը

```text
📂 english-bot/
├── 📄 bot.py             # Entry point (Main file)
├── 📄 database.py        # Database logic (SQLite/Postgres)
├── 📄 api_words.py       # External APIs (Gemini, Dictionary)
├── 📄 study.py           # Learning logic (Test, Review)
├── 📄 features.py        # AI features (Story, Palace, Search)
├── 📄 admin.py           # Admin panel handlers
├── 📄 ui.py              # Keyboards & Inline buttons
├── 📄 texts.py           # Text formatting helpers
├── 📄 config.py          # Configuration loader
└── 📄 requirements.txt   # Dependencies
```

## 🤝 Contributing

Pull request-ները ողջունելի են։ Խոշոր փոփոխությունների համար խնդրում ենք նախապես բացել issue՝ քննարկման համար։

---
Made with ❤️ for English Learners.