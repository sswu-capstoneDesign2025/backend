# routers/stt_router.py

from fastapi import APIRouter
from utils.stt_processor import transcribe_audio_from_url

router = APIRouter()

@router.post("/transcribe/")
async def transcribe(file_url: str):
    """
    음성 파일 URL을 텍스트로 변환합니다.
    """
    text = transcribe_audio_from_url(file_url)
    return {
        "transcribed_text": text
    }
