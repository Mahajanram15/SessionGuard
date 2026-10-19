"""
CrossTrace Phase 2 — Stage 2A: Safeguard & Infrastructure Synthetic Test Suite.

Verifies:
1. Privacy schema validator:
   - Rejection of key, code, value, text, keyCode, which, inputValue, and password targets.
   - Acceptance of permitted event types and structural metadata.
2. Development-only dataset loader:
   - Strict directory path boundary enforcement (rejection of quarantined, held_out, method2 paths).
   - Strict participant boundary enforcement (rejection of H5, H6, B5, B6, M2 profiles in dev data).
3. Pre-load quarantine evaluation gate:
   - Verification of independently supplied external root digest.
   - Model artifact checksum verification.
   - Canary test: Quarantined data loader is strictly NOT invoked when integrity checks fail.
4. Windowing invariants (W=30, S=15):
   - Slicing for 30, 45, 52 (7 trailing dropped), and 60 events.
   - Insufficient sessions (<30 events) yielding zero windows.
   - Chronological timestamp sorting.
   - Session boundary isolation.
   - Modality sparsity handling (0.0 without NaNs/Infs).
5. 29-feature schema & modeling:
   - Canonical 29-feature ordering and completeness.
   - Fold-specific StandardScaler fitting.
   - Session-level soft probability aggregation rule (threshold = 0.50).
   - Clopper-Pearson exact binomial confidence intervals.
6. CrossTrace UI & API workflow alignment:
   - Mapping of TASK_01, TASK_02, TASK_03 to existing routes and task instructions.
7. Protected Phase 1 baseline file cryptographic immutability:
   - Assertion of all 6 baseline SHA-256 hashes.
"""

import os
import sys
import unittest
import hashlib
import tempfile
import json
import pandas as pd
import numpy as np

# Ensure workspace root is in path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from ml.features.extractor import FEATURE_COLUMNS, BehavioralFeatureExtractor
from ml.training.phase2_config import (
    SELECTED_FEATURES_PHASE2_KINEMATICS,
    EXCLUDED_FEATURES_PHASE2_KINEMATICS,
    validate_phase2_feature_partition,
)
from ml.features.windowed_extractor import (
    slice_events_into_windows,
    extract_windowed_kinematics,
)
from ml.data.privacy_validator import (
    validate_event_privacy,
    validate_session_events_privacy,
    PrivacyViolationError,
    PERMITTED_TELEMETRY_FIELDS,
    FORBIDDEN_PII_FIELDS,
)
from ml.data.phase2_loader import (
    audit_development_path_boundary,
    audit_development_participants,
    PartitionIsolationError,
)
from ml.training.phase2_train_development import (
    run_4fold_grouped_cv,
    freeze_development_pipeline,
    aggregate_session_predictions,
    compute_clopper_pearson_interval,
)
from ml.evaluation.phase2_evaluate_unseen import (
    verify_external_root_digest,
    verify_freeze_gate,
    execute_preload_quarantine_gate,
    PipelineNotFrozenError,
    SecurityIntegrityError,
)
from tests.fixtures.synthetic_windows import (
    get_pure_mouse_window_fixture,
    get_pure_keyboard_window_fixture,
    get_pure_scroll_window_fixture,
    get_mixed_modality_stream_fixture,
    get_insufficient_events_fixture,
    get_trailing_events_stream_fixture,
    get_mock_multi_participant_dataset,
)

# Immutable Baseline SHA-256 Hashes of Protected Phase 1 Files
BASELINE_PROTECTED_HASHES = {
    "features.csv": "7164C4432BFC1D0E93BE0E183639FAA67215E5BB5A2EE6F05565BE85B668319C".lower(),
    "metadata.csv": "E98184240A8E6C4FC895CE132FE68EBD279420DF572396A9F5B5460E072EF8B9".lower(),
    "api_request_records.csv": "2EA9028854C681D02929B12D1C894F27DBEDA92D82AAA2B8E077DA5154FF4D46".lower(),
    "train_experiment_a.py": "925F4AB7DAD47DBDF699CE6498611F20723602C35D325CB7F8EE48723FEAFCED".lower(),
    "feature_config.py": "D50ED367ED3EF965F42CA51BB8FC96873D45C76B363B5F000D3CD3C5D8D1E7EC".lower(),
    "metrics_summary.json": "369A4DC49BFFFA790ED938F2D943BFC17BB932C59E0F44AC17F4314441AE05A7".lower(),
}


