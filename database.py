import asyncpg
from datetime import datetime, timedelta
import logging
import json
import re

from config import DATABASE_URL

ADMIN_AUDIT_TABLE = "admin.audit_log"
ADMIN_SETTINGS_TABLE = "admin.settings"


class _PgCursor:
    def __init__(self, rows: list | None = None, rowcount: int = 0, lastrowid: int | None = None):
        self._rows = rows or []
        self._idx = 0
        self.rowcount = int(rowcount or 0)
        self.lastrowid = lastrowid

    async def fetchone(self):
        if self._idx >= len(self._rows):
            return None
        row = self._rows[self._idx]
        self._idx += 1
        return row

    async def fetchall(self):
        if self._idx <= 0:
            return list(self._rows)
        return list(self._rows[self._idx :])

    def __aiter__(self):
        return self

    async def __anext__(self):
        row = await self.fetchone()
        if row is None:
            raise StopAsyncIteration
        return row


class _PgExecuteContext:
    def __init__(self, conn: "_PgConnection", sql: str, params: tuple | list | None = None):
        self._conn = conn
        self._sql = sql
        self._params = tuple(params or ())
        self._cursor: _PgCursor | None = None

    def __await__(self):
        return self._run().__await__()

    async def __aenter__(self):
        return await self._run()

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def _run(self) -> _PgCursor:
        if self._cursor is None:
            self._cursor = await self._conn._execute_internal(self._sql, self._params)
        return self._cursor


class _PgConnection:
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._conn: asyncpg.Connection | None = None
        self.row_factory = None

    async def __aenter__(self):
        dsn = self._dsn
        if not dsn or not dsn.startswith("postgres"):
            raise ValueError("Invalid or empty DATABASE_URL for PostgreSQL.")

        # Log the DSN for debugging, but hide the password
        safe_dsn = re.sub(r"://[^@/]+@", "://<user>:<password>@", dsn)
        logging.info(f"Connecting to PostgreSQL with DSN: {safe_dsn}")

        if dsn.startswith("postgresql+asyncpg://"):
            dsn = "postgresql://" + dsn[len("postgresql+asyncpg://") :]
        elif dsn.startswith("postgres+asyncpg://"):
            dsn = "postgres://" + dsn[len("postgres+asyncpg://") :]
        try:
            self._conn = await asyncpg.connect(dsn)
        except Exception as e:
            logging.error(f"Failed to connect to PostgreSQL: {e}")
            raise
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._conn is not None:
            await self._conn.close()
        self._conn = None
        return False

    def execute(self, sql: str, params: tuple | list | None = None):
        return _PgExecuteContext(self, sql, params)

    async def commit(self):
        # asyncpg auto-commits outside explicit transactions.
        return None

    async def _execute_internal(self, sql: str, params: tuple):
        assert self._conn is not None
        pg_sql, pg_params = _translate_sql_for_postgres(sql, params)
        if not pg_sql:
            return _PgCursor()

        up = pg_sql.strip().upper()
        is_select = up.startswith("SELECT") or up.startswith("WITH")
        has_returning = " RETURNING " in f" {up} "

        if is_select or has_returning:
            rows = await self._conn.fetch(pg_sql, *pg_params)
            lastrowid = None
            if has_returning and rows:
                first = rows[0]
                if "id" in first:
                    lastrowid = int(first["id"])
                elif len(first) > 0:
                    lastrowid = int(first[0])
            return _PgCursor(rows=list(rows), rowcount=len(rows), lastrowid=lastrowid)

        status = await self._conn.execute(pg_sql, *pg_params)
        rowcount = 0
        m = re.search(r"(\d+)$", status or "")
        if m:
            rowcount = int(m.group(1))
        return _PgCursor(rowcount=rowcount)


def _translate_sql_for_postgres(sql: str, params: tuple) -> tuple[str, tuple]:
    raw = (sql or "").strip()
    if not raw:
        return "", params
    up = raw.upper()
    if up.startswith("PRAGMA "):
        return "", params

    # SQLite-specific upsert style
    if "INSERT OR IGNORE INTO" in up:
        raw = re.sub(r"INSERT\s+OR\s+IGNORE\s+INTO", "INSERT INTO", raw, flags=re.IGNORECASE)
        raw = f"{raw} ON CONFLICT DO NOTHING"

    idx = 0

    def repl(_):
        nonlocal idx
        idx += 1
        return f"${idx}"

    raw = re.sub(r"\?", repl, raw)
    return raw, params


def _db_connect():
    return _PgConnection(DATABASE_URL)

# ═══════════════════════════════════════════════════════
# INIT
# ═══════════════════════════════════════════════════════

