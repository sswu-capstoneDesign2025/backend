# 키워드로 뉴스 검색해서 URL 리스트 가져오기
# crawling\news_searcher.py

import random
import requests
import json
import urllib.parse
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로드

client_id = os.getenv("NAVER2_CLIENT_ID")
client_secret = os.getenv("NAVER2_CLIENT_SECRET")

# 쿼리에서 완전히 제거할 불필요한 단어
IRRELEVANT_STOPWORDS = {'그리고', '그래서', '어떻게', '요청', '해주세요'}
# 시간 관련 단어
TIME_KEYWORDS = {'오늘', '어제', '지금'}
TIME_OFFSET = {'오늘': 0, '지금': 0, '어제': 1}

def clean_keyword(raw: str) -> str:
    """
    IRRELEVANT_STOPWORDS 제거, 시간단어는 남겨둠
    """
    tokens = [t for t in raw.split() if t not in IRRELEVANT_STOPWORDS]
    return " ".join(tokens) if tokens else raw

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
    person_patterns = [
        f"{keyword} 발언",
        f"{keyword} 인터뷰",
        f"{keyword} 관련 기사",
        f"{keyword} 최근 행보"
    ]
    general_patterns = [
        f"{keyword} 최신 뉴스",
        f"{keyword} 관련 이슈",
        f"{keyword} 최신 소식",
        f"{keyword} 이슈 정리",
    ]
    location_patterns = [
        f"{keyword} 지역 뉴스",
        f"{keyword} 현지 소식",
        f"{keyword} 최근 소식",
        f"{keyword} 이슈"
    ]
    economy_patterns = [
        f"{keyword} 주가 뉴스",
        f"{keyword} 시장 반응",
        f"{keyword} 경제 뉴스",
        f"{keyword} 관련 동향"
    ]

    if keyword in person_keywords or '대통령' in keyword:
        return random.choice(person_patterns)
    elif keyword in location_keywords:
        return random.choice(location_patterns)
    elif keyword in economy_keywords:
        return random.choice(economy_patterns)
    else:
        return random.choice(general_patterns)
    

with open("data/korea_location_hierarchy.json", encoding="utf-8") as f:
    LOCATION_MAP = json.load(f)


def build_and_query(tokens: list[str]) -> str:
    """
    ['미아동', '날씨'] → '"미아동"+"날씨"' (정확 AND 검색)
    """
    return urllib.parse.quote("+".join(f'"{t}"' for t in tokens if t))


def expand_location(token: str) -> list[str]:
    """
    행정동 위치 토큰을 ['동', '구', '시', '대한민국'] 등으로 확장
    - JSON 기반 매핑: 값이 리스트(부모 계층) 형태이므로,
      한번에 불러와서 chain에 붙여줍니다.
    """
    chain = [token]
    # LOCATION_MAP[token]이 바로 ['구','시','대한민국'] 리스트
    parents = LOCATION_MAP.get(token, [])
    for parent in parents:
        if parent and parent not in chain:
            chain.append(parent)
    # 안전장치: 마지막에 '대한민국'이 없으면 추가
    if chain[-1] != "대한민국":
        chain.append("대한민국")
    return chain


def search_news_by_keywords(keywords: list[str], max_per_keyword: int = 3) -> dict:
    """
    각 키워드(문장)에서 위치 단어 자동 탐색 → 단계 확장 → 뉴스 검색
    시간 키워드가 있다면 해당 날짜로 필터링
    """
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

    results: dict[str, list[str]] = {}

    for raw_keyword in keywords:
        if isinstance(raw_keyword, list):
            raw_keyword = " ".join(raw_keyword)

        keyword = clean_keyword(raw_keyword)
        tokens = keyword.split()
        if not tokens:
            results[keyword] = []
            continue

        # 1) 시간 키워드 탐색 → 날짜 필터링용 offset 설정
        date_offset = None
        for time_kw in TIME_KEYWORDS:
            if time_kw in tokens:
                date_offset = TIME_OFFSET[time_kw]
                break

        # 2) 위치 키워드 탐색
        loc_token = None
        for token in tokens:
            if token in LOCATION_MAP:
                loc_token = token
                break

        # 3) 검색 URL 생성
        if not loc_token:
            pattern = refine_keyword_for_search(keyword)
            q = urllib.parse.quote(pattern)
            url = (
                "https://openapi.naver.com/v1/search/news"
                f"?query={q}&display={max_per_keyword}&sort=date"
            )
        else:
            rest_tokens = [t for t in tokens if t != loc_token]
            loc_variants = expand_location(loc_token)
            urls: list[str] = []
            items: list[dict] = []

            for loc in loc_variants:
                query_tokens = [loc] + rest_tokens
                query = build_and_query(query_tokens)
                print(f"DEBUG ▶ 시도하는 쿼리: {urllib.parse.unquote(query)}")
                url = (
                    "https://openapi.naver.com/v1/search/news"
                    f"?query={query}&display={max_per_keyword}&sort=date"
                )
                try:
                    resp = requests.get(url, headers=headers, timeout=5)
                    resp.raise_for_status()
                    items = resp.json().get("items", [])
                    print(f"DEBUG ▶ {loc} 단계에서 반환된 기사 수: {len(items)}")
                    if items:
                        break
                except Exception as e:
                    print(f"[ERROR] {keyword} ({loc}) 검색 실패: {e}")
                    items = []

            # 4) 시간 필터링
            if date_offset is not None:
                target_date = (datetime.now() - timedelta(days=date_offset)).date()
                filtered = []
                for it in items:
                    try:
                        pub = datetime.strptime(it.get("pubDate", ""), "%a, %d %b %Y %H:%M:%S %z")
                        if pub.date() == target_date:
                            filtered.append(it)
                    except Exception:
                        continue
                items = filtered

            results[keyword] = [it["link"] for it in items]
            continue

        # 5) 일반 키워드 검색 (위치 없는 경우)
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            resp.raise_for_status()
            items = resp.json().get("items", [])
        except Exception:
            results[keyword] = []
            continue

        # 6) 시간 필터링
        if date_offset is not None:
            target_date = (datetime.now() - timedelta(days=date_offset)).date()
            filtered = []
            for it in items:
                try:
                    pub = datetime.strptime(it.get("pubDate", ""), "%a, %d %b %Y %H:%M:%S %z")
                    if pub.date() == target_date:
                        filtered.append(it)
                except Exception:
                    continue
            items = filtered

        # 7) 링크 추출
        results[keyword] = [it["link"] for it in items]

    return results
