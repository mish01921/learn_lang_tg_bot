import aiohttp
from src.core.config import GEMINI_API_KEY
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
try:
    from src.core.config import GOOGLE_TRANSLATE_API_KEY
except Exception:
    GOOGLE_TRANSLATE_API_KEY = ""

logging.basicConfig(level=logging.INFO)

# Այժմ ամբողջ COMMON_WORDS-ի աղբյուրը բեռնվում է ֆայլից
BASE_COMMON_WORDS: list[str] = ["time", "year", "people", "way", "day", "man", "thing", "woman", "life", "child", "world", "school", "state", "family", "student", "group", "country", "problem", "hand", "part", "place", "case", "week", "company", "system"]
WORD_CACHE_TTL_HOURS = 24
WORD_CACHE_MAX_SIZE = 5000
_word_data_cache: dict[str, tuple[datetime, dict]] = {}
_example_cache: dict[str, tuple[datetime, list[str]]] = {}
_http_session: Optional[aiohttp.ClientSession] = None
_http_session_lock = asyncio.Lock()
_network_blocked_until: Optional[datetime] = None

# Prefer more specific Armenian equivalents for ambiguous high-frequency words.
_TRANSLATION_OVERRIDES: dict[str, str] = {
    "desk": "գրասեղան / սեղան",
}


def extract_headword(line: str) -> str:
    """Oxford-format տողի առաջին բառը (օր. 'bank (money) n.' -> 'bank')."""
    match = re.match(r"^\s*([A-Za-z][A-Za-z'-]*)(?:\d+)?\b", line)
    return match.group(1).lower() if match else ""


def _normalize_word(word: str) -> str:
    return (word or "").strip().lower()


def _get_cached_word_data(word: str) -> Optional[dict]:
    key = _normalize_word(word)
    if not key:
        return None
    item = _word_data_cache.get(key)
    if not item:
        return None
    stored_at, data = item
    if datetime.now() - stored_at > timedelta(hours=WORD_CACHE_TTL_HOURS):
        _word_data_cache.pop(key, None)
        return None
    return data


def _set_cached_word_data(word: str, data: dict):
    key = _normalize_word(word)
    if not key:
        return
    _word_data_cache[key] = (datetime.now(), data)
    # Bounded cache: drop oldest inserted entries when max size is exceeded
    while len(_word_data_cache) > WORD_CACHE_MAX_SIZE:
        oldest_key = next(iter(_word_data_cache))
        _word_data_cache.pop(oldest_key, None)


def _get_cached_examples(word: str) -> Optional[list[str]]:
    key = _normalize_word(word)
    if not key:
        return None
    item = _example_cache.get(key)
    if not item:
        return None
    stored_at, data = item
    if datetime.now() - stored_at > timedelta(hours=WORD_CACHE_TTL_HOURS):
        _example_cache.pop(key, None)
        return None
    return data


def _set_cached_examples(word: str, examples: list[str]):
    key = _normalize_word(word)
    if not key:
        return
    _example_cache[key] = (datetime.now(), examples[:3])
    while len(_example_cache) > WORD_CACHE_MAX_SIZE:
        oldest_key = next(iter(_example_cache))
        _example_cache.pop(oldest_key, None)


async def _get_http_session() -> aiohttp.ClientSession:
    global _http_session
    if _http_session and not _http_session.closed:
        return _http_session
    async with _http_session_lock:
        if _http_session and not _http_session.closed:
            return _http_session
        _http_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5),
            connector=aiohttp.TCPConnector(limit=50, ttl_dns_cache=300),
        )
        return _http_session


async def close_http_session():
    global _http_session
    if _http_session and not _http_session.closed:
        await _http_session.close()
    _http_session = None


def _network_temporarily_blocked() -> bool:
    if not _network_blocked_until:
        return False
    return datetime.now() < _network_blocked_until


def _mark_network_blocked(seconds: int = 90):
    global _network_blocked_until
    _network_blocked_until = datetime.now() + timedelta(seconds=seconds)


def _load_words_from_file(path: str) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            words = []
            for line in f:
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                # Անտեսել մակարդակի գլխագրերը, նախաբանները և վերցնել միայն headword-ը
                word = extract_headword(raw)
                if word:
                    words.append(word)
            return words
    except FileNotFoundError:
        logging.info("Common words file not found: %s (using built-in list)", path)
        return []
    except Exception:
        logging.exception("Failed to load common words file: %s", path)
        return []


