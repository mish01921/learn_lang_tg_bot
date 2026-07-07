import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import unquote

from sqlalchemy import (
    BigInteger,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    asc,
    case,
    delete,
    desc,
    func,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.core.config import DATABASE_URL


def _is_sqlite_dsn(dsn: str) -> bool:
    if not dsn:
        return True
    return dsn.startswith("sqlite") or "://" not in dsn


def _sqlite_path_from_dsn(dsn: str) -> str:
    if not dsn or dsn == "sqlite:///:memory:":
        return ":memory:"
    if dsn.startswith("sqlite:///"):
        path = dsn[len("sqlite:///") :]
    elif dsn.startswith("sqlite://"):
        path = dsn[len("sqlite://") :]
    else:
        path = dsn
    return unquote(path)


ADMIN_AUDIT_TABLE = "admin_audit_log" if _is_sqlite_dsn(DATABASE_URL) else "admin.audit_log"
ADMIN_SETTINGS_TABLE = "admin_settings" if _is_sqlite_dsn(DATABASE_URL) else "admin.settings"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(Text, nullable=True)
    joined_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    last_active: Mapped[str | None] = mapped_column(Text, nullable=True)
    daily_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    daily_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(Text, nullable=True, default='hy')
    banned: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    ban_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    placement_done: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    placement_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    placement_taken_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    study_plan: Mapped[str] = mapped_column(Text, default='steady')
    daily_goal: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default=text("5"))
    daily_pomodoro_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    daily_practice_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    last_failed_test_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_failed_test_level: Mapped[str | None] = mapped_column(Text, nullable=True)