async def _init_postgres_schema():
    """Creates all tables and indexes for PostgreSQL if they don't exist."""
    async with _db_connect() as db:
        # Create admin schema if it doesn't exist
        await db.execute("CREATE SCHEMA IF NOT EXISTS admin")

        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id         BIGINT PRIMARY KEY,
                username        TEXT,
                joined_at       TEXT,
                streak          INTEGER DEFAULT 0,
                last_active     TEXT,
                daily_count     INTEGER DEFAULT 0,
                daily_date      TEXT,
                user_level      TEXT,
                banned          INTEGER DEFAULT 0,
                ban_reason      TEXT,
                placement_done  INTEGER DEFAULT 0,
                placement_score INTEGER DEFAULT 0,
                placement_taken_at TEXT
            )
        """)

        # word_progress table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS word_progress (
                id              SERIAL PRIMARY KEY,
                user_id         BIGINT NOT NULL,
                word            TEXT NOT NULL,
                level           INTEGER DEFAULT 0,
                seen            INTEGER DEFAULT 0,
                correct         INTEGER DEFAULT 0,
                correct_streak  INTEGER DEFAULT 0,
                wrong           INTEGER DEFAULT 0,
                learned         INTEGER DEFAULT 0,
                marked_hard     INTEGER DEFAULT 0,
                marked_know     INTEGER DEFAULT 0,
                added_at        TEXT,
                learned_at      TEXT,
                next_review     TEXT,
                ease_factor     REAL DEFAULT 2.5,
                interval_days   INTEGER DEFAULT 0,
                repetitions     INTEGER DEFAULT 0,
                last_reviewed_at TEXT,
                last_grade      TEXT,
                UNIQUE(user_id, word),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # sessions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          SERIAL PRIMARY KEY,
                user_id     BIGINT NOT NULL,
                word        TEXT NOT NULL,
                answered_at TEXT NOT NULL,
                correct     INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # story_history table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS story_history (
                id          SERIAL PRIMARY KEY,
                user_id     BIGINT NOT NULL,
                story_date  TEXT NOT NULL,
                genre       TEXT NOT NULL,
                words_json  TEXT NOT NULL,
                story_text  TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # memory_palace_history table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memory_palace_history (
                id          SERIAL PRIMARY KEY,
                user_id     BIGINT NOT NULL,
                palace_date TEXT NOT NULL,
                theme       TEXT NOT NULL,
                words_json  TEXT NOT NULL,
                palace_text TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # Indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_progress_user ON word_progress(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_progress_review ON word_progress(user_id, next_review)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_story_user_date ON story_history(user_id, story_date)")
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_palace_user_date ON memory_palace_history(user_id, palace_date)"
        )


async def init_db():
    """Initializes the database schema for PostgreSQL."""
    await _init_postgres_schema()


# ═══════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════

async def ensure_user(user_id: int, username: str = ""):
    now = datetime.now().isoformat()
    today = datetime.now().date().isoformat()
    safe_username = (username or "").strip()[:64]
    async with _db_connect() as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, joined_at, daily_date)
            VALUES (?, ?, ?, ?)
        """, (user_id, safe_username, now, today))
        if safe_username:
            # Keep username fresh for existing users as well.
            await db.execute(
                """
                UPDATE users
                SET username = ?
                WHERE user_id = ? AND COALESCE(username, '') <> ?
                """,
                (safe_username, user_id, safe_username),
            )
        await db.commit()
    await update_streak(user_id)


async def update_streak(user_id: int):
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            "SELECT streak, last_active FROM users WHERE user_id = ?",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()

        if not row:
            return

        now = datetime.now()
        today = now.date()
        last = datetime.fromisoformat(row["last_active"]).date() if row["last_active"] else None

        if last == today:
            # Keep last_active fresh on every interaction in the same day.
            await db.execute(
                "UPDATE users SET last_active = ? WHERE user_id = ?",
                (now.isoformat(), user_id),
            )
            await db.commit()
            return

        new_streak = 1 if (last is None or (today - last).days > 1) else row["streak"] + 1

        await db.execute("""
            UPDATE users SET streak = ?, last_active = ? WHERE user_id = ?
        """, (new_streak, now.isoformat(), user_id))
        await db.commit()


# ═══════════════════════════════════════════════════════
# DAILY COUNT
# ═══════════════════════════════════════════════════════

async def get_daily_count(user_id: int) -> int:
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            "SELECT daily_count, daily_date FROM users WHERE user_id = ?",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()

        if not row:
            return 0

        if row["daily_date"] != today:
            await db.execute("""
                UPDATE users SET daily_count = 0, daily_date = ? WHERE user_id = ?
            """, (today, user_id))
            await db.commit()
            return 0

        return row["daily_count"] or 0


