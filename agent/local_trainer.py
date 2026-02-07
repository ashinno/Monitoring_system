import os
import json
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime

# Local model storage
LOCAL_MODEL_PATH = "local_model.pkl"


def _laplace_noise(scale: float) -> float:
    if scale <= 0:
        return 0.0
    return float(np.random.laplace(loc=0.0, scale=scale))


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

class LocalTrainer:
    """
    Handles local model training for Federated Learning (Pathway 1).
    Ensures data privacy by keeping raw logs on the device.
    """
    
    def __init__(self):
        self.logs_buffer = []
        self.model = None
        self.feature_vector = np.zeros(3, dtype=np.float64)
        self.last_mask = None
        self.last_round_id = None
        
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

        # Aggregate a compact local feature vector that can be safely federated
        self.feature_vector = np.array([
            float(np.mean(X[:, 0])),  # hour
            float(np.mean(X[:, 1])),  # day
            float(np.mean(X[:, 2])),  # risk_score
        ], dtype=np.float64)
        
        # Save local model
        joblib.dump(clf, LOCAL_MODEL_PATH)
        
        # Clear buffer (or keep sliding window?)
        # For FL, we typically train on new data.
        self.logs_buffer = []
        
        print("Local training complete.")
        
        return self.get_model_weights()

    def _dp_clip_and_noise(self, vector: np.ndarray):
        dp_enabled = _to_bool(os.getenv("AGENT_DP_ENABLED", "1"), True)
        clip_norm = max(1e-6, float(os.getenv("AGENT_DP_CLIP_NORM", "10.0")))
        epsilon = max(1e-6, float(os.getenv("AGENT_DP_EPSILON", "1.0")))
        sensitivity = float(os.getenv("AGENT_DP_SENSITIVITY", "1.0"))

        clipped = np.array(vector, dtype=np.float64)
        norm = float(np.linalg.norm(clipped, ord=2))
        if norm > clip_norm:
            clipped = clipped * (clip_norm / norm)

        if not dp_enabled:
            return clipped, {
                "enabled": False,
                "epsilon": None,
                "clip_norm": clip_norm,
                "sensitivity": sensitivity,
                "mechanism": "none",
            }

        scale = sensitivity / epsilon
        noisy = clipped + np.array([_laplace_noise(scale) for _ in range(len(clipped))], dtype=np.float64)
        return noisy, {
            "enabled": True,
            "epsilon": epsilon,
            "clip_norm": clip_norm,
            "sensitivity": sensitivity,
            "mechanism": "laplace",
        }

    def build_secure_update(self, round_id: str, min_clients: int = 1, timeout_seconds: int = 300):
        if self.feature_vector is None or len(self.feature_vector) == 0:
            return None

        vector = np.array(self.feature_vector, dtype=np.float64)
        dp_vector, dp_meta = self._dp_clip_and_noise(vector)

        seed = int.from_bytes(os.urandom(8), "big")
        rng = np.random.default_rng(seed)
        mask = rng.normal(0.0, 1.0, size=len(dp_vector))
        masked_update = dp_vector + mask

        self.last_mask = mask
        self.last_round_id = round_id

        return {
            "round_id": round_id,
            "masked_update": masked_update.tolist(),
            "num_samples": len(self.logs_buffer) if self.logs_buffer else 1,
            "min_clients": min_clients,
            "timeout_seconds": timeout_seconds,
            "dp": dp_meta,
        }

    def build_mask_reveal(self):
        if self.last_round_id is None or self.last_mask is None:
            return None
        return {
            "round_id": self.last_round_id,
            "mask": self.last_mask.tolist(),
        }
        
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
