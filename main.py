from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from models import Base, ProcessedText, SummaryNote, OtherUserRecord, NewsHistory  # ✅ NewsHistory 추가
from database import SessionLocal, engine
from routers import search_router, stt_router, story_router, otherstory_router, auth_router, weather_router, tts_router
from routers.user_alert_router import router as user_alert_router
from routers.processing_router import router as processing_router
from routers.news_history_router import router as news_history_router  

from dotenv import load_dotenv
import logging
from fastapi.staticfiles import StaticFiles

# 로깅 기본 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="Capstone API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 테이블 생성 (모든 모델 포함)
Base.metadata.create_all(bind=engine)

# DB 세션 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ 라우터 등록
app.include_router(search_router.router)
app.include_router(stt_router.router)
app.include_router(story_router.router)
app.include_router(otherstory_router.router)
app.include_router(auth_router.router)
app.include_router(user_alert_router)
app.include_router(processing_router)
app.include_router(weather_router.router)
app.include_router(tts_router.router)
app.include_router(news_history_router)

# ✅ 정적 파일 경로 등록
app.mount("/static", StaticFiles(directory="static"), name="static")
