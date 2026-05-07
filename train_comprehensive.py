"""
Comprehensive Training Pipeline for Antigena Defense System
Uses both UNSW-NB15 and CIC-IDS2017 datasets for robust training
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime
import os
import sys
from typing import List, Tuple, Dict, Any
import warnings
warnings.filterwarnings('ignore')

# Add antigena_defense directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'antigena_defense'))

from antigena_defense.utils.real_data_preprocessing import RealDataPipeline
from antigena_defense.models.isolation_forest import IsolationForestModel
from antigena_defense.models.one_class_svm import OneClassSVMModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveEnsemble:
    """Comprehensive ensemble with multiple models"""
    
    def __init__(self):
        self.models = {}
        self.weights = {'isolation_forest': 0.6, 'one_class_svm': 0.4}
        self.threshold = 0.5
        self.is_trained = False
        self.training_history = {}
    
    def train_models(self, X_train_normal):
        """Train individual models"""
        logger.info("Training comprehensive ensemble models...")
        
        # Train Isolation Forest
        logger.info("Training Isolation Forest...")
        iforest = IsolationForestModel()
        iforest.train(X_train_normal, contamination=0.1)
        self.models['isolation_forest'] = iforest
        
        # Train One-Class SVM
        logger.info("Training One-Class SVM...")
        svm_model = OneClassSVMModel()
        svm_model.train(X_train_normal, nu=0.1)
        self.models['one_class_svm'] = svm_model
        
        self.is_trained = True
        logger.info("Comprehensive ensemble trained successfully")
    
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
    
    def optimize_threshold(self, X_val, y_val):
        """Optimize threshold using validation set"""
        logger.info("Optimizing threshold...")
        
        results = self.predict(X_val)
        scores = results['ensemble_score']
        
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
        
        return best_threshold, best_f1

def load_and_preprocess_unsw():
    """Load and preprocess UNSW-NB15 dataset"""
    logger.info("Loading UNSW-NB15 dataset...")
    
    pipeline = RealDataPipeline()
    
    # Dataset paths
    unsw_train_path = "data/OneDrive_data/Training and Testing Sets/UNSW_NB15_training-set.csv"
    unsw_test_path = "data/OneDrive_data/Training and Testing Sets/UNSW_NB15_testing-set.csv"
    
    try:
        # Preprocess data
        X_train, X_test, y_train, y_test = pipeline.preprocess_real_dataset(
            "UNSW", [unsw_train_path], [unsw_test_path]
        )
        
        logger.info(f"UNSW Data Loaded - Train: {X_train.shape}, Test: {X_test.shape}")
        logger.info(f"Attack rate in test: {np.mean(y_test):.3f}")
        
        # Prepare unsupervised training data
        X_train_normal, X_mixed_test = pipeline.prepare_unsupervised_data(X_train, y_train)
        
        return X_train_normal, X_test, y_test, pipeline
        
    except Exception as e:
        logger.error(f"Error loading UNSW dataset: {e}")
        return None, None, None, None

def load_and_preprocess_cic():
    """Load and preprocess CIC-IDS2017 dataset"""
    logger.info("Loading CIC-IDS2017 dataset...")
    
    pipeline = RealDataPipeline()
    
    # Use multiple CIC files for better coverage
    cic_files = [
        "data/ML_data/MachineLearningCVE/Monday-WorkingHours.pcap_ISCX.csv",
        "data/ML_data/MachineLearningCVE/Tuesday-WorkingHours.pcap_ISCX.csv",
        "data/ML_data/MachineLearningCVE/Wednesday-workingHours.pcap_ISCX.csv",
        "data/ML_data/MachineLearningCVE/Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv"
    ]
    
    try:
        # Preprocess data
        X_train, X_test, y_train, y_test = pipeline.preprocess_real_dataset("CIC", cic_files)
        
        logger.info(f"CIC Data Loaded - Train: {X_train.shape}, Test: {X_test.shape}")
        logger.info(f"Attack rate in test: {np.mean(y_test):.3f}")
        
        # Prepare unsupervised training data
        X_train_normal, X_mixed_test = pipeline.prepare_unsupervised_data(X_train, y_train)
        
        return X_train_normal, X_test, y_test, pipeline
        
    except Exception as e:
        logger.error(f"Error loading CIC dataset: {e}")
        return None, None, None, None

def train_and_evaluate_dataset(dataset_name: str, X_train_normal, X_test, y_test, pipeline):
    """Train and evaluate models on a specific dataset"""
    logger.info(f"Training and evaluating on {dataset_name}...")
    
    # Create validation set
    from sklearn.model_selection import train_test_split
    
    # Use part of test set for validation
    X_val, X_test_final, y_val, y_test_final = train_test_split(
        X_test, y_test, test_size=0.5, random_state=42, stratify=y_test
    )
    
    # Train ensemble
    ensemble = ComprehensiveEnsemble()
    ensemble.train_models(X_train_normal)
    
    # Optimize threshold
    ensemble.optimize_threshold(X_val, y_val)
    
    # Evaluate on test set
    logger.info(f"Evaluating {dataset_name} performance...")
    results = ensemble.predict(X_test_final)
    
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_fscore_support
    
    predictions = results['final_predictions']
    scores = results['ensemble_score']
    
    # Calculate metrics
    precision, recall, f1, _ = precision_recall_fscore_support(y_test_final, predictions, average='binary')
    auc = roc_auc_score(y_test_final, scores)
    
    metrics = {
        'dataset': dataset_name,
        'accuracy': np.mean(predictions == y_test_final),
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'auc_roc': auc,
        'anomaly_rate': np.mean(predictions),
        'avg_score': np.mean(scores),
        'threshold': ensemble.threshold
    }
    
    logger.info(f"{dataset_name} Results:")
    logger.info(f"  Accuracy: {metrics['accuracy']:.3f}")
    logger.info(f"  Precision: {metrics['precision']:.3f}")
    logger.info(f"  Recall: {metrics['recall']:.3f}")
    logger.info(f"  F1-Score: {metrics['f1_score']:.3f}")
    logger.info(f"  AUC-ROC: {metrics['auc_roc']:.3f}")
    logger.info(f"  Threshold: {metrics['threshold']:.3f}")
    
    return ensemble, pipeline, metrics

def train_comprehensive_system():
    """Train comprehensive system with multiple datasets"""
    print("=" * 80)
    print("🚀 COMPREHENSIVE ANTIGENA DEFENSE SYSTEM TRAINING")
    print("=" * 80)
    
    results = {}
    trained_ensembles = {}
    
    # Train on UNSW dataset
    print("\n" + "="*60)
    print("TRAINING ON UNSW-NB15 DATASET")
    print("="*60)
    
    X_train_unsw, X_test_unsw, y_test_unsw, pipeline_unsw = load_and_preprocess_unsw()
    
    if X_train_unsw is not None:
        ensemble_unsw, _, metrics_unsw = train_and_evaluate_dataset(
            "UNSW-NB15", X_train_unsw, X_test_unsw, y_test_unsw, pipeline_unsw
        )
        results['UNSW-NB15'] = metrics_unsw
        trained_ensembles['UNSW-NB15'] = (ensemble_unsw, pipeline_unsw)
    else:
        logger.error("Failed to load UNSW dataset")
    
    # Train on CIC dataset
    print("\n" + "="*60)
    print("TRAINING ON CIC-IDS2017 DATASET")
    print("="*60)
    
    X_train_cic, X_test_cic, y_test_cic, pipeline_cic = load_and_preprocess_cic()
    
    if X_train_cic is not None:
        ensemble_cic, _, metrics_cic = train_and_evaluate_dataset(
            "CIC-IDS2017", X_train_cic, X_test_cic, y_test_cic, pipeline_cic
        )
        results['CIC-IDS2017'] = metrics_cic
        trained_ensembles['CIC-IDS2017'] = (ensemble_cic, pipeline_cic)
    else:
        logger.error("Failed to load CIC dataset")
    
    # Compare results
    print("\n" + "="*80)
    print("📊 COMPARATIVE RESULTS")
    print("="*80)
    
    if results:
        results_df = pd.DataFrame(results).T
        print(results_df.round(3))
        
        # Find best performing model
        best_f1_idx = results_df['f1_score'].idxmax()
        best_auc_idx = results_df['auc_roc'].idxmax()
        
        print(f"\n🏆 Best F1-Score: {best_f1_idx} ({results_df.loc[best_f1_idx, 'f1_score']:.3f})")
        print(f"🏆 Best AUC-ROC: {best_auc_idx} ({results_df.loc[best_auc_idx, 'auc_roc']:.3f})")
    
    # Save best model
    if trained_ensembles:
        print("\n" + "="*60)
        print("💾 SAVING BEST MODELS")
        print("="*60)
        
        # Save all trained models
        for dataset_name, (ensemble, pipeline) in trained_ensembles.items():
            try:
                # Save models
                ensemble.models['isolation_forest'].save_model()
                ensemble.models['one_class_svm'].save_model()
                pipeline.save_scaler()
                
                # Save ensemble config
                import joblib
                config = {
                    'weights': ensemble.weights,
                    'threshold': ensemble.threshold,
                    'dataset': dataset_name,
                    'model_type': 'comprehensive_ensemble'
                }
                os.makedirs('models', exist_ok=True)
                config_path = f"models/{dataset_name.lower().replace('-', '_')}_config.pkl"
                joblib.dump(config, config_path)
                
                logger.info(f"Saved {dataset_name} models successfully")
                
            except Exception as e:
                logger.error(f"Error saving {dataset_name} models: {e}")
    
    return trained_ensembles, results

def test_cross_dataset_performance(trained_ensembles):
    """Test models on different datasets (cross-validation)"""
    print("\n" + "="*80)
    print("🔄 CROSS-DATASET TESTING")
    print("="*80)
    
    datasets = {}
    
    # Load all datasets for cross-testing
    X_train_unsw, X_test_unsw, y_test_unsw, pipeline_unsw = load_and_preprocess_unsw()
    X_train_cic, X_test_cic, y_test_cic, pipeline_cic = load_and_preprocess_cic()
    
    if X_test_unsw is not None:
        datasets['UNSW-NB15'] = (X_test_unsw, y_test_unsw, pipeline_unsw)
    if X_test_cic is not None:
        datasets['CIC-IDS2017'] = (X_test_cic, y_test_cic, pipeline_cic)
    
    cross_results = {}
    
    for train_dataset, (ensemble, _) in trained_ensembles.items():
        print(f"\nTesting {train_dataset} model on all datasets...")
        
        cross_results[train_dataset] = {}
        
        for test_dataset, (X_test, y_test, pipeline) in datasets.items():
            try:
                # Preprocess test data with training pipeline
                if train_dataset == 'UNSW-NB15':
                    X_test_processed = pipeline_unsw.preprocess_real_time(X_test)
                else:
                    X_test_processed = pipeline_cic.preprocess_real_time(X_test)
                
                # Make predictions
                results = ensemble.predict(X_test_processed)
                predictions = results['final_predictions']
                scores = results['ensemble_score']
                
                # Calculate metrics
                from sklearn.metrics import classification_report, roc_auc_score
                precision, recall, f1, _ = precision_recall_fscore_support(y_test, predictions, average='binary')
                auc = roc_auc_score(y_test, scores)
                
                cross_results[train_dataset][test_dataset] = {
                    'accuracy': np.mean(predictions == y_test),
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1,
                    'auc_roc': auc
                }
                
                print(f"  {test_dataset}: F1={f1:.3f}, AUC={auc:.3f}")
                
            except Exception as e:
                logger.error(f"Error testing {train_dataset} on {test_dataset}: {e}")
                cross_results[train_dataset][test_dataset] = None
    
    # Display cross-dataset results
    if cross_results:
        print("\n" + "="*60)
        print("CROSS-DATASET PERFORMANCE MATRIX")
        print("="*60)
        
        for train_dataset, test_results in cross_results.items():
            print(f"\n{train_dataset} model performance:")
            for test_dataset, metrics in test_results.items():
                if metrics:
                    print(f"  {test_dataset}: F1={metrics['f1_score']:.3f}, AUC={metrics['auc_roc']:.3f}")
    
    return cross_results

def main():
    """Main training function"""
    print("🛡️  ANTIGENA DEFENSE SYSTEM - COMPREHENSIVE TRAINING")
    print("Training with multiple real-world cybersecurity datasets")
    
    # Train comprehensive system
    trained_ensembles, results = train_comprehensive_system()
    
    if trained_ensembles:
        # Test cross-dataset performance
        cross_results = test_cross_dataset_performance(trained_ensembles)
        
        # Final summary
        print("\n" + "="*80)
        print("🎉 TRAINING COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        print("\n📋 Summary:")
        print(f"✅ Trained {len(trained_ensembles)} ensemble models")
        print(f"✅ Models saved in 'models/' directory")
        print(f"✅ Cross-dataset testing completed")
        
        print("\n🚀 Next Steps:")
        print("1. Start API server: python antigena_defense/api/api.py")
        print("2. Test predictions with real data")
        print("3. Deploy in production environment")
        print("4. Monitor performance and retrain as needed")
        
        # Recommend best model
        if results:
            best_model = max(results.keys(), key=lambda k: results[k]['f1_score'])
            print(f"\n💡 Recommended model for deployment: {best_model}")
            print(f"   F1-Score: {results[best_model]['f1_score']:.3f}")
            print(f"   AUC-ROC: {results[best_model]['auc_roc']:.3f}")
    
    else:
        print("\n❌ Training failed. Please check dataset paths and dependencies.")

if __name__ == "__main__":
    main()
