from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import User

# SQLite 데이터베이스 연결 URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./processed_texts.db"

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