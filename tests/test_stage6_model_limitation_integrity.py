"""
Stage 6 Test Suite: Honest Model Limitation Display & Demo Integrity.

Verifies:
1. Model limitation disclosure semantics.
2. Genuine non-zero SHAP contributor filtering (no padding with zero-contribution features).
3. Explicit honest unavailable state when telemetry/explanation data is missing (no fabricated fallbacks).
4. Strict separation of scenario metadata (e.g. HUMAN, AUTOMATED) from model predictions.
5. Invariance of model probabilities and decision thresholds.
"""

import unittest
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.services.ml_inference_service import ml_inference_service
from backend.app.services.session_service import session_service


class TestStage6ModelLimitationIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = TestClient(cls.app)

    def test_01_nonzero_shap_filtering(self):
        """Verify that explain_from_features returns only genuine non-zero feature drivers."""
        # Create a mock 64-feature vector with only mouse_event_count set
        features = {f: 0.0 for f in ml_inference_service._ordered_features}
        features["mouse_event_count"] = 15.0

        # Default nonzero_only=True
        exps = ml_inference_service.explain_from_features(features, top_k=5, nonzero_only=True)
        # Because all splits in the frozen model are on mouse_event_count, only 1 feature has non-zero SHAP
        self.assertEqual(len(exps), 1)
        self.assertEqual(exps[0]["feature_name"], "mouse_event_count")
        self.assertGreater(abs(exps[0]["shap_value"]), 0.0)

        # When nonzero_only=False, padded zero-contributions are returned
        exps_padded = ml_inference_service.explain_from_features(features, top_k=5, nonzero_only=False)
        self.assertEqual(len(exps_padded), 5)

    def test_02_explanation_endpoint_returns_honest_unavailable_state(self):
        """Verify GET /api/explanation returns empty shap_contributions when telemetry is absent."""
        # Start a brand new session with zero events
        res = self.client.post("/api/session/start", json={
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
            "client_timestamp": 1700000000000,
            "collection_mode": "HUMAN",
            "task_id": "TASK_EMPTY_TEST"
        })
        self.assertEqual(res.status_code, 201)
        session_id = res.json()["session_id"]

        # Query explanation without ending or sending events
        res_expl = self.client.get(f"/api/explanation/{session_id}")
        self.assertEqual(res_expl.status_code, 200)
        data = res_expl.json()
        # Verify no fabricated fallback features are injected
        self.assertEqual(data["shap_contributions"], [])

    def test_03_scenario_metadata_strictly_decoupled_from_prediction(self):
        """
        Verify that session collection_mode / scenario metadata does NOT dictate
        or substitute the model's prediction.
        """
        # Session A: collection_mode=HUMAN with short mouse events (<72)
        res_start = self.client.post("/api/session/start", json={
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
            "client_timestamp": 1700000000000,
            "collection_mode": "HUMAN",
            "task_id": "TASK_MANUAL_DEMO"
        })
        self.assertEqual(res_start.status_code, 201)
        s_id = res_start.json()["session_id"]

        # Send 8 mouse events (which is < 72)
        events = []
        for i in range(8):
            events.append({
                "event_type": "mouse_move",
                "client_timestamp": 1700000000000 + i * 40,
                "event_data": {"x": 100 + i * 10, "y": 100, "velocity_px_s": 500.0}
            })
        self.client.post("/api/behavior/events", json={"session_id": s_id, "events": events})

        # End session
        res_end = self.client.post("/api/session/end", json={"session_id": s_id})
        end_data = res_end.json()

        # The scenario was HUMAN, but the model independently classified as AUTOMATED
        # because mouse_event_count < 72!
        self.assertEqual(end_data["ml_inference"]["status"], "available")
        self.assertEqual(end_data["ml_inference"]["predicted_class"], "AUTOMATED")
        # Ensure collection_mode remained HUMAN in session record
        sess_record = session_service.get_session(s_id)
        self.assertEqual(sess_record["collection_mode"], "HUMAN")
        self.assertNotEqual(sess_record["collection_mode"], end_data["ml_inference"]["predicted_class"])

    def test_04_frozen_model_hash_and_threshold_integrity(self):
        """Verify the model status endpoint reports expected threshold and version."""
        res = self.client.get("/api/model/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["decision_threshold"], 0.50)
        self.assertEqual(data["feature_count"], 64)
        self.assertEqual(
            data["artifact_sha256"],
            "74ff7cb594ffa953ed51e433e5f059a9fbb19dd8beb650c422d1acec88b70fb0"
        )


if __name__ == "__main__":
    unittest.main()
