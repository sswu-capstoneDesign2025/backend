# utils/time_parser.py

import re
from datetime import datetime, timedelta

def parse_korean_time_expr(text: str) -> tuple[str, int]:
    """
    text 안에서 아래 표현을 찾아서
    - when: "오늘","내일","모레","글피","n일후","다음주","다음달","이번주","이번달"
    - offset: for 'n일후' → n, '글피'→3, others ignored
    반환. 표현이 없으면 ("오늘",0)
    """
    # 우선순위가 높은 순서대로 체크
    if re.search(r"\b이번\s?주\b|\b주간\b", text):
        return "이번주", None
    if re.search(r"\b다음\s?주\b", text):
        return "다음주", None
    if re.search(r"\b이번\s?달\b|\b월간\b", text):
        return "이번달", None
    if re.search(r"\b다음\s?달\b", text):
        return "다음달", None
    if re.search(r"\b글피\b", text):
        return "글피", 3
    m = re.search(r"(\d+)일\s*후\b", text)
    if m:
        return "n일후", int(m.group(1))
    if re.search(r"\b모레\b", text):
        return "모레", 2
    if re.search(r"\b내일\b", text):
        return "내일", 1
    # 기본
    return "오늘", 0
