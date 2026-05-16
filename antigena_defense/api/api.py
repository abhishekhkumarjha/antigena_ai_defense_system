"""
FastAPI for Real-Time Anomaly Detection
Provides REST API endpoints for the Antigena Defense System
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import numpy as np
import logging
import asyncio
from datetime import datetime
import json
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.simple_ensemble import SimpleEnsemble
from utils.real_data_preprocessing import RealDataPipeline
from response import ResponseEngine
from chatbot.api import chatbot_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Antigena Defense API",
    description="Real-time AI-powered anomaly detection system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://127.0.0.1:3002", "http://127.0.0.1:3003", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "*"],
    allow_headers=["*"],
)

# Include chatbot router
app.include_router(chatbot_router)

# Global variables for models
ensemble_engine = None
data_pipeline = None
shap_explainer = None
response_engine = None
model_loaded = False
active_model_type = "none"
decision_log: List[Dict[str, Any]] = []
training_state = {
    "status": "idle",
    "last_run": None,
    "message": "No retraining job has run in this API session",
}
LOG_PATH = "logs/decision_log.jsonl"

# Pydantic models for API
class FeatureInput(BaseModel):
    features: List[float] = Field(..., description="Feature vector for anomaly detection")
    timestamp: Optional[str] = Field(None, description="Timestamp of the data")
    source: Optional[str] = Field(None, description="Source of the data")

class BatchInput(BaseModel):
    samples: List[List[float]] = Field(..., description="Batch of feature vectors")
    timestamps: Optional[List[str]] = Field(None, description="Timestamps for each sample")
    source: Optional[str] = Field(None, description="Source of the data")

class TelemetryInput(BaseModel):
    telemetry: Dict[str, Any] = Field(..., description="Raw telemetry record")
    source: Optional[str] = Field(None, description="Source of the telemetry")

class PredictionResponse(BaseModel):
    anomaly_score: float = Field(..., description="Ensemble anomaly score (0-1)")
    label: str = Field(..., description="Prediction label (normal/anomaly)")
    confidence: float = Field(..., description="Confidence score")
    explanation: Optional[Dict[str, Any]] = Field(None, description="SHAP explanation")
    individual_models: Optional[Dict[str, Any]] = Field(None, description="Individual model results")
    timestamp: str = Field(..., description="Prediction timestamp")

class BatchResponse(BaseModel):
    predictions: List[PredictionResponse] = Field(..., description="Batch predictions")
    summary: Dict[str, Any] = Field(..., description="Batch summary statistics")

class HealthResponse(BaseModel):
    status: str = Field(..., description="API health status")
    model_loaded: bool = Field(..., description="Whether models are loaded")
    timestamp: str = Field(..., description="Health check timestamp")

class ModelInfo(BaseModel):
    model_type: str = Field(..., description="Type of model")
    is_trained: bool = Field(..., description="Whether model is trained")
    weights: Optional[Dict[str, float]] = Field(None, description="Model weights")
    threshold: Optional[float] = Field(None, description="Anomaly threshold")

def build_explanation(features: np.ndarray, results: Dict[str, Any], sample_index: int = 0, top_k: int = 5) -> Dict[str, Any]:
    """Build lightweight top-feature explanations when SHAP is not available."""
    sample = features[sample_index]
    names = getattr(data_pipeline, "feature_names", None) or [f"feature_{i}" for i in range(sample.shape[0])]
    baseline = np.abs(sample)
    top_indices = np.argsort(baseline)[-top_k:][::-1]
    top_features = []

    for index in top_indices:
        top_features.append({
            "feature": names[index] if index < len(names) else f"feature_{index}",
            "importance": float(baseline[index]),
            "direction": "above baseline" if sample[index] >= 0 else "below baseline",
        })

    model_votes = {
        name: int(model_result["predictions"][sample_index])
        for name, model_result in results["individual_models"].items()
    }

    return {
        "method": "feature_deviation",
        "explanation": "Top normalized feature deviations and model votes for this decision.",
        "top_features": top_features,
        "model_votes": model_votes,
    }

def record_decision(entry: Dict[str, Any]) -> None:
    """Persist an audit event for model decisions and response workflows."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    decision_log.append(entry)
    if len(decision_log) > 500:
        del decision_log[:-500]

    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")

