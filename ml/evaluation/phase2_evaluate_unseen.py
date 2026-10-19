"""
Phase 2 Out-of-Domain & Unseen Method 2 Evaluation Engine.

Responsibilities:
1. Enforces the Cryptographic Pipeline Freeze Gate:
   - Verifies that pipeline_freeze_manifest.json exists and is valid.
   - Computes live SHA-256 hashes of all serialized model artifacts and verifies exact match.
2. Ingests held-out human participants (H5, H6) and quarantined Method 2 data strictly
   for single-pass, out-of-domain inference.
3. Applies the pre-registered decision rule (mean window probability >= 0.50).
4. Zero feedback loop: Cannot modify models, features, thresholds, or hyperparameters.

CRITICAL: In Stage 1, this script is verified exclusively using mock synthetic fixtures.
Real held-out human data and Method 2 data will be evaluated in Stage 3 only.
"""

from typing import List, Dict, Any, Tuple, Optional
import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
import joblib

# Ensure workspace root is in path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from ml.training.phase2_config import SELECTED_FEATURES_PHASE2_KINEMATICS
from ml.training.phase2_train_development import (
    aggregate_session_predictions,
    compute_clopper_pearson_interval,
    compute_session_clustered_bootstrap,
)
from ml.training.evaluation_protocol import calculate_metrics, LeakageAuditor


class PipelineNotFrozenError(RuntimeError):
    """Raised when the freeze manifest is missing, corrupt, or model hashes do not match."""
    pass


class SecurityIntegrityError(RuntimeError):
    """Raised when the independently supplied root manifest digest does not match the manifest on disk."""
    pass


