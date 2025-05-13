# (자연어 입력 → 뉴스 URL 검색)

from fastapi import APIRouter
from pydantic import BaseModel
from crawling.news_searcher import search_news_by_keywords
from utils.keyword_extractor import extract_keyword_from_text

router = APIRouter()

class UserRequest(BaseModel):
    request_text: str

@router.post("/search-news-urls/")
async def search_news_urls(user_request: UserRequest):
    """
    자연어 입력받아 키워드를 추출하고,
    키워드로 뉴스 검색하여 URL 리스트를 반환합니다.
    """
    keywords = extract_keyword_from_text(user_request.request_text)  

    news_results = search_news_by_keywords(keywords)

    return {
        "keywords": keywords,
        "results": news_results
    }
