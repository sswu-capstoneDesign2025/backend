from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, date

Base = declarative_base()

# 🧑 사용자 정보
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    name = Column(String)
    phone_number = Column(String)
    hashed_password = Column(String)
    nickname = Column(String, nullable=False)
    profile_image = Column(String, nullable=True)

# 🗣️ 텍스트 요약 처리 데이터
class ProcessedText(Base):
    __tablename__ = "processed_texts"

    id = Column(Integer, primary_key=True, index=True)
    speaker = Column(String, nullable=True)
    original_text = Column(String)
    standardized_text = Column(String)
    cleaned_text = Column(String)
    summary_text = Column(String)

# 🧾 사용자가 저장한 요약 노트
class SummaryNote(Base):
    __tablename__ = "summary_notes"

    id = Column(Integer, primary_key=True, index=True)
    sum_title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 🌍 타 사용자 스토리 기록
class OtherUserRecord(Base):
    __tablename__ = "other_user_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    author = Column(String, nullable=False)
    profileUrl = Column(String, nullable=True)
    region = Column(String, nullable=True)
    topic = Column(String, nullable=True)

# 🏥 건강 알림 설정
class UserHealthAlert(Base):
    __tablename__ = "user_health_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_id = Column(Integer, ForeignKey("health_alerts.id"), nullable=False)
    enabled = Column(Boolean, default=True)

class HealthAlert(Base):
    __tablename__ = "health_alerts"

    id = Column(Integer, primary_key=True, index=True)
    time = Column(String, nullable=False)        # 예: "오전 9:00"
    message = Column(String, nullable=False)     # 예: "스트레칭 시간입니다."

# 📰 뉴스 기록 기능 
class NewsHistory(Base):
    __tablename__ = "news_history"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)        # 사용자명
    keyword = Column(String, nullable=False)         # 뉴스 키워드
    summary = Column(String, nullable=False)         # 요약 내용
    date = Column(Date, default=date.today)          # 저장 날짜
