# 혹시 더 빠른 처리가 될까해서 만든 gpt api용 함수(훨씬 빨라짐!! 성공!!)
# utils\news_processor.py

import openai
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
import re
import pickle
import tiktoken
import json

CACHE_PATH = "summary_cache.pkl"
SUMMARY_CACHE = {}
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

# -------------------
# NEW: 토큰 수 계산용
# -------------------
def count_tokens(text: str, model: str = "gpt-4o") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

# --------------------------
# NEW: 자동 청크 분할 로직
# --------------------------
def chunk_url_text_pairs(
    url_text_pairs: list[tuple[str, str]],
    model: str = "gpt-4o",
    max_tokens: int = 28000
) -> list[list[str]]:
    """
    [(url, text), ...] 를 model 한도(max_tokens)에 맞춰
    텍스트 블록 단위로 분할해 리스트 반환
    """
    # 각 기사를 하나의 '블록' 문자열로 변환
    blocks = [
        f"=== 기사 {i} ({url}) ===\n{txt.strip()}\n"
        for i, (url, txt) in enumerate(url_text_pairs, start=1)
    ]
    chunks = []
    current_chunk = []
    current_text = ""
    for block in blocks:
        # 현재 청크에 block을 추가했을 때 한도 초과 여부 검사
        if count_tokens(current_text + block, model) > max_tokens:
            # 초과하면 지금까지 쌓은 청크를 확정하고 새 청크 시작
            chunks.append(current_chunk)
            current_chunk = [block]
            current_text = block
        else:
            current_chunk.append(block)
            current_text += block
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

# --------------------------------------------------------
# NEW: 요약 + 쉬운 언어 변환 → 청크 단위로 처리 + 최종 통합
# --------------------------------------------------------
async def MASSaC(
    url_text_pairs: list[tuple[str, str]]
) -> dict[str, list[str] | str]:
    """
    함수 뜻: multi_article_simplified_summary_and_combine
    1) 토큰 한도 검사 → 필요 시 자동 청크 분할
    2) 각 청크별로 500자 요약 + 쉬운 말투 재작성 → summaries 수집
    3) 모든 summaries를 마지막에 한 번의 프롬프트로 통합
    - 반환: { "summaries": [...], "combined": "..." }
    """
    model = "gpt-4o"
    # 모델 한도 대비 여유분 둔 임계치 (예: 32K 한도 중 28K 토큰으로)
    max_input_tokens = 28_000

    print(f"📊 받은 기사 수: {len(url_text_pairs)}개")
    # 1) 청크 분할
    chunks = chunk_url_text_pairs(url_text_pairs, model, max_input_tokens)

    all_summaries: list[str] = []
    
    # 2) 청크별 요약 + 쉬운 말투 변환 (summaries만)
    for chunk in chunks:
        joined = "\n".join(chunk)
        prompt = f"""
        다음 {len(chunk)}건의 뉴스를 처리하세요:
        1) 1000자 내외로 간결하게 요약
        2) 경계선 지능형 장애인 수준의 사용자도 이해할 수 있도록 어려운 단어는 쉬운 말로 바꿔주세요
        3) 필요하다면 어려운 말 앞에 추가 설명을 넣어주세요.(ex. 배터리의 한 종류인 납축전지)

        [기사 블록]
        {joined}

        [출력 형식 - JSON]
        {{
        "summaries": [
            "기사1 요약+쉬운 문장",
            "기사2 요약+쉬운 문장",
            ...
        ]
        }}
        """
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "너는 어린이용 뉴스 편집자야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1500
        )
        out = resp.choices[0].message.content
        # JSON 블록 파싱
        m = re.search(r"\{\s*\"summaries\"\s*:\s*\[([\s\S]*?)\]\s*\}", out)
        if m:
            obj = json.loads("{" + m.group(0).split("{", 1)[1])
            all_summaries.extend(obj["summaries"])

    if not all_summaries:
        return {
            "summaries": [],
            "combined": "요약할 기사를 찾을 수 없습니다. 다시 시도해 주세요."
        }
    
    # 3) 최종 통합
    combined_prompt = f"""
    아래는 여러 뉴스 요약입니다.
    - 경계선 지능형 장애인 수준의 사용자도 이해할 수 있도록 한 문장에 하나의 정보만 담고, 어려운 말은 쉬운 말로 바꿔주세요.
    - 중복 없이 하나의 쉽고 명확한 이야기로 이어 붙이세요.
    - 마지막에 '이상이 오늘의 뉴스입니다.'로 마무리.

    [요약 목록]
    {json.dumps(all_summaries, ensure_ascii=False, indent=2)}

    [출력 형식 - JSON]
    {{ "combined": "여기에 통합 결과를 쓰세요" }}
    """
    resp2 = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "너는 어린이용 뉴스 편집자야."},
            {"role": "user", "content": combined_prompt}
        ],
        temperature=0.2,
        max_tokens=800
    )
    out2 = resp2.choices[0].message.content
    m2 = re.search(r"\{[\s\S]+\}$", out2)
    combined = ""
    try:
        m2 = re.search(r"\{[\s\S]+\}", out2)
        if m2:
            parsed = json.loads(m2.group(0))
            combined = parsed.get("combined", "")
        else:
            combined = "요약을 통합하는 데 실패했어요. 다시 시도해 주세요."
    except Exception as e:
        print(f"❗ 통합 요약 파싱 실패: {e}")
        combined = "요약을 통합하는 데 실패했어요. 다시 시도해 주세요."

    return {
        "summaries": all_summaries,
        "combined": combined
    }
