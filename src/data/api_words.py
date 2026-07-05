import asyncio
import logging
import os
import re
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx

from src.core.config import GEMINI_API_KEY

try:
    from src.core.config import GOOGLE_TRANSLATE_API_KEY
except Exception:
    GOOGLE_TRANSLATE_API_KEY = ""

logging.basicConfig(level=logging.INFO)

MISSING_TEXT = "—"

# --- Configuration ---
def _load_gemini_models() -> list[str]:
    raw = (os.getenv("GEMINI_MODELS") or "").strip()
    if raw:
        models = [m.strip() for m in raw.split(",") if m.strip()]
        if models:
            return models
    # Default order: keep only models that work with generateContent for typical API keys.
    return [
        "gemini-flash-lite-latest",
        "gemini-2.5-flash-lite",
        "gemini-flash-latest",
        "gemini-3.5-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]


GEMINI_MODELS = _load_gemini_models()
WORD_CACHE_TTL_HOURS = 24

_example_cache: dict[str, tuple[datetime, list[str]]] = {}
_word_data_cache: dict[str, tuple[datetime, dict]] = {}
_network_blocked_until: Optional[datetime] = None
_http_session: Optional[httpx.AsyncClient] = None
_bad_gemini_models: set[str] = set()

class HTTPClient:
    _client: Optional[httpx.AsyncClient] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get(cls) -> httpx.AsyncClient:
        global _http_session
        if cls._client and not cls._client.is_closed:
            _http_session = cls._client
            return cls._client
        async with cls._lock:
            if cls._client and not cls._client.is_closed:
                _http_session = cls._client
                return cls._client
            cls._client = httpx.AsyncClient(
                timeout=15.0,
                limits=httpx.Limits(max_connections=50, keepalive_expiry=300.0),
            )
            _http_session = cls._client
            return cls._client

    @classmethod
    async def close(cls):
        global _http_session
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None
        _http_session = None

_TRANSLATION_OVERRIDES: dict[str, str] = {
    "desk": "գրասեղան / սեղան",
}

# --- Basic Helpers ---
def _normalize_word(word: str) -> str:
    return (word or "").strip().lower()

def extract_headword(line: str) -> str:
    match = re.match(r"^\s*([A-Za-z][A-Za-z'-]*)(?:\d+)?\b", line)
    return match.group(1).lower() if match else ""

def _parse_examples_text(text: str) -> list[str]:
    lines = (text or "").splitlines()
    out: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^(?:\d+\s*[\.\)]\s*|[-•]\s*)", "", line).strip()
        if line:
            out.append(line)
    return out

def _fallback_examples(word: str) -> list[str]:
    w = _normalize_word(word)
    if not w:
        return ["This is an example."]
    return [
        f"I used the word {w} in a sentence.",
        f"Can you repeat the word {w}?",
        f"Let's practice: {w}.",
    ]

def _get_cached_word_data(word: str) -> dict | None:
    key = _normalize_word(word)
    if not key:
        return None
    record = _word_data_cache.get(key)
    if not record:
        return None
    created_at, payload = record
    if datetime.now() - created_at > timedelta(hours=WORD_CACHE_TTL_HOURS):
        _word_data_cache.pop(key, None)
        return None
    return payload

def _set_cached_word_data(word: str, data: dict) -> None:
    key = _normalize_word(word)
    if not key:
        return
    _word_data_cache[key] = (datetime.now(), dict(data or {}))

def _load_common_words() -> list[str]:
    base = ["time", "year", "people", "way", "day", "man", "thing", "woman", "life", "child", "world", "school", "state", "family", "student", "group", "country", "problem", "hand", "part", "place", "case", "week", "company", "system"]
    path = Path(__file__).parent / "common_words.txt"
    words = []
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    w = extract_headword(line.strip())
                    if w and w.upper() not in {"A1", "A2", "B1", "B2"}:
                        words.append(w)
        except Exception:
            logging.exception("Failed to load common words file")
    seen = set()
    return [x for x in (base + words) if not (x in seen or seen.add(x))]

