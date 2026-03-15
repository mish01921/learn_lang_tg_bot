from datetime import datetime


def format_word(word_data: dict, current: int, total: int, level: str, coach_hint: str = "") -> str:
    example = word_data.get("example", "—") or "—"
    example_tr = word_data.get("example_translation", "—") or "—"
    audio_url = word_data.get("audio_url", "") or ""
    audio_line = f"🔊 Pronunciation audio: {audio_url}\n" if audio_url else ""
    base = (
        f"🏷️ Level: {level}\n"
        f"📖 Word: {word_data['word']}   [{current}/{total}]\n"
        f"🧠 Coach: {coach_hint or 'Պլանային առաջընթաց'}\n"
        f"🔊 Transcription: {word_data['transcription']}\n"
        f"{audio_line}"
        f"🇦🇲 Translation: {word_data['translation']}\n"
        f"📝 Definition: {word_data['definition']}"
    )
    if example != "—" or example_tr != "—":
        base += f"\n💬 Example: {example}\n" f"🇦🇲 Թարգմանություն: {example_tr}"
    return base


def format_searched_word(word_data: dict, levels: list[str]) -> str:
    level_text = ", ".join(levels) if levels else "Չի գտնվել level ցուցակներում"
    example = word_data.get("example", "—") or "—"
    example_tr = word_data.get("example_translation", "—") or "—"
    audio_url = word_data.get("audio_url", "") or ""
    audio_line = f"🔊 Արտասանության հղում: {audio_url}\n" if audio_url else ""
    base = (
        f"🔎 Որոնման արդյունք\n"
        f"🏷️ Level: {level_text}\n"
        f"📖 Word: {word_data['word']}\n"
        f"🔊 Transcription: {word_data['transcription']}\n"
        f"{audio_line}"
        f"🇦🇲 Translation: {word_data['translation']}\n"
        f"📝 Definition: {word_data['definition']}"
    )
    if example != "—" or example_tr != "—":
        base += f"\n💬 Example: {example}\n" f"🇦🇲 Թարգմանություն: {example_tr}"
    return base


def format_date(iso_str: str) -> str:
    try:
        return datetime.fromisoformat(iso_str).strftime("%d.%m.%Y")
    except Exception:
        return ""


BOT_DESCRIPTION = (
    "🚀 Պատրա՞ստ ես փոխել կյանքդ՝ սովորելով անգլերեն։\n\n"
    "Այս բոտը քո անձնական AI մարզիչն է, որը կօգնի քեզ տիրապետել Oxford-ի 3000 ամենակարևոր բառերին։\n\n"
    "✨ Ինչո՞ւ ընտրել մեզ.\n"
    "🔹 Spaced Repetition (SRS) — հիշիր բառերը ընդմիշտ, ոչ թե մեկ օրով։\n"
    "🔹 AI Tutor (Gemini) — ստացիր խորացված բացատրություններ և օրինակներ։\n"
    "🔹 Contextual Stories — սովորիր բառերը հետաքրքիր պատմությունների միջոցով։\n"
    "🔹 Placement Test — սկսիր հենց քո մակարդակից (A1-B2)։\n\n"
    "💡 Հիշիր՝ ամեն մեծ ճանապարհ սկսվում է մեկ բառից։ Սկսիր հենց հիմա։ 👇"
)

BOT_SHORT_DESCRIPTION = "Սովորիր անգլերեն Oxford-ի բառերով և AI մարզիչի օգնությամբ։ 🚀"


def build_start_text(name: str, total_words: int, daily_limit: int, is_admin: bool = False) -> str:
    daily_line = f"🗓 Ամեն օր {daily_limit} նոր բառ"
    if is_admin:
        daily_line += " (ադմին՝ անսահմանափակ)"
    text = (
        f"Բարև, {name} 👋\n\n"
        f"Ես անգլերեն բառերի բոտ եմ 📚\n"
        f"Կօգնեմ սովորել անգլերենի {total_words} ամենաօգտագործվող բառերը։\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{daily_line}\n"
        f"❌ «Again» — կարճ interval-ով կկրկնվի\n"
        f"🟠 «Hard» — բարդ է, բայց ճիշտ էր\n"
        f"✅ «Good» — նորմալ հիշեցիր\n"
        f"🚀 «Easy» — հեշտ էր, interval-ը մեծանում է\n"
        f"⏭️ «Հաջորդ բառը» — պարզապես անցնել, չի հաշվվում\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"📌 Հրամաններ՝\n"
        f"/word — նոր բառ\n"
        f"/stats — վիճակագրություն\n"
        f"/review — սովորելու բառեր 📘\n"
        f"/learned — սովորած բառեր ✅\n"
        f"/coach — անձնական մարզչի խորհուրդներ 🧠\n"
        f"/test — խառը թեստ անցած բառերով 🧪\n"
        f"/search — փնտրել կոնկրետ բառ 🔎\n"
        f"/example — AI example նախադասություններ 🧠\n"
        f"/explain — AI խորացված բացատրիչ (Tutor Mode) 🧐\n"
        f"/story — contextual պատմություն օրվա բառերով 📖\n"
        f"/story_tr — story glossary custom թարգմանություններ 📘\n"
        f"/story_history [limit] — վերջին պատմությունները 📚\n"
        f"/palace — textual memory palace 🧠\n"
        f"/palace_history [limit] — վերջին memory palace-ները 🧠📚\n"
        f"/placement — մակարդակի test 📝\n"
        f"/levels — բաց/փակ մակարդակներ 🔐\n"
        f"/all_words — ամբողջ բառերի ցանկը ըստ մակարդակի (A1–B2) 📚\n"
        f"/reset — զրոյացնել առաջընթացը ⚠️\n\n"
        f"Պատրա՞ստ ես սկսել։ Սեղմիր /word 👇"
    )
    if is_admin:
        text += (
            "\n/admin — ադմին վահանակ 🛠"
            "\n/health — բոտ/DB առողջության ստուգում 🩺"
            "\n/users — բոլոր user-ների ցուցակ 👥"
            "\n/broadcast — զանգվածային հաղորդագրություն 📣"
            "\n/top — leaderboard 🏆"
            "\n/ban — արգելափակել user 🚫"
            "\n/unban — ապաշրջափակել user ✅"
        )
    return text