# Բեռնել լրացուցիչ բառեր ֆայլից
# Տեղադրեք բառերի ցանկը տող առ տող այստեղ՝ common_words.txt
_EXTRA_WORDS_FILE = str(Path(__file__).parent / "common_words.txt")
# Մակարդակային գլխագրերը պետք է անտեսվեն COMMON_WORDS-ի համար
_LEVEL_HEADERS = {"A1", "A2", "B1", "B2"}
_raw_file_words = _load_words_from_file(_EXTRA_WORDS_FILE)
_file_words = [w for w in _raw_file_words if w.upper() not in _LEVEL_HEADERS]

# Միավորում և դեդուպլիկացիա՝ պահելով հերթականությունը
_seen = set()
_combined: list[str] = []
for w in BASE_COMMON_WORDS + _file_words:
    if w not in _seen:
        _seen.add(w)
        _combined.append(w)

# Ամբողջական ցանկը
COMMON_WORDS = _combined
logging.info("COMMON_WORDS loaded: %d items.", len(COMMON_WORDS))




def _get_phonetic(dict_data: list) -> str:
    phonetic = dict_data[0].get("phonetic", "")
    if phonetic:
        return phonetic
    for p in dict_data[0].get("phonetics", []):
        text = p.get("text", "")
        if text:
            return text
    return "—"


def _get_audio_url(dict_data: list) -> str:
    try:
        if not isinstance(dict_data, list) or not dict_data:
            return ""
        for p in dict_data[0].get("phonetics", []):
            audio = (p.get("audio") or "").strip()
            if audio:
                if audio.startswith("//"):
                    return f"https:{audio}"
                return audio
    except Exception:
        logging.exception("Failed to extract audio URL from dictionary data")
    return ""


async def get_translation(session: aiohttp.ClientSession, word: str) -> str:
    if _network_temporarily_blocked():
        return "—"
    if not GOOGLE_TRANSLATE_API_KEY and not GEMINI_API_KEY:
        return "—"
    # Primary: Gemini (richer multi-sense output). Fallback: Google Translate.
    gm = await get_translation_gemini(session, word)
    if gm and gm != "—":
        return _postprocess_translation(word, gm)
    gt = await _google_translate_text(session, word, source_lang="en", target_lang="hy")
    if gt and gt != "—":
        return _postprocess_translation(word, gt)
    return "—"


def _postprocess_translation(word: str, translation: str) -> str:
    normalized_word = _normalize_word(word)
    clean = (translation or "").strip()
    if not clean:
        return "—"
    override = _TRANSLATION_OVERRIDES.get(normalized_word)
    if override:
        return override
    return clean


async def _google_translate_text(
    session: aiohttp.ClientSession,
    text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    if not GOOGLE_TRANSLATE_API_KEY:
        return "—"
    if _network_temporarily_blocked():
        return "—"
    url = "https://translation.googleapis.com/language/translate/v2"
    payload = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text",
        "key": GOOGLE_TRANSLATE_API_KEY,
    }
    timeout = aiohttp.ClientTimeout(total=3)
    for attempt in range(2):
        try:
            async with session.post(url, data=payload, timeout=timeout) as res:
                if res.status != 200:
                    logging.warning("Google Translate non-200 status: %s", res.status)
                    continue
                data = await res.json()
                translated = (
                    ((data.get("data") or {}).get("translations") or [{}])[0]
                    .get("translatedText", "")
                    .strip()
                )
                if translated:
                    return translated
        except aiohttp.ClientConnectorError:
            _mark_network_blocked()
            return "—"
        except Exception:
            logging.exception("Google Translate request failed (attempt %s)", attempt + 1)
            await asyncio.sleep(0.15 * (attempt + 1))
    return "—"


