import sys
import json
import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib

MODEL_FILE = os.path.join(os.path.dirname(__file__), "trained_model.joblib")

if __name__ == "__main__":
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            print(json.dumps({"error": "No input provided"}))
            sys.exit(0)
            
        data = json.loads(raw_input)
        temp = float(data.get("temp", 4.0))
        door_open = int(bool(data.get("doorOpen", False)))
        compressor = int(bool(data.get("compressor", False)))
        ambient = float(data.get("ambient", 25.0))
        
        # Real historical rolling features computed by backend from telemetryLogs:
        temp_diff_1m = float(data.get("temp_diff_1m", 0.0))
        temp_diff_5m = float(data.get("temp_diff_5m", 0.0))
        temp_diff_15m = float(data.get("temp_diff_15m", temp_diff_5m * 1.5))
        door_open_rolling_5m = float(data.get("door_open_rolling_5m", 0.0))
        door_open_rolling_15m = float(data.get("door_open_rolling_15m", door_open_rolling_5m))
        compressor_duty_15m = float(data.get("compressor_duty_15m", 0.5))
        
        feature_names = [
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

        row = pd.DataFrame([[
            temp,
            door_open,
            compressor,
            ambient,
            temp_diff_1m,
            temp_diff_5m,
            temp_diff_15m,
            door_open_rolling_5m,
            door_open_rolling_15m,
            compressor_duty_15m
        ]], columns=feature_names)

        model = joblib.load(MODEL_FILE)
        raw_pred = float(model.predict(row)[0])
        pred = round(raw_pred, 2)

        print(json.dumps({"predicted_temp": pred, "success": True}))
    except Exception as e:
        print(json.dumps({"error": str(e), "success": False}))
