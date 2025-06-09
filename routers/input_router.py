# routers\input_router.py

from pathlib import Path
import os
import torch
import requests
from pydantic import BaseModel
from transformers import ElectraForSequenceClassification, ElectraTokenizer
from fastapi import APIRouter

router = APIRouter()

# 라벨 매핑
id2label = {0: "날씨", 1: "뉴스", 2: "이야기"}

# 모델 경로
project_root = Path(__file__).resolve().parents[1]
model_dir = project_root / "best_model"
model_file = model_dir / "model.safetensors"

# Google Drive 다운로드 URL
GDRIVE_MODEL_URL = "https://drive.google.com/uc?export=download&id=1h-x9OPeJA3Oexg_KIsNhn12NA-Cu0KQL"

# 모델이 없을 때만 다운로드
def download_model_if_needed():
    if model_file.exists():
        print("✅ 모델 파일이 이미 존재합니다. 다운로드 생략.")
        return
    print("📥 모델 파일이 존재하지 않아 다운로드합니다...")
    os.makedirs(model_dir, exist_ok=True)
    response = requests.get(GDRIVE_MODEL_URL, stream=True)
    if response.status_code == 200:
        with open(model_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print("✅ 모델 다운로드 완료.")
    else:
        raise RuntimeError(f"❌ 모델 다운로드 실패. 응답 코드: {response.status_code}")

# 최초 실행 시 모델 체크
download_model_if_needed()

# 모델 및 토크나이저 로딩
tokenizer = ElectraTokenizer.from_pretrained(model_dir)
model = ElectraForSequenceClassification.from_pretrained(model_dir)
model.eval()

# 입력 데이터 구조
class TextInput(BaseModel):
    text: str

# API 엔드포인트
@router.post("/classify")
def classify_text(input_data: TextInput):
    text = input_data.text.strip()
    if not text:
        return {"error": "입력된 텍스트가 없습니다."}

    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1).squeeze()
        pred_id = torch.argmax(probs).item()
        confidence = probs[pred_id].item()

    return {
        "label": id2label[pred_id],
        "confidence": round(confidence, 4)
    }
