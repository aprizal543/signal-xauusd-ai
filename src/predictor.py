"""
src/predictor.py
Load model dan jalankan prediksi ensemble.
"""

import os
import json
import logging
import numpy as np
import joblib
from tensorflow.keras.models import load_model

logger = logging.getLogger(__name__)

# Label mapping
LABELS = {0: "SELL", 1: "HOLD", 2: "BUY"}
EMOJI  = {0: "", 1: "", 2: ""}


class XAUUSDPredictor:
    def __init__(self, model_dir: str = "models"):
        self.model_dir  = model_dir
        self.xgb_model  = None
        self.lstm_model = None
        self.scaler     = None
        self.metadata   = None
        self._load_models()

    def _load_models(self):
        """Load semua model dari folder."""
        try:
            # Load XGBoost
            xgb_path = os.path.join(self.model_dir, "xgb_model.joblib")
            self.xgb_model = joblib.load(xgb_path)
            logger.info("XGBoost loaded")

            # Load LSTM
            lstm_path = os.path.join(self.model_dir, "lstm_model.keras")
            self.lstm_model = load_model(lstm_path)
            logger.info("LSTM loaded")

            # Load Scaler
            scaler_path = os.path.join(self.model_dir, "scaler.joblib")
            self.scaler = joblib.load(scaler_path)
            logger.info("Scaler loaded")

            # Load Metadata
            meta_path = os.path.join(self.model_dir, "metadata.json")
            with open(meta_path, "r") as f:
                self.metadata = json.load(f)
            logger.info(f"Metadata loaded | Ensemble acc: {self.metadata.get('accuracy_ensemble', 'N/A'):.2%}")

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise

    def predict(self, x_flat: np.ndarray, x_seq: np.ndarray) -> dict:
        """
        Jalankan prediksi ensemble.

        Args:
            x_flat : fitur untuk XGBoost (1, n_features)
            x_seq  : sequence untuk LSTM (1, seq_len, n_features)

        Returns:
            dict berisi signal, confidence, probabilities
        """
        # Scale input
        x_flat_scaled = self.scaler.transform(x_flat)
        x_seq_scaled  = np.array([
            self.scaler.transform(x_seq[0])
        ])

        # XGBoost prediction
        xgb_prob = self.xgb_model.predict_proba(x_flat_scaled)

        # LSTM prediction
        lstm_prob = self.lstm_model.predict(x_seq_scaled, verbose=0)

        # Ensemble weighted average
        weight_xgb  = self.metadata.get("weight_xgb",  0.45)
        weight_lstm = self.metadata.get("weight_lstm", 0.55)
        ensemble_prob = (weight_xgb * xgb_prob) + (weight_lstm * lstm_prob)

        # Final prediction
        signal_idx  = int(np.argmax(ensemble_prob[0]))
        confidence  = float(ensemble_prob[0][signal_idx])

        return {
            "signal"     : signal_idx,
            "signal_name": LABELS[signal_idx],
            "emoji"      : EMOJI[signal_idx],
            "confidence" : confidence,
            "prob_sell"  : float(ensemble_prob[0][0]),
            "prob_hold"  : float(ensemble_prob[0][1]),
            "prob_buy"   : float(ensemble_prob[0][2]),
        }
