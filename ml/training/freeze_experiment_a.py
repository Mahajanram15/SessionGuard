"""
CrossTrace Experiment A Model Freeze Engine.

Fits the authorized Phase 1 demonstration XGBoost model on the 53-session development dataset,
serializes the estimator to ml/models/experiment_a_xgboost.joblib, and produces an immutable
provenance manifest (ml/models/experiment_a_manifest.json).

IMPORTANT NOTICE:
- This is a LOCAL DEMONSTRATION MODEL, NOT a production-validated bot detector.
- Fitting on all 53 development sessions is performed strictly for local inference readiness.
- Training set performance does NOT represent independent generalization.
- Historical Leave-One-Task-Out (LOTO) cross-validation results remain the sole benchmark.
- Strictly prohibited from loading, accessing, or inspecting held-out or quarantined data.
"""

from typing import Dict, Any, Tuple
import os
import sys
import json
import hashlib
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb

# Ensure workspace root is in sys.path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from ml.training.feature_config import load_experiment_dataset, SELECTED_FEATURES_EXPERIMENT_A
from ml.training.evaluation_protocol import LeakageAuditor, FORBIDDEN_METADATA_COLUMNS


# Historical Leave-One-Task-Out (LOTO) Cross-Validation Benchmark (Immutable)
HISTORICAL_LOTO_BENCHMARK = {
    "protocol": "Leave-One-Task-Out (LOTO) 3-Fold Cross-Validation",
    "mean_balanced_accuracy": 0.9259,
    "mean_macro_f1": 0.9388,
    "mean_precision": 1.0000,
    "mean_recall": 1.0000,
    "mean_human_fpr": 0.1481,
    "folds": [
        {
            "fold_id": "LOTO_TEST_TASK_03",
            "train_tasks": ["TASK_01", "TASK_02"],
            "test_tasks": ["TASK_03"],
            "train_samples": 36,
            "test_samples": 17,
            "balanced_accuracy": 1.0000,
            "macro_f1": 1.0000,
            "human_fpr": 0.0000,
        },
        {
            "fold_id": "LOTO_TEST_TASK_02",
            "train_tasks": ["TASK_01", "TASK_03"],
            "test_tasks": ["TASK_02"],
            "train_samples": 34,
            "test_samples": 19,
            "balanced_accuracy": 0.7778,
            "macro_f1": 0.8163,
            "human_fpr": 0.2222,
        },
        {
            "fold_id": "LOTO_TEST_TASK_01",
            "train_tasks": ["TASK_02", "TASK_03"],
            "test_tasks": ["TASK_01"],
            "train_samples": 36,
            "test_samples": 17,
            "balanced_accuracy": 1.0000,
            "macro_f1": 1.0000,
            "human_fpr": 0.0000,
        },
    ],
    "disclaimer": (
        "The historical LOTO metrics above represent the true offline generalizability estimate "
        "across experimental tasks. The final fitted model was trained on all 53 sessions to maximize "
        "signal coverage for local demonstration. Its training-set accuracy MUST NOT be cited as "
        "independent generalization performance."
    ),
}


def audit_quarantine_boundary(file_path: str) -> None:
    """Verifies that the dataset path does not reference quarantined or held-out partitions."""
    canonical_lower = os.path.realpath(file_path).lower()
    prohibited = ["quarantined", "held_out", "heldout", "method2", "method_2", "unseen"]
    for word in prohibited:
        if word in canonical_lower:
            raise PermissionError(
                f"Quarantine boundary violation! Path '{file_path}' contains forbidden substring '{word}'."
            )


