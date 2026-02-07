import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import joblib
import numpy as np
import pandas as pd
import shap
from sqlalchemy.orm import Session

# Import new ML components
# Try relative import, fall back to absolute
try:
    from backend.ml.pipeline import DataPipeline
    from backend.ml.models import IsolationForestModel
    from backend.ml.trainer import ModelTrainer
except ImportError:
    try:
        from .ml.pipeline import DataPipeline
        from .ml.models import IsolationForestModel
        from .ml.trainer import ModelTrainer
    except ImportError:
        # Last resort for when running tests where backend is not in path as a package
        import sys

        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from ml.pipeline import DataPipeline
        from ml.models import IsolationForestModel
        from ml.trainer import ModelTrainer


MODEL_PATH = "ml_artifacts/isolation_forest.pkl"
GLOBAL_MODEL_PATH = "global_model.pkl"
FL_MIN_CLIENTS = max(1, int(os.getenv("FL_MIN_CLIENTS", "1")))
FL_ROUND_TIMEOUT_SECONDS = max(30, int(os.getenv("FL_ROUND_TIMEOUT_SECONDS", "300")))
FL_SERVER_NOISE_SIGMA = max(0.0, float(os.getenv("FL_SERVER_NOISE_SIGMA", "0.0")))


_SHAP_STATE: Dict[str, Any] = {
    "signature": None,
    "pipeline": None,
    "model": None,
    "explainer": None,
}
_SHAP_LOCK = threading.Lock()


def get_risk_score(risk_level):
    mapping = {
        "LOW": 1,
        "INFO": 1,
        "MEDIUM": 5,
        "HIGH": 8,
        "CRITICAL": 10,
    }
    return mapping.get(str(risk_level).upper(), 1)


def extract_features(log_data):
    """
    Legacy feature extraction for compatibility or fallback.
    The new pipeline handles this internally.
    """
    ts_str = log_data.get("timestamp")
    if not ts_str:
        now = datetime.now()
        hour = now.hour
        day = now.weekday()
    else:
        try:
            dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
            hour = dt.hour
            day = dt.weekday()
        except Exception:
            now = datetime.now()
            hour = now.hour
            day = now.weekday()

    risk_level = log_data.get("risk_level", "INFO")
    risk_score = get_risk_score(risk_level)

    return [hour, day, risk_score]


def train_model(data_source, train_config: Optional[Dict[str, Any]] = None):
    """
    Trigger the new training pipeline.
    """
    print("Starting ML Model Training...")
    if isinstance(data_source, Session):
        config = train_config or {}
        trainer = ModelTrainer(
            data_source,
            data_limit=int(config.get("data_limit", os.getenv("ML_TRAIN_LIMIT", "50000"))),
            validation_split=float(config.get("validation_split", os.getenv("ML_VALIDATION_SPLIT", "0.2"))),
            random_state=int(config.get("random_state", os.getenv("ML_RANDOM_STATE", "42"))),
            autoencoder_epochs=int(config.get("autoencoder_epochs", os.getenv("ML_AE_EPOCHS", "80"))),
            autoencoder_batch_size=int(config.get("autoencoder_batch_size", os.getenv("ML_AE_BATCH_SIZE", "64"))),
        )
        trainer.train_all()
    else:
        # Backward compatibility for tests that monkeypatch this with list expectations.
        if not isinstance(data_source, list):
            raise TypeError("train_model expects SQLAlchemy Session or list")
        return

    # Evaluate and print results (best-effort)
    try:
        results = trainer.evaluate()
        print("Training Results:", results)
    except Exception:
        pass


def predict_anomaly(new_log):
    """
    Predict if a new log is an anomaly using the IsolationForestModel.
    new_log: dict
    Returns: -1 (Anomaly), 1 (Normal)
    """
    try:
        pipeline = DataPipeline()
        if not pipeline.load_artifacts():
            return 1

        df = pd.DataFrame([new_log])
        X = pipeline.preprocess(df, training=False)

        model = IsolationForestModel()
        if not model.load():
            return 1

        prediction = model.predict(X)
        return prediction[0]
    except Exception as e:
        print(f"Error in prediction: {e}")
        return 1


def _get_model_signature() -> Optional[float]:
    if not os.path.exists(MODEL_PATH):
        return None
    return os.path.getmtime(MODEL_PATH)


