# routers/processing_router.py
#음성 입력 종합 처리 라우터

import os
import uuid
import asyncio
import re
import httpx
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import time
from utils.stt_processor import transcribe_audio_from_url
from utils.input_classifier import classify_user_input
from utils.story_cleaner import process_user_story
from database import SessionLocal
from models import SummaryNote
from routers.search_router import search_news_urls, UserRequest
from crawling.weather_fetcher import get_current_weather, get_weather, normalize_location_name
from crawling.news_searcher import expand_location

router = APIRouter(prefix="/process", tags=["Audio Processing"])

UPLOAD_DIR = "./static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

    if session_state == "awaiting_story":
        if not username:
            raise HTTPException(400, "Username is required to save story")
        try:
            story_data = process_user_story(text)
            cleaned = story_data["cleaned_story"] 
        except Exception as e:
            raise HTTPException(500, f"스토리 클리닝 실패: {e}")
        db: Session = next(get_db())
        note = SummaryNote(
            sum_title="사용자 이야기",
            content=cleaned, 
            username=username
        )
        db.add(note); db.commit(); db.refresh(note)
        return {
            "type": "story",
            "transcribed_text": text,
            "response": "고마워, 이야기 잘 들었어!",
            "next_state": "complete"
        }

    # 3. 분류 (story / news / weather)
    start = time.time()
    input_type = classify_user_input(text)
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
        if session_state == "initial":
            if re.search(r"내가.*(이야기|얘기)", text):
                response_text = "그래, 어떤 이야기야?"
                tts_url = await get_tts_audio_url(response_text)
                return {
                    "type": "story",
                    "transcribed_text": text,
                    "response": response_text,
                    "response_audio_url": tts_url,
                    "next_state": "awaiting_story"
                }

            response_text = "너가 재밌는 얘기해줄래? 아니면 내가 해줄까?"
            tts_url = await get_tts_audio_url(response_text)
            return {
                "type": "story",
                "transcribed_text": text,
                "response": response_text,
                "response_audio_url": tts_url,
                "next_state": "awaiting_choice"
            }

        if session_state == "awaiting_choice":
            normalized_text = re.sub(r"[^\w\s]", "", text).strip()

            user_offer_patterns = r"(내가\s*(할게|해볼게|할래|한다고|얘기해줄게|얘기할게|이야기할게|시작할게|말할게|말해줄게|말할래|얘기해볼게|얘기할래|이야기해볼게|이야기할래|해줄게|할게요|해볼게요|하겠어))"
            story_request_patterns = r"(너[가는]?\s*)?(해줘|얘기(해)?줘|이야기(해)?줘|말(해)?줘|들려줘|재밌는 얘기\s*해줘|얘기\s*좀\s*해줘|뭐\s*재밌는\s*얘기\s*없어)"

            if re.search(user_offer_patterns, normalized_text):
                response_text = "그래, 어떤 이야기야?"
                tts_url = await get_tts_audio_url(response_text)
                return {
                    "type": "story",
                    "transcribed_text": text,
                    "response": response_text,
                    "response_audio_url": tts_url,
                    "next_state": "awaiting_story"
                }
            
            elif re.search(story_request_patterns, text):
                from random import choice
                import requests

                r = requests.get("http://localhost:8000/other-user-records/")
                stories = r.json()
                if stories:
                    selected = choice(stories)
                    response_text = f"그럼 내가 해줄게! {selected['title']}... {selected['content']}"
                    tts_url = await get_tts_audio_url(response_text)
                    return {
                        "type": "story",
                        "response": response_text,
                        "response_audio_url": tts_url,
                        "next_state": "complete"
                    }
                
                response_text = "아직 들려줄 이야기가 없어. 너가 하나 말해줄래?"
                tts_url = await get_tts_audio_url(response_text)
                return {
                    "type": "story",
                    "response": response_text,
                    "response_audio_url": tts_url,
                    "next_state": "awaiting_choice"
                }

        if session_state == "awaiting_story":
            if not username:
                raise HTTPException(400, "Username is required to save story")

            try:
                story_data = process_user_story(text)
            except Exception as e:
                raise HTTPException(500, f"GPT 처리 실패: {e}")

            cleaned = story_data['cleaned_story']
            region = story_data.get('region', '없음')
            topic = story_data.get('topic', '기타')

            # DB 저장
            import requests
            res = requests.post("http://localhost:8000/other-user-records/", json={
                "title": f"[{region}] {topic} 이야기",
                "content": cleaned,
                "author": username,
                "region": region,
                "topic": topic
            })
            if res.status_code != 200:
                raise HTTPException(500, f"DB 저장 실패: {res.text}")

            response_text = "좋은 이야기 고마워! 잘 저장해둘게."
            tts_url = await get_tts_audio_url(response_text)

            return {
                "type": "story",
                "response": response_text,
                "response_audio_url": tts_url,
                "next_state": "complete"
            }    
        return {
            "type": "story",
            "response": "알 수 없는 상태입니다.",
            "next_state": "initial"
        }



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