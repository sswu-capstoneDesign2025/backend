# routers/stt_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from utils.stt_processor import transcribe_audio_from_url
from utils.input_classifier import classify_user_input
from utils.keyword_extractor import extract_keyword_from_text
from crawling.news_searcher import search_news_by_keywords
from crawling.newscrawling import crawl_news
from utils.text_processor import process_text_with_gpt
from database import SessionLocal
from models import ProcessedText

router = APIRouter()

# DB 연결
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/transcribe-and-handle/")
async def transcribe_and_handle(
    file_url: str,
    speaker_id: str,
    db: Session = Depends(get_db)
):
    """
    1. 음성 파일 URL을 텍스트로 변환
    2. 텍스트 분류 (뉴스 요청 or 개인 이야기)
    3. 분류 결과에 따라 처리
    """
    # 1) 음성 → 텍스트 변환
    text = transcribe_audio_from_url(file_url)

    # 2) 분류: 뉴스 요청인지, 개인 이야기인지
    category = classify_user_input(text)

    if category == "news":
        # ─ 뉴스 요청 흐름 ─
        keywords = extract_keyword_from_text(text)  # 핵심 키워드 뽑기
        news_search_result = search_news_by_keywords(keywords)  # 키워드별 뉴스 URL 검색

        news_summaries = {}
        for keyword, urls in news_search_result.items():
            summaries = []
            for url in urls:
                body = crawl_news(url)
                if body:
                    _, _, easy_summary = process_text_with_gpt(body)
                    summaries.append({
                        "url": url,
                        "summary": easy_summary
                    })
            news_summaries[keyword] = summaries

        return {
            "category": "news",
            "original_text": text,
            "news_summaries": news_summaries
        }

    else:
        # ─ 개인 스토리 처리 흐름 ─
        standardized, cleaned, summary = process_text_with_gpt(text)

        # DB에 저장 (speaker 포함)
        db_obj = ProcessedText(
            speaker=speaker_id,
            original_text=text,
            standardized_text=standardized,
            cleaned_text=cleaned,
            summary_text=summary
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return {
            "category": "story",
            "original_text": text,
            "processed": {
                "standardized": standardized,
                "cleaned": cleaned,
                "summary": summary
            },
            "id": db_obj.id
        }
