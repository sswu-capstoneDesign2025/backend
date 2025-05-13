# OpenAI로 텍스트 정제, 요약 처리하는 함수 모듈

import openai
import os
from dotenv import load_dotenv
from openai import OpenAI
import re

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def simplify_article_content(text: str):
    """
    기사 하나를 쉬운 뉴스 문체로 바꿔주는 함수
    """
    prompt = f"""
    아래 뉴스 내용을 너무 어렵지 않게 풀어 설명해줘.
    뉴스 기사처럼 정돈해서 써주되, 구어체는 쓰지 말고
    정치 용어나 복잡한 표현은 풀어서 써줘.
    문장은 “~라고 했습니다”처럼 끝나도록 해줘.

    [뉴스 본문]
    {text}

    [출력 형식]
    - 요약 문장:
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "너는 뉴스 요약 전문가야. 기사 문체로 자연스럽게 정리해."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    output = response.choices[0].message.content
    match = re.search(r"요약:\s*(.+)", output, re.DOTALL)
    summary = match.group(1).strip() if match else output
    return summary


def combine_summaries_into_story(summaries: list[str]):
    """
    여러 요약을 하나의 기사처럼 자연스럽게 묶어주는 함수
    """
    combined = "\n\n".join(summaries)

    prompt = f"""
    아래에 여러 뉴스 요약이 있습니다.
    이들을 중복 없이 하나의 뉴스 기사처럼 자연스럽게 이어서 정리해줘.
    주제별 흐름을 고려해서 문단을 정리하고, 마지막엔 '오늘의 주요 뉴스였습니다'로 마무리해줘.

    문장 끝은 모두 '~라고 했습니다' 형태로 통일하고, 친구에게 말하는 식 표현은 쓰지 말아줘.

    [요약 목록]
    {combined}

    [출력 형식]
    - 종합 뉴스 기사:
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "너는 여러 뉴스를 하나로 엮는 뉴스 편집 기자야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    output = response.choices[0].message.content
    match = re.search(r"기사\s*:\s*(.+)", output, re.DOTALL)
    final_story = match.group(1).strip() if match else output
    return final_story
