# 사용자가 준 문장에서 핵심 키워드 뽑아내기
# utils/keyword_extractor.py

import re
from konlpy.tag import Okt
from collections import Counter
from crawling.news_searcher import (
    person_keywords,
    location_keywords,
    economy_keywords,
    environment_keywords
)

okt = Okt()

# 1) 불용어
STOPWORDS = {
    "우리나라", "최신", "뉴스", "관련", "기사", "좀", "말해봐", "알려줘", "해주세요",
    "지금", "그럼", "그래서", "이야기", "내용", "정보", "최근",
    "까지", "부터", "보다", "니다", "이다", "하고", "에도", "에서", "에게",
}

# 2) 경제 전용 지표 키워드
ECONOMY_TOPICS = {
    '금리', '물가', '환율', '실업률', '수출', '수입', '경기침체', '한국은행',
    '기준금리', '고용', '무역수지', '재정적자', '증시', '코스피', '코스닥',
    '부동산', '인플레이션', '청약', '분양', '소득', '임금'
}

# 3) 도메인별 키워드 사전 (사전 키워드 + 전용 토픽 합침)
DOMAIN_VOCABULARY = {
    'economy': set(economy_keywords) | ECONOMY_TOPICS,
    'person': set(person_keywords),
    'location': set(location_keywords),
    'environment': set(environment_keywords),
}

def extract_keyword_from_text(text: str, top_n: int = 3) -> list[str]:
    """
    1) 텍스트 정제
    2) Okt로 명사 추출 + 불용어 제거
    3) 도메인 감지 → 해당 도메인 키워드 우선 반환
    4) 없으면 3-gram/2-gram 조합 (띄어쓰기 유지)
    """
    # 1) 정제
    cleaned = re.sub(r'[^\w\s]', ' ', text)

    # 2) 토큰화
    tokens = [
        w for w, pos in okt.pos(cleaned)
        if pos == "Noun" and len(w) > 1 and w not in STOPWORDS
    ]
    if not tokens:
        return [text.strip()]

    # 3) 도메인 감지 & 사전 키워드 조합
    for domain, vocab in DOMAIN_VOCABULARY.items():
        # 토큰 중에 도메인 어휘가 하나라도 있으면 ‘감지’로 간주
        if any(tok in vocab for tok in tokens):
            specific = [tok for tok in tokens if tok in vocab and any(tok in seg for seg in text.split())]
            return specific[:top_n] if specific else [tokens[0]]

    # 4) n-gram 기반 추출 (띄어쓰기 유지)
    phrase_scores = Counter()
    for n in (3, 2):
        for i in range(len(tokens) - n + 1):
            phrase = " ".join(tokens[i : i + n])
            phrase_scores[phrase] += 1

    # 5) 스코어 정렬
    sorted_phrases = sorted(
        phrase_scores.items(),
        key=lambda x: (x[1], len(x[0].split())),
        reverse=True
    )
    result = [p for p, _ in sorted_phrases[:top_n]]

    # 6) 부족하면 단어 단위 보충
    for w in tokens:
        if len(result) >= top_n:
            break
        if w not in result:
            result.append(w)

    return result[:top_n]


def extract_passages_by_keywords(
    article: str,
    keywords: list[str],
    window: int = 1
) -> str:
    """
    기사 본문을 문장 단위로 쪼갠 뒤,
    keywords에 해당하는 문장과 앞뒤 window 문장만 반환.
    관련 문장이 없으면 원문 전체를 반환합니다.
    """
    sentences = re.split(r'(?<=[.!?])\s+', article)
    matched_idxs = set()

    for kw in keywords:
        for idx, sent in enumerate(sentences):
            if kw.lower() in sent.lower():
                start = max(0, idx - window)
                end = min(len(sentences), idx + window + 1)
                matched_idxs.update(range(start, end))

    if not matched_idxs:
        return article

    return " ".join(sentences[i] for i in sorted(matched_idxs))
