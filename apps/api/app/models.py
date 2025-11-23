from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from .db import Base

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)        # later from Telegram user id
    attachment_path = Column(String, nullable=False)
    full_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    title = Column(String, nullable=False)
    due_at = Column(DateTime, nullable=True)
    status = Column(String, default="open", index=True)
    note_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)