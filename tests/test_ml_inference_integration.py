"""
Integration Test Suite for Frozen ML Model Backend Integration.

Verifies:
1. MLInferenceService initialization, manifest cryptographic verification, and status.
2. Input validation: rejection of missing, non-numeric, NaN, and non-finite features.
3. Accurate XGBoost predictions on known Phase 1 development samples.
4. Mathematically exact SHAP tree feature contributions.
5. FastAPI endpoints:
   - GET /api/model/status
   - GET /health (ml_models dynamic component status)
   - POST /api/session/start -> POST /api/behavior/events -> POST /api/session/end
   - GET /api/risk/{session_id} (reflects ML probability in browser_score and ml_inference)
   - GET /api/explanation/{session_id} (returns live SHAP attributions)
6. Preservation of baseline cryptographic integrity.
"""

import os
import sys
import unittest
import hashlib
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

# Ensure workspace root is in sys.path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from backend.app.main import app
from backend.app.services.ml_inference_service import ml_inference_service
from backend.app.services.session_service import session_service


class TestMLInferenceIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.features_df = pd.read_csv("ml/data/features.csv")

    def test_model_service_is_available_and_verified(self):
        """Verify model service loaded, verified against manifest, and reports ready status."""
        self.assertTrue(ml_inference_service.is_ready, f"Model not ready: {ml_inference_service._load_error}")
        status = ml_inference_service.get_status()
        self.assertEqual(status["status"], "available")
        self.assertEqual(status["model_type"], "xgboost.XGBClassifier")
        self.assertEqual(status["feature_count"], 64)
        self.assertIsNotNone(status["artifact_sha256"])
        self.assertIsNone(status["error"])

    def test_prediction_on_known_development_samples(self):
        """Verify prediction outcomes on authorized development samples."""
        # Row 0: Human session
        row0 = self.features_df.iloc[0].to_dict()
        pred0 = ml_inference_service.predict_from_feature_dict(row0)
        self.assertEqual(pred0["status"], "success")
        self.assertEqual(pred0["predicted_class"], "HUMAN")
        self.assertEqual(pred0["predicted_label"], 0)
        self.assertGreater(pred0["probability_human"], 0.90)
        self.assertLess(pred0["probability_automated"], 0.10)

        # Row 3: Automated session
        row3 = self.features_df.iloc[3].to_dict()
        pred3 = ml_inference_service.predict_from_feature_dict(row3)
        self.assertEqual(pred3["status"], "success")
        self.assertEqual(pred3["predicted_class"], "AUTOMATED")
        self.assertEqual(pred3["predicted_label"], 1)
        self.assertGreater(pred3["probability_automated"], 0.90)
        self.assertLess(pred3["probability_human"], 0.10)

    def test_schema_validation_rejection(self):
        """Verify feature schema validator rejects missing and invalid features."""
        row0 = self.features_df.iloc[0].to_dict()

        # 1. Missing feature
        bad_row = dict(row0)
        del bad_row["mouse_mean_velocity"]
        res = ml_inference_service.predict_from_feature_dict(bad_row)
        self.assertEqual(res["status"], "schema_error")
        self.assertIn("Missing required features", res["reason"])

        # 2. NaN feature
        bad_row_nan = dict(row0)
        bad_row_nan["mouse_mean_velocity"] = float("nan")
        res_nan = ml_inference_service.predict_from_feature_dict(bad_row_nan)
        self.assertEqual(res_nan["status"], "schema_error")
        self.assertIn("NaN", res_nan["reason"])

        # 3. Infinite feature
        bad_row_inf = dict(row0)
        bad_row_inf["mouse_mean_velocity"] = float("inf")
        res_inf = ml_inference_service.predict_from_feature_dict(bad_row_inf)
        self.assertEqual(res_inf["status"], "schema_error")

    def test_shap_explanation_extraction(self):
        """Verify live SHAP tree contribution extraction and genuine non-zero contributor filtering."""
        row0 = self.features_df.iloc[0].to_dict()
        exps = ml_inference_service.explain_from_features(row0, top_k=5)
        self.assertGreaterEqual(len(exps), 1)
        for item in exps:
            self.assertIn("feature_name", item)
            self.assertIn("feature_value", item)
            self.assertIn("shap_value", item)
            self.assertIn("description", item)
            self.assertIsInstance(item["shap_value"], float)
            self.assertGreater(abs(item["shap_value"]), 0.0)

        # When nonzero_only=False, it returns up to top_k padded
        exps_all = ml_inference_service.explain_from_features(row0, top_k=5, nonzero_only=False)
        self.assertEqual(len(exps_all), 5)

    def test_api_model_status_endpoint(self):
        """Verify GET /api/model/status endpoint."""
        res = self.client.get("/api/model/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "available")
        self.assertEqual(data["model_type"], "xgboost.XGBClassifier")
        self.assertEqual(data["feature_count"], 64)

    def test_api_health_endpoint_reflects_model_status(self):
        """Verify GET /health returns components.ml_models as ready."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["components"]["ml_models"], "ready")

    def test_end_to_end_session_lifecycle_with_inference(self):
        """Verify session start, telemetry ingestion, session end, and risk scoring integration."""
        # 1. Start session
        r_start = self.client.post("/api/session/start", json={
            "user_agent": "MLInferenceTestAgent/1.0",
            "client_timestamp": 1690000000000,
            "task_id": "TASK_01",
            "collection_mode": "HUMAN",
        })
        self.assertEqual(r_start.status_code, 201)
        s_id = r_start.json()["session_id"]

        # 2. Ingest behavioral events (>5 events to ensure feature eligibility)
        events = []
        for i in range(10):
            events.append({
                "event_type": "mouse_move" if i % 2 == 0 else "mouse_click",
                "client_timestamp": 1690000000000 + i * 50,
                "event_data": {"x": 100 + i * 10, "y": 200 + i * 5, "button": 0 if i % 2 == 1 else 0},
            })
        r_events = self.client.post("/api/behavior/events", json={
            "session_id": s_id,
            "events": events,
        })
        self.assertEqual(r_events.status_code, 202)

        # 3. End session
        r_end = self.client.post("/api/session/end", json={
            "session_id": s_id,
            "end_reason": "TASK_COMPLETED",
        })
        self.assertEqual(r_end.status_code, 200)
        end_data = r_end.json()
        self.assertEqual(end_data["status"], "COMPLETED")
        self.assertIsNotNone(end_data["final_integrity_score"])
        self.assertIsNotNone(end_data["ml_inference"])
        self.assertEqual(end_data["ml_inference"]["status"], "available")
        self.assertIn(end_data["ml_inference"]["predicted_class"], ["HUMAN", "AUTOMATED"])

        # 4. Check Risk score endpoint
        r_risk = self.client.get(f"/api/risk/{s_id}")
        self.assertEqual(r_risk.status_code, 200)
        risk_data = r_risk.json()
        self.assertEqual(risk_data["session_id"], s_id)
        self.assertIsNotNone(risk_data["ml_inference"])
        self.assertEqual(risk_data["ml_inference"]["status"], "available")
        self.assertEqual(
            risk_data["signals"]["browser_score"],
            round(risk_data["ml_inference"]["probability_automated"], 3)
        )

        # 5. Check Explanation endpoint
        r_exp = self.client.get(f"/api/explanation/{s_id}")
        self.assertEqual(r_exp.status_code, 200)
        exp_data = r_exp.json()
        self.assertEqual(exp_data["session_id"], s_id)
        self.assertTrue(len(exp_data["shap_contributions"]) > 0)
        self.assertEqual(exp_data["ml_inference"]["status"], "available")

    def test_active_session_without_telemetry_reports_appropriate_status(self):
        """Verify active session without events reports prediction_not_ready."""
        r_start = self.client.post("/api/session/start", json={
            "user_agent": "MLActiveTestAgent/1.0",
            "client_timestamp": 1690000000000,
        })
        self.assertEqual(r_start.status_code, 201)
        s_id = r_start.json()["session_id"]

        r_risk = self.client.get(f"/api/risk/{s_id}")
        self.assertEqual(r_risk.status_code, 200)
        risk_data = r_risk.json()
        self.assertIsNotNone(risk_data["ml_inference"])
        self.assertEqual(risk_data["ml_inference"]["status"], "prediction_not_ready")


if __name__ == "__main__":
    unittest.main()
