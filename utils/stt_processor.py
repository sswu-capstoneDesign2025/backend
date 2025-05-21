# utils/stt_processor.py
import os
import requests
from urllib.parse import urlparse
import json
from dotenv import load_dotenv
load_dotenv(override=True)

DOMAIN_ID     = os.getenv("DOMAIN_ID", "").strip()
INVOKE_SECRET = os.getenv("CLOVA_INVOKE_SECRET", "").strip()
HEADER_SECRET = os.getenv("CLOVA_SPEECH_SECRET", "").strip()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def transcribe_audio_from_url(file_url: str) -> str:
    parsed = urlparse(file_url)
    if not parsed.path.startswith("/static/"):
        raise Exception("❌ 이 방식은 서버 내부 static 경로에서만 동작합니다.")

    local_path = os.path.join(BASE_DIR, parsed.path.lstrip("/"))
    if not os.path.isfile(local_path):
        raise Exception(f"❌ 파일 없음: {local_path}")

    invoke_url = (
        f"https://clovaspeech-gw.ncloud.com/external/v1/"
        f"{DOMAIN_ID}/{INVOKE_SECRET}/recognizer/upload"
    )

    headers = {
        "X-CLOVASPEECH-API-KEY": HEADER_SECRET,
    }

    files = {
        "media": open(local_path, "rb"),
        "params": (None, json.dumps({
            "language": "ko-KR",
            "completion": "sync",
            "fullText": True,
            "wordAlignment": True,
        }), "application/json"),
    }

    response = requests.post(invoke_url, headers=headers, files=files)

    if response.status_code == 200:
        result = response.json()
        if result.get("result") not in ("SUCCESS", "COMPLETED"):
            raise Exception(f"❌ CLOVA 응답 실패: {result}")

        # 성공 시 텍스트 추출
        return result.get("text", "")
