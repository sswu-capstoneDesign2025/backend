from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from models import Base, ProcessedText, SummaryNote, OtherUserRecord
from database import SessionLocal, engine
from utils.text_processor import process_text_with_gpt
from routers import search_router, summarize_router, stt_router, story_router, otherstory_router
from datetime import datetime

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
# class OtherUserRecordCreate(BaseModel):
#     title: str
#     content: str
#     author: str
#     profileUrl: str | None = None

# @app.post("/other-user-records/")
# def create_other_user_record(record: OtherUserRecordCreate, db: Session = Depends(get_db)):
#     db_record = OtherUserRecord(
#         title=record.title,
#         content=record.content,
#         author=record.author,
#         profileUrl=record.profileUrl
#     )
#     db.add(db_record)
#     db.commit()
#     db.refresh(db_record)
#     return {
#         "message": "Other user record saved!",
#         "record": {
#             "id": db_record.id,
#             "date": db_record.date.strftime("%Y-%m-%d"),
#             "title": db_record.title,
#             "content": db_record.content,
#             "author": db_record.author,
#             "profileUrl": db_record.profileUrl or "https://i.pravatar.cc/150?img=1"
#         }
#     }

# @app.get("/other-user-records/")
# def get_other_user_records(db: Session = Depends(get_db)):
#     records = db.query(OtherUserRecord).order_by(OtherUserRecord.date.desc()).all()
#     return [
#         {
#             "date": r.date,
#             "title": r.title,
#             "content": r.content,
#             "author": r.author,
#             "profileUrl": r.profileUrl
#         } for r in records
#     ]