# crawling/weather_fetcher.py

import requests, urllib.parse, re
from bs4 import BeautifulSoup, SoupStrainer

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/115.0.0.0 Safari/537.36"
)

def _get_soup(location: str) -> BeautifulSoup:
    url = "https://search.naver.com/search.naver?query=" \
          + urllib.parse.quote(f"{location} 날씨")
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9"}
    resp = requests.get(url, headers=headers, timeout=5)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def extract_air_quality(soup):
    pm10_text, pm25_text = None, None
    items = soup.select("ul.today_chart_list li.item_today")

    for item in items:
        box = item.select_one(".box") or item  # 💡 Fallback: 그냥 item 내부에서 찾기
        label_tag = box.select_one("strong.title")
        value_tag = box.select_one("span.txt")

        label = label_tag.get_text(strip=True) if label_tag else None
        value = value_tag.get_text(strip=True) if value_tag else None

        if not label or not value:
            continue

        if "미세먼지" in label and "초미세먼지" not in label:
            pm10_text = value
        elif "초미세먼지" in label:
            pm25_text = value

    if pm10_text is not None and pm25_text is not None:
        return f"미세먼지 {pm10_text}, 초미세먼지 {pm25_text}"
    return None


def get_current_weather(location: str):
    url = "https://search.naver.com/search.naver?query=" + urllib.parse.quote(f"{location} 날씨")
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9"}
    res = requests.get(url, headers=headers, timeout=5)
    soup = BeautifulSoup(res.text, "html.parser")
    with open("weather_debug.html", "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    # 현재 온도
    temp_span = soup.find("span", string=re.compile("현재 온도"))
    current_temp = temp_span.next_sibling.strip() if temp_span else None

    # 체감 온도
    dt_feel = soup.find("dt", string=re.compile("체감"))
    feel_dd = dt_feel.find_next_sibling("dd") if dt_feel else None
    perceived = feel_dd.get_text(strip=True) if feel_dd else None

    # 하늘 상태
    sky_span = soup.select_one("i.wt_icon span.blind")
    sky = sky_span.get_text(strip=True) if sky_span else None

    # 공기질
    air_quality = extract_air_quality(soup)
    if air_quality is None:
        air_quality = "정보 없음"

    summary = f"{location}의 현재 기온은 {current_temp}이며, 체감 온도는 {perceived}입니다."
    if sky:
        summary += f" 하늘 상태는 '{sky}'입니다."
    if air_quality:
        summary += f" 공기질 정보: {air_quality}"

    return {
        "location": location or "대한민국",
        "current_temp": current_temp,
        "perceived_temp": perceived,
        "sky": sky,
        "air_quality": air_quality,
        "summary": summary
    }


def get_forecast_weather(location: str, day_offset: int) -> str | None:
    """
    day_offset=1 → 내일, 2 → 모레
    """
    soup = _get_soup(location)
    items = soup.select(
        "div.api_subject_bx._weekly_weather_wrap "
        "div.list_box._weekly_weather ul li"
    )
    if not items or day_offset >= len(items):
        return None

    li = items[day_offset]

    # 1) 날짜·요일
    date_tag = li.select_one(".date")
    date = date_tag.get_text(strip=True).rstrip(".") if date_tag else ""

    # 2) 날씨 설명 (두 번째 .blind 엘리먼트)
    blinds = li.select("span.blind")
    if len(blinds) >= 2:
        desc = blinds[1].get_text(strip=True)
    else:
        desc_tag = li.select_one(".weather_desc") or blinds[:1]
        desc = desc_tag.get_text(strip=True) if desc_tag else "정보 없음"

    # 3) 최저·최고 기온
    low_tag  = li.select_one("span.lowest")
    high_tag = li.select_one("span.highest")
    low  = re.sub(r"[^\d.-]", "", low_tag.get_text())  + "°" if low_tag  else "—"
    high = re.sub(r"[^\d.-]", "", high_tag.get_text()) + "°" if high_tag else "—"

    label = "내일" if day_offset == 1 else "모레"
    return f"{label} ({date}) {location} 날씨는 {desc}, 최저 {low}, 최고 {high}입니다."


def get_weekly_weather(location: str) -> str:
    """
    이번 주 전체 예보
    """
    soup = _get_soup(location)
    items = soup.select(
        "div.api_subject_bx._weekly_weather_wrap "
        "div.list_box._weekly_weather ul li"
    )
    if not items:
        return f"{location} 이번 주 날씨 정보를 가져올 수 없습니다."

    lines = [f"{location}의 이번 주 날씨 예보"]
    for li in items:
        day_tag = li.select_one(".day")
        date_tag = li.select_one(".date")
        day  = day_tag.get_text(strip=True) if day_tag else ""
        date = date_tag.get_text(strip=True).rstrip(".") if date_tag else ""

        # 날씨 설명
        blinds = li.select("span.blind")
        if len(blinds) >= 2:
            desc = blinds[1].get_text(strip=True)
        else:
            desc_tag = li.select_one(".weather_desc") or blinds[:1]
            desc = desc_tag.get_text(strip=True) if desc_tag else "정보 없음"

        # 최저·최고 기온
        low_tag  = li.select_one("span.lowest")
        high_tag = li.select_one("span.highest")
        low  = re.sub(r"[^\d.-]", "", low_tag.get_text())  + "°" if low_tag  else "—"
        high = re.sub(r"[^\d.-]", "", high_tag.get_text()) + "°" if high_tag else "—"

        lines.append(f"{day}({date}): {desc}, {low} ~ {high}")

    return "\n".join(lines)


def get_monthly_weather(location: str) -> str:
    # 아직 구현되지 않은 기능
    return f"{location} 월간 예보 기능은 아직 구현되지 않았습니다."


def get_weather(location: str, when: str = "오늘", offset: int = None) -> str:
    if when == "오늘":
        text = get_current_weather(location)
    elif when in ("내일", "모레", "글피", "n일후"):
        day_offset = offset if offset is not None else (1 if when=="내일" else 2 if when=="모레" else 3)
        text = get_forecast_weather(location, day_offset)
    elif when == "이번주":
        text = get_weekly_weather(location)
    elif when == "다음주":
        text = get_monthly_weather(location)  # placeholder
    elif when in ("이번달","다음달"):
        text = get_monthly_weather(location)
    else:
        text = None

    return text or f"{when} {location} 날씨 정보를 가져올 수 없습니다."
