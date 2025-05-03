# (뉴스 URL 리스트 → 쉬운 요약)

from fastapi import APIRouter
from pydantic import BaseModel
from crawling.newscrawling import crawl_news
from utils.text_processor import process_text_with_gpt

router = APIRouter()

class URLListRequest(BaseModel):
    urls: list

@router.post("/summarize-news-from-urls/")
async def summarize_news_from_urls(url_list_request: URLListRequest):
    """
    뉴스 URL 리스트를 받아
    각각 본문 크롤링 후 쉬운 요약을 반환합니다.
    """
    summaries = []

    for url in url_list_request.urls:
        news_content = crawl_news(url)
        if news_content:
            _, _, easy_summary = process_text_with_gpt(news_content)

            summaries.append({
                "url": url,
                "summary": easy_summary
            })

    return {
        "news_summaries": summaries
    }
