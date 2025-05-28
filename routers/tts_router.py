import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from google.cloud import texttospeech
from dotenv import load_dotenv
load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"

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

        MAX_TTS_LENGTH = 5000
        safe_text = request.text[:MAX_TTS_LENGTH]
        print(f"📝 [TTS 요청 텍스트] {safe_text[:300]}...")

        synthesis_input = texttospeech.SynthesisInput(text=safe_text)

        voice_config = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name=request.voice or VOICE_NAME,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_config,
            audio_config=audio_config
        )

        if len(response.audio_content) < 500:
            raise HTTPException(status_code=500, detail="TTS 응답이 너무 짧습니다.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"tts_{timestamp}.wav"
        file_path = os.path.join(OUTPUT_DIR, filename)

        with open(file_path, "wb") as out:
            out.write(response.audio_content)

        if not os.path.exists(file_path) or os.path.getsize(file_path) < 1000:
            raise HTTPException(status_code=500, detail="TTS 파일 저장 실패 또는 파일이 너무 작습니다.")

        return {"message": "음성 생성 성공", "file_url": f"/static/tts/{filename}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 처리 실패: {e}")
