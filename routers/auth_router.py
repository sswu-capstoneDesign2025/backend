# 인증 라우터

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_user_by_username, create_user
from models import User
from utils.auth_handler import hash_password, verify_password, create_access_token
from database import SessionLocal
import os
import requests
from fastapi import Request
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse
import uuid
import logging
# 로그 객체 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

load_dotenv()

KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
KAKAO_EXTRA_INFO_URL = os.getenv("KAKAO_EXTRA_INFO_URL")

# Pydantic 모델
class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    phone_number: str

class UserLogin(BaseModel):
    username: str
    password: str

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Signup attempt for username: {user.username}")
    if get_user_by_username(db, user.username):
        logger.warning(f"Signup failed: Username already exists: {user.username}")
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pw = hash_password(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_pw,
        name=user.name,
        phone_number=user.phone_number
    )
    result = create_user(db, db_user)
    logger.info(f"User created successfully: {user.username}")
    return result

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    logger.info(f"Login attempt: {user.username}")
    db_user = get_user_by_username(db, user.username)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        logger.warning(f"Login failed for user: {user.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": db_user.username})
    logger.info(f"Login successful: {user.username}")
    return {"access_token": token, "token_type": "bearer"}


@router.get("/kakao/login")
def kakao_login():
    logger.info("Kakao login URL requested.")
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize?response_type=code"
        f"&client_id={KAKAO_CLIENT_ID}&redirect_uri={KAKAO_REDIRECT_URI}"
    )
    return {"redirect_url": kakao_auth_url}



@router.get("/kakao/callback")
def kakao_callback(code: str, db: Session = Depends(get_db)):
    logger.info("Kakao callback triggered.")

    try:
        token_res = requests.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": KAKAO_CLIENT_ID,
                "redirect_uri": KAKAO_REDIRECT_URI,
                "code": code,
            },
            headers={"Content-type": "application/x-www-form-urlencoded"}
        )
        token_json = token_res.json()
        access_token = token_json.get("access_token")

        if not access_token:
            logger.error(f"Kakao token error: {token_json}")
            raise HTTPException(status_code=400, detail="Failed to get Kakao token")

        profile_res = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        profile_json = profile_res.json()
        kakao_id = str(profile_json["id"])
        kakao_account = profile_json.get("kakao_account", {})
        nickname = kakao_account.get("profile", {}).get("nickname", "")
        phone = kakao_account.get("phone_number", "")

        user = get_user_by_username(db, kakao_id)

        if not user:
            logger.info(f"Kakao user not found, redirecting to extra info page. kakao_id={kakao_id}")
            return RedirectResponse(url=f"{KAKAO_EXTRA_INFO_URL}?kakao_id={kakao_id}&nickname={nickname}")

        jwt_token = create_access_token({"sub": user.username})
        logger.info(f"Kakao login success for existing user: {user.username}")
        return {"access_token": jwt_token, "token_type": "bearer"}

    except Exception as e:
        logger.error(f"Kakao login callback error: {e}")
        raise HTTPException(status_code=500, detail="Kakao login failed")



class KakaoExtraInfo(BaseModel):
    kakao_id: str
    name: str
    phone_number: str

@router.post("/kakao/extra-info")
def kakao_extra_info(data: KakaoExtraInfo, db: Session = Depends(get_db)):
    logger.info(f"Extra info received for Kakao user: {data.kakao_id}")
    if get_user_by_username(db, data.kakao_id):
        logger.warning(f"Kakao user already exists: {data.kakao_id}")
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        username=data.kakao_id,
        name=data.name,
        phone_number=data.phone_number,
        hashed_password=hash_password(str(uuid.uuid4()))
    )
    create_user(db, user)
    logger.info(f"Kakao user created and logged in: {data.kakao_id}")
    jwt_token = create_access_token({"sub": user.username})
    return {"access_token": jwt_token, "token_type": "bearer"}