from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from typing import List, Optional
from .utils import load_model_and_tools
import io

app = FastAPI(title="Stock Ranker API")

# Allow CORS (در production می‌توان originها را محدود کرد)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model and preprocessing artifacts on startup
try:
    model, scaler, FEATURE_COLS = load_model_and_tools()
except Exception as e:
    model = None
    scaler = None
    FEATURE_COLS = []
    print("Warning: model/tools not loaded:", e)

def detect_id_column(df: pd.DataFrame) -> Optional[str]:
    candidates = ['ticker', 'symbol', 'id', 'code', 'name']
    for c in candidates:
        if c in df.columns:
            return c
    return None

def find_extra_column(df: pd.DataFrame, feature_cols: List[str]) -> Optional[str]:
    """
    Try to find a helpful extra column to return to frontend.
    1) Prefer 'Volume_mean_5d' if present.
    2) Else look for any column containing 'volume' (case-insensitive) from df columns.
    3) Else None.
    """
    if 'Volume_mean_5d' in df.columns:
        return 'Volume_mean_5d'
    # search in feature_cols first for any name containing 'volume'
    for col in feature_cols:
        if 'volume' in col.lower() and col in df.columns:
            return col
    # fallback: search all df columns
    for col in df.columns:
        if 'volume' in col.lower():
            return col
    return None

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None or scaler is None or not FEATURE_COLS:
        raise HTTPException(status_code=500, detail="Model or preprocessing tools not available on server.")

    if not file.filename.lower().endswith((".csv", ".txt")):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV file: {e}")

    if df.shape[0] == 0:
        raise HTTPException(status_code=400, detail="Uploaded CSV is empty.")

    id_col = detect_id_column(df)
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required feature columns in CSV: {missing}")

    X = df[FEATURE_COLS].copy()
    X = X.fillna(method="ffill").fillna(0)

    try:
        X_scaled = scaler.transform(X.values)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scaler transform failed: {e}")

    try:
        preds = model.predict(X_scaled)
        preds = np.array(preds).reshape(-1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model prediction failed: {e}")

    out_df = df.copy()
    out_df["_score"] = preds

    topk = out_df.sort_values("_score", ascending=False).head(10).reset_index(drop=True)

    extra_col = find_extra_column(out_df, FEATURE_COLS)

    results = []
    for idx, row in topk.iterrows():
        item = {}
        # id (ticker or fallback index)
        if id_col:
            item["id"] = row[id_col]
        else:
            # if original index exists, try to preserve original index if present in uploaded CSV
            item["id"] = int(row.name) if hasattr(row.name, "__int__") else str(row.name)
        item["score"] = float(row["_score"])
        # include extra column value if available
        if extra_col and extra_col in row:
            # ensure json-serializable
            val = row[extra_col]
            if pd.isna(val):
                item[extra_col] = None
            else:
                # convert numpy types
                if isinstance(val, (np.floating, np.integer)):
                    item[extra_col] = float(val)
                else:
                    item[extra_col] = val
        results.append(item)

    return {"top_10": results}