async def increment_daily(user_id: int, word: str | None = None):
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        # Count only unique words per day (same word answered multiple times today counts once)
        should_increment = True
        if word:
            async with db.execute(
                """
                SELECT COUNT(*) as c
                FROM sessions
                WHERE user_id = ? AND word = ? AND substr(answered_at, 1, 10) = ?
                """,
                (user_id, word, today),
            ) as cur:
                row = await cur.fetchone()
                should_increment = (row[0] if row else 0) <= 1

        if should_increment:
            # If day changed, reset to 0 first, then increment
            await db.execute(
                """
                UPDATE users
                SET daily_count = CASE WHEN daily_date = ? THEN daily_count + 1 ELSE 1 END,
                    daily_date = ?
                WHERE user_id = ?
                """,
                (today, today, user_id),
            )
        else:
            # Keep day synced even when count is not incremented
            await db.execute(
                """
                UPDATE users
                SET daily_date = CASE WHEN daily_date IS NULL THEN ? ELSE daily_date END
                WHERE user_id = ?
                """,
                (today, user_id),
            )
        await db.commit()


# ═══════════════════════════════════════════════════════
# USER LEVEL
# ══════════════════════════���════════════════════════════

async def set_user_level(user_id: int, level: str):
    level = (level or "").upper()
    if level not in {"A1", "A2", "B1", "B2"}:
        return
    async with _db_connect() as db:
        await db.execute(
            "UPDATE users SET user_level = ? WHERE user_id = ?",
            (level, user_id),
        )
        await db.commit()


async def get_user_level(user_id: int) -> str:
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            "SELECT user_level FROM users WHERE user_id = ?",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
    lvl = (row["user_level"] if row else None) if row else None
    return lvl or "A1"


async def is_placement_done(user_id: int) -> bool:
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            "SELECT COALESCE(placement_done, 0) AS placement_done FROM users WHERE user_id = ?",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
    return bool(row and int(row["placement_done"] or 0) == 1)


async def set_placement_result(user_id: int, level: str, score: int) -> bool:
    level = (level or "A1").upper()
    if level not in {"A1", "A2", "B1", "B2"}:
        level = "A1"
    now = datetime.now().isoformat()
    async with _db_connect() as db:
        cur = await db.execute(
            """
            UPDATE users
            SET placement_done = 1,
                placement_score = ?,
                placement_taken_at = ?,
                user_level = ?
            WHERE user_id = ?
            """,
            (int(score or 0), now, level, user_id),
        )
        await db.commit()
    return (cur.rowcount or 0) > 0


# ═══════════════════════════════════════════════════════
# WORD PROGRESS
# ═══════════════════════════════════════════════════════

INTERVALS = {0: 0, 1: 1, 2: 3, 3: 7}


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(v, hi))


def _srs_schedule(
    *,
    correct: bool,
    marked_hard: bool,
    grade: str | None,
    ease_factor: float,
    interval_days: int,
    repetitions: int,
) -> tuple[float, int, int]:
    ef = float(ease_factor or 2.5)
    ivl = int(interval_days or 0)
    reps = int(repetitions or 0)

    g = (grade or ("hard" if (correct and marked_hard) else ("again" if not correct else "good"))).strip().lower()

    if g == "again":
        # Failed recall: reset reps and show again soon.
        ef = _clamp(ef - 0.20, 1.30, 3.00)
        return ef, 1, 0

    if g == "hard":
        # Hard recall: keep momentum but schedule near-term review.
        ef = _clamp(ef - 0.05, 1.30, 3.00)
        next_ivl = max(1, int(round((ivl if ivl > 0 else 1) * 1.2)))
        return ef, next_ivl, max(1, reps + 1)

    if g == "easy":
        ef = _clamp(ef + 0.08, 1.30, 3.00)
        if reps <= 0:
            next_ivl = 2
        elif reps == 1:
            next_ivl = 5
        else:
            base = ivl if ivl > 0 else 5
            next_ivl = max(6, int(round(base * (ef + 0.25))))
        return ef, next_ivl, reps + 1

    # Good recall
    ef = _clamp(ef + 0.03, 1.30, 3.00)
    if reps <= 0:
        next_ivl = 1
    elif reps == 1:
        next_ivl = 3
    else:
        base = ivl if ivl > 0 else 3
        next_ivl = max(4, int(round(base * ef)))
    return ef, next_ivl, reps + 1


