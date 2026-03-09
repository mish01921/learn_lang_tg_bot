import logging
import os
import re

COMMON_WORDS_FILE = "common_words.txt"
LEVEL_KEYS = ("A1", "A2", "B1", "B2")

_level_words_cache: dict | None = None
_level_words_mtime: float | None = None


def extract_headword(line: str) -> str:
    """Return the headword from Oxford-format line, e.g. 'about prep.' -> 'about'."""
    match = re.match(r"^\s*([A-Za-z][A-Za-z'-]*)(?:\d+)?\b", line)
    return match.group(1).lower() if match else ""


def load_levelled_words() -> dict:
    """Read common_words.txt and return {level: [word]} mapping."""
    global _level_words_cache, _level_words_mtime
    levels = {k: [] for k in LEVEL_KEYS}

    try:
        mtime = os.path.getmtime(COMMON_WORDS_FILE)
        if _level_words_cache is not None and _level_words_mtime == mtime:
            return _level_words_cache
    except Exception:
        mtime = None

    current = None
    try:
        with open(COMMON_WORDS_FILE, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                up = line.upper()
                if up in levels:
                    current = up
                    continue
                if current is not None:
                    word = extract_headword(line)
                    if word:
                        levels[current].append(word)
        _level_words_cache = levels
        _level_words_mtime = mtime
    except Exception:
        logging.exception("Failed to read %s for levels", COMMON_WORDS_FILE)
    return levels


def chunk_text(text: str, max_len: int = 4000) -> list[str]:
    chunks, buf = [], ""
    for line in text.splitlines(keepends=True):
        if len(buf) + len(line) > max_len:
            chunks.append(buf)
            buf = ""
        buf += line
    if buf:
        chunks.append(buf)
    return chunks


def find_word_levels(word: str) -> list[str]:
    target = (word or "").strip().lower()
    if not target:
        return []
    levels = load_levelled_words()
    return [lvl for lvl, words in levels.items() if target in words]

