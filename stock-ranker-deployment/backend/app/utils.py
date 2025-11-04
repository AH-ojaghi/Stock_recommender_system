import json
from pathlib import Path
import joblib
from catboost import CatBoost
from typing import List, Tuple, Any

# First try mounted path (docker-compose mounts model_artifacts to /app/model_artifacts)
MODEL_DIR = Path("/app/model_artifacts")
if not MODEL_DIR.exists():
    # fallback to repo-relative path (useful for local dev without compose)
    MODEL_DIR = Path(__file__).resolve().parents[1] / "model_artifacts"

def load_model_and_tools(model_filename: str = "catboost_ranker_optimized.cbm",
                         scaler_filename: str = "scaler.pkl",
                         feature_cols_filename: str = "feature_cols.json") -> Tuple[Any, Any, List[str]]:
    model_path = MODEL_DIR / model_filename
    scaler_path = MODEL_DIR / scaler_filename
    feature_cols_path = MODEL_DIR / feature_cols_filename

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    if not scaler_path.exists():
        raise FileNotFoundError(f"Scaler file not found at {scaler_path}")
    if not feature_cols_path.exists():
        raise FileNotFoundError(f"Feature columns file not found at {feature_cols_path}")

    # Load CatBoost model
    model = CatBoost()
    model.load_model(str(model_path))

    # Load scaler
    scaler = joblib.load(str(scaler_path))

    # Load feature columns (expecting JSON list)
    with open(str(feature_cols_path), "r", encoding="utf-8") as f:
        feature_cols = json.load(f)

    return model, scaler, feature_cols