class WordProgress(Base):
    __tablename__ = "word_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "word", name="uq_word_progress_user_word"),
        Index("idx_progress_user", "user_id"),
        Index("idx_progress_review", "user_id", "next_review"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    word: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    correct_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    wrong: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    learned: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    marked_hard: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    marked_know: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    added_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    learned_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_review: Mapped[str | None] = mapped_column(Text, nullable=True)
    ease_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.5, server_default=text("2.5"))
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    last_reviewed_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_grade: Mapped[str | None] = mapped_column(Text, nullable=True)


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (Index("idx_sessions_user", "user_id"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    word: Mapped[str] = mapped_column(Text, nullable=False)
    answered_at: Mapped[str] = mapped_column(Text, nullable=False)
    correct: Mapped[int] = mapped_column(Integer, nullable=False)


class StoryHistory(Base):
    __tablename__ = "story_history"
    __table_args__ = (Index("idx_story_user_date", "user_id", "story_date"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    story_date: Mapped[str] = mapped_column(Text, nullable=False)
    genre: Mapped[str] = mapped_column(Text, nullable=False)
    words_json: Mapped[str] = mapped_column(Text, nullable=False)
    story_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


class MemoryPalaceHistory(Base):
    __tablename__ = "memory_palace_history"
    __table_args__ = (Index("idx_palace_user_date", "user_id", "palace_date"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    palace_date: Mapped[str] = mapped_column(Text, nullable=False)
    theme: Mapped[str] = mapped_column(Text, nullable=False)
    words_json: Mapped[str] = mapped_column(Text, nullable=False)
    palace_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


class WordAudioCache(Base):
    __tablename__ = "word_audio_cache"

    word: Mapped[str] = mapped_column(Text, primary_key=True)
    file_id: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


class AuditLog(Base):
    __tablename__ = "admin_audit_log" if _is_sqlite_dsn(DATABASE_URL) else "audit_log"
    __table_args__ = {"schema": None if _is_sqlite_dsn(DATABASE_URL) else "admin"}

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    target_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


class Setting(Base):
    __tablename__ = "admin_settings" if _is_sqlite_dsn(DATABASE_URL) else "settings"
    __table_args__ = {"schema": None if _is_sqlite_dsn(DATABASE_URL) else "admin"}

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)


_async_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db_pool():
    global _async_engine, _async_session_factory
    if _async_engine is not None:
        return
    url = DATABASE_URL
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://").replace("postgresql://", "postgresql+asyncpg://")
    elif _is_sqlite_dsn(url):
        if url.startswith("sqlite://"):
            url = url.replace("sqlite://", "sqlite+aiosqlite://")
        else:
            url = f"sqlite+aiosqlite:///{url}"

    if _is_sqlite_dsn(DATABASE_URL):
        _async_engine = create_async_engine(url, echo=False)
    else:
        _async_engine = create_async_engine(url, pool_size=20, max_overflow=0, echo=False)

    _async_session_factory = async_sessionmaker(_async_engine, expire_on_commit=False, class_=AsyncSession)


async def close_db_pool():
    global _async_engine, _async_session_factory
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        _async_session_factory = None


class _Record(dict):
    def __init__(self, row, mapping):
        super().__init__(mapping)
        self._row = row

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._row[key]
        return super().__getitem__(key)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key) from None


class _CursorWrapper:
    def __init__(self, result):
        self._result = result
        self.rowcount = result.rowcount

    def _wrap_row(self, row):
        if row is None:
            return None
        return _Record(row, row._mapping)

    async def fetchone(self):
        return self._wrap_row(self._result.first())

    async def fetchall(self):
        return [self._wrap_row(r) for r in self._result.all()]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class _ExecuteWrapper:
    def __init__(self, session, statement, params=None):
        self._session = session
        self._statement = statement
        self._params = params

    def __await__(self):
        return self._run().__await__()

    async def _run(self):
        if self._params is not None:
            return await self._session.execute(self._statement, self._params)
        return await self._session.execute(self._statement)

    async def __aenter__(self):
        res = await self._run()
        return _CursorWrapper(res)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class _AsyncSessionContext:
    def __init__(self, session: AsyncSession):
        self._session = session
        self.row_factory = None

    def execute(self, statement: Any, params: Any = None) -> Any:
        if isinstance(statement, str):
            if params is not None and isinstance(params, (tuple, list)) and (not params or not isinstance(params[0], dict)):
                new_params = {}
                parts = statement.split("?")
                new_stmt = []
                for i in range(len(parts) - 1):
                    new_stmt.append(parts[i])
                    param_name = f"p_{i}"
                    new_stmt.append(f":{param_name}")
                    new_params[param_name] = params[i]
                new_stmt.append(parts[-1])
                statement = "".join(new_stmt)
                params = new_params
            statement = text(statement)
        return _ExecuteWrapper(self._session, statement, params)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def close(self) -> None:
        await self._session.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session, name)


@asynccontextmanager
async def _db_connect():
    if _async_session_factory is None:
        await init_db_pool()
    assert _async_session_factory is not None
    async with _async_session_factory() as session:
        wrapper = _AsyncSessionContext(session)
        try:
            yield wrapper
            await session.commit()
        except Exception:
            await session.rollback()
            raise



async def init_db():
    """Initializes the database schema."""
    await init_db_pool()
    assert _async_engine is not None
    if _is_sqlite_dsn(DATABASE_URL):
        async with _async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        import alembic.command
        import alembic.config
        def run_upgrade():
            alembic_cfg = alembic.config.Config("alembic.ini")
            try:
                alembic.command.upgrade(alembic_cfg, "head")
            except Exception as e:
                # If tables already exist (e.g. in existing Docker volume), stamp as head
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    alembic.command.stamp(alembic_cfg, "head")
                else:
                    raise

        await asyncio.to_thread(run_upgrade)

    # Ensure language, study_plan, daily_pomodoro_count, and daily_practice_count columns exist on existing database schema
    try:
        async with _db_connect() as db:
            if _is_sqlite_dsn(DATABASE_URL):
                for col, def_val in [("language", "'hy'"), ("study_plan", "'steady'"), ("daily_goal", "5"), ("daily_pomodoro_count", "0"), ("daily_practice_count", "0")]:
                    try:
                        sql_type = "TEXT" if col in ("language", "study_plan") else "INTEGER"
                        await db.execute(text(f"ALTER TABLE users ADD COLUMN {col} {sql_type} DEFAULT {def_val};"))
                    except Exception:
                        pass
            else:
                await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'hy';"))
                await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS study_plan TEXT DEFAULT 'steady';"))
                await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_goal INTEGER DEFAULT 5;"))
                await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_pomodoro_count INTEGER DEFAULT 0;"))
                await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_practice_count INTEGER DEFAULT 0;"))
    except Exception:
        pass


async def clear_all_tables():
    """Clear all tables (for test suites)."""
    async with _db_connect() as db:
        for model in [Session, WordProgress, StoryHistory, MemoryPalaceHistory, WordAudioCache, AuditLog, Setting, User]:
            await db.execute(delete(model))
        await db.commit()



async def _insert_ignore(db: _AsyncSessionContext, model: Any, values: dict, index_elements: list[str] | None = None):
    if _is_sqlite_dsn(DATABASE_URL):
        stmt = sqlite_insert(model).values(**values).on_conflict_do_nothing(index_elements=index_elements)
    else:
        stmt = pg_insert(model).values(**values).on_conflict_do_nothing(index_elements=index_elements)
    await db.execute(stmt)


async def ensure_user(user_id: int, username: str = ""):
    now = datetime.now().isoformat()
    today = datetime.now().date().isoformat()
    safe_username = (username or "").strip()[:64]
    async with _db_connect() as db:
        await _insert_ignore(
            db,
            User,
            {"user_id": user_id, "username": safe_username, "joined_at": now, "daily_date": today, "language": "hy"},
            index_elements=["user_id"],
        )
        if safe_username:
            await db.execute(
                update(User)
                .where(User.user_id == user_id, func.coalesce(User.username, "") != safe_username)
                .values(username=safe_username)
            )
        res = await db.execute(select(User.language).where(User.user_id == user_id))
        row = res.first()
        if row and row[0]:
            from src.core.app_state import user_language
            user_language[user_id] = row[0]
    await update_streak(user_id)


async def set_user_language_db(user_id: int, lang: str):
    if lang not in {"hy", "ru", "en"}:
        return
    async with _db_connect() as db:
        await db.execute(update(User).where(User.user_id == user_id).values(language=lang))


async def get_user_language_db(user_id: int) -> str:
    async with _db_connect() as db:
        res = await db.execute(select(User.language).where(User.user_id == user_id))
        row = res.first()
        return row[0] if row and row[0] else "hy"


async def update_streak(user_id: int):
    async with _db_connect() as db:
        res = await db.execute(select(User.streak, User.last_active).where(User.user_id == user_id))
        row = res.first()
        if not row:
            return

        streak, last_active_str = row[0], row[1]
        now = datetime.now()
        today = now.date()

        if not last_active_str:
            await db.execute(
                update(User).where(User.user_id == user_id).values(streak=1, last_active=now.isoformat())
            )
            return

        last = datetime.fromisoformat(last_active_str).date()
        if last == today:
            await db.execute(
                update(User).where(User.user_id == user_id).values(last_active=now.isoformat())
            )
            return

        if (today - last).days == 1:
            new_streak = streak + 1
        elif (today - last).days > 1:
            new_streak = 1
        else:
            new_streak = streak

        await db.execute(
            update(User).where(User.user_id == user_id).values(streak=new_streak, last_active=now.isoformat())
        )


# Plan → default daily goal mapping
PLAN_DEFAULT_GOALS = {"lite": 3, "steady": 5, "deep": 15}


async def set_user_plan(user_id: int, plan: str, custom_goal: int | None = None):
    """Set study plan. If custom_goal is provided it overrides the plan default."""
    if plan not in {"lite", "steady", "deep", "custom"}:
        return
    if plan == "custom":
        goal = max(1, min(30, int(custom_goal or 5)))
    else:
        goal = PLAN_DEFAULT_GOALS.get(plan, 5)
        if custom_goal is not None:
            goal = max(1, min(30, int(custom_goal)))
    async with _db_connect() as db:
        await db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(study_plan=plan, daily_goal=goal)
        )


async def get_user_plan(user_id: int) -> str:
    async with _db_connect() as db:
        res = await db.execute(select(User.study_plan).where(User.user_id == user_id))
        row = res.first()
    return row[0] if row and row[0] else "steady"


async def get_daily_limit(user_id: int) -> int:
    """Return the user's personal daily word goal (falls back to 5)."""
    from src.core.config import DAILY_LIMIT
    async with _db_connect() as db:
        res = await db.execute(select(User.daily_goal).where(User.user_id == user_id))
        row = res.first()
    val = row[0] if row and row[0] is not None else None
    return int(val) if val and val > 0 else DAILY_LIMIT


async def set_daily_goal(user_id: int, goal: int):
    """Directly set a custom daily word goal (1–30) without changing the plan tier."""
    goal = max(1, min(30, goal))
    async with _db_connect() as db:
        await db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(daily_goal=goal, study_plan="custom")
        )


# ═══════════════════════════════════════════════════════
# DAILY COUNT
# ═══════════════════════════════════════════════════════

async def get_daily_count(user_id: int) -> int:
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        res = await db.execute(select(User.daily_count, User.daily_date).where(User.user_id == user_id))
        row = res.first()
        if not row:
            return 0
        daily_count, daily_date = row[0], row[1]
        if daily_date != today:
            await db.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(daily_count=0, daily_pomodoro_count=0, daily_practice_count=0, daily_date=today)
            )
            return 0
        return daily_count or 0


