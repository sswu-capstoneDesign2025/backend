# C:/capstone_be/backend/routers/user_alert_router.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import (
    get_user_alerts, add_user_alert, toggle_user_alert,
    get_enabled_alerts_by_time, get_db
)

router = APIRouter(prefix="/alerts", tags=["User Alerts"])

@router.get("/user/{user_id}")
def get_user_alerts_view(user_id: int, db: Session = Depends(get_db)):
    return get_user_alerts(db, user_id)

@router.post("/user/{user_id}/{alert_id}")
def add_alert_for_user(user_id: int, alert_id: int, db: Session = Depends(get_db)):
    return add_user_alert(db, user_id, alert_id)

@router.put("/{user_alert_id}/toggle")
def toggle_alert(user_alert_id: int, db: Session = Depends(get_db)):
    return toggle_user_alert(db, user_alert_id)

@router.get("/trigger")
def trigger_alerts(user_id: int, time: str, db: Session = Depends(get_db)):
    return get_enabled_alerts_by_time(db, user_id, time)
