import os
import tempfile
import unittest
from datetime import datetime, timedelta

import src.main as bot
import src.database.models as database
import src.data.level_words as level_words
import src.core.texts as texts


class TestBotParsing(unittest.TestCase):
    def test_extract_headword_from_oxford_line(self):
        self.assertEqual(bot._extract_headword("about prep., adv."), "about")
        self.assertEqual(bot._extract_headword("bank (money) n."), "bank")
        self.assertEqual(bot._extract_headword("can1 modal v."), "can")
        self.assertEqual(bot._extract_headword(""), "")

    def test_load_levelled_words_reads_levels(self):
        content = """A1
about prep., adv.
bank (money) n.

A2
again adv.
"""
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp_path = f.name

        old_file = level_words.COMMON_WORDS_FILE
        old_cache = level_words._level_words_cache
        old_mtime = level_words._level_words_mtime
        try:
            level_words.COMMON_WORDS_FILE = tmp_path
            level_words._level_words_cache = None
            level_words._level_words_mtime = None
            levels = bot._load_levelled_words()
            self.assertEqual(levels["A1"], ["about", "bank"])
            self.assertEqual(levels["A2"], ["again"])
        finally:
            level_words.COMMON_WORDS_FILE = old_file
            level_words._level_words_cache = old_cache
            level_words._level_words_mtime = old_mtime
            os.remove(tmp_path)

    def test_build_start_text_shows_admin_command_for_admins(self):
        normal_text = texts.build_start_text("User", 700, 5, is_admin=False)
        admin_text = texts.build_start_text("Admin", 700, 5, is_admin=True)
        self.assertNotIn("/admin", normal_text)
        self.assertIn("/admin", admin_text)

    def test_parse_positive_int_arg_bounds(self):
        self.assertEqual(bot._parse_positive_int_arg("/users", 30, 1, 200), 30)
        self.assertEqual(bot._parse_positive_int_arg("/users abc", 30, 1, 200), 30)
        self.assertEqual(bot._parse_positive_int_arg("/users -3", 30, 1, 200), 1)
        self.assertEqual(bot._parse_positive_int_arg("/users 999", 30, 1, 200), 200)
        self.assertEqual(bot._parse_positive_int_arg("/users 50", 30, 1, 200), 50)

    def test_build_admin_overview_text_contains_core_metrics(self):
        overview = {
            "total_users": 10,
            "joined_today": 2,
            "active_today": 5,
            "learned_total": 120,
            "hard_total": 18,
        }
        text = bot._build_admin_overview_text(overview)
        self.assertIn("Total users: 10", text)
        self.assertIn("Joined today: 2", text)
        self.assertIn("Active today: 5", text)
        self.assertIn("Learned words (total): 120", text)
        self.assertIn("Hard words (total): 18", text)

    def test_active_status_badge(self):
        now_iso = datetime.now().isoformat()
        old_iso = (datetime.now() - timedelta(minutes=10)).isoformat()
        self.assertEqual(bot._active_status_badge(now_iso), "🟢")
        self.assertEqual(bot._active_status_badge(old_iso), "🔴")
        self.assertEqual(bot._active_status_badge(None), "🔴")

    def test_placement_level_from_score(self):
        self.assertEqual(bot._placement_level_from_score(0, 12), "A1")
        self.assertEqual(bot._placement_level_from_score(5, 12), "A2")
        self.assertEqual(bot._placement_level_from_score(8, 12), "B1")
        self.assertEqual(bot._placement_level_from_score(11, 12), "B2")


