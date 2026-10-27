"""
Experiment B: Kinematic Classifier Training & Evaluation Engine.

Trains and evaluates a scale-free kinematic classifier using regularized Logistic Regression
with pipeline feature scaling, completely isolated from event counts and session duration shortcuts.

Guarantees:
1. Strict preservation of Experiment A artifacts, baseline reports, and protected dataset files.
2. Complete exclusion of shortcut features (mouse_event_count, duration, etc.).
3. Rigorous fold isolation: StandardScaler is fitted strictly on X_train inside each fold.
4. Comprehensive evaluation across Leave-One-Task-Out (LOTO) and Stratified Group K-Fold (participant-aware).
5. Defensible metrics: Balanced Accuracy, Macro-F1, Human FPR, Automated FPR, and confusion matrices.
6. NO probability calibration (Platt/Isotonic) applied, adhering to data sufficiency limits.
"""

from typing import Dict, Any, List, Tuple, Optional
import os
import sys
import json
import hashlib

workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import (
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

from ml.training.experiment_b_config import (
    SELECTED_FEATURES_EXPERIMENT_B_KINEMATIC,
    EXCLUDED_SHORTCUT_FEATURES_EXPERIMENT_B,
    load_experiment_b_dataset,
    get_selected_features_experiment_b,
)
from ml.training.evaluation_protocol import (
    EvaluationProtocol,
    LeakageAuditor,
    BaselineClassifier,
    calculate_metrics,
    FORBIDDEN_METADATA_COLUMNS,
)

# Re-export for direct consumer access
__all__ = [
    "SELECTED_FEATURES_EXPERIMENT_B_KINEMATIC",
    "EXCLUDED_SHORTCUT_FEATURES_EXPERIMENT_B",
    "run_experiment_b_evaluation",
    "train_and_save_candidate_b",
]


def run_experiment_b_evaluation(
    features_csv: str = "ml/data/features.csv",
    metadata_csv: str = "ml/data/metadata.csv",
    random_state: int = 42,
    C: float = 1.0,
) -> Dict[str, Any]:
    """
    Executes the reproducible Experiment B kinematic evaluation protocol across:
    1. Leave-One-Task-Out (LOTO) cross-validation (3 task folds).
    2. Stratified Group K-Fold cross-validation (5 participant-isolated folds).
    """
    # 1. Load dataset with strict kinematic selection
    X, y, meta = load_experiment_b_dataset(
        features_csv_path=features_csv,
        metadata_csv_path=metadata_csv,
    )

    # 2. Verify dimensionality & zero forbidden features
    expected_feature_count = len(SELECTED_FEATURES_EXPERIMENT_B_KINEMATIC)
    if X.shape[1] != expected_feature_count:
        raise ValueError(f"Feature count mismatch: got {X.shape[1]}, expected {expected_feature_count}")

    # Audit for target/metadata leakage
    LeakageAuditor.audit_feature_matrix(X)
    for col in FORBIDDEN_METADATA_COLUMNS:
        if col in X.columns:
            raise ValueError(f"Forbidden column '{col}' detected in feature matrix X!")

    # Audit that NO shortcut feature is present
    for shortcut in EXCLUDED_SHORTCUT_FEATURES_EXPERIMENT_B:
        if shortcut in X.columns:
            raise ValueError(f"Shortcut feature '{shortcut}' detected in Experiment B feature matrix!")

    # -------------------------------------------------------------------------
    # Protocol A: Leave-One-Task-Out (LOTO) Evaluation
    # -------------------------------------------------------------------------
    loto_folds = EvaluationProtocol.generate_loto_folds(meta, enforce_strict_groups=False)
    loto_results: List[Dict[str, Any]] = []

    for fold in loto_folds:
        X_train, y_train = X.iloc[fold.train_indices], y.iloc[fold.train_indices]
        X_test, y_test = X.iloc[fold.test_indices], y.iloc[fold.test_indices]
        meta_train, meta_test = meta.iloc[fold.train_indices], meta.iloc[fold.test_indices]

        # Audit split isolation
        LeakageAuditor.audit_split_isolation(X_train, X_test, meta_train, meta_test)

        # Baseline: Majority Class
        baseline_clf = BaselineClassifier(strategy="majority")
        baseline_clf.fit(X_train, y_train)
        base_pred = baseline_clf.predict(X_test)
        base_prob = baseline_clf.predict_proba(X_test)
        base_metrics = calculate_metrics(y_test, base_pred, base_prob)
        base_macro_f1 = float(f1_score(y_test, base_pred, average="macro", zero_division=0))
        base_fp = base_metrics["confusion_matrix"]["fp"]
        base_tn = base_metrics["confusion_matrix"]["tn"]
        base_fn = base_metrics["confusion_matrix"]["fn"]
        base_tp = base_metrics["confusion_matrix"]["tp"]
        base_human_fpr = float(base_fp / (base_fp + base_tn)) if (base_fp + base_tn) > 0 else 0.0
        base_auto_fpr = float(base_fn / (base_fn + base_tp)) if (base_fn + base_tp) > 0 else 0.0

        # Candidate Model: Logistic Regression Pipeline with StandardScaler
        # StandardScaler is fit ONLY on X_train inside the pipeline
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(
                C=C,
                solver="lbfgs",
                max_iter=1000,
                random_state=random_state,
            )),
        ])
        pipeline.fit(X_train, y_train)

        lr_pred = pipeline.predict(X_test)
        lr_prob = pipeline.predict_proba(X_test)
        lr_metrics = calculate_metrics(y_test, lr_pred, lr_prob)
        lr_macro_f1 = float(f1_score(y_test, lr_pred, average="macro", zero_division=0))
        lr_fp = lr_metrics["confusion_matrix"]["fp"]
        lr_tn = lr_metrics["confusion_matrix"]["tn"]
        lr_fn = lr_metrics["confusion_matrix"]["fn"]
        lr_tp = lr_metrics["confusion_matrix"]["tp"]
        lr_human_fpr = float(lr_fp / (lr_fp + lr_tn)) if (lr_fp + lr_tn) > 0 else 0.0
        lr_auto_fpr = float(lr_fn / (lr_fn + lr_tp)) if (lr_fn + lr_tp) > 0 else 0.0

        loto_results.append({
            "fold_id": fold.fold_id,
            "train_tasks": fold.train_tasks,
            "test_tasks": fold.test_tasks,
            "train_samples": fold.n_train_total,
            "test_samples": fold.n_test_total,
            "train_human": fold.n_train_human,
            "train_automated": fold.n_train_automated,
            "test_human": fold.n_test_human,
            "test_automated": fold.n_test_automated,
            "baseline": {
                "balanced_accuracy": base_metrics["balanced_accuracy"],
                "precision": base_metrics["precision"],
                "recall": base_metrics["recall"],
                "f1": base_metrics["f1"],
                "macro_f1": round(base_macro_f1, 4),
                "roc_auc": base_metrics["roc_auc"],
                "human_fpr": round(base_human_fpr, 4),
                "automated_fpr": round(base_auto_fpr, 4),
                "confusion_matrix": base_metrics["confusion_matrix"],
            },
            "candidate_logistic_regression": {
                "balanced_accuracy": lr_metrics["balanced_accuracy"],
                "precision": lr_metrics["precision"],
                "recall": lr_metrics["recall"],
                "f1": lr_metrics["f1"],
                "macro_f1": round(lr_macro_f1, 4),
                "roc_auc": lr_metrics["roc_auc"],
                "human_fpr": round(lr_human_fpr, 4),
                "automated_fpr": round(lr_auto_fpr, 4),
                "confusion_matrix": lr_metrics["confusion_matrix"],
            },
        })

    # -------------------------------------------------------------------------
    # Protocol B: Stratified Group K-Fold Evaluation (Participant Isolation)
    # -------------------------------------------------------------------------
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=random_state)
    groups = meta["participant_id"].to_numpy()
    sgkf_results: List[Dict[str, Any]] = []

    for fold_idx, (train_idx, test_idx) in enumerate(sgkf.split(X, y, groups=groups)):
        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
        X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]
        meta_train, meta_test = meta.iloc[train_idx], meta.iloc[test_idx]

        # Audit split isolation
        LeakageAuditor.audit_split_isolation(X_train, X_test, meta_train, meta_test, check_groups=True)

        train_parts = sorted(meta_train["participant_id"].unique())
        test_parts = sorted(meta_test["participant_id"].unique())

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(
                C=C,
                solver="lbfgs",
                max_iter=1000,
                random_state=random_state,
            )),
        ])
        pipeline.fit(X_train, y_train)

        lr_pred = pipeline.predict(X_test)
        lr_prob = pipeline.predict_proba(X_test)
        lr_metrics = calculate_metrics(y_test, lr_pred, lr_prob)
        lr_macro_f1 = float(f1_score(y_test, lr_pred, average="macro", zero_division=0))
        lr_fp = lr_metrics["confusion_matrix"]["fp"]
        lr_tn = lr_metrics["confusion_matrix"]["tn"]
        lr_fn = lr_metrics["confusion_matrix"]["fn"]
        lr_tp = lr_metrics["confusion_matrix"]["tp"]
        lr_human_fpr = float(lr_fp / (lr_fp + lr_tn)) if (lr_fp + lr_tn) > 0 else 0.0
        lr_auto_fpr = float(lr_fn / (lr_fn + lr_tp)) if (lr_fn + lr_tp) > 0 else 0.0

        sgkf_results.append({
            "fold_id": f"SGKF_FOLD_{fold_idx + 1}",
            "train_participants": train_parts,
            "test_participants": test_parts,
            "train_samples": len(train_idx),
            "test_samples": len(test_idx),
            "train_human": int((y_train == 0).sum()),
            "train_automated": int((y_train == 1).sum()),
            "test_human": int((y_test == 0).sum()),
            "test_automated": int((y_test == 1).sum()),
            "candidate_logistic_regression": {
                "balanced_accuracy": lr_metrics["balanced_accuracy"],
                "precision": lr_metrics["precision"],
                "recall": lr_metrics["recall"],
                "f1": lr_metrics["f1"],
                "macro_f1": round(lr_macro_f1, 4),
                "roc_auc": lr_metrics["roc_auc"],
                "human_fpr": round(lr_human_fpr, 4),
                "automated_fpr": round(lr_auto_fpr, 4),
                "confusion_matrix": lr_metrics["confusion_matrix"],
            },
        })

    # -------------------------------------------------------------------------
    # Aggregate Metrics Calculation
    # -------------------------------------------------------------------------
    def mean_val(results, model_key, metric_key):
        vals = [r[model_key][metric_key] for r in results if r[model_key][metric_key] is not None]
        return round(float(np.mean(vals)), 4) if vals else None

    loto_aggregate_lr = {
        "mean_balanced_accuracy": mean_val(loto_results, "candidate_logistic_regression", "balanced_accuracy"),
        "mean_precision": mean_val(loto_results, "candidate_logistic_regression", "precision"),
        "mean_recall": mean_val(loto_results, "candidate_logistic_regression", "recall"),
        "mean_f1": mean_val(loto_results, "candidate_logistic_regression", "f1"),
        "mean_macro_f1": mean_val(loto_results, "candidate_logistic_regression", "macro_f1"),
        "mean_roc_auc": mean_val(loto_results, "candidate_logistic_regression", "roc_auc"),
        "mean_human_fpr": mean_val(loto_results, "candidate_logistic_regression", "human_fpr"),
        "mean_automated_fpr": mean_val(loto_results, "candidate_logistic_regression", "automated_fpr"),
    }

    sgkf_aggregate_lr = {
        "mean_balanced_accuracy": mean_val(sgkf_results, "candidate_logistic_regression", "balanced_accuracy"),
        "mean_precision": mean_val(sgkf_results, "candidate_logistic_regression", "precision"),
        "mean_recall": mean_val(sgkf_results, "candidate_logistic_regression", "recall"),
        "mean_f1": mean_val(sgkf_results, "candidate_logistic_regression", "f1"),
        "mean_macro_f1": mean_val(sgkf_results, "candidate_logistic_regression", "macro_f1"),
        "mean_roc_auc": mean_val(sgkf_results, "candidate_logistic_regression", "roc_auc"),
        "mean_human_fpr": mean_val(sgkf_results, "candidate_logistic_regression", "human_fpr"),
        "mean_automated_fpr": mean_val(sgkf_results, "candidate_logistic_regression", "automated_fpr"),
    }

    # -------------------------------------------------------------------------
    # Full Dataset Fit for Coefficients and Interpretation
    # -------------------------------------------------------------------------
    full_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            C=C,
            solver="lbfgs",
            max_iter=1000,
            random_state=random_state,
        )),
    ])
    full_pipeline.fit(X, y)
    coefs = full_pipeline.named_steps["classifier"].coef_[0]
    intercept = float(full_pipeline.named_steps["classifier"].intercept_[0])
    feature_coefficients = {
        feat: round(float(c), 4)
        for feat, c in sorted(zip(X.columns, coefs), key=lambda x: abs(x[1]), reverse=True)
    }

    return {
        "dataset_summary": {
            "total_sessions": len(X),
            "human_sessions": int((y == 0).sum()),
            "automated_sessions": int((y == 1).sum()),
            "feature_count": X.shape[1],
            "tasks": sorted(meta["task_id"].unique()),
            "participants": sorted(meta["participant_id"].unique()),
        },
        "loto_results": loto_results,
        "loto_aggregate": loto_aggregate_lr,
        "sgkf_results": sgkf_results,
        "sgkf_aggregate": sgkf_aggregate_lr,
        "feature_coefficients": feature_coefficients,
        "intercept": round(intercept, 4),
    }


