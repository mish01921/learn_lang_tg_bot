import asyncio
import logging
import os
import sys

# Ensure project root is in sys.path so running 'python src/main.py' works directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aiogram import Bot, Dispatcher

from src.bot.handlers import admin, features, general, placement, study
from src.core.config import TOKEN
from src.core.texts import BOT_DESCRIPTION, BOT_SHORT_DESCRIPTION
from src.data.api_words import (
    HTTPClient,
)
from src.database.models import (
    close_db_pool,
    init_db,
)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def start_health_check_server():
    """Starts a minimal web server to satisfy Render's port binding requirement."""
    from aiohttp import web

    async def handle_health(request):
        return web.Response(text="Bot is running OK")

    app = web.Application()
    app.router.add_get('/', handle_health)
    app.router.add_get('/health', handle_health)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Health check server started on port {port}")

async def start_daily_reminder_loop(bot: Bot):
    """Background loop that handles daily streak and review reminders."""
    while True:
        try:
            await asyncio.sleep(4 * 3600) # Check every 4 hours
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error(f"Reminder loop error: {e}")

async def main():
    if not TOKEN or TOKEN == "123456:TEST_TOKEN":
        raise RuntimeError(
            "TOKEN is not configured. Create a .env file and set a real Telegram bot token."
        )
    if ":" not in TOKEN or len(TOKEN) < 20:
        raise RuntimeError("TOKEN format looks invalid. Expected format: <id>:<secret>.")

    await init_db()

    # Update bot profile description and short description
    try:
        await bot.set_my_description(BOT_DESCRIPTION)
        await bot.set_my_short_description(BOT_SHORT_DESCRIPTION)
        logging.info("Bot profile description updated.")
    except Exception as e:
        logging.error(f"Failed to set bot description: {e}")

    # Start the dummy web server for Render
    await start_health_check_server()

    # Register all routers
    dp.include_router(placement.router)
    dp.include_router(admin.router)
    dp.include_router(general.router)
    dp.include_router(study.router)
    dp.include_router(features.router)

    reminder_task = asyncio.create_task(start_daily_reminder_loop(bot))
    try:
        await dp.start_polling(bot)
    finally:
        reminder_task.cancel()
        await close_db_pool()
        await HTTPClient.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        logging.exception("Bot terminated due to an unhandled exception")
