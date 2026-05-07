"""
Autoencoder Model for Anomaly Detection
Part of Antigena-inspired Self-Learning AI Defense System
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import Dense, Input, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import logging
from typing import Tuple, Dict, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoencoderModel:
    """Autoencoder model for anomaly detection using reconstruction error"""
    
    def __init__(self, model_path: str = "models/autoencoder.h5"):
        self.model = None
        self.encoder = None
        self.decoder = None
        self.model_path = model_path
        self.threshold = None
        self.encoding_dim = None
        self.input_dim = None
        
    def build_model(self, input_dim: int, encoding_dims: list = None, dropout_rate: float = 0.2) -> None:
        """
        Build autoencoder architecture
        
        Args:
            input_dim: Number of input features
            encoding_dims: List of encoding layer dimensions
            dropout_rate: Dropout rate for regularization
        """
        logger.info("Building autoencoder architecture...")
        
        self.input_dim = input_dim
        
        if encoding_dims is None:
            encoding_dims = [input_dim // 2, input_dim // 4, input_dim // 8]
        
        self.encoding_dim = encoding_dims[-1]
        
        # Encoder
        input_layer = Input(shape=(input_dim,))
        
        x = input_layer
        for dim in encoding_dims:
            x = Dense(dim, activation='relu')(x)
            x = Dropout(dropout_rate)(x)
        
        encoded = x
        
        # Decoder
        x = encoded
        for dim in reversed(encoding_dims[:-1]):
            x = Dense(dim, activation='relu')(x)
            x = Dropout(dropout_rate)(x)
        
        decoded = Dense(input_dim, activation='linear')(x)
        
        # Full autoencoder model
        self.model = Model(input_layer, decoded)
        
        # Encoder model (for feature extraction)
        self.encoder = Model(input_layer, encoded)
        
        # Build decoder separately
        decoder_input = Input(shape=(self.encoding_dim,))
        x = decoder_input
        for dim in reversed(encoding_dims[:-1]):
            x = Dense(dim, activation='relu')(x)
            x = Dropout(dropout_rate)(x)
        decoded_output = Dense(input_dim, activation='linear')(x)
        self.decoder = Model(decoder_input, decoded_output)
        
        logger.info(f"Autoencoder built with input_dim={input_dim}, encoding_dim={self.encoding_dim}")
    
    def train(self, X_train: np.ndarray, X_val: np.ndarray = None, 
              epochs: int = 100, batch_size: int = 32, 
              learning_rate: float = 0.001) -> Dict[str, Any]:
        """
        Train autoencoder on normal data
        
        Args:
            X_train: Training data (normal patterns)
            X_val: Validation data (optional)
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate for optimizer
            
        Returns:
            Training history
        """
        if self.model is None:
            self.build_model(X_train.shape[1])
        
        logger.info("Training autoencoder...")
        
        # Compile model
        optimizer = Adam(learning_rate=learning_rate)
        self.model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
        
        # Prepare validation data
        validation_data = (X_val, X_val) if X_val is not None else None
        
        # Callbacks
        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True, monitor='val_loss'),
            ReduceLROnPlateau(patience=5, factor=0.5, monitor='val_loss')
        ]
        
        # Train model
        history = self.model.fit(
            X_train, X_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=validation_data,
            callbacks=callbacks,
            verbose=1
        )
        
        # Calculate threshold based on training reconstruction error
        self.calculate_threshold(X_train)
        
        logger.info(f"Autoencoder training completed. Threshold: {self.threshold:.6f}")
        
        return history.history
    
    def calculate_threshold(self, X_normal: np.ndarray, percentile: float = 95) -> None:
        """
        Calculate anomaly threshold based on reconstruction error of normal data
        
        Args:
            X_normal: Normal data for threshold calculation
            percentile: Percentile for threshold (95% means 5% false positive rate)
        """
        reconstructions = self.model.predict(X_normal, verbose=0)
        reconstruction_errors = np.mean(np.square(X_normal - reconstructions), axis=1)
        
        self.threshold = np.percentile(reconstruction_errors, percentile)
        logger.info(f"Threshold calculated at {percentile}th percentile: {self.threshold:.6f}")
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions on new data
        
        Args:
            X: Input data
            
        Returns:
            Tuple of (predictions, reconstruction_errors)
            - predictions: 0 for normal, 1 for anomaly
            - reconstruction_errors: MSE reconstruction error for each sample
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        if self.threshold is None:
            raise ValueError("Threshold not calculated. Call calculate_threshold() first.")
        
        # Get reconstructions
        reconstructions = self.model.predict(X, verbose=0)
        
        # Calculate reconstruction errors
        reconstruction_errors = np.mean(np.square(X - reconstructions), axis=1)
        
        # Make predictions based on threshold
        predictions = (reconstruction_errors > self.threshold).astype(int)
        
        return predictions, reconstruction_errors
    
    def predict_autoencoder(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Main prediction function for ensemble integration
        
        Args:
            X: Input data
            
        Returns:
            Dictionary with predictions and scores
        """
        predictions, errors = self.predict(X)
        
        # Normalize reconstruction errors to 0-1 range
        normalized_errors = self._normalize_errors(errors)
        
        return {
            'predictions': predictions,
            'reconstruction_errors': errors,
            'normalized_scores': normalized_errors,
            'threshold': self.threshold,
            'method': 'autoencoder'
        }
    
    def _normalize_errors(self, errors: np.ndarray) -> np.ndarray:
        """
        Normalize reconstruction errors to 0-1 range
        
        Args:
            errors: Raw reconstruction errors
            
        Returns:
            Normalized errors (0-1, higher = more anomalous)
        """
        if self.threshold is None:
            return np.zeros_like(errors)
        
        # Normalize by threshold (errors > threshold = 1, scaled below threshold)
        normalized = np.minimum(errors / self.threshold, 2.0) / 2.0
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
        predictions, errors = self.predict(X_test)
        
        metrics = {
            'predictions': predictions,
            'reconstruction_errors': errors,
            'anomaly_rate': np.mean(predictions),
            'avg_error': np.mean(errors),
            'error_std': np.std(errors),
            'threshold': self.threshold
        }
        
        # Add classification metrics if true labels available
        if y_true is not None:
            metrics['classification_report'] = classification_report(y_true, predictions)
            metrics['confusion_matrix'] = confusion_matrix(y_true, predictions)
        
        return metrics
    
    def get_encoded_features(self, X: np.ndarray) -> np.ndarray:
        """
        Get encoded (compressed) features
        
        Args:
            X: Input data
            
        Returns:
            Encoded features
        """
        if self.encoder is None:
            raise ValueError("Encoder not built. Call build_model() first.")
        
        return self.encoder.predict(X, verbose=0)
    
    def save_model(self) -> None:
        """Save the trained model to disk"""
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Save model architecture and weights
        self.model.save(self.model_path)
        
        # Save additional metadata
        metadata = {
            'threshold': self.threshold,
            'input_dim': self.input_dim,
            'encoding_dim': self.encoding_dim
        }
        
        metadata_path = self.model_path.replace('.h5', '_metadata.pkl')
        joblib.dump(metadata, metadata_path)
        
        logger.info(f"Model saved to {self.model_path}")
        logger.info(f"Metadata saved to {metadata_path}")
    
    def load_model(self) -> None:
        """Load a trained model from disk"""
        try:
            # Load model
            self.model = tf.keras.models.load_model(self.model_path)
            
            # Load metadata
            metadata_path = self.model_path.replace('.h5', '_metadata.pkl')
            metadata = joblib.load(metadata_path)
            
            self.threshold = metadata['threshold']
            self.input_dim = metadata['input_dim']
            self.encoding_dim = metadata['encoding_dim']
            
            # Rebuild encoder and decoder
            self._rebuild_encoder_decoder()
            
            logger.info(f"Model loaded from {self.model_path}")
        except FileNotFoundError:
            logger.error(f"Model file not found at {self.model_path}")
            raise
    
    def _rebuild_encoder_decoder(self) -> None:
        """Rebuild encoder and decoder models from loaded model"""
        # This is a simplified approach - in practice, you might want to save
        # encoder and decoder separately during training
        
        # For now, we'll create a simple encoder based on the loaded model
        input_layer = Input(shape=(self.input_dim,))
        
        # Get the first half of the model as encoder (simplified)
        encoder_layers = []
        for layer in self.model.layers[:-1]:  # Exclude final output layer
            if hasattr(layer, 'output'):
                encoder_layers.append(layer.output)
        
        if encoder_layers:
            encoded = encoder_layers[-1]
            self.encoder = Model(input_layer, encoded)
        
        logger.info("Encoder and decoder rebuilt from loaded model")