COMMON_WORDS = _load_common_words()
logging.info(f"COMMON_WORDS loaded: {len(COMMON_WORDS)} items.")

# --- Gemini Core ---
class GeminiClient:
    @classmethod
    async def generate(
        cls,
        prompt: str,
        temp: float = 0.3,
        maxt: int = 512,
        audio_b64: Optional[str] = None,
        audio_mime_type: str = "audio/ogg",
        timeout: float = 15.0
    ) -> Optional[str]:
        if not GEMINI_API_KEY:
            return None

        parts = []
        if audio_b64:
            parts.append({"inlineData": {"mimeType": (audio_mime_type or "audio/ogg"), "data": audio_b64}})
        parts.append({"text": prompt})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": temp, "maxOutputTokens": maxt, "topP": 0.8, "topK": 40}
        }

        session = await HTTPClient.get()
        for _attempt in range(2):  # Add 1 retry on failure
            for model in GEMINI_MODELS:
                if model in _bad_gemini_models:
                    continue
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                try:
                    res = await session.post(url, json=payload, timeout=timeout)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates")
                        if candidates and candidates[0].get("content", {}).get("parts"):
                            full_text = "".join(p.get("text", "") for p in candidates[0]["content"]["parts"] if "text" in p)
                            return full_text.strip()
                    elif res.status_code == 404:
                        _bad_gemini_models.add(model)
                        logging.warning(
                            "Gemini model '%s' not supported for generateContent (404). Skipping it.",
                            model,
                        )
                    elif res.status_code in {429, 500, 503}:
                        logging.warning(f"Gemini {model} overloaded ({res.status_code}). Retrying...")
                        await asyncio.sleep(1)
                    else:
                        logging.warning(f"Gemini {model} error ({res.status_code}): {res.text}")
                except Exception as e:
                    logging.error(f"Gemini {model} exception: {e}")
        return None

# --- Session Management ---
def _network_temporarily_blocked() -> bool:
    return _network_blocked_until is not None and datetime.now() < _network_blocked_until

def _mark_network_blocked(seconds: int = 90):
    global _network_blocked_until
    _network_blocked_until = datetime.now() + timedelta(seconds=seconds)

# --- Public API Methods ---
async def get_translation(session: httpx.AsyncClient, word: str) -> str:
    if _network_temporarily_blocked():
        return MISSING_TEXT
    res = await get_translation_gemini(word)
    if res != MISSING_TEXT:
        return res
    return await _google_translate_text(session, word, "en", "hy")

async def get_translation_gemini(word: str) -> str:
    prompt = (
        f"Translate the English word '{word}' to Armenian. If the word has multiple distinct meanings "
        "(e.g., noun vs verb, or different concepts), list the top 2-3 most common meanings separated by a slash (' / '). "
        "Reply ONLY with the Armenian translation(s), nothing else."
    )
    return await GeminiClient.generate(prompt, temp=0.1, maxt=128, timeout=10.0) or "—"

async def _google_translate_text(session: httpx.AsyncClient, text: str, sl: str, tl: str) -> str:
    if not GOOGLE_TRANSLATE_API_KEY or _network_temporarily_blocked():
        return MISSING_TEXT
    url = "https://translation.googleapis.com/language/translate/v2"
    try:
        res = await session.post(url, params={"key": GOOGLE_TRANSLATE_API_KEY}, json={"q": text, "source": sl, "target": tl, "format": "text"}, timeout=5.0)
        if res.status_code == 200:
            data = res.json()
            return data["data"]["translations"][0]["translatedText"].strip()
    except Exception:
        logging.exception("Google Translate failed")
    return MISSING_TEXT

async def get_sentence_translation(session: httpx.AsyncClient, sentence: str) -> str:
    res = await _google_translate_text(session, sentence, "en", "hy")
    if res != MISSING_TEXT:
        return res
    return await get_sentence_translation_gemini(sentence)

