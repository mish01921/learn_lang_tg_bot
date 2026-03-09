from aiogram import Router, F
from aiogram.filters import BaseFilter, Command
from aiogram.types import Message, CallbackQuery
from datetime import datetime

from config import ADMIN_USER_IDS
from database import (
    get_health_snapshot,
    get_all_users,
    get_top_leaderboard,
    set_user_ban,
    find_user_id_by_username,
    get_all_user_ids,
    get_admin_overview
)
from ui import get_admin_keyboard, get_admin_users_keyboard
from utils import safe_edit_text, parse_positive_int_arg

router = Router()
BOT_STARTED_AT = datetime.now()

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if not message.from_user:
            return False
        return message.from_user.id in ADMIN_USER_IDS

def _format_uptime(from_dt: datetime) -> str:
    sec = max(0, int((datetime.now() - from_dt).total_seconds()))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

@router.message(Command("admin"), IsAdmin())
async def admin_panel_handler(message: Message):
    await message.answer("🛠 Admin Panel", reply_markup=get_admin_keyboard())

@router.message(Command("health"), IsAdmin())
async def health_handler(message: Message):
    health = await get_health_snapshot()
    status = "OK" if health.get("db_ok") else "FAIL"
    await message.answer(
        "🩺 Health Check\n\n"
        f"DB: {status}\n"
        f"Uptime: {_format_uptime(BOT_STARTED_AT)}\n"
        f"users: {health.get('users', 0)}\n"
        f"word_progress: {health.get('word_progress', 0)}\n"
        f"sessions: {health.get('sessions', 0)}\n"
        f"story_history: {health.get('story_history', 0)}\n"
        f"memory_palace_history: {health.get('memory_palace_history', 0)}"
    )

@router.message(Command("users"), IsAdmin())
async def users_handler(message: Message):
    limit = parse_positive_int_arg(message.text or "", default=20, min_value=1, max_value=50)
    rows = await get_all_users(limit=limit)
    if not rows:
        await message.answer("👥 User չի գտնվել։")
        return
    lines = [f"👥 Users (last {len(rows)})"]
    for i, u in enumerate(rows, 1):
        username = f"@{u['username']}" if u.get("username") else "—"
        lines.append(
            f"{i}. id={u['user_id']} | {username} | lvl={(u.get('user_level') or 'A1').upper()} | ban={'🚫' if int(u.get('banned') or 0)==1 else '✅'}"
        )
    await message.answer("\n".join(lines))

@router.message(Command("top"), IsAdmin())
async def top_handler(message: Message):
    limit = parse_positive_int_arg(message.text or "", default=10, min_value=1, max_value=30)
    rows = await get_top_leaderboard(limit=limit)
    if not rows:
        await message.answer("🏆 Leaderboard-ում տվյալ չկա։")
        return
    lines = [f"🏆 Top {len(rows)} leaderboard"]
    for i, r in enumerate(rows, 1):
        username = f"@{r['username']}" if r.get("username") else f"id={r['user_id']}"
        lines.append(
            f"{i}. {username} | learned={r['learned_count']} | accuracy={r['accuracy']}% | streak={r['streak']}"
        )
    await message.answer("\n".join(lines))

