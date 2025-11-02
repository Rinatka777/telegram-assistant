import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

bot = Bot(token="YOUR_TOKEN")
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_handler(message):
    await message.reply("Hello! I'm alive!")

executor.start_polling(dp)