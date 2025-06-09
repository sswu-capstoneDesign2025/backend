# routers/search_router.py

from fastapi import APIRouter
from pydantic import BaseModel
from crawling.news_searcher import search_news_by_keywords
from crawling.news_content import get_article_content
from utils.keyword_extractor import extract_keyword_from_text
from utils.text_processor import summarize_article_pipeline, combine_summaries_into_story
from crawling.weather_fetcher import get_weather
from utils.time_parser import parse_korean_time_expr
from crawling.rank_news import fetch_naver_trending_news
import asyncio
from utils.news_processor import MASSaC

router = APIRouter()

class UserRequest(BaseModel):
    request_text: str

def relevance_score(content: str, keyword: str) -> int:
    """
    키워드 토큰이 본문에 등장할 때마다 +1
    → 점수 1 이상이면 '관련 있음'으로 간주
    """
    lower_content = content.lower()
    return sum(1 for token in keyword.split() if token.lower() in lower_content)

async def summarize_safe(url, content, query):
    try:
        return await summarize_article_pipeline(url, content, query)
    except Exception as e:
        print(f"❗ 요약 실패 (url={url}): {e}")
        return None


async def get_top3_summarized_articles(result_dict: dict, user_query: str) -> list:
    keywords = result_dict.get("keywords", [])
    results = result_dict.get("results", {})

    if not keywords:
        return [{"url": "", "summary": "키워드를 추출할 수 없습니다."}]

    first_keyword = keywords[0]
    urls = results.get(first_keyword, [])[:10]

    summaries = []

    for url in urls:
        content = get_article_content(url)
        if not content or "에러 발생" in content:
            continue
        if relevance_score(content, first_keyword) == 0:
            continue
        summary = await summarize_safe(url, content, user_query)
        if summary:
            summaries.append({"url": url, "summary": summary})

    if not summaries:
        summaries.append({"url": "", "summary": "관련된 기사를 요약할 수 없습니다."})

    return summaries


@router.post("/search-news-urls/")
async def search_news_urls(user_request: UserRequest):
    text = user_request.request_text
    keywords = extract_keyword_from_text(text)

    # 인기 뉴스 조건이면 일반 뉴스는 무시
    if set(keywords) & {"오늘", "인기"}:
        # 1) 상위 6개 중 최대 3개 기사 원문 가져오기
        raw_articles = fetch_naver_trending_news(limit=6)
        url_text_pairs: list[tuple[str,str]] = []
        for article in raw_articles:
            if len(url_text_pairs) >= 3:
                break
            content = get_article_content(article["url"])
            if content:
                url_text_pairs.append((article["url"], content))

        # 2) 요약+쉬운말+통합 (MASSaC)
        if not url_text_pairs:
            return {
                "keywords": keywords,
                "summaries": [{"url": "", "summary": "인기 뉴스 요약에 실패했습니다."}],
                "combined_summary": "인기 뉴스 요약에 실패했습니다."
            }
        proc = await MASSaC(url_text_pairs)
        summaries = [
            {"url": url, "summary": summary}
            for (url, _), summary in zip(url_text_pairs, proc["summaries"])
        ]
        return {
            "keywords": keywords,
            "Detailed articles": [{"url": url} for url, _ in url_text_pairs],
            "summaries": summaries,
            "combined_summary": "오늘 많이 본 뉴스를 요약해서 알려드릴게요.\n" + proc["combined"]
        }


    # 일반 뉴스 키워드 처리
    news_results = await search_news_by_keywords(keywords)
    # 1) 상위 6개 중 relevance 체크하여 최대 3개 기사 원문 가져오기
    first_kw = keywords[0] if keywords else ""
    urls = news_results.get(first_kw, [])[:6]
    url_text_pairs = []
    from routers.search_router import relevance_score
    for url in urls:
        if len(url_text_pairs) >= 3:
            break
        content = get_article_content(url)
        if not content or relevance_score(content, first_kw) == 0:
            continue
        url_text_pairs.append((url, content))

    # 2) 요약+쉬운말+통합 (MASSaC)
    if not url_text_pairs:
        return {
            "keywords": keywords,
            "summaries": [{"url": "", "summary": "관련된 기사를 요약할 수 없습니다."}],
            "combined_summary": "관련된 기사를 요약할 수 없습니다."
        }
    proc = await MASSaC(url_text_pairs)
    summaries = [
        {"url": url, "summary": summary}
        for (url, _), summary in zip(url_text_pairs, proc["summaries"])
    ]
    return {
        "keywords": keywords,
        "summaries": summaries,
        "combined_summary": proc["combined"]
    }