@router.message(Command("broadcast"), IsAdmin())
async def broadcast_handler(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    payload = parts[1].strip() if len(parts) > 1 else ""
    
    if not payload and not message.reply_to_message:
        await message.answer("Օգտագործում՝ /broadcast <text> կամ reply արեք հաղորդագրությանը։")
        return

    recipients = await get_all_user_ids()
    if not recipients:
        await message.answer("Ուղարկման համար user չկա։")
        return

    sent, failed = 0, 0
    status_msg = await message.answer(f"📣 Broadcast started for {len(recipients)} users...")

    for uid in recipients:
        try:
            if message.reply_to_message:
                await message.reply_to_message.copy_to(uid)
            else:
                await message.bot.send_message(uid, payload)
            sent += 1
        except Exception:
            failed += 1
            
    await status_msg.edit_text(
        f"📣 Broadcast ավարտվեց\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"👥 Total: {len(recipients)}"
    )

@router.message(Command("ban"), IsAdmin())
async def ban_handler(message: Message):
    parts = (message.text or "").strip().split(maxsplit=2)
    if len(parts) < 2:
        await message.answer("Օգտագործում՝ /ban <user_id|@username> [reason]")
        return
    
    target_input = parts[1].strip()
    reason = parts[2].strip() if len(parts) > 2 else "Admin command"
    
    target_id = None
    if target_input.isdigit():
        target_id = int(target_input)
    elif target_input.startswith("@"):
        target_id = await find_user_id_by_username(target_input)
    
    if not target_id:
        await message.answer("❗ User չի գտնվել։")
        return
        
    if target_id in ADMIN_USER_IDS:
        await message.answer("⛔ Ադմին ban անել չի թույլատրվում։")
        return

    if await set_user_ban(target_id, True, reason=reason):
        await message.answer(f"🚫 User {target_id} banned")
    else:
        await message.answer("❗ Ban չհաջողվեց։")

@router.message(Command("unban"), IsAdmin())
async def unban_handler(message: Message):
    parts = (message.text or "").strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Օգտագործում՝ /unban <user_id|@username>")
        return
    
    target_input = parts[1].strip()
    target_id = None
    if target_input.isdigit():
        target_id = int(target_input)
    elif target_input.startswith("@"):
        target_id = await find_user_id_by_username(target_input)
    
    if not target_id:
        await message.answer("❗ User չի գտնվել։")
        return

    if await set_user_ban(target_id, False):
        await message.answer(f"✅ User {target_id} unbanned")
    else:
        await message.answer("❗ Unban չհաջողվեց։")

# Callback handlers for UI
@router.callback_query(F.data.startswith("adminui:"))
async def admin_ui_handler(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_USER_IDS:
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    action = callback.data.split(":")[1]
    
    if action == "overview":
        stats = await get_admin_overview()
        text = (
            f"📊 Overview\n\n"
            f"👥 Total Users: {stats['total_users']}\n"
            f"🆕 Joined Today: {stats['joined_today']}\n"
            f"🟢 Active Today: {stats['active_today']}\n"
            f"✅ Learned Words: {stats['learned_total']}\n"
            f"🔁 Hard Words: {stats['hard_total']}"
        )
        await safe_edit_text(callback.message, text, reply_markup=get_admin_keyboard())
        await callback.answer()

    elif action == "users":
        limit = int(callback.data.split(":")[2]) if len(callback.data.split(":")) > 2 else 30
        users = await get_all_users(limit=limit)
        await safe_edit_text(callback.message, f"👥 Last {len(users)} Users", reply_markup=get_admin_users_keyboard(users, limit))
        await callback.answer()

    elif action == "top":
        limit = int(callback.data.split(":")[2]) if len(callback.data.split(":")) > 2 else 10
        top = await get_top_leaderboard(limit=limit)
        lines = [f"🏆 Top {len(top)} Leaderboard"]
        for i, u in enumerate(top, 1):
            name = f"@{u['username']}" if u.get("username") else str(u['user_id'])
            lines.append(f"{i}. {name} — {u['learned_count']} learned")
        await safe_edit_text(callback.message, "\n".join(lines), reply_markup=get_admin_keyboard())
        await callback.answer()
        
    elif action == "broadcast_help":
        text = (
            "📣 Broadcast Help\n\n"
            "To send a message to all users:\n"
            "1. `/broadcast Your message`\n"
            "2. Reply to a message with `/broadcast`"
        )
        await safe_edit_text(callback.message, text, reply_markup=get_admin_keyboard())
        await callback.answer()

    elif action == "refresh":
        await safe_edit_text(callback.message, "🛠 Admin Panel", reply_markup=get_admin_keyboard())
        await callback.answer("Refreshed")

@router.callback_query(F.data.startswith("adminmod:"))
async def admin_mod_handler(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_USER_IDS:
        await callback.answer("⛔ Access denied", show_alert=True)
        return

    parts = callback.data.split(":")
    action = parts[1]
    
    if action == "back":
        await safe_edit_text(callback.message, "🛠 Admin Panel", reply_markup=get_admin_keyboard())
        await callback.answer()
        return

    if action == "refresh":
        limit = int(parts[2]) if len(parts) > 2 else 30
        users = await get_all_users(limit=limit)
        await safe_edit_text(callback.message, f"👥 Last {len(users)} Users", reply_markup=get_admin_users_keyboard(users, limit))
        await callback.answer("Refreshed list")
        return

    if action in ("ban", "unban"):
        target_id = int(parts[2])
        limit = int(parts[3]) if len(parts) > 3 else 30
        
        if target_id in ADMIN_USER_IDS:
             await callback.answer("⛔ Cannot ban admin", show_alert=True)
             return

        is_ban = (action == "ban")
        await set_user_ban(target_id, is_ban, reason="Admin UI action")
        
        # Refresh list
        users = await get_all_users(limit=limit)
        await safe_edit_text(callback.message, f"👥 Last {len(users)} Users", reply_markup=get_admin_users_keyboard(users, limit))
        await callback.answer(f"User {target_id} {'banned' if is_ban else 'unbanned'}")
        return
        
    if action == "user":
        target_id = int(parts[2])
        await callback.answer(f"User ID: {target_id}")
        return