async def get_next_word(
    user_id: int,
    all_words: list[str],
    exclude_word: str = "",
    exclude_words: list[str] | None = None,
    include_hard_due: bool = True,
) -> str:
    import random
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        today = datetime.now().isoformat()
        allowed = list(all_words)
        excluded_set = set()
        if exclude_word:
            excluded_set.add(exclude_word.strip())
        if exclude_words:
            excluded_set.update((w or "").strip() for w in exclude_words if w)
        filtered_allowed = [w for w in allowed if w not in excluded_set] or allowed
        if not allowed:
            return all_words[0] if all_words else ""
        placeholders = ",".join("?" * len(filtered_allowed))

        # 1. Marked hard + due (NULL next_review considered due)
        if include_hard_due:
            async with db.execute(
                f"""
                SELECT word FROM word_progress
                WHERE user_id = ? AND marked_hard = 1
                  AND (next_review IS NULL OR next_review <= ?)
                  AND word IN ({placeholders})
                ORDER BY next_review ASC LIMIT 1
                """,
                (user_id, today, *filtered_allowed),
            ) as cur:
                row = await cur.fetchone()
                if row:
                    return row["word"]

        # 2. Due words (explicitly require non-NULL next_review)
        async with db.execute(
            f"""
            SELECT word FROM word_progress
            WHERE user_id = ? AND marked_hard = 0
              AND next_review IS NOT NULL AND next_review <= ?
              AND word IN ({placeholders})
            ORDER BY next_review ASC LIMIT 1
            """,
            (user_id, today, *filtered_allowed),
        ) as cur:
            row = await cur.fetchone()
            if row:
                return row["word"]

        # 3. New words
        async with db.execute(
            "SELECT word FROM word_progress WHERE user_id = ?",
            (user_id,),
        ) as cur:
            seen = {r["word"] async for r in cur}

        new_words = [w for w in filtered_allowed if w not in seen]
        if new_words:
            return random.choice(new_words)

        # 4. Oldest next_review (treat NULLs as last)
        async with db.execute(
            f"""
            SELECT word FROM word_progress
            WHERE user_id = ? AND word IN ({placeholders})
            ORDER BY (next_review IS NULL) ASC, next_review ASC
            LIMIT 1
            """,
            (user_id, *filtered_allowed),
        ) as cur:
            row = await cur.fetchone()
            if row:
                return row["word"]
            return filtered_allowed[0] if filtered_allowed else all_words[0]


async def get_word_reason(user_id: int, word: str) -> str:
    """Return a short human-readable reason why this word is shown now."""
    if not word:
        return "Նոր բառ՝ շարունակելու համար։"

    now = datetime.now().isoformat()
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            """
            SELECT seen, marked_hard, next_review, correct, wrong
            FROM word_progress
            WHERE user_id = ? AND word = ?
            """,
            (user_id, word),
        ) as cur:
            row = await cur.fetchone()

    if not row:
        return "Նոր բառ է ձեր ծրագրում։"
    if (row["marked_hard"] or 0) == 1:
        return "Նշված էր «Կրկնել», դրա համար կրկին ցույց է տրվում։"
    if row["next_review"] and row["next_review"] <= now:
        return "Կրկնության ժամկետը եկել է։"
    if (row["seen"] or 0) <= 1:
        return "Նոր կամ քիչ տեսած բառ է՝ ամրապնդման համար։"
    wrong = row["wrong"] or 0
    correct = row["correct"] or 0
    if wrong > correct:
        return "Այս բառով ավելի հաճախ եք սխալվել, դրա համար առաջնահերթ է։"
    return "Պլանային հերթական բառ է ձեր մակարդակից։"


