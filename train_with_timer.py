"""
Training Script with Timer Display
Shows real-time progress during model training
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
import os
import sys
import time
import threading
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

class TrainingTimer:
    """Training progress timer"""
    
    def __init__(self):
        self.start_time = None
        self.current_task = ""
        self.stop_timer = False
        self.timer_thread = None
    
    def start_timer(self, task_name: str):
        """Start timer for a task"""
        self.start_time = time.time()
        self.current_task = task_name
        self.stop_timer = False
        
        # Start timer thread
        self.timer_thread = threading.Thread(target=self._display_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
        print(f"⏱️  Starting: {task_name}")
    
    def _display_timer(self):
        """Display elapsed time"""
        while not self.stop_timer and self.start_time:
            elapsed = time.time() - self.start_time
            mins, secs = divmod(int(elapsed), 60)
            hours, mins = divmod(mins, 60)
            
            # Create progress bar
            progress_chars = "⢹⢺⢼⢸⢰⢠⢀⡀⣀⣐⣒⣖⣶⣷⣾⣿"
            progress_idx = int(elapsed) % len(progress_chars)
            spinner = progress_chars[progress_idx]
            
            print(f"\r{spinner} {self.current_task}: {hours:02d}:{mins:02d}:{secs:02d}", end="", flush=True)
            time.sleep(1)
    
    def stop_task_timer(self):
        """Stop current timer"""
        self.stop_timer = True
        if self.start_time:
            elapsed = time.time() - self.start_time
            mins, secs = divmod(int(elapsed), 60)
            hours, mins = divmod(mins, 60)
            print(f"\r✅ {self.current_task} completed in {hours:02d}:{mins:02d}:{secs:02d}")
            self.start_time = None

class QuickEnsemble:
    """Quick ensemble for fast training"""
    
    def __init__(self):
        self.models = {}
        self.weights = {'isolation_forest': 0.6, 'one_class_svm': 0.4}
        self.threshold = 0.5
        self.is_trained = False
    
    def train_models(self, X_train_normal):
        """Train models with timer"""
        timer = TrainingTimer()
        
        # Train Isolation Forest
        timer.start_timer("Isolation Forest Training")
        iforest = IsolationForestModel()
        iforest.train(X_train_normal, contamination=0.1)
        self.models['isolation_forest'] = iforest
        timer.stop_task_timer()
        
        # Train One-Class SVM
        timer.start_timer("One-Class SVM Training")
        svm_model = OneClassSVMModel()
        svm_model.train(X_train_normal, nu=0.1)
        self.models['one_class_svm'] = svm_model
        timer.stop_task_timer()
        
        self.is_trained = True
        logger.info("Quick ensemble trained successfully")
    
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

def quick_train_unsw():
    """Quick training with UNSW dataset"""
    print("=" * 80)
    print("🚀 QUICK TRAINING - UNSW-NB15 DATASET")
    print("=" * 80)
    
    timer = TrainingTimer()
    
    # Load and preprocess data
    timer.start_timer("Data Loading & Preprocessing")
    
    pipeline = RealDataPipeline()
    unsw_train_path = "data/OneDrive_data/Training and Testing Sets/UNSW_NB15_training-set.csv"
    unsw_test_path = "data/OneDrive_data/Training and Testing Sets/UNSW_NB15_testing-set.csv"
    
    try:
        # Use smaller sample for quick training
        print("📊 Loading UNSW dataset (sample)...")
        train_df = pd.read_csv(unsw_train_path, nrows=10000)  # Sample 10K for quick training
        test_df = pd.read_csv(unsw_test_path, nrows=5000)     # Sample 5K for testing
        
        # Preprocess
        X_train, y_train = pipeline.preprocess_unsw_data(train_df, is_training=True)
        X_test, y_test = pipeline.preprocess_unsw_data(test_df, is_training=False)
        
        # Normalize
        X_train = pipeline.normalize_features(X_train, fit=True)
        X_test = pipeline.normalize_features(X_test, fit=False)
        
        # Prepare unsupervised data
        normal_mask = y_train == 0
        X_train_normal = X_train[normal_mask][:5000]  # Use 5K normal samples
        
        timer.stop_task_timer()
        
        print(f"✅ Data loaded: Train={X_train_normal.shape}, Test={X_test.shape}")
        print(f"   Attack rate: {np.mean(y_test):.3f}")
        
        # Train models
        print("\n🤖 Training Models...")
        ensemble = QuickEnsemble()
        ensemble.train_models(X_train_normal)
        
        # Evaluate
        timer.start_timer("Model Evaluation")
        results = ensemble.predict(X_test)
        
        from sklearn.metrics import classification_report, roc_auc_score
        
        predictions = results['final_predictions']
        scores = results['ensemble_score']
        
        # Calculate metrics
        accuracy = np.mean(predictions == y_test)
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, predictions, average='binary')
        auc = roc_auc_score(y_test, scores)
        
        timer.stop_task_timer()
        
        print(f"\n📈 Results:")
        print(f"   Accuracy: {accuracy:.3f}")
        print(f"   Precision: {precision:.3f}")
        print(f"   Recall: {recall:.3f}")
        print(f"   F1-Score: {f1:.3f}")
        print(f"   AUC-ROC: {auc:.3f}")
        
        # Save models
        timer.start_timer("Saving Models")
        ensemble.models['isolation_forest'].save_model()
        ensemble.models['one_class_svm'].save_model()
        pipeline.save_scaler()
        
        # Save config
        import joblib
        config = {
            'weights': ensemble.weights,
            'threshold': ensemble.threshold,
            'dataset': 'UNSW-NB15-Quick',
            'model_type': 'quick_ensemble',
            'metrics': {
                'accuracy': accuracy,
                'f1_score': f1,
                'auc_roc': auc
            }
        }
        os.makedirs('models', exist_ok=True)
        joblib.dump(config, 'models/quick_unsw_config.pkl')
        
        timer.stop_task_timer()
        
        print("✅ Models saved successfully!")
        return ensemble, pipeline, {'accuracy': accuracy, 'f1_score': f1, 'auc_roc': auc}
        
    except Exception as e:
        timer.stop_task_timer()
        print(f"❌ Error: {e}")
        return None, None, None

def quick_train_cic():
    """Quick training with CIC dataset"""
    print("\n" + "=" * 80)
    print("🚀 QUICK TRAINING - CIC-IDS2017 DATASET")
    print("=" * 80)
    
    timer = TrainingTimer()
    
    # Load and preprocess data
    timer.start_timer("Data Loading & Preprocessing")
    
    pipeline = RealDataPipeline()
    
    try:
        # Use smaller sample for quick training
        print("📊 Loading CIC dataset (sample)...")
        cic_files = [
            "data/ML_data/MachineLearningCVE/Monday-WorkingHours.pcap_ISCX.csv",
            "data/ML_data/MachineLearningCVE/Tuesday-WorkingHours.pcap_ISCX.csv"
        ]
        
        # Load samples
        dataframes = []
        for file_path in cic_files:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path, nrows=8000)  # Sample 8K per file
                df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('-', '_')
                dataframes.append(df)
        
        if not dataframes:
            raise ValueError("No CIC files found")
        
        combined_df = pd.concat(dataframes, ignore_index=True)
        
        # Preprocess
        X, y = pipeline.preprocess_cic_data(combined_df, is_training=True)
        
        # Split
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        # Normalize
        X_train = pipeline.normalize_features(X_train, fit=True)
        X_test = pipeline.normalize_features(X_test, fit=False)
        
        # Prepare unsupervised data
        normal_mask = y_train == 0
        X_train_normal = X_train[normal_mask][:4000]  # Use 4K normal samples
        
        timer.stop_task_timer()
        
        print(f"✅ Data loaded: Train={X_train_normal.shape}, Test={X_test.shape}")
        print(f"   Attack rate: {np.mean(y_test):.3f}")
        
        # Train models
        print("\n🤖 Training Models...")
        ensemble = QuickEnsemble()
        ensemble.train_models(X_train_normal)
        
        # Evaluate
        timer.start_timer("Model Evaluation")
        results = ensemble.predict(X_test)
        
        from sklearn.metrics import classification_report, roc_auc_score, precision_recall_fscore_support
        
        predictions = results['final_predictions']
        scores = results['ensemble_score']
        
        # Calculate metrics
        accuracy = np.mean(predictions == y_test)
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, predictions, average='binary')
        auc = roc_auc_score(y_test, scores)
        
        timer.stop_task_timer()
        
        print(f"\n📈 Results:")
        print(f"   Accuracy: {accuracy:.3f}")
        print(f"   Precision: {precision:.3f}")
        print(f"   Recall: {recall:.3f}")
        print(f"   F1-Score: {f1:.3f}")
        print(f"   AUC-ROC: {auc:.3f}")
        
        # Save models
        timer.start_timer("Saving Models")
        ensemble.models['isolation_forest'].save_model()
        ensemble.models['one_class_svm'].save_model()
        pipeline.save_scaler()
        
        # Save config
        import joblib
        config = {
            'weights': ensemble.weights,
            'threshold': ensemble.threshold,
            'dataset': 'CIC-IDS2017-Quick',
            'model_type': 'quick_ensemble',
            'metrics': {
                'accuracy': accuracy,
                'f1_score': f1,
                'auc_roc': auc
            }
        }
        os.makedirs('models', exist_ok=True)
        joblib.dump(config, 'models/quick_cic_config.pkl')
        
        timer.stop_task_timer()
        
        print("✅ Models saved successfully!")
        return ensemble, pipeline, {'accuracy': accuracy, 'f1_score': f1, 'auc_roc': auc}
        
    except Exception as e:
        timer.stop_task_timer()
        print(f"❌ Error: {e}")
        return None, None, None

def main():
    """Main training function with timer"""
    print("🛡️  ANTIGENA DEFENSE SYSTEM - QUICK TRAINING WITH TIMER")
    print("Fast training with real-time progress display")
    
    total_start_time = time.time()
    
    # Train UNSW
    unsw_results = quick_train_unsw()
    
    # Train CIC
    cic_results = quick_train_cic()
    
    # Total time
    total_elapsed = time.time() - total_start_time
    mins, secs = divmod(int(total_elapsed), 60)
    hours, mins = divmod(mins, 60)
    
    print("\n" + "=" * 80)
    print("🎉 TRAINING COMPLETED")
    print("=" * 80)
    print(f"⏱️  Total Time: {hours:02d}:{mins:02d}:{secs:02d}")
    
    # Compare results
    print(f"\n📊 Results Summary:")
    if unsw_results[2]:
        print(f"   UNSW-NB15: F1={unsw_results[2]['f1_score']:.3f}, AUC={unsw_results[2]['auc_roc']:.3f}")
    if cic_results[2]:
        print(f"   CIC-IDS2017: F1={cic_results[2]['f1_score']:.3f}, AUC={cic_results[2]['auc_roc']:.3f}")
    
    # Best model
    best_model = None
    best_f1 = 0
    
    for name, (_, _, metrics) in [('UNSW-NB15', unsw_results), ('CIC-IDS2017', cic_results)]:
        if metrics and metrics['f1_score'] > best_f1:
            best_f1 = metrics['f1_score']
            best_model = name
    
    if best_model:
        print(f"\n🏆 Best Model: {best_model} (F1: {best_f1:.3f})")
        print(f"✅ Ready for deployment!")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Test models: python test_trained_models.py")
    print(f"   2. Start API: python antigena_defense/api/api.py")
    print(f"   3. Deploy to production")

if __name__ == "__main__":
    main()
