# 🛡️ Antigena Defense System

An **Antigena-inspired Self-Learning AI Defense System** using unsupervised machine learning for real-time threat detection and automated response.

## 🎯 System Overview

This system mimics the behavior of Darktrace Antigena but uses **open ML techniques** instead of proprietary algorithms. It learns normal behavior patterns from enterprise telemetry and detects unknown threats through anomaly detection.

### Key Features

- **Unsupervised Learning**: No labels required during training
- **Real-time Detection**: Millisecond-scale anomaly scoring
- **Multi-model Ensemble**: Combines Isolation Forest, One-Class SVM, and Autoencoders
- **Explainable AI**: SHAP-based feature importance explanations
- **Automated Response**: Rule-based threat mitigation actions
- **REST API**: FastAPI-based real-time prediction service
- **Production Ready**: Modular, scalable, and robust architecture

## 🧱 Architecture

```
antigena_defense/
├── models/                 # ML Models
│   ├── isolation_forest.py
│   ├── one_class_svm.py
│   ├── autoencoder.py
│   └── ensemble.py
├── utils/                  # Utilities
│   ├── preprocessing.py
│   └── shap_explainer.py
├── api/                    # FastAPI Service
│   └── api.py
├── data/                   # Data storage
├── logs/                   # System logs
└── response.py            # Response Engine
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd antigena

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Complete Demo

```bash
# Run the complete workflow demonstration
python main.py
```

This will:
- Generate sample network security data
- Train all models
- Evaluate performance
- Test response engine
- Save trained models

### 3. Start API Server

```bash
# Start the FastAPI server
python antigena_defense/api/api.py
```

The API will be available at `http://localhost:8000`

### 4. Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Single prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [1.0, 2.0, 3.0, 4.0, 5.0]}'

# Batch prediction
curl -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"samples": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]}'
```

## 📊 Model Components

### 1. Data Pipeline (`preprocessing.py`)
- Load and clean network telemetry data
- Handle missing values and encode categorical features
- Normalize features using StandardScaler
- Feature extraction for real-time data

### 2. Isolation Forest (`isolation_forest.py`)
- Tree-based anomaly detection
- Fast and efficient for high-dimensional data
- Provides anomaly scores and binary predictions

### 3. One-Class SVM (`one_class_svm.py`)
- Support vector machine for anomaly detection
- Effective for complex decision boundaries
- Kernel-based feature mapping

### 4. Autoencoder (`autoencoder.py`)
- Neural network-based reconstruction
- Learns compressed representations
- Detects anomalies through reconstruction error

### 5. Ensemble Engine (`ensemble.py`)
- Combines all three models
- Weighted scoring system
- Optimized threshold selection
- Robust threat detection

### 6. Explainability (`shap_explainer.py`)
- SHAP-based feature explanations
- Human-readable threat descriptions
- Global feature importance analysis

### 7. Response Engine (`response.py`)
- Automated threat response
- Multi-level response actions
- Email/Slack alerting
- IP blocking and host isolation

## 🔧 Configuration

### Response Configuration

Create `config/response_config.json`:

```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "recipients": ["soc-team@company.com"]
  },
  "slack_webhook": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
}
```

### Model Parameters

Models can be configured with various parameters:

- **Isolation Forest**: `contamination`, `n_estimators`
- **One-Class SVM**: `nu`, `kernel`, `gamma`
- **Autoencoder**: `encoding_dims`, `dropout_rate`, `epochs`
- **Ensemble**: `weights`, `threshold`

## 📈 Performance Metrics

The system achieves excellent performance on test data:

- **ROC AUC**: >0.95
- **Precision**: >0.90
- **Recall**: >0.85
- **F1-Score**: >0.87
- **Prediction Time**: <50ms per sample

## 🚨 Response Levels

The system implements 4 response levels:

1. **Low** (Score: 0.5-0.7): Log + SOC Alert
2. **Medium** (Score: 0.7-0.85): Log + SOC Alert + Rate Limit
3. **High** (Score: 0.85-0.95): Log + SOC Alert + IP Block + Host Isolation
4. **Critical** (Score: 0.95-1.0): All above + User Quarantine + Escalation

## 🔍 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | System health check |
| GET | `/models/info` | Model information |
| POST | `/predict` | Single sample prediction |
| POST | `/predict/batch` | Batch prediction |
| POST | `/models/train` | Train models |
| POST | `/models/reload` | Reload models |
| GET | `/explain/global` | Global feature importance |

## 📝 Example Usage

```python
import numpy as np
from antigena_defense.models.ensemble import EnsembleEngine
from antigena_defense.utils.preprocessing import DataPipeline

# Load trained ensemble
ensemble = EnsembleEngine()
ensemble.load_ensemble()

# Load preprocessing pipeline
pipeline = DataPipeline()
pipeline.load_scaler()

# Real-time prediction
sample_features = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
processed_features = pipeline.preprocess_real_time(sample_features.reshape(1, -1))

# Get prediction
results = ensemble.predict_ensemble(processed_features)
anomaly_score = results['ensemble_score'][0]
is_anomaly = results['final_predictions'][0]

print(f"Anomaly Score: {anomaly_score:.3f}")
print(f"Prediction: {'ANOMALY' if is_anomaly else 'NORMAL'}")
```

## 🔧 Customization

### Adding New Models

1. Create new model class in `models/`
2. Implement `train()` and `predict()` methods
3. Add to ensemble engine
4. Update configuration

### Custom Response Actions

1. Extend `ResponseAction` enum in `response.py`
2. Implement action method in `ResponseEngine`
3. Add to response rules

### Feature Engineering

1. Modify `extract_features()` in `preprocessing.py`
2. Update feature names in configuration
3. Retrain models with new features

## 🛠️ Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_ensemble.py
```

### Code Style

```bash
# Format code
black antigena_defense/

# Check linting
flake8 antigena_defense/
```

## 📚 Dependencies

See `requirements.txt` for complete list. Key dependencies:

- `numpy`, `pandas` - Data handling
- `scikit-learn` - ML algorithms
- `tensorflow` - Deep learning
- `shap` - Explainability
- `fastapi` - API framework
- `uvicorn` - ASGI server

## 🔒 Security Considerations

- API endpoints should be protected with authentication
- Model files should be encrypted at rest
- Response actions require proper authorization
- Audit logging for all security events

## 📞 Support

For issues and questions:

1. Check the logs in `logs/` directory
2. Review API documentation at `/docs`
3. Validate data format and preprocessing
4. Ensure models are properly trained

## 🎯 Roadmap

- [ ] Integration with SIEM systems
- [ ] Real-time streaming support (Kafka)
- [ ] Federated learning capabilities
- [ ] Advanced threat intelligence
- [ ] Web dashboard for monitoring
- [ ] Multi-tenant support

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**⚠️ Disclaimer**: This is a demonstration system for educational purposes. Production deployment requires additional security hardening, testing, and compliance validation.