async def record_answer(
    user_id: int,
    word: str,
    correct: bool,
    marked_hard: bool = False,
    grade: str | None = None,
):
    now = datetime.now().isoformat()
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record

        await db.execute(
            """
            INSERT OR IGNORE INTO word_progress (user_id, word, added_at)
            VALUES (?, ?, ?)
            """,
            (user_id, word, now),
        )

        async with db.execute(
            """
            SELECT level, correct, correct_streak, wrong, marked_hard, marked_know,
                   ease_factor, interval_days, repetitions
            FROM word_progress WHERE user_id = ? AND word = ?
            """,
            (user_id, word),
        ) as cur:
            entry = await cur.fetchone()

        level = entry["level"]
        new_correct = entry["correct"] + (1 if correct else 0)
        new_wrong = entry["wrong"] + (0 if correct else 1)
        new_correct_streak = entry["correct_streak"] + 1 if correct else 0

        if correct:
            level = min(level + 1, 3)
        else:
            # allow level to drop to 0
            level = max(level - 1, 0)

        grade_norm = (grade or "").strip().lower()
        if not grade_norm:
            grade_norm = "hard" if (correct and marked_hard) else ("again" if not correct else "good")

        # marked_know — set on good/easy outcomes
        new_marked_know = 1 if grade_norm in {"good", "easy"} else entry["marked_know"]
        # marked_hard — persist for again/hard outcomes, clear for good/easy
        if grade_norm in {"again", "hard"}:
            new_marked_hard = 1
        elif grade_norm in {"good", "easy"}:
            new_marked_hard = 0
        else:
            new_marked_hard = 0 if correct else (1 if marked_hard else entry["marked_hard"])

        # learned_at — set on good/easy
        learned_at = now if grade_norm in {"good", "easy"} else None

        ef, srs_interval_days, srs_repetitions = _srs_schedule(
            correct=correct,
            marked_hard=marked_hard,
            grade=grade_norm,
            ease_factor=float(entry["ease_factor"] if entry["ease_factor"] is not None else 2.5),
            interval_days=int(entry["interval_days"] or 0),
            repetitions=int(entry["repetitions"] or 0),
        )
        days = max(INTERVALS[level], srs_interval_days)
        next_review = (datetime.now() + timedelta(days=days)).isoformat()

        await db.execute(
            """
            UPDATE word_progress
            SET level=?, seen=seen+1, correct=?, correct_streak=?,
                wrong=?, marked_hard=?, marked_know=?,
                learned_at=COALESCE(?, learned_at),
                next_review=?,
                ease_factor=?, interval_days=?, repetitions=?, last_reviewed_at=?,
                last_grade=?
            WHERE user_id=? AND word=?
            """,
            (
                level,
                new_correct,
                new_correct_streak,
                new_wrong,
                new_marked_hard,
                new_marked_know,
                learned_at,
                next_review,
                ef,
                days,
                srs_repetitions,
                now,
                grade_norm,
                user_id,
                word,
            ),
        )

        await db.execute(
            """
            INSERT INTO sessions (user_id, word, answered_at, correct)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, word, now, 1 if correct else 0),
        )

        await db.commit()


# ═══════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════

async def get_stats(user_id: int, total_words: int) -> dict:
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        today = datetime.now().isoformat()

        async with db.execute("""
            SELECT
                COUNT(*) as seen,
                SUM(marked_know) as learned,
                SUM(marked_hard) as hard,
                SUM(correct) as total_correct,
                SUM(wrong) as total_wrong,
                SUM(CASE WHEN marked_hard=1 AND next_review <= ? THEN 1 ELSE 0 END) as due_today
            FROM word_progress WHERE user_id = ?
        """, (today, user_id)) as cur:
            s = await cur.fetchone()

        async with db.execute(
            "SELECT streak FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            u = await cur.fetchone()

        seen = s["seen"] or 0
        learned = s["learned"] or 0
        total_correct = s["total_correct"] or 0
        total_wrong = s["total_wrong"] or 0
        total_answers = total_correct + total_wrong

        return {
            "total": total_words,
            "seen": seen,
            "unseen": total_words - seen,
            "learned": learned,
            "hard": s["hard"] or 0,
            "due_today": s["due_today"] or 0,
            "accuracy": round(total_correct / total_answers * 100) if total_answers else 0,
            "progress_pct": round(learned / total_words * 100, 1),
            "streak": u["streak"] if u else 0,
        }


async def get_hard_words(user_id: int) -> list[dict]:
    """🔁 Կրկնել սեղմած բառերը"""
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute("""
            SELECT word, wrong, correct, added_at, last_grade
            FROM word_progress
            WHERE user_id = ? AND marked_hard = 1
            ORDER BY added_at DESC
        """, (user_id,)) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_seen_words(user_id: int, limit: int = 300) -> list[str]:
    """Return words that user has already seen at least once."""
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            """
            SELECT word
            FROM word_progress
            WHERE user_id = ? AND seen > 0
            ORDER BY added_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ) as cur:
            rows = await cur.fetchall()
    return [r["word"] for r in rows]


async def get_today_answered_words(user_id: int, limit: int = 10) -> list[str]:
    today = datetime.now().date().isoformat()
    safe_limit = max(1, min(int(limit or 10), 30))
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            """
            SELECT word
            FROM sessions
            WHERE user_id = ? AND substr(answered_at, 1, 10) = ?
            ORDER BY id DESC
            LIMIT 200
            """,
            (user_id, today),
        ) as cur:
            rows = await cur.fetchall()

    out: list[str] = []
    seen: set[str] = set()
    for r in rows:
        w = (r["word"] or "").strip().lower()
        if not w or w in seen:
            continue
        seen.add(w)
        out.append(w)
        if len(out) >= safe_limit:
            break
    return out


async def save_story_history(user_id: int, genre: str, words: list[str], story_text: str) -> int:
    now = datetime.now().isoformat()
    story_date = now[:10]
    words_json = json.dumps(list(dict.fromkeys(words or [])), ensure_ascii=False)
    async with _db_connect() as db:
        sql = """
            INSERT INTO story_history (user_id, story_date, genre, words_json, story_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        sql += " RETURNING id"
        cur = await db.execute(
            sql,
            (user_id, story_date, (genre or "general")[:40], words_json, story_text, now),
        )
        await db.commit()
        row = await cur.fetchone()
        return int((row["id"] if row and "id" in row else 0) or 0)


async def count_story_generations_today(user_id: int) -> int:
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            "SELECT COUNT(*) AS c FROM story_history WHERE user_id = ? AND story_date = ?",
            (user_id, today),
        ) as cur:
            row = await cur.fetchone()
    return int(row["c"] if row else 0)


async def get_story_history(user_id: int, limit: int = 5) -> list[dict]:
    safe_limit = max(1, min(int(limit or 5), 20))
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            """
            SELECT story_date, genre, words_json, story_text, created_at
            FROM story_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, safe_limit),
        ) as cur:
            rows = await cur.fetchall()
    out: list[dict] = []
    for r in rows:
        d = dict(r)
        try:
            d["words"] = json.loads(d.get("words_json") or "[]")
        except Exception:
            d["words"] = []
        out.append(d)
    return out


