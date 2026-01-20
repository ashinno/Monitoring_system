import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import os
import shap
from datetime import datetime

MODEL_PATH = "anomaly_model.pkl"
EXPLAINER_PATH = "anomaly_explainer.pkl"
GLOBAL_MODEL_PATH = "global_model.pkl"

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
    
    # Create and save SHAP explainer
    explainer = shap.TreeExplainer(clf)
    joblib.dump(explainer, EXPLAINER_PATH)
    
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

def explain_prediction(log_features):
    """
    Calculate SHAP values for the specific log entry.
    log_features: list or array [hour, day, risk_score]
    Returns: JSON object mapping feature names to their impact score.
    """
    if not os.path.exists(EXPLAINER_PATH):
        return {}

    try:
        explainer = joblib.load(EXPLAINER_PATH)
        
        # shap_values returns a matrix if input is 2D, or list of arrays.
        # TreeExplainer for IsolationForest:
        # shap_values shape for single sample: (1, n_features)
        
        X_new = np.array([log_features])
        shap_values = explainer.shap_values(X_new)
        
        # shap_values might be a list (one for each class) or array.
        # For IsolationForest, it usually returns just the values for the score.
        
        # Check shape
        # If shap_values is a list, take the first element (though IsolationForest is usually single output)
        if isinstance(shap_values, list):
             shap_values = shap_values[0]
             
        # Now shap_values should be (1, n_features)
        vals = shap_values[0]
        
        feature_names = ["hour_of_day", "day_of_week", "risk_score"]
        
        explanation = {}
        for name, val in zip(feature_names, vals):
            explanation[name] = round(float(val), 4)
            
        return explanation
    except Exception as e:
        print(f"Error in explanation: {e}")
        return {}

# --- Pathway 1: Federated Learning Support ---

class FederatedAggregator:
    """
    Simulates the aggregation of model weights from multiple agents.
    In a real FL system, we would average the weights of Neural Networks.
    Since we are using IsolationForest (which is not easily parameter-averaged),
    we will simulate this by aggregating the 'estimators_' if they were compatible,
    or more realistically for this Thesis prototype, we switch to a simple 
    Mean/Variance model for the FL demo.
    
    For the Thesis: We will assume the 'Model' being federated is a set of 
    Thresholds or a simple Neural Network (e.g. Autoencoder) for anomaly detection.
    """
    
    def __init__(self):
        self.local_updates = []
        
    def collect_update(self, agent_id, weights):
        """
        Collects weights from an agent.
        weights: dict of numpy arrays
        """
        print(f"Received FL update from Agent {agent_id}")
        self.local_updates.append(weights)
        
    def aggregate(self):
        """
        Performs Federated Averaging (FedAvg).
        """
        if not self.local_updates:
            return None
            
        print(f"Aggregating updates from {len(self.local_updates)} agents...")
        
        # Example: Average the weights (assuming simple dict structure)
        n_updates = len(self.local_updates)
        avg_weights = {}
        
        # Initialize with first update
        first_update = self.local_updates[0]
        for key in first_update:
            avg_weights[key] = first_update[key] / n_updates
            
        # Add rest
        for i in range(1, n_updates):
            update = self.local_updates[i]
            for key in update:
                avg_weights[key] += update[key] / n_updates
                
        # Clear buffer
        self.local_updates = []
        
        # Save Global Model
        joblib.dump(avg_weights, GLOBAL_MODEL_PATH)
        print("Global Model updated via Federated Averaging.")
        return avg_weights

federated_aggregator = FederatedAggregator()
