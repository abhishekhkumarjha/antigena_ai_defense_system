"""
Isolation Forest Model for Anomaly Detection
Part of Antigena-inspired Self-Learning AI Defense System
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import logging
from typing import Tuple, Dict, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IsolationForestModel:
    """Isolation Forest model for anomaly detection"""
    
    def __init__(self, model_path: str = "models/isolation_forest.pkl"):
        self.model = None
        self.model_path = model_path
        self.contamination = 0.1  # Expected proportion of anomalies
        self.random_state = 42
        
    def train(self, X_train: np.ndarray, contamination: float = 0.1) -> None:
        """
        Train Isolation Forest on normal data
        
        Args:
            X_train: Training data (normal patterns)
            contamination: Expected proportion of anomalies
        """
        logger.info("Training Isolation Forest model...")
        
        self.contamination = contamination
        self.model = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination=contamination,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        # Fit the model
        self.model.fit(X_train)
        
        logger.info(f"Isolation Forest trained with contamination={contamination}")
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions on new data
        
        Args:
            X: Input data
            
        Returns:
            Tuple of (predictions, anomaly_scores)
            - predictions: 1 for normal, -1 for anomaly
            - anomaly_scores: Negative scores (more negative = more anomalous)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Get predictions
        predictions = self.model.predict(X)
        
        # Get anomaly scores (decision function)
        anomaly_scores = self.model.decision_function(X)
        
        return predictions, anomaly_scores
    
    def predict_iforest(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Main prediction function for ensemble integration
        
        Args:
            X: Input data
            
        Returns:
            Dictionary with predictions and scores
        """
        predictions, scores = self.predict(X)
        
        # Convert predictions to binary (0: normal, 1: anomaly)
        binary_predictions = np.where(predictions == -1, 1, 0)
        
        # Normalize scores to 0-1 range (higher = more anomalous)
        normalized_scores = self._normalize_scores(scores)
        
        return {
            'predictions': binary_predictions,
            'raw_scores': scores,
            'normalized_scores': normalized_scores,
            'method': 'isolation_forest'
        }
    
    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """
        Normalize anomaly scores to 0-1 range
        
        Args:
            scores: Raw anomaly scores (negative values)
            
        Returns:
            Normalized scores (0-1, higher = more anomalous)
        """
        # Since scores are negative, we invert and normalize
        min_score = np.min(scores)
        max_score = np.max(scores)
        
        if max_score == min_score:
            return np.zeros_like(scores)
        
        # Invert scores (make higher values more anomalous) and normalize to 0-1
        normalized = (max_score - scores) / (max_score - min_score)
        return normalized
    
    def evaluate(self, X_test: np.ndarray, y_true: np.ndarray = None) -> Dict[str, Any]:
        """
        Evaluate model performance
        
        Args:
            X_test: Test data
            y_true: True labels (optional)
            
        Returns:
            Evaluation metrics
        """
        predictions, scores = self.predict(X_test)
        
        # Convert to binary (0: normal, 1: anomaly)
        binary_predictions = np.where(predictions == -1, 1, 0)
        
        metrics = {
            'predictions': binary_predictions,
            'anomaly_scores': scores,
            'anomaly_rate': np.mean(binary_predictions),
            'avg_score': np.mean(scores),
            'score_std': np.std(scores)
        }
        
        # Add classification metrics if true labels available
        if y_true is not None:
            metrics['classification_report'] = classification_report(y_true, binary_predictions)
            metrics['confusion_matrix'] = confusion_matrix(y_true, binary_predictions)
        
        return metrics
    
    def save_model(self) -> None:
        """Save the trained model to disk"""
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        logger.info(f"Model saved to {self.model_path}")
    
    def load_model(self) -> None:
        """Load a trained model from disk"""
        try:
            self.model = joblib.load(self.model_path)
            logger.info(f"Model loaded from {self.model_path}")
        except FileNotFoundError:
            logger.error(f"Model file not found at {self.model_path}")
            raise
    
    def get_feature_importance(self, X: np.ndarray, feature_names: list = None) -> Dict[str, float]:
        """
        Get feature importance based on isolation depth
        
        Args:
            X: Input data
            feature_names: List of feature names
            
        Returns:
            Dictionary of feature importance scores
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Get path lengths for each feature
        path_lengths = self.model._compute_score_samples(X)
        
        # For simplicity, return variance-based importance
        # In practice, you might want more sophisticated feature importance
        feature_importance = np.var(X, axis=0)
        
        # Normalize to sum to 1
        feature_importance = feature_importance / np.sum(feature_importance)
        
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(len(feature_importance))]
        
        return dict(zip(feature_names, feature_importance))

# Example usage and testing
if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    
    # Normal data
    normal_data = np.random.randn(1000, 10)
    
    # Anomalous data (different distribution)
    anomaly_data = np.random.randn(50, 10) * 3 + 5
    
    # Combine data
    X = np.vstack([normal_data, anomaly_data])
    
    # Split for training (train only on normal data)
    X_train = normal_data[:800]
    X_test = np.vstack([normal_data[800:], anomaly_data])
    
    # True labels for evaluation
    y_true = np.hstack([np.zeros(200), np.ones(50)])
    
    # Create and train model
    iforest = IsolationForestModel()
    iforest.train(X_train, contamination=0.05)
    
    # Make predictions
    results = iforest.predict_iforest(X_test)
    
    print(f"Anomaly rate in test set: {np.mean(results['predictions']):.3f}")
    print(f"Average anomaly score: {np.mean(results['raw_scores']):.3f}")
    
    # Evaluate
    metrics = iforest.evaluate(X_test, y_true)
    if 'classification_report' in metrics:
        print("\nClassification Report:")
        print(metrics['classification_report'])
    
    # Save model
    iforest.save_model()
    
    print("Isolation Forest model test completed successfully!")
