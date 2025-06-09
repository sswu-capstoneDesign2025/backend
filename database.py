from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import (
    User, HealthAlert, UserHealthAlert, NewsHistory,  
    Base
)

# SQLite 데이터베이스 연결 URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Engine 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 전용 옵션
)

# 세션 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# DB 세션 의존성 주입 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🔹 사용자 관련 유틸 함수

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# 🔹 사용자 건강 알림 관련 유틸 함수

def get_user_alerts(db: Session, user_id: int):
    return db.query(UserHealthAlert).filter(UserHealthAlert.user_id == user_id).all()

def add_user_alert(db: Session, user_id: int, alert_id: int):
    user_alert = UserHealthAlert(user_id=user_id, alert_id=alert_id)
    db.add(user_alert)
    db.commit()
    db.refresh(user_alert)
    return user_alert

def toggle_user_alert(db: Session, user_alert_id: int):
    alert = db.query(UserHealthAlert).filter(UserHealthAlert.id == user_alert_id).first()
    if alert:
        alert.enabled = not alert.enabled
        db.commit()
        db.refresh(alert)
    return alert

def get_enabled_alerts_by_time(db: Session, user_id: int, time: str):
    return db.query(UserHealthAlert).join(HealthAlert).filter(
        UserHealthAlert.user_id == user_id,
        UserHealthAlert.enabled == True,
        HealthAlert.time == time
    ).all()


# ✅ (선택) 뉴스 기록 관련 유틸 함수 추가도 가능
def save_news_history(db: Session, username: str, keyword: str, summary: str):
    new_record = NewsHistory(
        username=username,
        keyword=keyword,
        summary=summary
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

def get_news_history(db: Session, username: str):
    return db.query(NewsHistory).filter(NewsHistory.username == username).order_by(NewsHistory.date.desc()).all()