async def increment_daily(user_id: int, word: str | None = None):
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        should_increment = True
        if word:
            res = await db.execute(
                select(func.count(Session.id)).where(
                    Session.user_id == user_id,
                    Session.word == word,
                    func.substr(Session.answered_at, 1, 10) == today,
                )
            )
            cnt = res.scalar() or 0
            should_increment = cnt <= 1

        if should_increment:
            await db.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(
                    daily_count=case((User.daily_date == today, User.daily_count + 1), else_=1),
                    daily_date=today,
                )
            )
        else:
            await db.execute(
                update(User)
                .where(User.user_id == user_id, User.daily_date.is_(None))
                .values(daily_date=today)
            )


async def get_daily_pomodoro_count(user_id: int) -> int:
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        res = await db.execute(select(User.daily_pomodoro_count, User.daily_date).where(User.user_id == user_id))
        row = res.first()
        if not row:
            return 0
        daily_count, daily_date = row[0], row[1]
        if daily_date != today:
            await db.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(daily_count=0, daily_pomodoro_count=0, daily_practice_count=0, daily_date=today)
            )
            return 0
        return daily_count or 0


async def increment_daily_pomodoro(user_id: int):
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        await db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(
                daily_pomodoro_count=case((User.daily_date == today, User.daily_pomodoro_count + 1), else_=1),
                daily_date=today,
            )
        )


async def get_daily_practice_count(user_id: int) -> int:
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        res = await db.execute(select(User.daily_practice_count, User.daily_date).where(User.user_id == user_id))
        row = res.first()
        if not row:
            return 0
        daily_count, daily_date = row[0], row[1]
        if daily_date != today:
            await db.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(daily_count=0, daily_pomodoro_count=0, daily_practice_count=0, daily_date=today)
            )
            return 0
        return daily_count or 0


async def increment_daily_practice(user_id: int):
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        await db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(
                daily_practice_count=case((User.daily_date == today, User.daily_practice_count + 1), else_=1),
                daily_date=today,
            )
        )


# ═══════════════════════════════════════════════════════
# USER LEVEL
# ═══════════════════════════════════════════════════════

async def set_user_level(user_id: int, level: str):
    level = (level or "").upper()
    if level not in {"A1", "A2", "B1", "B2"}:
        return
    async with _db_connect() as db:
        await db.execute(update(User).where(User.user_id == user_id).values(user_level=level))