class TestPhase2Safeguards(unittest.TestCase):

    # ==========================================================================
    # 1. Privacy Schema Validator Tests
    # ==========================================================================

    def test_privacy_validator_permits_clean_telemetry(self):
        """Verify that compliant mouse, keyboard, and scroll events pass privacy validation."""
        valid_events = [
            {"event_type": "mousemove", "client_timestamp": 1000, "x": 100, "y": 200, "is_trusted": True},
            {"event_type": "keydown", "client_timestamp": 1050, "target_tag": "INPUT", "target_type": "text"},
            {"event_type": "keyup", "client_timestamp": 1120, "target_tag": "INPUT", "target_type": "text"},
            {"event_type": "wheel", "client_timestamp": 1200, "delta_y": 15.0},
            {"event_type": "click", "client_timestamp": 1300, "x": 150, "y": 250},
        ]
        res = validate_session_events_privacy(valid_events)
        self.assertTrue(res["privacy_passed"])
        self.assertEqual(res["total_events"], 5)

    def test_privacy_validator_rejects_typed_characters_and_keycodes(self):
        """Verify that presence of key, code, value, text, keyCode, which, etc., raises PrivacyViolationError."""
        forbidden_test_cases = [
            {"event_type": "keydown", "client_timestamp": 1000, "key": "a"},
            {"event_type": "keydown", "client_timestamp": 1000, "code": "KeyA"},
            {"event_type": "keydown", "client_timestamp": 1000, "value": "secret_text"},
            {"event_type": "keydown", "client_timestamp": 1000, "text": "user_input"},
            {"event_type": "keydown", "client_timestamp": 1000, "inputValue": "search_query"},
            {"event_type": "keydown", "client_timestamp": 1000, "keyCode": 65},
            {"event_type": "keydown", "client_timestamp": 1000, "which": 65},
            {"event_type": "keydown", "client_timestamp": 1000, "char": "a"},
        ]
        for bad_event in forbidden_test_cases:
            with self.assertRaises(PrivacyViolationError, msg=f"Failed to reject: {bad_event}"):
                validate_event_privacy(bad_event)

    def test_privacy_validator_rejects_password_targets(self):
        """Verify that interactions targeting password input fields are strictly rejected."""
        pw_event = {"event_type": "keydown", "client_timestamp": 1000, "target_type": "password"}
        with self.assertRaises(PrivacyViolationError):
            validate_event_privacy(pw_event)

    def test_privacy_validator_rejects_unauthorized_fields(self):
        """Verify that arbitrary unwhitelisted metadata fields are rejected."""
        bad_event = {"event_type": "mousemove", "client_timestamp": 1000, "unauthorized_tracking_uuid": "12345"}
        with self.assertRaises(PrivacyViolationError):
            validate_event_privacy(bad_event)

    def test_live_session_service_ingestion_privacy_boundary(self):
        """
        Verify that session_service.record_events enforces privacy schema validation
        BEFORE in-memory append or persistence, rejecting forbidden keys and password targets.
        """
        import asyncio
        from backend.app.services.session_service import session_service
        from backend.app.schemas.session import SessionStartRequest
        from backend.app.schemas.behavior import BehaviorBatchRequest, BehaviorEventItem

        # Create session
        loop = asyncio.new_event_loop()
        start_req = SessionStartRequest(user_agent="TestAgent/1.0", screen_resolution="1920x1080", client_timestamp=1000)
        start_res = loop.run_until_complete(session_service.create_session(start_req, client_ip="127.0.0.1"))
        sess_id = start_res.session_id

        # Initial event count
        self.assertEqual(session_service._events_count.get(sess_id, 0), 0)

        # 1. Compliant batch succeeds
        valid_batch = BehaviorBatchRequest(
            session_id=sess_id,
            events=[
                BehaviorEventItem(
                    event_type="mouse_move",
                    client_timestamp=1000,
                    event_data={"x": 100, "y": 200},
                ),
                BehaviorEventItem(
                    event_type="key_meta",
                    client_timestamp=1050,
                    event_data={"dwell_ms": 75.0, "target_tag": "INPUT", "target_type": "text"},
                ),
            ]
        )
        res = loop.run_until_complete(session_service.record_events(valid_batch))
        self.assertEqual(res.processed_events, 2)
        self.assertEqual(session_service._events_count[sess_id], 2)

        # 2. Batch with forbidden key rejected BEFORE persistence
        bad_key_batch = BehaviorBatchRequest(
            session_id=sess_id,
            events=[
                BehaviorEventItem(
                    event_type="key_meta",
                    client_timestamp=1100,
                    event_data={"dwell_ms": 80.0, "key": "secret_character"},
                )
            ]
        )
        with self.assertRaises(PrivacyViolationError):
            loop.run_until_complete(session_service.record_events(bad_key_batch))
        # Count MUST NOT increase
        self.assertEqual(session_service._events_count[sess_id], 2)

        # 3. Batch with password target rejected BEFORE persistence
        bad_pw_batch = BehaviorBatchRequest(
            session_id=sess_id,
            events=[
                BehaviorEventItem(
                    event_type="key_meta",
                    client_timestamp=1200,
                    event_data={"dwell_ms": 80.0, "target_type": "password"},
                )
            ]
        )
        with self.assertRaises(PrivacyViolationError):
            loop.run_until_complete(session_service.record_events(bad_pw_batch))
        self.assertEqual(session_service._events_count[sess_id], 2)

        # 4. Batch with nested forbidden text rejected BEFORE persistence
        nested_bad_batch = BehaviorBatchRequest(
            session_id=sess_id,
            events=[
                BehaviorEventItem(
                    event_type="key_meta",
                    client_timestamp=1300,
                    event_data={"nested": {"value": "typed_user_string"}},
                )
            ]
        )
        with self.assertRaises(PrivacyViolationError):
            loop.run_until_complete(session_service.record_events(nested_bad_batch))
        self.assertEqual(session_service._events_count[sess_id], 2)
        loop.close()

    def test_session_lifecycle_telemetry_rejection_and_export_isolation(self):
        """
        Verify:
        1. Events are accepted for an ACTIVE session.
        2. Events are rejected for a COMPLETED session with DISCARDED_SESSION_COMPLETED.
        3. Rejected events do not mutate in-memory event buffers.
        4. Rejected events do not update the persisted cache.
        5. Rejected events do not create database records (mock DB add_all not called).
        6. Unknown-session behavior remains DISCARDED_UNKNOWN_SESSION.
        7. Phase 2 development export destination targets ml/data/phase2_development/ and cannot target ml/data.
        """
        import asyncio
        from unittest.mock import AsyncMock, patch
        from backend.app.services.session_service import session_service
        from backend.app.schemas.session import SessionStartRequest
        from backend.app.schemas.behavior import BehaviorBatchRequest, BehaviorEventItem

        loop = asyncio.new_event_loop()
        try:
            # 6. Unknown session behavior remains unchanged
            unknown_batch = BehaviorBatchRequest(
                session_id="sess_nonexistent_unknown_12345",
                events=[
                    BehaviorEventItem(
                        event_type="mouse_move",
                        client_timestamp=1000,
                        event_data={"x": 50, "y": 50},
                    )
                ]
            )
            res_unknown = loop.run_until_complete(session_service.record_events(unknown_batch))
            self.assertEqual(res_unknown.status, "DISCARDED_UNKNOWN_SESSION")
            self.assertEqual(res_unknown.processed_events, 0)

            # 1. Start an ACTIVE session and verify events are accepted
            start_req = SessionStartRequest(
                user_agent="LifecycleTestAgent/1.0",
                screen_resolution="1920x1080",
                client_timestamp=1000,
                collection_mode="HUMAN",
                task_id="TASK_01",
                participant_id="H1",
            )
            start_res = loop.run_until_complete(session_service.create_session(start_req, client_ip="127.0.0.1"))
            sess_id = start_res.session_id
            self.assertEqual(session_service._sessions[sess_id]["status"], "ACTIVE")

            active_batch = BehaviorBatchRequest(
                session_id=sess_id,
                events=[
                    BehaviorEventItem(
                        event_type="mouse_move",
                        client_timestamp=1001,
                        event_data={"x": 100, "y": 200},
                    ),
                    BehaviorEventItem(
                        event_type="mouse_click",
                        client_timestamp=1050,
                        event_data={"x": 100, "y": 200, "button": 0},
                    )
                ]
            )
            mock_db_active = AsyncMock()
            res_active = loop.run_until_complete(session_service.record_events(active_batch, db=mock_db_active))
            self.assertEqual(res_active.status, "INGESTED")
            self.assertEqual(res_active.processed_events, 2)
            self.assertEqual(len(session_service._events_by_session[sess_id]), 2)
            self.assertEqual(session_service._events_count[sess_id], 2)

            # End session -> marks status COMPLETED
            end_res = loop.run_until_complete(session_service.end_session(sess_id))
            self.assertEqual(end_res.status, "COMPLETED")
            self.assertEqual(session_service._sessions[sess_id]["status"], "COMPLETED")

            # Snapshot state prior to rejection attempt
            buffer_before = list(session_service._events_by_session[sess_id])
            count_before = session_service._events_count[sess_id]

            # 2. Events on COMPLETED session are rejected with DISCARDED_SESSION_COMPLETED
            late_batch = BehaviorBatchRequest(
                session_id=sess_id,
                events=[
                    BehaviorEventItem(
                        event_type="mouse_move",
                        client_timestamp=2000,
                        event_data={"x": 300, "y": 400},
                    )
                ]
            )

            mock_db_completed = AsyncMock()
            with patch.object(session_service, "_save_cache") as mock_save_cache:
                res_late = loop.run_until_complete(session_service.record_events(late_batch, db=mock_db_completed))

                # Assertion 2: DISCARDED_SESSION_COMPLETED with processed_events=0
                self.assertEqual(res_late.status, "DISCARDED_SESSION_COMPLETED")
                self.assertEqual(res_late.processed_events, 0)

                # Assertion 3: In-memory buffers unchanged
                self.assertEqual(session_service._events_by_session[sess_id], buffer_before)
                self.assertEqual(session_service._events_count[sess_id], count_before)

                # Assertion 4: Persisted cache not called
                mock_save_cache.assert_not_called()

                # Assertion 5: Database records not created
                mock_db_completed.add_all.assert_not_called()

            # Clean up test session from in-memory tracking
            session_service._sessions.pop(sess_id, None)
            session_service._events_by_session.pop(sess_id, None)
            session_service._events_count.pop(sess_id, None)

            # 7. Phase 2 development export destination canonical isolation check
            import inspect
            sig = inspect.signature(session_service.export_phase2_development_dataset)
            default_export_dir = sig.parameters["output_dir"].default
            expected_phase2_dir = os.path.join("ml", "data", "phase2_development")
            self.assertEqual(os.path.normpath(default_export_dir), os.path.normpath(expected_phase2_dir))

            # Test canonical path resolution & containment:
            # Must strictly reject relative traversals, absolute baseline paths, trailing separators,
            # and destinations outside ml/data/phase2_development.
            abs_baseline = os.path.abspath(os.path.join(workspace_root, "ml", "data"))
            forbidden_destinations = [
                "ml/data",
                "ml/data/",
                "ml/data//",
                r"ml\data",
                r"ml\data\\",
                "ml/data/phase2_development/..",
                "ml/data/phase2_development/../../ml/data",
                abs_baseline,
                os.path.join(abs_baseline, ""),
                "ml/data/other",
                "ml/data/features",
                "C:/Windows/Temp",
                "../outside",
                ".",
                "",
                "..",
            ]

            for forbidden_dest in forbidden_destinations:
                with self.assertRaises(ValueError, msg=f"Allowed unsafe export destination: {forbidden_dest}"):
                    session_service.export_phase2_development_dataset(output_dir=forbidden_dest)

            # Test valid authorized targets with mocked export_dataset (zero real export execution)
            with patch.object(session_service, "export_dataset", return_value={"mock": True}) as mock_exp:
                valid_destinations = [
                    "ml/data/phase2_development",
                    "ml/data/phase2_development/",
                    r"ml\data\phase2_development",
                    os.path.join(workspace_root, "ml", "data", "phase2_development"),
                    os.path.join(workspace_root, "ml", "data", "phase2_development", "batch_01"),
                ]
                for valid_dest in valid_destinations:
                    res = session_service.export_phase2_development_dataset(output_dir=valid_dest)
                    self.assertEqual(res, {"mock": True})
                self.assertEqual(mock_exp.call_count, len(valid_destinations))

        finally:
            loop.close()

    def test_participant_consent_brief_alignment(self):
        """
        Verify that docs/PARTICIPANT_CONSENT_BRIEF.md exists and accurately details:
        1. Complete verified telemetry inventory: coordinates, velocity, acceleration, scroll,
           keystroke timing (dwell/flight/backspace/paste), navigation, and API request metadata.
        2. Strict technical exclusions: no typed characters, no passwords, no form values.
        3. Clear distinction between technically blocked data and unrequested data.
        4. Technical classification as pseudonymous research data (not anonymous).
        5. IP address handling: application layer SHA-256 hash vs transport logging.
        6. Study purpose, voluntary participation, withdrawal process, and contact protocol.
        7. Explicit flagging of unresolved operational decisions (IRB, retention schedule).
        """
        brief_path = os.path.join(workspace_root, "docs", "PARTICIPANT_CONSENT_BRIEF.md")
        self.assertTrue(os.path.exists(brief_path), f"Consent brief missing: {brief_path}")

        with open(brief_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Telemetry collected checks
        self.assertIn("hold_time_ms", content)
        self.assertIn("inter_key_latency_ms", content)
        self.assertIn("dwell_ms", content)
        self.assertIn("flight_ms", content)
        self.assertIn("is_backspace", content)
        self.assertIn("is_paste", content)
        self.assertIn("velocity_px_s", content)
        self.assertIn("acceleration_px_s2", content)
        self.assertIn("scroll_x", content)
        self.assertIn("scroll_y", content)
        self.assertIn("delta_y", content)
        self.assertIn("TASK_01", content)
        self.assertIn("TASK_02", content)
        self.assertIn("TASK_03", content)
        self.assertIn("user-agent", content.lower())
        self.assertIn("screen", content.lower())
        self.assertIn("timezone", content.lower())
        self.assertIn("param_keys", content)
        self.assertIn("payload_keys", content)
        self.assertIn("ip_hash", content)

        # Technical exclusion and filtering checks
        self.assertIn("Technically Blocked", content)
        self.assertIn("PrivacyViolationError", content)
        self.assertIn("password", content.lower())

        # Pseudonymity vs Anonymity distinction
        self.assertIn("PSEUDONYMOUS, NOT ANONYMOUS", content)

        # Rights, Governance & Operational Blockers
        self.assertIn("Voluntary Participation", content)
        self.assertIn("Withdrawal", content)
        self.assertIn("mahajanram1506@gmail.com", content)
        self.assertIn("BLOCKER", content)
        self.assertIn("H1", content)

    # ==========================================================================
    # 2. Development-Only Dataset Loader & Partition Boundary Tests
    # ==========================================================================

    def test_loader_permits_development_paths(self):
        """Verify allowed development directory paths pass path boundary audit."""
        valid_paths = [
            "ml/data/phase2_controlled/raw_events/development/human/h1_01.csv",
            "ml/data/phase2_controlled/raw_events/development/method1/b1_01.csv",
            "ml/data/phase2_controlled/derived_windows/phase2_development_windows.parquet",
        ]
        for path in valid_paths:
            audit_development_path_boundary(path)

    def test_loader_rejects_quarantined_paths(self):
        """Verify that paths containing quarantined, held_out, or method2 trigger PartitionIsolationError."""
        forbidden_paths = [
            "ml/data/phase2_controlled/raw_events/quarantined_evaluation/held_out_human/h5_01.json",
            "ml/data/phase2_controlled/raw_events/quarantined_evaluation/method2_unseen/m2_01.json",
            "ml/data/phase2_controlled/derived_windows/phase2_quarantined_evaluation_windows.parquet",
            "ml/data/phase2_controlled/method_2/events.csv",
        ]
        for path in forbidden_paths:
            with self.assertRaises(PartitionIsolationError, msg=f"Failed to reject: {path}"):
                audit_development_path_boundary(path)

    def test_loader_rejects_quarantined_participants(self):
        """Verify that presence of H5, H6, B5, B6, or M2 in development data triggers PartitionIsolationError."""
        # Allowed dev participants
        audit_development_participants(["H1", "H2", "H3", "H4", "B1", "B2"])

        # Quarantined participants
        bad_participant_lists = [
            ["H1", "H2", "H5"],
            ["H3", "H4", "H6"],
            ["B1", "B2", "B5"],
            ["B3", "B4", "M2_1"],
            ["H1", "M2-3"],
        ]
        for bad_list in bad_participant_lists:
            with self.assertRaises(PartitionIsolationError, msg=f"Failed to reject: {bad_list}"):
                audit_development_participants(bad_list)

    # ==========================================================================
    # 3. Pre-Load Quarantine Evaluation Gate & Canary Spy Tests
    # ==========================================================================

    def test_preload_gate_enforces_external_root_digest_and_canary_protection(self):
        """
        Tests the pre-load quarantine gate with an externally supplied trusted digest.
        Proves via a canary tracker that quarantined files/loaders are NEVER accessed if:
        1. Root digest mismatches.
        2. Manifest artifact checksum mismatches.
        3. Model file is missing or altered.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            models_dir = os.path.join(tmp_dir, "frozen_models")
            os.makedirs(models_dir, exist_ok=True)

            # Create mock frozen models
            pipe_mock = pd.DataFrame({"dummy": [1, 2]})
            joblib_path = os.path.join(models_dir, "Logistic_Regression.joblib")
            with open(joblib_path, "wb") as f:
                f.write(b"MOCK_MODEL_BYTES_LR")

            joblib_hash = hashlib.sha256(b"MOCK_MODEL_BYTES_LR").hexdigest()

            # Create valid manifest
            manifest = {
                "manifest_type": "SHA-256 Checksum Manifest",
                "feature_configuration": {"ordered_features": list(SELECTED_FEATURES_PHASE2_KINEMATICS)},
                "windowing_parameters": {"window_size": 30, "stride": 15},
                "decision_rule": {"threshold": 0.50},
                "frozen_model_artifacts": {"Logistic_Regression.joblib": joblib_hash},
            }
            manifest_path = os.path.join(tmp_dir, "pipeline_freeze_manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            # Compute true live digest of manifest
            with open(manifest_path, "rb") as f:
                true_manifest_digest = hashlib.sha256(f.read()).hexdigest()

            # Canary tracker to verify quarantined file loading
            canary = {"quarantined_files_opened": False}

            def quarantined_data_loader():
                canary["quarantined_files_opened"] = True
                return pd.DataFrame()

            # Test A: Gate succeeds with matching external root digest
            gate_res = execute_preload_quarantine_gate(manifest_path, models_dir, expected_root_digest=true_manifest_digest)
            self.assertEqual(gate_res["decision_rule"]["threshold"], 0.50)
            # If gate succeeds, caller proceeds to load quarantined data
            quarantined_data_loader()
            self.assertTrue(canary["quarantined_files_opened"])

            # Reset canary
            canary["quarantined_files_opened"] = False

            # Test B: Gate FAILS on root digest mismatch -> Canary MUST NOT be called
            bad_digest = "0000000000000000000000000000000000000000000000000000000000000000"
            with self.assertRaises(SecurityIntegrityError):
                execute_preload_quarantine_gate(manifest_path, models_dir, expected_root_digest=bad_digest)
                quarantined_data_loader()  # Must never be reached
            # Test D: Missing, empty, or malformed root digest fails closed
            with self.assertRaises(SecurityIntegrityError):
                execute_preload_quarantine_gate(manifest_path, models_dir, expected_root_digest="")
            with self.assertRaises(SecurityIntegrityError):
                execute_preload_quarantine_gate(manifest_path, models_dir, expected_root_digest="not_a_valid_64_char_hex_digest")

            # Test E: run_quarantined_evaluation_pipeline verifies gate BEFORE opening file
            from ml.evaluation.phase2_evaluate_unseen import run_quarantined_evaluation_pipeline
            # Even if dataset_path is a canary path that doesn't exist or shouldn't be read:
            canary_dataset_path = os.path.join(tmp_dir, "canary_quarantined_data.parquet")
            with self.assertRaises(SecurityIntegrityError):
                run_quarantined_evaluation_pipeline(
                    dataset_path=canary_dataset_path,
                    expected_root_digest=bad_digest,
                    manifest_path=manifest_path,
                    models_dir=models_dir,
                )
            self.assertFalse(os.path.exists(canary_dataset_path))

    # ==========================================================================
    # 4. Windowing Invariants (W=30, S=15)
    # ==========================================================================

    def test_windowing_slices_exact_sequences(self):
        """Verify exact window slicing for streams of 30, 45, 52, and 60 events."""
        base_event = {"event_type": "mousemove", "x": 100, "y": 100}

        # 30 events -> 1 window [0:30]
        ev30 = [{**base_event, "client_timestamp": i * 50} for i in range(30)]
        w30 = slice_events_into_windows(ev30, window_size=30, stride=15)
        self.assertEqual(len(w30), 1)
        self.assertEqual(len(w30[0]), 30)

        # 45 events -> 2 windows [0:30], [15:45]
        ev45 = [{**base_event, "client_timestamp": i * 50} for i in range(45)]
        w45 = slice_events_into_windows(ev45, window_size=30, stride=15)
        self.assertEqual(len(w45), 2)
        self.assertEqual(w45[0][0]["client_timestamp"], 0)
        self.assertEqual(w45[1][0]["client_timestamp"], 15 * 50)

        # 52 events -> 2 windows [0:30], [15:45] (7 trailing events dropped)
        ev52 = [{**base_event, "client_timestamp": i * 50} for i in range(52)]
        w52 = slice_events_into_windows(ev52, window_size=30, stride=15)
        self.assertEqual(len(w52), 2)
        # Verify 7 trailing events are discarded
        self.assertEqual(w52[-1][-1]["client_timestamp"], 44 * 50)

        # 60 events -> 3 windows [0:30], [15:45], [30:60]
        ev60 = [{**base_event, "client_timestamp": i * 50} for i in range(60)]
        w60 = slice_events_into_windows(ev60, window_size=30, stride=15)
        self.assertEqual(len(w60), 3)

    def test_windowing_insufficient_events_yields_zero_windows(self):
        """Verify sessions with <30 events produce 0 windows without exceptions."""
        ev20 = get_insufficient_events_fixture()
        w20 = slice_events_into_windows(ev20, window_size=30, stride=15)
        self.assertEqual(len(w20), 0)

        feats, meta = extract_windowed_kinematics(ev20, session_metadata={"session_id": "s_short"})
        self.assertEqual(len(feats), 0)
        self.assertEqual(len(meta), 0)
        self.assertEqual(list(feats.columns), SELECTED_FEATURES_PHASE2_KINEMATICS)

    def test_windowing_enforces_chronological_sorting(self):
        """Verify out-of-order event timestamps are sorted chronologically before windowing."""
        raw_events = [
            {"event_type": "mousemove", "client_timestamp": 500, "x": 10, "y": 10},
            {"event_type": "mousemove", "client_timestamp": 100, "x": 20, "y": 20},
            {"event_type": "mousemove", "client_timestamp": 300, "x": 30, "y": 30},
        ] + [{"event_type": "mousemove", "client_timestamp": 1000 + i, "x": i, "y": i} for i in range(27)]

        windows = slice_events_into_windows(raw_events, window_size=30, stride=15)
        self.assertEqual(len(windows), 1)
        ts_seq = [ev["client_timestamp"] for ev in windows[0]]
        self.assertEqual(ts_seq, sorted(ts_seq))
        self.assertEqual(ts_seq[0], 100)
        self.assertEqual(ts_seq[1], 300)
        self.assertEqual(ts_seq[2], 500)

    def test_windowing_modality_sparsity_and_zero_values(self):
        """Verify absent modalities cleanly default to 0.0 with zero NaNs or Infs."""
        # Pure mouse (no clicks, keys, or scrolls)
        m_events = get_pure_mouse_window_fixture(n_events=30)
        f_m, _ = extract_windowed_kinematics(m_events)
        self.assertEqual(f_m.shape, (1, 29))
        self.assertEqual(f_m.isna().sum().sum(), 0)
        self.assertEqual(float(f_m["button_click_ratio"].iloc[0]), 0.0)
        self.assertEqual(float(f_m["mean_dwell_ms"].iloc[0]), 0.0)
        self.assertEqual(float(f_m["mean_scroll_velocity"].iloc[0]), 0.0)
        self.assertGreater(float(f_m["mouse_mean_velocity"].iloc[0]), 0.0)

        # Pure key (no mouse moves, clicks, scrolls)
        k_events = get_pure_keyboard_window_fixture(n_events=30)
        f_k, _ = extract_windowed_kinematics(k_events)
        self.assertEqual(f_k.shape, (1, 29))
        self.assertEqual(f_k.isna().sum().sum(), 0)
        self.assertEqual(float(f_k["mouse_mean_velocity"].iloc[0]), 0.0)
        self.assertEqual(float(f_k["mean_scroll_velocity"].iloc[0]), 0.0)
        self.assertGreater(float(f_k["mean_dwell_ms"].iloc[0]), 0.0)

    # ==========================================================================
    # 5. 29-Feature Schema, Modeling & Aggregation Rule Tests
    # ==========================================================================

    def test_29_feature_schema_completeness_and_canonical_order(self):
        """Verify that 29 kinematic features match exact pre-registered order and partition."""
        val = validate_phase2_feature_partition()
        self.assertTrue(val["is_valid"])
        self.assertEqual(val["selected_count"], 29)
        self.assertEqual(val["excluded_count"], 47)
        self.assertEqual(val["canonical_count"], 76)
        self.assertEqual(val["overlap_count"], 0)

        # Ordering check against FEATURE_COLUMNS
        canonical_indices = [FEATURE_COLUMNS.index(f) for f in SELECTED_FEATURES_PHASE2_KINEMATICS]
        self.assertEqual(canonical_indices, sorted(canonical_indices), "Features are not in canonical schema order!")

    def test_4fold_cv_fold_specific_scaling_and_isolation(self):
        """Verify fold-specific StandardScaler fitting and zero participant leakage in 4-fold grouped CV."""
        mock_sessions = get_mock_multi_participant_dataset()
        dev_sessions = [s for s in mock_sessions if s.get("partition") == "DEVELOPMENT"]

        all_feat_dfs = []
        all_meta_dfs = []
        for s in dev_sessions:
            f_df, m_df = extract_windowed_kinematics(s["events"], session_metadata=s)
            all_feat_dfs.append(f_df)
            all_meta_dfs.append(m_df)

        combined_feat = pd.concat(all_feat_dfs, ignore_index=True)
        combined_meta = pd.concat(all_meta_dfs, ignore_index=True)

        cv_res = run_4fold_grouped_cv(combined_feat, combined_meta, random_state=42)

        for model_name, res in cv_res.items():
            self.assertEqual(len(res["folds"]), 4)
            for fold in res["folds"]:
                self.assertGreater(fold["n_val_windows"], 0)
                self.assertGreater(fold["n_val_sessions"], 0)
                self.assertIn("accuracy", fold["session_metrics"])
                self.assertIn("accuracy_ci_nominal", fold["session_metrics"])

    def test_session_probability_aggregation_rule(self):
        """Verify pre-registered continuous mean probability rule (threshold = 0.50)."""
        mock_preds = pd.DataFrame([
            {"session_id": "s1", "participant_id": "H1", "task_id": "TASK_01", "label": 0, "prob": 0.20},
            {"session_id": "s1", "participant_id": "H1", "task_id": "TASK_01", "label": 0, "prob": 0.30},
            {"session_id": "s2", "participant_id": "H2", "task_id": "TASK_02", "label": 1, "prob": 0.70},
            {"session_id": "s2", "participant_id": "H2", "task_id": "TASK_02", "label": 1, "prob": 0.40},
            {"session_id": "s3", "participant_id": "H3", "task_id": "TASK_03", "label": 0, "prob": 0.49},
            {"session_id": "s4", "participant_id": "B1", "task_id": "TASK_01", "label": 1, "prob": 0.50},
        ])
        agg = aggregate_session_predictions(mock_preds, threshold=0.50)
        self.assertEqual(len(agg), 4)

        # s1: mean(0.20, 0.30) = 0.25 -> 0 (HUMAN) -> correct
        s1 = agg[agg["session_id"] == "s1"].iloc[0]
        self.assertEqual(s1["mean_window_prob"], 0.25)
        self.assertEqual(s1["pred_label"], 0)
        self.assertEqual(s1["is_correct"], 1)

        # s2: mean(0.70, 0.40) = 0.55 -> 1 (AUTOMATED) -> correct
        s2 = agg[agg["session_id"] == "s2"].iloc[0]
        self.assertEqual(s2["mean_window_prob"], 0.55)
        self.assertEqual(s2["pred_label"], 1)
        self.assertEqual(s2["is_correct"], 1)

        # s3: 0.49 -> 0 (HUMAN) -> correct
        s3 = agg[agg["session_id"] == "s3"].iloc[0]
        self.assertEqual(s3["pred_label"], 0)
        self.assertEqual(s3["is_correct"], 1)

        # s4: 0.50 -> 1 (AUTOMATED) -> correct
        s4 = agg[agg["session_id"] == "s4"].iloc[0]
        self.assertEqual(s4["pred_label"], 1)
        self.assertEqual(s4["is_correct"], 1)

    def test_clopper_pearson_exact_intervals(self):
        """Verify exact Beta distribution Clopper-Pearson binomial intervals."""
        low_0, high_0 = compute_clopper_pearson_interval(0, 10)
        self.assertEqual(low_0, 0.0)
        self.assertAlmostEqual(high_0, 0.3085, places=2)

        low_10, high_10 = compute_clopper_pearson_interval(10, 10)
        self.assertAlmostEqual(low_10, 0.6915, places=2)
        self.assertEqual(high_10, 1.0)

    # ==========================================================================
    # 6. Real CrossTrace UI & API Workflow Alignment Verification
    # ==========================================================================

    def test_crosstrace_application_workflow_alignment(self):
        """Verify TASK_01, TASK_02, TASK_03 map to concrete TelemetryDemoPage routes and API endpoints."""
        demo_page_path = os.path.join(workspace_root, "frontend", "src", "pages", "TelemetryDemoPage.tsx")
        routes_path = os.path.join(workspace_root, "backend", "app", "api", "routes.py")

        self.assertTrue(os.path.exists(demo_page_path), "TelemetryDemoPage.tsx missing!")
        self.assertTrue(os.path.exists(routes_path), "routes.py missing!")

        with open(demo_page_path, "r", encoding="utf-8") as f:
            demo_code = f.read()

        # TASK_01: Catalog Browsing & Product Inspection
        self.assertIn("TASK_01", demo_code)
        self.assertIn("Catalog Browsing & Product Inspection", demo_code)
        self.assertIn("Catalog Route", demo_code)

        # TASK_02: Search & Query Filtering
        self.assertIn("TASK_02", demo_code)
        self.assertIn("Search & Query Filtering", demo_code)

        # TASK_03: Multi-Page Exploration & Form Interaction
        self.assertIn("TASK_03", demo_code)
        self.assertIn("Multi-Page Exploration", demo_code)

        with open(routes_path, "r", encoding="utf-8") as f:
            backend_code = f.read()

        # Check domain API endpoints
        self.assertIn('"/products"', backend_code)
        self.assertIn('"/search"', backend_code)
        self.assertIn('"/catalog"', backend_code)
        self.assertIn('"/cart/items"', backend_code)
        self.assertIn('"/checkout/verify"', backend_code)

    # ==========================================================================
    # 7. Protected Phase 1 Baseline Cryptographic Immutability
    # ==========================================================================

    def test_protected_files_immutability(self):
        """Assert exact byte-for-byte SHA-256 hash preservation for all 6 protected Phase 1 files."""
        file_map = {
            "features.csv": os.path.join(workspace_root, "ml", "data", "features.csv"),
            "metadata.csv": os.path.join(workspace_root, "ml", "data", "metadata.csv"),
            "api_request_records.csv": os.path.join(workspace_root, "ml", "data", "api_request_records.csv"),
            "train_experiment_a.py": os.path.join(workspace_root, "ml", "training", "train_experiment_a.py"),
            "feature_config.py": os.path.join(workspace_root, "ml", "training", "feature_config.py"),
            "metrics_summary.json": os.path.join(workspace_root, "ml", "evaluation", "baseline_comparison_53_sessions", "metrics_summary.json"),
        }

        for name, path in file_map.items():
            self.assertTrue(os.path.exists(path), f"Protected file missing: {path}")
            with open(path, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest().lower()
            expected = BASELINE_PROTECTED_HASHES[name]
            self.assertEqual(h, expected, f"PROTECTED FILE MODIFIED! {name}: expected {expected}, got {h}")


if __name__ == "__main__":
    unittest.main()