def verify_external_root_digest(manifest_path: str, expected_root_digest: str) -> None:
    """
    Verifies the SHA-256 digest of the manifest against an independently supplied reference digest.
    
    Raises:
        SecurityIntegrityError: If the manifest does not match the external root digest.
    """
    if not os.path.exists(manifest_path):
        raise SecurityIntegrityError(f"Freeze manifest not found at: {manifest_path}")

    with open(manifest_path, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest().lower()

    expected_clean = expected_root_digest.strip().lower()
    if actual_hash != expected_clean:
        raise SecurityIntegrityError(
            f"ROOT MANIFEST INTEGRITY VIOLATION! Expected digest: '{expected_clean}', got live digest: '{actual_hash}'."
        )


def verify_freeze_gate(manifest_path: str, models_dir: str) -> Dict[str, Any]:
    """
    Verifies that the development pipeline has been frozen and that model artifacts
    have not been altered since the freeze.
    """
    if not os.path.exists(manifest_path):
        raise PipelineNotFrozenError(f"Freeze manifest not found at: {manifest_path}. Development pipeline has not been frozen!")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Verify feature configuration binding
    bound_features = manifest.get("feature_configuration", {}).get("ordered_features", [])
    if bound_features != SELECTED_FEATURES_PHASE2_KINEMATICS:
        raise PipelineNotFrozenError("Feature configuration mismatch between manifest and phase2_config!")

    # 2. Verify artifact SHA-256 hashes
    artifact_hashes = manifest.get("frozen_model_artifacts", {})
    if not artifact_hashes:
        raise PipelineNotFrozenError("No model artifacts bound in freeze manifest!")

    for filename, expected_hash in artifact_hashes.items():
        file_path = os.path.join(models_dir, filename)
        if not os.path.exists(file_path):
            raise PipelineNotFrozenError(f"Frozen model artifact missing: {file_path}")

        with open(file_path, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()

        if actual_hash != expected_hash:
            raise PipelineNotFrozenError(
                f"Artifact hash mismatch for {filename}! Expected {expected_hash}, got {actual_hash}. Pipeline integrity violated!"
            )

    return manifest


def execute_preload_quarantine_gate(
    manifest_path: str,
    models_dir: str,
    expected_root_digest: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enforces the complete pre-load quarantine evaluation gate:
    1. Verifies independent root manifest digest (if supplied).
    2. Verifies freeze manifest and model artifact checksums.
    Only returns when both gates succeed, guaranteeing zero access to quarantined files on failure.
    """
    if expected_root_digest is not None:
        verify_external_root_digest(manifest_path, expected_root_digest)

    return verify_freeze_gate(manifest_path, models_dir)


def evaluate_frozen_pipeline(
    X_test: pd.DataFrame,
    meta_test: pd.DataFrame,
    manifest_path: str = "ml/evaluation/phase2_kinematics/pipeline_freeze_manifest.json",
    models_dir: str = "ml/evaluation/phase2_kinematics/frozen_models",
    expected_root_digest: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes single-pass evaluation on out-of-domain data using strictly frozen model pipelines.
    Enforces pre-load quarantine verification before processing any test features.
    """
    # 1. Enforce pre-load quarantine gate verification
    manifest = execute_preload_quarantine_gate(manifest_path, models_dir, expected_root_digest=expected_root_digest)
    threshold = float(manifest.get("decision_rule", {}).get("threshold", 0.50))

    # 2. Verify feature matrix format
    LeakageAuditor.audit_feature_matrix(X_test)
    if list(X_test.columns) != SELECTED_FEATURES_PHASE2_KINEMATICS:
        raise ValueError("Evaluation features do not match the frozen 29-feature configuration!")

    artifact_hashes = manifest["frozen_model_artifacts"]
    eval_results = {}

    for filename in artifact_hashes:
        model_name = filename.replace(".joblib", "")
        file_path = os.path.join(models_dir, filename)
        pipeline = joblib.load(file_path)

        # Single-pass prediction
        y_test = meta_test["label"].to_numpy()
        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1] if hasattr(pipeline, "predict_proba") else y_pred

        # Window-level metrics
        w_metrics = calculate_metrics(y_test, y_pred, y_prob)

        # Window-level clustered bootstrap uncertainty
        w_pred_df = meta_test.copy()
        w_pred_df["prob"] = y_prob
        w_pred_df["pred"] = y_pred
        w_boot_ci = compute_session_clustered_bootstrap(w_pred_df, n_bootstraps=500, random_state=42)

        # Session-level aggregation
        sess_df = aggregate_session_predictions(w_pred_df, threshold=threshold)

        # Session-level discrete metrics
        n_sess = len(sess_df)
        n_correct = int(sess_df["is_correct"].sum())
        sess_acc = n_correct / n_sess if n_sess > 0 else 0.0
        acc_ci = compute_clopper_pearson_interval(n_correct, n_sess)

        # Class-specific rates
        human_sess = sess_df[sess_df["true_label"] == 0]
        bot_sess = sess_df[sess_df["true_label"] == 1]

        fp = int((human_sess["pred_label"] == 1).sum()) if len(human_sess) > 0 else 0
        fn = int((bot_sess["pred_label"] == 0).sum()) if len(bot_sess) > 0 else 0

        fpr = fp / len(human_sess) if len(human_sess) > 0 else None
        fnr = fn / len(bot_sess) if len(bot_sess) > 0 else None

        fpr_ci = compute_clopper_pearson_interval(fp, len(human_sess)) if len(human_sess) > 0 else None
        fnr_ci = compute_clopper_pearson_interval(fn, len(bot_sess)) if len(bot_sess) > 0 else None

        eval_results[model_name] = {
            "window_metrics": w_metrics,
            "window_metrics_clustered_ci": w_boot_ci,
            "session_metrics": {
                "n_sessions": n_sess,
                "n_human_sessions": len(human_sess),
                "n_bot_sessions": len(bot_sess),
                "accuracy": round(sess_acc, 4),
                "accuracy_ci_nominal": acc_ci,
                "human_fpr": round(fpr, 4) if fpr is not None else None,
                "human_fpr_ci_nominal": fpr_ci,
                "bot_fnr": round(fnr, 4) if fnr is not None else None,
                "bot_fnr_ci_nominal": fnr_ci,
            },
        }

    return eval_results
