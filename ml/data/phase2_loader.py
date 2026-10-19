"""
CrossTrace Phase 2: Development Dataset Loader and Partition Boundary Enforcer.

Enforces:
1. Strict directory boundaries: Development training scripts may only load data from designated development paths.
2. Hard quarantine against held-out human data (H5, H6) and Method 2 bot data.
3. Explicit participant validation ensuring zero partition leakage.
"""

from typing import List, Dict, Any, Tuple, Optional, Set
import os
import pandas as pd


class PartitionIsolationError(RuntimeError):
    """Raised when data from held-out or quarantined partitions is accessed or loaded during development."""
    pass


# Authorized development participant and profile identifiers
AUTHORIZED_DEVELOPMENT_PARTICIPANTS: Set[str] = {
    "H1", "H2", "H3", "H4",
    "p_h01", "p_h02", "p_h03", "p_h04",
    "B1", "B2", "B3", "B4",
    "bot_01", "bot_02", "bot_03", "bot_04",
}

# Strictly quarantined participant identifiers that must never be loaded in development
QUARANTINED_EVALUATION_PARTICIPANTS: Set[str] = {
    "H5", "H6",
    "p_h05", "p_h06",
    "B5", "B6",
    "bot_05", "bot_06",
    "M2_1", "M2_2", "M2_3", "M2_4", "M2_5", "M2_6",
    "M2-1", "M2-2", "M2-3", "M2-4", "M2-5", "M2-6",
}

# Forbidden directory path substrings during development loading
FORBIDDEN_DEVELOPMENT_PATH_SUBSTRINGS: List[str] = [
    "quarantined",
    "held_out",
    "heldout",
    "method2",
    "method_2",
    "unseen",
]


def audit_development_path_boundary(file_path: str) -> None:
    """
    Audits file path string to guarantee it does not point into quarantined evaluation directories.

    Raises:
        PartitionIsolationError: If the path contains forbidden quarantine substrings.
    """
    normalized_path = os.path.normpath(file_path).replace("\\", "/").lower()
    for forbidden in FORBIDDEN_DEVELOPMENT_PATH_SUBSTRINGS:
        if forbidden in normalized_path:
            raise PartitionIsolationError(
                f"Quarantine Breach: Development loader attempted to access forbidden path: '{file_path}' (contains '{forbidden}')"
            )


def audit_development_participants(participants: List[str]) -> None:
    """
    Audits a list of participant IDs to verify no held-out or Method 2 profiles are present.

    Raises:
        PartitionIsolationError: If any quarantined participant ID is present.
    """
    for p in participants:
        p_str = str(p).strip()
        if p_str in QUARANTINED_EVALUATION_PARTICIPANTS or any(q in p_str for q in ["H5", "H6", "M2"]):
            raise PartitionIsolationError(
                f"Partition Leakage: Quarantined evaluation participant '{p_str}' found in development dataset!"
            )


def load_phase2_development_dataset(
    features_path: str,
    metadata_path: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads Phase 2 development window features and metadata with strict partition boundary audits.

    Returns:
        (features_df, metadata_df)
    """
    audit_development_path_boundary(features_path)
    audit_development_path_boundary(metadata_path)

    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Development features file not found: {features_path}")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Development metadata file not found: {metadata_path}")

    # Load data
    if features_path.endswith(".parquet"):
        features_df = pd.read_parquet(features_path)
    else:
        features_df = pd.read_csv(features_path)

    if metadata_path.endswith(".parquet"):
        metadata_df = pd.read_parquet(metadata_path)
    else:
        metadata_df = pd.read_csv(metadata_path)

    # Participant isolation audit
    if "participant_id" in metadata_df.columns:
        audit_development_participants(metadata_df["participant_id"].tolist())

    return features_df, metadata_df
