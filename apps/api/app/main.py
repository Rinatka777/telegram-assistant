#uvicorn apps.api.app.main:app --reload --port 8000
#python3 -m apps.bot.run_bot

from pathlib import Path
from datetime import datetime
from typing import List
import uuid
import os
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query, Body
from sqlalchemy.orm import Session
from .db import engine, Base, get_db
from . import models, crud, schemas, ai_service
from apps.api.app.extraction import extract_text_generic
from fastapi.responses import FileResponse

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "service": "api"}

@app.get("/notes/{note_id}/download")
def download_note(
        note_id: int,
        db: Session = Depends(get_db),
):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    file_path = Path(note.attachment_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File missing from disk")

    return FileResponse(file_path)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/notes/search", response_model=list[schemas.NoteSearchResult])
def search_notes(
    q: str = Query(..., min_length=1),
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):

    raw_notes = crud.search_notes(db, user_id=user_id, search_term=q)
    results = []

    for note in raw_notes:
        display_name = os.path.basename(note.attachment_path)

        preview_text = generate_snippet(note.full_text, q)

        result_object = schemas.NoteSearchResult(
            id=note.id,
            created_at=note.created_at,
            filename=display_name,
            match_preview=preview_text
        )
        results.append(result_object)

    return results


@app.get("/notes/{note_id}", response_model=schemas.NoteOut)
def read_note(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

def generate_snippet(text: str, term: str) -> str:
    text_lower = text.lower()
    term_lower = term.lower()
    start_idx = text_lower.find(term_lower)

    if start_idx == -1:
        return text[:50] + "..."

    start = max(0, start_idx - 30)
    end = start_idx + len(term) + 30

    snippet = text[start:end]
    return snippet




@app.post("/tasks", response_model=schemas.TaskOut)
def create_task(
    task_in: schemas.TaskCreate,
    db: Session = Depends(get_db),
):
    task = crud.create_task(db, task_in)
    return task

@app.get("/tasks", response_model=list[schemas.TaskOut])
def list_tasks(
    user_id: int = Query(...),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    tasks = crud.list_tasks(db, user_id=user_id, status=status)
    return tasks


@app.post("/tasks/{task_id}/complete", response_model=schemas.TaskOut)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.complete_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/attachments")
async def upload_attachments(
    files: List[UploadFile] = File(...),
    user_id: int = Query(..., description="Telegram user id"),
    db: Session = Depends(get_db),
):
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum number of files is 10")

    os.makedirs("data/files", exist_ok=True)
    results = []

    for file in files:
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join("data", "files", unique_filename)

        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        text = ""

        try:
            text = extract_text_generic(Path(file_path))
        except Exception:
            text = ""

        ai_summary = ai_service.summarize_text(text)

        preview = text[:300] if text else ""

        note_in = schemas.NoteCreate(
            user_id=user_id,
            attachment_path=str(file_path),
            full_text=text,
            summary=ai_summary
        )
        note = crud.create_note(db, note_in=note_in)

        results.append({
            "success": True,
            "original_filename": file.filename,
            "stored_filename": unique_filename,
            "content_type": file.content_type,
            "size": len(contents),
            "upload_time": datetime.utcnow().isoformat(),
            "location": str(file_path),
            "note_id": note.id,
            "text_preview": preview,
        })

    return {"uploaded": results}


@app.post("/chat")
async def chat(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    found_notes = crud.search_notes(db, user_id=request.user_id)
    if not found_notes:
        print("Search failed. Switching to Recent Files Context.")
        found_notes = crud.get_user_notes(db, user_id=request.user_id, limit=3)
    texts = []
    for note in found_notes:
        texts.append(note.full_text)

    if texts:
        context_block = "\n\n".join(texts)
    else:
        context_block = ""
    return ai_service.answer_user_question(context_block, request.question)

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    temp_filename = f"temp_{uuid.uuid4()}.ogg"
    file_path = os.path.join("data", "files", temp_filename)
    os.makedirs("data/files", exist_ok=True)
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    text = ai_service.transcribe_audio(file_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    return {"text": text}


@app.delete("/notes")
async def clear_notes(user_id: int, db: Session = Depends(get_db)):
    count = crud.delete_user_notes(db, user_id=user_id)

    print(f"🗑️ DEBUG: Deleting notes for user {user_id}. Rows deleted: {count}")

    return {"message": f"Deleted {count} notes."}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.app.main:app", host="0.0.0.0", port=8000, reload=True)