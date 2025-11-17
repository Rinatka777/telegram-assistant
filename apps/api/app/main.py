from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
from datetime import datetime
import uuid
import os
from .db import engine, Base
from . import models
from apps.api.app.extraction import extract_text_generic

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "service": "api"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/attachments")
async def upload_attachments(files: List[UploadFile] = File(...)):
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

        preview = text[:300] if text else ""

        results.append({
            "success": True,
            "original_filename": file.filename,
            "stored_filename": unique_filename,
            "content_type": file.content_type,
            "size": len(contents),
            "upload_time": datetime.utcnow().isoformat(),
            "location": str(file_path),
            "text_preview": preview,
        })

    return {"uploaded": results}

#python3 -m uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.app.main:app", host="0.0.0.0", port=8000, reload=True)