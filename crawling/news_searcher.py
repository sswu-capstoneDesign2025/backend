# 키워드로 뉴스 검색해서 URL 리스트 가져오기
# crawling\news_searcher.py

import random
import requests
import json
import urllib.parse
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import httpx
import asyncio

load_dotenv()  # .env 파일 로드

client_id = os.getenv("NAVER2_CLIENT_ID")
client_secret = os.getenv("NAVER2_CLIENT_SECRET")

# 쿼리에서 완전히 제거할 불필요한 단어
IRRELEVANT_STOPWORDS = {
    # 일반적인 불용어
    '그리고', '그래서', '어떻게', '요청', '해주세요', '좀', '그냥', '많이',
    '조금', '뭐', '어떤지', '알려줘', '있잖아', '아니', '제발', '아주', '정말',
    '너무', '그', '저기', '그거', '이거', '거기', '저거', '알겠어', '알았어', 
    '혹시', '약간', '대충', '자세히', '빨리', '급하게', '천천히', '간단히',
    '정확히', '있어', '없어', '보여줘', '보여', '줘', '부탁해', '부탁', '찾아줘',
    '찾아봐', '해줘', '해봐', '지금', '오늘', '어제', '내일', '모레',
    
    # 질문 관련 단어
    '언제', '어디서', '누가', '무엇을', '왜', '어떻게', '어떤', '얼마나',

    # 요청 형태의 문장 종결어
    '해', '할래', '할까', '할래요', '할까요', '주세요', '줄래', '줄까요', '알려', '보여',

    # 감탄사/부가적 단어
    '음', '어', '아', '헐', '흠', '오', '와', '이야', '참', '정말로', '진짜로', '솔직히'
}
# 시간 관련 단어
TIME_KEYWORDS = {'오늘', '어제', '지금', '방금', '최근', '현재'}
TIME_OFFSET = {'오늘': 0, '지금': 0, '방금': 0, '현재': 0, '어제': 1, '최근': 0}

with open("data/korea_location_hierarchy.json", encoding="utf-8") as f:
    LOCATION_MAP = json.load(f)

def clean_keyword(raw: str) -> str:
    """
    IRRELEVANT_STOPWORDS 제거, 시간단어는 남겨둠
    """
    tokens = [t for t in raw.split() if t not in IRRELEVANT_STOPWORDS]
    return " ".join(tokens) if tokens else raw

# 샘플 인물 리스트
person_keywords = [
    # 정치 인물
    '윤석열', '이재명', '김기현', '한동훈', '이낙연', '홍준표', '유승민', '안철수', '오세훈', '원희룡',
    '추미애', '박지원', '심상정', '조국', '한덕수', '정은경', '박근혜', '문재인', '이명박', '노무현',
    '전두환', '김대중', '김영삼',

    # 해외 정치인
    '바이든', '트럼프', '시진핑', '김정은', '김여정', '푸틴', '기시다', '마크롱', '메르켈',
    '젤렌스키', '나렌드라 모디', '보리스 존슨', '리시 수낙', '올라프 숄츠', '카말라 해리스',

    # 경제계 유명 인사
    '이재용', '정의선', '최태원', '구광모', '신동빈', '엘론 머스크', '마크 저커버그', '제프 베이조스', 
    '팀 쿡', '손정의', '워런 버핏', '빌 게이츠', '잭 마',

    # 연예·스포츠 유명 인사
    '손흥민', '이강인', '김연아', '류현진', '이정후', '임영웅', 'BTS', '블랙핑크', '유재석', 
    '아이유', '전지현', '송중기', '현빈', '이병헌', '차은우',

    # 기타 사회적으로 유명한 인물
    '조코비치', '페더러', '메시', '호날두', '박항서', '손석희', '이국종', '백종원', '강형욱',
    '윤여정', '봉준호', '황선우', '추신수'
]

# 샘플 지역 리스트
location_keywords = [
    '서울', '부산', '대구', '광주', '인천', '울산', '대전', '세종', '수원', '성남',
    '고양', '용인', '창원', '청주', '전주', '포항', '여수', '천안', '안산', '제주',
    '강릉', '춘천', '평창', '경주', '군산', '목포', '진주', '김해', '양산',
    
    # 북한 주요 지역 (뉴스에 자주 등장)
    '평양', '개성', '함흥', '신의주',

    # 해외 주요 도시 (자주 등장)
    '뉴욕', '워싱턴', '베이징', '상하이', '도쿄', '오사카', '런던', '파리', '베를린',
    '모스크바', '홍콩', '싱가포르', '두바이', '로스앤젤레스', '실리콘밸리'
]

