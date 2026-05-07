"""
SHAP Explainability Module for Anomaly Detection
Provides human-readable explanations for model predictions
Part of Antigena-inspired Self-Learning AI Defense System
"""

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import IsolationForest
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import logging
from typing import Dict, Any, List, Tuple, Optional
import matplotlib.pyplot as plt
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SHAPExplainer:
    """SHAP-based explainer for anomaly detection models"""
    
    def __init__(self, model_type: str = "isolation_forest", background_samples: int = 100):
        """
        Initialize SHAP explainer
        
        Args:
            model_type: Type of model to explain
            background_samples: Number of background samples for SHAP
        """
        self.model_type = model_type
        self.background_samples = background_samples
        self.explainer = None
        self.background_data = None
        self.feature_names = None
        self.surrogate_model = None
        
    def fit_explainer(self, model, X_train: np.ndarray, feature_names: List[str] = None) -> None:
        """
        Fit SHAP explainer with trained model and background data
        
        Args:
            model: Trained anomaly detection model
            X_train: Training data for background
            feature_names: List of feature names
        """
        logger.info(f"Fitting SHAP explainer for {self.model_type}...")
        
        # Store feature names
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X_train.shape[1])]
        
        # Sample background data
        if len(X_train) > self.background_samples:
            indices = np.random.choice(len(X_train), self.background_samples, replace=False)
            self.background_data = X_train[indices]
        else:
            self.background_data = X_train
        
        # Create explainer based on model type
        if self.model_type == "isolation_forest":
            self._fit_isolation_forest_explainer(model)
        elif self.model_type == "surrogate":
            self._fit_surrogate_explainer(model, X_train)
        else:
            # Use KernelExplainer as fallback
            self.explainer = shap.KernelExplainer(
                self._model_predict, 
                self.background_data
            )
        
        logger.info("SHAP explainer fitted successfully")
    
    def _fit_isolation_forest_explainer(self, model) -> None:
        """Fit explainer for Isolation Forest model"""
        # Use TreeExplainer for tree-based models
        try:
            self.explainer = shap.TreeExplainer(model.model)
        except:
            # Fallback to KernelExplainer
            self.explainer = shap.KernelExplainer(
                lambda x: model.model.predict_proba(x)[:, 1],
                self.background_data
            )
    
    def _fit_surrogate_explainer(self, model, X_train: np.ndarray) -> None:
        """
        Fit surrogate model for black-box models
        Uses RandomForest as surrogate for explainability
        """
        logger.info("Creating surrogate model for explanation...")
        
        # Get anomaly scores from original model
        anomaly_scores = model.decision_function(X_train)
        
        # Create binary labels based on threshold
        threshold = np.percentile(anomaly_scores, 95)  # 5% anomaly rate
        y_train = (anomaly_scores > threshold).astype(int)
        
        # Train surrogate RandomForest
        self.surrogate_model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )
        self.surrogate_model.fit(X_train, y_train)
        
        # Create SHAP explainer for surrogate model
        self.explainer = shap.TreeExplainer(self.surrogate_model)
    
    def _model_predict(self, X: np.ndarray) -> np.ndarray:
        """Model prediction function for SHAP KernelExplainer"""
        # This should be overridden based on the specific model
        return np.zeros(len(X))
    
    def explain_sample(self, sample: np.ndarray, top_k: int = 5) -> Dict[str, Any]:
        """
        Explain a single sample
        
        Args:
            sample: Input sample to explain
            top_k: Number of top features to return
            
        Returns:
            Dictionary with feature importance and explanations
        """
        if self.explainer is None:
            raise ValueError("Explainer not fitted. Call fit_explainer() first.")
        
        # Ensure sample is 2D
        if sample.ndim == 1:
            sample = sample.reshape(1, -1)
        
        # Calculate SHAP values
        shap_values = self.explainer.shap_values(sample)
        
        # Handle different SHAP value formats
        if isinstance(shap_values, list):
            # For multi-class models
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        
        # Get feature importance
        if shap_values.ndim == 2:
            feature_importance = shap_values[0]  # First sample
        else:
            feature_importance = shap_values
        
        # Get top features
        top_indices = np.argsort(np.abs(feature_importance))[-top_k:][::-1]
        
        top_features = []
        for idx in top_indices:
            feature_name = self.feature_names[idx]
            importance = feature_importance[idx]
            direction = "increases" if importance > 0 else "decreases"
            
            top_features.append({
                'feature': feature_name,
                'importance': float(importance),
                'direction': direction,
                'value': float(sample[0, idx])
            })
        
        # Generate human-readable explanation
        explanation = self._generate_explanation(top_features, sample[0])
        
        return {
            'shap_values': feature_importance.tolist(),
            'top_features': top_features,
            'explanation': explanation,
            'feature_names': self.feature_names
        }
    
    def explain_batch(self, samples: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Explain multiple samples
        
        Args:
            samples: Input samples to explain
            top_k: Number of top features to return
            
        Returns:
            List of explanations for each sample
        """
        explanations = []
        
        for i, sample in enumerate(samples):
            try:
                explanation = self.explain_sample(sample, top_k)
                explanation['sample_index'] = i
                explanations.append(explanation)
            except Exception as e:
                logger.warning(f"Failed to explain sample {i}: {e}")
                continue
        
        return explanations
    
    def _generate_explanation(self, top_features: List[Dict], sample_values: np.ndarray) -> str:
        """
        Generate human-readable explanation
        
        Args:
            top_features: Top contributing features
            sample_values: Sample feature values
            
        Returns:
            Human-readable explanation string
        """
        if not top_features:
            return "No significant features contributing to the prediction."
        
        explanation_parts = []
        
        for feature in top_features[:3]:  # Top 3 features
            feature_name = feature['feature']
            importance = abs(feature['importance'])
            direction = feature['direction']
            value = feature['value']
            
            if importance > 0.1:
                explanation_parts.append(
                    f"{feature_name} (value: {value:.3f}) {direction} anomaly risk by {importance:.3f}"
                )
        
        if explanation_parts:
            explanation = "Key factors: " + "; ".join(explanation_parts)
        else:
            explanation = "Multiple features contribute slightly to the anomaly detection."
        
        return explanation
    
    def plot_explanation(self, sample: np.ndarray, save_path: str = None) -> None:
        """
        Create SHAP plot for sample explanation
        
        Args:
            sample: Input sample to explain
            save_path: Path to save the plot
        """
        if self.explainer is None:
            raise ValueError("Explainer not fitted. Call fit_explainer() first.")
        
        # Ensure sample is 2D
        if sample.ndim == 1:
            sample = sample.reshape(1, -1)
        
        # Calculate SHAP values
        shap_values = self.explainer.shap_values(sample)
        
        # Handle different SHAP value formats
        if isinstance(shap_values, list):
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        
        # Create plot
        plt.figure(figsize=(10, 6))
        shap.force_plot(
            self.explainer.expected_value,
            shap_values[0],
            sample[0],
            feature_names=self.feature_names,
            matplotlib=True,
            show=False
        )
        
        plt.title("SHAP Explanation for Anomaly Detection")
        plt.tight_layout()
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Explanation plot saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def get_global_feature_importance(self, X: np.ndarray, top_k: int = 10) -> Dict[str, float]:
        """
        Get global feature importance across multiple samples
        
        Args:
            X: Input samples
            top_k: Number of top features to return
            
        Returns:
            Dictionary of global feature importance
        """
        if self.explainer is None:
            raise ValueError("Explainer not fitted. Call fit_explainer() first.")
        
        # Calculate SHAP values for all samples
        shap_values = self.explainer.shap_values(X)
        
        # Handle different SHAP value formats
        if isinstance(shap_values, list):
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        
        # Calculate mean absolute SHAP values
        mean_importance = np.mean(np.abs(shap_values), axis=0)
        
        # Get top features
        top_indices = np.argsort(mean_importance)[-top_k:][::-1]
        
        global_importance = {}
        for idx in top_indices:
            feature_name = self.feature_names[idx]
            importance = mean_importance[idx]
            global_importance[feature_name] = float(importance)
        
        return global_importance
    
    def save_explainer(self, path: str) -> None:
        """Save the explainer to disk"""
        if self.explainer is None:
            raise ValueError("No explainer to save")
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save explainer and metadata
        explainer_data = {
            'explainer': self.explainer,
            'background_data': self.background_data,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'surrogate_model': self.surrogate_model
        }
        
        import joblib
        joblib.dump(explainer_data, path)
        logger.info(f"Explainer saved to {path}")
    
    def load_explainer(self, path: str) -> None:
        """Load explainer from disk"""
        try:
            import joblib
            explainer_data = joblib.load(path)
            
            self.explainer = explainer_data['explainer']
            self.background_data = explainer_data['background_data']
            self.feature_names = explainer_data['feature_names']
            self.model_type = explainer_data['model_type']
            self.surrogate_model = explainer_data.get('surrogate_model')
            
            logger.info(f"Explainer loaded from {path}")
        except FileNotFoundError:
            logger.error(f"Explainer file not found at {path}")
            raise

# Example usage and testing
if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    
    # Normal data
    normal_data = np.random.randn(1000, 10)
    
    # Anomalous data
    anomaly_data = np.random.randn(50, 10) * 3 + 5
    
    # Combine data
    X = np.vstack([normal_data, anomaly_data])
    
    # Feature names
    feature_names = [
        'bytes_sent', 'bytes_received', 'duration', 'packet_count',
        'src_port', 'dst_port', 'protocol_type', 'connection_count',
        'error_rate', 'response_time'
    ]
    
    # Train a simple Isolation Forest for testing
    from sklearn.ensemble import IsolationForest
    
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(normal_data)
    
    # Create and fit explainer
    explainer = SHAPExplainer(model_type="isolation_forest")
    explainer.fit_explainer(model, normal_data, feature_names)
    
    # Explain a sample
    sample_to_explain = anomaly_data[0]
    explanation = explainer.explain_sample(sample_to_explain, top_k=5)
    
    print("Sample Explanation:")
    print(f"Explanation: {explanation['explanation']}")
    print("\nTop Features:")
    for feature in explanation['top_features']:
        print(f"  {feature['feature']}: {feature['importance']:.3f} ({feature['direction']})")
    
    # Get global feature importance
    global_importance = explainer.get_global_feature_importance(X[:100], top_k=5)
    print("\nGlobal Feature Importance:")
    for feature, importance in global_importance.items():
        print(f"  {feature}: {importance:.3f}")
    
    # Save explainer
    explainer.save_explainer("models/shap_explainer.pkl")
    
    print("SHAP explainer test completed successfully!")