async def get_translation_gemini(session: aiohttp.ClientSession, word: str) -> str:
    if _network_temporarily_blocked():
        return "—"
    if not GEMINI_API_KEY:
        return "—"
    url = (
        f"https://generativelanguage.googleapis.com/v1/models/"
        f"gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f'Translate the English word "{word}" to Armenian.\n'
                            "This may be any part of speech: verb, noun, adjective, "
                            "article, preposition, conjunction, pronoun, etc.\n"
                            "If it has multiple meanings, list them separated by ' / '.\n"
                            "Put the most common and most precise everyday meaning FIRST.\n"
                            "Avoid overly broad generic Armenian terms when a specific one exists.\n"
                            "Reply ONLY with the Armenian translation(s), nothing else.\n"
                            "Example for 'go': գնալ / մեկնել / անցնել\n"
                            "Example for 'the': որոշյալ հոդ (ը, ն)\n"
                            "Example for 'and': և / ու\n"
                            "Example for 'desk': գրասեղան / սեղան"
                        )
                    }
                ]
            }
        ]
    }
    timeout = aiohttp.ClientTimeout(total=2.5)
    for attempt in range(2):
        try:
            async with session.post(url, json=payload, timeout=timeout) as res:
                if res.status != 200:
                    logging.warning("Gemini API non-200 status: %s", res.status)
                    continue
                data: Dict[str, Any] = await res.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    logging.warning("Gemini API missing candidates: %s", data)
                    continue
                content = candidates[0].get("content") or {}
                parts = content.get("parts") or []
                if not parts:
                    logging.warning("Gemini API missing parts: %s", content)
                    continue
                text = parts[0].get("text", "").strip()
                return text if text else "—"
        except aiohttp.ClientConnectorError:
            _mark_network_blocked()
            return "—"
        except Exception:
            logging.exception("Gemini word translation request failed (attempt %s)", attempt + 1)
            await asyncio.sleep(0.2 * (attempt + 1))
    return "—"


async def get_sentence_translation(session: aiohttp.ClientSession, sentence: str) -> str:
    if _network_temporarily_blocked():
        return "—"
    if not GOOGLE_TRANSLATE_API_KEY and not GEMINI_API_KEY:
        return "—"
    # Primary: Google Translate. Fallback: Gemini.
    gt = await _google_translate_text(session, sentence, source_lang="en", target_lang="hy")
    if gt and gt != "—":
        return gt
    return await get_sentence_translation_gemini(session, sentence)


async def get_sentence_translation_gemini(session: aiohttp.ClientSession, sentence: str) -> str:
    if _network_temporarily_blocked():
        return "—"
    if not GEMINI_API_KEY:
        return "—"
    url = (
        f"https://generativelanguage.googleapis.com/v1/models/"
        f"gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Translate the following English sentence into Armenian.\n"
                            "Reply ONLY with the Armenian translation.\n"
                            f"Sentence: {sentence}"
                        )
                    }
                ]
            }
        ]
    }
    timeout = aiohttp.ClientTimeout(total=3)
    for attempt in range(2):
        try:
            async with session.post(url, json=payload, timeout=timeout) as res:
                if res.status != 200:
                    logging.warning("Gemini API (sentence) non-200 status: %s", res.status)
                    continue
                data = await res.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    logging.warning("Gemini API (sentence) missing candidates: %s", data)
                    continue
                content = candidates[0].get("content") or {}
                parts = content.get("parts") or []
                if not parts:
                    logging.warning("Gemini API (sentence) missing parts: %s", content)
                    continue
                text = parts[0].get("text", "").strip()
                return text if text else "—"
        except aiohttp.ClientConnectorError:
            _mark_network_blocked()
            return "—"
        except Exception:
            logging.exception("Gemini sentence translation request failed (attempt %s)", attempt + 1)
            await asyncio.sleep(0.2 * (attempt + 1))
    return "—"


def _extract_example(dict_data: list) -> str:
    try:
        if not isinstance(dict_data, list) or not dict_data:
            return "—"
        for meaning in dict_data[0].get("meanings", []):
            for d in meaning.get("definitions", []):
                ex = d.get("example")
                if ex:
                    return ex.strip()
    except Exception:
        logging.exception("Failed to extract example from dictionary data")
    return "—"


