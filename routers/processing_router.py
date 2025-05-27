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
from utils.story_cleaner import clean_user_story
from database import SessionLocal
from models import SummaryNote
from routers.search_router import search_news_urls, UserRequest

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
            cleaned = clean_user_story(text)
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
                return {
                    "type": "story",
                    "transcribed_text": text,
                    "response": "그래, 어떤 이야기야?",
                    "next_state": "awaiting_story"
                }
            return {
                "type": "story",
                "transcribed_text": text,
                "response": "너가 재밌는 얘기해줄래? 아니면 내가 해줄까?",
                "next_state": "awaiting_choice"
            }

        if session_state == "awaiting_choice":
            user_offer_patterns = r"(내가\s*(할게|해볼게|할래|한다고|얘기해줄게|얘기할게|이야기할게|시작할게|말할게|말해줄게|말할래|얘기해볼게|얘기할래|이야기해볼게|이야기할래|해줄게|할게요|해볼게요|하겠어))"
            story_request_patterns = r"(너[가는]?\s*)?(해줘|얘기(해)?줘|이야기(해)?줘|말(해)?줘|들려줘|재밌는 얘기\s*해줘|얘기\s*좀\s*해줘|뭐\s*재밌는\s*얘기\s*없어)"
            if re.search(user_offer_patterns, text):
                return {
                    "type": "story",
                    "transcribed_text": text,
                    "response": "그래, 어떤 이야기야?",
                    "next_state": "awaiting_story"
                }
            elif re.search(story_request_patterns, text):
                return {
                    "type": "story",
                    "response": "그럼 내가 해줄게! 오늘의 이야기는…",
                    "next_state": "complete"
                }

        return {
            "type": "story",
            "response": "알 수 없는 상태입니다.",
            "next_state": "initial"
        }

    if input_type == "weather":
        weather_summary = await search_news_urls(UserRequest(request_text=text))
        try:
            summary_text = weather_summary["summaries"][0]["summary"]["summary"]
        except Exception as e:
            raise HTTPException(500, f"날씨 요약 텍스트 추출 실패: {e}")
        tts_url = await get_tts_audio_url(summary_text)
        return {
            "type": "weather",
            "transcribed_text": text,
            "response": weather_summary,
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