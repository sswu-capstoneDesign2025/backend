# OpenAI로 텍스트 정제, 요약 처리하는 함수 모듈

import openai
import os
from dotenv import load_dotenv
from openai import OpenAI
import re

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def process_text_with_gpt(text: str):
    """
    입력된 텍스트를
    - 표준어로 정제
    - 비속어 제거
    - 핵심 요약
    하는 함수 (Ultimate Robust Version)
    """
    prompt = f"""
    다음 텍스트를 표준어로 자연스럽게 바꾸고, 욕설 및 부적절한 표현은 모두 제거한 후, 핵심 내용만 간단히 요약해줘.

    [텍스트]
    {text}

    [출력형식]
    - 표준어 문장:
    - 비속어 제거한 문장:
    - 요약 문장:
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "너는 사투리와 비속어를 정제하고 핵심 요약하는 전문가야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    output = response.choices[0].message.content
    print("🛰 GPT 응답 확인:", output)

    # 정규표현식 기반으로 파싱
    standardized_text = re.search(r"- 표준어 문장:\s*(.+?)(?:- 비속어 제거한 문장:|$)", output, re.DOTALL)
    cleaned_text = re.search(r"- 비속어 제거한 문장:\s*(.+?)(?:- 요약 문장:|$)", output, re.DOTALL)
    summary_text = re.search(r"- 요약 문장:\s*(.+)", output, re.DOTALL)

    standardized = standardized_text.group(1).strip() if standardized_text else ""
    cleaned = cleaned_text.group(1).strip() if cleaned_text else ""
    summary = summary_text.group(1).strip() if summary_text else ""

    return standardized, cleaned, summary
