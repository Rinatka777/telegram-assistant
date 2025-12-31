import requests
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message
from fastapi import UploadFile
import uuid, os

router = Router()

class DocumentHandler:
    def __init__(self, max_size: int = 10 * 1024 * 1024):
        self.max_size = max_size
        self.allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']

    async def validate_file(self, file: UploadFile):
        result = {"valid": True, "errors": []}

        if not file.filename or file.filename.strip() == "":
            result["valid"] = False
            result["errors"].append("File name cannot be empty")
            return result

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            result["valid"] = False
            result["errors"].append(f"File extension '{file_ext}' is not allowed")
            return result

        content = await file.read()
        await file.seek(0)

        file_size = len(content)
        if file_size > self.max_size:
            result["valid"] = False
            result["errors"].append(
                f"File too large ({file_size:,} bytes). Maximum: {self.max_size:,} bytes"
            )
        return result


@router.message(F.text)
async def handle_text_message(message: Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    payload = {
        "question": message.text,
        "user_id": message.from_user.id
    }
    try:
        response = requests.post("http://127.0.0.1:8000/chat", json=payload)

        if response.status_code == 200:
            answer_text = response.json()
            await message.answer(answer_text)
        else:
            await message.answer(f"My brain is offline. (API Error: {response.status_code})")

    except Exception as e:
        await message.answer(f"Connection error: {e}")

@router.message(F.voice)
async def handle_voice_message(message: Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    file_id = message.voice.file_id
    file = message.bot.get_file(file_id)
    file_path = file.file_path
    temp_path = f"data/files/voice_{uuid.uuid4()}.ogg"
    os.makedirs("data/files", exist_ok=True)
    await message.bot.download_file(file_path, temp_path)

    try:
        with open(temp_path, 'rb') as f:
            files = {'file': (temp_path, f, 'audio/ogg')}
            response = requests.post("http://127.0.0.1:8000/transcribe", files=files)

        if response.status_code == 200:
            transcribed_text = response.json().get("text", "")
            await message.reply(f"🎤 I heard: \"{transcribed_text}\"")
            payload = {
                "question": transcribed_text,
                "user_id": message.from_user.id
            }
            chat_response = requests.post("http://127.0.0.1:8000/chat", json=payload)

            if chat_response.status_code == 200:
                await message.answer(chat_response.json())
            else:
                await message.answer("I heard you, but I couldn't think of an answer.")

        else:
            await message.answer("Could not transcribe audio.")

    except Exception as e:
        await message.answer(f"Voice Error: {e}")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)