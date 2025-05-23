import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def clean_user_story(raw_text: str) -> str:
    prompt = f"""
다음 사용자의 이야기를 다음 조건에 따라 정제해줘:
1. 표준어로 바꾸기
2. 비속어 제거
3. 유출되면 곤란한 개인정보(이름, 전화번호, 주소 등) 제거

사용자 이야기:
\"\"\"{raw_text}\"\"\"
"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response['choices'][0]['message']['content'].strip()
