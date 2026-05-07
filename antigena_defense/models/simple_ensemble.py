"""
Simple trained ensemble used by the current deployment artifacts.

This adapter loads the scikit-learn models produced by train_real_data_simple.py
and exposes the same prediction shape as the full EnsembleEngine.
"""

from typing import Any, Dict
import logging
import os

import joblib
import numpy as np

from .isolation_forest import IsolationForestModel
from .one_class_svm import OneClassSVMModel

logger = logging.getLogger(__name__)


class SimpleEnsemble:
    """Two-model ensemble backed by Isolation Forest and One-Class SVM."""

    def __init__(self, config_path: str = "models/simple_ensemble_config.pkl"):
        self.models: Dict[str, Any] = {}
        self.weights = {"isolation_forest": 0.6, "one_class_svm": 0.4}
        self.threshold = 0.5
        self.config_path = config_path
        self.is_trained = False

    def load_models(self) -> None:
        """Load trained model artifacts from disk."""
        iforest = IsolationForestModel()
        iforest.load_model()
        self.models["isolation_forest"] = iforest

        svm_model = OneClassSVMModel()
        svm_model.load_model()
        self.models["one_class_svm"] = svm_model

        if os.path.exists(self.config_path):
            config = joblib.load(self.config_path)
            self.weights = config.get("weights", self.weights)
            self.threshold = config.get("threshold", self.threshold)

        self.is_trained = True
        logger.info("Simple ensemble loaded with weights=%s threshold=%s", self.weights, self.threshold)

    def predict_ensemble(self, X: np.ndarray) -> Dict[str, Any]:
        """Predict using the same response contract as EnsembleEngine."""
        if not self.is_trained:
            raise ValueError("Models not loaded")

        iforest_results = self.models["isolation_forest"].predict_iforest(X)
        svm_results = self.models["one_class_svm"].predict_svm(X)

        self._repair_single_sample_scores(iforest_results)
        self._repair_single_sample_scores(svm_results)

        ensemble_scores = (
            self.weights["isolation_forest"] * iforest_results["normalized_scores"]
            + self.weights["one_class_svm"] * svm_results["normalized_scores"]
        )
        final_predictions = (ensemble_scores > self.threshold).astype(int)

        return {
            "ensemble_score": ensemble_scores,
            "final_predictions": final_predictions,
            "threshold": self.threshold,
            "individual_models": {
                "isolation_forest": iforest_results,
                "one_class_svm": svm_results,
            },
            "weights": self.weights,
            "summary": {
                "anomaly_rate": float(np.mean(final_predictions)),
                "avg_ensemble_score": float(np.mean(ensemble_scores)),
                "max_score": float(np.max(ensemble_scores)),
                "min_score": float(np.min(ensemble_scores)),
            },
        }

    @staticmethod
    def _repair_single_sample_scores(results: Dict[str, Any]) -> None:
        """
        Existing model score normalization is batch-relative, so a one-row request
        collapses to 0. Use model labels as a stable fallback for real-time calls.
        """
        scores = results.get("normalized_scores")
        if scores is None or len(scores) != 1 or float(scores[0]) != 0.0:
            return

        prediction = int(results["predictions"][0])
        results["normalized_scores"] = np.array([0.85 if prediction == 1 else 0.15])
