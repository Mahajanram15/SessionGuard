"""
Phase 2 Windowed Kinematics Feature Extractor.

Slices session behavioral event streams into fixed-event windows (W=30, S=15)
and extracts the pre-registered 29-feature intensive kinematics configuration.

Guarantees:
1. Reuses BehavioralFeatureExtractor directly without modifying canonical extractor code.
2. Slices exactly W=30 events per window with stride S=15.
3. Incomplete trailing events (<30) are strictly discarded (no zero-padding or fractional scaling).
4. Sessions with fewer than W=30 events yield zero windows (marked ineligible).
5. All 29 features are returned in exact pre-registered order with guaranteed finite float values.
"""

from typing import List, Dict, Any, Tuple, Optional
import math
import numpy as np
import pandas as pd

from ml.features.extractor import BehavioralFeatureExtractor
from ml.training.phase2_config import SELECTED_FEATURES_PHASE2_KINEMATICS


def slice_events_into_windows(
    events: List[Dict[str, Any]],
    window_size: int = 30,
    stride: int = 15,
) -> List[List[Dict[str, Any]]]:
    """
    Slices a list of behavioral events into fixed-size overlapping event windows.

    Rules:
    - Events are sorted chronologically by 'client_timestamp'.
    - If total events < window_size: returns an empty list [].
    - Trailing events that do not complete a full window_size window are discarded.
    - Each returned window contains precisely window_size event dictionaries.
    """
    if not events or len(events) < window_size:
        return []

    # Sort events chronologically
    sorted_events = sorted(
        [ev for ev in events if isinstance(ev, dict) and "event_type" in ev],
        key=lambda x: x.get("client_timestamp", 0)
    )

    total_events = len(sorted_events)
    if total_events < window_size:
        return []

    windows: List[List[Dict[str, Any]]] = []
    start_idx = 0

    while start_idx + window_size <= total_events:
        window_events = sorted_events[start_idx : start_idx + window_size]
        windows.append(window_events)
        start_idx += stride

    return windows


def extract_windowed_kinematics(
    events: List[Dict[str, Any]],
    session_metadata: Optional[Dict[str, Any]] = None,
    window_size: int = 30,
    stride: int = 15,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extracts the 29-feature intensive kinematics matrix from all complete windows of a session.

    Returns:
    - features_df: pd.DataFrame of shape (K, 29) with exactly the pre-registered 29 features.
    - metadata_df: pd.DataFrame of shape (K, M) with window-level audit provenance.
    """
    windows = slice_events_into_windows(events, window_size=window_size, stride=stride)
    meta = session_metadata or {}

    feature_rows: List[Dict[str, float]] = []
    meta_rows: List[Dict[str, Any]] = []

    for w_idx, w_events in enumerate(windows):
        # 1. Reuse existing canonical feature extractor
        raw_76_features = BehavioralFeatureExtractor.extract_features(w_events)

        # 2. Extract strictly the 29 pre-registered kinematic features
        row: Dict[str, float] = {}
        for col in SELECTED_FEATURES_PHASE2_KINEMATICS:
            val = float(raw_76_features.get(col, 0.0))
            if math.isnan(val) or math.isinf(val):
                val = 0.0
            row[col] = round(val, 4)

        feature_rows.append(row)

        # 3. Capture window audit metadata
        first_ts = int(w_events[0].get("client_timestamp", 0))
        last_ts = int(w_events[-1].get("client_timestamp", 0))
        duration_ms = max(0, last_ts - first_ts)

        meta_rows.append({
            "session_id": meta.get("session_id", ""),
            "participant_id": meta.get("participant_id", ""),
            "task_id": meta.get("task_id", ""),
            "label": int(meta.get("label", 0)) if meta.get("label") is not None else None,
            "window_index": w_idx,
            "window_event_count": len(w_events),
            "window_duration_ms": duration_ms,
            "start_timestamp": first_ts,
            "end_timestamp": last_ts,
        })

    if feature_rows:
        features_df = pd.DataFrame(feature_rows)[SELECTED_FEATURES_PHASE2_KINEMATICS]
        metadata_df = pd.DataFrame(meta_rows)
    else:
        features_df = pd.DataFrame(columns=SELECTED_FEATURES_PHASE2_KINEMATICS)
        metadata_df = pd.DataFrame(columns=[
            "session_id", "participant_id", "task_id", "label",
            "window_index", "window_event_count", "window_duration_ms",
            "start_timestamp", "end_timestamp"
        ])

    return features_df, metadata_df
