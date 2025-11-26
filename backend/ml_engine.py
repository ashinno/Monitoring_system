import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import os
from datetime import datetime

MODEL_PATH = "anomaly_model.pkl"

def get_risk_score(risk_level):
    mapping = {
        "LOW": 1,
        "INFO": 1,
        "MEDIUM": 5,
        "HIGH": 8,
        "CRITICAL": 10
    }
    return mapping.get(str(risk_level).upper(), 1) # Default to 1

def extract_features(log_data):
    """
    Extract features from a single log entry (dict) or a DataFrame row.
    Returns a list or array of features: [hour, day_of_week, risk_score]
    """
    # Handle timestamp
    ts_str = log_data.get('timestamp')
    if not ts_str:
        now = datetime.now()
        hour = now.hour
        day = now.weekday()
    else:
        try:
            # Handle ISO format
            dt = datetime.fromisoformat(str(ts_str).replace('Z', '+00:00'))
            hour = dt.hour
            day = dt.weekday()
        except Exception:
            now = datetime.now()
            hour = now.hour
            day = now.weekday()

    # Handle risk score
    risk_level = log_data.get('risk_level', 'INFO')
    risk_score = get_risk_score(risk_level)

    return [hour, day, risk_score]

def train_model(logs):
    """
    Train IsolationForest on the provided logs.
    logs: List of log objects or dicts.
    """
    if not logs:
        print("No logs provided for training.")
        return

    # Convert to list of dicts if they are SQLAlchemy objects
    data = []
    for log in logs:
        if hasattr(log, '__dict__'):
            d = log.__dict__.copy()
            # Remove SQLAlchemy internal state if present
            d.pop('_sa_instance_state', None)
            data.append(d)
        elif isinstance(log, dict):
            data.append(log)
        else:
            continue

    if not data:
        return

    df = pd.DataFrame(data)
    
    # Feature Engineering
    features_list = []
    for _, row in df.iterrows():
        features_list.append(extract_features(row))
    
    X = np.array(features_list)
    
    # Train IsolationForest
    # contamination='auto' or small value e.g. 0.05
    clf = IsolationForest(random_state=42, contamination=0.05)
    clf.fit(X)
    
    # Save model
    joblib.dump(clf, MODEL_PATH)
    print(f"Model trained on {len(X)} records and saved to {MODEL_PATH}")

def predict_anomaly(new_log):
    """
    Predict if a new log is an anomaly.
    new_log: dict
    Returns: -1 (Anomaly), 1 (Normal)
    """
    if not os.path.exists(MODEL_PATH):
        # If model doesn't exist, we can't predict. Assume Normal.
        return 1

    try:
        clf = joblib.load(MODEL_PATH)
        
        features = extract_features(new_log)
        X_new = np.array([features])
        
        prediction = clf.predict(X_new)
        return prediction[0]
    except Exception as e:
        print(f"Error in prediction: {e}")
        return 1
