"""
Phase 2 Feature Configuration: Controlled Kinematics-Only Specification.

Defines the pre-registered 29-feature intensive kinematics configuration and the
47-feature exclusion partition for CrossTrace Phase 2.

Guarantees:
1. Zero modification to Experiment A configuration (SELECTED_FEATURES_EXPERIMENT_A).
2. The 29 selected and 47 excluded features form a strict, disjoint, complete partition
   of the canonical 76-feature schema in ml.features.extractor.
3. Explicit sparse modality semantics: A 0.0 value in an unexercised modality represents
   the absence of that behavior in the window (e.g., no clicks in a 30-event mouse window),
   not an imputed measurement.
"""

from typing import List, Set, Dict, Any, Tuple
import os
import pandas as pd
from ml.features.extractor import FEATURE_COLUMNS

# ==============================================================================
# 1. Pre-Registered 29 Selected Kinematic Features (Ordered List)
# ==============================================================================
SELECTED_FEATURES_PHASE2_KINEMATICS: List[str] = [
    # Mouse Velocity & Acceleration Moments (6)
    "mouse_mean_velocity",
    "mouse_std_velocity",
    "mouse_max_velocity",
    "mouse_mean_acceleration",
    "mouse_std_acceleration",
    "mouse_max_acceleration",

    # Mouse Angular & Path Geometry (3)
    "mouse_direction_change_rate",
    "mouse_mean_direction_change",
    "mouse_path_straightness",

    # Click Dynamics: Local Intervals & Target Ratios (6)
    "mean_click_interval_ms",
    "std_click_interval_ms",
    "button_click_ratio",
    "link_click_ratio",
    "input_click_ratio",
    "other_click_ratio",

    # Keystroke Neuromotor Dynamics: Dwell, Flight & Inter-Key Moments (8)
    "mean_dwell_ms",
    "std_dwell_ms",
    "min_dwell_ms",
    "mean_flight_ms",
    "std_flight_ms",
    "min_flight_ms",
    "mean_inter_key_interval_ms",
    "std_inter_key_interval_ms",

    # Scroll Velocity, Directional Ratios & Intra-Burst Interval (6)
    "mean_scroll_velocity",
    "std_scroll_velocity",
    "max_scroll_velocity",
    "upward_scroll_ratio",
    "downward_scroll_ratio",
    "mean_scroll_interval_ms",
]

# ==============================================================================
# 2. Complete 47 Excluded Features (Disjoint Partition)
# ==============================================================================
EXCLUDED_FEATURES_PHASE2_KINEMATICS: List[str] = [
    # A. Session Timing & Elapsed Pacing (4)
    "session_duration_ms",
    "mouse_session_duration_ms",
    "active_behavior_duration_ms",
    "events_per_second",

    # B. Window Focus & Defocus Artifacts (8)
    "visibility_event_count",
    "hidden_event_count",
    "focus_event_count",
    "blur_event_count",
    "total_time_away_ms",
    "mean_time_away_ms",
    "max_time_away_ms",
    "time_away_ratio",

    # C. Zero-Variance Study Constants (3)
    "double_click_rate",
    "backspace_rate",
    "paste_rate",

    # D. Fixed Dispatch Proxy (1)
    "interaction_density",

    # E. Extensive Event Counts & Integer Tallies (10)
    "total_behavior_event_count",
    "mouse_event_count",
    "click_count",
    "key_event_count",
    "scroll_event_count",
    "navigation_count",
    "unique_route_count",
    "repeated_route_count",
    "scroll_burst_count",
    "scroll_direction_change_count",

    # F. Macro Distances & Tally Extremes (3)
    "mouse_total_distance_px",
    "total_scroll_distance",
    "mouse_direction_change_count",

    # G. Whole-Session Pacing Rates & Macro Ratios (7)
    "click_rate",
    "navigation_rate",
    "typing_speed",
    "mouse_to_click_ratio",
    "click_to_navigation_ratio",
    "navigation_to_session_ratio",
    "route_repetition_ratio",

    # H. Simulator Pause Absence Artifacts (3)
    "mouse_pause_count",
    "mouse_mean_pause_ms",
    "mouse_max_pause_ms",

    # I. Page-Level Navigation Dwells (4)
    "mean_page_dwell_ms",
    "std_page_dwell_ms",
    "min_page_dwell_ms",
    "max_page_dwell_ms",

    # J. Interval Extrema Leakage (4)
    "min_click_interval_ms",
    "max_click_interval_ms",
    "max_dwell_ms",
    "max_flight_ms",
]


def get_phase2_kinematic_features() -> List[str]:
    """Returns an immutable copy of the 29 pre-registered Phase 2 kinematic feature names."""
    return list(SELECTED_FEATURES_PHASE2_KINEMATICS)


def get_phase2_excluded_features() -> List[str]:
    """Returns an immutable copy of the 47 Phase 2 excluded feature names."""
    return list(EXCLUDED_FEATURES_PHASE2_KINEMATICS)


def validate_phase2_feature_partition() -> Dict[str, Any]:
    """
    Validates that SELECTED and EXCLUDED features form a strict, disjoint, complete
    partition of the canonical 76-feature schema.
    """
    selected_set = set(SELECTED_FEATURES_PHASE2_KINEMATICS)
    excluded_set = set(EXCLUDED_FEATURES_PHASE2_KINEMATICS)
    canonical_set = set(FEATURE_COLUMNS)

    overlap = selected_set.intersection(excluded_set)
    missing = canonical_set.difference(selected_set.union(excluded_set))
    extra = selected_set.union(excluded_set).difference(canonical_set)

    is_valid = (
        len(SELECTED_FEATURES_PHASE2_KINEMATICS) == 29
        and len(EXCLUDED_FEATURES_PHASE2_KINEMATICS) == 47
        and len(overlap) == 0
        and len(missing) == 0
        and len(extra) == 0
        and len(canonical_set) == 76
    )

    return {
        "is_valid": is_valid,
        "selected_count": len(SELECTED_FEATURES_PHASE2_KINEMATICS),
        "excluded_count": len(EXCLUDED_FEATURES_PHASE2_KINEMATICS),
        "canonical_count": len(canonical_set),
        "overlap_count": len(overlap),
        "overlap_features": sorted(list(overlap)),
        "missing_features": sorted(list(missing)),
        "extra_features": sorted(list(extra)),
    }
