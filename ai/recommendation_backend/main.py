# main.py
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date
import time
import threading

# Import components
from database import create_tables, get_db
from models import Recommendation
from scoring_engine import run_scoring_and_save

# --- FastAPI Initialization ---
app = FastAPI(
    title="Stock Ranker API",
    version="v1.0",
    description="Serves daily stock recommendations from the CatBoost Ranker model."
)

# --- Pydantic Schema for API Response ---
# Define the structure of the data returned to the user
from pydantic import BaseModel

class RecommendationSchema(BaseModel):
    ticker: str
    recommendation_date: date
    model_score: float
    rank_position: int
    holding_period_days: int

    class Config:
        orm_mode = True # Enables Pydantic to read from SQLAlchemy model

# --- 1. API Endpoints ---

@app.get("/api/v1/recommendations/latest", response_model=List[RecommendationSchema])
def get_latest_recommendations(db: Session = Depends(get_db)):
    """Retrieves the latest TOPK recommendations from the database."""
    
    # 1. Find the most recent date with recommendations
    latest_date_query = db.query(Recommendation.recommendation_date)\
        .order_by(Recommendation.recommendation_date.desc())\
        .first()

    if not latest_date_query:
        raise HTTPException(status_code=404, detail="No recommendations found in the database.")

    latest_date = latest_date_query[0]

    # 2. Fetch all recommendations for that date, sorted by rank
    recos = db.query(Recommendation)\
        .filter(Recommendation.recommendation_date == latest_date)\
        .order_by(Recommendation.rank_position.asc())\
        .all()
    
    return recos

# --- 2. Scheduled Job (Scoring) ---

def scheduled_scoring_job():
    """The function that runs the scoring engine once per day."""
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running daily scoring job...")
    
    # Get a dedicated session for the job
    db_session = SessionLocal()
    success = run_scoring_and_save(db_session)
    db_session.close()
    
    status = "SUCCESS" if success else "FAILURE"
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Daily scoring job finished. Status: {status}")

def run_scheduler(delay_seconds=3600):
    """Simple thread-based scheduler (for demonstration/local testing)."""
    
    # Run once immediately on startup (to populate initial data)
    scheduled_scoring_job() 

    # Then run every 24 hours (86400 seconds) - use a proper task manager in production!
    # Here we use 1 hour (3600s) for easier testing
    while True:
        time.sleep(delay_seconds) # Wait for the specified delay
        scheduled_scoring_job()

@app.on_event("startup")
def startup_event():
    """Runs on application startup."""
    # 1. Ensure DB tables exist
    create_tables()

    # 2. Start the scoring scheduler in a background thread
    # NOTE: In production (e.g., Docker/Cloud), use dedicated tools like Celery or Airflow for scheduling.
    # This thread is simple for local demonstration.
    scheduler_thread = threading.Thread(target=run_scheduler, kwargs={'delay_seconds': 3600}) # Run every hour for test
    scheduler_thread.daemon = True
    scheduler_thread.start()
    print("Background scoring scheduler initialized.")

# --- 3. Main Run Command ---
if __name__ == "__main__":
    # Command to start the API server
    # Run with: python main.py
    uvicorn.run(app, host="0.0.0.0", port=8000)