# 샘플 경제 키워드
economy_keywords = [
    # 국내 주요 기업·그룹
    '삼성', 'LG', '현대자동차', '기아', 'SK하이닉스', '카카오', '네이버', '롯데', '한화', '포스코', '쿠팡', '셀트리온',
    'CJ', 'KT', '신세계', '아모레퍼시픽', '하나은행', '신한은행', 'KB국민은행',

    # 해외 기업
    '애플', '테슬라', '엔비디아', '아마존', '구글', '알파벳', '넷플릭스', '메타', '마이크로소프트', '페이스북',
    '화웨이', '샤오미', '텐센트', '알리바바',

    # 주요 경제지표·분야
    '코스피', '코스닥', '나스닥', '다우존스', 'S&P500', '주식시장', '증시', '환율', '금리', '물가', '인플레이션',
    '부동산', '아파트 가격', '전세', '월세', '주택시장', '청약', '분양',

    # 금융·기술 이슈
    '비트코인', '이더리움', '암호화폐', '가상화폐', 'NFT', '블록체인', '핀테크', '스타트업', '창업', '벤처기업',
    '유니콘', 'IPO', '공모주', '한국은행', '미국 증시', '중국 경제', '무역수지', '수출입',

    # 글로벌 경제 상황
    '경제 위기', '침체', '호황', '불황', '구조조정', '실업률', '고용', '경기침체', '반도체', '자동차 산업', '조선업'
]

environment_keywords = {"미세먼지", "황사", "초미세먼지", "대기질"}


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
    environment_patterns = [
        f"{keyword} 농도",
        f"{keyword} 상황",
        f"{keyword} 예보",
        f"{keyword} 상태",
        f"{keyword} 환경 뉴스"
    ]
    general_patterns = [
        f"{keyword} 최신 뉴스",
        f"{keyword} 관련 이슈",
        f"{keyword} 최신 소식",
        f"{keyword} 이슈 정리"
    ]

    if keyword in person_keywords or '대통령' in keyword:
        return random.choice(person_patterns)
    elif keyword in location_keywords:
        return random.choice(location_patterns)
    elif keyword in economy_keywords:
        return random.choice(economy_patterns)
    elif keyword in environment_keywords:
        return random.choice(environment_patterns)
    else:
        return random.choice(general_patterns)
    



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

async def _fetch_items(client: httpx.AsyncClient, url: str) -> list[dict]:
    """단일 URL에서 JSON 아이템을 가져오고 실패 시 빈 리스트 리턴"""
    try:
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        return r.json().get("items", [])
    except Exception:
        return []

async def _fetch_for_keyword(
    client: httpx.AsyncClient,
    raw_keyword: str,
    max_per_keyword: int
) -> tuple[str, list[str]]:
    # 1) 기존 clean_keyword, token 분리, date_offset 계산
    keyword = clean_keyword(raw_keyword if isinstance(raw_keyword, str) else " ".join(raw_keyword))
    tokens = keyword.split()
    date_offset = next((TIME_OFFSET[t] for t in tokens if t in TIME_KEYWORDS), None)

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    urls_to_try: list[str] = []

    # 2) 위치 키워드 있을 때
    loc = next((t for t in tokens if t in LOCATION_MAP), None)
    if loc:
        for loc_variant in expand_location(loc):
            query = build_and_query([loc_variant] + [t for t in tokens if t != loc])
            urls_to_try.append(
                f"https://openapi.naver.com/v1/search/news"
                f"?query={query}&display={max_per_keyword}&sort=date"
            )
    # 3) 위치 없으면 일반 키워드 패턴
    else:
        pattern = refine_keyword_for_search(keyword)
        q = urllib.parse.quote(pattern)
        urls_to_try.append(
            f"https://openapi.naver.com/v1/search/news"
            f"?query={q}&display={max_per_keyword}&sort=date"
        )

    # 4) 후보 URL들 병렬 요청 → 첫 결과가 있으면 사용
    tasks = [_fetch_items(client, url) for url in urls_to_try]
    for items in await asyncio.gather(*tasks):
        if items:
            break
    else:
        items = []

    # 5) 날짜 필터링
    if date_offset is not None:
        target = (datetime.now() - timedelta(days=date_offset)).date()
        items = [
            it for it in items
            if datetime.strptime(it.get("pubDate", ""), "%a, %d %b %Y %H:%M:%S %z").date() == target
        ]
    print(f"🧪 refined query: {pattern}")
    print(f"🔗 request URL: {urls_to_try}")

    return keyword, [it["link"] for it in items]

async def search_news_by_keywords(
    keywords: list[str],
    max_per_keyword: int = 3
) -> dict[str, list[str]]:
    """
    비동기 httpx.AsyncClient + asyncio.gather로
    키워드별·위치별 검색을 병렬 처리합니다.
    """
    results: dict[str, list[str]] = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        tasks = [
            _fetch_for_keyword(client, kw, max_per_keyword)
            for kw in keywords
        ]
        for keyword, links in await asyncio.gather(*tasks):
            results[keyword] = links
    return results