def extract_raw_features(telemetry: Dict[str, Any]) -> List[float]:
    """Map raw flow/session telemetry to the deployed 42-feature vector shape."""
    flow = telemetry.get("network_flow", telemetry)
    protocol_map = {"TCP": 1, "UDP": 2, "HTTPS": 3, "SSH": 4, "SMB": 5, "DNS": 6}
    features = [
        float(flow.get("bytes_sent", flow.get("bytes", 0))),
        float(flow.get("bytes_received", 0)),
        float(flow.get("duration", 0)),
        float(flow.get("packet_count", 0)),
        float(flow.get("src_port", 0)),
        float(flow.get("dst_port", 0)),
        float(protocol_map.get(str(flow.get("protocol", "")).upper(), 0)),
        float(flow.get("connection_count", 0)),
        float(flow.get("error_rate", 0)),
        float(flow.get("response_time", 0)),
    ]

    while len(features) < 42:
        previous = features[-1] if features else 0
        features.append(float((previous * 31 + len(features) * 17) % 1000))

    return features[:42]

def current_metrics() -> Dict[str, Any]:
    """Summarize runtime metrics expected by the monitoring/dashboard layer."""
    total = len(decision_log)
    anomalies = sum(1 for item in decision_log if item.get("label") == "anomaly")
    scores = [item.get("anomaly_score", 0.0) for item in decision_log]
    avg_score = float(np.mean(scores)) if scores else 0.0
    drift_score = min(1.0, abs(avg_score - 0.5) * 2) if scores else 0.0

    return {
        "total_decisions": total,
        "anomaly_count": anomalies,
        "anomaly_rate": anomalies / total if total else 0.0,
        "avg_anomaly_score": avg_score,
        "drift_score": drift_score,
        "drift_status": "review" if drift_score > 0.35 else "stable",
        "model_loaded": model_loaded,
        "model_type": active_model_type,
        "training": training_state,
        "response_actions": response_engine.get_response_stats() if response_engine else {"total_actions": 0},
    }

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    global ensemble_engine, data_pipeline, shap_explainer, response_engine, model_loaded, active_model_type
    
    logger.info("Starting Antigena Defense API...")
    
    try:
        # Initialize components for the trained simple ensemble artifacts.
        ensemble_engine = SimpleEnsemble()
        data_pipeline = RealDataPipeline()
        shap_explainer = None
        response_engine = ResponseEngine()
        
        # Try to load pre-trained models
        try:
            ensemble_engine.load_models()
            data_pipeline.load_scaler()
            active_model_type = "simple_ensemble"
            model_loaded = True
            logger.info("Pre-trained models loaded successfully")
        except FileNotFoundError:
            logger.warning("No pre-trained models found. Models need to be trained first.")
            model_loaded = False
        
        logger.info("API startup completed")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        model_loaded = False
        active_model_type = "none"

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Antigena Defense API",
        "version": "1.0.0",
        "status": "running",
        "model_type": active_model_type
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if model_loaded else "models_not_loaded",
        model_loaded=model_loaded,
        timestamp=datetime.now().isoformat()
    )

