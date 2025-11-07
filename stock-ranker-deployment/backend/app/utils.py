# backend/app/utils.py
import pandas as pd
import numpy as np
import yfinance as yf
from ta import add_all_ta_features
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import joblib
import json
from pathlib import Path
from catboost import CatBoostRanker
from typing import List, Tuple, Any

# مسیرهای مصنوعات (Artifacts)
MODEL_DIR = Path("/app/model_artifacts")
MODEL_PATH = MODEL_DIR / "catboost_ranker_optimized.cbm"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
FEATURES_PATH = MODEL_DIR / "feature_cols.json"
PCA_PATH = MODEL_DIR / "pca.pkl" # ما این را نیز ذخیره خواهیم کرد

# لیست نمادها از نوت‌بوک شما
TICKERS = [
    # 💎 Top Tech/Mega-Cap (برترین فناوری و مگاکپ)
    "NVDA", "MSFT", "AAPL", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "AVGO", "ASML",

    # 🚀 High Growth & Chipmakers (رشد بالا و تولیدکنندگان تراشه)
    "NFLX", "AMD", "QCOM", "TXN", "AMAT", "INTU", "ADBE", "CRM", "INTC", "MU", 
    "PYPL", "ZM", "OKTA", "SNOW", "PANW", "CDNS", "ANSS", "MRVL", "KLAC", "LRCX",

    # 🛒 Retail & Consumer Staples (خرده‌فروشی و کالاهای اساسی)
    "COST", "PEP", "WMT", "HD", "MCD", "SBUX", "KO", "PG", "NKE", "TGT", 

    # 🏥 Healthcare & Biotech (بهداشت و درمان و بیوتک)
    "JNJ", "UNH", "LLY", "ABBV", "PFE", "MRK", "AMGN", "GILD", "BMY", "VRTX",

    # 💰 Financials & Payments (مالی و پرداخت‌ها)
    "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "AXP", "SPGI", "CME",

    # ⚡ Industrials & Materials (صنعتی و مواد اولیه)
    "LIN", "GE", "CAT", "BA", "MMM", "RTX", "HON", "ECL", "SHW", "DE",

    # 🔋 Energy & Utilities (انرژی و خدمات عمومی)
    "XOM", "CVX", "EOG", "SLB", "OXY", "COP", "DUK", "NEE", "SO", "AEP",

    # 🏠 Real Estate & Telecom (املاک و مستغلات و ارتباطات)
    "T", "VZ", "TMUS", "DLR", "EQIX", "AMT", "CCI", "PLD", "PSA", "URI",

    # ✨ Diversified & Others (متنوع و سایر موارد)
    "BRK-B", "ORCL", "CMCSA", "DIS", "TMO", "DELL", "MOH", "ISRG", "LOW", "PGR"
]

def load_prediction_tools():
    """بارگذاری مدل، scaler، لیست ویژگی‌ها و مدل PCA"""
    if not all([MODEL_PATH.exists(), SCALER_PATH.exists(), FEATURES_PATH.exists()]):
        raise FileNotFoundError("One or more critical artifacts (model, scaler, features) are missing.")
    
    model = CatBoostRanker()
    model.load_model(str(MODEL_PATH))
    
    scaler = joblib.load(str(SCALER_PATH))
    
    with open(FEATURES_PATH, "r") as f:
        feature_cols = json.load(f)
        
    # بارگذاری PCA اگر وجود داشته باشد، در غیر این صورت None
    pca = joblib.load(PCA_PATH) if PCA_PATH.exists() else None
        
    return model, scaler, feature_cols, pca

def fetch_raw_data(tickers: List[str]) -> pd.DataFrame:
    """بخش ۱ نوت‌بوک: دانلود داده‌های yfinance و اطلاعات پایه"""
    print("Step 1: Downloading yfinance historical data...")
    # به داده‌های کافی برای محاسبه اندیکاتورها نیاز داریم (مثلاً ۱ سال)
    data = yf.download(tickers, period="1y", group_by="ticker", auto_adjust=False, actions=True)
    
    df = data.stack(level=0, future_stack=True).reset_index().rename(columns={"level_1": "Ticker"})
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    df = df.drop_duplicates(subset=["Date", "Ticker"])
    df = df.sort_values(by=["Ticker", "Date"])

    print("Step 2: Fetching fundamental info (EPS, Market Cap)...")
    # این بخش کند است، اما برای ویژگی‌های شما ضروری است
    company_info = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            company_info.append({
                "Ticker": ticker,
                "Market Cap": info.get("marketCap"),
                "P/E Ratio": info.get("trailingPE"),
                "EPS": info.get("trailingEps"),
            })
        except Exception:
            company_info.append({"Ticker": ticker}) # افزودن ردیف خالی در صورت خطا
            
    company_df = pd.DataFrame(company_info)
    df = df.merge(company_df, on="Ticker", how="left")
    
    # پر کردن ffill برای اطلاعات پایه (چون هر روز تغییر نمی‌کنند)
    df[['Market Cap', 'P/E Ratio', 'EPS']] = df.groupby('Ticker')[['Market Cap', 'P/E Ratio', 'EPS']].ffill()

    return df

