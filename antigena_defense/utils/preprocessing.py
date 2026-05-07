"""
Data Pipeline Module for Antigena Defense System
Handles data loading, preprocessing, and feature engineering
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import logging
from typing import Tuple, Dict, Any, Optional
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPipeline:
    """Data preprocessing pipeline for network security data"""
    
    def __init__(self, scaler_path: str = "models/scaler.pkl"):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.scaler_path = scaler_path
        self.feature_names = []
        
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load dataset from CSV file"""
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Data loaded successfully: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the dataset"""
        logger.info("Handling missing values...")
        
        # Fill numeric columns with median
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        
        # Fill categorical columns with mode
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown')
            
        logger.info("Missing values handled")
        return df
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows"""
        initial_shape = df.shape[0]
        df = df.drop_duplicates()
        final_shape = df.shape[0]
        logger.info(f"Removed {initial_shape - final_shape} duplicate rows")
        return df
    
    def encode_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical features using Label Encoding"""
        logger.info("Encoding categorical features...")
        
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[col] = self.label_encoders[col].fit_transform(df[col])
            else:
                # Use existing encoder for transform
                df[col] = self.label_encoders[col].transform(df[col])
        
        logger.info(f"Encoded {len(categorical_cols)} categorical features")
        return df
    
    def normalize_features(self, df: pd.DataFrame, fit: bool = True) -> np.ndarray:
        """Normalize features using StandardScaler"""
        logger.info("Normalizing features...")
        
        # Store feature names
        self.feature_names = df.columns.tolist()
        
        # Convert to numpy array
        X = df.values
        
        if fit:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
            
        logger.info("Features normalized")
        return X_scaled
    
    def extract_features(self, raw_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract features from raw data for real-time prediction
        Placeholder for future real-time feature extraction
        """
        # This is a placeholder - implement based on your specific data format
        features = []
        
        # Example feature extraction (customize based on your data)
        if 'network_flow' in raw_data:
            flow = raw_data['network_flow']
            features.extend([
                flow.get('bytes_sent', 0),
                flow.get('bytes_received', 0),
                flow.get('duration', 0),
                flow.get('packet_count', 0),
                flow.get('src_port', 0),
                flow.get('dst_port', 0)
            ])
        
        if 'log_data' in raw_data:
            log = raw_data['log_data']
            features.extend([
                log.get('event_count', 0),
                log.get('severity_score', 0),
                log.get('unique_ips', 0)
            ])
        
        return np.array(features).reshape(1, -1)
    
    def preprocess_data(self, file_path: str, save_scaler: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Complete preprocessing pipeline
        Returns processed features and splits into train/test
        """
        # Load data
        df = self.load_data(file_path)
        
        # Handle missing values
        df = self.handle_missing_values(df)
        
        # Remove duplicates
        df = self.remove_duplicates(df)
        
        # Encode categorical features
        df = self.encode_categorical_features(df)
        
        # Normalize features
        X = self.normalize_features(df, fit=True)
        
        # Save scaler if requested
        if save_scaler:
            self.save_scaler()
        
        # Split data (assuming no labels for unsupervised learning)
        X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
        
        logger.info(f"Preprocessing complete. Train shape: {X_train.shape}, Test shape: {X_test.shape}")
        return X_train, X_test
    
    def save_scaler(self):
        """Save the fitted scaler to disk"""
        os.makedirs(os.path.dirname(self.scaler_path), exist_ok=True)
        joblib.dump(self.scaler, self.scaler_path)
        logger.info(f"Scaler saved to {self.scaler_path}")
    
    def load_scaler(self):
        """Load scaler from disk"""
        try:
            self.scaler = joblib.load(self.scaler_path)
            logger.info(f"Scaler loaded from {self.scaler_path}")
        except FileNotFoundError:
            logger.error(f"Scaler file not found at {self.scaler_path}")
            raise
    
    def preprocess_real_time(self, data: np.ndarray) -> np.ndarray:
        """Preprocess real-time data for prediction"""
        if not hasattr(self.scaler, 'mean_'):
            logger.warning("Scaler not fitted. Loading from disk...")
            self.load_scaler()
        
        return self.scaler.transform(data)

# Example usage and testing
if __name__ == "__main__":
    # Create sample data for testing
    sample_data = {
        'timestamp': ['2023-01-01 10:00:00', '2023-01-01 10:01:00', '2023-01-01 10:02:00'],
        'src_ip': ['192.168.1.1', '192.168.1.2', '192.168.1.1'],
        'dst_ip': ['10.0.0.1', '10.0.0.2', '10.0.0.1'],
        'src_port': [80, 443, 22],
        'dst_port': [8080, 8443, 2222],
        'protocol': ['TCP', 'HTTPS', 'SSH'],
        'bytes_sent': [1024, 2048, 512],
        'bytes_received': [2048, 4096, 1024],
        'duration': [10, 15, 5],
        'packet_count': [20, 30, 10]
    }
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(sample_data)
    df.to_csv('sample_network_data.csv', index=False)
    
    # Test the pipeline
    pipeline = DataPipeline()
    X_train, X_test = pipeline.preprocess_data('sample_network_data.csv')
    
    print(f"Training data shape: {X_train.shape}")
    print(f"Test data shape: {X_test.shape}")
    print(f"Feature names: {pipeline.feature_names}")
