# 텍스트가 뉴스 요청인지, 개인 이야기인지 판단하는 기능

import re

def classify_user_input(text: str) -> str:
    """
    사용자의 입력 텍스트를 분류한다.
    - 뉴스 요청이면 "news"
    - 개인 이야기이면 "story"
    """

    # 뉴스 요청 관련 키워드 패턴 (예시)
    news_keywords = [
        "뉴스", "기사", "속보", "보도", "이슈", "정보 알려줘", "최신 소식", "기사 알려줘", "기사 읽어줘", "소식"
    ]

    # 뉴스 키워드가 하나라도 포함되면 'news'로 분류
    for keyword in news_keywords:
        if keyword in text:
            return "news"

    # 기본은 'story'로 분류
    return "story"