async def get_word_data(word: str, level: str = "") -> dict:
    """Վերցնել բառի տվյալները — word parameter-ը database-ից է գալիս"""
    normalized_word = _normalize_word(word)
    if not normalized_word:
        return {
            "word": "—",
            "transcription": "—",
            "translation": "—",
            "definition": "—",
            "example": "—",
            "example_translation": "—",
        }

    cached = _get_cached_word_data(normalized_word)
    if cached is not None:
        return cached

    session = await _get_http_session()
    transcription = "—"
    definition = "—"
    example = "—"
    audio_url = ""

    async def _fetch_dictionary_fields() -> tuple[str, str, str, str]:
        local_transcription = "—"
        local_definition = "—"
        local_example = "—"
        local_audio = ""
        try:
            if _network_temporarily_blocked():
                return local_transcription, local_definition, local_example, local_audio
            async with session.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{normalized_word}",
                timeout=aiohttp.ClientTimeout(total=2.5),
            ) as res:
                if res.status != 200:
                    return local_transcription, local_definition, local_example, local_audio
                dict_data = await res.json()
                if not (isinstance(dict_data, list) and dict_data):
                    return local_transcription, local_definition, local_example, local_audio
                try:
                    local_transcription = _get_phonetic(dict_data)
                except Exception:
                    local_transcription = "—"
                try:
                    meaning0 = dict_data[0].get("meanings", [])
                    defs0 = meaning0[0].get("definitions", []) if meaning0 else []
                    local_definition = defs0[0].get("definition", "—") if defs0 else "—"
                    ex = _extract_example(dict_data)
                    local_example = ex if ex else "—"
                except Exception:
                    local_definition = "—"
                try:
                    local_audio = _get_audio_url(dict_data)
                except Exception:
                    local_audio = ""
        except aiohttp.ClientConnectorError:
            _mark_network_blocked()
        except Exception:
            logging.exception("Dictionary API request failed for word '%s'", normalized_word)
        return local_transcription, local_definition, local_example, local_audio

    # If level is A1/A2, prefer AI example for simplicity
    ai_ex_task = None
    if level and level.upper() in ("A1", "A2") and GEMINI_API_KEY:
        ai_ex_task = asyncio.create_task(get_ai_example_sentences(normalized_word, count=1, level=level))

    dict_task = asyncio.create_task(_fetch_dictionary_fields())
    trans_task = asyncio.create_task(get_translation(session, normalized_word))
    (transcription, definition, example, audio_url), translation = await asyncio.gather(
        dict_task, trans_task
    )
    if ai_ex_task:
        ai_exs = await ai_ex_task
        if ai_exs:
            example = ai_exs[0]

    example_translation = "—"
    if example and example != "—":
        example_translation = await get_sentence_translation(session, example)

    result = {
        "word": normalized_word,
        "transcription": transcription,
        "translation": translation,
        "definition": definition,
        "example": example,
        "example_translation": example_translation,
        "audio_url": audio_url,
    }
    _set_cached_word_data(normalized_word, result)
    return result


def _fallback_examples(word: str) -> list[str]:
    return [
        f"I use the word '{word}' in this sentence.",
        f"Learning '{word}' every day helps my English.",
        f"Can you make your own sentence with '{word}'?",
    ]


def _parse_examples_text(text: str, limit: int = 3) -> list[str]:
    lines = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^\d+[\).\-\s]+", "", line).strip()
        line = line.strip('"').strip("'").strip()
        if line:
            lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def _fallback_story(words: list[str], genre: str, level: str) -> str:
    safe_words = [w.strip().lower() for w in (words or []) if (w or "").strip()]
    if not safe_words:
        safe_words = ["learn", "practice", "remember"]
    genre_title = (genre or "general").title()
    level = (level or "A2").upper()
    word_line = ", ".join(safe_words)
    story = (
        f"📖 {genre_title} Story ({level})\n\n"
        f"Today I tried to use these words in real life: {word_line}. "
        f"In this small {genre_title.lower()} scene, every word appeared at least once. "
        f"I repeated them, said them aloud, and used them in short sentences. "
        f"By the end, the words felt more natural and easier to remember.\n\n"
    )
    # Make target words visually distinctive in fallback too.
    for w in safe_words[:6]:
        story += f"I used ⟦{w}⟧ in a meaningful sentence. "
    return story


