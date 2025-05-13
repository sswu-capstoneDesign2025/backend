# 키워드로 뉴스 검색해서 URL 리스트 가져오기

import requests
from bs4 import BeautifulSoup
import random
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로드

client_id = os.getenv("NAVER_CLIENT_ID")
client_secret = os.getenv("NAVER_CLIENT_SECRET")


# 샘플 인물 리스트
person_keywords = [
    '윤석열', '이재명', '바이든', '트럼프', '김정은', '시진핑', '푸틴', '조코비치', '엘론 머스크',
    '김여정', '한덕수', '조 바이든', '마크롱', '기시다', '정은경', '오세훈', '박형준', '유승민',
    '안철수', '홍준표', '이낙연', '추미애', '조국', '문재인', '박근혜', '이명박'
]

# 샘플 지역 리스트
location_keywords = [
    '서울', '부산', '대구', '광주', '인천', '울산', '대전', '세종', '수원', '성남',
    '고양', '용인', '창원', '청주', '전주', '포항', '여수', '천안', '안산', '제주',
    '강릉', '춘천', '평창', '경주', '군산', '목포', '진주', '김해', '양산'
]

# 샘플 경제 키워드
economy_keywords = [
    '삼성', 'LG', '코스피', '나스닥', '카카오', '네이버', '현대자동차', '기아', 'SK하이닉스',
    '애플', '테슬라', '엔비디아', '아마존', '구글', '넷플릭스', '비트코인', '이더리움', '은행',
    '주식시장', '환율', '금리', '코인', '부동산', '미국 증시', '한국은행', '월스트리트'
]


def refine_keyword_for_search(keyword: str) -> str:
    """
    키워드를 검색 친화적으로 정제하는 함수
    - 키워드 종류(인물, 사건, 지역, 경제 등)에 따라 다른 패턴 적용
    """

    # 기본 패턴 (기타)
    general_patterns = [
        f"{keyword} 최신 뉴스",
        f"{keyword} 관련 이슈",
        f"{keyword} 최신 소식",
        f"{keyword} 이슈 정리",
    ]

    # 인물 패턴
    person_patterns = [
        f"{keyword} 발언",
        f"{keyword} 인터뷰",
        f"{keyword} 관련 기사",
        f"{keyword} 최근 행보"
    ]

    # 장소 패턴
    location_patterns = [
        f"{keyword} 지역 뉴스",
        f"{keyword} 현지 소식",
        f"{keyword} 최근 소식",
        f"{keyword} 이슈"
    ]

    # 경제 패턴
    economy_patterns = [
        f"{keyword} 주가 뉴스",
        f"{keyword} 시장 반응",
        f"{keyword} 경제 뉴스",
        f"{keyword} 관련 동향"
    ]

    # 키워드 종류별 분류
    if keyword in person_keywords:
        return random.choice(person_patterns)
    elif keyword in location_keywords:
        return random.choice(location_patterns)
    elif keyword in economy_keywords:
        return random.choice(economy_patterns)
    else:
        return random.choice(general_patterns)

def search_news_by_keywords(keywords: list[str], max_per_keyword: int = 3) -> dict:
    """
    키워드 리스트를 받아서
    각 키워드별로 뉴스 URL max_per_keyword개씩 가져오는 함수
    """
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

    results = {}

    for keyword in keywords:
        query = urllib.parse.quote(keyword)
        url = f"https://openapi.naver.com/v1/search/news?query={query}&display={max_per_keyword}&start=1&sort=sim"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            urls = [item["originallink"] for item in data["items"]]
            results[keyword] = urls
        except Exception as e:
            print(f"[ERROR] {keyword} 실패: {e}")
            results[keyword] = []

    return results

