import numpy as np
import joblib
import json
import time
from pathlib import Path
import tensorflow as tf

MODELS_DIR = Path("./models")

class FraudPredictor:
    def __init__(self):
        print("Loading models...")
        self.xgb        = joblib.load(MODELS_DIR / "xgboost_model.pkl")
        self.iso_forest = joblib.load(MODELS_DIR / "isolation_forest.pkl")
        self.scaler     = joblib.load(MODELS_DIR / "scaler.pkl")
        self.meta       = joblib.load(MODELS_DIR / "meta_learner.pkl")
        self.lstm       = tf.keras.models.load_model(MODELS_DIR / "lstm_model.keras")

        with open(MODELS_DIR / "global_stats.json") as f:
            self.global_stats = json.load(f)

        self.feature_cols  = self.global_stats['feature_cols']
        self.threshold     = self.global_stats.get('best_threshold', 0.3)
        print(f"✓ All models loaded. Features: {len(self.feature_cols)}, Threshold: {self.threshold:.4f}")

    def predict(self, features: dict) -> dict:
        start = time.time()

        X = np.array([[features.get(col, -999) for col in self.feature_cols]])

        # XGBoost
        xgb_score = float(self.xgb.predict_proba(X)[0, 1])

        # Isolation Forest
        iso_raw   = self.iso_forest.decision_function(X)[0]
        iso_score = float(np.clip(1 - (iso_raw + 0.5), 0, 1))

        # LSTM
        X_scaled   = self.scaler.transform(X)
        X_lstm     = X_scaled.reshape(1, 1, X_scaled.shape[1])
        lstm_score = float(self.lstm.predict(X_lstm, verbose=0)[0, 0])

        # Meta-learner
        meta_X      = np.array([[xgb_score, iso_score, lstm_score]])
        final_score = float(self.meta.predict_proba(meta_X)[0, 1])

        # Risk label using tuned threshold
        if final_score >= self.threshold * 1.5:
            risk = "HIGH"
        elif final_score >= self.threshold * 0.6:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        latency_ms = round((time.time() - start) * 1000, 2)

        return {
            "fraud_probability": round(final_score, 4),
            "risk_level":        risk,
            "model_scores": {
                "xgboost":          round(xgb_score, 4),
                "isolation_forest": round(iso_score, 4),
                "lstm":             round(lstm_score, 4),
            },
            "latency_ms": latency_ms
        }

_predictor = None

def get_predictor() -> FraudPredictor:
    global _predictor
    if _predictor is None:
        _predictor = FraudPredictor()
    return _predictor
