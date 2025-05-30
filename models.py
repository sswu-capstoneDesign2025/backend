# models.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import ForeignKey, Boolean

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    name = Column(String)                
    phone_number = Column(String)        
    hashed_password = Column(String)
    nickname = Column(String, nullable=False)
    profile_image = Column(String, nullable=True) 



class ProcessedText(Base):
    __tablename__ = "processed_texts"

    id                = Column(Integer, primary_key=True, index=True)
    speaker           = Column(String, nullable=True)     # 누구 이야기인지
    original_text     = Column(String)
    standardized_text = Column(String)
    cleaned_text      = Column(String)
    summary_text      = Column(String)

class SummaryNote(Base):
    __tablename__ = "summary_notes"

    id = Column(Integer, primary_key=True, index=True)
    sum_title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    username = Column(String, nullable=True)
    topic = Column(String, nullable=True)     
    region = Column(String, nullable=True)     
    created_at = Column(DateTime, default=datetime.utcnow)

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
    
class UserHealthAlert(Base):
    __tablename__ = "user_health_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_id = Column(Integer, ForeignKey("health_alerts.id"), nullable=False)

    enabled = Column(Boolean, default=True)  # ON/OFF 스위치


    from sqlalchemy import Column, Integer, String

class HealthAlert(Base):
    __tablename__ = "health_alerts"

    id = Column(Integer, primary_key=True, index=True)
    time = Column(String, nullable=False)        # 예: "오전 9:00"
    message = Column(String, nullable=False)     # 예: "스트레칭 시간입니다."
