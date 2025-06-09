#utils\story_handler.py

import re
from random import choice
from fastapi import HTTPException
from utils.story_cleaner import process_user_story
from models import SummaryNote, OtherUserRecord
from database import SessionLocal
from routers.tts_router import get_tts_audio_url

# 실패 횟수 추적용 임시 메모리
fail_count_map = {}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def handle_story_interaction(text: str, session_state: str, username: str | None):
    if session_state == "initial":
        if re.search(r"내가.*(이야기|얘기)", text):
            return await respond("그래, 어떤 이야기야?", "awaiting_story")

        if re.search(r"(심심|놀아줘|할거 없어|지루해|외로워|뭐할까|심심한데)", text):
            return await respond("재밌는 얘기 하나 해줄까? 아니면 너가 해줄래?", "awaiting_choice")

        return await respond("너가 재밌는 얘기해줄래? 아니면 내가 해줄까?", "awaiting_choice")

    if session_state == "awaiting_choice":
        normalized_text = re.sub(r"[^\w\s]", "", text).strip()

        if re.search(r"(내가\s*(할게|해볼게|...))", normalized_text):  # 생략
            return await respond("그래, 어떤 이야기야?", "awaiting_story")

        elif re.search(r"(얘기해줘|재밌는 얘기\s*있니|...)", text):  # 생략
            from requests import get
            r = get("http://localhost:8000/other-user-records/")
            stories = r.json()
            if stories:
                selected = choice(stories)
                return await respond(f"그럼 내가 해줄게! {selected['title']}... {selected['content']}", "complete")
            return await respond("아직 들려줄 이야기가 없어. 너가 하나 말해줄래?", "awaiting_choice")

    if session_state == "awaiting_story":
        if not username:
            raise HTTPException(400, "Username is required to save story")

        key = f"{username}_story_fail"
        fail_count = fail_count_map.get(key, 0)

        try:
            story_data = await process_user_story(text)
        except TimeoutError:
            fail_count += 1
            fail_count_map[key] = fail_count
            if fail_count >= 2:
                return await respond("잘 들었어요. 고마워요!", "complete")
            return await respond("이야기를 정리하는 데 너무 오래 걸렸어요. 다시 한 번 말해줄래요?", "awaiting_story")
        except Exception as e:
            raise HTTPException(500, f"GPT 처리 실패: {e}")

        if key in fail_count_map:
            del fail_count_map[key]

        title = story_data.get("title", text[:30])
        cleaned = story_data.get("cleaned_story", text)
        region = story_data.get("region", "없음")
        topic = story_data.get("topic", "기타")

        try:
            db = next(get_db())

            # SummaryNote 저장
            note = SummaryNote(
                sum_title=title,
                content=cleaned,
                username=username,
                region=region,
                topic=topic
            )
            db.add(note)

            # OtherUserRecord 저장
            record = OtherUserRecord(
                title=title,
                content=cleaned,
                author=username,
                region=region,
                topic=topic
            )
            db.add(record)

            db.commit()
            print("✅ DB 저장 성공 (summary_notes + other_user_records)")

        except Exception as e:
            print(f"❌ DB 저장 실패: {e}")
            raise HTTPException(500, f"DB 저장 실패: {e}")

        return await respond("좋은 이야기 고마워! 잘 저장해둘게.", "complete")

    return await respond("알 수 없는 상태입니다.", "initial")

async def respond(response_text: str, next_state: str):
    try:
        tts_url = await get_tts_audio_url(response_text)
        print(f"🔊 TTS 생성 성공: {tts_url}")
    except Exception as e:
        print(f"❌ TTS 요청 실패: {e}")
        tts_url = None

    return {
        "type": "story",
        "response": response_text,
        "response_audio_url": tts_url,
        "next_state": next_state
    }
