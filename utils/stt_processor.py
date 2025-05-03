from dotenv import load_dotenv
import os
import requests

# 환경변수 로드
load_dotenv(override=True)

DOMAIN_ID     = os.getenv("DOMAIN_ID", "").strip()
INVOKE_SECRET = os.getenv("CLOVA_INVOKE_SECRET", "").strip()
HEADER_SECRET = os.getenv("CLOVA_SPEECH_SECRET", "").strip()

assert DOMAIN_ID,     "❌ DOMAIN_ID 로드 실패"
assert INVOKE_SECRET, "❌ Invoke URL용 시크릿 로드 실패"
assert HEADER_SECRET, "❌ 헤더용 시크릿 로드 실패"

def transcribe_audio_from_url(file_url: str) -> str:
    """
    CLOVA Speech-to-Text API를 사용해
    주어진 음성 파일 URL을 텍스트로 변환하여 반환합니다.
    예외 발생 시 에러 메시지로 Exception을 raise합니다.
    """
    # Invoke URL 조립
    invoke_url = (
        f"https://clovaspeech-gw.ncloud.com/external/v1/"
        f"{DOMAIN_ID}/{INVOKE_SECRET}/recognizer/url"
    )

    headers = {
        "Content-Type": "application/json",
        "X-CLOVASPEECH-API-KEY": HEADER_SECRET,
    }

    payload = {
        "url":        file_url,
        "language":   "ko-KR",
        "completion": "sync",
    }

    # 요청 보내기
    response = requests.post(invoke_url, headers=headers, json=payload)

    # 응답 처리
    if response.status_code == 200:
        data = response.json()
        result = data.get("result")
        if result in ("COMPLETED", "SUCCEEDED"):
            return data.get("text", "").strip()
        else:
            error_msg = data.get("message", "Unknown error")
            raise Exception(f"❌ 변환 실패 [{result}]: {error_msg}")
    else:
        raise Exception(f"❌ HTTP 오류 {response.status_code}: {response.text}")
