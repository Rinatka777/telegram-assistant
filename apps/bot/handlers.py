import os
import requests
import uuid
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

# Initialize the Router
router = Router()

# API URL
API_URL = "http://127.0.0.1:8000"


# ---------------------------------------------------------
# 1. THE CLEAR COMMAND
# ---------------------------------------------------------
@router.message(Command("clear"))
async def handle_clear(message: Message):
    user_id = message.from_user.id
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        response = requests.delete(f"{API_URL}/notes?user_id={user_id}")
        if response.status_code == 200:
            data = response.json()
            # This will confirm exactly how many were deleted
            await message.answer(f"🧹 {data.get('message', 'Cleared!')}")
        else:
            await message.answer("❌ Error: Could not clear memory.")
    except Exception as e:
        await message.answer(f"❌ Connection Error: {e}")


# ---------------------------------------------------------
# 2. FILE HANDLER (Documents & Voice)
# ---------------------------------------------------------

@router.message(F.document | F.photo | F.audio | F.voice)
async def handle_files(message: Message):
    user_id = message.from_user.id

    # 1. IDENTIFY FILE TYPE & METADATA
    # We restore the logic to detect extensions and mime types correctly
    if message.document:
        file_id = message.document.file_id
        filename = message.document.file_name or f"doc_{uuid.uuid4()}"
        content_type = message.document.mime_type or "application/octet-stream"
        endpoint = "attachments"  # standard upload

    elif message.voice:
        file_id = message.voice.file_id
        filename = f"voice_{uuid.uuid4()}.ogg"
        content_type = "audio/ogg"
        endpoint = "transcribe"  # voice specific

    elif message.photo:
        # Photos come in a list of sizes; take the largest one (-1)
        file_id = message.photo[-1].file_id
        filename = f"photo_{uuid.uuid4()}.jpg"
        content_type = "image/jpeg"
        endpoint = "attachments"

    elif message.audio:
        file_id = message.audio.file_id
        filename = message.audio.file_name or f"audio_{uuid.uuid4()}.mp3"
        content_type = message.audio.mime_type or "audio/mpeg"
        endpoint = "attachments"
    else:
        await message.answer("⚠️ Unsupported file type.")
        return

    # UX: Show we are working
    action = "typing" if endpoint == "transcribe" else "upload_document"
    await message.bot.send_chat_action(chat_id=message.chat.id, action=action)

    # 2. DOWNLOAD & PROCESS
    temp_path = f"data/files/{filename}"
    os.makedirs("data/files", exist_ok=True)

    try:
        # Download from Telegram
        file_info = await message.bot.get_file(file_id)
        await message.bot.download_file(file_info.file_path, temp_path)

        api_url = f"{API_URL}/{endpoint}"
        if endpoint == "attachments":
            api_url += f"?user_id={user_id}"

        # 3. UPLOAD TO API
        with open(temp_path, "rb") as f:
            # CRITICAL FIX: The key here must be "files" (plural) to match your API
            files_payload = {"files": (filename, f, content_type)}

            response = requests.post(api_url, files=files_payload)

            if response.status_code == 200:
                data = response.json()

                # Case A: Voice Transcription
                if endpoint == "transcribe":
                    text = data.get("text", "")
                    await message.reply(f"🎤 **Transcribed:** \"{text}\"")
                    # Auto-send to Chat
                    chat_payload = {"question": text, "user_id": user_id}
                    chat_resp = requests.post(f"{API_URL}/chat", json=chat_payload)
                    await message.answer(chat_resp.json())

                # Case B: Document/Photo Upload
                else:
                    summary = data.get("summary", "Saved successfully.")
                    await message.reply(f"📄 **Saved!**\n\n{summary}")
            else:
                await message.reply(f"❌ API Error {response.status_code}: {response.text}")

    except Exception as e:
        await message.answer(f"❌ Error: {str(e)}")

    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ---------------------------------------------------------
# 3. TEXT CHAT
# ---------------------------------------------------------
@router.message(F.text)
async def handle_text(message: Message):
    if message.text.startswith("/"): return  # Ignore other commands

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        payload = {"question": message.text, "user_id": message.from_user.id}
        response = requests.post(f"{API_URL}/chat", json=payload)

        if response.status_code == 200:
            await message.answer(response.json())
        else:
            await message.answer("⚠️ Brain offline.")

    except Exception as e:
        await message.answer(f"Connection Error: {e}")