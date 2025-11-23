from sqlalchemy.orm import Session
from . import models, schemas

def create_note(db: Session, note_in: schemas.NoteCreate) -> models.Note:
    db_note = models.Note(
        user_id=note_in.user_id,
        attachment_path=note_in.attachment_path,
        full_text=note_in.full_text,
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

def get_note(db: Session, note_id: int) -> models.Note | None:
    return db.query(models.Note).filter(models.Note.id == note_id).first()

def create_task

def list_tasks

def complete_task
