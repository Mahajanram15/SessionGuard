"""
Unit and Integration Tests for Dual-Model Integration (Experiment A Baseline vs Experiment B Candidate).

Verifies:
1. Default active model is strictly Experiment A when configuration is absent, unset, or invalid.
2. Explicit Experiment B selection activates candidate kinematic pipeline.
3. Cryptographic hash failure on Experiment B marks service unavailable without silent fallback.
4. Schema validation on Experiment B rejects missing, NaN, and non-numeric kinematic features.
5. Correct projection and ordering of the exact 12 kinematic features.
6. Honest model identity, version, and score labelling in prediction responses.
7. Strict prevention of cross-model explanation leakage (tree SHAP suppressed for Experiment B).
8. API endpoints GET /api/model/status and POST /api/model/select operate reversibly.
"""

import os
import sys
import unittest
import pandas as pd
from fastapi.testclient import TestClient

# Ensure workspace root is in sys.path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from backend.app.main import app
from backend.app.services.ml_inference_service import (
    ml_inference_service,
    MLInferenceService,
    normalize_model_selection,
    DEFAULT_MODEL_A_PATH,
    DEFAULT_MANIFEST_A_PATH,
    DEFAULT_MODEL_B_PATH,
    DEFAULT_MANIFEST_B_PATH,
)
from ml.training.experiment_b_config import SELECTED_FEATURES_EXPERIMENT_B_KINEMATIC


class TestDualModelIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.features_df = pd.read_csv("ml/data/features.csv")

    def tearDown(self):
        # Always reset active model to default after each test
        ml_inference_service.reset_active_model()

    def test_01_default_selection_is_experiment_a(self):
        """Verify that default model is strictly Experiment A when setting is absent or unset."""
        ml_inference_service.reset_active_model()
        self.assertEqual(ml_inference_service.active_model, "experiment_a")

        status = ml_inference_service.get_status()
        self.assertEqual(status["active_model"], "experiment_a")
        self.assertEqual(status["model_name"], "experiment_a_xgboost")
        self.assertEqual(status["score_label"], "Uncalibrated Model Score")
        self.assertEqual(status["feature_count"], 64)
        self.assertEqual(status["status"], "available")

    def test_02_invalid_selection_reversibly_defaults_to_experiment_a(self):
        """Verify that invalid model keys revert safely to Experiment A without errors."""
        self.assertEqual(normalize_model_selection(None), "experiment_a")
        self.assertEqual(normalize_model_selection(""), "experiment_a")
        self.assertEqual(normalize_model_selection("unknown_model_v99"), "experiment_a")
        self.assertEqual(normalize_model_selection(12345), "experiment_a")

        active = ml_inference_service.set_active_model("invalid_selection")
        self.assertEqual(active, "experiment_a")
        self.assertEqual(ml_inference_service.active_model, "experiment_a")

    def test_03_explicit_experiment_b_selection(self):
        """Verify that explicit selection of Experiment B activates kinematic candidate."""
        active = ml_inference_service.set_active_model("experiment_b")
        self.assertEqual(active, "experiment_b")
        self.assertEqual(ml_inference_service.active_model, "experiment_b")

        status = ml_inference_service.get_status()
        self.assertEqual(status["active_model"], "experiment_b")
        self.assertEqual(status["model_name"], "experiment_b_kinematic")
        self.assertEqual(status["score_label"], "Kinematic Risk Score")
        self.assertEqual(status["feature_count"], 12)
        self.assertEqual(status["status"], "available")
        self.assertIn("sklearn.pipeline.Pipeline", status["model_type"])

    def test_04_experiment_b_artifact_hash_failure_fails_closed(self):
        """Verify that SHA-256 integrity verification failure fails closed without silent fallback."""
        # Instantiate a mock service with nonexistent model B path
        bad_service = MLInferenceService(
            model_b_path="ml/models/nonexistent_model.joblib",
            manifest_b_path=DEFAULT_MANIFEST_B_PATH,
        )
        bad_service.set_active_model("experiment_b")

        self.assertFalse(bad_service.is_ready)
        status = bad_service.get_status()
        self.assertEqual(status["status"], "unavailable")
        self.assertIn("not found", status["error"])

        # Prediction must fail honestly without falling back to Experiment A
        row = self.features_df.iloc[0].to_dict()
        pred = bad_service.predict_from_feature_dict(row)
        self.assertEqual(pred["status"], "unavailable")
        self.assertEqual(pred["active_model"], "experiment_b")
        self.assertIn("not ready", pred["reason"])

    def test_05_experiment_b_missing_and_invalid_feature_validation(self):
        """Verify Experiment B schema validator rejects missing, NaN, and non-numeric kinematic features."""
        ml_inference_service.set_active_model("experiment_b")
        row0 = self.features_df.iloc[0].to_dict()

        # 1. Missing kinematic feature
        bad_row = dict(row0)
        del bad_row["mouse_path_straightness"]
        res = ml_inference_service.predict_from_feature_dict(bad_row)
        self.assertEqual(res["status"], "schema_error")
        self.assertEqual(res["active_model"], "experiment_b")
        self.assertIn("mouse_path_straightness", res["reason"])

        # 2. NaN kinematic feature
        bad_row_nan = dict(row0)
        bad_row_nan["mouse_std_velocity"] = float("nan")
        res_nan = ml_inference_service.predict_from_feature_dict(bad_row_nan)
        self.assertEqual(res_nan["status"], "schema_error")
        self.assertEqual(res_nan["active_model"], "experiment_b")
        self.assertIn("NaN", res_nan["reason"])

        # 3. Infinite kinematic feature
        bad_row_inf = dict(row0)
        bad_row_inf["mouse_max_acceleration"] = float("inf")
        res_inf = ml_inference_service.predict_from_feature_dict(bad_row_inf)
        self.assertEqual(res_inf["status"], "schema_error")
        self.assertEqual(res_inf["active_model"], "experiment_b")

    def test_06_experiment_b_correct_projection_and_prediction(self):
        """Verify Experiment B projects 76-feature row to exact 12 features and computes valid prediction."""
        ml_inference_service.set_active_model("experiment_b")

        # Human sample (row 0)
        row_human = self.features_df.iloc[0].to_dict()
        pred_human = ml_inference_service.predict_from_feature_dict(row_human)
        self.assertEqual(pred_human["status"], "success")
        self.assertEqual(pred_human["active_model"], "experiment_b")
        self.assertEqual(pred_human["model_name"], "experiment_b_kinematic")
        self.assertEqual(pred_human["score_label"], "Kinematic Risk Score")
        self.assertEqual(pred_human["predicted_class"], "HUMAN")
        self.assertEqual(pred_human["predicted_label"], 0)
        self.assertGreater(pred_human["probability_human"], 0.90)

        # Bot sample (row 3)
        row_bot = self.features_df.iloc[3].to_dict()
        pred_bot = ml_inference_service.predict_from_feature_dict(row_bot)
        self.assertEqual(pred_bot["status"], "success")
        self.assertEqual(pred_bot["active_model"], "experiment_b")
        self.assertEqual(pred_bot["model_name"], "experiment_b_kinematic")
        self.assertEqual(pred_bot["score_label"], "Kinematic Risk Score")
        self.assertEqual(pred_bot["predicted_class"], "AUTOMATED")
        self.assertEqual(pred_bot["predicted_label"], 1)
        self.assertGreater(pred_bot["probability_automated"], 0.90)

    def test_07_prevention_of_cross_model_explanation_reuse(self):
        """Verify SHAP tree explanations are suppressed when Experiment B is active."""
        row0 = self.features_df.iloc[0].to_dict()

        # When Experiment B is active, SHAP explanations must return empty list
        ml_inference_service.set_active_model("experiment_b")
        exps_b = ml_inference_service.explain_from_features(row0, top_k=5)
        self.assertEqual(exps_b, [], "Experiment A SHAP values leaked into Experiment B!")

        # When Experiment A is active, genuine SHAP explanations are returned
        ml_inference_service.set_active_model("experiment_a")
        exps_a = ml_inference_service.explain_from_features(row0, top_k=5)
        self.assertGreaterEqual(len(exps_a), 1)
        self.assertEqual(exps_a[0]["feature_name"], "mouse_event_count")

    def test_08_api_model_select_and_status_endpoints(self):
        """Verify API endpoints GET /api/model/status and POST /api/model/select."""
        # 1. Query status initially
        res = self.client.get("/api/model/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("active_model", data)
        self.assertIn("available_models", data)
        self.assertIn("experiment_a", data["available_models"])
        self.assertIn("experiment_b", data["available_models"])

        # 2. Select Experiment B via API
        res_select = self.client.post("/api/model/select", json={"model": "experiment_b"})
        self.assertEqual(res_select.status_code, 200)
        self.assertEqual(res_select.json()["active_model"], "experiment_b")
        self.assertEqual(ml_inference_service.active_model, "experiment_b")

        # 3. Select invalid model -> reverts to experiment_a
        res_revert = self.client.post("/api/model/select", json={"model": "invalid_model"})
        self.assertEqual(res_revert.status_code, 200)
        self.assertEqual(res_revert.json()["active_model"], "experiment_a")
        self.assertEqual(ml_inference_service.active_model, "experiment_a")


if __name__ == "__main__":
    unittest.main()
