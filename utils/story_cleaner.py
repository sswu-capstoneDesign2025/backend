from openai import OpenAI
import os
import json
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

REGIONS = ['서울', '부산', '대구', '인천', '광주', '대전', '용산', '세종']
TOPICS = ['일상', '사랑', '설화']

def process_user_story(raw_text: str) -> dict:
    prompt = f"""
다음 사용자의 이야기를 정제하고, 다음 조건에 따라 주제와 지역을 분류해줘:

1. 표준어로 정제
2. 비속어 제거
3. 개인정보(이름, 번호, 주소 등) 제거
4. 이야기 주제는 다음 중 하나로 분류 (없으면 "기타"): {', '.join(TOPICS)}
5. 지역은 다음 중 포함된 게 있다면 명시 (없으면 "없음"): {', '.join(REGIONS)}

출력 형식은 JSON으로:
{{
  "cleaned_story": "...",
  "topic": "...",
  "region": "..."
}}

사용자 이야기:
\"\"\"{raw_text}\"\"\"
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return json.loads(response.choices[0].message.content.strip())