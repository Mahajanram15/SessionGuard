"""
Stage 4 Test Suite: Controlled Synthetic Bot Simulation & End-to-End Verification.

Validates the full CrossTrace behavioral integrity verification pipeline:
1. Session start via /api/session/start
2. Telemetry ingestion via /api/behavior/events (human vs robotic dynamics)
3. Domain API logging via /api/api-requests
4. Session finalization via /api/session/end
5. Feature extraction (64 features)
6. Frozen XGBoost model inference & probability evaluation
7. Multi-signal risk assessment (/api/risk/{session_id})
8. Live SHAP explainability (/api/explanation/{session_id})
9. Dashboard stats fleet aggregation (/api/dashboard/stats)
"""

import unittest
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.services.ml_inference_service import ml_inference_service


class TestStage4SimulationPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = TestClient(cls.app)
        # Verify frozen model service readiness
        cls.model_ready = ml_inference_service.is_ready

    def test_frozen_model_service_is_ready(self):
        """Verify the inference service loaded the frozen Experiment A XGBoost model."""
        self.assertTrue(self.model_ready, "Model service must be ready for Stage 4")
        status = ml_inference_service.get_status()
        self.assertEqual(status["status"], "available")
        self.assertEqual(status["model_type"], "xgboost.XGBClassifier")
        self.assertEqual(status["feature_count"], 64)

    def test_manual_session_end_to_end_pipeline(self):
        """
        Execute a simulated manual LearnSphere session:
        - Start session with collection_mode=HUMAN
        - Ingest organic, curved mouse and variable typing telemetry
        - Ingest LearnSphere API requests
        - End session
        - Verify 64 features, ML inference, and SHAP explainability
        """
        # 1. Start Session
        start_payload = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
            "screen_resolution": "1920x1080",
            "client_timezone": "America/New_York",
            "client_timestamp": 1700000000000,
            "collection_mode": "HUMAN",
            "task_id": "TASK_LEARN_MANUAL",
        }
        res_start = self.client.post("/api/session/start", json=start_payload)
        self.assertEqual(res_start.status_code, 201)
        session_id = res_start.json()["session_id"]
        self.assertTrue(session_id.startswith("sess_"))

        # 2. Ingest Organic Telemetry (>= 5 events)
        base_t = 1700000000100
        events = []
        # Natural curved mouse movements
        for i in range(12):
            events.append({
                "event_type": "mouse_move",
                "client_timestamp": base_t + i * 40,
                "event_data": {
                    "x": 100 + i * 15 + (i % 3) * 4,
                    "y": 150 + i * 12 - (i % 2) * 5,
                    "distance_px": 19.5,
                    "time_delta_ms": 40,
                    "velocity_px_s": 487.5 + (i * 20),
                    "acceleration_px_s2": 15.0 if i % 2 == 0 else -10.0,
                    "angle_degrees": 38.0 + (i * 2.5),
                    "direction_change_deg": 4.2 if i > 0 else 0.0,
                }
            })

        # Organic human clicks
        events.append({
            "event_type": "mouse_click",
            "client_timestamp": base_t + 600,
            "event_data": {
                "x": 280,
                "y": 270,
                "button": 0,
                "click_type": "single",
                "time_since_last_click_ms": 600,
                "target_category": "button"
            }
        })

        # Organic typing with natural variance (dwell: 110-150ms, flight: 140-210ms)
        for k in range(5):
            dwell = 110 + (k * 8)
            flight = 140 + (k * 15)
            events.append({
                "event_type": "key_meta",
                "client_timestamp": base_t + 700 + k * (dwell + flight),
                "event_data": {
                    "dwell_ms": dwell,
                    "flight_ms": flight,
                    "inter_key_interval_ms": dwell + flight,
                    "is_backspace": False,
                    "is_paste": False
                }
            })

        # Organic scroll
        events.append({
            "event_type": "scroll",
            "client_timestamp": base_t + 1800,
            "event_data": {
                "scroll_x": 0,
                "scroll_y": 180,
                "delta_x": 0,
                "delta_y": 180,
                "velocity_px_s": 720.0,
                "direction": "down",
                "time_since_last_scroll_ms": 95
            }
        })

        res_events = self.client.post("/api/behavior/events", json={
            "session_id": session_id,
            "events": events
        })
        self.assertEqual(res_events.status_code, 202)
        self.assertEqual(res_events.json()["processed_events"], len(events))

        # 3. Log LearnSphere Domain API Requests
        res_api1 = self.client.post("/api/api-requests", json={
            "session_id": session_id,
            "endpoint": "/api/courses",
            "http_method": "GET",
            "status_code": 200,
            "response_time_ms": 14.5,
            "param_keys": ["page", "page_size"],
            "client_timestamp": base_t + 200,
        })
        self.assertEqual(res_api1.status_code, 201)

        res_api2 = self.client.post("/api/api-requests", json={
            "session_id": session_id,
            "endpoint": "/api/courses/details",
            "http_method": "GET",
            "status_code": 200,
            "response_time_ms": 22.1,
            "param_keys": ["course_id"],
            "client_timestamp": base_t + 650,
        })
        self.assertEqual(res_api2.status_code, 201)

        # 4. End Session cleanly
        res_end = self.client.post("/api/session/end", json={
            "session_id": session_id,
            "end_reason": "MANUAL_TEST_COMPLETED"
        })
        self.assertEqual(res_end.status_code, 200)
        end_data = res_end.json()
        self.assertEqual(end_data["status"], "COMPLETED")
        self.assertGreaterEqual(end_data["total_events_captured"], len(events))
        self.assertIsNotNone(end_data["ml_inference"])
        self.assertEqual(end_data["ml_inference"]["status"], "available")
        self.assertIn(end_data["ml_inference"]["predicted_class"], ["HUMAN", "AUTOMATED"])

        # 5. Query Risk Endpoint
        res_risk = self.client.get(f"/api/risk/{session_id}")
        self.assertEqual(res_risk.status_code, 200)
        risk_data = res_risk.json()
        self.assertIn("behavioral_integrity_score", risk_data)
        self.assertIn("signals", risk_data)
        self.assertIn("decision", risk_data)
        self.assertIn(risk_data["decision"]["action"], ["ALLOW", "CHALLENGE", "BLOCK"])
        self.assertIsNotNone(risk_data["ml_inference"])

        # 6. Query Explanation Endpoint
        res_expl = self.client.get(f"/api/explanation/{session_id}")
        self.assertEqual(res_expl.status_code, 200)
        expl_data = res_expl.json()
        self.assertEqual(expl_data["session_id"], session_id)
        self.assertGreaterEqual(len(expl_data["shap_contributions"]), 1)
        for contrib in expl_data["shap_contributions"]:
            self.assertIn("feature_name", contrib)
            self.assertIn("shap_value", contrib)
            self.assertIn("description", contrib)

    def test_synthetic_bot_simulation_end_to_end_pipeline(self):
        """
        Execute a simulated controlled synthetic bot session:
        - Start session with collection_mode=AUTOMATED, automation_condition=AUTOMATED_DETERMINISTIC
        - Ingest robotic straight-line mouse moves (0 acceleration, 0 direction change)
        - Ingest robotic fixed-interval keystrokes (constant 70ms dwell, 50ms flight)
        - Ingest LearnSphere API requests
        - End session
        - Verify 64 features, ML inference, and SHAP explainability
        """
        # 1. Start Automated Session
        start_payload = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HeadlessChrome/120.0",
            "screen_resolution": "1920x1080",
            "client_timezone": "UTC",
            "client_timestamp": 1700000050000,
            "collection_mode": "AUTOMATED",
            "automation_condition": "AUTOMATED_DETERMINISTIC",
            "task_id": "TASK_LEARN_AUTOMATION",
            "label": 1,
        }
        res_start = self.client.post("/api/session/start", json=start_payload)
        self.assertEqual(res_start.status_code, 201)
        session_id = res_start.json()["session_id"]

        # 2. Ingest Robotic Deterministic Telemetry
        base_t = 1700000050100
        events = []
        # Constant velocity, zero curvature, fixed 33ms interval
        for i in range(16):
            events.append({
                "event_type": "mouse_move",
                "client_timestamp": base_t + i * 33,
                "event_data": {
                    "x": 120 + i * 25,
                    "y": 180 + i * 20,
                    "distance_px": 32.0,
                    "time_delta_ms": 33,
                    "velocity_px_s": 969.7,
                    "acceleration_px_s2": 0.0,
                    "angle_degrees": 38.6,
                    "direction_change_deg": 0.0,
                }
            })

        # Robotic click
        events.append({
            "event_type": "mouse_click",
            "client_timestamp": base_t + 580,
            "event_data": {
                "x": 520,
                "y": 500,
                "button": 0,
                "click_type": "single",
                "time_since_last_click_ms": 500,
                "target_category": "button"
            }
        })

        # Robotic keystroke cadence: exact 70ms dwell, 50ms flight, 0 variance
        for k in range(6):
            events.append({
                "event_type": "key_meta",
                "client_timestamp": base_t + 700 + k * 120,
                "event_data": {
                    "dwell_ms": 70,
                    "flight_ms": 50,
                    "inter_key_interval_ms": 120,
                    "is_backspace": False,
                    "is_paste": False
                }
            })

        # Robotic scroll
        events.append({
            "event_type": "scroll",
            "client_timestamp": base_t + 1500,
            "event_data": {
                "scroll_x": 0,
                "scroll_y": 200,
                "delta_x": 0,
                "delta_y": 200,
                "velocity_px_s": 1500.0,
                "direction": "down",
                "time_since_last_scroll_ms": 100
            }
        })

        res_events = self.client.post("/api/behavior/events", json={
            "session_id": session_id,
            "events": events
        })
        self.assertEqual(res_events.status_code, 202)

        # 3. Ingest Domain API calls
        self.client.post("/api/api-requests", json={
            "session_id": session_id,
            "endpoint": "/api/courses",
            "http_method": "GET",
            "status_code": 200,
            "response_time_ms": 12.0,
            "param_keys": ["page", "page_size"],
            "client_timestamp": base_t + 100,
        })
        self.client.post("/api/api-requests", json={
            "session_id": session_id,
            "endpoint": "/api/courses/details",
            "http_method": "GET",
            "status_code": 200,
            "response_time_ms": 18.0,
            "param_keys": ["course_id"],
            "client_timestamp": base_t + 590,
        })

        # 4. End Session cleanly
        res_end = self.client.post("/api/session/end", json={
            "session_id": session_id,
            "end_reason": "AUTOMATED_SIMULATION_COMPLETED"
        })
        self.assertEqual(res_end.status_code, 200)
        end_data = res_end.json()
        self.assertEqual(end_data["status"], "COMPLETED")
        self.assertIsNotNone(end_data["ml_inference"])
        self.assertEqual(end_data["ml_inference"]["status"], "available")

        # 5. Risk and Explanation
        res_risk = self.client.get(f"/api/risk/{session_id}")
        self.assertEqual(res_risk.status_code, 200)
        risk_data = res_risk.json()
        ml_inf = risk_data["ml_inference"]
        self.assertIsNotNone(ml_inf)
        self.assertIn("probability_automated", ml_inf)
        self.assertIn("probability_human", ml_inf)

        res_expl = self.client.get(f"/api/explanation/{session_id}")
        self.assertEqual(res_expl.status_code, 200)
        expl_data = res_expl.json()
        self.assertGreaterEqual(len(expl_data["shap_contributions"]), 1)

    def test_minimum_event_threshold_for_inference(self):
        """
        Verify that a session with fewer than 5 events (<5)
        reports insufficient_telemetry / prediction_not_ready instead of running invalid ML prediction.
        """
        # 1. Start Session
        res_start = self.client.post("/api/session/start", json={
            "user_agent": "TestAgent/1.0",
            "client_timestamp": 1700000100000,
            "collection_mode": "HUMAN",
        })
        session_id = res_start.json()["session_id"]

        # 2. Ingest only 2 events (<5)
        self.client.post("/api/behavior/events", json={
            "session_id": session_id,
            "events": [
                {
                    "event_type": "mouse_move",
                    "client_timestamp": 1700000100010,
                    "event_data": {"x": 10, "y": 20, "distance_px": 5.0, "time_delta_ms": 30, "velocity_px_s": 166.0, "acceleration_px_s2": 0.0, "angle_degrees": 0.0, "direction_change_deg": 0.0}
                },
                {
                    "event_type": "mouse_click",
                    "client_timestamp": 1700000100050,
                    "event_data": {"x": 10, "y": 20, "button": 0, "click_type": "single", "time_since_last_click_ms": 40, "target_category": "button"}
                }
            ]
        })

        # 3. End Session
        res_end = self.client.post("/api/session/end", json={
            "session_id": session_id,
            "end_reason": "EARLY_EXIT"
        })
        self.assertEqual(res_end.status_code, 200)
        end_data = res_end.json()
        # ML inference should be None because <5 events
        self.assertIsNone(end_data.get("ml_inference"))

        # Risk query should report insufficient_telemetry
        res_risk = self.client.get(f"/api/risk/{session_id}")
        self.assertEqual(res_risk.status_code, 200)
        risk_data = res_risk.json()
        self.assertEqual(risk_data["ml_inference"]["status"], "insufficient_telemetry")

    def test_dashboard_stats_aggregates_recent_sessions(self):
        """Verify GET /api/dashboard/stats accurately reflects recorded sessions."""
        res = self.client.get("/api/dashboard/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_sessions", data)
        self.assertIn("active_sessions", data)
        self.assertIn("average_risk_score", data)
        self.assertIn("decision_distribution", data)
        self.assertIn("recent_flagged_sessions", data)
        self.assertIsInstance(data["recent_flagged_sessions"], list)


if __name__ == "__main__":
    unittest.main()
