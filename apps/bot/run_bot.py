import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# Import the unified router
from apps.bot.handlers import router

load_dotenv()


async def main():
    logging.basicConfig(level=logging.INFO)

    # 1. Setup
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env")
        return

    bot = Bot(token=bot_token)
    dp = Dispatcher()

    # 2. Register the Router (The ONLY brain)
    dp.include_router(router)

    # 3. Launch
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())