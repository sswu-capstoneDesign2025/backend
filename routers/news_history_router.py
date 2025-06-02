from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import SessionLocal
from models import NewsHistory
from datetime import date
from pydantic import BaseModel

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class NewsHistoryRequest(BaseModel):
    username: str
    keyword: str
    summary: str

@router.post("/news-history")
def save_news_history(request: NewsHistoryRequest, db: Session = Depends(get_db)):
    record = NewsHistory(
        username=request.username,
        keyword=request.keyword,
        summary=request.summary,
        date=date.today()
    )
    db.add(record)
    db.commit()
    return {"message": "저장 완료"}

@router.get("/news-history")
def get_news_history(username: str = Query(...), db: Session = Depends(get_db)):
    records = db.query(NewsHistory).filter(NewsHistory.username == username).order_by(NewsHistory.date.desc()).all()
    return {
        "records": [
            {
                "date": r.date.strftime("%Y.%m.%d"),
                "keyword": r.keyword,
                "summary": r.summary,
            }
            for r in records
        ]
    }  