# routers/stt_router.py
# 음성 파일 URL을 텍스트로 변환

import logging
from fastapi import APIRouter
from pydantic import BaseModel 
from utils.stt_processor import transcribe_audio_from_url

logger = logging.getLogger("uvicorn.error")

router = APIRouter()


class TranscribeRequest(BaseModel):
    file_url: str

@router.post("/transcribe/")
async def transcribe(req: TranscribeRequest): 
    file_url = req.file_url  
    logger.info(f"[STT] 받은 file_url: {file_url}")
    text = transcribe_audio_from_url(file_url)
    logger.info(f"[STT] 변환된 텍스트: {text}")
    return {"transcribed_text": text}