async def get_user_level(user_id: int) -> str:
    async with _db_connect() as db:
        res = await db.execute(select(User.user_level).where(User.user_id == user_id))
        return res.scalar() or "A1"


async def record_failed_level_test(user_id: int, target_level: str):
    async with _db_connect() as db:
        today = datetime.now().strftime("%Y-%m-%d")
        await db.execute(
            update(User).where(User.user_id == user_id).values(
                last_failed_test_date=today,
                last_failed_test_level=target_level
            )
        )
        await db.commit()


async def can_take_level_test(user_id: int, target_level: str) -> bool:
    async with _db_connect() as db:
        res = await db.execute(
            select(User.last_failed_test_date, User.last_failed_test_level)
            .where(User.user_id == user_id)
        )
        row = res.first()
        if not row:
            return True
        today = datetime.now().strftime("%Y-%m-%d")
        last_date, last_level = row[0], row[1]
        if last_date == today and last_level == target_level:
            return False
        return True


async def is_placement_done(user_id: int) -> bool:
    async with _db_connect() as db:
        res = await db.execute(select(func.coalesce(User.placement_done, 0)).where(User.user_id == user_id))
        row = res.first()
    return bool(row and int(row[0] or 0) == 1)


async def set_placement_result(user_id: int, level: str, score: int) -> bool:
    level = (level or "A1").upper()
    if level not in {"A1", "A2", "B1", "B2"}:
        level = "A1"
    now = datetime.now().isoformat()
    async with _db_connect() as db:
        res = await db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(placement_done=1, placement_score=int(score or 0), placement_taken_at=now, user_level=level)
        )
    return (res.rowcount or 0) > 0



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

        # 1. Marked hard + due (NULL next_review considered due)
        if include_hard_due:
            res = await db.execute(
                select(WordProgress.word)
                .where(
                    WordProgress.user_id == user_id,
                    WordProgress.marked_hard == 1,
                    (WordProgress.next_review.is_(None)) | (WordProgress.next_review <= today),
                    WordProgress.word.in_(filtered_allowed),
                )
                .order_by(asc(WordProgress.next_review))
                .limit(1)
            )
            word = res.scalar()
            if word:
                return word

        # 2. Due words (explicitly require non-NULL next_review)
        res = await db.execute(
            select(WordProgress.word)
            .where(
                WordProgress.user_id == user_id,
                WordProgress.marked_hard == 0,
                WordProgress.next_review.is_not(None),
                WordProgress.next_review <= today,
                WordProgress.word.in_(filtered_allowed),
            )
            .order_by(asc(WordProgress.next_review))
            .limit(1)
        )
        word = res.scalar()
        if word:
            return word

        # 3. New words
        res = await db.execute(select(WordProgress.word).where(WordProgress.user_id == user_id))
        seen = {row[0] for row in res}
        new_words = [w for w in filtered_allowed if w not in seen]
        if new_words:
            return random.choice(new_words)

        # 4. Oldest next_review (treat NULLs as last)
        res = await db.execute(
            select(WordProgress.word)
            .where(WordProgress.user_id == user_id, WordProgress.word.in_(filtered_allowed))
            .order_by(asc(WordProgress.next_review.is_(None)), asc(WordProgress.next_review))
            .limit(1)
        )
        word = res.scalar()
        if word:
            return word
        return filtered_allowed[0] if filtered_allowed else all_words[0]


