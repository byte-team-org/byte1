import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.database import init_db
from bot.handlers import common, participant, volunteer
from bot.middlewares.i18n import I18nMiddleware
from bot.services.regions import init_regions
from bot.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register middlewares
    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())

    # Register routers
    dp.include_router(common.router)
    dp.include_router(participant.router)
    dp.include_router(volunteer.router)

    # Initialize DB and seed regions
    await init_db()
    async with AsyncSessionLocal() as session:
        await init_regions(session)

    logger.info("Bot started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
