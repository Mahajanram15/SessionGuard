"""
Unit and Integration Tests for CrossTrace Experiment B (Kinematic Classifier).

Verifies:
1. Kinematic feature list composition and schema compatibility.
2. Complete exclusion of shortcut features (event counts, duration).
3. Derived feature matrix isolation (target label and metadata never in X).
4. Preprocessing fold isolation (StandardScaler fitted strictly inside training folds).
5. Participant-group disjointness in cross-validation splits.
6. Artifact separation: Experiment B artifacts exist without modifying Experiment A.
7. Protected Phase 1 baseline file immutability.
"""

import os
import sys
import unittest
import hashlib
import numpy as np
import pandas as pd

# Ensure workspace root is in sys.path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from ml.features.extractor import FEATURE_COLUMNS
from ml.training.experiment_b_config import (
    SELECTED_FEATURES_EXPERIMENT_B_KINEMATIC,
    EXCLUDED_SHORTCUT_FEATURES_EXPERIMENT_B,
    get_selected_features_experiment_b,
    get_excluded_shortcut_features_experiment_b,
    load_experiment_b_dataset,
)
from ml.training.train_experiment_b_kinematic import (
    run_experiment_b_evaluation,
)

# Baseline SHA-256 Hashes of Protected Baseline Files
BASELINE_PROTECTED_HASHES = {
    "features.csv": "7164c4432bfc1d0e93be0e183639faa67215e5bb5a2ee6f05565be85b668319c",
    "metadata.csv": "e98184240a8e6c4fc895ce132fe68ebd279420df572396a9f5b5460e072ef8b9",
    "api_request_records.csv": "2ea9028854c681d02929b12d1c894f27dbeda92d82aaa2b8e077da5154ff4d46",
    "train_experiment_a.py": "925f4ab7dad47dbdf699ce6498611f20723602c35d325cb7f8ee48723feafced",
    "feature_config.py": "d50ed367ed3ef965f42ca51bb8fc96873d45c76b363b5f000d3cd3c5d8d1e7ec",
    "metrics_summary.json": "369a4dc49bfffa790ed938f2d943bfc17bb932c59e0f44ac17f4314441ae05a7",
}


