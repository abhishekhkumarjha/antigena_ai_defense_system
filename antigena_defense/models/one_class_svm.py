"""
One-Class SVM Model for Anomaly Detection
Part of Antigena-inspired Self-Learning AI Defense System
"""

import numpy as np
import pandas as pd
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import logging
from typing import Tuple, Dict, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OneClassSVMModel:
    """One-Class SVM model for anomaly detection"""
    
    def __init__(self, model_path: str = "models/one_class_svm.pkl"):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = model_path
        self.nu = 0.1  # Upper bound on fraction of training errors
        self.kernel = 'rbf'
        self.gamma = 'scale'
        
    def train(self, X_train: np.ndarray, nu: float = 0.1, kernel: str = 'rbf', gamma: str = 'scale') -> None:
        """
        Train One-Class SVM on normal data
        
        Args:
            X_train: Training data (normal patterns)
            nu: Upper bound on fraction of training errors
            kernel: Kernel type ('rbf', 'linear', 'poly', 'sigmoid')
            gamma: Kernel coefficient
        """
        logger.info("Training One-Class SVM model...")
        
        # Normalize input data
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        self.nu = nu
        self.kernel = kernel
        self.gamma = gamma
        
        self.model = OneClassSVM(
            kernel=kernel,
            gamma=gamma,
            nu=nu
        )
        
        # Fit the model
        self.model.fit(X_train_scaled)
        
        logger.info(f"One-Class SVM trained with nu={nu}, kernel={kernel}")
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions on new data
        
        Args:
            X: Input data
            
        Returns:
            Tuple of (predictions, decision_scores)
            - predictions: 1 for normal, -1 for anomaly
            - decision_scores: Distance to decision boundary
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Normalize input data
        X_scaled = self.scaler.transform(X)
        
        # Get predictions
        predictions = self.model.predict(X_scaled)
        
        # Get decision function scores
        decision_scores = self.model.decision_function(X_scaled)
        
        return predictions, decision_scores
    
    def predict_svm(self, X: np.ndarray) -> Dict[str, Any]:
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
            'method': 'one_class_svm'
        }
    
    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """
        Normalize decision scores to 0-1 range
        
        Args:
            scores: Raw decision scores (negative for anomalies)
            
        Returns:
            Normalized scores (0-1, higher = more anomalous)
        """
        # Since negative scores indicate anomalies, we invert and normalize
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
            'decision_scores': scores,
            'anomaly_rate': np.mean(binary_predictions),
            'avg_score': np.mean(scores),
            'score_std': np.std(scores)
        }
        
        # Add classification metrics if true labels available
        if y_true is not None:
            metrics['classification_report'] = classification_report(y_true, binary_predictions)
            metrics['confusion_matrix'] = confusion_matrix(y_true, binary_predictions)
        
        return metrics
    
    def find_optimal_nu(self, X_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray) -> float:
        """
        Find optimal nu parameter using validation set
        
        Args:
            X_train: Training data
            X_val: Validation data
            y_val: True labels for validation
            
        Returns:
            Optimal nu value
        """
        logger.info("Finding optimal nu parameter...")
        
        nu_values = [0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
        best_f1 = 0
        best_nu = 0.1
        
        for nu in nu_values:
            # Train temporary model
            temp_model = OneClassSVMModel()
            temp_model.train(X_train, nu=nu)
            
            # Evaluate on validation set
            predictions, _ = temp_model.predict(X_val)
            binary_predictions = np.where(predictions == -1, 1, 0)
            
            # Calculate F1 score (simplified)
            from sklearn.metrics import f1_score
            f1 = f1_score(y_val, binary_predictions, average='binary')
            
            if f1 > best_f1:
                best_f1 = f1
                best_nu = nu
        
        logger.info(f"Optimal nu found: {best_nu} (F1: {best_f1:.3f})")
        return best_nu
    
    def save_model(self) -> None:
        """Save the trained model and scaler to disk"""
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Save both model and scaler
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'nu': self.nu,
            'kernel': self.kernel,
            'gamma': self.gamma
        }
        
        joblib.dump(model_data, self.model_path)
        logger.info(f"Model and scaler saved to {self.model_path}")
    
    def load_model(self) -> None:
        """Load a trained model and scaler from disk"""
        try:
            model_data = joblib.load(self.model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.nu = model_data['nu']
            self.kernel = model_data['kernel']
            self.gamma = model_data['gamma']
            
            logger.info(f"Model and scaler loaded from {self.model_path}")
        except FileNotFoundError:
            logger.error(f"Model file not found at {self.model_path}")
            raise
    
    def get_support_vectors_info(self) -> Dict[str, Any]:
        """
        Get information about support vectors
        
        Returns:
            Dictionary with support vector information
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        n_support = self.model.n_support_
        support_vectors = self.model.support_vectors_
        
        return {
            'n_support': n_support,
            'total_support_vectors': len(support_vectors),
            'support_ratio': len(support_vectors) / len(self.model.support_)
        }

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
    X_val = normal_data[800:900]
    X_test = np.vstack([normal_data[900:], anomaly_data])
    
    # True labels for evaluation
    y_val = np.zeros(100)
    y_test = np.hstack([np.zeros(100), np.ones(50)])
    
    # Create and train model
    svm_model = OneClassSVMModel()
    
    # Find optimal nu (optional)
    optimal_nu = svm_model.find_optimal_nu(X_train, X_val, y_val)
    
    # Train with optimal nu
    svm_model.train(X_train, nu=optimal_nu)
    
    # Make predictions
    results = svm_model.predict_svm(X_test)
    
    print(f"Anomaly rate in test set: {np.mean(results['predictions']):.3f}")
    print(f"Average decision score: {np.mean(results['raw_scores']):.3f}")
    
    # Evaluate
    metrics = svm_model.evaluate(X_test, y_test)
    if 'classification_report' in metrics:
        print("\nClassification Report:")
        print(metrics['classification_report'])
    
    # Get support vector info
    sv_info = svm_model.get_support_vectors_info()
    print(f"\nSupport vectors: {sv_info['total_support_vectors']}")
    
    # Save model
    svm_model.save_model()
    
    print("One-Class SVM model test completed successfully!")
