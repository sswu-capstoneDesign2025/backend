# (자연어 입력 → 뉴스 URL 검색)
from fastapi import FastAPI, Depends
from fastapi import APIRouter
from pydantic import BaseModel
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from models import Base, OtherUserRecord

router = APIRouter()
Base.metadata.create_all(bind=engine)

# Dependency - DB 연결
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class OtherUserRecordCreate(BaseModel):
    title: str
    content: str
    author: str
    profileUrl: str | None = None

@router.post("/other-user-records/")
def create_other_user_record(record: OtherUserRecordCreate, db: Session = Depends(get_db)):
    db_record = OtherUserRecord(
        title=record.title,
        content=record.content,
        author=record.author,
        profileUrl=record.profileUrl
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return {
        "message": "Other user record saved!",
        "record": {
            "id": db_record.id,
            "date": db_record.date.strftime("%Y-%m-%d"),
            "title": db_record.title,
            "content": db_record.content,
            "author": db_record.author,
            "profileUrl": db_record.profileUrl or "https://i.pravatar.cc/150?img=1"
        }
    }

@router.get("/other-user-records/")
def get_other_user_records(db: Session = Depends(get_db)):
    records = db.query(OtherUserRecord).order_by(OtherUserRecord.date.desc()).all()
    return [
        {
            "date": r.date,
            "title": r.title,
            "content": r.content,
            "author": r.author,
            "profileUrl": r.profileUrl
        } for r in records
    ]

@router.delete("/other-user-records/")
def delete_all_other_user_records(db: Session = Depends(get_db)):
    deleted_count = db.query(OtherUserRecord).delete()
    db.commit()
    return {
        "message": f"모든 기록이 삭제되었습니다.",
        "deleted_count": deleted_count
    }
