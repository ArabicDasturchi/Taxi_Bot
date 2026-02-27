import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core.config import ADMIN_BOT_TOKEN, USER_BOT_TOKEN
from app.database.db import init_db
from app.driver_bot.handlers import driver_router
from app.admin_bot.handlers import admin_router
from app.worker.scheduler import start_scheduler
from app.worker.scraper import start_userbot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def start_bots():
    logger.info("Starting up database...")
    await init_db()

    logger.info("Starting up Pyrogram Userbot...")
    await start_userbot()

    logger.info("Starting up scheduler...")
    start_scheduler()

    # Admin Bot
    admin_bot = Bot(token=ADMIN_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    admin_dp = Dispatcher()
    admin_dp.include_router(admin_router)
    
    # User (Driver) Bot
    user_bot = Bot(token=USER_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    user_dp = Dispatcher()
    user_dp.include_router(driver_router)

    # Pass specific bot instances to handlers if needed, though they handle from Context
    # It's better to run them concurrently:
    
    logger.info("Bots are starting...")
    await asyncio.gather(
        admin_bot.delete_webhook(drop_pending_updates=True),
        user_bot.delete_webhook(drop_pending_updates=True)
    )

    await asyncio.gather(
        admin_dp.start_polling(admin_bot),
        user_dp.start_polling(user_bot)
    )

if __name__ == "__main__":
    asyncio.run(start_bots())
