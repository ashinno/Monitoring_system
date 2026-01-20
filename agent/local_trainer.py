import os
import json
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime

# Local model storage
LOCAL_MODEL_PATH = "local_model.pkl"

class LocalTrainer:
    """
    Handles local model training for Federated Learning (Pathway 1).
    Ensures data privacy by keeping raw logs on the device.
    """
    
    def __init__(self):
        self.logs_buffer = []
        self.model = None
        
    def add_log(self, log_entry):
        """
        Adds a log to the local training buffer.
        """
        self.logs_buffer.append(log_entry)
        
    def train(self):
        """
        Trains a local Isolation Forest model on buffered logs.
        Returns: Model parameters (simulated weights) for federation.
        """
        if len(self.logs_buffer) < 10:
            print("Not enough local logs to train.")
            return None
            
        print(f"Training local model on {len(self.logs_buffer)} logs...")
        
        # Feature Extraction (Simplified matching backend)
        features = []
        for log in self.logs_buffer:
            # We assume log is a dict
            ts = log.get('timestamp', datetime.now().isoformat())
            try:
                dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                hour = dt.hour
                day = dt.weekday()
            except:
                hour = 12
                day = 0
            
            # Risk mapping
            risk = log.get('risk_level', 'INFO')
            risk_map = {"LOW": 1, "INFO": 1, "MEDIUM": 5, "HIGH": 8, "CRITICAL": 10}
            risk_score = risk_map.get(risk, 1)
            
            features.append([hour, day, risk_score])
            
        X = np.array(features)
        
        # Train
        clf = IsolationForest(n_estimators=50, random_state=42)
        clf.fit(X)
        self.model = clf
        
        # Save local model
        joblib.dump(clf, LOCAL_MODEL_PATH)
        
        # Clear buffer (or keep sliding window?)
        # For FL, we typically train on new data.
        self.logs_buffer = []
        
        print("Local training complete.")
        
        return self.get_model_weights()
        
    def get_model_weights(self):
        """
        Extracts 'weights' to send to server.
        For IsolationForest, this is complex (tree structures).
        For Thesis Simulation: We send statistical summaries or encoded tree paths.
        Here we simulate sending 'feature_importances' or similar metadata.
        """
        if not self.model:
            return None
            
        # Simulated weights: Just random noise + some structure for the demo
        # In a real neural net FL, this would be: return self.model.get_weights()
        return {
            "n_estimators": 50,
            "max_samples": "auto",
            "dummy_weights": np.random.rand(10).tolist() # Placeholder
        }

local_trainer = LocalTrainer()
