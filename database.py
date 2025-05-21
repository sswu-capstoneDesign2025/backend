from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import User, HealthAlert, UserHealthAlert, Base 

# SQLite 데이터베이스 연결 URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Engine 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user



# 사용자별 알림 설정 가져오기
def get_user_alerts(db: Session, user_id: int):
    return db.query(UserHealthAlert).filter(UserHealthAlert.user_id == user_id).all()

# 사용자 알림 설정 추가
def add_user_alert(db: Session, user_id: int, alert_id: int):
    user_alert = UserHealthAlert(user_id=user_id, alert_id=alert_id)
    db.add(user_alert)
    db.commit()
    db.refresh(user_alert)
    return user_alert

# 알림 ON/OFF 토글
def toggle_user_alert(db: Session, user_alert_id: int):
    alert = db.query(UserHealthAlert).filter(UserHealthAlert.id == user_alert_id).first()
    if alert:
        alert.enabled = not alert.enabled
        db.commit()
        db.refresh(alert)
    return alert

# 특정 시각의 사용자 알림만 가져오기 (알림 울릴 때 사용)
def get_enabled_alerts_by_time(db: Session, user_id: int, time: str):
    return db.query(UserHealthAlert).join(HealthAlert).filter(
        UserHealthAlert.user_id == user_id,
        UserHealthAlert.enabled == True,
        HealthAlert.time == time
    ).all()



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


