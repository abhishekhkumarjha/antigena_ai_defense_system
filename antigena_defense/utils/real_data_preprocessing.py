"""
Enhanced Data Pipeline for Real Network Security Datasets
Supports UNSW-NB15 and CIC-IDS2017 datasets
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import logging
from typing import Tuple, Dict, Any, Optional, List
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealDataPipeline:
    """Enhanced data pipeline for real network security datasets"""
    
    def __init__(self, scaler_path: str = "models/real_scaler.pkl"):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.scaler_path = scaler_path
        self.feature_names = []
        self.dataset_type = None
        
    def load_unsw_dataset(self, train_path: str, test_path: str = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load UNSW-NB15 dataset
        
        Args:
            train_path: Path to training CSV
            test_path: Path to test CSV (optional)
            
        Returns:
            Tuple of (train_df, test_df)
        """
        logger.info("Loading UNSW-NB15 dataset...")
        
        # Load training data
        train_df = pd.read_csv(train_path)
        
        # Load test data if provided
        test_df = None
        if test_path:
            test_df = pd.read_csv(test_path)
        
        self.dataset_type = "UNSW"
        logger.info(f"UNSW dataset loaded - Train: {train_df.shape}, Test: {test_df.shape if test_df is not None else 'None'}")
        
        return train_df, test_df
    
    def load_cic_dataset(self, file_paths: List[str]) -> pd.DataFrame:
        """
        Load CIC-IDS2017 dataset
        
        Args:
            file_paths: List of CSV file paths
            
        Returns:
            Combined DataFrame
        """
        logger.info("Loading CIC-IDS2017 dataset...")
        
        dataframes = []
        for file_path in file_paths:
            try:
                df = pd.read_csv(file_path)
                # Clean column names (remove spaces and special characters)
                df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('-', '_')
                dataframes.append(df)
                logger.info(f"Loaded {file_path}: {df.shape}")
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
        
        if not dataframes:
            raise ValueError("No CIC dataset files could be loaded")
        
        combined_df = pd.concat(dataframes, ignore_index=True)
        self.dataset_type = "CIC"
        
        logger.info(f"CIC dataset combined: {combined_df.shape}")
        return combined_df
    
    def preprocess_unsw_data(self, df: pd.DataFrame, is_training: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess UNSW-NB15 dataset
        
        Args:
            df: Input DataFrame
            is_training: Whether this is training data
            
        Returns:
            Tuple of (features, labels)
        """
        logger.info("Preprocessing UNSW-NB15 data...")
        
        # Make a copy to avoid modifying original
        df_processed = df.copy()
        
        # Handle missing values
        df_processed = self._handle_missing_values(df_processed)
        
        # Remove unnecessary columns
        columns_to_remove = ['id']  # Remove ID column
        existing_columns = [col for col in columns_to_remove if col in df_processed.columns]
        df_processed = df_processed.drop(columns=existing_columns)
        
        # Handle categorical features
        categorical_columns = ['proto', 'service', 'state']
        for col in categorical_columns:
            if col in df_processed.columns:
                df_processed[col] = df_processed[col].fillna('Unknown')
                
                # Convert to string to handle mixed types
                df_processed[col] = df_processed[col].astype(str)
                
                if is_training:
                    if col not in self.label_encoders:
                        self.label_encoders[col] = LabelEncoder()
                    df_processed[col] = self.label_encoders[col].fit_transform(df_processed[col])
                else:
                    if col in self.label_encoders:
                        # Handle unseen labels
                        unique_values = set(df_processed[col].unique())
                        known_values = set(self.label_encoders[col].classes_)
                        unseen_values = unique_values - known_values
                        
                        if unseen_values:
                            logger.warning(f"Unseen values in {col}: {unseen_values}")
                            # Assign unknown label to unseen values
                            df_processed[col] = df_processed[col].apply(
                                lambda x: x if x in known_values else self.label_encoders[col].classes_[0]
                            )
                            
                        df_processed[col] = self.label_encoders[col].transform(df_processed[col])
        
        # Extract features and labels
        feature_columns = [col for col in df_processed.columns if col not in ['attack_cat', 'label']]
        X = df_processed[feature_columns].values
        
        # Create binary labels (0: normal, 1: attack)
        if 'label' in df_processed.columns:
            y = df_processed['label'].values
        else:
            # If no label column, assume all are normal for unsupervised learning
            y = np.zeros(len(df_processed))
        
        # Store feature names
        self.feature_names = feature_columns
        
        logger.info(f"UNSW preprocessing complete - Features: {X.shape}, Labels: {y.shape}")
        return X, y
    
    def preprocess_cic_data(self, df: pd.DataFrame, is_training: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess CIC-IDS2017 dataset
        
        Args:
            df: Input DataFrame
            is_training: Whether this is training data
            
        Returns:
            Tuple of (features, labels)
        """
        logger.info("Preprocessing CIC-IDS2017 data...")
        
        # Make a copy to avoid modifying original
        df_processed = df.copy()
        
        # Handle missing values
        df_processed = self._handle_missing_values(df_processed)
        
        # Remove columns with all NaN values or infinite values
        df_processed = df_processed.replace([np.inf, -np.inf], np.nan)
        df_processed = df_processed.dropna(axis=1, how='all')
        
        # Remove columns with zero variance
        numeric_columns = df_processed.select_dtypes(include=[np.number]).columns
        zero_var_cols = []
        for col in numeric_columns:
            if df_processed[col].var() == 0:
                zero_var_cols.append(col)
        
        if zero_var_cols:
            df_processed = df_processed.drop(columns=zero_var_cols)
            logger.info(f"Removed zero variance columns: {zero_var_cols}")
        
        # Extract features and labels
        label_column = 'Label'  # CIC dataset uses 'Label' column
        feature_columns = [col for col in df_processed.columns if col != label_column]
        
        X = df_processed[feature_columns].values
        
        # Create binary labels (0: BENIGN, 1: ATTACK)
        if label_column in df_processed.columns:
            y = (df_processed[label_column] != 'BENIGN').astype(int).values
        else:
            # If no label column, assume all are normal for unsupervised learning
            y = np.zeros(len(df_processed))
        
        # Store feature names
        self.feature_names = feature_columns
        
        logger.info(f"CIC preprocessing complete - Features: {X.shape}, Labels: {y.shape}")
        return X, y
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in dataset"""
        logger.info("Handling missing values...")
        
        # Replace infinite values with NaN
        df = df.replace([np.inf, -np.inf], np.nan)
        
        # Fill numeric columns with median
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isnull().sum() > 0:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
        
        # Fill categorical columns with mode
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if df[col].isnull().sum() > 0:
                mode_val = df[col].mode()[0] if not df[col].mode().empty else 'Unknown'
                df[col] = df[col].fillna(mode_val)
        
        # Check for any remaining NaN values
        remaining_nan = df.isnull().sum().sum()
        if remaining_nan > 0:
            logger.warning(f"Still have {remaining_nan} NaN values after preprocessing")
            # Drop rows with NaN values as last resort
            df = df.dropna()
            logger.info(f"Dropped {remaining_nan} rows with NaN values")
        
        return df
    
    def normalize_features(self, X: np.ndarray, fit: bool = True) -> np.ndarray:
        """Normalize features using StandardScaler"""
        logger.info("Normalizing features...")
        
        if fit:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        logger.info("Features normalized")
        return X_scaled
    
    def prepare_unsupervised_data(self, X: np.ndarray, y: np.ndarray, 
                              normal_ratio: float = 0.8) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for unsupervised learning by separating normal and attack samples
        
        Args:
            X: Features
            y: Labels
            normal_ratio: Ratio of normal data to use for training
            
        Returns:
            Tuple of (X_train_normal, X_mixed)
        """
        # Separate normal and attack samples
        normal_mask = y == 0
        attack_mask = y == 1
        
        X_normal = X[normal_mask]
        X_attack = X[attack_mask]
        
        logger.info(f"Normal samples: {len(X_normal)}, Attack samples: {len(X_attack)}")
        
        # Use portion of normal data for training
        n_train_normal = int(len(X_normal) * normal_ratio)
        X_train_normal = X_normal[:n_train_normal]
        
        # Create mixed test set (remaining normal + all attacks)
        X_test_normal = X_normal[n_train_normal:]
        X_mixed = np.vstack([X_test_normal, X_attack])
        
        logger.info(f"Training normal: {X_train_normal.shape}, Mixed test: {X_mixed.shape}")
        
        return X_train_normal, X_mixed
    
    def preprocess_real_dataset(self, dataset_type: str, file_paths: List[str], 
                            test_paths: List[str] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Complete preprocessing pipeline for real datasets
        
        Args:
            dataset_type: 'UNSW' or 'CIC'
            file_paths: List of training file paths
            test_paths: List of test file paths (for UNSW)
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        if dataset_type.upper() == "UNSW":
            return self._preprocess_unsw_complete(file_paths, test_paths)
        elif dataset_type.upper() == "CIC":
            return self._preprocess_cic_complete(file_paths)
        else:
            raise ValueError("Dataset type must be 'UNSW' or 'CIC'")
    
    def _preprocess_unsw_complete(self, train_paths: List[str], test_paths: List[str] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Complete UNSW dataset preprocessing"""
        # Load training data
        train_path = train_paths[0] if train_paths else None
        test_path = test_paths[0] if test_paths else None
        
        if not train_path:
            raise ValueError("Training path required for UNSW dataset")
        
        train_df, test_df = self.load_unsw_dataset(train_path, test_path)
        
        # Preprocess training data
        X_train_full, y_train_full = self.preprocess_unsw_data(train_df, is_training=True)
        
        # Preprocess test data
        if test_df is not None:
            X_test, y_test = self.preprocess_unsw_data(test_df, is_training=False)
        else:
            # Split training data for train/test
            X_train_full, X_test, y_train_full, y_test = train_test_split(
                X_train_full, y_train_full, test_size=0.3, random_state=42, stratify=y_train_full
            )
        
        # Normalize features
        X_train = self.normalize_features(X_train_full, fit=True)
        X_test = self.normalize_features(X_test, fit=False)
        
        return X_train, X_test, y_train_full, y_test
    
    def _preprocess_cic_complete(self, file_paths: List[str]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Complete CIC dataset preprocessing"""
        # Load and combine all CIC files
        combined_df = self.load_cic_dataset(file_paths)
        
        # Preprocess data
        X_full, y_full = self.preprocess_cic_data(combined_df, is_training=True)
        
        # Split into train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X_full, y_full, test_size=0.3, random_state=42, stratify=y_full
        )
        
        # Normalize features
        X_train = self.normalize_features(X_train, fit=True)
        X_test = self.normalize_features(X_test, fit=False)
        
        return X_train, X_test, y_train, y_test
    
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

# Example usage
if __name__ == "__main__":
    # Example with UNSW dataset
    pipeline = RealDataPipeline()
    
    # UNSW dataset paths
    unsw_train = "data/OneDrive_data/Training and Testing Sets/UNSW_NB15_training-set.csv"
    unsw_test = "data/OneDrive_data/Training and Testing Sets/UNSW_NB15_testing-set.csv"
    
    try:
        X_train, X_test, y_train, y_test = pipeline.preprocess_real_dataset(
            "UNSW", [unsw_train], [unsw_test]
        )
        
        print(f"UNSW Dataset - Train: {X_train.shape}, Test: {X_test.shape}")
        print(f"Feature names: {len(pipeline.feature_names)}")
        
        # Save scaler
        pipeline.save_scaler()
        
    except Exception as e:
        print(f"Error processing UNSW dataset: {e}")
    
    # Example with CIC dataset
    cic_files = [
        "data/ML_data/MachineLearningCVE/Monday-WorkingHours.pcap_ISCX.csv",
        # Add more CIC files as needed
    ]
    
    try:
        X_train_cic, X_test_cic, y_train_cic, y_test_cic = pipeline.preprocess_real_dataset(
            "CIC", cic_files
        )
        
        print(f"CIC Dataset - Train: {X_train_cic.shape}, Test: {X_test_cic.shape}")
        print(f"Feature names: {len(pipeline.feature_names)}")
        
    except Exception as e:
        print(f"Error processing CIC dataset: {e}")
