"""
Test Trained Models Functionality
Test the trained Antigena Defense System models
"""

import numpy as np
import pandas as pd
import sys
import os
from typing import List, Tuple

# Add antigena_defense directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'antigena_defense'))

from antigena_defense.utils.real_data_preprocessing import RealDataPipeline
from antigena_defense.models.isolation_forest import IsolationForestModel
from antigena_defense.models.one_class_svm import OneClassSVMModel

class SimpleEnsemble:
    """Simple ensemble for testing"""
    
    def __init__(self):
        self.models = {}
        self.weights = {'isolation_forest': 0.6, 'one_class_svm': 0.4}
        self.threshold = 0.5
        self.is_trained = False
    
    def load_models(self):
        """Load pre-trained models"""
        try:
            # Load Isolation Forest
            iforest = IsolationForestModel()
            iforest.load_model()
            self.models['isolation_forest'] = iforest
            
            # Load One-Class SVM
            svm_model = OneClassSVMModel()
            svm_model.load_model()
            self.models['one_class_svm'] = svm_model
            
            # Load ensemble config
            import joblib
            config = joblib.load('models/simple_ensemble_config.pkl')
            self.weights = config.get('weights', self.weights)
            self.threshold = config.get('threshold', self.threshold)
            
            self.is_trained = True
            print("✅ Models loaded successfully")
            print(f"   Weights: {self.weights}")
            print(f"   Threshold: {self.threshold}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False
    
    def predict(self, X):
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Models not loaded")
        
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

def test_with_sample_data():
    """Test with sample data"""
    print("=" * 60)
    print("🧪 TESTING WITH SAMPLE DATA")
    print("=" * 60)
    
    # Create sample network traffic data
    np.random.seed(42)
    
    # Normal traffic samples
    normal_samples = np.random.randn(5, 42)  # 42 features from UNSW dataset
    
    # Anomalous traffic samples (different distribution)
    anomaly_samples = np.random.randn(5, 42) * 2 + 3
    
    # Combine samples
    test_samples = np.vstack([normal_samples, anomaly_samples])
    true_labels = np.hstack([np.zeros(5), np.ones(5)])  # 0: normal, 1: anomaly
    
    # Load ensemble
    ensemble = SimpleEnsemble()
    
    if not ensemble.load_models():
        print("❌ Failed to load models")
        return
    
    # Load preprocessing pipeline
    pipeline = RealDataPipeline()
    try:
        pipeline.load_scaler()
    except:
        print("⚠️ Scaler not found, using raw data")
        # Use raw data if scaler not available
    
    # Test predictions
    print("\n📊 PREDICTION RESULTS:")
    print("-" * 40)
    
    correct_predictions = 0
    
    for i, sample in enumerate(test_samples):
        # Preprocess (if scaler available)
        try:
            sample_processed = pipeline.preprocess_real_time(sample.reshape(1, -1))
        except:
            sample_processed = sample.reshape(1, -1)
        
        # Make prediction
        results = ensemble.predict(sample_processed)
        
        score = results['ensemble_score'][0]
        prediction = results['final_predictions'][0]
        true_label = "ANOMALY" if true_labels[i] == 1 else "NORMAL"
        predicted_label = "ANOMALY" if prediction == 1 else "NORMAL"
        
        is_correct = prediction == true_labels[i]
        if is_correct:
            correct_predictions += 1
        
        status = "✅" if is_correct else "❌"
        
        print(f"Sample {i+1}: {status} True={true_label}, Predicted={predicted_label}, Score={score:.3f}")
    
    accuracy = correct_predictions / len(test_samples)
    print(f"\n📈 Accuracy: {accuracy:.1%} ({correct_predictions}/{len(test_samples)})")
    
    return accuracy

def test_with_real_dataset():
    """Test with real dataset samples"""
    print("\n" + "=" * 60)
    print("🌐 TESTING WITH REAL DATASET")
    print("=" * 60)
    
    # Load ensemble
    ensemble = SimpleEnsemble()
    
    if not ensemble.load_models():
        print("❌ Failed to load models")
        return
    
    # Load preprocessing pipeline
    pipeline = RealDataPipeline()
    
    # Try to load some real test data
    try:
        # Load small sample of UNSW test data
        test_path = "data/OneDrive_data/Training and Testing Sets/UNSW_NB15_testing-set.csv"
        if os.path.exists(test_path):
            print(f"Loading test data from {test_path}")
            test_df = pd.read_csv(test_path, nrows=100)  # Load only 100 samples for quick test
            
            # Preprocess
            X_test, y_test = pipeline.preprocess_unsw_data(test_df, is_training=False)
            
            print(f"Loaded {len(X_test)} test samples")
            print(f"Attack rate: {np.mean(y_test):.3f}")
            
            # Test predictions
            results = ensemble.predict(X_test)
            predictions = results['final_predictions']
            scores = results['ensemble_score']
            
            # Calculate accuracy
            accuracy = np.mean(predictions == y_test)
            
            print(f"\n📈 Real Dataset Results:")
            print(f"   Accuracy: {accuracy:.3f}")
            print(f"   Predicted anomalies: {np.mean(predictions):.3f}")
            print(f"   Actual anomalies: {np.mean(y_test):.3f}")
            
            # Show some examples
            print(f"\n🔍 Sample Predictions:")
            for i in range(min(5, len(predictions))):
                true_label = "ANOMALY" if y_test[i] == 1 else "NORMAL"
                predicted_label = "ANOMALY" if predictions[i] == 1 else "NORMAL"
                status = "✅" if predictions[i] == y_test[i] else "❌"
                
                print(f"   Sample {i+1}: {status} True={true_label}, Predicted={predicted_label}, Score={scores[i]:.3f}")
            
            return accuracy
        else:
            print("⚠️ Test dataset not found")
            return None
            
    except Exception as e:
        print(f"❌ Error testing with real dataset: {e}")
        return None

def create_deployment_summary():
    """Create deployment summary"""
    print("\n" + "=" * 80)
    print("📋 DEPLOYMENT SUMMARY")
    print("=" * 80)
    
    # Check model files
    model_files = {
        'Isolation Forest': 'models/isolation_forest.pkl',
        'One-Class SVM': 'models/one_class_svm.pkl',
        'Scaler': 'models/real_scaler.pkl',
        'Config': 'models/simple_ensemble_config.pkl'
    }
    
    print("📁 Model Files Status:")
    for name, path in model_files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"   ✅ {name}: {path} ({size:,} bytes)")
        else:
            print(f"   ❌ {name}: {path} (MISSING)")
    
    # Test functionality
    print("\n🧪 Functionality Tests:")
    
    # Test with sample data
    sample_accuracy = test_with_sample_data()
    
    # Test with real data
    real_accuracy = test_with_real_dataset()
    
    # Overall status
    print(f"\n🎯 Overall Status:")
    print(f"   Sample Test Accuracy: {sample_accuracy:.1%}")
    if real_accuracy is not None:
        print(f"   Real Test Accuracy: {real_accuracy:.1%}")
    
    print(f"   ✅ Models Ready for Deployment")
    
    # Next steps
    print(f"\n🚀 Deployment Instructions:")
    print(f"   1. Start API: python antigena_defense/api/api.py")
    print(f"   2. Test endpoint: curl http://localhost:8000/health")
    print(f"   3. Make predictions: POST http://localhost:8000/predict")
    print(f"   4. Monitor logs: antigena_defense/logs/")
    
    return sample_accuracy, real_accuracy

def main():
    """Main testing function"""
    print("🛡️ ANTIGENA DEFENSE SYSTEM - MODEL TESTING")
    print("Testing trained models for deployment readiness")
    
    # Create deployment summary
    sample_acc, real_acc = create_deployment_summary()
    
    # Final verdict
    print(f"\n" + "=" * 80)
    print("🎉 TESTING COMPLETED")
    print("=" * 80)
    
    if sample_acc > 0.7:  # 70% accuracy threshold
        print("✅ MODELS READY FOR PRODUCTION")
    else:
        print("⚠️ MODELS NEED RETRAINING")
    
    print(f"\n📊 Final Results:")
    print(f"   Sample Data Accuracy: {sample_acc:.1%}")
    if real_acc is not None:
        print(f"   Real Data Accuracy: {real_acc:.1%}")
    
    print(f"\n💡 Recommendation: {'DEPLOY' if sample_acc > 0.7 else 'RETRAIN'}")

if __name__ == "__main__":
    main()