def compute_file_sha256(file_path: str) -> str:
    """Computes lowercase hex SHA-256 digest of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def freeze_experiment_a_model(
    features_csv_path: str = "ml/data/features.csv",
    metadata_csv_path: str = "ml/data/metadata.csv",
    output_model_path: str = "ml/models/experiment_a_xgboost.joblib",
    output_manifest_path: str = "ml/models/experiment_a_manifest.json",
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Executes the authorized freeze of the Experiment A demonstration model.
    """
    # 1. Collision detection: stop immediately if outputs already exist
    if os.path.exists(output_model_path):
        raise FileExistsError(
            f"Target model artifact already exists at '{output_model_path}'. "
            "Halting execution to prevent overwriting existing model artifact."
        )
    if os.path.exists(output_manifest_path):
        raise FileExistsError(
            f"Target manifest artifact already exists at '{output_manifest_path}'. "
            "Halting execution to prevent overwriting existing manifest."
        )

    # 2. Quarantine boundary check
    audit_quarantine_boundary(features_csv_path)
    audit_quarantine_boundary(metadata_csv_path)

    # 3. Load dataset via established repository loader
    X, y, meta = load_experiment_dataset(
        features_csv_path=features_csv_path,
        metadata_csv_path=metadata_csv_path,
        experiment="A",
    )

    # 4. Strict schema & data integrity assertions
    expected_rows = 53
    expected_features = 64
    expected_human = 23
    expected_automated = 30

    if len(X) != expected_rows:
        raise ValueError(f"Row count mismatch: got {len(X)}, expected {expected_rows}")
    if X.shape[1] != expected_features:
        raise ValueError(f"Feature count mismatch: got {X.shape[1]}, expected {expected_features}")
    if list(X.columns) != SELECTED_FEATURES_EXPERIMENT_A:
        raise ValueError("Feature ordering mismatch against SELECTED_FEATURES_EXPERIMENT_A!")

    # Leakage audit
    LeakageAuditor.audit_feature_matrix(X)
    for col in FORBIDDEN_METADATA_COLUMNS:
        if col in X.columns:
            raise ValueError(f"Forbidden column '{col}' detected in feature matrix X!")

    # Check for NaN / Inf
    nan_count = int(X.isna().sum().sum())
    if nan_count > 0:
        raise ValueError(f"Dataset contains {nan_count} NaN values!")
    inf_count = int(np.isinf(X.to_numpy()).sum())
    if inf_count > 0:
        raise ValueError(f"Dataset contains {inf_count} infinite values!")

    # Validate label distribution
    unique_labels = set(y.unique())
    if unique_labels != {0, 1}:
        raise ValueError(f"Unexpected target labels: {unique_labels}, expected {{0, 1}}")
    n_human = int((y == 0).sum())
    n_auto = int((y == 1).sum())
    if n_human != expected_human:
        raise ValueError(f"Human class count mismatch: got {n_human}, expected {expected_human}")
    if n_auto != expected_automated:
        raise ValueError(f"Automated class count mismatch: got {n_auto}, expected {expected_automated}")

    # 5. Fit the authorized XGBoost model
    model = xgb.XGBClassifier(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        random_state=random_state,
        eval_metric="logloss",
    )
    model.fit(X, y)

    # 6. Ensure output directory exists
    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)

    # 7. Safe serialization
    temp_model_path = output_model_path + ".tmp"
    try:
        joblib.dump(model, temp_model_path, compress=3)
        os.replace(temp_model_path, output_model_path)
    except Exception as e:
        if os.path.exists(temp_model_path):
            os.remove(temp_model_path)
        raise RuntimeError(f"Failed to serialize model artifact: {e}") from e

    # 8. Compute artifact digest
    model_sha256 = compute_file_sha256(output_model_path)
    dataset_sha256 = compute_file_sha256(features_csv_path)

    # 9. Build provenance manifest
    now_utc = datetime.now(timezone.utc).isoformat()
    manifest = {
        "manifest_type": "CrossTrace Experiment A Frozen Model Manifest",
        "model_metadata": {
            "model_type": "xgboost.XGBClassifier",
            "model_library": "xgboost",
            "model_version": xgb.__version__,
            "serialization_format": "joblib",
            "created_at_utc": now_utc,
            "status": "FROZEN_DEMONSTRATION_MODEL",
            "random_state": random_state,
            "hyperparameters": {
                "n_estimators": 50,
                "max_depth": 3,
                "learning_rate": 0.1,
                "eval_metric": "logloss",
            },
        },
        "training_dataset": {
            "path": features_csv_path,
            "dataset_sha256": dataset_sha256,
            "total_sessions": len(X),
            "human_sessions": n_human,
            "automated_sessions": n_auto,
            "partition": "phase1_baseline_development",
        },
        "feature_configuration": {
            "feature_count": len(SELECTED_FEATURES_EXPERIMENT_A),
            "ordered_features": list(SELECTED_FEATURES_EXPERIMENT_A),
            "scaling_applied": False,
        },
        "decision_policy": {
            "default_decision_threshold": 0.50,
            "label_encoding": {
                "0": "HUMAN",
                "1": "AUTOMATED",
            },
            "positive_class": 1,
        },
        "model_artifact": {
            "filename": os.path.basename(output_model_path),
            "relative_path": output_model_path,
            "artifact_sha256": model_sha256,
        },
        "historical_evaluation_benchmark": HISTORICAL_LOTO_BENCHMARK,
        "demonstration_disclaimer": (
            "This model was fitted on all 53 authorized Phase 1 development sessions strictly for "
            "local system demonstration and backend integration. It is NOT a production-validated "
            "bot detection system. Training set predictions must not be used as evidence of generalization. "
            "The human false-positive rate under LOTO cross-validation is 14.81%."
        ),
    }

    # 10. Safe manifest write
    temp_manifest_path = output_manifest_path + ".tmp"
    try:
        with open(temp_manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        os.replace(temp_manifest_path, output_manifest_path)
    except Exception as e:
        if os.path.exists(temp_manifest_path):
            os.remove(temp_manifest_path)
        raise RuntimeError(f"Failed to write manifest artifact: {e}") from e

    return manifest


def verify_and_smoke_test(
    model_path: str = "ml/models/experiment_a_xgboost.joblib",
    manifest_path: str = "ml/models/experiment_a_manifest.json",
    features_csv_path: str = "ml/data/features.csv",
) -> Dict[str, Any]:
    """
    Reloads the frozen artifact, verifies manifest consistency, and executes a single
    read-only smoke test prediction on an authorized development sample.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifact not found at '{model_path}'")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest artifact not found at '{manifest_path}'")

    # 1. Verify live checksum against manifest
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    expected_sha256 = manifest["model_artifact"]["artifact_sha256"]
    actual_sha256 = compute_file_sha256(model_path)

    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"Artifact checksum violation! Expected {expected_sha256}, got {actual_sha256}"
        )

    # 2. Reload model
    loaded_model = joblib.load(model_path)
    if not hasattr(loaded_model, "predict") or not hasattr(loaded_model, "predict_proba"):
        raise TypeError("Loaded model does not implement predict or predict_proba interface!")

    # 3. Load development sample (Row 0 from authorized features.csv)
    df = pd.read_csv(features_csv_path)
    feature_cols = manifest["feature_configuration"]["ordered_features"]
    sample_X = df.loc[[0], feature_cols]
    true_label = int(df.loc[0, "label"])

    if sample_X.shape[1] != 64:
        raise ValueError(f"Input dimension mismatch: got {sample_X.shape[1]}, expected 64")

    # 4. Execute single smoke prediction
    pred_class = int(loaded_model.predict(sample_X)[0])
    pred_probs = loaded_model.predict_proba(sample_X)[0]
    prob_human = float(pred_probs[0])
    prob_automated = float(pred_probs[1])

    return {
        "integrity_verified": True,
        "artifact_sha256": actual_sha256,
        "smoke_test": {
            "sample_index": 0,
            "true_label": true_label,
            "true_class": "HUMAN" if true_label == 0 else "AUTOMATED",
            "predicted_label": pred_class,
            "predicted_class": "HUMAN" if pred_class == 0 else "AUTOMATED",
            "probability_human": round(prob_human, 4),
            "probability_automated": round(prob_automated, 4),
            "threshold": manifest["decision_policy"]["default_decision_threshold"],
            "disclaimer": (
                "Development-set smoke test only. Demonstrates that the frozen pipeline accepts "
                "the 64-feature vector and outputs valid probabilities. This is NOT an independent "
                "evaluation of generalization."
            ),
        },
    }


def main():
    print("=" * 78)
    print("CROSSTRACE: EXPERIMENT A MODEL FREEZE & DEMONSTRATION ARTIFACT GENERATION")
    print("=" * 78)

    model_dest = "ml/models/experiment_a_xgboost.joblib"
    manifest_dest = "ml/models/experiment_a_manifest.json"

    print(f"Target Model    : {model_dest}")
    print(f"Target Manifest : {manifest_dest}")
    print("Fitting model on authorized 53-session Phase 1 development dataset...")

    manifest = freeze_experiment_a_model(
        output_model_path=model_dest,
        output_manifest_path=manifest_dest,
    )

    print("Model fitted and serialized successfully.")
    print(f"Model SHA-256   : {manifest['model_artifact']['artifact_sha256']}")
    print(f"Dataset SHA-256 : {manifest['training_dataset']['dataset_sha256']}")
    print()

    print("Executing post-freeze verification and smoke test...")
    smoke_result = verify_and_smoke_test(
        model_path=model_dest,
        manifest_path=manifest_dest,
    )

    smoke = smoke_result["smoke_test"]
    print("Verification Succeeded:")
    print(f"  Artifact Integrity : Verified (matches manifest SHA-256)")
    print(f"  Sample Tested      : Row {smoke['sample_index']} (True: {smoke['true_class']})")
    print(f"  Predicted Class    : {smoke['predicted_class']} (Label: {smoke['predicted_label']})")
    print(f"  Probabilities      : P(Human)={smoke['probability_human']:.4f}, P(Automated)={smoke['probability_automated']:.4f}")
    print(f"  Decision Threshold : {smoke['threshold']}")
    print("=" * 78)


if __name__ == "__main__":
    main()
