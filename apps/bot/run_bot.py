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
from aiogram.filters import CommandStart, Command, CommandObject

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

@dp.message(Command("add"))
async def add_task_handler(message: Message, command: CommandObject) -> None:
    task_title = command.args
    if not task_title:
        await message.answer("Please provide a task title. Example: /add Buy milk")
        return

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            payload = {
                "user_id": message.from_user.id,
                "title": task_title,
                "due_at": None,
                "note_id": None
            }
            resp = await client.post(f"{API_BASE_URL}/tasks", json=payload)
            if resp.status_code == 200:
                task = resp.json()
                await message.answer(f"✅ Task created! [ID: {task['id']}] {task['title']}")
            else:
                await message.answer(f"Failed to create task: {resp.status_code}")
        except Exception as e:
            await message.answer(f"Connection error: {str(e)}")

@dp.message(Command("get"))
async def get_note_handler(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("Please provide a note ID. Example: /get 5")
        return

    try:
        note_id = int(command.args)
    except ValueError:
        await message.answer("Invalid ID. Please use a number (e.g., /get 5).")
        return


@dp.message(Command("search"))
async def search_notes_handler(message: Message, command: CommandObject) -> None:
    # 1. Input Validation
    query = command.args
    if not query:
        await message.answer("Please provide a search query. Example: /search milk")
        return

    # 2. API Call
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                f"{API_BASE_URL}/notes/search",
                params={
                    "q": query,
                    "user_id": message.from_user.id
                }
            )

            if resp.status_code == 200:
                notes = resp.json()

                if not notes:
                    await message.answer("No notes found matching that query.")
                    return

                # 3. Formatting Output
                lines = [f"<b>Found {len(notes)} notes:</b>"]

                for note in notes:
                    # Use .get() for safety, though 'filename' should exist now
                    filename = note.get('filename') or "Unnamed File"
                    preview = note.get('match_preview') or "..."
                    note_id = note['id']

                    # HTML Formatting
                    block = f"📄 <b>{filename}</b> (ID: {note_id})\n<i>{preview}</i>"
                    lines.append(block)

                await message.answer("\n\n".join(lines))

            else:
                await message.answer(f"Search failed: {resp.status_code}")

        except Exception as e:
            await message.answer(f"Connection error: {str(e)}")



@dp.message(Command("tasks"))
async def list_tasks_handler(message: Message) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                f"{API_BASE_URL}/tasks",
                params={"user_id": message.from_user.id, "status": "open"}
            )
            if resp.status_code == 200:
                tasks = resp.json()
                if not tasks:
                    await message.answer("You have no open tasks! 🎉")
                    return

                lines = ["<b>Your Open Tasks:</b>"]
                for t in tasks:
                    lines.append(f"• <code>{t['id']}</code>: {t['title']}")
                await message.answer("\n".join(lines))
            else:
                await message.answer(f"Failed to fetch tasks: {resp.status_code}")
        except Exception as e:
            await message.answer(f"Connection error: {str(e)}")

@dp.message(Command("done"))
async def complete_task_handler(message: Message, command: CommandObject) -> None:
    task_id_str = command.args
    if not task_id_str or task_id_str.isdigit():
        await message.answer("Please specify a valid numeric task ID. Example: /done 1")
    task_id = int(task_id_str)

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(
                f"{API_BASE_URL}/tasks/{task_id}/complete"
            )
            if resp.status_code == 200:
                task = resp.json()
                await message.answer(f"✅ Marked task #{task['id']} as completed.")
            elif resp.status_code == 404:
                await message.answer(f"Task #{task_id} not found.")
            else:
                await message.answer(f"Error completing task: {resp.status_code}")

        except Exception as e:
            await message.answer(f"Connection error: {str(e)}")

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