async def generate_contextual_story(words: list[str], genre: str, level: str) -> str:
    safe_words = [w.strip().lower() for w in (words or []) if (w or "").strip()]
    safe_words = list(dict.fromkeys(safe_words))[:12]
    if not safe_words:
        return _fallback_story([], genre, level)

    if not GEMINI_API_KEY or _network_temporarily_blocked():
        return _fallback_story(safe_words, genre, level)

    session = await _get_http_session()
    url = (
        "https://generativelanguage.googleapis.com/v1/models/"
        f"gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    )
    level = (level or "A2").upper()
    genre_title = (genre or "general").strip().lower()
    words_list = ", ".join(safe_words)
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are an English learning assistant.\n"
                            f"Write one short, engaging {genre_title} story (120-220 words) for CEFR {level}.\n"
                            "Rules:\n"
                            f"1) Use EVERY target word at least once: {words_list}\n"
                            "2) Every time you use a target word, wrap it exactly like this: ⟦word⟧\n"
                            "3) Keep grammar and vocabulary suitable for that CEFR level.\n"
                            "4) Natural, fun tone.\n"
                            "5) Output ONLY the story body, no glossary, no title, no lists.\n"
                            "6) Return plain text only."
                        )
                    }
                ]
            }
        ]
    }

    timeout = aiohttp.ClientTimeout(total=10)
    for _ in range(2):
        try:
            async with session.post(url, json=payload, timeout=timeout) as res:
                if res.status != 200:
                    continue
                data = await res.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    continue
                parts = ((candidates[0].get("content") or {}).get("parts") or [])
                if not parts:
                    continue
                txt = (parts[0].get("text") or "").strip()
                if txt:
                    return txt
        except aiohttp.ClientConnectorError:
            _mark_network_blocked()
            break
        except Exception:
            continue
    return _fallback_story(safe_words, genre, level)


def _fallback_memory_palace(words: list[str], theme: str, level: str) -> str:
    safe_words = [w.strip().lower() for w in (words or []) if (w or "").strip()]
    safe_words = list(dict.fromkeys(safe_words))[:10]
    if not safe_words:
        safe_words = ["mirror", "ancient", "cat"]
    theme = (theme or "classic room").strip()
    level = (level or "A2").upper()
    lines = [
        f"🧠 Memory Palace ({theme}, {level})",
        "",
        f"Imagine one vivid room. Put each word as a visual anchor: {', '.join(safe_words)}.",
        "Walk clockwise and connect each object with an exaggerated action.",
        "Use smell, color, sound, and movement to make the scene memorable.",
        "",
        "Route:",
    ]
    for i, w in enumerate(safe_words, 1):
        lines.append(f"{i}. ⟦{w}⟧ — place it in a unique corner with a strange action.")
    lines.append("")
    lines.append("Recall tip: close your eyes, walk the same route, and say each word aloud.")
    return "\n".join(lines)


async def generate_memory_palace_text(words: list[str], theme: str, level: str) -> str:
    safe_words = [w.strip().lower() for w in (words or []) if (w or "").strip()]
    safe_words = list(dict.fromkeys(safe_words))[:10]
    if not safe_words:
        return _fallback_memory_palace([], theme, level)

    if not GEMINI_API_KEY or _network_temporarily_blocked():
        return _fallback_memory_palace(safe_words, theme, level)

    session = await _get_http_session()
    url = (
        "https://generativelanguage.googleapis.com/v1/models/"
        f"gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    )
    level = (level or "A2").upper()
    theme = (theme or "classic room").strip()
    words_list = ", ".join(safe_words)
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are a memory coach.\n"
                            f"Create one textual memory palace scene for CEFR {level}.\n"
                            f"Theme: {theme}\n"
                            f"Target words: {words_list}\n"
                            "Rules:\n"
                            "1) Use every target word at least once, wrapped as ⟦word⟧\n"
                            "2) Output 120-220 words\n"
                            "3) Give a short step-by-step route (1..N) through the room\n"
                            "4) Keep language simple and vivid\n"
                            "5) Plain text only"
                        )
                    }
                ]
            }
        ]
    }

    timeout = aiohttp.ClientTimeout(total=10)
    for _ in range(2):
        try:
            async with session.post(url, json=payload, timeout=timeout) as res:
                if res.status != 200:
                    continue
                data = await res.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    continue
                parts = ((candidates[0].get("content") or {}).get("parts") or [])
                if not parts:
                    continue
                txt = (parts[0].get("text") or "").strip()
                if txt:
                    return txt
        except aiohttp.ClientConnectorError:
            _mark_network_blocked()
            break
        except Exception:
            continue
    return _fallback_memory_palace(safe_words, theme, level)


