
import pandas as pd
import numpy as np
import joblib
import os
import shap
from datetime import datetime
from sqlalchemy.orm import Session

# Import new ML components
# Try relative import, fall back to absolute
try:
    from backend.ml.trainer import ModelTrainer
    from backend.ml.models import IsolationForestModel
    from backend.ml.pipeline import DataPipeline
except ImportError:
    try:
        from .ml.trainer import ModelTrainer
        from .ml.models import IsolationForestModel
        from .ml.pipeline import DataPipeline
    except ImportError:
        # Last resort for when running tests where backend is not in path as a package
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from ml.trainer import ModelTrainer
        from ml.models import IsolationForestModel
        from ml.pipeline import DataPipeline

MODEL_PATH = "ml_artifacts/isolation_forest.pkl"
EXPLAINER_PATH = "ml_artifacts/isolation_forest_explainer.pkl"
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
    Legacy feature extraction for compatibility or fallback.
    The new pipeline handles this internally.
    """
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

    risk_level = log_data.get('risk_level', 'INFO')
    risk_score = get_risk_score(risk_level)

    return [hour, day, risk_score]

def train_model(db: Session):
    """
    Trigger the new training pipeline.
    """
    print("Starting ML Model Training...")
    trainer = ModelTrainer(db)
    trainer.train_all()
    
    # Evaluate and print results
    results = trainer.evaluate()
    print("Training Results:", results)

def predict_anomaly(new_log):
    """
    Predict if a new log is an anomaly using the new IsolationForestModel.
    new_log: dict
    Returns: -1 (Anomaly), 1 (Normal)
    """
    try:
        # Load pipeline artifacts to preprocess the single log
        pipeline = DataPipeline()
        if not pipeline.load_artifacts():
             # Fallback if no artifacts (not trained yet)
             return 1
             
        # Convert log to DataFrame
        df = pd.DataFrame([new_log])
        
        # Preprocess
        X = pipeline.preprocess(df, training=False)
        
        # Load Model
        model = IsolationForestModel()
        if not model.load():
            return 1
            
        prediction = model.predict(X)
        return prediction[0]
    except Exception as e:
        print(f"Error in prediction: {e}")
        return 1

def explain_prediction(log_features):
    """
    Calculate SHAP values for the specific log entry.
    Note: SHAP explanation needs to be adapted to the new pipeline.
    For now, we return a placeholder or adapt if possible.
    """
    # TODO: Update SHAP integration with the new pipeline features
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
