from openai import AsyncOpenAI, OpenAIError
import os
import json
from dotenv import load_dotenv
import asyncio

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=15.0  
)

REGIONS = ['서울', '부산', '대구', '인천', '광주', '대전', '용산', '세종']
TOPICS = ['일상', '사랑', '설화']

async def process_user_story(raw_text: str) -> dict:
    prompt = f"""
다음 사용자의 이야기를 정제하고, 다음 조건에 따라 주제와 지역을 분류해줘:

1. 표준어로 정제
2. 비속어 제거
3. 개인정보(이름, 번호, 주소 등) 제거
4. 이야기 주제는 다음 중 하나로 분류 (없으면 "기타"): {', '.join(TOPICS)}
5. 지역은 다음 중 포함된 게 있다면 명시 (없으면 "없음"): {', '.join(REGIONS)}

출력 형식은 JSON으로:
{{
  "title": "...",
  "cleaned_story": "...",
  "topic": "...",
  "region": "..."
}}

사용자 이야기:
\"\"\"{raw_text}\"\"\"
"""
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
        print(f"🧾 GPT 응답 원문:\n{content}")  # ✅ 추가
        return json.loads(content)

    except asyncio.TimeoutError:
        raise TimeoutError("⏰ GPT 응답 지연: 15초 초과")
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON 파싱 실패: {e}")
        print(f"🔍 응답 원본:\n{content}") 
        raise ValueError("⚠️ GPT 응답이 JSON 형식이 아닙니다:\n" + content)
    except OpenAIError as e:
        raise RuntimeError(f"❌ OpenAI API 오류: {e}")