# Example usage and testing
if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    tf.random.set_seed(42)
    
    # Normal data
    normal_data = np.random.randn(1000, 20)
    
    # Anomalous data (different distribution)
    anomaly_data = np.random.randn(50, 20) * 3 + 5
    
    # Combine data
    X = np.vstack([normal_data, anomaly_data])
    
    # Split for training (train only on normal data)
    X_train = normal_data[:800]
    X_val = normal_data[800:900]
    X_test = np.vstack([normal_data[900:], anomaly_data])
    
    # True labels for evaluation
    y_test = np.hstack([np.zeros(100), np.ones(50)])
    
    # Create and train model
    autoencoder = AutoencoderModel()
    autoencoder.build_model(input_dim=20, encoding_dims=[15, 10, 5])
    
    # Train model
    history = autoencoder.train(X_train, X_val, epochs=50, batch_size=32)
    
    # Make predictions
    results = autoencoder.predict_autoencoder(X_test)
    
    print(f"Anomaly rate in test set: {np.mean(results['predictions']):.3f}")
    print(f"Average reconstruction error: {np.mean(results['reconstruction_errors']):.6f}")
    print(f"Threshold: {results['threshold']:.6f}")
    
    # Evaluate
    metrics = autoencoder.evaluate(X_test, y_test)
    if 'classification_report' in metrics:
        print("\nClassification Report:")
        print(metrics['classification_report'])
    
    # Get encoded features
    encoded_features = autoencoder.get_encoded_features(X_test[:5])
    print(f"\nEncoded features shape: {encoded_features.shape}")
    
    # Save model
    autoencoder.save_model()
    
    print("Autoencoder model test completed successfully!")
