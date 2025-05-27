import openai
import os
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
import re
import pickle

from utils.keyword_extractor import (
    extract_keyword_from_text,
    extract_passages_by_keywords
)

CACHE_PATH = "summary_cache.pkl"
SUMMARY_CACHE = {}
# 서버 시작 시 캐시 로드
if os.path.exists(CACHE_PATH):
    try:
        with open(CACHE_PATH, "rb") as f:
            SUMMARY_CACHE = pickle.load(f)
        print(f"📂 캐시 로드 완료: {len(SUMMARY_CACHE)}개")
    except Exception as e:
        print(f"❗ 캐시 로드 실패: {e}")


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI()

async def long_article_summary(text: str) -> str:
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
    resp = await client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
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


async def simplify_for_borderline(text: str) -> str:
    """
    2차 다듬기: 
    - 경계선 지능 수준 사용자도 이해할 수 있도록
    - 문장은 짧고 간단하게
    - 어려운 단어는 쉬운 말로 바꿔줌
    """
    prompt = f"""
    아래는 이미 요약된 뉴스입니다.
    경계선 지능형 장애인 수준의 사용자도 쉽게 이해할 수 있게 하나의 뉴스로 재작성해주세요.
    - 한 문장에 하나의 정보만 담아주세요.
    - 문장은 최대 2~3줄로 짧게.
    - 어려운 단어는 쉬운 말로 바꿔주세요.
    - 필요하다면 어려운 말 앞에 추가 설명을 넣어주세요.(ex. 배터리의 한 종류인 납축전지)
    - 친근하게 말하는 말투로 바꿔주세요.
    
    [요약된 뉴스]
    {text}

    [출력 형식]
    - 간단한 요약:
    """
    resp = await client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "너는 어린이용 뉴스 편집자야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=1000
    )
    out = resp.choices[0].message.content
    m = re.search(r"간단한 요약:\s*(.+)", out, re.DOTALL)
    return m.group(1).strip() if m else out.strip()


async def summarize_article_pipeline(url: str, text: str, user_query: str, window: int = 1) -> str:
    """
    1) user_query에서 핵심 키워드 추출
    2) 기사 본문에서 키워드 주변 문장만 필터링
    3) GPT-3.5로 압축 요약 → 어린이용으로 쉬운 문장으로 변환
    + 캐시 적용
    """
    cache_key = f"{url}|{user_query}"
    if cache_key in SUMMARY_CACHE:
        return SUMMARY_CACHE[cache_key]

    keywords = extract_keyword_from_text(user_query)
    filtered = extract_passages_by_keywords(text, keywords, window=window)

    short = await long_article_summary(filtered)            
    simplified = await simplify_for_borderline(short)      

    SUMMARY_CACHE[cache_key] = simplified
    with open(CACHE_PATH, "wb") as f:
        pickle.dump(SUMMARY_CACHE, f)

    return simplified


async def combine_summaries_into_story(summaries: list[str]) -> str:
    """
    여러 요약을 하나로 묶은 뒤, 
    경계선 지능 수준의 사용자도 이해할 수 있게 쉽고 명확하게 정리
    """
    combined = "\n\n".join(summaries)
    prompt = f"""
    아래는 여러 뉴스 요약입니다.
    이들을 중복 없이 하나의 쉽고 명확한 이야기로 이어주세요.
    - 문장은 짧게, 한 문장당 하나의 정보.
    - 어려운 용어 대신 쉬운 말 사용.
    - 필요하면 괄호 안에 간단한 추가 설명 포함.
    - 마지막에 '이상이 오늘의 뉴스입니다.'로 마무리.

    [요약 목록]
    {combined}

    [출력 형식]
    - 쉬운 뉴스:
    """
    resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "너는 어린이용 뉴스 편집자야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=1200
    )
    out = resp.choices[0].message.content
    m = re.search(r"쉬운 뉴스:\s*(.+)", out, re.DOTALL)
    return m.group(1).strip() if m else out.strip()