"""
CrossTrace: Baseline Machine-Learning Experiment Engine (53 Sessions).

Compares Logistic Regression, Random Forest, and XGBoost on behavioral telemetry.
Strictly preserves existing data files and follows established project conventions:
1. Canonical 64-feature derived configuration from feature_config.py.
2. Leakage-free preprocessing (StandardScaler fit strictly on training folds).
3. Stratified 80/20 train/test split (42 train / 11 test).
4. Stratified 5-Fold cross-validation on training data.
5. StratifiedGroupKFold (5-fold) participant/profile leakage audit.
6. Comprehensive correlation audit exported to CSV.
"""

from typing import Dict, Any, List, Tuple
import os
import sys

# Ensure workspace root is in sys.path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

import json
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, StratifiedKFold, StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb

from ml.training.feature_config import load_experiment_dataset, SELECTED_FEATURES_EXPERIMENT_A
from ml.training.evaluation_protocol import (
    LeakageAuditor,
    calculate_metrics,
    FORBIDDEN_METADATA_COLUMNS,
)


def run_correlation_audit(
    features_csv_path: str = "ml/data/features.csv",
    output_csv_path: str = "ml/evaluation/baseline_comparison_53_sessions/feature_correlation_audit.csv",
) -> pd.DataFrame:
    """
    Performs full pairwise correlation audit across all numeric features in features.csv.
    Identifies zero-variance constants and collinear clusters (|r| >= 0.90 and >= 0.95).
    """
    df = pd.read_csv(features_csv_path)
    feature_cols = [c for c in df.columns if c != "label"]
    X = df[feature_cols].copy()

    # Identify zero-variance features
    zero_var = [c for c in feature_cols if X[c].nunique() <= 1]

    # Compute correlation matrix
    corr_matrix = X.corr(numeric_only=True)

    # Extract upper triangle pairs
    records = []
    cols = corr_matrix.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            f1 = cols[i]
            f2 = cols[j]
            r = corr_matrix.loc[f1, f2]
            abs_r = abs(r) if pd.notna(r) else 0.0
            if abs_r >= 0.80 or pd.isna(r):
                records.append({
                    "feature_1": f1,
                    "feature_2": f2,
                    "pearson_r": round(float(r), 4) if pd.notna(r) else None,
                    "abs_r": round(float(abs_r), 4),
                    "is_zero_variance": f1 in zero_var or f2 in zero_var,
                    "collinearity_tier": "EXTREME_GE_95" if abs_r >= 0.95 else ("HIGH_90_95" if abs_r >= 0.90 else "MODERATE_80_90"),
                })

    audit_df = pd.DataFrame(records)
    if not audit_df.empty:
        audit_df.sort_values(by="abs_r", ascending=False, inplace=True)

    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    audit_df.to_csv(output_csv_path, index=False)
    return audit_df


def get_model_instances(random_state: int = 42) -> Dict[str, Any]:
    """
    Instantiates the 3 candidate baseline models with fixed random seeds.
    Preprocessing (StandardScaler) is embedded in Pipeline for Logistic Regression.
    """
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