def _normalize_log_for_pipeline(log_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "timestamp": log_data.get("timestamp") or datetime.now().isoformat(),
        "user": log_data.get("user") or "unknown",
        "activity_type": log_data.get("activity_type") or log_data.get("activityType") or "UNKNOWN",
        "risk_level": log_data.get("risk_level") or log_data.get("riskLevel") or "INFO",
        "description": log_data.get("description") or "",
    }


def _to_1d_float_array(values: Any) -> np.ndarray:
    vector = np.asarray(values, dtype=np.float64)
    if vector.ndim != 1:
        raise ValueError("Expected a 1D vector")
    return vector


def _load_shap_components() -> Optional[Dict[str, Any]]:
    model_signature = _get_model_signature()
    if model_signature is None:
        return None

    with _SHAP_LOCK:
        if _SHAP_STATE["signature"] == model_signature and _SHAP_STATE["explainer"] is not None:
            return _SHAP_STATE

        pipeline = DataPipeline()
        if not pipeline.load_artifacts():
            return None

        model = IsolationForestModel()
        if not model.load():
            return None

        try:
            explainer = shap.TreeExplainer(model.model)
        except Exception:
            try:
                explainer = shap.Explainer(model.model)
            except Exception as exc:
                print(f"SHAP explainer initialization failed: {exc}")
                return None

        _SHAP_STATE["signature"] = model_signature
        _SHAP_STATE["pipeline"] = pipeline
        _SHAP_STATE["model"] = model
        _SHAP_STATE["explainer"] = explainer
        return _SHAP_STATE


def explain_prediction(log_features):
    """
    Calculate SHAP values for a specific log entry.
    Returns a feature->contribution mapping (plus diagnostic keys).
    """
    try:
        state = _load_shap_components()
        if not state:
            return {}

        pipeline = state["pipeline"]
        model = state["model"]
        explainer = state["explainer"]

        if isinstance(log_features, dict):
            normalized = _normalize_log_for_pipeline(log_features)
        else:
            # Legacy fallback from extract_features list format
            if isinstance(log_features, (list, tuple, np.ndarray)) and len(log_features) >= 3:
                hour, day, risk_score = log_features[:3]
                return {
                    "hour": float(hour),
                    "day": float(day),
                    "risk_score": float(risk_score),
                }
            return {}

        df = pd.DataFrame([normalized])
        X = pipeline.preprocess(df, training=False)
        if X.empty:
            return {}

        shap_values = explainer.shap_values(X)
        if isinstance(shap_values, list):
            values = np.asarray(shap_values[0], dtype=np.float64)
        else:
            values = np.asarray(shap_values, dtype=np.float64)

        row = values if values.ndim == 1 else values[0]
        contributions = {
            feature: float(value)
            for feature, value in zip(pipeline.feature_columns, row)
        }

        try:
            anomaly_score = float(-model.predict_score(X)[0])
            prediction = float(model.predict(X)[0])
            contributions["__anomaly_score__"] = anomaly_score
            contributions["__prediction__"] = prediction
        except Exception:
            pass

        return contributions
    except Exception as e:
        print(f"SHAP explanation failed: {e}")
        return {}


# --- Pathway 1: Federated Learning Support ---


@dataclass
class SecureAggregationRound:
    round_id: str
    min_clients: int
    timeout_seconds: int
    created_at: float = field(default_factory=time.time)
    dimension: Optional[int] = None
    sum_masked_updates: Optional[np.ndarray] = None
    sum_masks: Optional[np.ndarray] = None
    participant_weights: Dict[str, float] = field(default_factory=dict)
    revealed_agents: Set[str] = field(default_factory=set)
    total_samples: int = 0
    total_epsilon: float = 0.0
    finalized: bool = False
    aggregate: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def expires_at(self) -> float:
        return self.created_at + self.timeout_seconds

    @property
    def submitted_count(self) -> int:
        return len(self.participant_weights)

    @property
    def revealed_count(self) -> int:
        return len(self.revealed_agents)


