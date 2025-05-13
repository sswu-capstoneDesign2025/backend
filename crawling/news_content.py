import requests
from bs4 import BeautifulSoup

# 기사 본문 크롤링 함수
def get_article_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        article = soup.select_one("#dic_area") or soup.find("article")
        if article:
            return article.get_text(strip=True)
        return "본문을 불러올 수 없습니다."
    except Exception as e:
        return f"에러 발생: {e}"
