from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from models import Base, ProcessedText, SummaryNote, OtherUserRecord
from database import SessionLocal, engine
from routers import search_router, summarize_router, stt_router, story_router, otherstory_router, auth_router
from datetime import datetime
from dotenv import load_dotenv
import logging

# 로깅 기본 설정
logging.basicConfig(
    level=logging.INFO,  # 개발 중엔 DEBUG도 가능
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

load_dotenv()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*",]
)

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# Dependency - DB 연결
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Router 등록
app.include_router(search_router.router)
app.include_router(summarize_router.router)
app.include_router(stt_router.router)
app.include_router(story_router.router)
app.include_router(otherstory_router.router)
app.include_router(auth_router.router)


