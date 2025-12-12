from datetime import datetime
from pydantic import BaseModel


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

class NoteSearchResult(NoteBase):
    id: int
    match_preview: str
    created_at: datetime



class TaskBase(BaseModel):
    user_id: int
    title: str
    due_at: datetime | None = None
    note_id: int | None = None


class TaskCreate(TaskBase):
    pass


class TaskOut(TaskBase):
    id: int
    status: str
    created_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True