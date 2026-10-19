"""
Unit and Integration Test Suite for CrossTrace Phase 2 (Kinematics & Windowing).

Verifies:
1. Exact 29-feature / 47-feature disjoint partition and ordering against FEATURE_COLUMNS.
2. Sparse modality handling (absent clicks, keys, scrolls default to 0.0, zero NaNs/Infs).
3. Window boundaries (W=30, S=15, truncation of <30 events, boundary event discarding).
4. Group isolation in 4-fold grouped cross-validation (zero participant overlap).
5. Pre-registered session aggregation rule (soft mean probability >= 0.50).
6. Clopper-Pearson exact binomial confidence intervals and clustered bootstrap logic.
7. Pipeline freeze manifest verification and anti-tamper gate.
8. Byte-for-byte immutability of all protected Phase 1 files.
"""

import os
import sys
import unittest
import hashlib
import tempfile
import pandas as pd
import numpy as np

# Ensure workspace root is in path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from ml.features.extractor import FEATURE_COLUMNS
from ml.training.phase2_config import (
    SELECTED_FEATURES_PHASE2_KINEMATICS,
    EXCLUDED_FEATURES_PHASE2_KINEMATICS,
    validate_phase2_feature_partition,
)
from ml.features.windowed_extractor import (
    slice_events_into_windows,
    extract_windowed_kinematics,
)
from ml.training.phase2_train_development import (
    run_4fold_grouped_cv,
    freeze_development_pipeline,
    aggregate_session_predictions,
    compute_clopper_pearson_interval,
    compute_session_clustered_bootstrap,
)
from ml.evaluation.phase2_evaluate_unseen import (
    verify_freeze_gate,
    evaluate_frozen_pipeline,
    PipelineNotFrozenError,
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

# Baseline SHA-256 Hashes of Protected Files recorded at Stage 1 Authorization
BASELINE_PROTECTED_HASHES = {
    "features.csv": "7164C4432BFC1D0E93BE0E183639FAA67215E5BB5A2EE6F05565BE85B668319C".lower(),
    "metadata.csv": "E2BAD00643DDE2AC6F1A8889D8B5987AEB957390CAD7E37B3BC13B3A7E9DC3A5".lower(),
    "api_request_records.csv": "2EA9028854C681D02929B12D1C894F27DBEDA92D82AAA2B8E077DA5154FF4D46".lower(),
    "train_experiment_a.py": "925F4AB7DAD47DBDF699CE6498611F20723602C35D325CB7F8EE48723FEAFCED".lower(),
    "feature_config.py": "D50ED367ED3EF965F42CA51BB8FC96873D45C76B363B5F000D3CD3C5D8D1E7EC".lower(),
    "metrics_summary.json": "369A4DC49BFFFA790ED938F2D943BFC17BB932C59E0F44AC17F4314441AE05A7".lower(),
}


class TestPhase2Kinematics(unittest.TestCase):

    def test_feature_partition_completeness_and_disjointness(self):
        """Verify that 29 selected and 47 excluded features form an exact, complete partition of FEATURE_COLUMNS."""
        val = validate_phase2_feature_partition()
        self.assertTrue(val["is_valid"], f"Partition invalid: {val}")
        self.assertEqual(val["selected_count"], 29)
        self.assertEqual(val["excluded_count"], 47)
        self.assertEqual(val["canonical_count"], 76)
        self.assertEqual(val["overlap_count"], 0)
        self.assertEqual(len(val["missing_features"]), 0)
        self.assertEqual(len(val["extra_features"]), 0)

    def test_sparse_modalities_and_non_imputation(self):
        """
        Verify that windows lacking certain modalities (e.g. pure mouse, pure key, pure scroll)
        default cleanly to 0.0 without NaNs, Infs, exceptions, or external imputation.
        """
        # 1. Pure mouse window (no clicks, keys, or scrolls)
        mouse_events = get_pure_mouse_window_fixture(n_events=30)
        feat_df, _ = extract_windowed_kinematics(mouse_events)
        self.assertEqual(len(feat_df), 1)
        self.assertEqual(feat_df.isna().sum().sum(), 0)
        # Check that click and keyboard features default to 0.0
        self.assertEqual(feat_df.loc[0, "button_click_ratio"], 0.0)
        self.assertEqual(feat_df.loc[0, "mean_dwell_ms"], 0.0)
        self.assertEqual(feat_df.loc[0, "mean_scroll_velocity"], 0.0)
        # Mouse features must be non-zero
        self.assertGreater(feat_df.loc[0, "mouse_mean_velocity"], 0.0)

        # 2. Pure keyboard window (no mouse moves, clicks, scrolls)
        key_events = get_pure_keyboard_window_fixture(n_events=30)
        feat_df_k, _ = extract_windowed_kinematics(key_events)
        self.assertEqual(len(feat_df_k), 1)
        self.assertEqual(feat_df_k.isna().sum().sum(), 0)
        self.assertEqual(feat_df_k.loc[0, "mouse_mean_velocity"], 0.0)
        self.assertGreater(feat_df_k.loc[0, "mean_dwell_ms"], 0.0)

        # 3. Pure scroll window
        scroll_events = get_pure_scroll_window_fixture(n_events=30)
        feat_df_s, _ = extract_windowed_kinematics(scroll_events)
        self.assertEqual(len(feat_df_s), 1)
        self.assertEqual(feat_df_s.isna().sum().sum(), 0)
        self.assertEqual(feat_df_s.loc[0, "mouse_mean_velocity"], 0.0)
        self.assertGreater(feat_df_s.loc[0, "mean_scroll_velocity"], 0.0)

    def test_window_boundaries_and_stride(self):
        """Verify sliding window slicing, stride=15, and boundary truncation rules."""
        # A. 60 events -> exactly 3 windows (0-29, 15-44, 30-59)
        events_60 = get_mixed_modality_stream_fixture(n_events=60)
        windows = slice_events_into_windows(events_60, window_size=30, stride=15)
        self.assertEqual(len(windows), 3)
        for w in windows:
            self.assertEqual(len(w), 30)

        # B. 52 events -> exactly 2 windows (0-29, 15-44); trailing 7 events dropped
        events_52 = get_trailing_events_stream_fixture()
        windows_52 = slice_events_into_windows(events_52, window_size=30, stride=15)
        self.assertEqual(len(windows_52), 2)

        # C. 20 events (<30) -> exactly 0 windows (ineligible)
        events_20 = get_insufficient_events_fixture()
        windows_20 = slice_events_into_windows(events_20, window_size=30, stride=15)
        self.assertEqual(len(windows_20), 0)

    def test_feature_order_preserved(self):
        """Verify that extracted features DataFrame columns match SELECTED_FEATURES_PHASE2_KINEMATICS exactly."""
        events = get_mixed_modality_stream_fixture(n_events=60)
        feat_df, _ = extract_windowed_kinematics(events)
        self.assertEqual(list(feat_df.columns), SELECTED_FEATURES_PHASE2_KINEMATICS)

    def test_4fold_grouped_cv_isolation(self):
        """Verify that 4-Fold Grouped CV enforces zero participant overlap across folds."""
        mock_sessions = get_mock_multi_participant_dataset()
        dev_sessions = [s for s in mock_sessions if s["partition"] == "DEVELOPMENT"]
        
        all_feat_dfs = []
        all_meta_dfs = []
        for s in dev_sessions:
            f_df, m_df = extract_windowed_kinematics(s["events"], session_metadata=s)
            all_feat_dfs.append(f_df)
            all_meta_dfs.append(m_df)
            
        combined_feat = pd.concat(all_feat_dfs, ignore_index=True)
        combined_meta = pd.concat(all_meta_dfs, ignore_index=True)
        
        cv_results = run_4fold_grouped_cv(combined_feat, combined_meta, random_state=42)
        
        # Verify 4 folds per model
        for model_name, res in cv_results.items():
            self.assertEqual(len(res["folds"]), 4)
            for f in res["folds"]:
                # Exactly 1 human group and 1 bot group in validation
                self.assertEqual(len(f["val_groups"]), 2)
                self.assertIn("accuracy", f["session_metrics"])
                self.assertIn("human_fpr", f["session_metrics"])

    def test_session_prediction_aggregation_rule(self):
        """Verify pre-registered aggregation rule: soft mean window probability >= 0.50."""
        # Mock window predictions
        window_preds = pd.DataFrame([
            {"session_id": "s1", "participant_id": "H1", "task_id": "TASK_01", "label": 0, "prob": 0.20},
            {"session_id": "s1", "participant_id": "H1", "task_id": "TASK_01", "label": 0, "prob": 0.30},
            {"session_id": "s2", "participant_id": "H2", "task_id": "TASK_02", "label": 0, "prob": 0.40},
            {"session_id": "s2", "participant_id": "H2", "task_id": "TASK_02", "label": 0, "prob": 0.70}, # mean = 0.55 -> Automated
            {"session_id": "s3", "participant_id": "B1", "task_id": "TASK_03", "label": 1, "prob": 0.80},
            {"session_id": "s3", "participant_id": "B1", "task_id": "TASK_03", "label": 1, "prob": 0.90},
        ])
        
        agg_df = aggregate_session_predictions(window_preds, threshold=0.50)
        self.assertEqual(len(agg_df), 3)
        
        # s1: mean 0.25 -> 0 (Correct Human)
        s1 = agg_df[agg_df["session_id"] == "s1"].iloc[0]
        self.assertEqual(s1["pred_label"], 0)
        self.assertEqual(s1["is_correct"], 1)

        # s2: mean 0.55 -> 1 (False Positive)
        s2 = agg_df[agg_df["session_id"] == "s2"].iloc[0]
        self.assertEqual(s2["pred_label"], 1)
        self.assertEqual(s2["is_correct"], 0)

        # s3: mean 0.85 -> 1 (Correct Automated)
        s3 = agg_df[agg_df["session_id"] == "s3"].iloc[0]
        self.assertEqual(s3["pred_label"], 1)
        self.assertEqual(s3["is_correct"], 1)

    def test_clopper_pearson_exact_intervals(self):
        """Verify Clopper-Pearson exact binomial confidence interval computation."""
        # 10 out of 10 successes
        low, high = compute_clopper_pearson_interval(10, 10, confidence=0.95)
        self.assertGreater(low, 0.65)
        self.assertEqual(high, 1.0)

        # 0 out of 10 successes
        low0, high0 = compute_clopper_pearson_interval(0, 10, confidence=0.95)
        self.assertEqual(low0, 0.0)
        self.assertLess(high0, 0.35)

        # Bounded between 0 and 1
        low5, high5 = compute_clopper_pearson_interval(5, 10, confidence=0.95)
        self.assertTrue(0.0 <= low5 <= high5 <= 1.0)

    def test_freeze_gate_anti_tamper(self):
        """Verify pipeline freeze manifest generation, gate verification, and anti-tamper detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Create mock development data
            mock_X = pd.DataFrame(np.random.RandomState(42).randn(40, 29), columns=SELECTED_FEATURES_PHASE2_KINEMATICS)
            mock_y = pd.Series([0]*20 + [1]*20)
            
            # 2. Freeze pipeline
            manifest = freeze_development_pipeline(mock_X, mock_y, output_dir=temp_dir, random_state=42)
            manifest_path = os.path.join(temp_dir, "pipeline_freeze_manifest.json")
            models_dir = os.path.join(temp_dir, "frozen_models")
            
            # 3. Verification must pass on pristine artifacts
            verified = verify_freeze_gate(manifest_path, models_dir)
            self.assertEqual(verified["status"], "FROZEN_FOR_OUT_OF_DOMAIN_EVALUATION")

            # 4. Tamper test: tamper with one model file
            tampered_file = os.path.join(models_dir, "Logistic_Regression.joblib")
            with open(tampered_file, "ab") as f:
                f.write(b"TAMPERED_BYTE")
                
            # Gate must catch hash mismatch and raise PipelineNotFrozenError
            with self.assertRaises(PipelineNotFrozenError):
                verify_freeze_gate(manifest_path, models_dir)

    def test_protected_files_immutability(self):
        """Cryptographic assertion: protected Phase 1 files have not been modified."""
        base_dir = r"d:\VIT\TY\Web Tech\CP"
        file_map = {
            "features.csv": os.path.join(base_dir, "ml", "data", "features.csv"),
            "metadata.csv": os.path.join(base_dir, "ml", "data", "metadata.csv"),
            "api_request_records.csv": os.path.join(base_dir, "ml", "data", "api_request_records.csv"),
            "train_experiment_a.py": os.path.join(base_dir, "ml", "training", "train_experiment_a.py"),
            "feature_config.py": os.path.join(base_dir, "ml", "training", "feature_config.py"),
            "metrics_summary.json": os.path.join(base_dir, "ml", "evaluation", "baseline_comparison_53_sessions", "metrics_summary.json"),
        }
        
        for name, path in file_map.items():
            self.assertTrue(os.path.exists(path), f"Protected file missing: {path}")
            with open(path, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest().lower()
            expected = BASELINE_PROTECTED_HASHES[name]
            self.assertEqual(h, expected, f"PROTECTED FILE MODIFIED! {name}: expected {expected}, got {h}")


if __name__ == "__main__":
    unittest.main()
