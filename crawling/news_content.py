# 기사 본문 크롤링 함수

import requests
from bs4 import BeautifulSoup, Tag

def get_article_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        article = None

        # ── 1) MBN 전용 처리 ──
        if "mbn.co.kr" in url:
            # (a) 먼저 메타 description 확인
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                return meta_desc["content"].strip()

        # ── 2) 노컷뉴스 ──
        if "nocutnews.co.kr" in url:
            article = soup.select_one("div#pnlContent")
        # ── 3) 연합뉴스 ──
        elif "yna.co.kr" in url:
            for sel in ("#articleFailoverContent", "#articleWrap", "#articleContent"):
                article = soup.select_one(sel)
                if article and article.get_text(strip=True):
                    break

        # ── 4) 일반적인 fallback ──
        if not article:
            article = soup.select_one("#dic_area") or soup.find("article")
        if not article:
            article = soup.find("div", class_=lambda x: x and "content" in x)

        # ── 5) 불필요 요소 제거 및 텍스트 반환 ──
        if article:
            for bad in article.select("script, style, aside, .ad"):
                bad.decompose()
            text = article.get_text(separator=" ", strip=True)
            return text if text else "본문이 비어 있습니다."

        return "본문을 불러올 수 없습니다."

    except Exception as e:
        return f"에러 발생: {e}"
