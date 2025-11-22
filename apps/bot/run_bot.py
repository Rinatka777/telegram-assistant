from io import BytesIO
import asyncio
import logging
import os
import sys

import httpx
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Export it or put it in your .env.")

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")

@dp.message(F.document | F.photo | F.audio | F.voice)
async def file_handler(message: Message, bot: Bot) -> None:
    try:
        if message.document:
            tg_file = message.document
            filename = tg_file.file_name or "document"
            content_type = tg_file.mime_type or "application/octet-stream"
        elif message.photo:
            tg_file = message.photo[-1]
            filename = "photo.jpg"
            content_type = "image/jpeg"
        elif message.audio:
            tg_file = message.audio
            filename = tg_file.file_name or "audio"
            content_type = tg_file.mime_type or "audio/mpeg"
        elif message.voice:
            tg_file = message.voice
            filename = "voice.ogg"
            content_type = "audio/ogg"
        else:
            return

        buf = BytesIO()
        await bot.download(tg_file, destination=buf)
        buf.seek(0)

        files = [("files", (filename, buf.getvalue(), content_type))]

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{API_BASE_URL}/attachments",
                params={"user_id": message.from_user.id},
                files=files,
            )

        if resp.status_code == 200:
            data = resp.json()
            uploaded = data["uploaded"][0]
            note_id = uploaded["note_id"]
            preview = uploaded.get("text_preview") or ""
            if preview:
                await message.answer(f"Note #{note_id} created.\n\nPreview:\n{preview}")
            else:
                await message.answer(
                    f"Note #{note_id} created, but I couldn't extract any text."
                )
        else:
            await message.answer(
                f"Upload failed: {resp.status_code} {resp.text[:200]}"
            )

    except Exception as e:
        await message.answer(f"Error: {e.__class__.__name__}")

@dp.message()
async def echo_handler(message: Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")

async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())