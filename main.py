"""
Main Example Usage for Antigena Defense System
Demonstrates the complete workflow from training to prediction
"""

import numpy as np
import pandas as pd
import asyncio
import logging
from datetime import datetime
import os
import sys

# Add the antigena_defense directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'antigena_defense'))

# Ensure a top-level ASGI `app` symbol exists so deployment platforms
# (Vercel, Render) can auto-detect the FastAPI application during builds.
# We create a lightweight fallback `FastAPI` instance and then try to
# import the real application to replace it. This avoids build-time
# import errors from preventing detection.
try:
    from fastapi import FastAPI
except Exception:
    FastAPI = None

# Fallback app always defined
app = None
if FastAPI is not None:
    app = FastAPI()

try:
    # If the internal app can be imported, use it instead of the fallback
    from antigena_defense.api.api import app as internal_app
    if internal_app is not None:
        app = internal_app
except Exception:
    # Import may fail during build (missing deps). Keep fallback `app` so
    # the deployment platform recognizes an ASGI application.
    pass

from antigena_defense.utils.preprocessing import DataPipeline
from antigena_defense.models.isolation_forest import IsolationForestModel
from antigena_defense.models.one_class_svm import OneClassSVMModel
from antigena_defense.models.autoencoder import AutoencoderModel
from antigena_defense.models.ensemble import EnsembleEngine
from antigena_defense.utils.shap_explainer import SHAPExplainer
from antigena_defense.response import ResponseEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_sample_data(n_samples: int = 2000, n_features: int = 15, anomaly_ratio: float = 0.05):
    """
    Generate sample network security data for demonstration
    
    Args:
        n_samples: Total number of samples
        n_features: Number of features
        anomaly_ratio: Ratio of anomalies in the dataset
    
    Returns:
        Tuple of (features, labels, feature_names)
    """
    logger.info(f"Generating sample data: {n_samples} samples, {n_features} features")
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Calculate number of anomalies
    n_anomalies = int(n_samples * anomaly_ratio)
    n_normal = n_samples - n_anomalies
    
    # Generate normal data (multivariate normal distribution)
    normal_mean = np.zeros(n_features)
    normal_cov = np.eye(n_features) * 0.5  # Some correlation between features
    normal_data = np.random.multivariate_normal(normal_mean, normal_cov, n_normal)
    
    # Generate anomalous data (different distribution)
    anomaly_mean = np.random.uniform(2, 5, n_features)  # Shifted mean
    anomaly_cov = np.eye(n_features) * 2.0  # Higher variance
    anomaly_data = np.random.multivariate_normal(anomaly_mean, anomaly_cov, n_anomalies)
    
    # Combine data
    X = np.vstack([normal_data, anomaly_data])
    
    # Create labels (0: normal, 1: anomaly)
    y = np.hstack([np.zeros(n_normal), np.ones(n_anomalies)])
    
    # Shuffle data
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]
    
    # Create feature names (network security related)
    feature_names = [
        'bytes_sent', 'bytes_received', 'duration', 'packet_count',
        'src_port', 'dst_port', 'protocol_type', 'connection_count',
        'error_rate', 'response_time', 'cpu_usage', 'memory_usage',
        'disk_io', 'network_latency', 'session_length'
    ][:n_features]
    
    logger.info(f"Generated {n_normal} normal and {n_anomalies} anomalous samples")
    
    return X, y, feature_names

def save_sample_data_to_csv(X: np.ndarray, feature_names: list, filename: str = "sample_network_data.csv"):
    """Save sample data to CSV file"""
    df = pd.DataFrame(X, columns=feature_names)
    df.to_csv(filename, index=False)
    logger.info(f"Sample data saved to {filename}")
    return filename

