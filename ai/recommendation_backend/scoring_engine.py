# scoring_engine.py
import os
from datetime import date
import pandas as pd
import joblib
import numpy as np
from catboost import CatBoostRanker, Pool
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from models import Recommendation
from database import SessionLocal

load_dotenv()

# --- CONFIG ---
TOPK = 5 
# --- PATHS ---
MODEL_PATH = os.getenv("MODEL_PATH")
SCALER_PATH = os.getenv("SCALER_PATH")
DATA_PATH = os.getenv("DATA_PATH") # NOTE: In a real environment, this should be a DB connection or live feed

def load_assets():
    """Loads CatBoost Model and StandardScaler."""
    try:
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        print("Model and Scaler loaded successfully.")
        return model, scaler
    except Exception as e:
        print(f"Error loading assets: {e}")
        return None, None

def get_latest_data(data_path):
    """
    Retrieves and prepares the latest daily data for scoring.
    
    NOTE: In a real-time system, this function connects to a live data source,
    not a static CSV. We use the CSV here for demonstration continuity.
    """
    try:
        df = pd.read_csv(data_path, parse_dates=["Date"])
        
        # Get the latest date available in the dataset (Simulating T+0)
        latest_date = df["Date"].max()
        daily_df = df[df["Date"] == latest_date].copy().reset_index(drop=True)
        
        # Identify feature columns (must be consistent with training)
        non_feature_cols = ["Ticker", "Date", "Return_7d", "index"]
        feature_cols = [c for c in daily_df.columns if c not in non_feature_cols and pd.api.types.is_numeric_dtype(daily_df[c])]
        
        # Handle NaNs (same as training)
        daily_df[feature_cols] = daily_df[feature_cols].fillna(method="ffill").fillna(0)
        
        # NOTE: Implement actual Volume filter here if 'Volume' is in daily_df
        # If 'Volume' is an unscaled feature (as implied in the backtest logic),
        # filter it now before scaling.
        # daily_df = daily_df[daily_df["Volume"] > 100000] # Example filter
        
        return daily_df, feature_cols, latest_date.date()
    
    except Exception as e:
        print(f"Error loading or preparing data: {e}")
        return None, None, None

def run_scoring_and_save(db: Session):
    """Executes the full model scoring pipeline and saves TOPK to DB."""
    
    cb_ranker, scaler = load_assets()
    if cb_ranker is None or scaler is None:
        return False

    daily_df, feature_cols, current_date = get_latest_data(DATA_PATH)
    if daily_df is None or len(daily_df) == 0:
        print("No data available for scoring.")
        return False

    # 1. Scale Features
    X_scaled = scaler.transform(daily_df[feature_cols])

    # 2. Predict Scores
    group_ids = np.zeros(len(daily_df), dtype=int)
    daily_pool = Pool(data=X_scaled, group_id=group_ids)
    preds = cb_ranker.predict(daily_pool)

    # 3. Rank and Select TOPK
    daily_df["Score"] = preds
    top_stocks = daily_df.sort_values("Score", ascending=False).head(TOPK)

    # 4. Prepare and Save to Database
    new_recommendations = []
    
    for i, (_, stock) in enumerate(top_stocks.iterrows()):
        reco = Recommendation(
            ticker=stock["Ticker"],
            recommendation_date=current_date,
            model_score=stock["Score"],
            rank_position=i + 1,
            holding_period_days=5 # Optimal holding period
        )
        new_recommendations.append(reco)
    
    try:
        # Check for existing records to prevent duplication (due to UniqueConstraint)
        existing_count = db.query(Recommendation).filter(
            Recommendation.recommendation_date == current_date
        ).count()

        if existing_count > 0:
            print(f"Recommendations for {current_date} already exist ({existing_count} records). Skipping insertion.")
            return True

        db.add_all(new_recommendations)
        db.commit()
        print(f"✅ Successfully saved {len(new_recommendations)} recommendations for {current_date}.")
        return True
    
    except Exception as e:
        db.rollback()
        print(f"❌ Database error during save: {e}")
        return False

if __name__ == '__main__':
    # Initialize DB (run once before first use)
    from database import create_tables
    create_tables()

    # Get a session and run the scoring
    db_session = SessionLocal()
    run_scoring_and_save(db_session)
    db_session.close()