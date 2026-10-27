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


DEFAULT_MODEL_A_PATH = "ml/models/experiment_a_xgboost.joblib"
DEFAULT_MANIFEST_A_PATH = "ml/models/experiment_a_manifest.json"
DEFAULT_MODEL_B_PATH = "ml/models/experiment_b_logistic_regression.joblib"
DEFAULT_MANIFEST_B_PATH = "ml/models/experiment_b_manifest.json"


def normalize_model_selection(model_key: Optional[str]) -> str:
    """
    Normalizes an input string to an authoritative model selection key ('experiment_a' or 'experiment_b').
    Strictly defaults to 'experiment_a' when the setting is absent, invalid, or unset.
    """
    if not model_key or not isinstance(model_key, str):
        return "experiment_a"
    norm = model_key.strip().lower()
    if norm in ("experiment_b", "b", "exp_b", "candidate_b", "experiment_b_kinematic"):
        return "experiment_b"
    return "experiment_a"


class MLInferenceService:
    """
    Dual-model inference service managing:
    1. Frozen Experiment A baseline (XGBoost 64-feature demonstration model).
    2. Candidate Experiment B (Scale-free kinematic classifier with StandardScaler + Logistic Regression).

    Guarantees:
    - Experiment A is strictly the default active model.
    - Manifest cryptographic integrity (SHA-256) is verified before loading either model.
    - When Experiment B is active, features are projected strictly to its 12 kinematic features.
    - Zero silent fallback: failures on Experiment B return honest error states.
    - SHAP tree explanations are strictly suppressed for Experiment B to prevent cross-model attribution leakage.
    """

    def __init__(
        self,
        model_path: str = DEFAULT_MODEL_A_PATH,
        manifest_path: str = DEFAULT_MANIFEST_A_PATH,
        model_b_path: str = DEFAULT_MODEL_B_PATH,
        manifest_b_path: str = DEFAULT_MANIFEST_B_PATH,
    ):
        self.model_path = os.path.abspath(os.path.join(workspace_root, model_path))
        self.manifest_path = os.path.abspath(os.path.join(workspace_root, manifest_path))
        self.model_b_path = os.path.abspath(os.path.join(workspace_root, model_b_path))
        self.manifest_b_path = os.path.abspath(os.path.join(workspace_root, manifest_b_path))

        self._configured_active_model: Optional[str] = None

        # Experiment A state
        self._model: Optional[xgb.XGBClassifier] = None
        self._manifest: Optional[Dict[str, Any]] = None
        self._ordered_features: List[str] = []
        self._is_ready: bool = False
        self._load_error: Optional[str] = None
        self._artifact_sha256: Optional[str] = None
        self._threshold: float = 0.50

        # Experiment B state
        self._model_b: Optional[Any] = None
        self._manifest_b: Optional[Dict[str, Any]] = None
        self._ordered_features_b: List[str] = []
        self._is_ready_b: bool = False
        self._load_error_b: Optional[str] = None
        self._artifact_sha256_b: Optional[str] = None
        self._threshold_b: float = 0.50

        # Attempt initial loads
        self._load_model()
        self._load_model_b()

    def _compute_sha256(self, file_path: str) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest().lower()

    def _load_model(self) -> None:
        """
        Validates artifact presence, manifest integrity, and loads Experiment A into memory.
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

    def _load_model_b(self) -> None:
        """
        Validates artifact presence, manifest integrity, and loads candidate Experiment B into memory.
        """
        try:
            if not os.path.exists(self.model_b_path):
                self._is_ready_b = False
                self._load_error_b = f"Experiment B model artifact not found at: {self.model_b_path}"
                return

            if not os.path.exists(self.manifest_b_path):
                self._is_ready_b = False
                self._load_error_b = f"Experiment B manifest artifact not found at: {self.manifest_b_path}"
                return

            with open(self.manifest_b_path, "r", encoding="utf-8") as f:
                self._manifest_b = json.load(f)

            expected_sha256 = (
                self._manifest_b.get("model_artifact", {}).get("artifact_sha256", "").lower()
                or self._manifest_b.get("artifact_integrity", {}).get("artifact_sha256", "").lower()
            )
            live_sha256 = self._compute_sha256(self.model_b_path)
            self._artifact_sha256_b = live_sha256

            if not expected_sha256 or live_sha256 != expected_sha256:
                self._is_ready_b = False
                self._load_error_b = (
                    f"Experiment B integrity check failed! Expected SHA-256 '{expected_sha256}', "
                    f"got live digest '{live_sha256}'."
                )
                return

            feat_config = self._manifest_b.get("feature_configuration", {})
            self._ordered_features_b = feat_config.get("ordered_features", [])
            if len(self._ordered_features_b) != 12:
                self._is_ready_b = False
                self._load_error_b = (
                    f"Invalid Experiment B feature schema: expected 12 ordered features, got {len(self._ordered_features_b)}"
                )
                return

            self._threshold_b = float(
                self._manifest_b.get("decision_policy", {}).get("default_decision_threshold", 0.50)
            )

            self._model_b = joblib.load(self.model_b_path)
            if not hasattr(self._model_b, "predict") or not hasattr(self._model_b, "predict_proba"):
                self._is_ready_b = False
                self._load_error_b = "Loaded Experiment B artifact does not implement predict or predict_proba interface."
                return

            self._is_ready_b = True
            self._load_error_b = None
        except Exception as e:
            self._is_ready_b = False
            self._load_error_b = f"Exception loading Experiment B candidate: {str(e)}"

    @property
    def active_model(self) -> str:
        """
        Returns the active model key ('experiment_a' or 'experiment_b').
        Precedence:
        1. Dynamic override via set_active_model()
        2. Environment variables CROSSTRACE_ACTIVE_MODEL or ACTIVE_MODEL
        3. Fallback: 'experiment_a'
        """
        if self._configured_active_model:
            return normalize_model_selection(self._configured_active_model)
        env_val = os.environ.get("CROSSTRACE_ACTIVE_MODEL", os.environ.get("ACTIVE_MODEL", ""))
        return normalize_model_selection(env_val)

    def set_active_model(self, model_key: Optional[str]) -> str:
        """
        Dynamically selects the active model ('experiment_a' or 'experiment_b').
        Reversibly defaults to 'experiment_a' if model_key is absent or invalid.
        """
        self._configured_active_model = normalize_model_selection(model_key)
        return self._configured_active_model

    def reset_active_model(self) -> None:
        """Resets dynamic override to environment default."""
        self._configured_active_model = None

    @property
    def is_ready(self) -> bool:
        if self.active_model == "experiment_b":
            return self._is_ready_b
        return self._is_ready

    @property
    def model_name(self) -> str:
        if self.active_model == "experiment_b":
            return "experiment_b_kinematic"
        return "experiment_a_xgboost"

    @property
    def model_version(self) -> Optional[str]:
        if self.active_model == "experiment_b":
            if self._manifest_b:
                return self._manifest_b.get("model_metadata", {}).get("model_version")
            return None
        if self._manifest:
            return self._manifest.get("model_metadata", {}).get("model_version")
        return None

    @property
    def model_type(self) -> Optional[str]:
        if self.active_model == "experiment_b":
            if self._manifest_b:
                return self._manifest_b.get("model_metadata", {}).get("model_type")
            return None
        if self._manifest:
            return self._manifest.get("model_metadata", {}).get("model_type")
        return None

    @property
    def score_label(self) -> str:
        if self.active_model == "experiment_b":
            return "Kinematic Risk Score"
        return "Uncalibrated Model Score"

    def get_status(self) -> Dict[str, Any]:
        """Returns the operational status, version, and integrity digest of the active model and candidate models."""
        active = self.active_model
        is_b = active == "experiment_b"

        return {
            "status": "available" if self.is_ready else "unavailable",
            "active_model": active,
            "model_name": self.model_name,
            "model_type": self.model_type,
            "model_version": self.model_version,
            "score_label": self.score_label,
            "decision_threshold": self._threshold_b if is_b else self._threshold,
            "feature_count": len(self._ordered_features_b if is_b else self._ordered_features),
            "artifact_sha256": self._artifact_sha256_b if is_b else self._artifact_sha256,
            "model_path": self.model_b_path if is_b else self.model_path,
            "manifest_path": self.manifest_b_path if is_b else self.manifest_path,
            "error": self._load_error_b if is_b else self._load_error,
            "available_models": {
                "experiment_a": {
                    "status": "available" if self._is_ready else "unavailable",
                    "model_name": "experiment_a_xgboost",
                    "model_version": self._manifest.get("model_metadata", {}).get("model_version") if self._manifest else None,
                    "feature_count": len(self._ordered_features),
                    "artifact_sha256": self._artifact_sha256,
                    "error": self._load_error,
                },
                "experiment_b": {
                    "status": "available" if self._is_ready_b else "unavailable",
                    "model_name": "experiment_b_kinematic",
                    "model_version": self._manifest_b.get("model_metadata", {}).get("model_version") if self._manifest_b else None,
                    "feature_count": len(self._ordered_features_b),
                    "artifact_sha256": self._artifact_sha256_b,
                    "error": self._load_error_b,
                },
            },
        }

    def predict_from_feature_dict(self, features_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes prediction to the active model:
        - If active model is 'experiment_a', uses the 64-feature XGBoost baseline.
        - If active model is 'experiment_b', projects to 12 kinematic features and runs the candidate pipeline.
        Never silently falls back between models.
        """
        if self.active_model == "experiment_b":
            return self._predict_experiment_b(features_dict)
        return self._predict_experiment_a(features_dict)

    def _predict_experiment_a(self, features_dict: Dict[str, Any]) -> Dict[str, Any]:
        if not self._is_ready or self._model is None:
            return {
                "status": "unavailable",
                "active_model": "experiment_a",
                "reason": f"Experiment A model is not ready: {self._load_error}",
            }

        if not isinstance(features_dict, dict):
            return {
                "status": "schema_error",
                "active_model": "experiment_a",
                "reason": f"Expected feature dictionary, got {type(features_dict)}",
            }

        missing = [f for f in self._ordered_features if f not in features_dict]
        if missing:
            return {
                "status": "schema_error",
                "active_model": "experiment_a",
                "reason": f"Missing required features ({len(missing)}): {missing[:5]}",
            }

        row: List[float] = []
        for feat in self._ordered_features:
            val = features_dict[feat]
            if not isinstance(val, (int, float, np.number)) or np.isnan(val) or np.isinf(val):
                return {
                    "status": "schema_error",
                    "active_model": "experiment_a",
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
                "active_model": "experiment_a",
                "model_name": "experiment_a_xgboost",
                "model_version": self.model_version,
                "model_type": self.model_type,
                "score_label": "Uncalibrated Model Score",
                "predicted_label": pred_label,
                "predicted_class": "HUMAN" if pred_label == 0 else "AUTOMATED",
                "probability_human": round(prob_human, 4),
                "probability_automated": round(prob_automated, 4),
                "decision_threshold": self._threshold,
                "demonstration_note": "Pilot demonstration model fitted on 53 Phase 1 development sessions.",
            }
        except Exception as e:
            return {
                "status": "prediction_error",
                "active_model": "experiment_a",
                "reason": f"Inference execution failed: {str(e)}",
            }

    def _predict_experiment_b(self, features_dict: Dict[str, Any]) -> Dict[str, Any]:
        if not self._is_ready_b or self._model_b is None:
            return {
                "status": "unavailable",
                "active_model": "experiment_b",
                "reason": f"Experiment B candidate model is not ready: {self._load_error_b}",
            }

        if not isinstance(features_dict, dict):
            return {
                "status": "schema_error",
                "active_model": "experiment_b",
                "reason": f"Expected feature dictionary, got {type(features_dict)}",
            }

        missing = [f for f in self._ordered_features_b if f not in features_dict]
        if missing:
            return {
                "status": "schema_error",
                "active_model": "experiment_b",
                "reason": f"Missing required Experiment B kinematic features ({len(missing)}): {missing}",
            }

        row: List[float] = []
        for feat in self._ordered_features_b:
            val = features_dict[feat]
            if not isinstance(val, (int, float, np.number)) or np.isnan(val) or np.isinf(val):
                return {
                    "status": "schema_error",
                    "active_model": "experiment_b",
                    "reason": f"Non-numeric, NaN, or infinite value detected for Experiment B feature '{feat}': {val}",
                }
            row.append(float(val))

        try:
            X = pd.DataFrame([row], columns=self._ordered_features_b)
            pred_label = int(self._model_b.predict(X)[0])
            probs = self._model_b.predict_proba(X)[0]
            prob_human = float(probs[0])
            prob_automated = float(probs[1])

            return {
                "status": "success",
                "active_model": "experiment_b",
                "model_name": "experiment_b_kinematic",
                "model_version": self.model_version,
                "model_type": self.model_type,
                "score_label": "Kinematic Risk Score",
                "predicted_label": pred_label,
                "predicted_class": "HUMAN" if pred_label == 0 else "AUTOMATED",
                "probability_human": round(prob_human, 4),
                "probability_automated": round(prob_automated, 4),
                "decision_threshold": self._threshold_b,
                "demonstration_note": (
                    "Candidate kinematic model evaluated on 53 Phase 1 sessions. "
                    "Validated only against current synthetic bot profiles."
                ),
            }
        except Exception as e:
            return {
                "status": "prediction_error",
                "active_model": "experiment_b",
                "reason": f"Experiment B inference execution failed: {str(e)}",
            }

    def explain_from_features(
        self, features_dict: Dict[str, Any], top_k: int = 5, nonzero_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Computes mathematically exact tree SHAP values for Experiment A (XGBoost).
        When Experiment B is active, returns an empty list to strictly prevent
        cross-model explanation leakage.
        """
        if self.active_model == "experiment_b":
            # Feature attributions are suppressed for Experiment B to prevent cross-model SHAP leakage
            return []

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

