import requests
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message
from fastapi import UploadFile

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