import asyncio
import logging

from aiogram import Bot, Dispatcher

from api_words import (
    close_http_session,
)
from config import TOKEN
from database import (
    init_db,
)
import placement
import general
import study
import features
import admin

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def main():
    if not TOKEN or TOKEN == "123456:TEST_TOKEN":
        raise RuntimeError(
            "TOKEN is not configured. Create a .env file and set a real Telegram bot token."
        )
    if ":" not in TOKEN or len(TOKEN) < 20:
        raise RuntimeError("TOKEN format looks invalid. Expected format: <id>:<secret>.")

    await init_db()

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
