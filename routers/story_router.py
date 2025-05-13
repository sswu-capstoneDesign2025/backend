# (자연어 입력 → 뉴스 URL 검색)
from fastapi import FastAPI, Depends
from fastapi import APIRouter
from pydantic import BaseModel
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from models import Base, SummaryNote

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

@router.post("/summary-notes/")
def create_summary_note(note: summaryNoteCreate, db: Session = Depends(get_db)):
    db_note = SummaryNote(
        sum_title=note.sum_title,
        content=note.content
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