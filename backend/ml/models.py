
import os
import joblib
import numpy as np
import json
from abc import ABC, abstractmethod
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import classification_report, precision_recall_fscore_support, roc_auc_score
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except Exception as e:
    XGBOOST_AVAILABLE = False
    XGBOOST_IMPORT_ERROR = str(e)
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

if not globals().get("XGBOOST_AVAILABLE", False):
    XGBOOST_IMPORT_ERROR = globals().get("XGBOOST_IMPORT_ERROR", "not installed")

class BaseModel(ABC):
    def __init__(self, model_path="ml_artifacts"):
        self.model_path = model_path
        if not os.path.exists(model_path):
            os.makedirs(model_path)
        self.model = None
        self.model_name = "base_model"

    @abstractmethod
    def train(self, X, y=None):
        pass

    @abstractmethod
    def predict(self, X):
        pass

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def get_latent(self, X):
        """
        Get latent representation for visualization.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            latent = self.model.encoder(X_tensor)
        return latent.cpu().numpy()

    def get_reconstruction_error(self, X):
        """
        Get raw reconstruction error.
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
        return mse.cpu().numpy()

    def save(self):
        path = os.path.join(self.model_path, f"{self.model_name}.pkl")
        joblib.dump(self.model, path)
        print(f"Model saved to {path}")

    def load(self):
        path = os.path.join(self.model_path, f"{self.model_name}.pkl")
        if os.path.exists(path):
            self.model = joblib.load(path)
            print(f"Model loaded from {path}")
            return True
        return False

class IsolationForestModel(BaseModel):
    def __init__(
        self,
        model_path="ml_artifacts",
        n_estimators=300,
        contamination=0.05,
        max_samples="auto",
        random_state=42,
    ):
        super().__init__(model_path)
        self.model_name = "isolation_forest"
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            max_samples=max_samples,
            random_state=random_state,
        )

    def train(self, X, y=None):
        print("Training Isolation Forest...")
        self.model.fit(X)

    def predict(self, X):
        # Returns -1 for anomaly, 1 for normal
        return self.model.predict(X)

    def predict_score(self, X):
        # Returns anomaly score (lower is more anomalous)
        return self.model.decision_function(X)

class XGBoostRiskModel(BaseModel):
    def __init__(
        self,
        model_path="ml_artifacts",
        n_estimators=300,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.9,
        colsample_bytree=0.9,
    ):
        super().__init__(model_path)
        self.model_name = "xgboost_risk"
        if XGBOOST_AVAILABLE:
            self.model = xgb.XGBClassifier(
                objective='multi:softprob', 
                n_estimators=n_estimators,
                learning_rate=learning_rate,
                max_depth=max_depth,
                subsample=subsample,
                colsample_bytree=colsample_bytree,
                eval_metric='mlogloss',
                random_state=42,
            )
        else:
            self.model = None

    def train(self, X, y):
        if not self.model:
            if os.getenv("SENTINEL_TESTING") != "1":
                print(f"XGBoost not available ({XGBOOST_IMPORT_ERROR}). Skipping training.")
            return
        print("Training XGBoost Classifier...")
        # Ensure y is encoded 0..N
        self.model.fit(X, y)

    def predict(self, X):
        if not self.model:
            return np.zeros(len(X))
        return self.model.predict(X)
    
    def predict_proba(self, X):
        if not self.model:
            return np.zeros((len(X), 1))
        return self.model.predict_proba(X)

# --- Deep Learning: AutoEncoder for Anomaly Detection ---

class AutoEncoder(nn.Module):
    def __init__(self, input_dim):
        super(AutoEncoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 4),  # Latent space
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

class AutoEncoderModel(BaseModel):
    def __init__(self, model_path="ml_artifacts", input_dim=10, learning_rate=0.001):
        super().__init__(model_path)
        self.model_name = "autoencoder_torch"
        self.input_dim = input_dim
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AutoEncoder(input_dim).to(self.device)
        self.criterion = nn.MSELoss()
        self.learning_rate = learning_rate
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.threshold = 0.1 # To be determined after training

    def train(self, X, y=None, epochs=20, batch_size=32):
        print(f"Training AutoEncoder on {self.device}...")
        self.input_dim = X.shape[1]
        # Re-init model if dim changed (simple handling)
        if self.model.encoder[0].in_features != self.input_dim:
             self.model = AutoEncoder(self.input_dim).to(self.device)
             self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)

        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        dataset = TensorDataset(X_tensor)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        history = {'loss': []}

        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            for batch in dataloader:
                inputs = batch[0]
                self.optimizer.zero_grad()
                outputs = self.model(inputs)
                loss = self.criterion(outputs, inputs)
                loss.backward()
                self.optimizer.step()
                total_loss += loss.item()
            
            avg_loss = total_loss / len(dataloader)
            history['loss'].append(avg_loss)
            
            if (epoch + 1) % 5 == 0:
                print(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.4f}")

        # Determine threshold (e.g., 95th percentile of reconstruction error on training data)
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
            self.threshold = np.percentile(mse.cpu().numpy(), 95)
            print(f"AutoEncoder Threshold set to: {self.threshold}")
            
        return history

    def predict(self, X):
        """
        Returns -1 for anomaly (High MSE), 1 for normal (Low MSE)
        """
        self.model.eval()
        X_tensor = torch.tensor(X.values, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            mse = torch.mean((outputs - X_tensor) ** 2, dim=1)
            mse_np = mse.cpu().numpy()
            
        # If error > threshold, it's an anomaly (-1)
        predictions = np.where(mse_np > self.threshold, -1, 1)
        return predictions

    def save(self):
        path = os.path.join(self.model_path, f"{self.model_name}.pth")
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'threshold': self.threshold,
            'input_dim': self.input_dim
        }, path)
        print(f"PyTorch Model saved to {path}")

    def load(self):
        path = os.path.join(self.model_path, f"{self.model_name}.pth")
        if os.path.exists(path):
            # weights_only=False required because we save numpy scalars (threshold) in the dict
            checkpoint = torch.load(path, map_location=self.device, weights_only=False)
            self.input_dim = checkpoint['input_dim']
            self.model = AutoEncoder(self.input_dim).to(self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.threshold = checkpoint['threshold']
            print(f"PyTorch Model loaded from {path}")
            return True
        return False
