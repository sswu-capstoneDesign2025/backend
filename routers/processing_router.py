# routers/processing_router.py
#음성 입력 종합 처리 라우터

import os
import uuid
import asyncio
import re

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

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
    session_state: str = Form("initial"),           # 대화 상태
    username: str | None = Form(None)               # 이야기 저장 시 필요
):
    # 1. 파일 저장 (생략—이전 코드와 동일)
    filename = f"{uuid.uuid4().hex}.wav"
    path = os.path.join(UPLOAD_DIR, filename)
    try:
        with open(path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(500, f"파일 저장 실패: {e}")
    file_url = f"http://10.50.101.143:8000/static/uploads/{filename}"

    # 2. STT 처리
    try:
        text = transcribe_audio_from_url(file_url)
    except Exception as e:
        raise HTTPException(500, f"STT 실패: {e}")

    # 3. 분류 (story / news / weather)
    input_type = classify_user_input(text)
    # 3-1. 기대 키워드에 해당하지 않으면 invalid 처리
    if input_type not in ["story","news","weather"]:
        # session_state가 invalid_repeat면 두 번째 실패
        if session_state == "invalid_repeat":
            resp = "못 알아듣겠어요."
            next_s = "initial"
        else:
            resp = "알아듣지 못했어요. 다시 말해줄래요?"
            next_s = "invalid_repeat"

        return {
            "type": "invalid",
            "transcribed_text": text,
            "response": resp,
            "next_state": next_s
        }

    # 4. 분기 처리
    if input_type == "story":
        # ─── 초기 질문 ──────────────────────
        if session_state == "initial":
            return {
                "type": "story",
                "transcribed_text": text,
                "response": "너가 재밌는 얘기해줄래? 아니면 내가 해줄까?",
                "next_state": "awaiting_choice"
            }

        # ─── 사용자의 선택 처리 ───────────────
        if session_state == "awaiting_choice":
            # "내가" 포함 여부로 분기
            user_offer_patterns = r"((내가\s*)?(할게|얘기(해)?(볼게|할래|할게)?|이야기(해)?(볼게|할래|할게)?|말(해줄게|할게|할래)?|해줄게|할래|해볼게|시작할게))"
            story_request_patterns = (
                r"(너[가는]?\s*)?(해줘|얘기(해)?줘|이야기(해)?줘|말(해)?줘|들려줘|재밌는 얘기\s*해줘|얘기\s*좀\s*해줘|뭐\s*재밌는\s*얘기\s*없어)"
            )
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

        # ─── 사용자가 이야기 입력 ─────────────
        if session_state == "awaiting_story":
            if not username:
                raise HTTPException(400, "Username is required to save story")
            # GPT로 정제
            try:
                cleaned = clean_user_story(text)
            except Exception as e:
                raise HTTPException(500, f"스토리 클리닝 실패: {e}")
            # DB 저장
            db: Session = next(get_db())
            note = SummaryNote(sum_title="사용자 이야기", content=cleaned)
            db.add(note); db.commit(); db.refresh(note)
            return {
                "type": "story",
                "transcribed_text": text,
                "response": "고마워, 이야기 잘 들었어!",
                "next_state": "complete"
            }

        # ─── 그 외 상태 ──────────────────────
        return {
            "type": "story",
            "response": "알 수 없는 상태입니다.",
            "next_state": "initial"
        }

    # ─── news / weather 처리 (기존 로직 재사용) ─────
    if input_type == "weather":
        weather_summary = await search_news_urls(UserRequest(request_text=text))
        return {
            "type": "weather",
            "transcribed_text": text,
            "response": weather_summary,
            "next_state": "initial"
        }

    if input_type == "news":
        result = await search_news_urls(UserRequest(request_text=text))
        return {
            "type": "news",
            "transcribed_text": text,
            "result": result,
            "next_state": "initial"
        }
    
    raise HTTPException(500, "Unhandled input_type")