from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
import shutil
from pathlib import Path
import uuid
from datetime import datetime
from apps.bot.handlers import DocumentHandler


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
app = FastAPI()

doc_validator = DocumentHandler(max_size=25 * 1024 * 1024)

@app.get("/health")
def health() -> dict[str, str]:
    return {"message": "FastAPI File Upload Service is running"}

@app.post("/attachment/single")
async def upload_attachment(file: UploadFile):
    validation = await doc_validator.validate_file(file)

    if not validation["valid"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "File validation failed",
                "errors": validation["errors"]
            }
        )

    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR/unique_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

    return {
        "success": True,
        "original_filename": file.filename,
        "stored_filename": unique_filename,
        "content_type": file.content_type,
        "size": file.size,
        "upload_time": datetime.utcnow().isoformat(),
        "location": str(file_path)
    }

@app.post("/attachment/multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    if len(files) > 10:
        raise HTTPException(
            status_code = 400,
            detail = "Maximum number of files is 10"
        )

    results = []
    # Validate each file
    for file in files:
        validation = await doc_validator.validate_file(file)
        if not validation["valid"]:
            results.append({
                "filename": file.filename,
                "success": False,
                "errors": validation["errors"]
            })
            continue

    # Save valid files
    for file in files:
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR/unique_filename
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            results.append({
                "filename": file.filename,
                "success": True,
                "stored_filename": unique_filename,
                "location": str(file_path)
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": [f"Failed to save: {str(e)}"]
            })

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    return{
        "total_files": len(files),
        "successful": len(successful),
        "failed": len(failed),
        "upload_time": datetime.utcnow().isoformat(),
        "results": results
    }