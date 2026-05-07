"""
Ensemble Engine for Anomaly Detection
Combines multiple models for robust threat detection
Part of Antigena-inspired Self-Learning AI Defense System
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
import logging
from .isolation_forest import IsolationForestModel
from .one_class_svm import OneClassSVMModel
from .autoencoder import AutoencoderModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnsembleEngine:
    """Ensemble engine combining multiple anomaly detection models"""
    
    def __init__(self, weights: Dict[str, float] = None, threshold: float = 0.5):
        """
        Initialize ensemble engine
        
        Args:
            weights: Weights for each model (default: equal weights)
            threshold: Final anomaly threshold (0-1)
        """
        self.models = {}
        self.weights = weights or {
            'isolation_forest': 0.4,
            'one_class_svm': 0.3,
            'autoencoder': 0.3
        }
        self.threshold = threshold
        self.is_trained = False
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self) -> None:
        """Initialize individual models"""
        self.models = {
            'isolation_forest': IsolationForestModel(),
            'one_class_svm': OneClassSVMModel(),
            'autoencoder': AutoencoderModel()
        }
        logger.info("Individual models initialized")
    
    def train_all_models(self, X_train: np.ndarray, X_val: np.ndarray = None,
                        iforest_contamination: float = 0.1,
                        svm_nu: float = 0.1,
                        autoencoder_epochs: int = 100) -> Dict[str, Any]:
        """
        Train all models in the ensemble
        
        Args:
            X_train: Training data (normal patterns)
            X_val: Validation data (optional)
            iforest_contamination: Contamination parameter for Isolation Forest
            svm_nu: Nu parameter for One-Class SVM
            autoencoder_epochs: Training epochs for Autoencoder
            
        Returns:
            Training results for each model
        """
        logger.info("Training ensemble models...")
        
        results = {}
        
        # Train Isolation Forest
        logger.info("Training Isolation Forest...")
        self.models['isolation_forest'].train(X_train, contamination=iforest_contamination)
        results['isolation_forest'] = 'trained'
        
        # Train One-Class SVM
        logger.info("Training One-Class SVM...")
        self.models['one_class_svm'].train(X_train, nu=svm_nu)
        results['one_class_svm'] = 'trained'
        
        # Train Autoencoder
        logger.info("Training Autoencoder...")
        if X_val is not None:
            ae_history = self.models['autoencoder'].train(
                X_train, X_val, epochs=autoencoder_epochs
            )
            results['autoencoder'] = ae_history
        else:
            # Use part of training data for validation
            split_idx = int(0.8 * len(X_train))
            X_train_ae = X_train[:split_idx]
            X_val_ae = X_train[split_idx:]
            ae_history = self.models['autoencoder'].train(
                X_train_ae, X_val_ae, epochs=autoencoder_epochs
            )
            results['autoencoder'] = ae_history
        
        self.is_trained = True
        logger.info("All ensemble models trained successfully")
        
        return results
    
    def predict_ensemble(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Make ensemble predictions
        
        Args:
            X: Input data
            
        Returns:
            Dictionary with ensemble predictions and individual model results
        """
        if not self.is_trained:
            raise ValueError("Models not trained. Call train_all_models() first.")
        
        logger.info(f"Making ensemble predictions on {X.shape[0]} samples...")
        
        # Get predictions from all models
        model_results = {}
        
        try:
            model_results['isolation_forest'] = self.models['isolation_forest'].predict_iforest(X)
        except Exception as e:
            logger.warning(f"Isolation Forest prediction failed: {e}")
            model_results['isolation_forest'] = {
                'predictions': np.zeros(X.shape[0]),
                'normalized_scores': np.zeros(X.shape[0])
            }
        
        try:
            model_results['one_class_svm'] = self.models['one_class_svm'].predict_svm(X)
        except Exception as e:
            logger.warning(f"One-Class SVM prediction failed: {e}")
            model_results['one_class_svm'] = {
                'predictions': np.zeros(X.shape[0]),
                'normalized_scores': np.zeros(X.shape[0])
            }
        
        try:
            model_results['autoencoder'] = self.models['autoencoder'].predict_autoencoder(X)
        except Exception as e:
            logger.warning(f"Autoencoder prediction failed: {e}")
            model_results['autoencoder'] = {
                'predictions': np.zeros(X.shape[0]),
                'normalized_scores': np.zeros(X.shape[0])
            }
        
        # Calculate weighted ensemble score
        ensemble_scores = self._calculate_weighted_scores(model_results)
        
        # Make final predictions
        final_predictions = (ensemble_scores > self.threshold).astype(int)
        
        # Compile results
        results = {
            'ensemble_score': ensemble_scores,
            'final_predictions': final_predictions,
            'threshold': self.threshold,
            'individual_models': model_results,
            'weights': self.weights
        }
        
        # Add summary statistics
        results['summary'] = {
            'anomaly_rate': np.mean(final_predictions),
            'avg_ensemble_score': np.mean(ensemble_scores),
            'score_std': np.std(ensemble_scores),
            'max_score': np.max(ensemble_scores),
            'min_score': np.min(ensemble_scores)
        }
        
        logger.info(f"Ensemble prediction complete. Anomaly rate: {np.mean(final_predictions):.3f}")
        
        return results
    
    def _calculate_weighted_scores(self, model_results: Dict[str, Any]) -> np.ndarray:
        """
        Calculate weighted ensemble scores from individual model results
        
        Args:
            model_results: Results from individual models
            
        Returns:
            Weighted ensemble scores
        """
        n_samples = len(next(iter(model_results.values()))['normalized_scores'])
        ensemble_scores = np.zeros(n_samples)
        
        for model_name, results in model_results.items():
            weight = self.weights.get(model_name, 0)
            scores = results['normalized_scores']
            ensemble_scores += weight * scores
        
        return ensemble_scores
    
    def optimize_weights(self, X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, float]:
        """
        Optimize model weights using validation set
        
        Args:
            X_val: Validation data
            y_val: True labels
            
        Returns:
            Optimized weights
        """
        logger.info("Optimizing ensemble weights...")
        
        # Get predictions from all models
        model_results = {}
        for model_name, model in self.models.items():
            if hasattr(model, 'predict_iforest'):
                model_results[model_name] = model.predict_iforest(X_val)
            elif hasattr(model, 'predict_svm'):
                model_results[model_name] = model.predict_svm(X_val)
            elif hasattr(model, 'predict_autoencoder'):
                model_results[model_name] = model.predict_autoencoder(X_val)
        
        # Grid search for optimal weights
        best_f1 = 0
        best_weights = self.weights.copy()
        
        # Simple grid search (can be made more sophisticated)
        weight_ranges = np.linspace(0.1, 0.6, 6)
        
        for w1 in weight_ranges:
            for w2 in weight_ranges:
                for w3 in weight_ranges:
                    total = w1 + w2 + w3
                    if total == 0:
                        continue
                    
                    # Normalize weights
                    weights = {
                        'isolation_forest': w1 / total,
                        'one_class_svm': w2 / total,
                        'autoencoder': w3 / total
                    }
                    
                    # Calculate ensemble score
                    self.weights = weights
                    ensemble_results = self.predict_ensemble(X_val)
                    predictions = ensemble_results['final_predictions']
                    
                    # Calculate F1 score
                    from sklearn.metrics import f1_score
                    f1 = f1_score(y_val, predictions, average='binary')
                    
                    if f1 > best_f1:
                        best_f1 = f1
                        best_weights = weights.copy()
        
        self.weights = best_weights
        logger.info(f"Optimized weights: {best_weights} (F1: {best_f1:.3f})")
        
        return best_weights
    
    def optimize_threshold(self, X_val: np.ndarray, y_val: np.ndarray) -> float:
        """
        Optimize anomaly threshold using validation set
        
        Args:
            X_val: Validation data
            y_val: True labels
            
        Returns:
            Optimized threshold
        """
        logger.info("Optimizing anomaly threshold...")
        
        # Get ensemble scores
        ensemble_results = self.predict_ensemble(X_val)
        scores = ensemble_results['ensemble_score']
        
        # Find optimal threshold
        best_f1 = 0
        best_threshold = 0.5
        
        thresholds = np.linspace(0.1, 0.9, 81)
        
        for threshold in thresholds:
            predictions = (scores > threshold).astype(int)
            
            # Calculate F1 score
            from sklearn.metrics import f1_score
            f1 = f1_score(y_val, predictions, average='binary')
            
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = threshold
        
        self.threshold = best_threshold
        logger.info(f"Optimized threshold: {best_threshold:.3f} (F1: {best_f1:.3f})")
        
        return best_threshold
    
    def evaluate_ensemble(self, X_test: np.ndarray, y_test: np.ndarray = None) -> Dict[str, Any]:
        """
        Evaluate ensemble performance
        
        Args:
            X_test: Test data
            y_test: True labels (optional)
            
        Returns:
            Evaluation metrics
        """
        results = self.predict_ensemble(X_test)
        
        metrics = {
            'ensemble_scores': results['ensemble_score'],
            'final_predictions': results['final_predictions'],
            'anomaly_rate': results['summary']['anomaly_rate'],
            'avg_score': results['summary']['avg_ensemble_score'],
            'score_std': results['summary']['score_std'],
            'threshold': self.threshold,
            'weights': self.weights
        }
        
        # Add individual model metrics
        for model_name, model_results in results['individual_models'].items():
            metrics[f'{model_name}_predictions'] = model_results['predictions']
            metrics[f'{model_name}_scores'] = model_results['normalized_scores']
        
        # Add classification metrics if true labels available
        if y_test is not None:
            from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
            
            metrics['classification_report'] = classification_report(y_test, results['final_predictions'])
            metrics['confusion_matrix'] = confusion_matrix(y_test, results['final_predictions'])
            metrics['roc_auc'] = roc_auc_score(y_test, results['ensemble_score'])
        
        return metrics
    
    def save_ensemble(self, base_path: str = "models/ensemble") -> None:
        """Save all models in the ensemble"""
        if not self.is_trained:
            raise ValueError("No trained models to save")
        
        # Save individual models
        for model_name, model in self.models.items():
            model_path = f"{base_path}_{model_name}.pkl"
            if model_name == 'autoencoder':
                model_path = f"{base_path}_{model_name}.h5"
                model.model_path = model_path
            
            if hasattr(model, 'save_model'):
                model.save_model()
        
        # Save ensemble configuration
        import joblib
        config = {
            'weights': self.weights,
            'threshold': self.threshold,
            'is_trained': self.is_trained
        }
        
        config_path = f"{base_path}_config.pkl"
        joblib.dump(config, config_path)
        
        logger.info(f"Ensemble saved with config at {config_path}")
    
    def load_ensemble(self, base_path: str = "models/ensemble") -> None:
        """Load all models in the ensemble"""
        # Load ensemble configuration
        import joblib
        config_path = f"{base_path}_config.pkl"
        
        try:
            config = joblib.load(config_path)
            self.weights = config['weights']
            self.threshold = config['threshold']
            self.is_trained = config['is_trained']
        except FileNotFoundError:
            logger.warning(f"Ensemble config not found at {config_path}")
        
        # Load individual models
        for model_name, model in self.models.items():
            model_path = f"{base_path}_{model_name}.pkl"
            if model_name == 'autoencoder':
                model_path = f"{base_path}_{model_name}.h5"
                model.model_path = model_path
            
            if hasattr(model, 'load_model'):
                try:
                    model.load_model()
                except FileNotFoundError:
                    logger.warning(f"Model {model_name} not found at {model_path}")
        
        logger.info("Ensemble loaded successfully")

