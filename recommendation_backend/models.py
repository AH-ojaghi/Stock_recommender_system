# models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Date, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class Recommendation(Base):
    """SQLAlchemy model for storing daily stock recommendations."""
    __tablename__ = "daily_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Core Recommendation Data
    ticker = Column(String, index=True, nullable=False)
    recommendation_date = Column(Date, nullable=False)
    model_score = Column(Float, nullable=False)
    rank_position = Column(Integer, nullable=False) # 1st, 2nd, 3rd, etc.
    
    # Operational Details (for monitoring)
    holding_period_days = Column(Integer, default=5)
    
    # Timestamp for when the record was created
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Ensure only one recommendation per ticker per day
    __table_args__ = (UniqueConstraint('ticker', 'recommendation_date', name='uq_ticker_date'),)

    def __repr__(self):
        return f"<Recommendation(ticker='{self.ticker}', date='{self.recommendation_date}', rank={self.rank_position})>"