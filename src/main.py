import asyncio
import logging
import os

from aiogram import Bot, Dispatcher

from src.bot.handlers import admin, features, general, placement, study
from src.core.config import TOKEN
from src.core.texts import BOT_DESCRIPTION, BOT_SHORT_DESCRIPTION
from src.data.api_words import (
    close_http_session,
)
from src.database.models import (
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

    try:
        await dp.start_polling(bot)
    finally:
        await close_http_session()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        logging.exception("Bot terminated due to an unhandled exception")