def train_and_save_candidate_b(
    model_output_path: str = "ml/models/experiment_b_logistic_regression.joblib",
    manifest_output_path: str = "ml/models/experiment_b_manifest.json",
    features_csv: str = "ml/data/features.csv",
    metadata_csv: str = "ml/data/metadata.csv",
    random_state: int = 42,
    C: float = 1.0,
) -> Dict[str, Any]:
    """
    Trains the full candidate Experiment B Logistic Regression Pipeline on permitted data
    and serializes the candidate model and manifest to new Experiment B filenames.
    Preserves Experiment A artifacts completely unchanged.
    """
    # Safeguard check against overwriting Experiment A
    forbidden_targets = {
        "experiment_a_xgboost.joblib",
        "experiment_a_manifest.json",
        "features.csv",
        "metadata.csv",
    }
    for forbidden in forbidden_targets:
        if forbidden in os.path.basename(model_output_path) or forbidden in os.path.basename(manifest_output_path):
            raise ValueError(f"Safety Violation: Cannot save to protected Experiment A target: {forbidden}")

    # Evaluate first
    eval_results = run_experiment_b_evaluation(
        features_csv=features_csv,
        metadata_csv=metadata_csv,
        random_state=random_state,
        C=C,
    )

    # Load and fit final candidate pipeline
    X, y, meta = load_experiment_b_dataset(features_csv, metadata_csv)
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            C=C,
            solver="lbfgs",
            max_iter=1000,
            random_state=random_state,
        )),
    ])
    pipeline.fit(X, y)

    # Serialize candidate model
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump(pipeline, model_output_path)

    # Calculate SHA-256 hash of serialized artifact
    with open(model_output_path, "rb") as f:
        model_sha256 = hashlib.sha256(f.read()).hexdigest()

    with open(features_csv, "rb") as f:
        dataset_sha256 = hashlib.sha256(f.read()).hexdigest()

    # Build Experiment B manifest
    manifest = {
        "manifest_type": "CrossTrace Experiment B Candidate Model Manifest",
        "model_metadata": {
            "model_type": "sklearn.pipeline.Pipeline[StandardScaler, LogisticRegression]",
            "model_library": "scikit-learn",
            "model_version": "1.0.0-candidate",
            "serialization_format": "joblib",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "EXPERIMENTAL_CANDIDATE_MODEL",
            "random_state": random_state,
            "hyperparameters": {
                "C": C,
                "penalty": "l2",
                "solver": "lbfgs",
                "max_iter": 1000,
            },
        },
        "training_dataset": {
            "path": features_csv,
            "dataset_sha256": dataset_sha256,
            "total_sessions": len(X),
            "human_sessions": int((y == 0).sum()),
            "automated_sessions": int((y == 1).sum()),
            "partition": "phase1_baseline_development",
        },
        "feature_configuration": {
            "feature_count": len(SELECTED_FEATURES_EXPERIMENT_B_KINEMATIC),
            "ordered_features": SELECTED_FEATURES_EXPERIMENT_B_KINEMATIC,
            "excluded_shortcuts": EXCLUDED_SHORTCUT_FEATURES_EXPERIMENT_B,
            "scaling_applied": True,
            "scaler_type": "StandardScaler",
        },
        "decision_policy": {
            "default_decision_threshold": 0.5,
            "label_encoding": {
                "0": "HUMAN",
                "1": "AUTOMATED",
            },
            "probability_interpretation": "Uncalibrated classification risk score. Probability calibration (Platt/Isotonic) was NOT applied due to sample size constraints.",
        },
        "validation_summary": {
            "loto_aggregate": eval_results["loto_aggregate"],
            "sgkf_aggregate": eval_results["sgkf_aggregate"],
            "feature_coefficients": eval_results["feature_coefficients"],
        },
        "model_artifact": {
            "filename": os.path.basename(model_output_path),
            "relative_path": model_output_path,
            "artifact_sha256": model_sha256,
        },
        "artifact_integrity": {
            "artifact_path": model_output_path,
            "artifact_sha256": model_sha256,
        },
    }

    with open(manifest_output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return {
        "model_path": model_output_path,
        "manifest_path": manifest_output_path,
        "model_sha256": model_sha256,
        "evaluation_results": eval_results,
    }


def main():
    print("=" * 80)
    print("EXPERIMENT B: KINEMATIC CLASSIFIER TRAINING & EVALUATION")
    print("=" * 80)

    res = train_and_save_candidate_b()
    eval_res = res["evaluation_results"]
    d_sum = eval_res["dataset_summary"]

    print(f"Dataset : {d_sum['total_sessions']} sessions ({d_sum['human_sessions']} Human, {d_sum['automated_sessions']} Automated)")
    print(f"Features: {d_sum['feature_count']} scale-free kinematic features (Zero Event Count/Duration Shortcuts)")
    print(f"Tasks   : {d_sum['tasks']}")
    print(f"Model   : Pipeline[StandardScaler, LogisticRegression(C=1.0, penalty='l2')]")
    print(f"Artifact: {res['model_path']} (SHA-256: {res['model_sha256'][:16]}...)")
    print()

    print("--- 1. LEAVE-ONE-TASK-OUT (LOTO) RESULTS ---")
    for r in eval_res["loto_results"]:
        lr = r["candidate_logistic_regression"]
        print(f"Fold: {r['fold_id']}")
        print(f"  Train: {r['train_tasks']} ({r['train_samples']} samples: {r['train_human']}H, {r['train_automated']}A)")
        print(f"  Test : {r['test_tasks']} ({r['test_samples']} samples: {r['test_human']}H, {r['test_automated']}A)")
        print(f"  Candidate LR : BalAcc={lr['balanced_accuracy']:.4f}, Prec={lr['precision']:.4f}, Rec={lr['recall']:.4f}, MacroF1={lr['macro_f1']:.4f}, HumanFPR={lr['human_fpr']:.4f}, AutoFPR={lr['automated_fpr']:.4f}, CM={lr['confusion_matrix']}")
        print()

    print("--- 2. STRATIFIED GROUP K-FOLD (PARTICIPANT ISOLATION) RESULTS ---")
    for r in eval_res["sgkf_results"]:
        lr = r["candidate_logistic_regression"]
        print(f"Fold: {r['fold_id']}")
        print(f"  Test Participants: {r['test_participants']} ({r['test_samples']} samples: {r['test_human']}H, {r['test_automated']}A)")
        print(f"  Candidate LR     : BalAcc={lr['balanced_accuracy']:.4f}, Prec={lr['precision']:.4f}, Rec={lr['recall']:.4f}, MacroF1={lr['macro_f1']:.4f}, HumanFPR={lr['human_fpr']:.4f}, AutoFPR={lr['automated_fpr']:.4f}, CM={lr['confusion_matrix']}")
        print()

    print("--- 3. AGGREGATE PROTOCOL SUMMARY ---")
    loto_agg = eval_res["loto_aggregate"]
    sgkf_agg = eval_res["sgkf_aggregate"]
    print(f"  LOTO Mean Metrics : BalAcc={loto_agg['mean_balanced_accuracy']:.4f}, MacroF1={loto_agg['mean_macro_f1']:.4f}, HumanFPR={loto_agg['mean_human_fpr']:.4f}, AutoFPR={loto_agg['mean_automated_fpr']:.4f}")
    print(f"  SGKF Mean Metrics : BalAcc={sgkf_agg['mean_balanced_accuracy']:.4f}, MacroF1={sgkf_agg['mean_macro_f1']:.4f}, HumanFPR={sgkf_agg['mean_human_fpr']:.4f}, AutoFPR={sgkf_agg['mean_automated_fpr']:.4f}")
    print()

    print("--- 4. FEATURE COEFFICIENTS (LOG-ODDS IMPACT ON AUTOMATED CLASS) ---")
    for feat, coef in eval_res["feature_coefficients"].items():
        print(f"  {feat:30s}: {coef:+.4f}")
    print(f"  {'INTERCEPT':30s}: {eval_res['intercept']:+.4f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
