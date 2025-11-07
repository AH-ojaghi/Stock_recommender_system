# backend/app/schemas.py

from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class StockRecommendation(BaseModel):
    id: str
    score: float
    extra_data: Optional[Dict[str, Any]] = None
    class Config:
        orm_mode = True

class RecommendationResponse(BaseModel):
    top_k_recommendations: List[StockRecommendation]