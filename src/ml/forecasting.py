# src/ml/forecasting.py
"""ML Forecasting module — load trained model dan hasilkan prediksi."""

import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL_PATH = BASE_DIR / "models" / "sales_forecast.pkl"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Cache model di memori
_model_cache = None


def load_model():
    """Load trained model dari file pickle."""
    global _model_cache
    if _model_cache is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model tidak ditemukan di {MODEL_PATH}. "
                "Jalankan notebook 04_sales_forecasting.ipynb terlebih dahulu."
            )
        _model_cache = joblib.load(MODEL_PATH)
    return _model_cache


def get_daily_sales():
    """Load daily sales data yang sudah diproses ETL."""
    path = PROCESSED_DIR / "daily_sales.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


def get_inventory_metrics():
    """Load inventory metrics yang sudah dihitung di notebook 03."""
    path = PROCESSED_DIR / "inventory_metrics.csv"
    return pd.read_csv(path)


def predict_revenue(days_ahead: int = 7) -> pd.DataFrame:
    """
    Prediksi total revenue harian untuk N hari ke depan.
    
    Menggunakan recursive forecasting:
    - Prediksi hari 1 → pakai lag dari data aktual
    - Prediksi hari 2 → pakai prediksi hari 1 sebagai lag_1
    - dst.
    
    Returns:
        DataFrame dengan kolom [date, predicted_revenue]
    """
    bundle = load_model()
    model = bundle["model"]
    feature_cols = bundle["feature_cols"]
    
    daily = get_daily_sales()
    last_date = daily["date"].max()
    
    # Ambil data historis yang cukup untuk lag
    history = daily["total_revenue"].values.tolist()
    
    predictions = []
    for i in range(1, days_ahead + 1):
        future_date = last_date + pd.Timedelta(days=i)
        
        # Build features
        row = {
            "day_of_week": future_date.dayofweek,
            "is_weekend": int(future_date.dayofweek >= 5),
            "lag_1": history[-1],
            "lag_7": history[-7] if len(history) >= 7 else history[0],
            "rolling_mean_7": np.mean(history[-7:]),
            "rolling_mean_14": np.mean(history[-14:]) if len(history) >= 14 else np.mean(history[-7:]),
        }
        
        X = pd.DataFrame([row])[feature_cols]
        pred = float(model.predict(X)[0])
        pred = max(pred, 0)  # revenue tidak mungkin negatif
        
        predictions.append({"date": future_date, "predicted_revenue": round(pred)})
        history.append(pred)  # recursive: pakai prediksi sebagai input berikutnya
    
    return pd.DataFrame(predictions)


def get_restock_recommendations(safety_factor: float = 1.3) -> list[dict]:
    """
    Hasilkan rekomendasi restock berdasarkan:
    - avg_daily_sales dari inventory metrics
    - current_stock
    - days_remaining
    - safety_factor (default 1.3 = buffer 30%)
    
    Logic:
    - Hitung kebutuhan 7 hari ke depan: avg_daily_sales * 7 * safety_factor
    - Restock qty = kebutuhan - current_stock (minimal 0)
    - Prioritas: produk dengan days_remaining terendah di atas
    
    Returns:
        List of dicts sorted by urgency (days_remaining ascending)
    """
    metrics = get_inventory_metrics()
    
    recommendations = []
    for _, row in metrics.iterrows():
        avg_daily = row.get("avg_daily_sales", 0)
        current = row.get("current_stock", 0)
        days_rem = row.get("days_remaining", None)
        
        if avg_daily <= 0:
            continue
        
        demand_7d = avg_daily * 7 * safety_factor
        restock_qty = max(0, round(demand_7d - current))
        
        # Tentukan urgency
        if days_rem is not None and days_rem < 3:
            urgency = "KRITIS"
        elif days_rem is not None and days_rem < 7:
            urgency = "SEGERA"
        elif days_rem is not None and days_rem < 14:
            urgency = "PERLU"
        else:
            urgency = "AMAN"
        
        recommendations.append({
            "product_id": int(row["product_id"]),
            "name": row["name"],
            "current_stock": round(current, 1),
            "avg_daily_sales": round(avg_daily, 1),
            "days_remaining": round(days_rem, 1) if pd.notna(days_rem) else None,
            "demand_7_hari": round(demand_7d),
            "restock_qty": restock_qty,
            "urgency": urgency,
        })
    
    # Sort by days_remaining (None last), then by restock_qty descending
    recommendations.sort(
        key=lambda x: (x["days_remaining"] if x["days_remaining"] is not None else 999)
    )
    
    return recommendations
