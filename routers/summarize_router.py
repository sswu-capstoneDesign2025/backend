# (뉴스 본문 리스트 → 쉬운 요약)

from fastapi import APIRouter
from pydantic import BaseModel
from utils.text_processor import simplify_article_content, combine_summaries_into_story

router = APIRouter()

class Article(BaseModel):
    url: str
    content: str

class ArticleListRequest(BaseModel):
    keyword: str
    articles: list[Article]

@router.post("/summarize-news-from-urls/")
async def summarize_news_from_urls(article_list_request: ArticleListRequest):
    simplified_summaries = []

    for article in article_list_request.articles:
        simplified = simplify_article_content(article.content)
        simplified_summaries.append(simplified)

    full_story = combine_summaries_into_story(simplified_summaries)

    return {
        "keyword": article_list_request.keyword,
        "news_summary": full_story
    }
