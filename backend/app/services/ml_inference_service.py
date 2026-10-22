"""
CrossTrace ML Inference Service.

Orchestrates loading, pre-load cryptographic verification, input schema validation,
live inference, and localized SHAP tree explainability for the frozen Experiment A XGBoost model.
"""

from typing import Dict, Any, List, Optional
import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb

# Ensure workspace root is in sys.path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)


FEATURE_DESCRIPTIONS: Dict[str, str] = {
    "mouse_event_count": "Total count of cursor movement samples captured during the session.",
    "mouse_total_distance_px": "Cumulative Euclidean distance traversed by the pointer in pixels.",
    "mouse_mean_velocity": "Average cursor traversal velocity across movement strokes (px/ms).",
    "mouse_std_velocity": "Variance and dispersion in cursor velocity, indicating motor naturalness.",
    "mouse_max_velocity": "Peak instantaneous cursor movement speed observed during interaction.",
    "mouse_mean_acceleration": "Mean rate of change in pointer speed across consecutive vectors.",
    "mouse_std_acceleration": "Jitter and irregularity in pointer acceleration and deceleration.",
    "mouse_max_acceleration": "Peak instantaneous pointer acceleration.",
    "mouse_direction_change_count": "Count of angular directional shifts exceeding motor thresholds.",
    "mouse_direction_change_rate": "Frequency of directional adjustments per unit of cursor distance.",
    "mouse_mean_direction_change": "Mean angular deviation across directional change points.",
    "mouse_pause_count": "Count of periods where pointer movement remained stationary.",
    "mouse_mean_pause_ms": "Average duration of pointer pauses between movement strokes.",
    "mouse_max_pause_ms": "Longest single pause duration observed during pointer movement.",
    "mouse_path_straightness": "Ratio of start-to-end displacement over total curvilinear path length.",
    "click_count": "Total count of mouse button click interactions.",
    "click_rate": "Click interactions per second over the active session duration.",
    "mean_click_interval_ms": "Mean latency between consecutive click interactions.",
    "std_click_interval_ms": "Standard deviation in inter-click intervals, capturing rhythmic regularity.",
    "min_click_interval_ms": "Shortest duration observed between successive clicks.",
    "max_click_interval_ms": "Longest duration observed between successive clicks.",
    "button_click_ratio": "Proportion of clicks landing on semantic HTML button elements.",
    "link_click_ratio": "Proportion of clicks landing on anchor navigation hyperlinks.",
    "input_click_ratio": "Proportion of clicks targeting form input or textarea elements.",
    "other_click_ratio": "Proportion of clicks on non-interactive or structural container elements.",
    "key_event_count": "Total count of keyboard events (keydown and keyup metadata only).",
    "mean_dwell_ms": "Mean key hold time between keydown and keyup transitions.",
    "std_dwell_ms": "Natural physiological variance in key hold duration.",
    "min_dwell_ms": "Shortest keypress hold duration observed.",
    "max_dwell_ms": "Longest keypress hold duration observed.",
    "mean_flight_ms": "Mean latency between successive keystrokes (flight time).",
    "std_flight_ms": "Variance in typing flight time, distinguishing human cadence from fixed delays.",
    "min_flight_ms": "Minimum flight duration observed between consecutive keypresses.",
    "max_flight_ms": "Maximum flight duration observed between consecutive keypresses.",
    "mean_inter_key_interval_ms": "Mean interval between keystroke onset timestamps.",
    "std_inter_key_interval_ms": "Standard deviation of inter-key intervals.",
    "typing_speed": "Estimated keystroke entry rate in characters per second.",
    "scroll_event_count": "Total count of window and container scroll telemetry samples.",
    "total_scroll_distance": "Cumulative vertical and horizontal scroll offset traversed in pixels.",
    "mean_scroll_velocity": "Average scroll velocity across scrolling strokes.",
    "std_scroll_velocity": "Variance in scroll velocity over active scroll windows.",
    "max_scroll_velocity": "Peak instantaneous scroll velocity observed.",
    "upward_scroll_ratio": "Proportion of scroll movement directed upward.",
    "downward_scroll_ratio": "Proportion of scroll movement directed downward.",
    "scroll_direction_change_count": "Count of reversals in scroll direction.",
    "mean_scroll_interval_ms": "Mean latency between successive scroll event batches.",
    "scroll_burst_count": "Count of distinct, clustered scrolling interaction bursts.",
    "navigation_count": "Total count of client-side route transitions and page visits.",
    "unique_route_count": "Number of unique URL paths visited during the session.",
    "mean_page_dwell_ms": "Average dwell duration spent per unique route view.",
    "std_page_dwell_ms": "Variance in page dwell duration across visited routes.",
    "min_page_dwell_ms": "Shortest duration spent on any single route view.",
    "max_page_dwell_ms": "Longest duration spent on any single route view.",
    "navigation_rate": "Route transitions per minute of active session interaction.",
    "repeated_route_count": "Count of route views returning to previously visited paths.",
    "route_repetition_ratio": "Proportion of total route transitions that revisited existing paths.",
    "visibility_event_count": "Total count of document visibility state transitions.",
    "total_time_away_ms": "Total time spent with browser document hidden or blurred.",
    "mean_time_away_ms": "Average duration per document blur or hidden event.",
    "total_behavior_event_count": "Consolidated count of all raw interaction telemetry events.",
    "events_per_second": "Consolidated interaction density across all telemetry channels.",
    "mouse_to_click_ratio": "Ratio of cursor movement events per click interaction.",
    "click_to_navigation_ratio": "Ratio of click interactions per route transition.",
    "navigation_to_session_ratio": "Navigation transitions relative to total session duration.",
}


