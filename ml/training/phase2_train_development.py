"""
Phase 2 Development Training, 4-Fold Grouped Cross-Validation & Pipeline Freeze Engine.

Responsibilities:
1. Executes 4-Fold Grouped Cross-Validation across development participants (H1..H4, B1..B4).
2. Fits StandardScaler strictly on the training partition of each CV fold.
3. Implements the pre-registered session aggregation rule: soft mean window probability >= 0.50.
4. Computes Clopper-Pearson exact binomial intervals for session metrics and
   session-clustered block-bootstrap intervals for window metrics.
5. Fits the final pipeline on the full development partition and generates the SHA-256
   checksum manifest (pipeline_freeze_manifest.json).

CRITICAL QUARANTINE: This module contains ZERO imports, references, or path access to Method 2.
"""

from typing import List, Dict, Any, Tuple, Optional
import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
from scipy import stats

from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import joblib

# Ensure workspace root is in path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from ml.training.phase2_config import SELECTED_FEATURES_PHASE2_KINEMATICS
from ml.training.evaluation_protocol import LeakageAuditor, calculate_metrics, FORBIDDEN_METADATA_COLUMNS


# ==============================================================================
# 1. Statistical Uncertainty Functions
# ==============================================================================

def compute_clopper_pearson_interval(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Computes exact Clopper-Pearson binomial confidence interval using Beta distribution quantiles.
    Applies to discrete session-level counts (e.g. Accuracy, FPR, FNR) where sample count is small.
    """
    if n <= 0:
        return 0.0, 1.0
    alpha = 1.0 - confidence
    lower = 0.0 if k == 0 else float(stats.beta.ppf(alpha / 2.0, k, n - k + 1))
    upper = 1.0 if k == n else float(stats.beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))
    return round(lower, 4), round(upper, 4)


def compute_session_clustered_bootstrap(
    window_df: pd.DataFrame,
    y_true_col: str = "label",
    y_pred_col: str = "pred",
    y_prob_col: str = "prob",
    session_id_col: str = "session_id",
    n_bootstraps: int = 2000,
    confidence: float = 0.95,
    random_state: int = 42,
) -> Dict[str, Dict[str, float]]:
    """
    Computes session-clustered block-bootstrap confidence intervals for window-level metrics.
    Averages across clusters (sessions) with replacement, preserving within-session autocorrelation.
    """
    unique_sessions = window_df[session_id_col].unique()
    n_sessions = len(unique_sessions)
    if n_sessions < 2:
        return {}

    rng = np.random.RandomState(random_state)
    boot_f1 = []
    boot_bal_acc = []

    for _ in range(n_bootstraps):
        sampled_sessions = rng.choice(unique_sessions, size=n_sessions, replace=True)
        # Select all windows for sampled sessions
        sample_windows = pd.concat([window_df[window_df[session_id_col] == s] for s in sampled_sessions], ignore_index=True)

        y_t = sample_windows[y_true_col].to_numpy()
        y_p = sample_windows[y_pred_col].to_numpy()
        y_pr = sample_windows[y_prob_col].to_numpy() if y_prob_col in sample_windows.columns else None

        m = calculate_metrics(y_t, y_p, y_pr)
        boot_f1.append(m["f1"])
        boot_bal_acc.append(m["balanced_accuracy"])

    alpha = (1.0 - confidence) / 2.0
    return {
        "f1": {
            "lower": round(float(np.percentile(boot_f1, alpha * 100)), 4),
            "upper": round(float(np.percentile(boot_f1, (1.0 - alpha) * 100)), 4),
        },
        "balanced_accuracy": {
            "lower": round(float(np.percentile(boot_bal_acc, alpha * 100)), 4),
            "upper": round(float(np.percentile(boot_bal_acc, (1.0 - alpha) * 100)), 4),
        },
    }


# ==============================================================================
# 2. Pre-Registered Session Aggregation Rule
# ==============================================================================

def aggregate_session_predictions(
    window_preds_df: pd.DataFrame,
    threshold: float = 0.50,
) -> pd.DataFrame:
    """
    Applies the pre-registered mathematical session aggregation rule:
    1. Continuous score: mean window probability p_bar = (1/K) * sum(p_k).
    2. Binary decision: 1 (AUTOMATED) if p_bar >= 0.50 else 0 (HUMAN).
    """
    records = []
    for s_id, group in window_preds_df.groupby("session_id"):
        true_label = int(group["label"].iloc[0])
        participant_id = group["participant_id"].iloc[0]
        task_id = group["task_id"].iloc[0]
        k_windows = len(group)

        # Soft mean window automation probability
        p_bar = float(group["prob"].mean())
        pred_label = 1 if p_bar >= threshold else 0

        records.append({
            "session_id": s_id,
            "participant_id": participant_id,
            "task_id": task_id,
            "k_windows": k_windows,
            "mean_window_prob": round(p_bar, 4),
            "true_label": true_label,
            "pred_label": pred_label,
            "is_correct": int(true_label == pred_label),
        })

    return pd.DataFrame(records)


# ==============================================================================
# 3. Model Definition Helpers
# ==============================================================================

def create_model_instances(random_state: int = 42) -> Dict[str, Any]:
    """Instantiates candidate baseline models with fixed random seeds."""
    return {
        "Logistic_Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=random_state)),
        ]),
        "Random_Forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=4,
            min_samples_leaf=2,
            random_state=random_state,
        ),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
            eval_metric="logloss",
            random_state=random_state,
        ),
    }


# ==============================================================================
# 4. 4-Fold Grouped Cross-Validation Driver
# ==============================================================================

def run_4fold_grouped_cv(
    window_features_df: pd.DataFrame,
    window_metadata_df: pd.DataFrame,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Executes strictly isolated 4-Fold Grouped Cross-Validation across development participants.
    Folds fit StandardScaler only on the training portion of that fold.
    """
    # Verify feature columns and order
    if list(window_features_df.columns) != SELECTED_FEATURES_PHASE2_KINEMATICS:
        raise ValueError("Features do not match the exact pre-registered 29-feature Phase 2 configuration!")

    # Check for forbidden columns in X
    LeakageAuditor.audit_feature_matrix(window_features_df)

    # Participant groups
    groups = window_metadata_df["participant_id"].to_numpy()
    unique_groups = sorted(list(set(groups)))
    if len(unique_groups) < 4:
        raise ValueError(f"INSUFFICIENT_PARTICIPANT_GROUPS: Minimum 4 required for 4-fold grouped CV, found {len(unique_groups)}")

    sgkf = StratifiedGroupKFold(n_splits=4)
    y = window_metadata_df["label"].to_numpy()

    cv_results = {model_name: {"folds": [], "summary": {}} for model_name in ["Logistic_Regression", "Random_Forest", "XGBoost"]}

    for fold_idx, (train_idx, val_idx) in enumerate(sgkf.split(window_features_df, y, groups=groups)):
        # Partition data
        X_tr, y_tr = window_features_df.iloc[train_idx], y[train_idx]
        X_val, y_val = window_features_df.iloc[val_idx], y[val_idx]
        meta_val = window_metadata_df.iloc[val_idx].copy()

        # Audit group disjointness
        tr_groups = set(groups[train_idx])
        val_groups = set(groups[val_idx])
        overlap = tr_groups.intersection(val_groups)
        if overlap:
            raise ValueError(f"Participant group leakage detected in Fold {fold_idx + 1}: {overlap}")

        models = create_model_instances(random_state=random_state + fold_idx)

        for name, model in models.items():
            # For models that require scaling without an embedded pipeline scaler, fit scaler on X_tr only
            if name != "Logistic_Regression":
                scaler = StandardScaler()
                X_tr_proc = scaler.fit_transform(X_tr)
                X_val_proc = scaler.transform(X_val)
            else:
                X_tr_proc = X_tr
                X_val_proc = X_val

            model.fit(X_tr_proc, y_tr)
            y_pred = model.predict(X_val_proc)
            y_prob = model.predict_proba(X_val_proc)[:, 1] if hasattr(model, "predict_proba") else None

            # Window-level metrics
            w_metrics = calculate_metrics(y_val, y_pred, y_prob)

            # Session-level aggregation
            pred_df = meta_val.copy()
            pred_df["prob"] = y_prob if y_prob is not None else y_pred
            pred_df["pred"] = y_pred
            sess_agg_df = aggregate_session_predictions(pred_df, threshold=0.50)

            # Session-level discrete metrics
            n_sess = len(sess_agg_df)
            n_correct = int(sess_agg_df["is_correct"].sum())
            sess_acc = n_correct / n_sess if n_sess > 0 else 0.0
            lower_acc, upper_acc = compute_clopper_pearson_interval(n_correct, n_sess)

            # Class-specific error rates
            human_sess = sess_agg_df[sess_agg_df["true_label"] == 0]
            bot_sess = sess_agg_df[sess_agg_df["true_label"] == 1]

            fp_count = int((human_sess["pred_label"] == 1).sum())
            fn_count = int((bot_sess["pred_label"] == 0).sum())

            fpr = fp_count / len(human_sess) if len(human_sess) > 0 else 0.0
            fnr = fn_count / len(bot_sess) if len(bot_sess) > 0 else 0.0

            fpr_lower, fpr_upper = compute_clopper_pearson_interval(fp_count, len(human_sess))
            fnr_lower, fnr_upper = compute_clopper_pearson_interval(fn_count, len(bot_sess))

            cv_results[name]["folds"].append({
                "fold": fold_idx + 1,
                "val_groups": sorted(list(val_groups)),
                "n_val_windows": len(val_idx),
                "n_val_sessions": n_sess,
                "window_metrics": w_metrics,
                "session_metrics": {
                    "accuracy": round(sess_acc, 4),
                    "accuracy_ci_nominal": [lower_acc, upper_acc],
                    "human_fpr": round(fpr, 4),
                    "human_fpr_ci_nominal": [fpr_lower, fpr_upper],
                    "bot_fnr": round(fnr, 4),
                    "bot_fnr_ci_nominal": [fnr_lower, fnr_upper],
                },
            })

    return cv_results


# ==============================================================================
# 5. Final Pipeline Freeze Gate
# ==============================================================================

def freeze_development_pipeline(
    X_dev: pd.DataFrame,
    y_dev: pd.Series,
    output_dir: str = "ml/evaluation/phase2_kinematics",
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Fits final models on the entire Development partition, serializes weights,
    and generates an immutable SHA-256 Checksum Manifest.
    """
    models_dir = os.path.join(output_dir, "frozen_models")
    os.makedirs(models_dir, exist_ok=True)

    # 1. Fit final models on full development data
    models = create_model_instances(random_state=random_state)
    artifact_hashes = {}

    for name, model in models.items():
        if name != "Logistic_Regression":
            scaler = StandardScaler()
            X_proc = scaler.fit_transform(X_dev)
            # Save scaler and model together
            full_pipe = Pipeline([("scaler", scaler), ("model", model)])
            full_pipe.fit(X_dev, y_dev)
            path = os.path.join(models_dir, f"{name}.joblib")
            joblib.dump(full_pipe, path)
        else:
            model.fit(X_dev, y_dev)
            path = os.path.join(models_dir, f"{name}.joblib")
            joblib.dump(model, path)

        # Compute SHA-256 hash of serialized artifact
        with open(path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        artifact_hashes[f"{name}.joblib"] = h

    # 2. Build SHA-256 Checksum Manifest
    manifest = {
        "manifest_type": "SHA-256 Checksum Manifest (Phase 2 Development Freeze)",
        "status": "FROZEN_FOR_OUT_OF_DOMAIN_EVALUATION",
        "feature_configuration": {
            "feature_count": len(SELECTED_FEATURES_PHASE2_KINEMATICS),
            "ordered_features": list(SELECTED_FEATURES_PHASE2_KINEMATICS),
        },
        "windowing_parameters": {
            "window_size": 30,
            "stride": 15,
            "boundary_rule": "DISCARD_TRAILING_INCOMPLETE_EVENTS",
        },
        "decision_rule": {
            "aggregation": "SOFT_MEAN_WINDOW_PROBABILITY",
            "threshold": 0.50,
        },
        "development_dataset_hash": hashlib.sha256(X_dev.to_csv(index=False).encode("utf-8")).hexdigest(),
        "frozen_model_artifacts": artifact_hashes,
    }

    manifest_path = os.path.join(output_dir, "pipeline_freeze_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest
