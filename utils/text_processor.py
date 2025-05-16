import openai
import os
from dotenv import load_dotenv
from openai import OpenAI
import re

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()


def long_article_summary(text: str) -> str:
    """
    1차 요약: GPT-3.5-turbo 로 긴 본문을 압축해서 500~700자 이내로 줄여줌
    """
    prompt = f"""
    다음 뉴스 본문을 500자 내외로 간결하게 요약해줘.
    뉴스 기사처럼 쓰되, 구어체는 쓰지 말고 핵심만 담아줘.

    [뉴스 본문]
    {text}

    [출력 형식]
    - 요약:
    """
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "너는 뉴스 요약 전문가야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=800
    )
    out = resp.choices[0].message.content
    m = re.search(r"요약:\s*(.+)", out, re.DOTALL)
    return m.group(1).strip() if m else out.strip()


def refine_summary(text: str) -> str:
    """
    2차 다듬기: GPT-4-turbo 로 뉴스 기사 문체(+“~라고 했습니다”)로 정제
    """
    prompt = f"""
    아래는 이미 요약된 뉴스입니다.
    한 문단으로, 문장 끝을 모두 "~라고 했습니다"로 맞추고,
    정치 용어·복잡한 표현은 풀어서 쓰되, 구어체는 쓰지 말아주세요.

    [요약된 뉴스]
    {text}

    [출력 형식]
    - 기사:
    """
    resp = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "너는 뉴스 편집 기자야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=500
    )
    out = resp.choices[0].message.content
    m = re.search(r"기사\s*:\s*(.+)", out, re.DOTALL)
    return m.group(1).strip() if m else out.strip()


def summarize_article_pipeline(text: str) -> str:
    """
    1단계: 긴 기사 압축 → 2단계: 문체 다듬기
    """
    short = long_article_summary(text)
    return refine_summary(short)


def combine_summaries_into_story(summaries: list[str]) -> str:
    """
    여러 요약을 하나의 통합 뉴스 기사처럼 자연스럽게 묶어주는 함수
    """
    combined = "\n\n".join(summaries)
    prompt = f"""
    아래에 여러 뉴스 요약이 있습니다.
    이들을 중복 없이 하나의 뉴스 기사처럼 자연스럽게 이어서 정리해 주세요.
    주제별 흐름을 고려해서 문단을 정리하고,
    마지막엔 '오늘의 주요 뉴스였습니다'로 마무리해 주세요.

    문장 끝은 모두 '~라고 했습니다' 형태로 통일하고,
    친구에게 말하는 식 표현은 사용하지 말아주세요.

    [요약 목록]
    {combined}

    [출력 형식]
    - 종합 뉴스 기사:
    """
    resp = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "너는 여러 뉴스를 하나로 엮는 뉴스 편집 기자야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    out = resp.choices[0].message.content
    m = re.search(r"기사\s*:\s*(.+)", out, re.DOTALL)
    return m.group(1).strip() if m else out.strip()
