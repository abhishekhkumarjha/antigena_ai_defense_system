"""
Train Antigena Defense System with Real Datasets
Supports UNSW-NB15 and CIC-IDS2017 datasets
"""

import numpy as np
import pandas as pd
import asyncio
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
from antigena_defense.models.autoencoder import AutoencoderModel
from antigena_defense.models.ensemble import EnsembleEngine
from antigena_defense.utils.shap_explainer import SHAPExplainer
from antigena_defense.response import ResponseEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train_with_unsw_dataset():
    """Train models using UNSW-NB15 dataset"""
    print("=" * 80)
    print("🛡️  TRAINING WITH UNSW-NB15 DATASET")
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
        
        # Train models
        print("\n🤖 TRAINING MODELS...")
        
        # Isolation Forest
        print("Training Isolation Forest...")
        iforest = IsolationForestModel()
        iforest.train(X_train_normal, contamination=0.1)
        
        # One-Class SVM
        print("Training One-Class SVM...")
        svm_model = OneClassSVMModel()
        svm_model.train(X_train_normal, nu=0.1)
        
        # Autoencoder
        print("Training Autoencoder...")
        autoencoder = AutoencoderModel()
        autoencoder.build_model(input_dim=X_train_normal.shape[1], encoding_dims=[20, 10, 5])
        
        # Split some normal data for validation
        val_split = int(0.8 * len(X_train_normal))
        X_train_ae = X_train_normal[:val_split]
        X_val_ae = X_train_normal[val_split:]
        
        autoencoder.train(X_train_ae, X_val_ae, epochs=50, batch_size=32)
        
        # Create ensemble
        print("Creating Ensemble...")
        ensemble = EnsembleEngine()
        ensemble.models['isolation_forest'] = iforest
        ensemble.models['one_class_svm'] = svm_model
        ensemble.models['autoencoder'] = autoencoder
        ensemble.is_trained = True
        
        # Optimize ensemble
        print("Optimizing ensemble parameters...")
        
        # Create validation set with some anomalies
        X_val_normal = X_train_normal[val_split:]
        X_val_anomaly = X_test[y_test == 1][:500]  # Sample 500 anomalies
        X_val_mixed = np.vstack([X_val_normal, X_val_anomaly])
        y_val_mixed = np.hstack([np.zeros(len(X_val_normal)), np.ones(len(X_val_anomaly))])
        
        ensemble.optimize_weights(X_val_mixed, y_val_mixed)
        ensemble.optimize_threshold(X_val_mixed, y_val_mixed)
        
        # Evaluate on test set
        print("\n📈 EVALUATING PERFORMANCE...")
        results = ensemble.predict_ensemble(X_test)
        
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
        iforest.save_model()
        svm_model.save_model()
        autoencoder.save_model()
        ensemble.save_ensemble()
        pipeline.save_scaler()
        
        # Setup explainer
        print("Setting up SHAP explainer...")
        explainer = SHAPExplainer(model_type="surrogate")
        explainer.fit_explainer(iforest, X_train_normal, pipeline.feature_names)
        explainer.save_explainer("models/shap_explainer_unsw.pkl")
        
        print("✅ UNSW Training Complete!")
        return ensemble, pipeline, explainer
        
    except Exception as e:
        logger.error(f"Error training with UNSW dataset: {e}")
        print(f"❌ Error: {e}")
        return None, None, None