async def save_memory_palace_history(user_id: int, theme: str, words: list[str], palace_text: str) -> int:
    now = datetime.now().isoformat()
    palace_date = now[:10]
    words_json = json.dumps(list(dict.fromkeys(words or [])), ensure_ascii=False)
    async with _db_connect() as db:
        sql = """
            INSERT INTO memory_palace_history
                (user_id, palace_date, theme, words_json, palace_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        sql += " RETURNING id"
        cur = await db.execute(
            sql,
            (user_id, palace_date, (theme or "general")[:40], words_json, palace_text, now),
        )
        await db.commit()
        row = await cur.fetchone()
        return int((row["id"] if row and "id" in row else 0) or 0)


async def count_palace_generations_today(user_id: int) -> int:
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            "SELECT COUNT(*) AS c FROM memory_palace_history WHERE user_id = ? AND palace_date = ?",
            (user_id, today),
        ) as cur:
            row = await cur.fetchone()
    return int(row["c"] if row else 0)


async def get_memory_palace_history(user_id: int, limit: int = 5) -> list[dict]:
    safe_limit = max(1, min(int(limit or 5), 20))
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            """
            SELECT palace_date, theme, words_json, palace_text, created_at
            FROM memory_palace_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, safe_limit),
        ) as cur:
            rows = await cur.fetchall()
    out: list[dict] = []
    for r in rows:
        d = dict(r)
        try:
            d["words"] = json.loads(d.get("words_json") or "[]")
        except Exception:
            d["words"] = []
        out.append(d)
    return out


async def mark_word_learned(user_id: int, word: str) -> bool:
    """Move a word from review list to learned list."""
    now = datetime.now().isoformat()
    async with _db_connect() as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO word_progress (user_id, word, added_at)
            VALUES (?, ?, ?)
            """,
            (user_id, word, now),
        )
        cur = await db.execute(
            """
            UPDATE word_progress
            SET marked_hard = 0,
                marked_know = 1,
                learned = 1,
                learned_at = COALESCE(learned_at, ?),
                last_grade = 'good'
            WHERE user_id = ? AND word = ?
            """,
            (now, user_id, word),
        )
        await db.commit()
        return (cur.rowcount or 0) > 0


async def get_top_weak_words(user_id: int, limit: int = 3) -> list[dict]:
    """Words with the highest error pressure."""
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            """
            SELECT word, wrong, correct
            FROM word_progress
            WHERE user_id = ? AND wrong > 0
            ORDER BY (wrong - correct) DESC, wrong DESC
            LIMIT ?
            """,
            (user_id, limit),
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_wordset_progress(user_id: int, words: list[str]) -> dict:
    if not words:
        return {"total": 0, "learned": 0, "accuracy": 0}
    uniq = list(dict.fromkeys(w.strip() for w in words if (w or "").strip()))
    if not uniq:
        return {"total": 0, "learned": 0, "accuracy": 0}
    placeholders = ",".join("?" * len(uniq))
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            f"""
            SELECT COALESCE(SUM(marked_know), 0) AS learned
            FROM word_progress
            WHERE user_id = ? AND word IN ({placeholders})
            """,
            (user_id, *uniq),
        ) as cur:
            row = await cur.fetchone()
            learned = int(row["learned"] or 0) if row else 0

        async with db.execute(
            f"""
            SELECT
                COALESCE(SUM(correct), 0) AS total_correct,
                COALESCE(SUM(wrong), 0) AS total_wrong
            FROM word_progress
            WHERE user_id = ? AND word IN ({placeholders})
            """,
            (user_id, *uniq),
        ) as cur:
            row2 = await cur.fetchone()
            total_correct = int(row2["total_correct"] or 0) if row2 else 0
            total_wrong = int(row2["total_wrong"] or 0) if row2 else 0

    total_answers = total_correct + total_wrong
    return {
        "total": len(uniq),
        "learned": learned,
        "accuracy": round(total_correct * 100 / total_answers) if total_answers else 0,
    }


async def get_recent_accuracy(user_id: int, limit: int = 20) -> int:
    """Accuracy percentage for the latest N answered words."""
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            """
            SELECT correct
            FROM sessions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ) as cur:
            rows = await cur.fetchall()

    if not rows:
        return 0
    total = len(rows)
    ok = sum(int(r["correct"] or 0) for r in rows)
    return round(ok * 100 / total)


