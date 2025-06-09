# routers/processing_router.py
#음성 입력 종합 처리 라우터

import os
import uuid
import re
import httpx
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import time
from utils.stt_processor import transcribe_audio_from_url
from database import SessionLocal
from routers.search_router import search_news_urls, UserRequest
from crawling.weather_fetcher import get_weather, normalize_location_name
from crawling.news_searcher import expand_location
from utils.story_handler import handle_story_interaction


router = APIRouter(prefix="/process", tags=["Audio Processing"])

UPLOAD_DIR = "./static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def classify_with_model(text: str) -> str:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://localhost:8000/classify", json={"text": text})
            if response.status_code == 200:
                data = response.json()
                label = data.get("label", "")
                confidence = data.get("confidence", 0)
                if label in ["이야기", "뉴스", "날씨"] and confidence > 0.5:
                    return {"이야기": "story", "뉴스": "news", "날씨": "weather"}[label]
        except Exception as e:
            print(f"❌ 입력 분류 API 실패: {e}")
    return "invalid"


@router.post("/audio/")
async def process_audio(
    file: UploadFile = File(...),
    session_state: str = Form("initial"),
    username: str | None = Form(None)
):
    start_total = time.time()
    print("🟢 [전체 시작]")

    # 1. 파일 저장
    start = time.time()
    filename = f"{uuid.uuid4().hex}.wav"
    path = os.path.join(UPLOAD_DIR, filename)
    try:
        with open(path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(500, f"파일 저장 실패: {e}")
    file_url = f"http://10.50.101.143:8000/static/uploads/{filename}"
    print(f"📁 [파일 저장] 완료: {time.time() - start:.2f}s")
    
    
    # 2. STT 처리
    start = time.time()
    try:
        text = transcribe_audio_from_url(file_url)
        if not text:  
            raise HTTPException(400, "음성에서 텍스트를 추출하지 못했습니다.")
    except Exception as e:
        raise HTTPException(500, f"STT 실패: {e}")
    print(f"🗣️ [STT 완료] 텍스트: {text[:20]}... / 시간: {time.time() - start:.2f}s")


    # 3. 분류 (story / news / weather)
    start = time.time()
    input_type = await classify_with_model(text)
    print(f"📦 [입력 분류] → {input_type} / 시간: {time.time() - start:.2f}s")

    if input_type not in ["story", "news", "weather"]:
        if session_state == "invalid_repeat":
            return {
                "type": "invalid",
                "transcribed_text": text,
                "response": "못 알아듣겠어요.",
                "next_state": "initial"
            }
        return {
            "type": "invalid",
            "transcribed_text": text,
            "response": "알아듣지 못했어요. 다시 말해줄래요?",
            "next_state": "invalid_repeat"
        }

    # 4. 분기 처리
    if input_type == "story":
        result = await handle_story_interaction(text, session_state, username)
        if result is not None:
            result["transcribed_text"] = text
            return result


    if input_type == "weather":
        try:
            # 1. 지역 추출
            location_parts = expand_location(text)
            full_location = " ".join(reversed(location_parts[:-1])) if len(location_parts) > 1 else "대한민국"
            full_location = normalize_location_name(full_location)
            full_location = clean_location_name(full_location)
            print(f"🧭 날씨 지역 추출 결과: {full_location}")

            # 2. 시점 추론
            lowered = text.lower()
            when = "오늘"
            if "내일" in lowered:
                when = "내일"
            elif "모레" in lowered:
                when = "모레"
            elif "이번주" in lowered or "이번 주" in lowered:
                when = "이번주"
            elif "다음주" in lowered or "다음 주" in lowered:
                when = "다음주"
            elif "이번달" in lowered or "이번 달" in lowered:
                when = "이번달"
            elif "다음달" in lowered or "다음 달" in lowered:
                when = "다음달"

            # 3. 요약 문자열 얻기
            summary_text = get_weather(full_location, when=when)
        except Exception as e:
            raise HTTPException(500, f"날씨 정보 수집 실패: {e}")

        # 4. TTS 생성
        tts_url = await get_tts_audio_url(summary_text)
        return {
            "type": "weather",
            "transcribed_text": text,
            "response": {
                "location": full_location,
                "when": when,
                "summary": summary_text
            },
            "response_text": summary_text,
            "response_audio_url": tts_url,
            "next_state": "initial"
        }

    if input_type == "news":
        result = await search_news_urls(UserRequest(request_text=text))
        print(f"📰 [뉴스 검색/요약 완료] / 시간: {time.time() - start:.2f}s")
        start = time.time()
        try:
            combined = result.get("combined_summary", "")
            if not isinstance(combined, str) or "요약 실패" in combined:
                raise ValueError("통합 요약이 유효하지 않습니다.")
        except Exception as e:
            raise HTTPException(500, f"뉴스 요약 텍스트 추출 실패: {e}")

        tts_url = await get_tts_audio_url(combined)
        print(f"🔊 [TTS 생성 완료] / 시간: {time.time() - start:.2f}s")

        print(f"✅ [전체 처리 완료] / 총 시간: {time.time() - start_total:.2f}s")

        return {
            "type": "news",
            "transcribed_text": text,
            "result": result,
            "response_text": combined, 
            "response_audio_url": tts_url,
            "next_state": "initial"
        }


async def get_tts_audio_url(text: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:8000/tts/synthesize", json={"text": text})
        if response.status_code != 200:
            raise Exception(f"TTS 요청 실패: {response.text}")
        return response.json()["file_url"]
    

def clean_location_name(text: str) -> str:
    """
    '동선동2가 날씨 알려줘' → '동선동2가' 같은 실질적 지역명만 추출
    """
    # 날씨 앞까지 자르기
    if "날씨" in text:
        text = text.split("날씨")[0].strip()
    
    # 숫자+가 대응 (동선동2가 등), 또는 '동 + 한글숫자 + 가'
    # 예: 동선동 이가 → 동선동2가 로 normalize된 상태 기준
    match = re.search(r"(\w+동\s*\d*가?)", text)
    if match:
        return match.group(1).strip()
    
    # 그냥 마지막 '동'까지 자르기
    match = re.search(r"(\w+동)", text)
    if match:
        return match.group(1).strip()
    
    return text.strip()  # fallback