class TestDatabaseNextWord(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Ensure schema exists
        await database.init_db()
        
        # Clean up tables before each test
        async with database._db_connect() as db:
            await db.execute("TRUNCATE users, word_progress, sessions, story_history, memory_palace_history, admin.audit_log RESTART IDENTITY CASCADE")
            
        await database.ensure_user(1, "tester")

    async def asyncTearDown(self):
        pass

    async def test_hard_due_word_priority(self):
        due = (datetime.now() - timedelta(days=1)).isoformat()
        async with database._db_connect() as db:
            await db.execute(
                """
                INSERT INTO word_progress (user_id, word, marked_hard, next_review, added_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (1, "alpha", 1, due, datetime.now().isoformat()),
            )
            await db.execute(
                """
                INSERT INTO word_progress (user_id, word, marked_hard, next_review, added_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (1, "beta", 0, due, datetime.now().isoformat()),
            )
            await db.commit()

        word = await database.get_next_word(1, ["alpha", "beta"])
        self.assertEqual(word, "alpha")

    async def test_hard_due_can_be_skipped(self):
        due = (datetime.now() - timedelta(days=1)).isoformat()
        async with database._db_connect() as db:
            await db.execute(
                """
                INSERT INTO word_progress (user_id, word, marked_hard, next_review, added_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (1, "hard_word", 1, due, datetime.now().isoformat()),
            )
            await db.execute(
                """
                INSERT INTO word_progress (user_id, word, marked_hard, next_review, added_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (1, "normal_due", 0, due, datetime.now().isoformat()),
            )
            await db.commit()

        word = await database.get_next_word(
            1,
            ["hard_word", "normal_due"],
            include_hard_due=False,
        )
        self.assertEqual(word, "normal_due")

    async def test_new_word_is_returned_when_unseen_exists(self):
        async with database._db_connect() as db:
            await db.execute(
                """
                INSERT INTO word_progress (user_id, word, added_at)
                VALUES (?, ?, ?)
                """,
                (1, "known", datetime.now().isoformat()),
            )
            await db.commit()

        allowed = ["known", "fresh1", "fresh2"]
        word = await database.get_next_word(1, allowed)
        self.assertIn(word, {"fresh1", "fresh2"})

    async def test_get_next_word_respects_exclude_word(self):
        async with database._db_connect() as db:
            await db.execute(
                """
                INSERT INTO word_progress (user_id, word, marked_hard, next_review, added_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (1, "same", 1, (datetime.now() - timedelta(days=1)).isoformat(), datetime.now().isoformat()),
            )
            await db.execute(
                """
                INSERT INTO word_progress (user_id, word, marked_hard, next_review, added_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (1, "other", 1, (datetime.now() - timedelta(hours=1)).isoformat(), datetime.now().isoformat()),
            )
            await db.commit()

        word = await database.get_next_word(1, ["same", "other"], exclude_word="same")
        self.assertEqual(word, "other")

    async def test_get_next_word_respects_exclude_words_list(self):
        async with database._db_connect() as db:
            await db.execute(
                """
                INSERT INTO word_progress (user_id, word, marked_hard, next_review, added_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (1, "a", 1, (datetime.now() - timedelta(days=1)).isoformat(), datetime.now().isoformat()),
            )
            await db.execute(
                """
                INSERT INTO word_progress (user_id, word, marked_hard, next_review, added_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (1, "b", 1, (datetime.now() - timedelta(hours=2)).isoformat(), datetime.now().isoformat()),
            )
            await db.execute(
                """
                INSERT INTO word_progress (user_id, word, marked_hard, next_review, added_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (1, "c", 1, (datetime.now() - timedelta(hours=1)).isoformat(), datetime.now().isoformat()),
            )
            await db.commit()

        word = await database.get_next_word(1, ["a", "b", "c"], exclude_words=["a", "b"])
        self.assertEqual(word, "c")

    async def test_daily_count_increments_only_once_per_word_per_day(self):
        await database.record_answer(1, "repeat", correct=True, marked_hard=False)
        await database.increment_daily(1, "repeat")
        c1 = await database.get_daily_count(1)

        await database.record_answer(1, "repeat", correct=True, marked_hard=False)
        await database.increment_daily(1, "repeat")
        c2 = await database.get_daily_count(1)

        self.assertEqual(c1, 1)
        self.assertEqual(c2, 1)

    async def test_mark_word_learned_moves_from_review_to_learned(self):
        await database.record_answer(1, "focus", correct=False, marked_hard=True)
        hard_before = await database.get_hard_words(1)
        self.assertTrue(any(w["word"] == "focus" for w in hard_before))

        ok = await database.mark_word_learned(1, "focus")
        self.assertTrue(ok)

        hard_after = await database.get_hard_words(1)
        learned = await database.get_learned_words(1)
        self.assertFalse(any(w["word"] == "focus" for w in hard_after))
        self.assertTrue(any(w["word"] == "focus" for w in learned))

    async def test_get_seen_words_returns_only_seen(self):
        await database.record_answer(1, "seen_word", correct=True, marked_hard=False)
        async with database._db_connect() as db:
            await db.execute(
                """
                INSERT INTO word_progress (user_id, word, seen, added_at)
                VALUES (?, ?, ?, ?)
                """,
                (1, "unseen_word", 0, datetime.now().isoformat()),
            )
            await db.commit()

        seen = await database.get_seen_words(1)
        self.assertIn("seen_word", seen)
        self.assertNotIn("unseen_word", seen)

    async def test_admin_user_lists_and_leaderboard(self):
        await database.ensure_user(2, "alice")
        await database.ensure_user(3, "bob")

        await database.record_answer(2, "alpha", correct=True, marked_hard=False)
        await database.record_answer(2, "beta", correct=True, marked_hard=False)
        await database.record_answer(2, "gamma", correct=False, marked_hard=True)

        await database.record_answer(3, "alpha", correct=True, marked_hard=False)

        user_ids = await database.get_all_user_ids()
        self.assertEqual(user_ids, [1, 2, 3])

        users = await database.get_all_users(limit=10)
        self.assertEqual(len(users), 3)
        self.assertTrue(any(int(u["user_id"]) == 2 for u in users))

        top = await database.get_top_leaderboard(limit=3)
        self.assertEqual(len(top), 3)
        self.assertEqual(int(top[0]["user_id"]), 2)

    async def test_ensure_user_updates_existing_username(self):
        await database.ensure_user(1, "tester")
        await database.ensure_user(1, "tester_new")

        users = await database.get_all_users(limit=10)
        me = next((u for u in users if int(u["user_id"]) == 1), None)
        self.assertIsNotNone(me)
        self.assertEqual(me["username"], "tester_new")

    async def test_ban_and_unban_user(self):
        await database.ensure_user(2, "alice")
        self.assertFalse(await database.is_banned(2))

        ok_ban = await database.set_user_ban(2, True, reason="spam")
        self.assertTrue(ok_ban)
        self.assertTrue(await database.is_banned(2))

        users = await database.get_all_users(limit=10)
        alice = next((u for u in users if int(u["user_id"]) == 2), None)
        self.assertIsNotNone(alice)
        self.assertEqual(int(alice["banned"]), 1)
        self.assertEqual(alice["ban_reason"], "spam")

        ok_unban = await database.set_user_ban(2, False, reason="")
        self.assertTrue(ok_unban)
        self.assertFalse(await database.is_banned(2))

    async def test_find_user_id_by_username(self):
        await database.ensure_user(2, "AliceUser")
        found = await database.find_user_id_by_username("@aliceuser")
        self.assertEqual(found, 2)

    async def test_update_streak_refreshes_last_active_same_day(self):
        await database.ensure_user(1, "tester")
        async with database._db_connect() as db:
            async with db.execute(
                "SELECT last_active FROM users WHERE user_id = ?",
                (1,),
            ) as cur:
                first = await cur.fetchone()
        first_ts = first["last_active"]
        self.assertTrue(first_ts)

        await database.ensure_user(1, "tester")
        async with database._db_connect() as db:
            async with db.execute(
                "SELECT last_active FROM users WHERE user_id = ?",
                (1,),
            ) as cur:
                second = await cur.fetchone()
        second_ts = second["last_active"]
        self.assertTrue(second_ts)
        self.assertGreaterEqual(second_ts, first_ts)

    async def test_srs_progression_fields_update(self):
        await database.record_answer(1, "alpha", correct=True, marked_hard=False)
        async with database._db_connect() as db:
            async with db.execute(
                """
                SELECT interval_days, repetitions, ease_factor, last_reviewed_at
                FROM word_progress WHERE user_id = ? AND word = ?
                """,
                (1, "alpha"),
            ) as cur:
                row1 = await cur.fetchone()
        self.assertIsNotNone(row1)
        self.assertEqual(int(row1["interval_days"]), 1)
        self.assertEqual(int(row1["repetitions"]), 1)
        self.assertTrue(float(row1["ease_factor"]) >= 2.5)
        self.assertTrue(bool(row1["last_reviewed_at"]))

        await database.record_answer(1, "alpha", correct=True, marked_hard=False)
        async with database._db_connect() as db:
            async with db.execute(
                """
                SELECT interval_days, repetitions
                FROM word_progress WHERE user_id = ? AND word = ?
                """,
                (1, "alpha"),
            ) as cur:
                row2 = await cur.fetchone()
        self.assertEqual(int(row2["interval_days"]), 3)
        self.assertEqual(int(row2["repetitions"]), 2)

    async def test_srs_failure_resets_repetitions(self):
        await database.record_answer(1, "beta", correct=True, marked_hard=False)
        await database.record_answer(1, "beta", correct=True, marked_hard=False)
        await database.record_answer(1, "beta", correct=False, marked_hard=False)
        async with database._db_connect() as db:
            async with db.execute(
                """
                SELECT interval_days, repetitions, ease_factor
                FROM word_progress WHERE user_id = ? AND word = ?
                """,
                (1, "beta"),
            ) as cur:
                row = await cur.fetchone()
        self.assertEqual(int(row["interval_days"]), 1)
        self.assertEqual(int(row["repetitions"]), 0)
        self.assertLess(float(row["ease_factor"]), 2.6)

    async def test_srs_easy_interval_is_longer_than_good(self):
        await database.record_answer(1, "good_word", correct=True, marked_hard=False, grade="good")
        await database.record_answer(1, "easy_word", correct=True, marked_hard=False, grade="easy")
        async with database._db_connect() as db:
            async with db.execute(
                "SELECT interval_days FROM word_progress WHERE user_id = ? AND word = ?",
                (1, "good_word"),
            ) as cur:
                good_row = await cur.fetchone()
            async with db.execute(
                "SELECT interval_days FROM word_progress WHERE user_id = ? AND word = ?",
                (1, "easy_word"),
            ) as cur:
                easy_row = await cur.fetchone()
        self.assertIsNotNone(good_row)
        self.assertIsNotNone(easy_row)
        self.assertGreaterEqual(int(easy_row["interval_days"]), int(good_row["interval_days"]))

    async def test_reset_preserve_history_and_full_reset(self):
        await database.record_answer(1, "keepme", correct=True, marked_hard=False)
        seen_before = await database.get_seen_words(1)
        self.assertIn("keepme", seen_before)

        await database.reset_progress(1, preserve_history=True)
        seen_after_soft = await database.get_seen_words(1)
        self.assertIn("keepme", seen_after_soft)

        await database.reset_progress(1, preserve_history=False)
        seen_after_full = await database.get_seen_words(1)
        self.assertNotIn("keepme", seen_after_full)

    async def test_placement_persistence(self):
        self.assertFalse(await database.is_placement_done(1))
        ok = await database.set_placement_result(1, "B1", 8)
        self.assertTrue(ok)
        self.assertTrue(await database.is_placement_done(1))
        self.assertEqual(await database.get_user_level(1), "B1")

    async def test_wordset_progress(self):
        await database.record_answer(1, "w1", correct=True, marked_hard=False, grade="good")
        await database.record_answer(1, "w2", correct=False, marked_hard=False, grade="again")
        p = await database.get_wordset_progress(1, ["w1", "w2", "w3"])
        self.assertEqual(p["total"], 3)
        self.assertGreaterEqual(p["learned"], 1)

    async def test_today_answered_words_and_story_history(self):
        await database.record_answer(1, "story1", correct=True, marked_hard=False, grade="good")
        await database.record_answer(1, "story2", correct=True, marked_hard=False, grade="good")
        await database.record_answer(1, "story1", correct=True, marked_hard=False, grade="good")
        words = await database.get_today_answered_words(1, limit=10)
        self.assertIn("story1", words)
        self.assertIn("story2", words)
        self.assertEqual(len(words), len(set(words)))

        sid = await database.save_story_history(
            1,
            "Cyberpunk",
            words,
            "Sample story text",
        )
        self.assertGreater(sid, 0)

    async def test_word_grade_map(self):
        await database.record_answer(1, "g_again", correct=False, marked_hard=False, grade="again")
        await database.record_answer(1, "g_hard", correct=True, marked_hard=True, grade="hard")
        await database.record_answer(1, "g_good", correct=True, marked_hard=False, grade="good")
        await database.record_answer(1, "g_easy", correct=True, marked_hard=False, grade="easy")
        m = await database.get_word_grade_map(1, ["g_again", "g_hard", "g_good", "g_easy", "g_new"])
        self.assertEqual(m.get("g_again"), "again")
        self.assertEqual(m.get("g_hard"), "hard")
        self.assertEqual(m.get("g_good"), "good")
        self.assertEqual(m.get("g_easy"), "easy")
        self.assertIsNone(m.get("g_new"))

    async def test_save_memory_palace_history(self):
        palace_id = await database.save_memory_palace_history(
            1,
            "Ancient Room",
            ["mirror", "ancient", "cat"],
            "Memory palace sample text",
        )
        self.assertGreater(palace_id, 0)

    async def test_story_and_palace_history_helpers(self):
        sid = await database.save_story_history(1, "Fantasy", ["a", "b"], "Story text")
        self.assertGreater(sid, 0)
        pid = await database.save_memory_palace_history(1, "Cozy Home", ["x", "y"], "Palace text")
        self.assertGreater(pid, 0)

        story_count = await database.count_story_generations_today(1)
        palace_count = await database.count_palace_generations_today(1)
        self.assertGreaterEqual(story_count, 1)
        self.assertGreaterEqual(palace_count, 1)

        sh = await database.get_story_history(1, limit=5)
        ph = await database.get_memory_palace_history(1, limit=5)
        self.assertTrue(any((r.get("genre") or "") == "Fantasy" for r in sh))
        self.assertTrue(any((r.get("theme") or "") == "Cozy Home" for r in ph))


if __name__ == "__main__":
    unittest.main()
