# backend/app/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
from .schemas import RecommendationResponse

# API شما اکنون به هیچ‌کدام از کتابخانه‌های ML نیاز ندارد!
# (مگر اینکه utils.py را در اینجا import کنید)

app = FastAPI(
    title="Stock Ranker API",
    description="Serves pre-calculated stock recommendations.",
    version="2.0.0" # نسخه ۲ (معماری جدید)
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# مسیر فایل JSON که توسط اسکریپت روزانه نوشته می‌شود
JSON_DATA_PATH = Path("/app/model_artifacts/top_10_recommendations.json")

@app.get(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Get Top 10 Pre-Calculated Stock Recommendations"
)
async def recommend_market():
    """
    این اندپوینت به سادگی آخرین نتایج رتبه‌بندی شده که به صورت آفلاین
    محاسبه شده‌اند را می‌خواند و برمی‌گرداند.
    """
    if not JSON_DATA_PATH.exists():
        raise HTTPException(
            status_code=503, # Service Unavailable
            detail="Ranking data is not yet available. Please try again later."
        )
        
    try:
        with open(JSON_DATA_PATH, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to read or parse ranking data: {e}"
        )