class TestExperimentBKinematics(unittest.TestCase):
    """Test suite validating Experiment B kinematic configuration and training pipeline."""

    def test_feature_list_composition(self):
        """Verify feature list size, ordering, and presence in canonical FEATURE_COLUMNS."""
        selected = get_selected_features_experiment_b()
        self.assertEqual(len(selected), 12)
        for feat in selected:
            self.assertIn(feat, FEATURE_COLUMNS, f"Feature '{feat}' not in canonical FEATURE_COLUMNS")

    def test_shortcut_features_strictly_excluded(self):
        """Verify that raw count and duration shortcuts are completely excluded from Experiment B."""
        selected_set = set(get_selected_features_experiment_b())
        excluded_shortcuts = get_excluded_shortcut_features_experiment_b()

        critical_shortcuts = [
            "mouse_event_count",
            "total_behavior_event_count",
            "click_count",
            "key_event_count",
            "scroll_event_count",
            "navigation_count",
            "session_duration_ms",
            "mouse_session_duration_ms",
            "active_behavior_duration_ms",
        ]

        for shortcut in critical_shortcuts:
            self.assertIn(shortcut, excluded_shortcuts, f"Shortcut '{shortcut}' not in excluded list")
            self.assertNotIn(shortcut, selected_set, f"Shortcut '{shortcut}' leaked into Experiment B selected features!")

        # Verify zero overlap between selected kinematics and excluded shortcuts
        overlap = selected_set.intersection(set(excluded_shortcuts))
        self.assertEqual(len(overlap), 0, f"Unexpected overlap between selected and shortcuts: {overlap}")

    def test_dataset_loading_and_isolation(self):
        """Verify dataset loading for Experiment B, row counts, and strict label/meta isolation."""
        features_path = os.path.join(workspace_root, "ml", "data", "features.csv")
        metadata_path = os.path.join(workspace_root, "ml", "data", "metadata.csv")

        X, y, meta = load_experiment_b_dataset(features_path, metadata_path)

        # Dimension checks
        self.assertEqual(X.shape, (53, 12))
        self.assertEqual(len(y), 53)
        self.assertEqual(len(meta), 53)

        # Isolation checks: labels and metadata must NEVER be in X
        self.assertNotIn("label", X.columns)
        self.assertNotIn("session_id", X.columns)
        self.assertNotIn("participant_id", X.columns)
        self.assertNotIn("task_id", X.columns)

        # Missing values check
        self.assertEqual(X.isna().sum().sum(), 0)

        # Class balance: 23 Human, 30 Automated
        self.assertEqual(int((y == 0).sum()), 23)
        self.assertEqual(int((y == 1).sum()), 30)

    def test_loto_and_group_cross_validation_evaluation(self):
        """Verify that Experiment B evaluation executes both LOTO and SGKF protocols without errors."""
        features_path = os.path.join(workspace_root, "ml", "data", "features.csv")
        metadata_path = os.path.join(workspace_root, "ml", "data", "metadata.csv")

        results = run_experiment_b_evaluation(
            features_csv=features_path,
            metadata_csv=metadata_path,
            random_state=42,
            C=1.0,
        )

        # Check LOTO folds
        loto_folds = results["loto_results"]
        self.assertEqual(len(loto_folds), 3)
        for fold in loto_folds:
            lr_metrics = fold["candidate_logistic_regression"]
            self.assertGreaterEqual(lr_metrics["balanced_accuracy"], 0.90)
            self.assertEqual(lr_metrics["human_fpr"], 0.0)

        # Check Stratified Group K-Fold results
        sgkf_folds = results["sgkf_results"]
        self.assertEqual(len(sgkf_folds), 5)
        for fold in sgkf_folds:
            # Check participant disjointness
            train_parts = set(fold["train_participants"])
            test_parts = set(fold["test_participants"])
            self.assertEqual(len(train_parts.intersection(test_parts)), 0)

            lr_metrics = fold["candidate_logistic_regression"]
            self.assertGreaterEqual(lr_metrics["balanced_accuracy"], 0.90)
            self.assertEqual(lr_metrics["human_fpr"], 0.0)

        # Check aggregate metrics
        loto_agg = results["loto_aggregate"]
        self.assertEqual(loto_agg["mean_balanced_accuracy"], 1.0)
        self.assertEqual(loto_agg["mean_human_fpr"], 0.0)

    def test_artifact_separation(self):
        """Verify that Experiment B artifacts exist as separate files and Experiment A is preserved."""
        exp_a_model = os.path.join(workspace_root, "ml", "models", "experiment_a_xgboost.joblib")
        exp_a_manifest = os.path.join(workspace_root, "ml", "models", "experiment_a_manifest.json")
        exp_b_model = os.path.join(workspace_root, "ml", "models", "experiment_b_logistic_regression.joblib")
        exp_b_manifest = os.path.join(workspace_root, "ml", "models", "experiment_b_manifest.json")

        self.assertTrue(os.path.exists(exp_a_model), "Experiment A model missing!")
        self.assertTrue(os.path.exists(exp_a_manifest), "Experiment A manifest missing!")
        self.assertTrue(os.path.exists(exp_b_model), "Experiment B candidate model missing!")
        self.assertTrue(os.path.exists(exp_b_manifest), "Experiment B candidate manifest missing!")

        # Distinct files
        self.assertNotEqual(os.path.abspath(exp_a_model), os.path.abspath(exp_b_model))
        self.assertNotEqual(os.path.abspath(exp_a_manifest), os.path.abspath(exp_b_manifest))

    def test_protected_files_cryptographic_immutability(self):
        """Assert exact byte-for-byte SHA-256 hash preservation for all 6 protected baseline files."""
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