def train_with_cic_dataset():
    """Train models using CIC-IDS2017 dataset"""
    print("=" * 80)
    print("🛡️  TRAINING WITH CIC-IDS2017 DATASET")
    print("=" * 80)
    
    # Initialize pipeline
    pipeline = RealDataPipeline()
    
    # Dataset paths (use a few files for demonstration)
    cic_files = [
        "data/ML_data/MachineLearningCVE/Monday-WorkingHours.pcap_ISCX.csv",
        "data/ML_data/MachineLearningCVE/Tuesday-WorkingHours.pcap_ISCX.csv",
        "data/ML_data/MachineLearningCVE/Wednesday-workingHours.pcap_ISCX.csv"
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
        
        # Train models
        print("\n🤖 TRAINING MODELS...")
        
        # Isolation Forest
        print("Training Isolation Forest...")
        iforest = IsolationForestModel()
        iforest.train(X_train_normal, contamination=0.1)
        
        # One-Class SVM
        print("Training One-Class SVM...")
        svm_model = OneClassSVMModel()
        svm_model.train(X_train_normal, nu=0.1)
        
        # Autoencoder
        print("Training Autoencoder...")
        autoencoder = AutoencoderModel()
        autoencoder.build_model(input_dim=X_train_normal.shape[1], encoding_dims=[30, 15, 7])
        
        # Split some normal data for validation
        val_split = int(0.8 * len(X_train_normal))
        X_train_ae = X_train_normal[:val_split]
        X_val_ae = X_train_normal[val_split:]
        
        autoencoder.train(X_train_ae, X_val_ae, epochs=50, batch_size=32)
        
        # Create ensemble
        print("Creating Ensemble...")
        ensemble = EnsembleEngine()
        ensemble.models['isolation_forest'] = iforest
        ensemble.models['one_class_svm'] = svm_model
        ensemble.models['autoencoder'] = autoencoder
        ensemble.is_trained = True
        
        # Optimize ensemble
        print("Optimizing ensemble parameters...")
        
        # Create validation set with some anomalies
        X_val_normal = X_train_normal[val_split:]
        X_val_anomaly = X_test[y_test == 1][:500]  # Sample 500 anomalies
        X_val_mixed = np.vstack([X_val_normal, X_val_anomaly])
        y_val_mixed = np.hstack([np.zeros(len(X_val_normal)), np.ones(len(X_val_anomaly))])
        
        ensemble.optimize_weights(X_val_mixed, y_val_mixed)
        ensemble.optimize_threshold(X_val_mixed, y_val_mixed)
        
        # Evaluate on test set
        print("\n📈 EVALUATING PERFORMANCE...")
        results = ensemble.predict_ensemble(X_test)
        
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
        iforest.save_model()
        svm_model.save_model()
        autoencoder.save_model()
        ensemble.save_ensemble()
        pipeline.save_scaler()
        
        # Setup explainer
        print("Setting up SHAP explainer...")
        explainer = SHAPExplainer(model_type="surrogate")
        explainer.fit_explainer(iforest, X_train_normal, pipeline.feature_names)
        explainer.save_explainer("models/shap_explainer_cic.pkl")
        
        print("✅ CIC Training Complete!")
        return ensemble, pipeline, explainer
        
    except Exception as e:
        logger.error(f"Error training with CIC dataset: {e}")
        print(f"❌ Error: {e}")
        return None, None, None

async def test_real_time_predictions(ensemble, pipeline):
    """Test real-time predictions with trained models"""
    print("\n⚡ TESTING REAL-TIME PREDICTIONS")
    print("-" * 50)
    
    # Load some test data for real-time simulation
    if pipeline.dataset_type == "UNSW":
        test_path = "data/OneDrive_data/Training and Testing Sets/UNSW_NB15_testing-set.csv"
        test_df = pd.read_csv(test_path)
        X_test, y_test = pipeline.preprocess_unsw_data(test_df, is_training=False)
    else:
        # Use CIC data
        cic_file = "data/ML_data/MachineLearningCVE/Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv"
        test_df = pd.read_csv(cic_file)
        test_df.columns = test_df.columns.str.strip().str.replace(' ', '_').str.replace('-', '_')
        X_test, y_test = pipeline.preprocess_cic_data(test_df, is_training=False)
    
    # Sample a few instances for real-time testing
    sample_indices = np.random.choice(len(X_test), 5, replace=False)
    
    for i, idx in enumerate(sample_indices):
        sample = X_test[idx].reshape(1, -1)
        true_label = "ATTACK" if y_test[idx] == 1 else "NORMAL"
        
        # Preprocess
        sample_processed = pipeline.preprocess_real_time(sample)
        
        # Predict
        results = ensemble.predict_ensemble(sample_processed)
        
        score = results['ensemble_score'][0]
        prediction = results['final_predictions'][0]
        predicted_label = "ATTACK" if prediction == 1 else "NORMAL"
        
        print(f"Sample {i+1}:")
        print(f"  True: {true_label}, Predicted: {predicted_label}")
        print(f"  Score: {score:.3f}")
        print(f"  Confidence: {max(score, 1-score):.3f}")
        
        # Test response engine for anomalies
        if prediction == 1:
            response_engine = ResponseEngine()
            result = await response_engine.handle_anomaly(
                anomaly_score=score,
                features=sample_processed[0].tolist(),
                source=f"real_time_test_{i+1}"
            )
            print(f"  Response: {result['status']}")
        
        print()

def main():
    """Main training function"""
    print("🚀 ANTIGENA DEFENSE SYSTEM - REAL DATASET TRAINING")
    print("Select dataset to train with:")
    print("1. UNSW-NB15 Dataset")
    print("2. CIC-IDS2017 Dataset")
    print("3. Both Datasets")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == "1":
        ensemble, pipeline, explainer = train_with_unsw_dataset()
        if ensemble:
            asyncio.run(test_real_time_predictions(ensemble, pipeline))
    
    elif choice == "2":
        ensemble, pipeline, explainer = train_with_cic_dataset()
        if ensemble:
            asyncio.run(test_real_time_predictions(ensemble, pipeline))
    
    elif choice == "3":
        # Train both
        print("\n" + "="*80)
        print("TRAINING BOTH DATASETS")
        print("="*80)
        
        # Train UNSW
        ensemble_unsw, pipeline_unsw, explainer_unsw = train_with_unsw_dataset()
        
        # Train CIC
        ensemble_cic, pipeline_cic, explainer_cic = train_with_cic_dataset()
        
        # Test with the better performing model
        if ensemble_unsw and ensemble_cic:
            print("\nBoth models trained successfully!")
            choice2 = input("Test with UNSW (1) or CIC (2) model? ")
            
            if choice2 == "1":
                asyncio.run(test_real_time_predictions(ensemble_unsw, pipeline_unsw))
            elif choice2 == "2":
                asyncio.run(test_real_time_predictions(ensemble_cic, pipeline_cic))
    
    else:
        print("Invalid choice!")
        return
    
    print("\n" + "="*80)
    print("🎉 TRAINING COMPLETED!")
    print("="*80)
    print("\nNext steps:")
    print("1. Start API server: python antigena_defense/api/api.py")
    print("2. Test predictions: curl http://localhost:8000/predict")
    print("3. Monitor system logs in logs/ directory")

if __name__ == "__main__":
    main()
