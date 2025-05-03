# 사용자가 준 문장에서 핵심 키워드 뽑아내기

from konlpy.tag import Okt

okt = Okt()

def extract_keyword_from_text(text: str) -> list:
    """
    사용자가 준 문장에서 의미 있는 키워드(명사)를 뽑아 리스트로 반환
    - 1글자 짧은 단어 제거
    - 불용어(stopwords) 필터링
    """
    stopwords = ['오늘', '내일', '어제', '지금', '방금', '이번', '다음', '지난']

    # 명사만 추출
    nouns = okt.nouns(text)

    # 1글자 제외 + stopwords 제외
    nouns = [noun for noun in nouns if len(noun) > 1 and noun not in stopwords]

    # 키워드가 하나도 없으면 전체 텍스트 반환
    if not nouns:
        return [text.strip()]

    return nouns
