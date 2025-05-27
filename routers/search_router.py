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

def get_top3_summarized_articles(result_dict: dict, user_query: str) -> list:
    keywords = result_dict.get("keywords", [])
    results = result_dict.get("results", {})

    if not keywords:
        return [{"url": "", "summary": "키워드를 추출할 수 없습니다."}]

    first_keyword = keywords[0]
    urls = results.get(first_keyword, [])[:20]  # 최대 20개 후보 확보

    summaries = []

    for url in urls:
        content = get_article_content(url)
        if not content or "에러 발생" in content:
            continue


        # 키워드 관련성 확인
        if relevance_score(content, first_keyword) == 0:
            continue

        try:
            # 2단계 파이프라인으로 요약
            summary = summarize_article_pipeline(content, user_query)
            summaries.append({"url": url, "summary": summary})
        except Exception as e:
            summaries.append({"url": url, "summary": f"요약 실패: {e}"})

        if len(summaries) == 3:
            break

    if not summaries:
        summaries.append({
            "url": "",
            "summary": f"'{first_keyword}' 관련 기사를 찾지 못했습니다."
        })

    return summaries

@router.post("/search-news-urls/")
async def search_news_urls(user_request: UserRequest):
    text = user_request.request_text
    keywords = extract_keyword_from_text(text)

    # 날씨 요청 처리
    if any("날씨" in kw for kw in keywords):
        when, offset = parse_korean_time_expr(text)
        loc_token = keywords[0].replace("날씨", "").strip()
        weather_summary = get_weather(loc_token, when, offset)
        return {
            "keywords": [f"{loc_token} 날씨"],
            "summaries": [{"url": "", "summary": weather_summary}],
            "combined_summary": weather_summary
        }

    # 뉴스 검색
    # "오늘 인기" 요청은 랭킹 크롤링으로 처리
    if set(keywords) & {"오늘", "인기"}:
        raw_articles = fetch_naver_trending_news(limit=3)
        summaries = []

        for article in raw_articles:
            content = get_article_content(article["url"])
            if not content:
                continue
            summary = summarize_article_pipeline(content, text)
            summaries.append({"url": article["url"], "summary": summary})

        combined_story = combine_summaries_into_story([s["summary"] for s in summaries])
        return {
            "keywords": keywords,
            "summaries": summaries,
            "combined_summary": f"오늘 많이 본 뉴스 {len(summaries)}건을 알려드릴게요.\n{combined_story}"
        }

    # 일반 뉴스 검색 처리
    news_results = await search_news_by_keywords(keywords)
    result_dict = {"keywords": keywords, "results": news_results}

    # 1) 개별 기사 요약 3개
    article_summaries = get_top3_summarized_articles(result_dict, text)

    # 2) 요약문만 모아서 종합 기사 생성
    summary_texts = [item["summary"] for item in article_summaries]
    combined_story = combine_summaries_into_story(summary_texts)

    return {
        "keywords": keywords,
        "summaries": article_summaries,       # 3개의 요약 리스트
        "combined_summary": combined_story    # 묶은 뉴스 한 편
    }
