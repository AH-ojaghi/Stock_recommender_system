# backend/run_daily_ranking.py
import pandas as pd
import numpy as np
import json
from pathlib import Path
from app.utils import (
    fetch_raw_data, 
    run_feature_engineering, 
    load_prediction_tools, 
    TICKERS
)

# مسیر فایل خروجی JSON که API آن را می‌خواند
OUTPUT_DIR = Path("/app/model_artifacts") # یا هر مسیر دیگری که در داکر volume شده
JSON_OUTPUT_PATH = OUTPUT_DIR / "top_10_recommendations.json"

def main():
    print("--- Starting Daily Ranking Job ---")
    
    # 1. بارگذاری ابزارهای آموزش‌دیده
    try:
        model, scaler, feature_cols, pca_model = load_prediction_tools()
        print(f"Loaded {len(feature_cols)} features, model, and scaler.")
    except Exception as e:
        print(f"FATAL: Could not load model artifacts. {e}")
        return

    # 2. واکشی داده‌های خام جدید
    try:
        df_raw = fetch_raw_data(TICKERS)
    except Exception as e:
        print(f"FATAL: Data fetching failed. {e}")
        return

    # 3. اجرای خط لوله مهندسی ویژگی
    # (توجه: PCA در اینجا 'fit' نمی‌شود، فقط 'transform' می‌شود اگر از قبل وجود داشت)
    try:
        df_features, _ = run_feature_engineering(df_raw)
        print(f"Feature engineering complete. Shape: {df_features.shape}")
    except Exception as e:
        print(f"FATAL: Feature engineering failed. {e}")
        return

    # 4. پیش‌پردازش نهایی (دقیقاً مانند نوت‌بوک CatBoost)
    # اطمینان حاصل کنید که DataFrame شامل تمام ستون‌های مورد نیاز است
    missing_cols = set(feature_cols) - set(df_features.columns)
    if missing_cols:
        print(f"Warning: Missing columns after FE, filling with 0: {missing_cols}")
        for col in missing_cols:
            df_features[col] = 0.0

    # فیلتر کردن فقط ستون‌های مورد نیاز
    X_today = df_features[feature_cols].copy()
    X_today = X_today.fillna(method="ffill").fillna(0) # پر کردن NaN ها

    # 5. اعمال Scaler
    try:
        X_scaled = scaler.transform(X_today)
    except Exception as e:
        print(f"FATAL: Scaler failed. {e}")
        print(f"Data columns: {X_today.columns.tolist()}")
        return

    # 6. پیش‌بینی
    print("Predicting ranks...")
    scores = model.predict(X_scaled)
    
    df_features["score"] = scores

    # 7. رتبه‌بندی و ذخیره خروجی
    top_10 = df_features.sort_values("score", ascending=False).head(10)

    # فرمت کردن خروجی برای API
    results = []
    for _, row in top_10.iterrows():
        # افزودن داده‌های اضافی برای نمایش (مثلاً P/E)
        extra = {
            "P/E Ratio": row.get("P/E Ratio"),
            "Market Cap": row.get("Market Cap")
        }
        results.append({
            "id": row["Ticker"],
            "score": row["score"],
            "extra_data": extra
        })
        
    output_data = {"top_k_recommendations": results}

    # 8. ذخیره فایل JSON
    try:
        with open(JSON_OUTPUT_PATH, "w") as f:
            json.dump(output_data, f, indent=4)
        print(f"✅ --- Job complete. Top 10 saved to {JSON_OUTPUT_PATH} ---")
    except Exception as e:
        print(f"FATAL: Failed to write JSON output. {e}")

if __name__ == "__main__":
    main()