async def get_sentence_translation_gemini(sentence: str) -> str:
    return await GeminiClient.generate(
        f"Translate this English sentence to Armenian. Reply ONLY with the Armenian translation, no intro or markdown: {sentence}",
        temp=0.1,
        maxt=256,
        timeout=10.0,
    ) or MISSING_TEXT

async def _fill_missing_word_fields_gemini(word: str, level: str, transcription: str, definition: str, example: str) -> tuple[str, str, str]:
    if transcription != MISSING_TEXT and definition != MISSING_TEXT and example != MISSING_TEXT:
        return transcription, definition, example

    prompt = f"""For the English word '{word}' (CEFR level {level or 'A1'}), provide simple educational data.
Reply EXACTLY with these 3 lines:
TRANSCRIPTION: /IPA phonetic transcription/
DEFINITION: Simple English definition for an Armenian learner
EXAMPLE: One short English example sentence using '{word}'

Do not add any intro or markdown."""
    text = await GeminiClient.generate(prompt, temp=0.2, maxt=256, timeout=10.0)
    if not text:
        return (
            transcription if transcription != MISSING_TEXT else f"/{word}/",
            definition if definition != MISSING_TEXT else f"Word: {word}",
            example if example != MISSING_TEXT else f"This is {word}.",
        )

    new_tr, new_def, new_ex = transcription, definition, example
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("TRANSCRIPTION:") and new_tr == MISSING_TEXT:
            val = line.split(":", 1)[1].strip()
            if val:
                new_tr = val
        elif line.startswith("DEFINITION:") and new_def == MISSING_TEXT:
            val = line.split(":", 1)[1].strip()
            if val:
                new_def = val
        elif line.startswith("EXAMPLE:") and new_ex == MISSING_TEXT:
            val = line.split(":", 1)[1].strip()
            if val:
                new_ex = val

    if new_tr == MISSING_TEXT:
        new_tr = f"/{word}/"
    if new_def == MISSING_TEXT:
        new_def = f"Word: {word}"
    if new_ex == MISSING_TEXT:
        new_ex = f"This is {word}."

    return new_tr, new_def, new_ex

async def get_word_data(word: str, level: str = "") -> dict:
    normalized = _normalize_word(word)
    cached = _get_cached_word_data(normalized)
    if cached is not None:
        return cached
    session = await HTTPClient.get()
    async with asyncio.TaskGroup() as tg:
        dict_task = tg.create_task(_fetch_dictionary_fields(session, normalized))
        trans_task = tg.create_task(get_translation(session, normalized))

    transcription, definition, example, audio = dict_task.result()
    translation = trans_task.result()

    if transcription == MISSING_TEXT or definition == MISSING_TEXT or example == MISSING_TEXT:
        transcription, definition, example = await _fill_missing_word_fields_gemini(
            normalized, level, transcription, definition, example
        )

    res = {
        "word": normalized, "transcription": transcription, "translation": translation,
        "definition": definition, "example": example,
        "example_translation": await get_sentence_translation(session, example) if example != MISSING_TEXT else MISSING_TEXT,
        "audio_url": audio
    }
    if definition != MISSING_TEXT and example != MISSING_TEXT:
        _set_cached_word_data(normalized, res)
    return res

async def _fetch_dictionary_fields(session: httpx.AsyncClient, word: str) -> tuple:
    try:
        safe_word = urllib.parse.quote(word)
        res = await session.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{safe_word}", timeout=5.0)
        if res.status_code == 200:
            resp_data = res.json()
            if isinstance(resp_data, list) and len(resp_data) > 0:
                data = resp_data[0]
                phonetic = data.get("phonetic", "—")
                meaning = data.get("meanings", [{}])[0] if data.get("meanings") else {}
                definition = meaning.get("definitions", [{}])[0].get("definition", "—") if meaning.get("definitions") else "—"
                example = meaning.get("definitions", [{}])[0].get("example", "—") if meaning.get("definitions") else "—"
                audio = ""
                for p in data.get("phonetics", []):
                    if p.get("audio"):
                        audio = p["audio"]
                        break
                return phonetic, definition, example, audio
    except Exception:
        pass
    return MISSING_TEXT, MISSING_TEXT, MISSING_TEXT, ""