def evaluate_cv_folds(
    models: Dict[str, Any],
    X_train: pd.DataFrame,
    y_train: pd.Series,
    cv_splitter: Any,
    groups: Any = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluates models across CV folds, enforcing isolated fitting and metric tracking.
    """
    cv_results = {name: {"fold_metrics": [], "summary": {}} for name in models}

    for fold_idx, (train_idx, val_idx) in enumerate(cv_splitter.split(X_train, y_train, groups=groups)):
        X_tr, y_tr = X_train.iloc[train_idx], y_train.iloc[train_idx]
        X_val, y_val = X_train.iloc[val_idx], y_train.iloc[val_idx]

        # Audit split isolation
        LeakageAuditor.audit_feature_matrix(X_tr)
        LeakageAuditor.audit_feature_matrix(X_val)

        for name, model in models.items():
            # Clone/instantiate fresh model
            fresh_models = get_model_instances(random_state=42 + fold_idx)
            m = fresh_models[name]

            m.fit(X_tr, y_tr)
            y_pred = m.predict(X_val)
            y_prob = m.predict_proba(X_val) if hasattr(m, "predict_proba") else None

            metrics = calculate_metrics(y_val, y_pred, y_prob)
            metrics["fold"] = fold_idx + 1
            metrics["n_val"] = len(y_val)
            metrics["n_val_human"] = int((y_val == 0).sum())
            metrics["n_val_automated"] = int((y_val == 1).sum())
            cv_results[name]["fold_metrics"].append(metrics)

    # Compute mean and std
    for name in models:
        f_metrics = cv_results[name]["fold_metrics"]
        summary = {}
        for metric_key in ["balanced_accuracy", "precision", "recall", "f1"]:
            vals = [fm[metric_key] for fm in f_metrics]
            summary[f"{metric_key}_mean"] = round(float(np.mean(vals)), 4)
            summary[f"{metric_key}_std"] = round(float(np.std(vals)), 4)

        # ROC-AUC (handle None if any fold was single-class)
        auc_vals = [fm["roc_auc"] for fm in f_metrics if fm["roc_auc"] is not None]
        if auc_vals:
            summary["roc_auc_mean"] = round(float(np.mean(auc_vals)), 4)
            summary["roc_auc_std"] = round(float(np.std(auc_vals)), 4)
        else:
            summary["roc_auc_mean"] = None
            summary["roc_auc_std"] = None

        cv_results[name]["summary"] = summary

    return cv_results


def run_baseline_experiment(
    features_csv: str = "ml/data/features.csv",
    metadata_csv: str = "ml/data/metadata.csv",
    output_dir: str = "ml/evaluation/baseline_comparison_53_sessions",
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Main experiment execution driver.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Run feature correlation audit
    correlation_audit_csv = os.path.join(output_dir, "feature_correlation_audit.csv")
    corr_audit_df = run_correlation_audit(features_csv, correlation_audit_csv)

    # 2. Load dataset with canonical 64-feature configuration
    X, y, meta = load_experiment_dataset(
        features_csv_path=features_csv,
        metadata_csv_path=metadata_csv,
        experiment="A",
    )

    if X.shape[1] != len(SELECTED_FEATURES_EXPERIMENT_A):
        raise ValueError(f"Feature count mismatch: {X.shape[1]} vs {len(SELECTED_FEATURES_EXPERIMENT_A)}")

    # Leakage check
    LeakageAuditor.audit_feature_matrix(X)
    for col in FORBIDDEN_METADATA_COLUMNS:
        if col in X.columns:
            raise ValueError(f"Forbidden column '{col}' detected in feature matrix X!")

    total_sessions = len(X)
    n_human = int((y == 0).sum())
    n_automated = int((y == 1).sum())

    # 3. Stratified 80/20 Train/Test Split
    test_size = 11  # exactly 11 out of 53 sessions (~20.75%)
    X_train, X_test, y_train, y_test, meta_train, meta_test = train_test_split(
        X, y, meta,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    LeakageAuditor.audit_split_isolation(X_train, X_test, meta_train, meta_test)

    split_info = {
        "total_sessions": total_sessions,
        "n_human_total": n_human,
        "n_automated_total": n_automated,
        "n_train": len(X_train),
        "n_train_human": int((y_train == 0).sum()),
        "n_train_automated": int((y_train == 1).sum()),
        "n_test": len(X_test),
        "n_test_human": int((y_test == 0).sum()),
        "n_test_automated": int((y_test == 1).sum()),
        "test_session_ids": meta_test["session_id"].tolist(),
        "test_participants": meta_test["participant_id"].tolist(),
    }

    # 4. Training-Only Stratified 5-Fold Cross-Validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    models_cv = get_model_instances(random_state=random_state)
    train_cv_results = evaluate_cv_folds(models_cv, X_train, y_train, cv_splitter=skf)

    # 5. Fit on Full Training Set and Evaluate on Held-Out Test Set
    test_results = {}
    models_full = get_model_instances(random_state=random_state)
    for name, model in models_full.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None
        metrics = calculate_metrics(y_test, y_pred, y_prob)
        test_results[name] = metrics

    # 6. Participant/Profile Grouped Evaluation (StratifiedGroupKFold on Full Dataset)
    # Audits performance when entire participants/bot profiles are held out
    sgkf = StratifiedGroupKFold(n_splits=5)
    models_grouped = get_model_instances(random_state=random_state)
    grouped_cv_results = evaluate_cv_folds(
        models_grouped,
        X,
        y,
        cv_splitter=sgkf,
        groups=meta["participant_id"],
    )

    # 7. Compile Final Results Object
    experiment_results = {
        "experiment_name": "CrossTrace Baseline Behavioral Telemetry Model Comparison",
        "date": "2026-10-19",
        "dataset_info": split_info,
        "feature_selection": {
            "selected_feature_count": len(SELECTED_FEATURES_EXPERIMENT_A),
            "excluded_feature_count": 76 - len(SELECTED_FEATURES_EXPERIMENT_A),
            "collinear_pairs_ge_95": len(corr_audit_df[corr_audit_df["abs_r"] >= 0.95]) if not corr_audit_df.empty else 0,
            "collinear_pairs_ge_90": len(corr_audit_df[corr_audit_df["abs_r"] >= 0.90]) if not corr_audit_df.empty else 0,
        },
        "test_set_results": test_results,
        "training_cv_5fold_results": train_cv_results,
        "participant_grouped_cv_results": grouped_cv_results,
        "disclaimer": (
            "PRELIMINARY PILOT RESULTS: Evaluated on 53 pilot sessions across 3 experimental tasks. "
            "The 11-session test set provides an indicative proof-of-concept benchmark but produces "
            "inherently uncertain point estimates. Results demonstrate pipeline feasibility, not "
            "generalized production discrimination."
        ),
    }

    # Save JSON metrics summary
    json_path = os.path.join(output_dir, "metrics_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(experiment_results, f, indent=2)

    return experiment_results


if __name__ == "__main__":
    results = run_baseline_experiment()
    print("Baseline experiment completed successfully.")
    print("Test Set Results:")
    for model_name, metrics in results["test_set_results"].items():
        print(f"  {model_name}: F1={metrics['f1']}, Acc={metrics['balanced_accuracy']}, AUC={metrics['roc_auc']}, CM={metrics['confusion_matrix']}")