def run_feature_engineering(df: pd.DataFrame) -> Tuple[pd.DataFrame, PCA]:
    """بخش‌های ۳ و ۴ نوت‌بوک: اجرای کامل مهندسی ویژگی"""
    print("Step 3: Adding Technical Indicators (TA)...")
    # نوت‌بوک شما از ta استفاده کرده است، نه pandas-ta
    df = add_all_ta_features(df, open="Open", high="High", low="Low", close="Close", volume="Volume", fillna=True)

    print("Step 4: Engineering Advanced Features...")
    
    # 4.1. Lag ها
    for lag in [1, 3, 5]:
        # 'Return_7d' هنوز وجود ندارد، پس از 'Adj Close' لگ می‌گیریم
        df[f'Adj_Close_Lag_{lag}'] = df.groupby('Ticker')['Adj Close'].shift(lag)
    
    # 4.2. میانگین‌های متحرک
    windows = [5, 10, 20]
    for window in windows:
        df[f'SMA_{window}'] = df.groupby('Ticker')['Adj Close'].rolling(window=window, min_periods=1).mean().reset_index(0, drop=True)
        df[f'EMA_{window}'] = df.groupby('Ticker')['Adj Close'].ewm(span=window, adjust=False, min_periods=1).mean().reset_index(0, drop=True)

    # 4.3. نسبت‌های مالی (پر کردن مقادیر 0 و NaN)
    df['EPS'] = df['EPS'].replace(0, np.nan).fillna(df.groupby('Ticker')['EPS'].transform('mean')).fillna(0)
    df['Market Cap'] = df['Market Cap'].replace(0, np.nan).fillna(df.groupby('Ticker')['Market Cap'].transform('mean')).fillna(1e-6)
    df['PE_to_EPS'] = df['P/E Ratio'] / (df['EPS'] + 1e-6) # جلوگیری از تقسیم بر صفر

    # 4.4. نوسانات (Sharpe_Ratio به Return_7d نیاز دارد که هنوز نداریم)
    df['Volatility_Rolling_Std'] = df.groupby('Ticker')['Adj Close'].rolling(window=10, min_periods=1).std().reset_index(0, drop=True)

    # 4.5. ویژگی‌های بازار (Beta, Market_Return)
    df['Market_Return'] = df.groupby('Date')['Adj Close'].transform('mean')
    # محاسبه Beta (ساده شده)
    cov_matrix = df.groupby('Ticker')[['Adj Close', 'Market_Return']].rolling(window=30).cov().unstack()
    if not cov_matrix.empty:
        beta = cov_matrix[('Adj Close', 'Market_Return')] / (cov_matrix[('Market_Return', 'Market_Return')] + 1e-6)
        df['Beta'] = beta.reset_index(level=0, drop=True)
    else:
        df['Beta'] = 0.0

    # 4.6. PCA (و ذخیره آن)
    tech_features = [col for col in df.columns if 'momentum_' in col or 'trend_' in col or 'volatility_' in col]
    # اطمینان از حذف ستون‌هایی که PCA نمی‌تواند بپذیرد
    tech_features = [col for col in tech_features if col in df and pd.api.types.is_numeric_dtype(df[col])]
    
    # پر کردن NaN ها قبل از PCA
    df_tech_filled = df[tech_features].fillna(0)
    
    scaler_pca = StandardScaler()
    pca = PCA(n_components=5)
    
    df_tech_scaled = scaler_pca.fit_transform(df_tech_filled)
    pca_features = pca.fit_transform(df_tech_scaled)
    
    for i in range(pca_features.shape[1]):
        df[f'PCA_Tech_{i+1}'] = pca_features[:, i]
        
    # ذخیره PCA برای استفاده‌های بعدی (اگر اولین بار است)
    if not PCA_PATH.exists():
        joblib.dump(pca, PCA_PATH)

    # 4.7. ویژگی‌های زمانی
    df['Day_of_Week'] = df['Date'].dt.dayofweek
    df['Month'] = df['Date'].dt.month
    df['Quarter'] = df['Date'].dt.quarter

    print("Step 5: Final data cleanup...")
    # ویژگی‌هایی که در نوت‌بوک برای مدل CatBoost حذف شدند
    df = df.drop(columns=['Company', 'Sector', 'Industry'], errors='ignore')
    # 'Sentiment' از ابتدا اضافه نشد
    
    # بازگرداندن فقط آخرین ردیف داده برای هر نماد
    final_data_today = df.groupby('Ticker').last().reset_index()
    
    return final_data_today, pca
# app/utils.py (Sample)
import json
import os
from typing import List, Dict


def read_recommendations_json(file_path: str) -> List[Dict]:
    """فایل JSON توصیه‌های روزانه را می‌خواند."""
    
    # اطمینان حاصل کنید که مسیر فایل درست است
    # این مسیر باید به فایل نهایی top_k_recommendations.json اشاره کند
    
    if not os.path.exists(file_path):
        # این خطا نباید باعث Crash شدن سرور شود، بلکه باید در API مدیریت شود.
        print(f"Warning: Recommendation file not found at {file_path}")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # فرض می‌کنیم فایل JSON یک دیکشنری با کلید اصلی 'top_k_recommendations' است
            return data.get("top_k_recommendations", [])
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {file_path}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while reading JSON: {e}")
        return []