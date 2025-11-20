from pydantic import BaseModel
from datetime import datetime

class NoteBase(BaseModel):
    user_id: int
    attachment_path: str

class NoteCreate(NoteBase):
    full_text: str

class NoteOut(NoteBase):
    id: int
    full_text: str
    created_at: datetime

    class Config:
        from_attributes = True