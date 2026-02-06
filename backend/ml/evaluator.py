
import json
import os
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, f1_score, precision_score, recall_score, accuracy_score, roc_curve, precision_recall_curve, auc
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA

# Set academic style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 18
})

class ModelEvaluator:
    def __init__(self, artifact_dir="ml_artifacts"):
        self.artifact_dir = artifact_dir
        if not os.path.exists(artifact_dir):
            os.makedirs(artifact_dir)

    def generate_report(self, y_true, y_pred, model_name, probabilities=None):
        """
        Generate a comprehensive evaluation report.
        """
        report = {}
        
        # Basic Metrics
        report['accuracy'] = float(accuracy_score(y_true, y_pred))
        report['precision'] = float(precision_score(y_true, y_pred, average='weighted', zero_division=0))
        report['recall'] = float(recall_score(y_true, y_pred, average='weighted', zero_division=0))
        report['f1_score'] = float(f1_score(y_true, y_pred, average='weighted', zero_division=0))
        
        # Classification Report
        report['classification_report'] = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        
        # Confusion Matrix
        cm = confusion_matrix(y_true, y_pred)
        report['confusion_matrix'] = cm.tolist()
        
        # ROC-AUC (if probabilities provided and binary/multiclass)
        if probabilities is not None:
            try:
                # Handle multiclass ROC AUC
                n_classes = probabilities.shape[1]
                if n_classes == 2:
                    report['roc_auc'] = float(roc_auc_score(y_true, probabilities[:, 1]))
                else:
                    report['roc_auc'] = float(roc_auc_score(y_true, probabilities, multi_class='ovr'))
            except Exception as e:
                report['roc_auc_error'] = str(e)

        # Save report
        report_path = os.path.join(self.artifact_dir, f"{model_name}_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=4)
            
        print(f"Report saved to {report_path}")
        return report

    def plot_confusion_matrix(self, y_true, y_pred, model_name):
        cm = confusion_matrix(y_true, y_pred)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
        plt.title(f'Confusion Matrix - {model_name}')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        
        plot_path = os.path.join(self.artifact_dir, f"{model_name}_cm.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Confusion Matrix plot saved to {plot_path}")

    def plot_training_curves(self, history, model_name):
        """
        Plot training loss/accuracy curves.
        history: dict containing 'loss', 'accuracy', 'val_loss', etc.
        """
        if not history or 'loss' not in history:
            return

        plt.figure(figsize=(10, 6))
        plt.plot(history['loss'], label='Training Loss', linewidth=2)
        if 'val_loss' in history:
            plt.plot(history['val_loss'], label='Validation Loss', linewidth=2, linestyle='--')
        
        plt.title(f'Learning Curve - {model_name}')
        plt.xlabel('Epochs')
        plt.ylabel('Loss')
        plt.legend()
        plt.tight_layout()
        
        plot_path = os.path.join(self.artifact_dir, f"{model_name}_loss_curve.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Loss curve saved to {plot_path}")

    def plot_roc_curve(self, y_true, probabilities, model_name):
        """
        Plot ROC Curve. Supports binary and multiclass (via macro-average).
        """
        if probabilities is None:
            return

        n_classes = probabilities.shape[1]
        
        plt.figure(figsize=(10, 8))
        
        # Binary Classification
        if n_classes == 2:
            fpr, tpr, _ = roc_curve(y_true, probabilities[:, 1])
            roc_auc = auc(fpr, tpr)
            plt.plot(fpr, tpr, lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
        else:
            # Multiclass
            from sklearn.preprocessing import label_binarize
            classes = sorted(list(set(y_true)))
            y_bin = label_binarize(y_true, classes=classes)
            
            for i in range(n_classes):
                if i < len(classes):
                    fpr, tpr, _ = roc_curve(y_bin[:, i], probabilities[:, i])
                    roc_auc = auc(fpr, tpr)
                    plt.plot(fpr, tpr, lw=2, label=f'Class {classes[i]} (AUC = {roc_auc:.2f})')
        
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'Receiver Operating Characteristic - {model_name}')
        plt.legend(loc="lower right")
        plt.tight_layout()
        
        plot_path = os.path.join(self.artifact_dir, f"{model_name}_roc_curve.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()

    def plot_pr_curve(self, y_true, probabilities, model_name):
        """
        Plot Precision-Recall Curve.
        """
        if probabilities is None:
            return

        n_classes = probabilities.shape[1]
        plt.figure(figsize=(10, 8))
        
        if n_classes == 2:
            precision, recall, _ = precision_recall_curve(y_true, probabilities[:, 1])
            pr_auc = auc(recall, precision)
            plt.plot(recall, precision, lw=2, label=f'PR curve (AUC = {pr_auc:.2f})')
        else:
            pass

        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title(f'Precision-Recall Curve - {model_name}')
        plt.legend(loc="lower left")
        plt.tight_layout()
        
        plot_path = os.path.join(self.artifact_dir, f"{model_name}_pr_curve.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()

    def plot_feature_importance(self, model, feature_names, model_name):
        """
        Plot feature importance for tree-based models.
        """
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            indices = np.argsort(importances)[::-1]
            
            plt.figure(figsize=(12, 6))
            plt.title(f"Feature Importance - {model_name}")
            plt.bar(range(len(importances)), importances[indices], align="center")
            plt.xticks(range(len(importances)), [feature_names[i] for i in indices], rotation=45, ha='right')
            plt.ylabel("Importance Score")
            plt.tight_layout()
            
            plot_path = os.path.join(self.artifact_dir, f"{model_name}_feature_importance.png")
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()

    def plot_latent_space(self, latent_vectors, labels, model_name, method='pca'):
        """
        Visualize latent space using PCA or t-SNE.
        latent_vectors: numpy array (N, latent_dim)
        labels: array of class labels (for coloring)
        """
        plt.figure(figsize=(10, 8))
        
        if method == 'tsne':
            reducer = TSNE(n_components=2, random_state=42)
            title = f"t-SNE Projection of Latent Space - {model_name}"
        else:
            reducer = PCA(n_components=2, random_state=42)
            title = f"PCA Projection of Latent Space - {model_name}"
            
        embedding = reducer.fit_transform(latent_vectors)
        
        scatter = plt.scatter(embedding[:, 0], embedding[:, 1], c=labels, cmap='viridis', alpha=0.6, s=50)
        plt.colorbar(scatter, label='Class/Risk Level')
        plt.title(title)
        plt.xlabel(f"{method.upper()} Component 1")
        plt.ylabel(f"{method.upper()} Component 2")
        plt.tight_layout()
        
        plot_path = os.path.join(self.artifact_dir, f"{model_name}_latent_space_{method}.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Latent space plot saved to {plot_path}")

    def plot_reconstruction_error_distribution(self, errors, labels, model_name):
        """
        Plot KDE of reconstruction errors separated by class.
        errors: array of MSE values
        labels: binary labels (0=Normal, 1=Anomaly)
        """
        plt.figure(figsize=(10, 6))
        
        sns.kdeplot(errors[labels==0], shade=True, label='Normal', color='blue')
        sns.kdeplot(errors[labels==1], shade=True, label='Anomaly', color='red')
        
        plt.title(f"Reconstruction Error Distribution - {model_name}")
        plt.xlabel("Mean Squared Error (MSE)")
        plt.ylabel("Density")
        plt.legend()
        plt.tight_layout()
        
        plot_path = os.path.join(self.artifact_dir, f"{model_name}_error_dist.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Error distribution plot saved to {plot_path}")

    def plot_calibration_curve(self, y_true, probabilities, model_name):
        """
        Plot reliability diagram (Calibration curve).
        """
        plt.figure(figsize=(8, 8))
        
        # Check if binary
        n_classes = probabilities.shape[1]
        if n_classes == 2:
            prob_pos = probabilities[:, 1]
            fraction_of_positives, mean_predicted_value = calibration_curve(y_true, prob_pos, n_bins=10)
            
            plt.plot(mean_predicted_value, fraction_of_positives, "s-", label=f"{model_name}")
            plt.plot([0, 1], [0, 1], "k--", label="Perfectly calibrated")
            
            plt.ylabel("Fraction of positives")
            plt.xlabel("Mean predicted value")
            plt.title(f"Calibration Curve - {model_name}")
            plt.legend()
            plt.tight_layout()
            
            plot_path = os.path.join(self.artifact_dir, f"{model_name}_calibration.png")
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Calibration curve saved to {plot_path}")

    def create_dashboard(self, model_names):
        """
        Create a simple HTML dashboard to view the artifacts.
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PhD Model Analysis Dashboard</title>
            <style>
                body {{ font-family: 'Times New Roman', serif; margin: 40px; background-color: #f9f9f9; color: #333; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                h1, h2 {{ color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }}
                .model-section {{ margin-bottom: 60px; }}
                .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; }}
                .figure-card {{ background: white; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }}
                img {{ max-width: 100%; height: auto; display: block; }}
                .caption {{ font-style: italic; margin-top: 10px; font-size: 0.9em; color: #666; text-align: center; }}
                .metrics {{ background-color: #f8f9fa; padding: 20px; border-radius: 4px; margin-bottom: 20px; font-family: monospace; border-left: 4px solid #3498db; }}
                pre {{ margin: 0; white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Machine Learning Model Analysis</h1>
                <p>Generated on: {pd.Timestamp.now()}</p>
                <p>This dashboard presents a comprehensive evaluation of the machine learning models developed for the Sentinel AI Monitoring System. The visualizations are generated with publication-quality standards suitable for academic inclusion.</p>
        """
        
        for name in model_names:
            report_path = os.path.join(self.artifact_dir, f"{name}_report.json")
            metrics_html = "<p>No report found.</p>"
            if os.path.exists(report_path):
                with open(report_path, 'r') as f:
                    metrics = json.load(f)
                    key_metrics = {k: v for k, v in metrics.items() if k in ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']}
                    metrics_html = "<pre>" + json.dumps(key_metrics, indent=2) + "</pre>"

            html_content += f"""
                <div class="model-section">
                    <h2>{name.replace('_', ' ').title()}</h2>
                    <div class="metrics">
                        <h3>Performance Metrics</h3>
                        {metrics_html}
                    </div>
                    <div class="grid">
            """
            
            # Expanded list of images
            images = [
                (f"{name}_loss_curve.png", "Learning Curve: Training vs Validation Loss over Epochs."),
                (f"{name}_cm.png", "Confusion Matrix: Normalized prediction accuracy per class."),
                (f"{name}_roc_curve.png", "ROC Curve: Trade-off between True Positive Rate and False Positive Rate."),
                (f"{name}_pr_curve.png", "Precision-Recall Curve: Performance balance for imbalanced datasets."),
                (f"{name}_feature_importance.png", "Feature Importance: Relative contribution of features to model decisions."),
                (f"{name}_latent_space_pca.png", "PCA Projection: 2D visualization of the latent feature space."),
                (f"{name}_latent_space_tsne.png", "t-SNE Projection: Manifold learning visualization of cluster separation."),
                (f"{name}_error_dist.png", "Reconstruction Error Density: Distribution overlap between Normal and Anomalous samples."),
                (f"{name}_calibration.png", "Calibration Curve: Reliability of predicted probabilities.")
            ]
            
            for img, caption in images:
                if os.path.exists(os.path.join(self.artifact_dir, img)):
                    html_content += f"""
                        <div class="figure-card">
                            <img src="{img}" alt="{img}">
                            <div class="caption"><strong>Figure:</strong> {caption}</div>
                        </div>
                    """
            
            html_content += """
                    </div>
                </div>
            """
            
        html_content += """
            </div>
        </body>
        </html>
        """
        
        dashboard_path = os.path.join(self.artifact_dir, "dashboard.html")
        with open(dashboard_path, 'w') as f:
            f.write(html_content)
            
        print(f"Dashboard generated at {dashboard_path}")
