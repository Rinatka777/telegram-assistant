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
@router.message(F.document | F.voice)
async def handle_files(message: Message):
    user_id = message.from_user.id

    # --- A. VOICE MESSAGES ---
    if message.voice:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        file_id = message.voice.file_id
        temp_filename = f"voice_{uuid.uuid4()}.ogg"
        api_endpoint = f"{API_URL}/transcribe"

    # --- B. DOCUMENTS (PDF, etc.) ---
    elif message.document:
        # Simple Validation (Optional)
        if message.document.file_size > 10 * 1024 * 1024:  # 10MB limit
            await message.reply("❌ File is too big (Max 10MB).")
            return

        await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_document")
        file_id = message.document.file_id
        temp_filename = message.document.file_name or f"doc_{uuid.uuid4()}"
        api_endpoint = f"{API_URL}/attachments?user_id={user_id}"

    # --- COMMON DOWNLOAD & UPLOAD ---
    try:
        # 1. Download
        file_info = await message.bot.get_file(file_id)
        temp_path = f"data/files/{temp_filename}"
        os.makedirs("data/files", exist_ok=True)
        await message.bot.download_file(file_info.file_path, temp_path)

        # 2. Upload to API
        with open(temp_path, "rb") as f:
            if message.voice:
                # Voice -> Transcribe -> Chat
                files = {"file": (temp_filename, f, "audio/ogg")}
                resp = requests.post(api_endpoint, files=files)
                if resp.status_code == 200:
                    text = resp.json().get("text", "")
                    await message.reply(f"🎤 **Transcribed:** \"{text}\"")
                    # Send text to Chat
                    chat_payload = {"question": text, "user_id": user_id}
                    chat_resp = requests.post(f"{API_URL}/chat", json=chat_payload)
                    await message.answer(chat_resp.json())
            else:
                # Document -> Save -> Summary
                files = {"file": (temp_filename, f, "application/pdf")}
                resp = requests.post(api_endpoint, files=files)
                if resp.status_code == 200:
                    summary = resp.json().get("summary", "Saved.")
                    await message.reply(f"📄 **Saved!**\n\n{summary}")

    except Exception as e:
        await message.answer(f"Error handling file: {e}")

    finally:
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