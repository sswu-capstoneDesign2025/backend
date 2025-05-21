# routers/upload_router.py

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import os
import uuid

router = APIRouter()

UPLOAD_DIR = "./static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/audio/")
async def upload_audio(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4().hex}.wav"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # TODO: 여기를 배포 주소에 맞게 수정
    file_url = f"http://10.50.102.53:8000/static/uploads/{filename}"
    return JSONResponse(content={"file_url": file_url})
