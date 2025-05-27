import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from google.cloud import texttospeech
from dotenv import load_dotenv
load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

OUTPUT_DIR = "./static/tts"
VOICE_NAME = "ko-KR-Standard-A"
os.makedirs(OUTPUT_DIR, exist_ok=True)

router = APIRouter(prefix="/tts", tags=["Text-to-Speech"])

class TTSRequest(BaseModel):
    text: str
    voice: str | None = None

@router.post("/synthesize")
async def synthesize_tts(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="텍스트가 비어 있습니다.")

    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=request.text)

        voice_config = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name=request.voice or VOICE_NAME,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16  # WAV
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_config,
            audio_config=audio_config
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"tts_{timestamp}.wav"
        file_path = os.path.join(OUTPUT_DIR, filename)

        with open(file_path, "wb") as out:
            out.write(response.audio_content)

        return {"message": "음성 생성 성공", "file_url": f"/static/tts/{filename}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 처리 실패: {e}")
