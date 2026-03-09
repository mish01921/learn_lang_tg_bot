import argparse
import asyncio
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import asyncpg

from config import DATABASE_URL


TABLES_WITH_SERIAL_ID = [
    ("word_progress", "id"),
    ("sessions", "id"),
    ("story_history", "id"),
    ("memory_palace_history", "id"),
]


def _sqlite_rows(db_path: Path, table: str, columns: list[str]) -> list[tuple]:
    conn = sqlite3.connect(str(db_path))
    try:
        query = f"SELECT {', '.join(columns)} FROM {table}"
        cur = conn.execute(query)
        return cur.fetchall()
    finally:
        conn.close()


async def _copy_table(pg: asyncpg.Connection, db_path: Path, table: str, columns: list[str]):
    rows = _sqlite_rows(db_path, table, columns)
    if not rows:
        return
    placeholders = ", ".join(f"${i}" for i in range(1, len(columns) + 1))
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    await pg.executemany(sql, rows)
    return len(rows)


def _backup_sqlite(sqlite_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{sqlite_path.stem}.backup_{ts}{sqlite_path.suffix}"
    shutil.copy2(sqlite_path, backup_path)
    return backup_path


async def migrate(
    sqlite_path: Path,
    *,
    truncate: bool,
    backup: bool,
    backup_dir: Path,
):
    if not DATABASE_URL.startswith("postgresql"):
        raise RuntimeError("DATABASE_URL must be PostgreSQL for this migration script.")
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite DB not found: {sqlite_path}")

    backup_path: Path | None = None
    if backup:
        backup_path = _backup_sqlite(sqlite_path, backup_dir)
        print(f"[SAFEGUARD] SQLite backup created: {backup_path}")

    pg = await asyncpg.connect(DATABASE_URL)
    try:
        async with pg.transaction():
            if truncate:
                await pg.execute(
                    "TRUNCATE TABLE memory_palace_history, story_history, sessions, word_progress, users CASCADE"
                )
                print("[SAFEGUARD] Target Postgres tables truncated.")
            else:
                print("[SAFEGUARD] Running in append mode (no TRUNCATE).")

            copied_users = await _copy_table(
                pg,
                sqlite_path,
                "users",
                [
                    "user_id",
                    "username",
                    "joined_at",
                    "streak",
                    "last_active",
                    "daily_count",
                    "daily_date",
                    "user_level",
                    "banned",
                    "ban_reason",
                    "placement_done",
                    "placement_score",
                    "placement_taken_at",
                ],
            )

            copied_progress = await _copy_table(
                pg,
                sqlite_path,
                "word_progress",
                [
                    "id",
                    "user_id",
                    "word",
                    "level",
                    "seen",
                    "correct",
                    "correct_streak",
                    "wrong",
                    "learned",
                    "marked_hard",
                    "marked_know",
                    "added_at",
                    "learned_at",
                    "next_review",
                    "ease_factor",
                    "interval_days",
                    "repetitions",
                    "last_reviewed_at",
                    "last_grade",
                ],
            )

            copied_sessions = await _copy_table(
                pg,
                sqlite_path,
                "sessions",
                ["id", "user_id", "word", "answered_at", "correct"],
            )

            copied_stories = await _copy_table(
                pg,
                sqlite_path,
                "story_history",
                ["id", "user_id", "story_date", "genre", "words_json", "story_text", "created_at"],
            )

            copied_palaces = await _copy_table(
                pg,
                sqlite_path,
                "memory_palace_history",
                ["id", "user_id", "palace_date", "theme", "words_json", "palace_text", "created_at"],
            )

            for table, id_col in TABLES_WITH_SERIAL_ID:
                await pg.execute(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table}', '{id_col}'),
                        COALESCE((SELECT MAX({id_col}) FROM {table}), 1),
                        COALESCE((SELECT MAX({id_col}) FROM {table}), 0) > 0
                    )
                    """
                )
        print(
            "[REPORT] Copied rows -> "
            f"users={copied_users}, "
            f"word_progress={copied_progress}, "
            f"sessions={copied_sessions}, "
            f"story_history={copied_stories}, "
            f"memory_palace_history={copied_palaces}"
        )
    finally:
        await pg.close()


def main():
    parser = argparse.ArgumentParser(description="Migrate data from SQLite words_bot.db to PostgreSQL.")
    parser.add_argument(
        "--sqlite-path",
        default="words_bot.db",
        help="Path to SQLite database file (default: words_bot.db)",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate target Postgres tables before import. Disabled by default for safety.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Disable SQLite file backup before migration (not recommended).",
    )
    parser.add_argument(
        "--backup-dir",
        default="db_backups",
        help="Directory where SQLite backup is stored (default: db_backups).",
    )
    args = parser.parse_args()
    asyncio.run(
        migrate(
            Path(args.sqlite_path),
            truncate=bool(args.truncate),
            backup=not bool(args.no_backup),
            backup_dir=Path(args.backup_dir),
        )
    )
    print("Migration completed successfully.")


if __name__ == "__main__":
    main()
