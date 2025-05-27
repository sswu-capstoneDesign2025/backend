# crawling/rank_news.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def fetch_naver_trending_news(limit=3):
    """
    네이버 뉴스 홈의 '많이 본 뉴스'를 크롤링하여 상위 기사 링크와 제목을 반환합니다.
    """
    url = "https://news.naver.com/main/ranking/popularDay.naver"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        result = []

        # 언론사별 랭킹 박스 순회
        for box in soup.select("div.rankingnews_box"):
            ul = box.select_one("ul.rankingnews_list")
            if not ul:
                continue

            for li in ul.select("li")[:limit]:
                a_tag = li.find("a")
                if not a_tag:
                    continue

                title = a_tag.get_text(strip=True)
                link = urljoin(url, a_tag["href"])  # 상대경로 보정
                result.append({"title": title, "url": link})

                if len(result) >= limit:
                    return result

        return result

    except Exception as e:
        print(f"❌ 크롤링 실패: {e}")
        return []
