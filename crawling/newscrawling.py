# 뉴스 크롤링 기능 (ipynb → py 변환)

import requests
from bs4 import BeautifulSoup

def crawl_news(url: str) -> str:
    """
    주어진 URL에서 뉴스 본문만 추출하는 함수
    """
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 기사 본문 찾기 - 여기서는 예시로 'article' 태그 사용
        article = soup.find('article')
        if article:
            paragraphs = article.find_all('p')
            news_content = "\n".join([p.get_text(strip=True) for p in paragraphs])
        else:
            # fallback: div 태그 기반
            paragraphs = soup.find_all('p')
            news_content = "\n".join([p.get_text(strip=True) for p in paragraphs])

        return news_content

    except Exception as e:
        print(f"Error occurred while crawling news: {e}")
        return ""
