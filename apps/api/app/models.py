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