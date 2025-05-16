# 사용자가 준 문장에서 핵심 키워드 뽑아내기
# utils/keyword_extractor.py

from konlpy.tag import Okt

okt = Okt()

# 불용어 정의
STOPWORDS = {
    "우리나라", "최신", "뉴스", "관련", "기사", "좀", "말해봐", "알려줘", "해주세요",
    "지금", "그럼", "그래서", "이야기", "내용", "정보", "최근"
}

def extract_keyword_from_text(text: str, top_n: int = 3) -> list[str]:
    """
    1) Okt로 명사만 뽑아서 tokens 리스트 생성
    2) tokens로부터 2-gram, 3-gram 키워드 후보 생성
    3) 긴 n-gram, '뉴스' 포함 구문 우선 정렬
    4) 부족하면 단어 단위로 보충
    5) 불용어 및 부분어 제거
    """
    # 1) 명사 추출 + 불용어 필터링
    tokens = [w for w, pos in okt.pos(text)
              if pos == "Noun" and len(w) > 1 and w not in STOPWORDS]

    phrase_scores = {}

    # 2) 2-gram, 3-gram 생성
    for n in (3, 2):
        for i in range(len(tokens) - n + 1):
            ng = tokens[i : i + n]
            phrase = " ".join(ng)
            KEYWORD_BOOST = {"뉴스", "날씨"}
            score = phrase_scores.get(phrase, 0) + (
                2 if any(k in ng for k in KEYWORD_BOOST) else 1
            )
            phrase_scores[phrase] = score

    # 3) 정렬
    sorted_phrases = sorted(
        phrase_scores.items(),
        key=lambda x: (len(x[0].split()), x[1]),
        reverse=True
    )
    result = [p for p, _ in sorted_phrases[:top_n]]

    # 4) 부족하면 단어 보충
    for w in tokens:
        if len(result) >= top_n:
            break
        if w not in result:
            result.append(w)

    # 5) 부분어 제거
    result.sort(key=len, reverse=True)
    pruned = []
    for kw in result:
        if any(kw != keep and kw in keep for keep in pruned):
            continue
        pruned.append(kw)

    return pruned[:top_n] or [text.strip()]
