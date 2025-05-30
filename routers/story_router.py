# (자연어 입력 → 뉴스 URL 검색)
# routers\story_router.py

from fastapi import FastAPI, Depends, HTTPException
from fastapi import APIRouter
from pydantic import BaseModel
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from models import Base, SummaryNote
from typing import Optional

router = APIRouter()
Base.metadata.create_all(bind=engine)

# Dependency - DB 연결
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class summaryNoteCreate(BaseModel):
    sum_title: str
    content: str
    topic: Optional[str] = "기타"
    region: Optional[str] = "없음"
    username: Optional[str] = "익명"

from utils.story_cleaner import process_user_story  # 기존과 동일하게 import

@router.post("/summary-notes/")
async def create_summary_note(note: summaryNoteCreate, db: Session = Depends(get_db)):
    username = note.username or "익명"

    db_note = SummaryNote(
        sum_title=note.sum_title,
        content=note.content,
        topic=note.topic or "기타",
        region=note.region or "없음",
        username=username
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    return {
        "message": "Summary note saved!",
        "note": {
            "id": db_note.id,
            "sum_title": db_note.sum_title,
            "content": db_note.content,
            "topic": db_note.topic,
            "region": db_note.region,
            "username": db_note.username,
            "created_at": db_note.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    }


@router.get("/summary-notes/")
def get_all_summary_notes(db: Session = Depends(get_db)):
    notes = db.query(SummaryNote).order_by(SummaryNote.created_at.desc()).all()
    return {
        "notes": [
            {
                "id": note.id,
                "sum_title": note.sum_title,
                "content": note.content,
                "created_at": note.created_at.strftime("%Y-%m-%d %H:%M:%S")
            } for note in notes
        ]
    }