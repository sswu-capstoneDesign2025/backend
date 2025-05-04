from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import Base, ProcessedText
from database import SessionLocal, engine
from utils.text_processor import process_text_with_gpt
from routers import search_router, summarize_router, stt_router
from routers import auth_router
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
app.include_router(auth_router.router)


# ===== 모델 정의 =====
class UserText(BaseModel):
    text: str

# 1. 일반 텍스트 처리 API
@app.post("/process-text/")
async def process_user_text(user_text: UserText, db: Session = Depends(get_db)):
    standardized_text, cleaned_text, summary_text = process_text_with_gpt(user_text.text)

    db_obj = ProcessedText(
        original_text=user_text.text,
        standardized_text=standardized_text,
        cleaned_text=cleaned_text,
        summary_text=summary_text
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    return {
        "message": "Text processed and saved successfully!",
        "data": {
            "original": user_text.text,
            "standardized": standardized_text,
            "cleaned": cleaned_text,
            "summary": summary_text
        }
    }