class MLInferenceService:
    """
    Singleton service managing the lifecycle of the frozen Experiment A model.
    Enforces manifest cryptographic integrity before loading, validates feature schema,
    and returns genuine XGBoost predictions and localized SHAP explanations.
    """

    def __init__(
        self,
        model_path: str = "ml/models/experiment_a_xgboost.joblib",
        manifest_path: str = "ml/models/experiment_a_manifest.json",
    ):
        self.model_path = os.path.abspath(os.path.join(workspace_root, model_path))
        self.manifest_path = os.path.abspath(os.path.join(workspace_root, manifest_path))
        self._model: Optional[xgb.XGBClassifier] = None
        self._manifest: Optional[Dict[str, Any]] = None
        self._ordered_features: List[str] = []
        self._is_ready: bool = False
        self._load_error: Optional[str] = None
        self._artifact_sha256: Optional[str] = None
        self._threshold: float = 0.50

        # Attempt safe initial load
        self._load_model()

    def _compute_sha256(self, file_path: str) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest().lower()

    def _load_model(self) -> None:
        """
        Validates artifact presence, manifest integrity, and loads the model into memory.
        Fails closed without crashing the host application.
        """
        try:
            if not os.path.exists(self.model_path):
                self._is_ready = False
                self._load_error = f"Model artifact not found at: {self.model_path}"
                return

            if not os.path.exists(self.manifest_path):
                self._is_ready = False
                self._load_error = f"Manifest artifact not found at: {self.manifest_path}"
                return

            # Read manifest
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self._manifest = json.load(f)

            expected_sha256 = (
                self._manifest.get("model_artifact", {}).get("artifact_sha256", "").lower()
            )
            live_sha256 = self._compute_sha256(self.model_path)
            self._artifact_sha256 = live_sha256

            if not expected_sha256 or live_sha256 != expected_sha256:
                self._is_ready = False
                self._load_error = (
                    f"Integrity check failed! Expected SHA-256 '{expected_sha256}', "
                    f"got live digest '{live_sha256}'."
                )
                return

            # Extract feature configuration & threshold
            feat_config = self._manifest.get("feature_configuration", {})
            self._ordered_features = feat_config.get("ordered_features", [])
            if len(self._ordered_features) != 64:
                self._is_ready = False
                self._load_error = (
                    f"Invalid feature schema: expected 64 ordered features, got {len(self._ordered_features)}"
                )
                return

            self._threshold = float(
                self._manifest.get("decision_policy", {}).get("default_decision_threshold", 0.50)
            )

            # Load model artifact
            self._model = joblib.load(self.model_path)
            if not hasattr(self._model, "predict") or not hasattr(self._model, "predict_proba"):
                self._is_ready = False
                self._load_error = "Loaded artifact does not implement predict or predict_proba interface."
                return

            self._is_ready = True
            self._load_error = None

        except Exception as e:
            self._is_ready = False
            self._load_error = f"Exception loading frozen model: {str(e)}"

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    @property
    def model_version(self) -> Optional[str]:
        if self._manifest:
            return self._manifest.get("model_metadata", {}).get("model_version")
        return None

    @property
    def model_type(self) -> Optional[str]:
        if self._manifest:
            return self._manifest.get("model_metadata", {}).get("model_type")
        return None

    def get_status(self) -> Dict[str, Any]:
        """Returns the operational status, version, and integrity digest of the model."""
        return {
            "status": "available" if self._is_ready else "unavailable",
            "model_type": self.model_type,
            "model_version": self.model_version,
            "decision_threshold": self._threshold,
            "feature_count": len(self._ordered_features),
            "artifact_sha256": self._artifact_sha256,
            "model_path": self.model_path,
            "manifest_path": self.manifest_path,
            "error": self._load_error,
        }

    def predict_from_feature_dict(self, features_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates input features, extracts the 64 canonical features in order,
        and computes class predictions and probabilities.
        """
        if not self._is_ready or self._model is None:
            return {
                "status": "unavailable",
                "reason": f"ML model is not ready: {self._load_error}",
            }

        if not isinstance(features_dict, dict):
            return {
                "status": "schema_error",
                "reason": f"Expected feature dictionary, got {type(features_dict)}",
            }

        # Check for missing features
        missing = [f for f in self._ordered_features if f not in features_dict]
        if missing:
            return {
                "status": "schema_error",
                "reason": f"Missing required features ({len(missing)}): {missing[:5]}",
            }

        # Validate numeric types and finite values
        row: List[float] = []
        for feat in self._ordered_features:
            val = features_dict[feat]
            if not isinstance(val, (int, float, np.number)) or np.isnan(val) or np.isinf(val):
                return {
                    "status": "schema_error",
                    "reason": f"Non-numeric, NaN, or infinite value detected for feature '{feat}': {val}",
                }
            row.append(float(val))

        try:
            X = pd.DataFrame([row], columns=self._ordered_features)
            pred_label = int(self._model.predict(X)[0])
            probs = self._model.predict_proba(X)[0]
            prob_human = float(probs[0])
            prob_automated = float(probs[1])

            return {
                "status": "success",
                "predicted_label": pred_label,
                "predicted_class": "HUMAN" if pred_label == 0 else "AUTOMATED",
                "probability_human": round(prob_human, 4),
                "probability_automated": round(prob_automated, 4),
                "decision_threshold": self._threshold,
                "model_version": self.model_version,
                "model_type": self.model_type,
                "demonstration_note": "Pilot demonstration model fitted on 53 Phase 1 development sessions.",
            }
        except Exception as e:
            return {
                "status": "prediction_error",
                "reason": f"Inference execution failed: {str(e)}",
            }

    def explain_from_features(
        self, features_dict: Dict[str, Any], top_k: int = 5, nonzero_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Computes mathematically exact tree SHAP values for the 64 features using
        XGBoost's native pred_contribs interface and returns genuine feature drivers.
        When nonzero_only is True, skips features with 0.0 contribution.
        """
        if not self._is_ready or self._model is None:
            return []

        row: List[float] = []
        for feat in self._ordered_features:
            val = features_dict.get(feat, 0.0)
            if not isinstance(val, (int, float, np.number)) or np.isnan(val) or np.isinf(val):
                val = 0.0
            row.append(float(val))

        try:
            X = pd.DataFrame([row], columns=self._ordered_features)
            booster = self._model.get_booster()
            contribs = booster.predict(xgb.DMatrix(X), pred_contribs=True)[0]
            feat_contribs = contribs[:-1]  # discard bias intercept

            # Rank by absolute magnitude of contribution
            ranked_indices = np.argsort(np.abs(feat_contribs))[::-1]

            explanations: List[Dict[str, Any]] = []
            for idx in ranked_indices:
                shap_val = float(feat_contribs[idx])
                if nonzero_only and abs(shap_val) < 1e-4:
                    continue

                feat_name = self._ordered_features[idx]
                feat_val = row[idx]
                desc = FEATURE_DESCRIPTIONS.get(
                    feat_name, f"Behavioral dynamic metric: {feat_name}"
                )

                explanations.append({
                    "feature_name": feat_name,
                    "feature_value": round(feat_val, 4),
                    "shap_value": round(shap_val, 4),
                    "description": desc,
                })
                if len(explanations) >= top_k:
                    break

            return explanations
        except Exception:
            return []


# Global singleton instance
ml_inference_service = MLInferenceService()
