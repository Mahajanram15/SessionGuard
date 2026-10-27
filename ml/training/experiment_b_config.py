"""
Experiment B: Controlled Kinematic Feature Configuration.

Defines the dedicated kinematic feature selection and explicit shortcut exclusions
for CrossTrace Experiment B. Evaluates whether genuine neuromuscular and motor dynamics
can classify HUMAN vs AUTOMATED behavior without relying on event count or session
duration shortcuts.

Guarantees:
1. Zero modification to Experiment A configuration or frozen baseline artifacts.
2. Complete exclusion of raw event counts (mouse_event_count, click_count, etc.)
   and duration features (session_duration_ms, etc.).
3. All selected features represent scale-free kinematic, geometric, and interval dynamics.
"""

from typing import List, Tuple, Optional
import os
import sys
import pandas as pd

workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from ml.features.extractor import FEATURE_COLUMNS

# ==============================================================================
# 1. Selected Scale-Free Kinematic Features for Experiment B
# ==============================================================================
SELECTED_FEATURES_EXPERIMENT_B_KINEMATIC: List[str] = [
    # Mouse Velocity Moments (3 features)
    "mouse_mean_velocity",
    "mouse_std_velocity",
    "mouse_max_velocity",

    # Mouse Acceleration Moments (3 features)
    "mouse_mean_acceleration",
    "mouse_std_acceleration",
    "mouse_max_acceleration",

    # Mouse Angular & Geometric Trajectory (2 features)
    "mouse_mean_direction_change",
    "mouse_path_straightness",

    # Mouse Pause Dynamics (1 feature)
    "mouse_mean_pause_ms",

    # Keystroke Neuromotor Dynamics: Flight & Dwell Intervals (3 features)
    "mean_flight_ms",
    "std_flight_ms",
    "mean_dwell_ms",
]

# ==============================================================================
# 2. Explicitly Excluded Shortcut Features
# ==============================================================================
EXCLUDED_SHORTCUT_FEATURES_EXPERIMENT_B: List[str] = [
    # A. Raw Event Counts & Integer Tallies (Shortcut Risk)
    "mouse_event_count",
    "total_behavior_event_count",
    "click_count",
    "key_event_count",
    "scroll_event_count",
    "navigation_count",
    "unique_route_count",
    "mouse_direction_change_count",
    "mouse_pause_count",
    "scroll_burst_count",
    "scroll_direction_change_count",
    "repeated_route_count",
    "visibility_event_count",
    "hidden_event_count",
    "focus_event_count",
    "blur_event_count",

    # B. Session Timing & Elapsed Duration Pacing
    "session_duration_ms",
    "mouse_session_duration_ms",
    "active_behavior_duration_ms",
    "total_time_away_ms",
    "mean_time_away_ms",
    "max_time_away_ms",
    "time_away_ratio",
    "events_per_second",
    "interaction_density",
]


def get_selected_features_experiment_b() -> List[str]:
    """Returns a copy of the canonical Experiment B kinematic feature list."""
    return list(SELECTED_FEATURES_EXPERIMENT_B_KINEMATIC)


def get_excluded_shortcut_features_experiment_b() -> List[str]:
    """Returns a copy of the explicitly excluded shortcut features for Experiment B."""
    return list(EXCLUDED_SHORTCUT_FEATURES_EXPERIMENT_B)


def load_experiment_b_dataset(
    features_csv_path: str = "ml/data/features.csv",
    metadata_csv_path: Optional[str] = "ml/data/metadata.csv",
) -> Tuple[pd.DataFrame, pd.Series, Optional[pd.DataFrame]]:
    """
    Loads features and metadata for Experiment B, extracting only the kinematic feature set.
    Ensures complete label and metadata isolation from the feature matrix X.
    """
    if not os.path.exists(features_csv_path):
        raise FileNotFoundError(f"Features file not found: {features_csv_path}")

    df_features = pd.read_csv(features_csv_path)

    if "label" not in df_features.columns:
        raise ValueError("Features file must contain an authoritative 'label' column.")

    selected_cols = get_selected_features_experiment_b()

    # Validate that all selected columns exist in the features CSV
    missing_cols = [col for col in selected_cols if col not in df_features.columns]
    if missing_cols:
        raise KeyError(f"Features CSV is missing required columns for Experiment B: {missing_cols}")

    # Derived feature matrix X
    X = df_features[selected_cols].copy()
    y = df_features["label"].astype(int).copy()

    meta_df = None
    if metadata_csv_path and os.path.exists(metadata_csv_path):
        meta_df = pd.read_csv(metadata_csv_path)
        if len(meta_df) != len(df_features):
            raise ValueError(f"Row mismatch: features ({len(df_features)}) vs metadata ({len(meta_df)})")

    return X, y, meta_df
