
# Enhanced Machine Learning Module

This module provides a robust, modular framework for anomaly detection and risk prediction in the Sentinel AI Monitoring System.

## Architecture

The ML pipeline consists of the following components:

1.  **Data Pipeline (`pipeline.py`)**:
    -   **Data Loading**: Fetches logs from the database.
    -   **Preprocessing**: 
        -   Temporal features (Hour of day, Day of week).
        -   Categorical encoding (User, Activity Type).
        -   Feature Scaling (StandardScaler).
    -   **Artifact Management**: Saves/loads encoders and scalers for consistent inference.

2.  **Model Registry (`models.py`)**:
    -   **BaseModel**: Abstract base class for uniform API.
    -   **IsolationForestModel**: Unsupervised anomaly detection using Scikit-Learn.
    -   **XGBoostRiskModel**: Supervised classification for Risk Level prediction using XGBoost.
    -   **AutoEncoderModel**: Deep Learning-based anomaly detection using PyTorch (reconstruction error).

3.  **Training & Evaluation (`trainer.py`, `evaluator.py`)**:
    -   **ModelTrainer**: Orchestrates the training of all models.
    -   **ModelEvaluator**: Generates detailed metrics (Accuracy, Precision, Recall, F1, ROC-AUC) and confusion matrices.

## Supported Models

| Model | Type | Use Case | Framework |
| :--- | :--- | :--- | :--- |
| **Isolation Forest** | Unsupervised | Outlier detection in logs | Scikit-Learn |
| **XGBoost Classifier** | Supervised | Predicting high-risk events | XGBoost |
| **AutoEncoder** | Unsupervised (DL) | Complex anomaly patterns | PyTorch |

## Usage

### Training

Training is triggered via the API endpoint `/ml/train`.

```python
from backend.ml.trainer import ModelTrainer
# db is a SQLAlchemy Session
trainer = ModelTrainer(db)
trainer.train_all()
```

### Inference

```python
from backend.ml_engine import predict_anomaly

log = {
    "timestamp": "2023-10-27T10:00:00",
    "user": "alice",
    "activity_type": "LOGIN",
    "risk_level": "INFO"
}

is_anomaly = predict_anomaly(log) # Returns -1 (Anomaly) or 1 (Normal)
```

## Directory Structure

-   `pipeline.py`: Data ingestion and transformation.
-   `models.py`: Model wrappers.
-   `trainer.py`: Training logic.
-   `evaluator.py`: Metrics and reporting.
-   `ml_artifacts/`: Stores trained models (.pkl, .pth) and preprocessors.
