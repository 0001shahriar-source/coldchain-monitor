import os
import json
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score, precision_score, recall_score
import joblib

MODEL_FILE = os.path.join(os.path.dirname(__file__), "trained_model.joblib")
METRICS_FILE = os.path.join(os.path.dirname(__file__), "model_metrics.json")

def generate_ground_truth_dataset(total_records=8640):
    """
    Simulates exactly 8,640 records (24 hours at 10s intervals) of continuous
    fridge thermal physics with realistic hysteresis cycling between 3C and 7C.
    Includes realistic door openings and isolated breach incidents (prolonged door ajar
    or power cut) distributed across both train and test partitions.
    """
    np.random.seed(42)
    rows = []
    
    current_temp = 4.5
    compressor_on = True
    door_open = False
    min_guard = 0
    time_cursor = datetime.now() - timedelta(days=1)

    def is_incident(s):
        # Realistic outages and door breaches distributed across the 24 hours
        return (1200 <= s <= 1380) or (3200 <= s <= 3350) or (5400 <= s <= 5550) or (7200 <= s <= 7380)

    for step in range(total_records):
        # 1. Daily ambient temperature sinusoid (23C - 29C)
        ambient_temp = 26.0 + 3.0 * math.sin((2 * math.pi * step) / (24 * 360))
        leakage = 0.0006 * (ambient_temp - current_temp)
        
        # 2. Door opening simulation (normal access ~0.5% chance)
        if not door_open and np.random.rand() < 0.005:
            door_open = True
        elif door_open and np.random.rand() < 0.15:
            door_open = False
            
        incident = is_incident(step)
        if incident and (3200 <= step <= 3350 or 7200 <= step <= 7380):
            door_open = True # Door kept open breach
            
        door_gain = 0.045 if door_open else 0.0
        cooling = 0.025 if (compressor_on and not incident) else 0.0
        
        current_temp += (leakage + door_gain - cooling) + np.random.normal(0, 0.005)
        
        min_guard += 1
        if compressor_on and current_temp <= 3.0 and min_guard >= 6:
            compressor_on = False
            min_guard = 0
        elif not compressor_on and current_temp >= 7.0 and min_guard >= 6:
            compressor_on = True
            min_guard = 0
            
        rows.append({
            "step": step,
            "timestamp": time_cursor.isoformat(),
            "temp": round(float(current_temp), 2),
            "door_open": int(door_open),
            "compressor": int(compressor_on),
            "ambient_temp": round(float(ambient_temp), 2)
        })
        time_cursor += timedelta(seconds=10)
        
    df = pd.DataFrame(rows)
    df["future_temp_30m"] = df["temp"].shift(-180)
    df["temp_diff_1m"] = df["temp"] - df["temp"].shift(6).fillna(df["temp"])
    df["temp_diff_5m"] = df["temp"] - df["temp"].shift(30).fillna(df["temp"])
    df["temp_diff_15m"] = df["temp"] - df["temp"].shift(90).fillna(df["temp"])
    df["door_open_rolling_5m"] = df["door_open"].rolling(30, min_periods=1).mean()
    df["door_open_rolling_15m"] = df["door_open"].rolling(90, min_periods=1).mean()
    df["compressor_duty_15m"] = df["compressor"].rolling(90, min_periods=1).mean()
    
    return df.dropna().copy()

def train_and_evaluate():
    print(f"Generating 8,640 records dataset for ColdChain AI Training...")
    df = generate_ground_truth_dataset(8640)
    
    features = [
        "temp", 
        "door_open", 
        "compressor", 
        "ambient_temp", 
        "temp_diff_1m", 
        "temp_diff_5m", 
        "temp_diff_15m",
        "door_open_rolling_5m", 
        "door_open_rolling_15m",
        "compressor_duty_15m"
    ]
    X = df[features]
    y = df["future_temp_30m"]
    
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    model = GradientBoostingRegressor(n_estimators=150, max_depth=5, learning_rate=0.06, random_state=42)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    
    mae = float(mean_absolute_error(y_test, preds))
    r2 = float(r2_score(y_test, preds))
    
    true_breach = (y_test > 8.0).astype(int)
    pred_breach = (preds > 8.0).astype(int)
    
    precision = float(precision_score(true_breach, pred_breach, zero_division=0))
    recall = float(recall_score(true_breach, pred_breach, zero_division=0))
    
    metrics = {
        "dataset_records": int(len(df)),
        "train_records": int(len(X_train)),
        "test_records": int(len(X_test)),
        "mae_30m_celsius": round(mae, 3),
        "r2_score": round(r2, 3),
        "breach_precision": round(precision * 100.0, 1),
        "breach_recall": round(recall * 100.0, 1),
        "timestamp": datetime.now().isoformat()
    }
    
    joblib.dump(model, MODEL_FILE)
    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)
        
    print("Training finished successfully!")
    print(json.dumps(metrics, indent=2))
    return metrics

def run_inference(current_temp, door_open, compressor, ambient=25.0):
    """
    Loads trained model and predicts future temp 30 mins ahead.
    """
    if not os.path.exists(MODEL_FILE):
        train_and_evaluate()
        
    model = joblib.load(MODEL_FILE)
    features = np.array([[
        current_temp,
        int(door_open),
        int(compressor),
        ambient,
        0.05, # temp_diff_1m
        0.20, # temp_diff_5m
        0.30 if door_open else 0.0,
        0.50 if compressor else 0.2
    ]])
    
    pred_temp = float(model.predict(features)[0])
    return round(pred_temp, 2)

if __name__ == "__main__":
    train_and_evaluate()
