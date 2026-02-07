
from sqlalchemy.orm import Session
import os
from .pipeline import DataPipeline
from .models import IsolationForestModel, AutoEncoderModel, XGBoostRiskModel
from .evaluator import ModelEvaluator
import numpy as np
from sklearn.model_selection import train_test_split

class ModelTrainer:
    def __init__(
        self,
        db: Session,
        data_limit=50000,
        validation_split=0.2,
        random_state=42,
        autoencoder_epochs=80,
        autoencoder_batch_size=64,
    ):
        self.db = db
        self.pipeline = DataPipeline(data_limit=data_limit)
        self.validation_split = max(0.1, min(validation_split, 0.4))
        self.random_state = random_state
        self.autoencoder_epochs = int(autoencoder_epochs)
        self.autoencoder_batch_size = int(autoencoder_batch_size)

        contamination = float(os.getenv("ML_IFOREST_CONTAMINATION", "0.05"))
        if contamination <= 0 or contamination >= 0.5:
            contamination = 0.05

        self.models = {
            "isolation_forest": IsolationForestModel(
                n_estimators=int(os.getenv("ML_IFOREST_ESTIMATORS", "300")),
                contamination=contamination,
            ),
            "autoencoder": AutoEncoderModel(
                learning_rate=float(os.getenv("ML_AE_LR", "0.001")),
            ),
            "xgboost": XGBoostRiskModel()
        }
        self.evaluator = ModelEvaluator()

    def train_all(self):
        """Train all configured models and generate visualizations."""
        # 1. Load Data
        print("Loading data...")
        df = self.pipeline.load_data(self.db)
        if df.empty:
            print("No data found. Skipping training.")
            return

        # 2. Preprocess
        print("Preprocessing data...")
        X = self.pipeline.preprocess(df, training=True)
        self.pipeline.save_artifacts()

        # Prepare targets for supervised
        risk_map = {"LOW": 0, "INFO": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3, "unknown": 0}
        y = df['risk_level'].map(lambda x: risk_map.get(x, 0))

        # Split for validation (simple 80/20)
        X_train, X_val, y_train, y_val = train_test_split(
            X,
            y,
            test_size=self.validation_split,
            random_state=self.random_state,
            stratify=y if len(set(y.tolist())) > 1 else None,
        )

        # 3. Train Unsupervised Models
        print("Training Unsupervised Models...")
        
        # Isolation Forest
        self.models["isolation_forest"].train(X_train) 
        self.models["isolation_forest"].save()
        
        # Evaluate IF
        if_preds = self.models["isolation_forest"].predict(X_val)
        if_y_true = y_val.apply(lambda x: -1 if x >= 2 else 1) # HIGH/CRITICAL are anomalies
        
        self.evaluator.generate_report(if_y_true, if_preds, "isolation_forest")
        self.evaluator.plot_confusion_matrix(if_y_true, if_preds, "isolation_forest")
        self.evaluator.plot_feature_importance(self.models["isolation_forest"].model, self.pipeline.feature_columns, "isolation_forest")
        
        # AutoEncoder
        history = self.models["autoencoder"].train(
            X_train,
            epochs=self.autoencoder_epochs,
            batch_size=self.autoencoder_batch_size,
        )
        self.models["autoencoder"].save()
        self.evaluator.plot_training_curves(history, "autoencoder")
        
        # Eval AE
        ae_preds = self.models["autoencoder"].predict(X_val)
        self.evaluator.generate_report(if_y_true, ae_preds, "autoencoder")
        self.evaluator.plot_confusion_matrix(if_y_true, ae_preds, "autoencoder")
        
        # Advanced AE Visualization
        try:
            # Latent Space
            latent = self.models["autoencoder"].get_latent(X_val)
            self.evaluator.plot_latent_space(latent, if_y_true, "autoencoder", method='pca')
            self.evaluator.plot_latent_space(latent, if_y_true, "autoencoder", method='tsne')
            
            # Reconstruction Error Density
            errors = self.models["autoencoder"].get_reconstruction_error(X_val)
            # Map labels to 0/1 for the plot function
            labels_01 = np.where(if_y_true == 1, 0, 1) # 1=Normal->0, -1=Anomaly->1
            self.evaluator.plot_reconstruction_error_distribution(errors, labels_01, "autoencoder")
        except Exception as e:
            print(f"Error generating advanced AE plots: {e}")

        # 4. Train Supervised Model (XGBoost)
        print("Training Supervised Models...")
        
        self.models["xgboost"].train(X_train, y_train)
        self.models["xgboost"].save()
        
        # Eval XGBoost
        xgb_preds = self.models["xgboost"].predict(X_val)
        xgb_probs = self.models["xgboost"].predict_proba(X_val)
        
        self.evaluator.generate_report(y_val, xgb_preds, "xgboost", probabilities=xgb_probs)
        self.evaluator.plot_confusion_matrix(y_val, xgb_preds, "xgboost")
        self.evaluator.plot_feature_importance(self.models["xgboost"].model, self.pipeline.feature_columns, "xgboost")
        self.evaluator.plot_roc_curve(y_val, xgb_probs, "xgboost")
        self.evaluator.plot_pr_curve(y_val, xgb_probs, "xgboost")
        self.evaluator.plot_calibration_curve(y_val, xgb_probs, "xgboost")

        # 5. Generate Dashboard
        print("Generating Dashboard...")
        self.evaluator.create_dashboard(["isolation_forest", "autoencoder", "xgboost"])
        print("Training and Evaluation Complete.")

    def evaluate(self):
        """Legacy evaluate method."""
        pass