async def get_recent_accuracy_window(user_id: int, limit: int = 20, offset: int = 0) -> int | None:
    """Accuracy for a window of latest answers (supports OFFSET). Returns None if window is empty."""
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            """
            SELECT correct
            FROM sessions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        ) as cur:
            rows = await cur.fetchall()

    if not rows:
        return None
    total = len(rows)
    ok = sum(int(r["correct"] or 0) for r in rows)
    return round(ok * 100 / total)


async def get_learned_words(user_id: int) -> list[dict]:
    """✅ Գիտեմ սեղմած բառերը"""
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute("""
            SELECT word, correct, learned_at, last_grade
            FROM word_progress
            WHERE user_id = ? AND marked_know = 1
            ORDER BY learned_at DESC
        """, (user_id,)) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_word_grade_map(user_id: int, words: list[str]) -> dict[str, str]:
    uniq = list(dict.fromkeys((w or "").strip().lower() for w in (words or []) if (w or "").strip()))
    if not uniq:
        return {}
    placeholders = ",".join("?" * len(uniq))
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            f"""
            SELECT word, COALESCE(last_grade, '') AS last_grade, marked_hard, marked_know, seen
            FROM word_progress
            WHERE user_id = ? AND word IN ({placeholders})
            """,
            (user_id, *uniq),
        ) as cur:
            rows = await cur.fetchall()

    out: dict[str, str] = {}
    for r in rows:
        w = (r["word"] or "").strip().lower()
        g = (r["last_grade"] or "").strip().lower()
        if g:
            out[w] = g
            continue
        if int(r["marked_hard"] or 0) == 1:
            out[w] = "hard"
        elif int(r["marked_know"] or 0) == 1:
            out[w] = "good"
        elif int(r["seen"] or 0) > 0:
            out[w] = "again"
    return out


async def reset_progress(user_id: int, *, preserve_history: bool = True):
    async with _db_connect() as db:
        if not preserve_history:
            await db.execute("DELETE FROM word_progress WHERE user_id = ?", (user_id,))
            await db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        await db.execute(
            """
            UPDATE users SET streak=0, last_active=NULL,
            daily_count=0, daily_date=NULL WHERE user_id=?
            """,
            (user_id,),
        )
        await db.commit()


async def get_admin_overview() -> dict:
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record

        async with db.execute("SELECT COUNT(*) AS c FROM users") as cur:
            total_users = int((await cur.fetchone())["c"])

        async with db.execute(
            "SELECT COUNT(*) AS c FROM users WHERE date(joined_at) = date('now')"
        ) as cur:
            joined_today = int((await cur.fetchone())["c"])

        async with db.execute(
            "SELECT COUNT(*) AS c FROM users WHERE date(last_active) = date('now')"
        ) as cur:
            active_today = int((await cur.fetchone())["c"])

        async with db.execute("SELECT COUNT(*) AS c FROM word_progress WHERE learned = 1") as cur:
            learned_total = int((await cur.fetchone())["c"])

        async with db.execute("SELECT COUNT(*) AS c FROM word_progress WHERE marked_hard = 1") as cur:
            hard_total = int((await cur.fetchone())["c"])

    return {
        "total_users": total_users,
        "joined_today": joined_today,
        "active_today": active_today,
        "learned_total": learned_total,
        "hard_total": hard_total,
    }


async def get_health_snapshot() -> dict:
    """Basic DB health check + key row counts for admin /health command."""
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record

        async with db.execute("SELECT 1 AS ok") as cur:
            row = await cur.fetchone()
        db_ok = bool(row and int(row["ok"] or 0) == 1)

        async with db.execute("SELECT COUNT(*) AS c FROM users") as cur:
            users_row = await cur.fetchone()
        async with db.execute("SELECT COUNT(*) AS c FROM word_progress") as cur:
            progress_row = await cur.fetchone()
        async with db.execute("SELECT COUNT(*) AS c FROM sessions") as cur:
            sessions_row = await cur.fetchone()
        async with db.execute("SELECT COUNT(*) AS c FROM story_history") as cur:
            stories_row = await cur.fetchone()
        async with db.execute("SELECT COUNT(*) AS c FROM memory_palace_history") as cur:
            palaces_row = await cur.fetchone()

    return {
        "db_ok": db_ok,
        "users": int((users_row["c"] if users_row else 0) or 0),
        "word_progress": int((progress_row["c"] if progress_row else 0) or 0),
        "sessions": int((sessions_row["c"] if sessions_row else 0) or 0),
        "story_history": int((stories_row["c"] if stories_row else 0) or 0),
        "memory_palace_history": int((palaces_row["c"] if palaces_row else 0) or 0),
    }


async def get_all_users(limit: int = 200) -> list[dict]:
    safe_limit = max(1, min(int(limit or 200), 1000))
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            """
            SELECT
                u.user_id,
                u.username,
                u.joined_at,
                u.last_active,
                u.streak,
                u.daily_count,
                u.user_level,
                COALESCE(u.banned, 0) AS banned,
                u.ban_reason
            FROM users u
            ORDER BY COALESCE(u.last_active, u.joined_at) DESC, u.user_id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def get_all_user_ids() -> list[int]:
    async with _db_connect() as db:
        async with db.execute("SELECT user_id FROM users ORDER BY user_id ASC") as cur:
            rows = await cur.fetchall()
    return [int(r[0]) for r in rows]