async def generate_contextual_story(words: list[str], genre: str, level: str) -> str:
    words_str = ", ".join(words)
    prompt = f"Write a short {genre} story for a {level} English learner using these words: {words_str}. Wrap every target word in ⟦word⟧."
    return await GeminiClient.generate(prompt, temp=0.7, maxt=1024, timeout=15.0) or "Today I learned new words..."

async def generate_memory_palace_text(words: list[str], theme: str, level: str) -> str:
    words_str = ", ".join(words)
    prompt = f"Create a memory palace story (Theme: {theme}) for a {level} learner using these words: {words_str}. Wrap target words in ⟦word⟧."
    return await GeminiClient.generate(prompt, temp=0.7, maxt=1024, timeout=15.0) or "Imagine a big room..."

async def get_ai_example_sentences(word: str, count: int = 3, level: str = "A2") -> list[str]:
    prompt = f"Provide {count} simple English example sentences for the word '{word}' at {level} level. List only the sentences."
    text = await GeminiClient.generate(prompt, temp=0.3, maxt=256, timeout=10.0)
    if text:
        return [line.strip() for line in text.splitlines() if line.strip()][:count]
    return [f"This is an example with {word}."]

async def get_tutor_explanation_gemini(query: str, level: str = "B1") -> str:
    prompt = (
        f"You are a friendly English Tutor. A {level} student asks about: '{query}'.\n"
        "Explain it clearly using this structure:\n"
        "1. Brief Summary (Armenian)\n2. Detailed English Explanation\n3. Armenian Translation\n4. Two examples."
    )
    return await GeminiClient.generate(prompt, temp=0.3, maxt=1024, timeout=15.0) or "I am sorry, I cannot explain this right now."


async def get_practice_analysis_gemini(word: str, user_sentence: str, level: str = "B1", lang: str = "hy") -> str:
    lang_names = {"hy": "Armenian", "ru": "Russian", "en": "English"}
    target_lang = lang_names.get(lang, "Armenian")
    prompt = f"""You are an expert English teacher for {target_lang} speakers (level: {level}).
The student is practicing the word: "{word}".
They submitted this sentence: "{user_sentence}".

IMPORTANT: Do NOT write long conversational introductions or greetings. Jump DIRECTLY into the 4 structured points below!
Respond in warm, natural {target_lang} (using clean Markdown formatting):

1. **🎯 Score / Evaluation:**
   - Did they use the word "{word}" with the correct meaning and grammar? (Yes / Almost / No).
   - If there are any mistakes, briefly explain *what* was wrong and *why* in simple {target_lang}.

2. **✅ Corrected / Flawless Version:**
   - Give the grammatically flawless version of their exact sentence.
   - If already correct, show how to make it sound even more native or advanced!

3. **💡 Tips & Collocations:**
   - Give 1-2 valuable tips on collocations or prepositions in {target_lang}.

4. **🌟 2 Native Examples:**
   - Provide 2 alternative, real-life English sentences using "{word}" with their {target_lang} translations.

Make your formatting clean, structured, and concise!"""
    fallback = {
        "hy": "⚠️ Չհաջողվեց կապվել AI ուսուցչի հետ։ Խնդրում եմ փորձել մի փոքր ուշ։",
        "ru": "⚠️ Не удалось связаться с AI-учителем. Пожалуйста, попробуйте позже.",
        "en": "⚠️ Unable to reach AI tutor. Please try again later.",
    }
    return await GeminiClient.generate(prompt, temp=0.3, maxt=2048, timeout=20.0) or fallback.get(lang, fallback["hy"])


async def get_coach_analysis_gemini(prompt: str) -> str:
    return await GeminiClient.generate(prompt, temp=0.5, maxt=512, timeout=15.0) or "👨‍🏫 Keep learning at the same pace, everything is going great! 💪"
