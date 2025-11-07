# backend/app/api.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json

# Import کردن *فقط* تابع مورد نیاز از utils
from .utils import read_recommendations_json 
# Import کردن مدل‌های Pydantic
from .schemas import RecommendationResponse 

app = FastAPI(
    title="Stock Ranker API",
    description="سرویس‌دهی توصیه‌های سهام از پیش محاسبه‌شده.",
    version="2.0.0" # نسخه ۲ (معماری جدید)
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # در production محدود شود
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚠️ ما در اینجا هیچ مدلی را بارگذاری نمی‌کنیم. 
# این باعث می‌شود API فوق‌العاده سبک و سریع باشد.

# مسیر فایل JSON که توسط اسکریپت روزانه (run_daily_ranking.py) نوشته می‌شود
JSON_DATA_PATH = Path("/app/model_artifacts/top_10_recommendations.json")


@app.get(
    "/recommend",
    response_model=RecommendationResponse,
    summary="دریافت ۱۰ توصیه برتر سهام (از پیش محاسبه‌شده)"
)
async def recommend_market():
    """
    این اندپوینت آخرین نتایج رتبه‌ بندی شده را که به صورت آفلاین
    محاسبه شده‌اند، می‌خواند و برمی‌گرداند.
    """
    if not JSON_DATA_PATH.exists():
        print(f"Error: JSON file not found at {JSON_DATA_PATH}")
        raise HTTPException(
            status_code=503, # Service Unavailable
            detail="داده‌های رتبه‌بندی هنوز در دسترس نیستند. لطفاً بعداً تلاش کنید."
        )
        
    try:
        # استفاده از تابع کمکی در utils برای خواندن فایل
        recommendations_list = read_recommendations_json(str(JSON_DATA_PATH))
        
        if not recommendations_list:
             raise HTTPException(status_code=404, detail="هیچ توصیه‌ای در فایل یافت نشد.")
        
        # بسته‌بندی در ساختار Pydantic
        return RecommendationResponse(top_k_recommendations=recommendations_list)
    
    except Exception as e:
        print(f"Error reading/parsing JSON: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"خطا در خواندن داده‌های رتبه‌بندی: {e}"
        )

@app.get("/health", summary="بررسی سلامت سرویس")
async def health_check():
    """یک اندپوینت ساده برای اطمینان از اینکه API در حال اجرا است."""
    return {"status": "ok"}