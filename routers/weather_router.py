# routers/weather_router.py

from fastapi import APIRouter, Query
from crawling.news_searcher import expand_location  
from crawling.weather_fetcher import get_weather, get_current_weather
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.get("/")
def fetch_weather(text: str = Query(...), when: str = "오늘"):
    print(f"📥 받은 text = {text}")
    location_parts = expand_location(text)
    print(f"🧩 확장된 location_parts = {location_parts}")
    full_location = " ".join(reversed(location_parts[:-1]))  # '대한민국' 제외
    print(f"🧭 최종 full_location = {full_location}")

    if when == "오늘":
        weather_data = get_current_weather(full_location)
        return JSONResponse(
            content=weather_data,
            media_type="application/json",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    else:
        weather_summary = get_weather(full_location, when=when)
        return JSONResponse(
            content={
                "location": full_location,
                "summary": weather_summary
            },
            media_type="application/json",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