async def get_word_reason(user_id: int, word: str) -> str:
    """Return a short human-readable reason why this word is shown now."""
    if not word:
        return "Նոր բառ՝ շարունակելու համար։"

    now = datetime.now().isoformat()
    async with _db_connect() as db:
        res = await db.execute(
            select(
                WordProgress.seen,
                WordProgress.marked_hard,
                WordProgress.next_review,
                WordProgress.correct,
                WordProgress.wrong,
            ).where(WordProgress.user_id == user_id, WordProgress.word == word)
        )
        row = res.first()

    if not row:
        return "Նոր բառ է ձեր ծրագրում։"
    seen, marked_hard, next_review, correct, wrong = row[0], row[1], row[2], row[3], row[4]
    if (marked_hard or 0) == 1:
        return "Նշված էր «Կրկնել», դրա համար կրկին ցույց է տրվում։"
    if next_review and next_review <= now:
        return "Կրկնության ժամկետը եկել է։"
    if (seen or 0) <= 1:
        return "Նոր կամ քիչ տեսած բառ է՝ ամրապնդման համար։"
    if (wrong or 0) > (correct or 0):
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
        await _insert_ignore(
            db,
            WordProgress,
            {"user_id": user_id, "word": word, "added_at": now},
            index_elements=["user_id", "word"],
        )

        res = await db.execute(
            select(
                WordProgress.level,
                WordProgress.correct,
                WordProgress.correct_streak,
                WordProgress.wrong,
                WordProgress.marked_hard,
                WordProgress.marked_know,
                WordProgress.ease_factor,
                WordProgress.interval_days,
                WordProgress.repetitions,
            ).where(WordProgress.user_id == user_id, WordProgress.word == word)
        )
        entry = res.first()
        if not entry:
            return

        level = entry[0]
        new_correct = entry[1] + (1 if correct else 0)
        new_wrong = entry[3] + (0 if correct else 1)
        new_correct_streak = entry[2] + 1 if correct else 0

        if correct:
            level = min(level + 1, 3)
        else:
            level = max(level - 1, 0)

        grade_norm = (grade or "").strip().lower()
        if not grade_norm:
            grade_norm = "hard" if (correct and marked_hard) else ("again" if not correct else "good")

        new_marked_know = 1 if grade_norm in {"good", "easy"} else entry[5]
        if grade_norm in {"again", "hard"}:
            new_marked_hard = 1
        elif grade_norm in {"good", "easy"}:
            new_marked_hard = 0
        else:
            new_marked_hard = 0 if correct else (1 if marked_hard else entry[4])

        learned_at = now if grade_norm in {"good", "easy"} else None

        ef, srs_interval_days, srs_repetitions = _srs_schedule(
            correct=correct,
            marked_hard=marked_hard,
            grade=grade_norm,
            ease_factor=float(entry[6] if entry[6] is not None else 2.5),
            interval_days=int(entry[7] or 0),
            repetitions=int(entry[8] or 0),
        )
        days = max(INTERVALS[level], srs_interval_days)
        next_review = (datetime.now() + timedelta(days=days)).isoformat()

        await db.execute(
            update(WordProgress)
            .where(WordProgress.user_id == user_id, WordProgress.word == word)
            .values(
                level=level,
                seen=WordProgress.seen + 1,
                correct=new_correct,
                correct_streak=new_correct_streak,
                wrong=new_wrong,
                marked_hard=new_marked_hard,
                marked_know=new_marked_know,
                learned_at=func.coalesce(learned_at, WordProgress.learned_at),
                next_review=next_review,
                ease_factor=ef,
                interval_days=days,
                repetitions=srs_repetitions,
                last_reviewed_at=now,
                last_grade=grade_norm,
            )
        )

        await db.execute(
            insert(Session).values(user_id=user_id, word=word, answered_at=now, correct=1 if correct else 0)
        )



# ═══════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════

async def get_stats(user_id: int, total_words: int) -> dict:
    async with _db_connect() as db:
        today = datetime.now().isoformat()

        res = await db.execute(
            text("""
                SELECT
                    COUNT(*) as seen,
                    COALESCE(SUM(marked_know), 0) as learned,
                    COALESCE(SUM(marked_hard), 0) as hard,
                    COALESCE(SUM(correct), 0) as total_correct,
                    COALESCE(SUM(wrong), 0) as total_wrong,
                    COALESCE(SUM(CASE WHEN marked_hard=1 AND next_review <= :today THEN 1 ELSE 0 END), 0) as due_today
                FROM word_progress WHERE user_id = :user_id
            """),
            {"today": today, "user_id": user_id},
        )
        s = res.mappings().first()

        res_u = await db.execute(select(User.streak).where(User.user_id == user_id))
        streak = res_u.scalar() or 0

    seen = int(s["seen"] or 0) if s else 0
    learned = int(s["learned"] or 0) if s else 0
    total_correct = int(s["total_correct"] or 0) if s else 0
    total_wrong = int(s["total_wrong"] or 0) if s else 0
    total_answers = total_correct + total_wrong

    return {
        "total": total_words,
        "seen": seen,
        "unseen": total_words - seen,
        "learned": learned,
        "hard": int(s["hard"] or 0) if s else 0,
        "due_today": int(s["due_today"] or 0) if s else 0,
        "accuracy": round(total_correct / total_answers * 100) if total_answers else 0,
        "progress_pct": round(learned / total_words * 100, 1),
        "streak": streak,
    }


async def get_hard_words(user_id: int) -> list[dict]:
    """Կրկնել սեղմած բառերը (Words marked as hard)."""
    async with _db_connect() as db:
        res = await db.execute(
            select(
                WordProgress.word,
                WordProgress.wrong,
                WordProgress.correct,
                WordProgress.added_at,
                WordProgress.last_grade,
            )
            .where(WordProgress.user_id == user_id, WordProgress.marked_hard == 1)
            .order_by(desc(WordProgress.added_at))
        )
        return [dict(r) for r in res.mappings().all()]


async def get_seen_words(user_id: int, limit: int = 300) -> list[str]:
    """Return words that user has already seen at least once."""
    async with _db_connect() as db:
        res = await db.execute(
            select(WordProgress.word)
            .where(WordProgress.user_id == user_id, WordProgress.seen > 0)
            .order_by(desc(WordProgress.added_at))
            .limit(limit)
        )
        return [r[0] for r in res.all()]


async def get_today_answered_words(user_id: int, limit: int = 10) -> list[str]:
    today = datetime.now().date().isoformat()
    safe_limit = max(1, min(int(limit or 10), 30))
    async with _db_connect() as db:
        res = await db.execute(
            select(Session.word)
            .where(Session.user_id == user_id, func.substr(Session.answered_at, 1, 10) == today)
            .order_by(desc(Session.id))
            .limit(200)
        )
        rows = res.all()

    out: list[str] = []
    seen: set[str] = set()
    for r in rows:
        w = (r[0] or "").strip().lower()
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
        res = await db.execute(
            insert(StoryHistory).values(
                user_id=user_id,
                story_date=story_date,
                genre=(genre or "general")[:40],
                words_json=words_json,
                story_text=story_text,
                created_at=now,
            )
        )
        return int(res.inserted_primary_key[0] if res.inserted_primary_key else 0)