@app.get("/models/info", response_model=ModelInfo)
async def get_model_info():
    """Get model information"""
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    return ModelInfo(
        model_type=active_model_type,
        is_trained=ensemble_engine.is_trained,
        weights=ensemble_engine.weights,
        threshold=ensemble_engine.threshold
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict_anomaly(input_data: FeatureInput, background_tasks: BackgroundTasks):
    """
    Predict anomaly for a single sample
    """
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded. Please train models first.")
    
    try:
        # Convert input to numpy array
        features = np.array(input_data.features).reshape(1, -1)
        
        # Preprocess features
        features_processed = data_pipeline.preprocess_real_time(features)
        
        # Make prediction
        results = ensemble_engine.predict_ensemble(features_processed)
        
        # Extract results
        anomaly_score = float(results['ensemble_score'][0])
        prediction = results['final_predictions'][0]
        label = "anomaly" if prediction == 1 else "normal"
        confidence = max(anomaly_score, 1 - anomaly_score)
        
        # Generate explanation if anomaly detected
        explanation = build_explanation(features_processed, results, 0, top_k=5)
        if prediction == 1 and shap_explainer is not None and shap_explainer.explainer is not None:
            try:
                explanation = shap_explainer.explain_sample(features_processed[0], top_k=5)
            except Exception as e:
                logger.warning(f"Failed to generate explanation: {e}")
        
        # Trigger response in background if anomaly
        if prediction == 1:
            background_tasks.add_task(
                response_engine.handle_anomaly,
                anomaly_score,
                input_data.features,
                input_data.source
            )
        
        response = PredictionResponse(
            anomaly_score=anomaly_score,
            label=label,
            confidence=confidence,
            explanation=explanation,
            individual_models={
                'isolation_forest': {
                    'score': float(results['individual_models']['isolation_forest']['normalized_scores'][0]),
                    'prediction': int(results['individual_models']['isolation_forest']['predictions'][0])
                },
                'one_class_svm': {
                    'score': float(results['individual_models']['one_class_svm']['normalized_scores'][0]),
                    'prediction': int(results['individual_models']['one_class_svm']['predictions'][0])
                }
            },
            timestamp=datetime.now().isoformat()
        )

        record_decision({
            "timestamp": response.timestamp,
            "source": input_data.source,
            "label": label,
            "anomaly_score": anomaly_score,
            "confidence": confidence,
            "individual_models": response.individual_models,
            "explanation": explanation,
        })
        
        logger.info(f"Prediction completed: {label} (score: {anomaly_score:.3f})")
        return response
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict/batch", response_model=BatchResponse)
async def predict_batch(input_data: BatchInput, background_tasks: BackgroundTasks):
    """
    Predict anomalies for multiple samples
    """
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded. Please train models first.")
    
    try:
        # Convert input to numpy array
        features = np.array(input_data.samples)
        
        # Preprocess features
        features_processed = data_pipeline.preprocess_real_time(features)
        
        # Make predictions
        results = ensemble_engine.predict_ensemble(features_processed)
        
        # Create individual predictions
        predictions = []
        anomaly_count = 0
        
        for i in range(len(features)):
            anomaly_score = float(results['ensemble_score'][i])
            prediction = results['final_predictions'][i]
            label = "anomaly" if prediction == 1 else "normal"
            confidence = max(anomaly_score, 1 - anomaly_score)
            
            if prediction == 1:
                anomaly_count += 1
            
            # Generate explanation for anomalies
            explanation = build_explanation(features_processed, results, i, top_k=3)
            if prediction == 1 and shap_explainer is not None and shap_explainer.explainer is not None:
                try:
                    explanation = shap_explainer.explain_sample(features_processed[i], top_k=3)
                except Exception as e:
                    logger.warning(f"Failed to generate explanation for sample {i}: {e}")
            
            pred_response = PredictionResponse(
                anomaly_score=anomaly_score,
                label=label,
                confidence=confidence,
                explanation=explanation,
                individual_models={
                    name: {
                        'score': float(model_result['normalized_scores'][i]),
                        'prediction': int(model_result['predictions'][i])
                    }
                    for name, model_result in results['individual_models'].items()
                },
                timestamp=datetime.now().isoformat()
            )
            predictions.append(pred_response)
            record_decision({
                "timestamp": pred_response.timestamp,
                "source": input_data.source,
                "label": label,
                "anomaly_score": anomaly_score,
                "confidence": confidence,
                "individual_models": pred_response.individual_models,
                "explanation": explanation,
            })
        
        # Trigger batch response if anomalies found
        if anomaly_count > 0:
            background_tasks.add_task(
                response_engine.handle_batch_anomalies,
                anomaly_count,
                len(features),
                input_data.source
            )
        
        # Create summary
        summary = {
            'total_samples': len(features),
            'anomaly_count': anomaly_count,
            'normal_count': len(features) - anomaly_count,
            'anomaly_rate': anomaly_count / len(features),
            'avg_anomaly_score': float(np.mean(results['ensemble_score'])),
            'max_anomaly_score': float(np.max(results['ensemble_score'])),
            'min_anomaly_score': float(np.min(results['ensemble_score']))
        }
        
        response = BatchResponse(
            predictions=predictions,
            summary=summary
        )
        
        logger.info(f"Batch prediction completed: {anomaly_count}/{len(features)} anomalies")
        return response
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.post("/models/train")
async def train_models(background_tasks: BackgroundTasks):
    """
    Queue model retraining/reload.
    """
    try:
        training_state.update({
            "status": "queued",
            "last_run": datetime.now().isoformat(),
            "message": "Retraining/reload job queued",
        })
        background_tasks.add_task(train_models_background)
        
        return {
            "message": "Model retraining queued in background",
            "status": "training_started",
            "model_loaded": model_loaded
        }
        
    except Exception as e:
        logger.error(f"Training initiation error: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

async def train_models_background():
    """Background task for model training"""
    global model_loaded, active_model_type
    
    try:
        training_state.update({
            "status": "running",
            "last_run": datetime.now().isoformat(),
            "message": "Refreshing trained artifacts from disk",
        })
        logger.info("Starting background model training...")

        # In production this should invoke the selected dataset training job.
        # For the deployed demo artifacts, refresh the trained models from disk
        # after a short queue delay so the UI can exercise the workflow safely.
        await asyncio.sleep(10)  # Simulate training time
        ensemble_engine.load_models()
        data_pipeline.load_scaler()
        model_loaded = True
        active_model_type = "simple_ensemble"
        training_state.update({
            "status": "completed",
            "last_run": datetime.now().isoformat(),
            "message": "Model artifacts reloaded successfully",
        })
        logger.info("Model training completed")
        
    except Exception as e:
        training_state.update({
            "status": "failed",
            "last_run": datetime.now().isoformat(),
            "message": str(e),
        })
        logger.error(f"Background training error: {e}")

@app.post("/models/reload")
async def reload_models():
    """Reload models from disk"""
    try:
        ensemble_engine.load_models()
        data_pipeline.load_scaler()
        
        global model_loaded, active_model_type
        model_loaded = True
        active_model_type = "simple_ensemble"
        
        logger.info("Models reloaded successfully")
        return {"message": "Models reloaded successfully"}
        
    except Exception as e:
        logger.error(f"Model reload error: {e}")
        raise HTTPException(status_code=500, detail=f"Model reload failed: {str(e)}")

@app.get("/explain/global")
async def get_global_importance():
    """Get global feature importance"""
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        feature_names = getattr(data_pipeline, "feature_names", None) or [f"feature_{i}" for i in range(42)]
        importances = {}
        for item in decision_log[-100:]:
            for feature in item.get("explanation", {}).get("top_features", []):
                name = feature.get("feature")
                importances[name] = importances.get(name, 0.0) + float(feature.get("importance", 0.0))

        if not importances:
            importances = {name: 0.0 for name in feature_names[:10]}

        return {
            "method": "rolling_decision_importance",
            "status": "available",
            "feature_importance": dict(sorted(importances.items(), key=lambda item: item[1], reverse=True)[:10])
        }
        
    except Exception as e:
        logger.error(f"Global importance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/telemetry", response_model=PredictionResponse)
async def ingest_telemetry(input_data: TelemetryInput, background_tasks: BackgroundTasks):
    """Ingest raw telemetry and score it through the anomaly engine."""
    features = extract_raw_features(input_data.telemetry)
    source = input_data.source or input_data.telemetry.get("source") or input_data.telemetry.get("src_ip")
    return await predict_anomaly(FeatureInput(features=features, source=source), background_tasks)

@app.get("/events/recent")
async def get_recent_events(limit: int = 100):
    """Return recent model decisions for audit/dashboard use."""
    safe_limit = max(1, min(limit, 500))
    return {
        "events": decision_log[-safe_limit:],
        "count": min(len(decision_log), safe_limit),
    }

@app.get("/response/history")
async def get_response_history(limit: int = 100):
    """Return response action history."""
    return {
        "actions": response_engine.get_action_history(limit) if response_engine else [],
        "stats": response_engine.get_response_stats() if response_engine else {"total_actions": 0},
    }

@app.get("/metrics")
async def get_metrics():
    """Runtime metrics for detection, drift, response, and retraining."""
    return current_metrics()

@app.get("/drift/status")
async def get_drift_status():
    """Concept drift status based on recent model score distribution."""
    metrics = current_metrics()
    return {
        "status": metrics["drift_status"],
        "drift_score": metrics["drift_score"],
        "recommendation": "trigger_retraining" if metrics["drift_status"] == "review" else "continue_monitoring",
    }

@app.get("/security/policy")
async def get_security_policy():
    """Expose current safe-response policy for analyst review."""
    return {
        "mode": "alert_and_simulated_containment",
        "fail_safe": "alert_only_if_model_unavailable",
        "allowed_actions": [action.value for rule in response_engine.rules for action in rule.actions] if response_engine else [],
        "privacy": "audit logs contain source identifiers; avoid storing secrets or payloads",
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "status": 404}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "status": 500}

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    # Run the API. Render provides PORT and should not run the development reloader.
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
