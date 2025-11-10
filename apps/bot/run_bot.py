from io import BytesIO

from dotenv import load_dotenv; load_dotenv()
import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

load_dotenv()
# Bot token can be obtained via https://t.me/BotFather
TOKEN = os.getenv("BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Export it or put it in your .env.")
# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")

@dp.message(F.document | F.photo | F.audio | F.voice):
async def file_handler(message: Message, bot: Bot)-> None:
    try:
        if message.document:
            tg_file = message.document
            filename = tg_file.file_name
            content_type = tg_file.mime_type
        elif message.photo:
            tg_file = message.photo[-1]
            filename = "photo.jpg"
            content_type = "image/jpeg"
        elif message.audio:
            tg_file = message.audio
            filename = tg_file.file_name
            content_type = tg_file.mime_type
        elif message.voice:
            tg_file = message.voice
            filename = tg_file.file_name
            content_type = tg_file.mime_type
        else:
            return

        buf = BytesIO()
        await bot.download(tg_file, destination = buf)
        buf.seek(0)

        files = [("files", (filename, buf.getvalue(), content_type))]
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{API_BASE_URL}/attachments", files=files)
        if resp.status_code != 200:
            data = resp.json()
            stored = [x["stored"] for x in data["uploaded"]]
            await message.answer(f"Uploaded: {', '.join(stored)}")
        else:
            await message.answer(f"Upload failed: {resp.status_code} {resp.text[:200]}")

    except Exception as e:
        await message.answer(f"Error: {e.__class__.__name__}")





@dp.message()
async def echo_handler(message: Message) -> None:
    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())