async def count_story_generations_today(user_id: int) -> int:
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        res = await db.execute(
            select(func.count()).where(StoryHistory.user_id == user_id, StoryHistory.story_date == today)
        )
        return int(res.scalar() or 0)


async def get_story_history(user_id: int, limit: int = 5) -> list[dict]:
    safe_limit = max(1, min(int(limit or 5), 20))
    async with _db_connect() as db:
        res = await db.execute(
            select(
                StoryHistory.story_date,
                StoryHistory.genre,
                StoryHistory.words_json,
                StoryHistory.story_text,
                StoryHistory.created_at,
            )
            .where(StoryHistory.user_id == user_id)
            .order_by(desc(StoryHistory.id))
            .limit(safe_limit)
        )
        rows = res.mappings().all()
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
        res = await db.execute(
            insert(MemoryPalaceHistory).values(
                user_id=user_id,
                palace_date=palace_date,
                theme=(theme or "general")[:40],
                words_json=words_json,
                palace_text=palace_text,
                created_at=now,
            )
        )
        return int(res.inserted_primary_key[0] if res.inserted_primary_key else 0)


async def count_palace_generations_today(user_id: int) -> int:
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        res = await db.execute(
            select(func.count()).where(MemoryPalaceHistory.user_id == user_id, MemoryPalaceHistory.palace_date == today)
        )
        return int(res.scalar() or 0)


async def get_memory_palace_history(user_id: int, limit: int = 5) -> list[dict]:
    safe_limit = max(1, min(int(limit or 5), 20))
    async with _db_connect() as db:
        res = await db.execute(
            select(
                MemoryPalaceHistory.palace_date,
                MemoryPalaceHistory.theme,
                MemoryPalaceHistory.words_json,
                MemoryPalaceHistory.palace_text,
                MemoryPalaceHistory.created_at,
            )
            .where(MemoryPalaceHistory.user_id == user_id)
            .order_by(desc(MemoryPalaceHistory.id))
            .limit(safe_limit)
        )
        rows = res.mappings().all()
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
        await _insert_ignore(db, WordProgress, {"user_id": user_id, "word": word, "added_at": now})
        res = await db.execute(
            update(WordProgress)
            .where(WordProgress.user_id == user_id, WordProgress.word == word)
            .values(
                marked_hard=0,
                marked_know=1,
                learned=1,
                learned_at=func.coalesce(WordProgress.learned_at, now),
                last_grade="good",
            )
        )
        await db.commit()
        return (res.rowcount or 0) > 0


async def get_top_weak_words(user_id: int, limit: int = 3) -> list[dict]:
    """Words with the highest error pressure."""
    async with _db_connect() as db:
        res = await db.execute(
            select(WordProgress.word, WordProgress.wrong, WordProgress.correct)
            .where(WordProgress.user_id == user_id, WordProgress.wrong > 0)
            .order_by(desc(WordProgress.wrong - WordProgress.correct), desc(WordProgress.wrong))
            .limit(limit)
        )
        return [dict(r) for r in res.mappings().all()]


async def get_wordset_progress(user_id: int, words: list[str]) -> dict:
    if not words:
        return {"total": 0, "learned": 0, "accuracy": 0}
    uniq = list(dict.fromkeys(w.strip() for w in words if (w or "").strip()))
    if not uniq:
        return {"total": 0, "learned": 0, "accuracy": 0}
    async with _db_connect() as db:
        res1 = await db.execute(
            select(func.coalesce(func.sum(WordProgress.marked_know), 0).label("learned"))
            .where(WordProgress.user_id == user_id, WordProgress.word.in_(uniq))
        )
        learned = int(res1.scalar() or 0)

        res2 = await db.execute(
            select(
                func.coalesce(func.sum(WordProgress.correct), 0).label("total_correct"),
                func.coalesce(func.sum(WordProgress.wrong), 0).label("total_wrong"),
            )
            .where(WordProgress.user_id == user_id, WordProgress.word.in_(uniq))
        )
        row2 = res2.mappings().first()
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
        res = await db.execute(
            select(Session.correct)
            .where(Session.user_id == user_id)
            .order_by(desc(Session.id))
            .limit(limit)
        )
        rows = res.all()

    if not rows:
        return 0
    total = len(rows)
    ok = sum(int(r[0] or 0) for r in rows)
    return round(ok * 100 / total)


async def get_recent_accuracy_window(user_id: int, limit: int = 20, offset: int = 0) -> int | None:
    """Accuracy for a window of latest answers (supports OFFSET). Returns None if window is empty."""
    async with _db_connect() as db:
        res = await db.execute(
            select(Session.correct)
            .where(Session.user_id == user_id)
            .order_by(desc(Session.id))
            .limit(limit)
            .offset(offset)
        )
        rows = res.all()

    if not rows:
        return None
    total = len(rows)
    ok = sum(int(r[0] or 0) for r in rows)
    return round(ok * 100 / total)


async def get_learned_words(user_id: int) -> list[dict]:
    """Գիտեմ սեղմած բառերը (Words marked as learned)."""
    async with _db_connect() as db:
        res = await db.execute(
            select(WordProgress.word, WordProgress.correct, WordProgress.learned_at, WordProgress.last_grade)
            .where(WordProgress.user_id == user_id, WordProgress.marked_know == 1)
            .order_by(desc(WordProgress.learned_at))
        )
        return [dict(r) for r in res.mappings().all()]


