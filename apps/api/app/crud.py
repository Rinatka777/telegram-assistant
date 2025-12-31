from datetime import datetime
from sqlalchemy.orm import Session
from . import models, schemas


def create_note(db: Session, note_in: schemas.NoteCreate) -> models.Note:
    db_note = models.Note(
        user_id=note_in.user_id,
        attachment_path=note_in.attachment_path,
        full_text=note_in.full_text,
        summary=note_in.summary
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

def search_notes(db: Session, user_id: int, limit: int = 3)-> list[models.Note]:
    return db.query(models.Note)\
        .filter(models.Note.user_id == user_id)\
        .order_by(models.Note.created_at.desc())\
        .limit(limit)\
        .all()

def get_note(db: Session, note_id: int) -> models.Note | None:
    return db.query(models.Note).filter(models.Note.id == note_id).first()

def create_task(db: Session, task_in: schemas.TaskCreate) -> models.Task:
    db_task = models.Task(
        user_id=task_in.user_id,
        title=task_in.title,
        due_at=task_in.due_at,
        note_id=task_in.note_id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def list_tasks(
    db: Session,
    user_id: int,
    status: str | None = None,
) -> list[models.Task]:
    q = db.query(models.Task).filter(models.Task.user_id == user_id)
    if status:
        q = q.filter(models.Task.status == status)
    return q.order_by(models.Task.due_at.is_(None), models.Task.due_at).all()


def complete_task(db: Session, task_id: int) -> models.Task | None:
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None
    task.status = "done"
    task.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task

def delete_user_notes(db: Session, user_id: int) -> int:
    """Deletes notes and returns the count of deleted items."""
    # .delete() returns the number of rows matched/deleted
    num_deleted = db.query(models.Note).filter(models.Note.user_id == user_id).delete()
    db.commit()
    return num_deleted

def get_user_notes(db: Session, user_id: int, limit: int = 3):
    """Fetch the most recent notes for a user, regardless of content."""
    return db.query(models.Note)\
        .filter(models.Note.user_id == user_id)\
        .order_by(models.Note.created_at.desc())\
        .limit(limit)\
        .all()