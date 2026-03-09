import os
from pathlib import Path

def _load_local_env() -> None:
    """Minimal .env loader to avoid external dependency in restricted environments."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        # Ignore malformed .env; runtime validation happens in bot.py.
        pass


_load_local_env()


def _getenv(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or "").strip()


# Keep a test-safe fallback so imports don't fail in local tests.
TOKEN = _getenv("TOKEN", "123456:TEST_TOKEN")
GEMINI_API_KEY = _getenv("GEMINI_API_KEY", "")
GOOGLE_TRANSLATE_API_KEY = _getenv("GOOGLE_TRANSLATE_API_KEY", "")
DATABASE_URL = _getenv("DATABASE_URL", "sqlite+aiosqlite:///words_bot.db")


def _parse_admin_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for chunk in (raw or "").split(","):
        val = chunk.strip()
        if not val:
            continue
        try:
            ids.add(int(val))
        except ValueError:
            continue
    return ids


ADMIN_USER_IDS = _parse_admin_ids(_getenv("ADMIN_USER_IDS", ""))

# Bot settings
DAILY_LIMIT = 5
WORD_LEVEL_CHOICES = ("A1", "A2", "B1", "B2")
DAILY_STORY_LIMIT = 3
DAILY_PALACE_LIMIT = 3

STORY_GENRES = {
    "cyberpunk": "Cyberpunk",
    "detective": "Detective (Sherlock style)",
    "fantasy": "Fantasy",
    "comedy": "Comedy",
    "reallife": "Real-life Dialog",
}
PALACE_THEMES = {
    "ancient": "Ancient Room",
    "cyber": "Cyber Loft",
    "detective": "Detective Office",
    "fantasy": "Fantasy Tower",
    "cozy": "Cozy Home",
}