async def get_word_grade_map(user_id: int, words: list[str]) -> dict[str, str]:
    uniq = list(dict.fromkeys((w or "").strip().lower() for w in (words or []) if (w or "").strip()))
    if not uniq:
        return {}
    async with _db_connect() as db:
        res = await db.execute(
            select(
                WordProgress.word,
                func.coalesce(WordProgress.last_grade, "").label("last_grade"),
                WordProgress.marked_hard,
                WordProgress.marked_know,
                WordProgress.seen,
            )
            .where(WordProgress.user_id == user_id, WordProgress.word.in_(uniq))
        )
        rows = res.mappings().all()

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


async def reset_user_completely(user_id: int):
    async with _db_connect() as db:
        await db.execute(delete(WordProgress).where(WordProgress.user_id == user_id))
        await db.execute(delete(Session).where(Session.user_id == user_id))
        await db.execute(delete(StoryHistory).where(StoryHistory.user_id == user_id))
        await db.execute(delete(MemoryPalaceHistory).where(MemoryPalaceHistory.user_id == user_id))
        await db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(
                streak=0,
                last_active=None,
                daily_count=0,
                daily_date=None,
                placement_done=0,
                placement_score=0,
                placement_taken_at=None,
                study_plan="steady",
                daily_pomodoro_count=0,
                daily_practice_count=0,
                language="hy"
            )
        )
        await db.commit()


async def get_admin_overview() -> dict:
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        res1 = await db.execute(select(func.count()).select_from(User))
        total_users = int(res1.scalar() or 0)

        res2 = await db.execute(select(func.count()).select_from(User).where(func.substr(User.joined_at, 1, 10) == today))
        joined_today = int(res2.scalar() or 0)

        res3 = await db.execute(select(func.count()).select_from(User).where(func.substr(User.last_active, 1, 10) == today))
        active_today = int(res3.scalar() or 0)

        res4 = await db.execute(select(func.count()).select_from(WordProgress).where(WordProgress.learned == 1))
        learned_total = int(res4.scalar() or 0)

        res5 = await db.execute(
            text("""
                SELECT word, SUM(wrong) as total_wrong, SUM(correct) as total_correct
                FROM word_progress
                GROUP BY word
                HAVING SUM(wrong) > 0
                ORDER BY (SUM(wrong) - SUM(correct)) DESC
                LIMIT 5
            """)
        )
        difficult_words = [dict(r) for r in res5.mappings().all()]

        res6 = await db.execute(
            select(func.coalesce(User.user_level, "A1").label("lvl"), func.count().label("c"))
            .group_by(func.coalesce(User.user_level, "A1"))
            .order_by(asc("lvl"))
        )
        levels = {r.lvl: r.c for r in res6.all()}

    return {
        "total_users": total_users,
        "joined_today": joined_today,
        "active_today": active_today,
        "learned_total": learned_total,
        "difficult_words": difficult_words,
        "levels": levels
    }


async def get_user_daily_stats(user_id: int) -> dict:
    today = datetime.now().date().isoformat()
    async with _db_connect() as db:
        res1 = await db.execute(
            select(func.count()).where(Session.user_id == user_id, func.substr(Session.answered_at, 1, 10) == today)
        )
        answered_today = int(res1.scalar() or 0)

        res2 = await db.execute(
            select(func.count()).where(WordProgress.user_id == user_id, func.substr(WordProgress.learned_at, 1, 10) == today)
        )
        learned_today = int(res2.scalar() or 0)

        res3 = await db.execute(
            select(func.min(Session.answered_at).label("first"), func.max(Session.answered_at).label("last"))
            .where(Session.user_id == user_id, func.substr(Session.answered_at, 1, 10) == today)
        )
        row = res3.mappings().first()
        if row and row["first"] and row["last"]:
            start = datetime.fromisoformat(row["first"])
            end = datetime.fromisoformat(row["last"])
            diff = end - start
            minutes = round(diff.total_seconds() / 60)
        else:
            minutes = 0

    return {
        "answered_today": answered_today,
        "learned_today": learned_today,
        "minutes_today": minutes
    }


async def get_user_full_profile(user_id: int) -> dict | None:
    async with _db_connect() as db:
        res_u = await db.execute(select(User).where(User.user_id == user_id))
        user = res_u.scalar_one_or_none()
        if not user:
            return None

        res_p = await db.execute(
            select(
                func.count().label("seen"),
                func.coalesce(func.sum(WordProgress.marked_know), 0).label("learned"),
                func.coalesce(func.sum(WordProgress.marked_hard), 0).label("hard"),
                func.coalesce(func.sum(WordProgress.correct), 0).label("correct"),
                func.coalesce(func.sum(WordProgress.wrong), 0).label("wrong"),
            ).where(WordProgress.user_id == user_id)
        )
        prog = res_p.mappings().first()

        user_dict = {
            "user_id": user.user_id,
            "username": user.username or "",
            "joined_at": user.joined_at,
            "last_active": user.last_active,
            "streak": user.streak,
            "daily_count": user.daily_count,
            "daily_date": user.daily_date,
            "user_level": user.user_level,
            "banned": user.banned,
            "ban_reason": user.ban_reason,
            "user_plan": user.user_plan,
            "placement_done": user.placement_done,
            "placement_score": user.placement_score,
        }
        return {
            "info": user_dict,
            "stats": dict(prog) if prog else {}
        }