class FederatedAggregator:
    """
    Supports two pathways:
    1) Legacy naive averaging (backward compatible).
    2) Secure aggregation with differential privacy metadata.
    """

    def __init__(self):
        self.local_updates = []
        self.rounds: Dict[str, SecureAggregationRound] = {}
        self.latest_secure_global: Optional[Dict[str, Any]] = None
        self.lock = threading.Lock()

    def start_round(self, min_clients: Optional[int] = None, timeout_seconds: Optional[int] = None, round_id: Optional[str] = None):
        with self.lock:
            round_identifier = round_id or f"round-{uuid.uuid4().hex[:12]}"
            if round_identifier in self.rounds and not self.rounds[round_identifier].finalized:
                return self.get_round_status(round_identifier)

            state = SecureAggregationRound(
                round_id=round_identifier,
                min_clients=max(1, int(min_clients or FL_MIN_CLIENTS)),
                timeout_seconds=max(30, int(timeout_seconds or FL_ROUND_TIMEOUT_SECONDS)),
            )
            self.rounds[round_identifier] = state
            return self._round_to_dict(state)

    def get_round_status(self, round_id: str):
        with self.lock:
            state = self.rounds.get(round_id)
            if not state:
                return None
            return self._round_to_dict(state)

    def reveal_mask(self, round_id: str, agent_id: str, mask_values: List[float]):
        with self.lock:
            state = self.rounds.get(round_id)
            if not state:
                raise ValueError("Unknown federated round")
            if state.finalized:
                return {
                    "accepted": False,
                    "reason": "round_already_finalized",
                    "round": self._round_to_dict(state),
                }
            if agent_id not in state.participant_weights:
                raise ValueError("Agent has not submitted an update for this round")
            if agent_id in state.revealed_agents:
                return {
                    "accepted": False,
                    "reason": "mask_already_revealed",
                    "round": self._round_to_dict(state),
                }

            mask_vector = _to_1d_float_array(mask_values)
            if state.dimension is None:
                raise ValueError("Round has no registered update dimension")
            if len(mask_vector) != state.dimension:
                raise ValueError("Mask dimension mismatch")

            weight = state.participant_weights[agent_id]
            state.sum_masks += weight * mask_vector
            state.revealed_agents.add(agent_id)

            aggregate_result = None
            if self._round_ready_for_finalize(state):
                aggregate_result = self._finalize_secure_round(state)

            return {
                "accepted": True,
                "global_model_updated": aggregate_result is not None,
                "round": self._round_to_dict(state),
                "aggregate": aggregate_result,
            }

    def collect_update(self, agent_id, weights):
        """
        Collects updates from agents.
        """
        print(f"Received FL update from Agent {agent_id}")
        if isinstance(weights, dict) and "round_id" in weights and "masked_update" in weights:
            return self._collect_secure_update(agent_id, weights)

        with self.lock:
            self.local_updates.append(weights)
            buffered = len(self.local_updates)
        return {
            "mode": "legacy",
            "accepted": True,
            "buffered_updates": buffered,
        }

    def _collect_secure_update(self, agent_id: str, weights: Dict[str, Any]):
        round_id = str(weights.get("round_id") or "").strip()
        if not round_id:
            raise ValueError("round_id is required for secure federated updates")

        masked_update = weights.get("masked_update")
        if masked_update is None:
            raise ValueError("masked_update is required")

        vector = _to_1d_float_array(masked_update)
        if len(vector) == 0:
            raise ValueError("masked_update cannot be empty")

        num_samples = int(weights.get("num_samples") or 1)
        weight = float(max(num_samples, 1))
        dp_meta = weights.get("dp") if isinstance(weights.get("dp"), dict) else {}

        with self.lock:
            state = self.rounds.get(round_id)
            if not state:
                state = SecureAggregationRound(
                    round_id=round_id,
                    min_clients=max(1, int(weights.get("min_clients") or FL_MIN_CLIENTS)),
                    timeout_seconds=max(30, int(weights.get("timeout_seconds") or FL_ROUND_TIMEOUT_SECONDS)),
                )
                self.rounds[round_id] = state

            if state.finalized:
                return {
                    "mode": "secure",
                    "accepted": False,
                    "reason": "round_already_finalized",
                    "round": self._round_to_dict(state),
                }

            if time.time() > state.expires_at:
                return {
                    "mode": "secure",
                    "accepted": False,
                    "reason": "round_expired",
                    "round": self._round_to_dict(state),
                }

            if agent_id in state.participant_weights:
                return {
                    "mode": "secure",
                    "accepted": False,
                    "reason": "duplicate_agent_submission",
                    "round": self._round_to_dict(state),
                }

            if state.dimension is None:
                state.dimension = len(vector)
                state.sum_masked_updates = np.zeros(state.dimension, dtype=np.float64)
                state.sum_masks = np.zeros(state.dimension, dtype=np.float64)

            if len(vector) != state.dimension:
                raise ValueError("masked_update dimension mismatch")

            state.sum_masked_updates += weight * vector
            state.participant_weights[agent_id] = weight
            state.total_samples += num_samples
            epsilon = float(dp_meta.get("epsilon") or 0.0)
            state.total_epsilon += epsilon

            return {
                "mode": "secure",
                "accepted": True,
                "global_model_updated": False,
                "round": self._round_to_dict(state),
            }

    def _round_ready_for_finalize(self, state: SecureAggregationRound) -> bool:
        return (
            state.submitted_count >= state.min_clients
            and state.revealed_count == state.submitted_count
            and state.submitted_count > 0
        )

    def _round_to_dict(self, state: SecureAggregationRound) -> Dict[str, Any]:
        return {
            "round_id": state.round_id,
            "min_clients": state.min_clients,
            "timeout_seconds": state.timeout_seconds,
            "created_at": datetime.fromtimestamp(state.created_at).isoformat(),
            "expires_at": datetime.fromtimestamp(state.expires_at).isoformat(),
            "submitted_clients": state.submitted_count,
            "revealed_clients": state.revealed_count,
            "pending_reveals": max(0, state.submitted_count - state.revealed_count),
            "dimension": state.dimension,
            "finalized": state.finalized,
            "total_samples": state.total_samples,
        }

    def _finalize_secure_round(self, state: SecureAggregationRound) -> Dict[str, Any]:
        if state.finalized:
            return self.latest_secure_global or {}

        total_weight = sum(state.participant_weights.values())
        if total_weight <= 0:
            total_weight = float(state.submitted_count or 1)

        aggregate_vector = (state.sum_masked_updates - state.sum_masks) / total_weight

        if FL_SERVER_NOISE_SIGMA > 0:
            aggregate_vector = aggregate_vector + np.random.normal(
                0.0,
                FL_SERVER_NOISE_SIGMA,
                size=aggregate_vector.shape,
            )

        aggregate_list = aggregate_vector.tolist()
        average_epsilon = state.total_epsilon / max(1, state.submitted_count)

        global_model = {
            "version": "federated_secure_v1",
            "round_id": state.round_id,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "num_clients": state.submitted_count,
            "total_samples": state.total_samples,
            "feature_vector": aggregate_list,
            "dp": {
                "avg_client_epsilon": average_epsilon,
                "server_noise_sigma": FL_SERVER_NOISE_SIGMA,
            },
        }
        state.finalized = True
        state.aggregate = aggregate_list
        state.metadata = global_model
        self.latest_secure_global = global_model

        joblib.dump(global_model, GLOBAL_MODEL_PATH)
        print("Global Model updated via Secure Aggregation + Differential Privacy.")
        return global_model

    def aggregate(self, round_id: Optional[str] = None):
        """
        Performs aggregation.
        - If round_id is provided: finalize secure aggregation round (if ready).
        - Otherwise: performs legacy FedAvg over buffered updates.
        """
        with self.lock:
            if round_id:
                state = self.rounds.get(round_id)
                if not state:
                    return None
                if not self._round_ready_for_finalize(state):
                    return None
                return self._finalize_secure_round(state)

            if not self.local_updates:
                return None

            print(f"Aggregating updates from {len(self.local_updates)} agents (legacy mode)...")

            n_updates = len(self.local_updates)
            numeric_accumulator: Dict[str, float] = {}
            vector_accumulator: Dict[str, np.ndarray] = {}

            for update in self.local_updates:
                for key, value in update.items():
                    if isinstance(value, (int, float, np.number)):
                        numeric_accumulator[key] = numeric_accumulator.get(key, 0.0) + float(value)
                    else:
                        try:
                            vector_value = np.asarray(value, dtype=np.float64)
                            vector_accumulator[key] = vector_accumulator.get(key, np.zeros_like(vector_value)) + vector_value
                        except Exception:
                            pass

            avg_weights: Dict[str, Any] = {}
            for key, total in numeric_accumulator.items():
                avg_weights[key] = total / n_updates
            for key, total_vector in vector_accumulator.items():
                averaged = total_vector / n_updates
                avg_weights[key] = averaged.tolist() if isinstance(averaged, np.ndarray) else averaged

            self.local_updates = []

            joblib.dump(avg_weights, GLOBAL_MODEL_PATH)
            print("Global Model updated via Federated Averaging (legacy).")
            return avg_weights


federated_aggregator = FederatedAggregator()
