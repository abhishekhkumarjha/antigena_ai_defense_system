"""
Simplified Training Script - No TensorFlow Required
Uses only scikit-learn models for real dataset training
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime
import os
import sys
from typing import List, Tuple

# Add antigena_defense directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'antigena_defense'))

from antigena_defense.utils.real_data_preprocessing import RealDataPipeline
from antigena_defense.models.isolation_forest import IsolationForestModel
from antigena_defense.models.one_class_svm import OneClassSVMModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleEnsemble:
    """Simple ensemble without autoencoder"""
    
    def __init__(self):
        self.models = {}
        self.weights = {'isolation_forest': 0.6, 'one_class_svm': 0.4}
        self.threshold = 0.5
        self.is_trained = False
    
    def train_models(self, X_train_normal):
        """Train individual models"""
        # Train Isolation Forest
        iforest = IsolationForestModel()
        iforest.train(X_train_normal, contamination=0.1)
        self.models['isolation_forest'] = iforest
        
        # Train One-Class SVM
        svm_model = OneClassSVMModel()
        svm_model.train(X_train_normal, nu=0.1)
        self.models['one_class_svm'] = svm_model
        
        self.is_trained = True
        logger.info("Simple ensemble trained successfully")
    
    def predict(self, X):
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Models not trained")
        
        # Get predictions from both models
        iforest_results = self.models['isolation_forest'].predict_iforest(X)
        svm_results = self.models['one_class_svm'].predict_svm(X)
        
        # Combine scores
        ensemble_scores = (
            self.weights['isolation_forest'] * iforest_results['normalized_scores'] +
            self.weights['one_class_svm'] * svm_results['normalized_scores']
        )
        
        # Make final predictions
        final_predictions = (ensemble_scores > self.threshold).astype(int)
        
        return {
            'ensemble_score': ensemble_scores,
            'final_predictions': final_predictions,
            'individual_models': {
                'isolation_forest': iforest_results,
                'one_class_svm': svm_results
            }
        }

def train_with_unsw_simple():
    """Train simplified models with UNSW dataset"""
    print("=" * 80)
    print("🛡️  TRAINING WITH UNSW-NB15 DATASET (SIMPLIFIED)")
    print("=" * 80)
    
    # Initialize pipeline
    pipeline = RealDataPipeline()
    
    # Dataset paths
    unsw_train_path = "data/OneDrive_data/Training and Testing Sets/UNSW_NB15_training-set.csv"
    unsw_test_path = "data/OneDrive_data/Training and Testing Sets/UNSW_NB15_testing-set.csv"
    
    try:
        # Preprocess data
        X_train, X_test, y_train, y_test = pipeline.preprocess_real_dataset(
            "UNSW", [unsw_train_path], [unsw_test_path]
        )
        
        print(f"✅ UNSW Data Loaded:")
        print(f"   Training: {X_train.shape}")
        print(f"   Testing: {X_test.shape}")
        print(f"   Features: {len(pipeline.feature_names)}")
        print(f"   Attack rate in test: {np.mean(y_test):.3f}")
        
        # Prepare unsupervised training data (normal only)
        X_train_normal, X_mixed_test = pipeline.prepare_unsupervised_data(X_train, y_train)
        
        # Train simple ensemble
        print("\n🤖 TRAINING MODELS...")
        ensemble = SimpleEnsemble()
        ensemble.train_models(X_train_normal)
        
        # Evaluate on test set
        print("\n📈 EVALUATING PERFORMANCE...")
        results = ensemble.predict(X_test)
        
        from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
        
        predictions = results['final_predictions']
        scores = results['ensemble_score']
        
        print(f"Anomaly rate in test: {np.mean(predictions):.3f}")
        print(f"Average ensemble score: {np.mean(scores):.3f}")
        
        print("\nClassification Report:")
        print(classification_report(y_test, predictions))
        
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, predictions))
        
        print(f"\nROC AUC Score: {roc_auc_score(y_test, scores):.3f}")
        
        # Save models
        print("\n💾 SAVING MODELS...")
        ensemble.models['isolation_forest'].save_model()
        ensemble.models['one_class_svm'].save_model()
        pipeline.save_scaler()
        
        # Save ensemble config
        import joblib
        config = {
            'weights': ensemble.weights,
            'threshold': ensemble.threshold,
            'model_type': 'simple_ensemble'
        }
        os.makedirs('models', exist_ok=True)
        joblib.dump(config, 'models/simple_ensemble_config.pkl')
        
        print("✅ UNSW Training Complete!")
        return ensemble, pipeline
        
    except Exception as e:
        logger.error(f"Error training with UNSW dataset: {e}")
        print(f"❌ Error: {e}")
        return None, None

def train_with_cic_simple():
    """Train simplified models with CIC dataset"""
    print("=" * 80)
    print("🛡️  TRAINING WITH CIC-IDS2017 DATASET (SIMPLIFIED)")
    print("=" * 80)
    
    # Initialize pipeline
    pipeline = RealDataPipeline()
    
    # Dataset paths (use a few files for demonstration)
    cic_files = [
        "data/ML_data/MachineLearningCVE/Monday-WorkingHours.pcap_ISCX.csv",
        "data/ML_data/MachineLearningCVE/Tuesday-WorkingHours.pcap_ISCX.csv"
    ]
    
    try:
        # Preprocess data
        X_train, X_test, y_train, y_test = pipeline.preprocess_real_dataset("CIC", cic_files)
        
        print(f"✅ CIC Data Loaded:")
        print(f"   Training: {X_train.shape}")
        print(f"   Testing: {X_test.shape}")
        print(f"   Features: {len(pipeline.feature_names)}")
        print(f"   Attack rate in test: {np.mean(y_test):.3f}")
        
        # Prepare unsupervised training data (normal only)
        X_train_normal, X_mixed_test = pipeline.prepare_unsupervised_data(X_train, y_train)
        
        # Train simple ensemble
        print("\n🤖 TRAINING MODELS...")
        ensemble = SimpleEnsemble()
        ensemble.train_models(X_train_normal)
        
        # Evaluate on test set
        print("\n📈 EVALUATING PERFORMANCE...")
        results = ensemble.predict(X_test)
        
        from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
        
        predictions = results['final_predictions']
        scores = results['ensemble_score']
        
        print(f"Anomaly rate in test: {np.mean(predictions):.3f}")
        print(f"Average ensemble score: {np.mean(scores):.3f}")
        
        print("\nClassification Report:")
        print(classification_report(y_test, predictions))
        
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, predictions))
        
        print(f"\nROC AUC Score: {roc_auc_score(y_test, scores):.3f}")
        
        # Save models
        print("\n💾 SAVING MODELS...")
        ensemble.models['isolation_forest'].save_model()
        ensemble.models['one_class_svm'].save_model()
        pipeline.save_scaler()
        
        # Save ensemble config
        import joblib
        config = {
            'weights': ensemble.weights,
            'threshold': ensemble.threshold,
            'model_type': 'simple_ensemble'
        }
        os.makedirs('models', exist_ok=True)
        joblib.dump(config, 'models/simple_ensemble_config.pkl')
        
        print("✅ CIC Training Complete!")
        return ensemble, pipeline
        
    except Exception as e:
        logger.error(f"Error training with CIC dataset: {e}")
        print(f"❌ Error: {e}")
        return None, None

def test_predictions(ensemble, pipeline):
    """Test predictions with trained models"""
    print("\n⚡ TESTING PREDICTIONS")
    print("-" * 50)
    
    # Load some test data
    if pipeline.dataset_type == "UNSW":
        test_path = "data/OneDrive_data/Training and Testing Sets/UNSW_NB15_testing-set.csv"
        test_df = pd.read_csv(test_path)
        X_test, y_test = pipeline.preprocess_unsw_data(test_df, is_training=False)
    else:
        # Use CIC data
        cic_file = "data/ML_data/MachineLearningCVE/Monday-WorkingHours.pcap_ISCX.csv"
        test_df = pd.read_csv(cic_file)
        test_df.columns = test_df.columns.str.strip().str.replace(' ', '_').str.replace('-', '_')
        X_test, y_test = pipeline.preprocess_cic_data(test_df, is_training=False)
    
    # Sample a few instances for testing
    sample_indices = np.random.choice(len(X_test), 5, replace=False)
    
    for i, idx in enumerate(sample_indices):
        sample = X_test[idx].reshape(1, -1)
        true_label = "ATTACK" if y_test[idx] == 1 else "NORMAL"
        
        # Preprocess
        sample_processed = pipeline.preprocess_real_time(sample)
        
        # Predict
        results = ensemble.predict(sample_processed)
        
        score = results['ensemble_score'][0]
        prediction = results['final_predictions'][0]
        predicted_label = "ATTACK" if prediction == 1 else "NORMAL"
        
        print(f"Sample {i+1}:")
        print(f"  True: {true_label}, Predicted: {predicted_label}")
        print(f"  Score: {score:.3f}")
        print(f"  Confidence: {max(score, 1-score):.3f}")
        print()

def main():
    """Main training function"""
    print("🚀 ANTIGENA DEFENSE SYSTEM - SIMPLIFIED TRAINING")
    print("Select dataset to train with:")
    print("1. UNSW-NB15 Dataset")
    print("2. CIC-IDS2017 Dataset")
    print("3. Both Datasets")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == "1":
        ensemble, pipeline = train_with_unsw_simple()
        if ensemble:
            test_predictions(ensemble, pipeline)
    
    elif choice == "2":
        ensemble, pipeline = train_with_cic_simple()
        if ensemble:
            test_predictions(ensemble, pipeline)
    
    elif choice == "3":
        # Train both
        print("\n" + "="*80)
        print("TRAINING BOTH DATASETS")
        print("="*80)
        
        # Train UNSW
        ensemble_unsw, pipeline_unsw = train_with_unsw_simple()
        
        # Train CIC
        ensemble_cic, pipeline_cic = train_with_cic_simple()
        
        # Test with the better performing model
        if ensemble_unsw and ensemble_cic:
            print("\nBoth models trained successfully!")
            choice2 = input("Test with UNSW (1) or CIC (2) model? ")
            
            if choice2 == "1":
                test_predictions(ensemble_unsw, pipeline_unsw)
            elif choice2 == "2":
                test_predictions(ensemble_cic, pipeline_cic)
    
    else:
        print("Invalid choice!")
        return
    
    print("\n" + "="*80)
    print("🎉 TRAINING COMPLETED!")
    print("="*80)
    print("\nNext steps:")
    print("1. Models saved in models/ directory")
    print("2. Scaler saved for preprocessing")
    print("3. Ready for real-time predictions")
    print("4. To use with API: modify api.py to load simple ensemble")

if __name__ == "__main__":
    main()