async def get_ai_example_sentences(word: str, count: int = 3, level: str = "A2") -> list[str]:
    normalized_word = _normalize_word(word)
    if not normalized_word:
        return []

    cached = _get_cached_examples(normalized_word)
    if cached is not None:
        return cached[:count]

    if not GEMINI_API_KEY or _network_temporarily_blocked():
        fallback = _fallback_examples(normalized_word)[:count]
        _set_cached_examples(normalized_word, fallback)
        return fallback

    safe_level = (level or "A2").upper()
    session = await _get_http_session()
    url = (
        "https://generativelanguage.googleapis.com/v1/models/"
        f"gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"Generate exactly {count} short English example sentences for the word "
                            f"'{normalized_word}'.\n"
                            f"Level: {safe_level}.\n"
                            "Output format:\n"
                            "1. sentence\n2. sentence\n3. sentence\n"
                            "No explanations."
                        )
                    }
                ]
            }
        ]
    }

    timeout = aiohttp.ClientTimeout(total=5)
    for _ in range(2):
        try:
            async with session.post(url, json=payload, timeout=timeout) as res:
                if res.status != 200:
                    continue
                data = await res.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    continue
                parts = ((candidates[0].get("content") or {}).get("parts") or [])
                if not parts:
                    continue
                raw_text = (parts[0].get("text") or "").strip()
                parsed = _parse_examples_text(raw_text, limit=count)
                if len(parsed) >= min(2, count):
                    _set_cached_examples(normalized_word, parsed)
                    return parsed[:count]
        except aiohttp.ClientConnectorError:
            _mark_network_blocked()
            break
        except Exception:
            continue

    fallback = _fallback_examples(normalized_word)[:count]
    _set_cached_examples(normalized_word, fallback)
    return fallback


async def get_tutor_explanation_gemini(session: aiohttp.ClientSession, query: str, level: str = "B1") -> str:
    """Gemini-powered English tutor explanation for words, phrases, or grammar."""
    if _network_temporarily_blocked():
        return "⚠️ Network is temporarily blocked. Please try again later."
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API key is not configured."

    url = (
        f"https://generativelanguage.googleapis.com/v1/models/"
        f"gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    )
    
    level = (level or "B1").upper()
    
    prompt = (
        "You are a friendly and expert English Tutor (Tutor Mode).\n"
        f"The student (Level: {level}) wants an explanation for: '{query}'.\n\n"
        "Structure your response exactly like this for Telegram Markdown:\n\n"
        "🧐 **Tutor Explanation: " + query + "**\n"
        "━━━━━━━━━━━━━━━\n\n"
        "📌 **Համառոտ (Summary)**\n"
        "[1-2 sentence brief Armenian summary]\n\n"
        "💡 **Detailed Explanation (English)**\n"
        "[Thorough English explanation for CEFR " + level + "]\n\n"
        "🇦🇲 **Մանրամասն Բացատրություն (Armenian)**\n"
        "[Full Armenian translation of the above English part]\n\n"
        "💬 **Examples / Օրինակներ**\n"
        "• `English Example sentence` — *Հայերեն թարգմանություն*\n"
        "• `English Example sentence` — *Հայերեն թարգմանություն*\n\n"
        "━━━━━━━━━━━━━━━\n"
        "✨ *Keep practicing! / Շարունակիր պարապել:* \n\n"
        "Rules:\n"
        "- Use **bold** for section headers and key terms.\n"
        "- Use `fixed-width code` for the target word or English examples.\n"
        "- Use *italic* for translations.\n"
        "- Use separators like ━━━━━━━━━━━━━━━.\n"
        "- If comparing ('A vs B'), use a clear comparison list."
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    timeout = aiohttp.ClientTimeout(total=15)
    for attempt in range(2):
        try:
            async with session.post(url, json=payload, timeout=timeout) as res:
                if res.status != 200:
                    logging.warning("Gemini Tutor API non-200 status: %s", res.status)
                    continue
                data = await res.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    continue
                content = candidates[0].get("content") or {}
                parts = content.get("parts") or []
                if not parts:
                    continue
                text = parts[0].get("text", "").strip()
                return text if text else "⚠️ Could not generate an explanation."
        except aiohttp.ClientConnectorError:
            _mark_network_blocked()
            return "⚠️ Network connection error."
        except Exception:
            logging.exception("Gemini Tutor request failed (attempt %s)", attempt + 1)
            await asyncio.sleep(0.5 * (attempt + 1))
            
    return "⚠️ Sorry, I'm having trouble connecting to my knowledge base right now."
