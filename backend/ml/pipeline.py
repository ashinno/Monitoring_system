
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import os
from datetime import datetime
import sys

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import models

class DataPipeline:
    def __init__(self, artifact_dir="ml_artifacts"):
        self.artifact_dir = artifact_dir
        if not os.path.exists(artifact_dir):
            os.makedirs(artifact_dir)
            
        self.scalers = {}
        self.encoders = {}
        self.feature_columns = []

    def load_data(self, db: Session, limit=10000):
        """Load logs from database into a pandas DataFrame."""
        query = db.query(models.Log).order_by(models.Log.timestamp.desc()).limit(limit)
        logs = query.all()
        
        if not logs:
            return pd.DataFrame()

        data = []
        for log in logs:
            data.append({
                "timestamp": log.timestamp,
                "user": log.user,
                "activity_type": log.activity_type,
                "risk_level": log.risk_level,
                "description": log.description
            })
            
        return pd.DataFrame(data)

    def preprocess(self, df: pd.DataFrame, training=True):
        """
        Preprocess log data for anomaly detection.
        Features: hour, day_of_week, user (encoded), activity_type (encoded)
        """
        if df.empty:
            return pd.DataFrame()

        df = df.copy()
        
        # Time features
        # Handle ISO format strings
        df['dt'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['dt'].dt.hour
        df['day_of_week'] = df['dt'].dt.dayofweek
        
        # Categorical features to encode
        cat_features = ['user', 'activity_type']
        
        for col in cat_features:
            if training:
                le = LabelEncoder()
                # Handle unknown values in future by using a comprehensive list or 'unknown' token strategy
                # For simplicity here, we fit on available data
                df[col] = df[col].fillna('unknown')
                df[f'{col}_encoded'] = le.fit_transform(df[col].astype(str))
                self.encoders[col] = le
            else:
                le = self.encoders.get(col)
                if le:
                    # Handle unseen labels by assigning a special value or mode
                    # This is a simple approach: map known, fill unknown with -1 (if model handles it) or 0
                    # Better: use a robust encoder. Here we use a safe map.
                    known_classes = set(le.classes_)
                    df[col] = df[col].fillna('unknown').astype(str)
                    df[f'{col}_encoded'] = df[col].apply(lambda x: le.transform([x])[0] if x in known_classes else 0)
                else:
                    df[f'{col}_encoded'] = 0

        # Numerical features to scale
        # We might want to scale hour/day if using distance-based models (SVM/KNN), 
        # but for Trees (RF/XGB) it's not strictly necessary. 
        # We'll scale them to be safe for all model types.
        num_features = ['hour', 'day_of_week']
        
        if training:
            scaler = StandardScaler()
            df[num_features] = scaler.fit_transform(df[num_features])
            self.scalers['time_features'] = scaler
        else:
            scaler = self.scalers.get('time_features')
            if scaler:
                df[num_features] = scaler.transform(df[num_features])

        # Select final features
        self.feature_columns = ['hour', 'day_of_week', 'user_encoded', 'activity_type_encoded']
        X = df[self.feature_columns]
        
        return X

    def save_artifacts(self):
        """Save encoders and scalers."""
        joblib.dump(self.encoders, os.path.join(self.artifact_dir, "encoders.pkl"))
        joblib.dump(self.scalers, os.path.join(self.artifact_dir, "scalers.pkl"))
        joblib.dump(self.feature_columns, os.path.join(self.artifact_dir, "features.pkl"))

    def load_artifacts(self):
        """Load encoders and scalers."""
        try:
            self.encoders = joblib.load(os.path.join(self.artifact_dir, "encoders.pkl"))
            self.scalers = joblib.load(os.path.join(self.artifact_dir, "scalers.pkl"))
            self.feature_columns = joblib.load(os.path.join(self.artifact_dir, "features.pkl"))
            return True
        except FileNotFoundError:
            return False
