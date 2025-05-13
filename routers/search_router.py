from fastapi import APIRouter
from pydantic import BaseModel
from crawling.news_searcher import search_news_by_keywords
from crawling.news_content import get_article_content
from utils.keyword_extractor import extract_keyword_from_text

router = APIRouter()

class UserRequest(BaseModel):
    request_text: str

# 뉴스 본문 크롤링 함수
def get_top3_article_contents_from_result(result_dict: dict) -> list:
    keywords = result_dict.get("keywords", [])
    results = result_dict.get("results", {})

    if not keywords:
        return ["키워드가 없습니다."]

    first_keyword = keywords[0]
    urls = results.get(first_keyword, [])[:3]

    contents = []
    for url in urls:
        content = get_article_content(url)
        contents.append({
            "url": url,
            "content": content
        })

    return contents

@router.post("/search-news-urls/")
async def search_news_urls(user_request: UserRequest):
    """
    자연어 입력 → 키워드 추출 → 뉴스 URL 검색 → 첫 키워드 상위 3개 뉴스 본문 추출
    """
    keywords = extract_keyword_from_text(user_request.request_text)
    news_results = search_news_by_keywords(keywords)

    result_dict = {
        "keywords": keywords,
        "results": news_results
    }

    article_contents = get_top3_article_contents_from_result(result_dict)

    return {
        "keyword": keywords[0] if keywords else "",
        "articles": article_contents
    }
