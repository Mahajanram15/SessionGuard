# CrossTrace Baseline Machine-Learning Experiment Report
## Model Comparison on Behavioral Telemetry (53 Pilot Sessions)

**Date**: 2026-10-19  
**Status**: Completed  
**Nature of Experiment**: Preliminary Baseline Pilot Benchmark  

> [!CAUTION]
> **RESEARCH & GENERALIZATION DISCLAIMER**:
> This experiment establishes an empirical baseline comparison across 53 pilot sessions collected in controlled experimental tasks (TASK_01, TASK_02, TASK_03). The held-out test set ($N = 11$) provides an initial proof-of-concept benchmark with inherently wide confidence bounds. **These preliminary findings do NOT prove generalized human or bot identity in production environments.** Client-side behavioral signals provide probabilistic motor evidence only, which must be cross-correlated with API telemetry and backend session sequences for robust verification.

---

### 1. Dataset & Split Specification

- **Total Sessions**: **53**
  - **HUMAN (`label = 0`)**: 23 sessions across 5 unique participants (`p_01`–`p_05`).
  - **AUTOMATED (`label = 1`)**: 30 sessions across 10 unique bot profiles (`bot_var_s42`–`bot_var_s51` under `AUTOMATED_VARIABLE`).
- **Feature Schema**:
  - Raw Canonical Schema: 76 numeric behavioral features ([ml/data/features.csv](file:///d:/VIT/TY/Web%20Tech/CP/ml/data/features.csv)).
  - Derived Model Matrix: **64 features** selected via [ml/training/feature_config.py](file:///d:/VIT/TY/Web%20Tech/CP/ml/training/feature_config.py).
  - Target: Binary `label` (0 = Human, 1 = Automated). Isolated completely from feature matrix $X$.
  - Metadata: Completely isolated from feature matrix $X$ (`session_id`, `participant_id`, `task_id`, `collection_timestamp`, `event_count` strictly forbidden).
- **Train/Test Partitioning** (Stratified 80/20, `random_state = 42`):
  - **Training Set**: 42 sessions (18 Human, 24 Automated).
  - **Held-Out Test Set**: 11 sessions (5 Human, 6 Automated).
    - Test Session IDs: `sess_e122c4b24bf440159901`, `sess_a0806f1aa1c44cb0ab8a`, `sess_5b9d733943db49808a40`, `sess_fe43f1533ab447798be2`, `sess_3201022922764d1e96c8`, `sess_843a0702b36f49aba2b8`, `sess_0e32178e4d9b4f5d9985`, `sess_b9ac0c2c076f40a790c8`, `sess_fe75babaa66b499c8913`, `sess_c7ba41d9a4d04c65a820`, `sess_fbe5cfa68bc347a2a1ea`.
    - Test Participants: `p_01`, `p_03`, `p_04`, `p_05`, and 7 bot profiles.

---

### 2. Feature Selection & Correlation Audit Findings

Full pairwise correlations were calculated and exported to `ml/evaluation/baseline_comparison_53_sessions/feature_correlation_audit.csv`.

1. **Documented Exclusions (12 Features)**:
   - *Experimental Timing Leakage (3)*: `session_duration_ms`, `mouse_session_duration_ms`, `active_behavior_duration_ms`. (Human reading/deliberation time vs. bot script speed).
   - *Environmental / Tab Focus Leakage (5)*: `hidden_event_count`, `blur_event_count`, `focus_event_count`, `time_away_ratio`, `max_time_away_ms`. (Tab-switching artifacts).
   - *Zero-Variance Constants (3)*: `double_click_rate`, `backspace_rate`, `paste_rate`.
   - *Dispatch Rate Proxy (1)*: `interaction_density` (Fixed timer artifact of simulation harness).
2. **Collinearity Findings**:
   - Extreme collinearity ($|r| \ge 0.95$): **46 pairs** (e.g., `mouse_total_distance_px` $\leftrightarrow$ `mouse_event_count`, velocity statistics $\leftrightarrow$ acceleration statistics).
   - High collinearity ($0.90 \le |r| < 0.95$): **69 pairs**.
   - Following project protocol, these correlated features were **not dropped arbitrarily**, preserving the canonical 64 kinematic features to allow tree ensembles and L2-regularized linear models to manage collinear weighting naturally.

---

### 3. Model Performance Comparison

Three candidate models were evaluated:
1. **Logistic Regression**: Preprocessed with `StandardScaler` (fit strictly on training folds inside an sklearn `Pipeline`), $C=1.0$, L2 penalty.
2. **Random Forest**: 100 trees, `max_depth = 4`, `min_samples_leaf = 2`, `random_state = 42`.
3. **XGBoost**: 50 estimators, `max_depth = 3`, `learning_rate = 0.1`, `eval_metric = "logloss"`, `random_state = 42`.

#### Table 1: Held-Out Test Set Performance ($N = 11$: 5 Human, 6 Automated)

| Model | Balanced Acc | Precision (Bot) | Recall (Bot) | F1-Score | ROC-AUC | Confusion Matrix (TN, FP, FN, TP) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | $\begin{pmatrix} 5 & 0 \\ 0 & 6 \end{pmatrix}$ |
| **Random Forest** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | $\begin{pmatrix} 5 & 0 \\ 0 & 6 \end{pmatrix}$ |
| **XGBoost** | **0.9000** | **0.8571** | **1.0000** | **0.9231** | **0.9000** | $\begin{pmatrix} 4 & 1 \\ 0 & 6 \end{pmatrix}$ |

*Note on XGBoost*: XGBoost yielded 1 false positive (`FP = 1`) on the test set (1 human session classified as bot), achieving 85.7% precision and 90.0% balanced accuracy, whereas Logistic Regression and Random Forest classified all 11 test sessions cleanly.

---

#### Table 2: Stratified 5-Fold Cross-Validation on Training Data ($N = 42$, 5 Folds)

Evaluates variance across folds within the training split without leaking test data:

| Model | Balanced Acc (Mean $\pm$ Std) | Precision (Mean $\pm$ Std) | Recall (Mean $\pm$ Std) | F1-Score (Mean $\pm$ Std) | ROC-AUC (Mean $\pm$ Std) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** |
| **Random Forest** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** |
| **XGBoost** | **$0.9667 \pm 0.0667$** | **$0.9667 \pm 0.0667$** | **$1.0000 \pm 0.0000$** | **$0.9818 \pm 0.0364$** | **$0.9667 \pm 0.0667$** |

---

#### Table 3: Participant/Profile Leakage Assessment (`StratifiedGroupKFold`, 5 Folds)

Evaluates generalization across unseen participants and bot profiles by ensuring zero participant overlap between train and validation folds:

| Model | Balanced Acc (Mean $\pm$ Std) | Precision (Mean $\pm$ Std) | Recall (Mean $\pm$ Std) | F1-Score (Mean $\pm$ Std) | ROC-AUC (Mean $\pm$ Std) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** |
| **Random Forest** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** | **$1.0000 \pm 0.0000$** |
| **XGBoost** | **$0.9667 \pm 0.0667$** | **$0.9333 \pm 0.1333$** | **$1.0000 \pm 0.0000$** | **$0.9600 \pm 0.0800$** | **$0.9667 \pm 0.0667$** |

- **Participant Isolation**: In Fold 1, `p_01` (representing 9 human sessions) was tested against models trained exclusively on `p_02`–`p_05`. Both Logistic Regression and Random Forest correctly classified `p_01` sessions with zero false positives.
- **XGBoost Sensitivity**: XGBoost showed a slight false positive rate on Fold 1 ($TN=6, FP=3$), reflecting sensitivity to small-sample depth splits on participant `p_01`.

---

### 4. Validation Limitations & Statistical Caveats

1. **Test Set Uncertainty ($N = 11$)**:
   With only 5 human and 6 automated test sessions, a single misclassification changes accuracy/precision by $\approx 9\text{–}10\%$. Point estimates must be interpreted with this granularity in mind.
2. **Participant Diversity ($N_{\text{human}} = 5$)**:
   Although sessions are distinct and motor trajectories vary, all 23 human sessions originated from 5 individual participants (`p_01` through `p_05`). While `StratifiedGroupKFold` verified that models generalize across these 5 individuals, scaling to 30+ diverse human participants is recommended for population-level validity.
3. **Synthetic Bot Variety**:
   All 30 automated sessions used `AUTOMATED_VARIABLE` trajectory generation with variable jitter and pauses. More sophisticated adversarial simulation profiles (e.g. human-replay or bezier-spline evasion) should be tested in subsequent research phases.

---

### 5. Integrity Verification of Protected Data Files

The three research CSV files and baseline archives were verified with SHA256 checksums before and after the experiment:

| File Path | SHA256 Hash | Status |
| :--- | :--- | :---: |
| `ml/data/features.csv` | `7164C4432BFC1D0E93BE0E183639FAA67215E5BB5A2EE6F05565BE85B668319C` | **MATCH (Unchanged)** |
| `ml/data/metadata.csv` | `EC86E429B266CED76EDAF52C3712FB9892692B343B93540F7B342B437F066D59` | **MATCH (Unchanged)** |
| `ml/data/api_request_records.csv` | `2EA9028854C681D02929B12D1C894F27DBEDA92D82AAA2B8E077DA5154FF4D46` | **MATCH (Unchanged)** |
| `ml/data/archive_phase4bc_baseline/` | All files intact | **MATCH (Unchanged)** |
