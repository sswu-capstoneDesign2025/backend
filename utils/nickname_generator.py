# utils\nickname_generator.py
import random
from sqlalchemy.orm import Session
from models import User

adjectives = ["멋쟁이", "귀여운", "용감한", "지혜로운", "상냥한", "반짝이는", "든든한"]
nouns = ["할부지", "할무니", "친구", "이웃", "동네형", "고수", "챔피언"]

def generate_random_nickname():
    return f"{random.choice(adjectives)} {random.choice(nouns)}"

def generate_unique_nickname(db: Session) -> str:
    for _ in range(100):  # 최대 100회 시도
        nickname = generate_random_nickname()
        exists = db.query(User).filter(User.nickname == nickname).first()
        if not exists:
            return nickname
    raise Exception("❌ 닉네임 생성 실패: 너무 많은 중복")