# Example usage and testing
if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    
    # Normal data
    normal_data = np.random.randn(1000, 15)
    
    # Anomalous data (different distribution)
    anomaly_data = np.random.randn(50, 15) * 3 + 5
    
    # Combine data
    X = np.vstack([normal_data, anomaly_data])
    
    # Split data
    X_train = normal_data[:700]
    X_val = np.vstack([normal_data[700:850], anomaly_data[:25]])
    X_test = np.vstack([normal_data[850:], anomaly_data[25:]])
    
    # True labels
    y_val = np.hstack([np.zeros(150), np.ones(25)])
    y_test = np.hstack([np.zeros(150), np.ones(25)])
    
    # Create and train ensemble
    ensemble = EnsembleEngine()
    
    # Train all models
    training_results = ensemble.train_all_models(X_train, X_val, autoencoder_epochs=50)
    
    # Optimize weights and threshold
    ensemble.optimize_weights(X_val, y_val)
    ensemble.optimize_threshold(X_val, y_val)
    
    # Make predictions
    results = ensemble.predict_ensemble(X_test)
    
    print(f"Ensemble anomaly rate: {results['summary']['anomaly_rate']:.3f}")
    print(f"Average ensemble score: {results['summary']['avg_ensemble_score']:.3f}")
    print(f"Threshold: {results['threshold']:.3f}")
    print(f"Weights: {ensemble.weights}")
    
    # Evaluate
    metrics = ensemble.evaluate_ensemble(X_test, y_test)
    if 'classification_report' in metrics:
        print("\nClassification Report:")
        print(metrics['classification_report'])
        print(f"\nROC AUC: {metrics['roc_auc']:.3f}")
    
    # Save ensemble
    ensemble.save_ensemble()
    
    print("Ensemble engine test completed successfully!")