def main():
    """Main function demonstrating the complete Antigena Defense System workflow"""
    
    print("=" * 80)
    print("🛡️  ANTIGENA DEFENSE SYSTEM - COMPLETE WORKFLOW DEMONSTRATION")
    print("=" * 80)
    
    # Step 1: Generate and prepare sample data
    print("\n📊 STEP 1: Generating Sample Data")
    print("-" * 50)
    
    X, y, feature_names = generate_sample_data(n_samples=2000, n_features=15, anomaly_ratio=0.05)
    
    # Save sample data to CSV
    csv_file = save_sample_data_to_csv(X, feature_names)
    
    # Step 2: Data Preprocessing
    print("\n🔧 STEP 2: Data Preprocessing")
    print("-" * 50)
    
    # Initialize data pipeline
    pipeline = DataPipeline()
    
    # Load and preprocess data
    X_train, X_test = pipeline.preprocess_data(csv_file, save_scaler=True)
    
    # Split test data for evaluation
    from sklearn.model_selection import train_test_split
    X_test_final, X_val, y_test_final, y_val = train_test_split(
        X_test, y[:len(X_test)], test_size=0.5, random_state=42, stratify=y[:len(X_test)]
    )
    
    print(f"Training data: {X_train.shape}")
    print(f"Validation data: {X_val.shape}")
    print(f"Test data: {X_test_final.shape}")
    
    # Step 3: Train Individual Models
    print("\n🤖 STEP 3: Training Individual Models")
    print("-" * 50)
    
    # Train Isolation Forest
    print("Training Isolation Forest...")
    iforest = IsolationForestModel()
    iforest.train(X_train, contamination=0.05)
    
    # Train One-Class SVM
    print("Training One-Class SVM...")
    svm_model = OneClassSVMModel()
    svm_model.train(X_train, nu=0.05)
    
    # Train Autoencoder
    print("Training Autoencoder...")
    autoencoder = AutoencoderModel()
    autoencoder.build_model(input_dim=X_train.shape[1], encoding_dims=[10, 6, 3])
    autoencoder.train(X_train, X_val, epochs=50, batch_size=32)
    
    print("✅ All individual models trained successfully!")
    
    # Step 4: Create and Train Ensemble
    print("\n🎯 STEP 4: Training Ensemble Engine")
    print("-" * 50)
    
    ensemble = EnsembleEngine()
    
    # Train all models in ensemble
    training_results = ensemble.train_all_models(
        X_train, X_val, 
        iforest_contamination=0.05,
        svm_nu=0.05,
        autoencoder_epochs=50
    )
    
    print("✅ Ensemble models trained!")
    
    # Optimize ensemble parameters
    print("Optimizing ensemble weights and threshold...")
    ensemble.optimize_weights(X_val, y_val)
    ensemble.optimize_threshold(X_val, y_val)
    
    print(f"Optimized weights: {ensemble.weights}")
    print(f"Optimized threshold: {ensemble.threshold:.3f}")
    
    # Step 5: Evaluate Ensemble Performance
    print("\n📈 STEP 5: Evaluating Ensemble Performance")
    print("-" * 50)
    
    # Make predictions on test set
    results = ensemble.predict_ensemble(X_test_final)
    
    # Calculate metrics
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
    
    predictions = results['final_predictions']
    scores = results['ensemble_score']
    
    print(f"Anomaly rate in test set: {np.mean(predictions):.3f}")
    print(f"Average ensemble score: {np.mean(scores):.3f}")
    
    # Classification metrics
    print("\nClassification Report:")
    print(classification_report(y_test_final, predictions))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test_final, predictions))
    
    print(f"\nROC AUC Score: {roc_auc_score(y_test_final, scores):.3f}")
    
    # Step 6: Setup Explainability
    print("\n🔍 STEP 6: Setting Up Explainability")
    print("-" * 50)
    
    # Initialize SHAP explainer
    explainer = SHAPExplainer(model_type="surrogate")
    
    # Fit explainer using training data
    explainer.fit_explainer(iforest, X_train, feature_names)
    
    # Explain a few anomalous samples
    anomaly_indices = np.where(predictions == 1)[0][:3]  # First 3 anomalies
    
    for i, idx in enumerate(anomaly_indices):
        print(f"\nExplaining Anomaly Sample {i+1}:")
        explanation = explainer.explain_sample(X_test_final[idx], top_k=5)
        print(f"Explanation: {explanation['explanation']}")
        
        for feature in explanation['top_features'][:3]:
            print(f"  - {feature['feature']}: {feature['importance']:.3f} ({feature['direction']})")
    
    # Step 7: Test Response Engine
    print("\n🚨 STEP 7: Testing Response Engine")
    print("-" * 50)
    
    # Initialize response engine
    response_engine = ResponseEngine()
    
    # Test response with different anomaly levels
    test_samples = [
        (0.3, "low_risk_sample"),
        (0.6, "medium_risk_sample"),
        (0.8, "high_risk_sample"),
        (0.95, "critical_risk_sample")
    ]
    
    async def test_responses():
        for score, source in test_samples:
            print(f"\nTesting response for score: {score:.2f}")
            result = await response_engine.handle_anomaly(
                anomaly_score=score,
                features=X_test_final[0].tolist(),
                source=source,
                ip_address="192.168.1.100",
                user_id="test_user"
            )
            print(f"Response: {result['status']}")
            if result['status'] == 'action_taken':
                print(f"Actions: {result['actions']}")
    
    # Run async test
    asyncio.run(test_responses())
    
    # Step 8: Save Models
    print("\n💾 STEP 8: Saving Models")
    print("-" * 50)
    
    # Save individual models
    iforest.save_model()
    svm_model.save_model()
    autoencoder.save_model()
    
    # Save ensemble
    ensemble.save_ensemble()
    
    # Save explainer
    explainer.save_explainer("models/shap_explainer.pkl")
    
    print("✅ All models saved successfully!")
    
    # Step 9: Demonstrate Real-time Prediction
    print("\n⚡ STEP 9: Real-time Prediction Demo")
    print("-" * 50)
    
    # Simulate real-time data
    real_time_samples = X_test_final[:5]
    
    print("Making real-time predictions on 5 samples...")
    
    for i, sample in enumerate(real_time_samples):
        # Preprocess
        sample_processed = pipeline.preprocess_real_time(sample.reshape(1, -1))
        
        # Predict
        prediction_results = ensemble.predict_ensemble(sample_processed)
        
        score = prediction_results['ensemble_score'][0]
        prediction = prediction_results['final_predictions'][0]
        label = "ANOMALY" if prediction == 1 else "NORMAL"
        
        print(f"Sample {i+1}: {label} (Score: {score:.3f})")
        
        # Get explanation if anomaly
        if prediction == 1:
            explanation = explainer.explain_sample(sample_processed[0], top_k=3)
            print(f"  Explanation: {explanation['explanation']}")
    
    # Step 10: System Statistics
    print("\n📊 STEP 10: System Statistics")
    print("-" * 50)
    
    # Response engine statistics
    response_stats = response_engine.get_response_stats()
    print(f"Total response actions: {response_stats['total_actions']}")
    print(f"Actions by level: {response_stats['actions_by_level']}")
    print(f"Actions by type: {response_stats['actions_by_type']}")
    
    # Global feature importance
    global_importance = explainer.get_global_feature_importance(X_train, top_k=5)
    print(f"\nTop 5 Important Features:")
    for feature, importance in global_importance.items():
        print(f"  {feature}: {importance:.3f}")
    
    print("\n" + "=" * 80)
    print("🎉 ANTIGENA DEFENSE SYSTEM DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    
    print("\n🚀 Next Steps:")
    print("1. Start the FastAPI server: python antigena_defense/api/api.py")
    print("2. Test the API endpoints at http://localhost:8000")
    print("3. Integrate with your real network telemetry data")
    print("4. Customize response rules for your environment")
    print("5. Set up email/Slack notifications in config/response_config.json")
    
    print("\n📚 API Endpoints:")
    print("- GET /health - Check system health")
    print("- POST /predict - Single sample prediction")
    print("- POST /predict/batch - Batch prediction")
    print("- GET /models/info - Model information")
    print("- POST /models/train - Train models")

if __name__ == "__main__":
    main()