async def get_health_snapshot() -> dict:
    """Basic DB health check + key row counts for admin /health command."""
    async with _db_connect() as db:
        res_ok = await db.execute(select(1))
        db_ok = bool(res_ok.scalar() == 1)

        res_u = await db.execute(select(func.count()).select_from(User))
        res_wp = await db.execute(select(func.count()).select_from(WordProgress))
        res_s = await db.execute(select(func.count()).select_from(Session))
        res_sh = await db.execute(select(func.count()).select_from(StoryHistory))
        res_mp = await db.execute(select(func.count()).select_from(MemoryPalaceHistory))

    return {
        "db_ok": db_ok,
        "users": int(res_u.scalar() or 0),
        "word_progress": int(res_wp.scalar() or 0),
        "sessions": int(res_s.scalar() or 0),
        "story_history": int(res_sh.scalar() or 0),
        "memory_palace_history": int(res_mp.scalar() or 0),
    }


async def get_all_users(limit: int = 200) -> list[dict]:
    safe_limit = max(1, min(int(limit or 200), 1000))
    async with _db_connect() as db:
        res = await db.execute(
            select(
                User.user_id,
                User.username,
                User.joined_at,
                User.last_active,
                User.streak,
                User.daily_count,
                User.user_level,
                func.coalesce(User.banned, 0).label("banned"),
                User.ban_reason,
            )
            .order_by(desc(func.coalesce(User.last_active, User.joined_at)), desc(User.user_id))
            .limit(safe_limit)
        )
        return [dict(r) for r in res.mappings().all()]


async def get_all_user_ids() -> list[int]:
    async with _db_connect() as db:
        res = await db.execute(select(User.user_id).order_by(asc(User.user_id)))
        return [int(r[0]) for r in res.all()]


async def get_top_leaderboard(limit: int = 10) -> list[dict]:
    safe_limit = max(1, min(int(limit or 10), 50))
    async with _db_connect() as db:
        res = await db.execute(
            text("""
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
                LIMIT :safe_limit
            """),
            {"safe_limit": safe_limit},
        )
        rows = res.mappings().all()

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
        res = await db.execute(
            select(func.coalesce(User.banned, 0)).where(User.user_id == user_id)
        )
        val = res.scalar()
    return val == 1


async def find_user_id_by_username(username: str) -> int | None:
    clean = (username or "").strip().lstrip("@")
    if not clean:
        return None
    async with _db_connect() as db:
        res = await db.execute(
            select(User.user_id)
            .where(func.lower(func.coalesce(User.username, "")) == clean.lower())
            .order_by(desc(func.coalesce(User.last_active, User.joined_at)))
            .limit(1)
        )
        row = res.first()
    return int(row[0]) if row else None


async def set_user_ban(user_id: int, banned: bool, reason: str = "") -> bool:
    reason = (reason or "").strip()[:300]
    async with _db_connect() as db:
        res = await db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(
                banned=1 if banned else 0,
                ban_reason=reason if banned else None,
            )
        )
        await db.commit()
    return (res.rowcount or 0) > 0


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
        res = await db.execute(
            insert(AuditLog).values(
                actor_user_id=int(actor_user_id),
                target_user_id=target_user_id,
                action=safe_action,
                details=safe_details,
                metadata_json=meta_json,
                created_at=now,
            )
        )
        return int(res.inserted_primary_key[0] if res.inserted_primary_key else 0)


async def get_admin_audit_logs(limit: int = 20) -> list[dict]:
    safe_limit = max(1, min(int(limit or 20), 200))
    async with _db_connect() as db:
        res = await db.execute(
            select(
                AuditLog.id,
                AuditLog.actor_user_id,
                AuditLog.target_user_id,
                AuditLog.action,
                AuditLog.details,
                AuditLog.metadata_json,
                AuditLog.created_at,
            )
            .order_by(desc(AuditLog.id))
            .limit(safe_limit)
        )
        rows = res.mappings().all()
    out: list[dict] = []
    for r in rows:
        d = dict(r)
        try:
            d["metadata"] = json.loads(d.get("metadata_json") or "{}")
        except Exception:
            d["metadata"] = {}
        out.append(d)
    return out


# ═══════════════════════════════════════════════════════
# AUDIO CACHE
# ═══════════════════════════════════════════════════════

async def get_voice_file_id(word: str) -> str | None:
    async with _db_connect() as db:
        res = await db.execute(
            select(WordAudioCache.file_id).where(WordAudioCache.word == word.strip().lower())
        )
        return res.scalar_one_or_none()


async def save_voice_file_id(word: str, file_id: str):
    now = datetime.now().isoformat()
    async with _db_connect() as db:
        await _insert_ignore(db, WordAudioCache, {"word": word.strip().lower(), "file_id": file_id, "created_at": now})
        await db.execute(
            update(WordAudioCache)
            .where(WordAudioCache.word == word.strip().lower())
            .values(file_id=file_id, created_at=now)
        )
        await db.commit()
