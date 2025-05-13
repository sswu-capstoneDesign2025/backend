from fastapi import APIRouter
from pydantic import BaseModel
from crawling.news_searcher import search_news_by_keywords
from crawling.news_content import get_article_content
from utils.keyword_extractor import extract_keyword_from_text
from utils.text_processor import simplify_article_content  # ✅ 요약 함수 추가

router = APIRouter()

class UserRequest(BaseModel):
    request_text: str

# 뉴스 본문 + 요약 처리 함수
def get_top3_summarized_articles(result_dict: dict) -> list:
    keywords = result_dict.get("keywords", [])
    results = result_dict.get("results", {})

    if not keywords:
        return [{"url": "", "summary": "키워드를 추출할 수 없습니다."}]

    first_keyword = keywords[0]
    urls = results.get(first_keyword, [])[:3]

    summaries = []
    for url in urls:
        content = get_article_content(url)
        if content and "에러 발생" not in content:
            try:
                summary = simplify_article_content(content)
                summaries.append({
                    "url": url,
                    "summary": summary
                })
            except Exception as e:
                summaries.append({
                    "url": url,
                    "summary": f"요약 실패: {e}"
                })

    return summaries

@router.post("/search-news-urls/")
async def search_news_urls(user_request: UserRequest):
    """
    자연어 입력 → 키워드 추출 → 뉴스 URL 검색 → 본문 → GPT 요약 반환
    """
    keywords = extract_keyword_from_text(user_request.request_text)
    news_results = search_news_by_keywords(keywords)

    result_dict = {
        "keywords": keywords,
        "results": news_results
    }

    article_summaries = get_top3_summarized_articles(result_dict)

    return article_summaries