def build_coach_text(
    level: str,
    today_count: int,
    daily_limit: int,
    overall_accuracy: int,
    recent_accuracy: int,
    trend_text: str,
    due_today: int,
    hard_count: int,
    weak_words: list[dict],
    focus_words: list[str],
    plan_steps: list[str],
) -> str:
    if weak_words:
        weak_text = "\n".join(
            f"- {w['word']} (սխալ՝ {w.get('wrong', 0)}, ճիշտ՝ {w.get('correct', 0)})"
            for w in weak_words
        )
    else:
        weak_text = "- Թուլացած բառեր չկան, լավ առաջընթաց ունեք։"

    if focus_words:
        focus_text = ", ".join(focus_words)
    else:
        focus_text = "Առայժմ հատուկ focus բառեր չկան։"

    if plan_steps:
        plan_text = "\n".join(f"{i}. {step}" for i, step in enumerate(plan_steps, 1))
    else:
        plan_text = "1. Շարունակեք /word"

    return (
        "🧠 Ձեր անձնական մարզիչը\n\n"
        f"🏷️ Մակարդակ: {level}\n"
        f"📅 Այսօր: {today_count}/{daily_limit}\n"
        f"🎯 Ընդհանուր ճշտություն: {overall_accuracy}%\n"
        f"⚡ Վերջին 20 փորձի ճշտություն: {recent_accuracy}%\n"
        f"📈 Թրենդ: {trend_text}\n"
        f"⏰ Due կրկնություններ: {due_today}\n"
        f"🔁 Hard բառեր: {hard_count}\n\n"
        "Թուլացած բառեր.\n"
        f"{weak_text}\n\n"
        f"🎯 Focus words: {focus_text}\n\n"
        "Այսօրվա պլան.\n"
        f"{plan_text}"
    )


HELP_TEXT = """
❓ <b>Ինչպե՞ս օգտվել բոտից:</b>

Ահա հիմնական հրամանները և դրանց օգտագործման <b>օրինակները</b>.

📖 <b>Ուսումնական հրամաններ:</b>
• /word — Ստանալ նոր բառ:
• /review — Կրկնել անցած բառերը (Flashcards):
• /test — Ստուգել գիտելիքները թեստի միջոցով:
• /learned — Տեսնել ձեր բոլոր սովորած բառերը:

🤖 <b>AI Հնարավորություններ:</b>
• /coach — AI մարզիչի վերլուծություն և խորհուրդներ:
• /story — Ստեղծել պատմություն ձեր սովորած բառերով:
• /palace — Ստեղծել «Հիշողության պալատ» (Memory Palace):

📘 <b>Custom Թարգմանություններ (Glossary):</b>
• /story_tr — Սահմանել բառի թարգմանությունը AI-ի համար:
  <i>Օրինակ:</i> <code>/story_tr book=ամրագրել</code>
  <i>Օրինակ:</i> <code>/story_tr fire=ազատել աշխատանքից</code>

🎙️ <b>Արտասանության ստուգում:</b>
Յուրաքանչյուր բառի տակ սեղմեք <b>🎙️ Test my Voice</b> կոճակը և ուղարկեք Voice:
  <i>Օրինակ:</i> Սեղմում եք կոճակը -> Բոտն ասում է «Արտասանեք hello» -> Ուղարկում եք ձեր ձայնը:

🧠 <b>Ինտերակտիվ Պրակտիկա (Practice):</b>
Բառի քարտի վրա սեղմեք <b>🧠 Կիրառել (Practice)</b> կոճակը և գրեք նախադասություն այդ բառով:
  <i>Օրինակ:</i> <code>I love this book.</code> -> AI-ն կստուգի քերականությունը:

📈 <b>Պլան և Dashboard:</b>
• /roadmap — Տեսնել օրվա անելիքները:
• /stats — Ձեր առաջընթացը և Streak-ը:
• /plan — Փոխել ուսումնական տեմպը (Steady/Deep):

💡 <i>Հուշում: Օգտագործեք /help հրամանը ցանկացած պահի այս ուղեցույցը տեսնելու համար:</i>
"""

