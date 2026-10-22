# CrossTrace: Experimental Methodology & Evaluation Protocol

**Document Version:** 2.0.0  
**Phase:** Stage 2B Development & Evaluation Design  
**Classification:** Research Methodology Specification  

---

## 1. Research Problem & Evaluation Objectives

CrossTrace investigates whether client-side behavioral dynamics—measured through fine-grained mouse kinematics, keystroke timing metadata, scroll dynamics, and correlated API consumption—can reliably distinguish genuine human users from automated bot agents under controlled web workflows.

### Hypotheses
- **Null Hypothesis ($H_0$):** Behavioral dynamics and cross-layer API telemetry perform no better than a baseline majority-class classifier on zero-shot cross-task transfers ($\text{Balanced Accuracy} \le 0.50$, $\text{Macro } F_1 \le 0.50$).
- **Alternative Hypothesis ($H_1$):** Behavioral dynamics models significantly outperform baseline classifiers across cross-task and cross-condition scenarios, achieving $\text{Balanced Accuracy} \ge 0.85$, $\text{Macro } F_1 \ge 0.90$, with a human false-positive rate ($\text{FPR}_{\text{human}}$) $\le 0.05$.

---

## 2. Dataset Architecture & Partition Isolation

```
CrossTrace Dataset Hierarchy
│
├── Phase 1 Baseline Dataset (ml/data/) [RESTORED BASELINE — IMMUTABLE]
│   ├── Total: 53 Sessions (23 Human, 30 Automated)
│   ├── Task Breakdown: TASK_01 (17), TASK_02 (19), TASK_03 (17)
│   └── Automation Breakdown: Deterministic (15), Variable-Seed (15)
│
└── Phase 2 Planned Architecture (90 Total Planned Sessions)
    ├── Development Partition (40 Sessions) [TARGET FOR STAGE 2B]
    │   ├── Human Cohort: H1–H4 (4 participants × 5 sessions = 20)
    │   └── Bot Method 1: B1–B4 (4 profiles × 5 sessions = 20)
    │
    ├── Held-Out Partition (20 Sessions) [RESERVED FOR STAGE 3 EVALUATION]
    │   ├── Human Cohort: H5–H6 (2 participants × 5 sessions = 10)
    │   └── Bot Method 1: B5–B6 (2 profiles × 5 sessions = 10)
    │
    └── Method 2 Bot Cohort (30 Sessions) [STRICTLY QUARANTINED]
        └── Advanced Playwright Kinematics: M2-1 through M2-6 (30 sessions)
```

### Partition Boundary Controls
1. **Pre-Load Quarantine Gate (`ml/data/phase2_loader.py`):**
   - Automatically intercepts dataset paths before reading files.
   - Forbids any path containing substrings: `"quarantined"`, `"held_out"`, `"heldout"`, `"method2"`, `"method_2"`, `"unseen"`.
   - Rejects participant tokens `H5`, `H6`, `B5`, `B6`, `M2-1` through `M2-6`.
2. **Canonical Export Containment (`backend/app/services/session_service.py`):**
   - Development exports resolve paths using `os.path.realpath` and `os.path.commonpath`.
   - Rejects writes attempting to target `ml/data/` or any path outside `ml/data/phase2_development/`.

---

## 3. Windowing & Feature Extraction Mechanics

### Window Parameters
- **Window Size ($W$):** 30 events.
- **Stride ($S$):** 15 events (50% temporal overlap).

### Structural Rules & Guarantees
1. **Zero Cross-Session Slicing:** Windows are generated strictly within individual sessions. Slicing never spans session boundaries.
2. **Chronological Invariance:** Events are sorted chronologically by `client_timestamp` before slicing.
3. **Incomplete Trailing Policy:** Slices with $< 30$ events are discarded. No zero-padding or fractional interpolation is applied.
4. **Session Eligibility:** Sessions with fewer than 30 total events produce zero windows and are marked ineligible for windowed kinematic evaluation.
5. **Feature Dimensionality:** Each complete window yields exactly 29 numerical kinematic features in canonical order (`ml/training/phase2_config.py`).
6. **Modality Sparsity:** When an interaction modality is absent in a window (e.g., no keypresses during a pure mouse trajectory), statistical moments default to `0.0`. This represents physical behavioral absence, not missing data imputation.

---

## 4. Leakage Prevention & Cross-Validation Protocols

### 4.1 Feature Matrix Isolation
- Target labels (`label`) and collection metadata (`session_id`, `participant_id`, `task_id`, `automation_condition`) are stripped from the feature matrix prior to training.
- The `LeakageAuditor` validates that no metadata column enters the feature tensor $X$.

### 4.2 Grouped Cross-Validation
- **Leave-One-Task-Out (LOTO):** Evaluates generalizability across workflows. In each fold, two tasks form the training set, and the third unobserved task forms the test set.
- **Leave-One-Group-Out (LOGO):** In development validation with human participants, folds are partitioned by `participant_id` to prevent subject-level identity leakage.

### 4.3 Preprocessing Isolation
- Feature scalers (e.g., `StandardScaler`, min-max normalizers) and imputer transformations are fitted **exclusively on the training split** of each cross-validation fold.
- The fitted transformer is then applied to the validation/test fold without refitting (`LeakageAuditor.apply_isolated_preprocessing`).

---

## 5. Decision Threshold Selection & Small-Sample Uncertainty

### 5.1 Threshold Calibration Boundary
- Classification thresholds ($\tau \in [0.0, 1.0]$) must be calibrated strictly on training partitions or development validation splits.
- **Evaluation Rule:** Threshold tuning against held-out human or quarantined Method 2 data is strictly prohibited to prevent overoptimistic evaluation bias.

### 5.2 Session-Level Probability Aggregation
When aggregating window-level probability predictions $\hat{p}_w = P(\text{Automated} \mid W_w)$ to a session-level prediction:
$$\hat{P}_{\text{session}} = \frac{1}{K} \sum_{w=1}^K \hat{p}_w$$
$$\hat{Y}_{\text{session}} = \mathbb{I}(\hat{P}_{\text{session}} \ge \tau)$$

### 5.3 Small-Sample Uncertainty Disclosure
Due to the controlled cohort size in research pilots ($N=53$ baseline, $N=40$ development):
- Point metric estimates (accuracy, precision, recall, $F_1$) must be reported alongside **Clopper-Pearson exact 95% binomial confidence intervals**.
- Metrics must not be generalized to universal web populations without explicit disclosure of sample size limitations.