async def get_top_leaderboard(limit: int = 10) -> list[dict]:
    safe_limit = max(1, min(int(limit or 10), 50))
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            """
            SELECT
                u.user_id,
                u.username,
                u.streak,
                u.user_level,
                COALESCE(SUM(wp.marked_know), 0) AS learned_count,
                COALESCE(SUM(wp.correct), 0) AS total_correct,
                COALESCE(SUM(wp.wrong), 0) AS total_wrong
            FROM users u
            LEFT JOIN word_progress wp ON wp.user_id = u.user_id
            GROUP BY u.user_id, u.username, u.streak, u.user_level
            ORDER BY learned_count DESC, total_correct DESC, u.streak DESC, u.user_id ASC
            LIMIT ?
            """,
            (safe_limit,),
        ) as cur:
            rows = await cur.fetchall()

    out: list[dict] = []
    for r in rows:
        total_correct = int(r["total_correct"] or 0)
        total_wrong = int(r["total_wrong"] or 0)
        total_answers = total_correct + total_wrong
        out.append(
            {
                "user_id": int(r["user_id"]),
                "username": r["username"] or "",
                "streak": int(r["streak"] or 0),
                "user_level": r["user_level"] or "A1",
                "learned_count": int(r["learned_count"] or 0),
                "accuracy": round(total_correct * 100 / total_answers) if total_answers else 0,
            }
        )
    return out


async def is_banned(user_id: int) -> bool:
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            "SELECT COALESCE(banned, 0) AS banned FROM users WHERE user_id = ?",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
    return bool(row and int(row["banned"] or 0) == 1)


async def find_user_id_by_username(username: str) -> int | None:
    clean = (username or "").strip().lstrip("@")
    if not clean:
        return None
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            """
            SELECT user_id
            FROM users
            WHERE lower(COALESCE(username, '')) = lower(?)
            ORDER BY COALESCE(last_active, joined_at) DESC
            LIMIT 1
            """,
            (clean,),
        ) as cur:
            row = await cur.fetchone()
    return int(row["user_id"]) if row else None


async def set_user_ban(user_id: int, banned: bool, reason: str = "") -> bool:
    reason = (reason or "").strip()[:300]
    async with _db_connect() as db:
        cur = await db.execute(
            """
            UPDATE users
            SET banned = ?, ban_reason = CASE WHEN ? = 1 THEN ? ELSE NULL END
            WHERE user_id = ?
            """,
            (1 if banned else 0, 1 if banned else 0, reason, user_id),
        )
        await db.commit()
    return (cur.rowcount or 0) > 0


async def log_admin_action(
    actor_user_id: int,
    action: str,
    *,
    target_user_id: int | None = None,
    details: str = "",
    metadata: dict | None = None,
) -> int:
    now = datetime.now().isoformat()
    meta_json = json.dumps(metadata or {}, ensure_ascii=False)
    safe_action = (action or "unknown").strip()[:80] or "unknown"
    safe_details = (details or "").strip()[:2000]

    async with _db_connect() as db:
        sql = (
            f"""
            INSERT INTO {ADMIN_AUDIT_TABLE}
                (actor_user_id, target_user_id, action, details, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """
        )
        sql += " RETURNING id"
        cur = await db.execute(
            sql,
            (int(actor_user_id), target_user_id, safe_action, safe_details, meta_json, now),
        )
        await db.commit()
        row = await cur.fetchone()
        return int((row["id"] if row else 0) or 0)


async def get_admin_audit_logs(limit: int = 20) -> list[dict]:
    safe_limit = max(1, min(int(limit or 20), 200))
    async with _db_connect() as db:
        db.row_factory = asyncpg.Record
        async with db.execute(
            f"""
            SELECT id, actor_user_id, target_user_id, action, details, metadata_json, created_at
            FROM {ADMIN_AUDIT_TABLE}
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ) as cur:
            rows = await cur.fetchall()
    out: list[dict] = []
    for r in rows:
        d = dict(r)
        try:
            d["metadata"] = json.loads(d.get("metadata_json") or "{}")
        except Exception:
            d["metadata"] = {}
        out.append(d)
    return out
