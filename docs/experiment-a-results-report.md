# CrossTrace: Experiment A Baseline Results & Scientific Evaluation Report

**Document Version:** 2.0.0  
**Baseline Dataset:** 53-Session Restored Verified Baseline (`commit 58c045b`)  
**Evaluation Mode:** Leave-One-Task-Out (LOTO) Cross-Validation  
**Report Status:** Verified Against Live Execution Artifacts  

---

## 1. Executive Summary & Verification Provenance

This report presents the verified benchmark results for **Experiment A**, evaluating the 64-feature behavioral dynamics model against a Majority-Class Baseline Classifier.

All figures in this document are derived from:
- The cryptographically restored 53-session dataset (`ml/data/features.csv`, `ml/data/metadata.csv`).
- Automated Leave-One-Task-Out (LOTO) cross-validation executed via `ml/training/train_experiment_a.py`.
- Baseline comparison records archived in `ml/evaluation/baseline_comparison_53_sessions/metrics_summary.json`.

---

## 2. Dataset Distribution & Task Breakdown

| Task ID | Task Description | Human Sessions ($y=0$) | Automated Sessions ($y=1$) | Total Sessions |
| :--- | :--- | :--- | :--- | :--- |
| **TASK_01** | E-Commerce Catalog Browsing | 7 | 10 (5 Det, 5 Var) | 17 |
| **TASK_02** | Product Search & Filtering | 9 | 10 (5 Det, 5 Var) | 19 |
| **TASK_03** | Cart Review & Checkout | 7 | 10 (5 Det, 5 Var) | 17 |
| **Total** | | **23** | **30** | **53** |

- **Human Participants:** $N=5$ participants (`p_01`: 9, `p_02`: 4, `p_03`: 4, `p_04`: 3, `p_05`: 3).
- **Automated Profiles:** 10 seeded conditions across 3 tasks (15 Deterministic, 15 Variable).

---

## 3. Leave-One-Task-Out (LOTO) Performance Summary

In each fold, two tasks are used for training and feature scaling, and the model is evaluated on the third unobserved task (zero-shot workflow transfer):

| Fold Identifier | Holdout Task | Train / Test Size | Baseline Balanced Acc | XGBoost Balanced Acc | XGBoost Macro $F_1$ | XGBoost Recall | Human FPR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `LOTO_TEST_TASK_03` | TASK_03 (Checkout) | 36 / 17 | 0.5000 | **1.0000** | **1.0000** | 1.0000 | 0.0000 |
| `LOTO_TEST_TASK_02` | TASK_02 (Search) | 34 / 19 | 0.5000 | **0.7778** | **0.8163** | 1.0000 | 0.4444 |
| `LOTO_TEST_TASK_01` | TASK_01 (Catalog) | 36 / 17 | 0.5000 | **1.0000** | **1.0000** | 1.0000 | 0.0000 |
| **Aggregate Mean** | | **53 Total** | **0.5000** | **0.9259** | **0.9388** | **1.0000** | **0.1481** |

---

## 4. Confusion Matrix Analysis

### Fold 1: `LOTO_TEST_TASK_03` (Zero-Shot Transfer to Checkout)
- **Test Samples:** 17 (7 Human, 10 Automated)
- **Predictions:** TP = 10, TN = 7, FP = 0, FN = 0
- **Result:** Perfect zero-shot transfer ($F_1 = 1.000$).

### Fold 2: `LOTO_TEST_TASK_02` (Zero-Shot Transfer to Search Querying)
- **Test Samples:** 19 (9 Human, 10 Automated)
- **Predictions:** TP = 10, TN = 5, FP = 4, FN = 0
- **Result:** Automated bots perfectly captured (Recall = 1.000), but 4 human participants flagged as bots ($\text{FPR}_{\text{human}} = 44.4\%$).
- **Root Cause:** Search interactions involve short, bursty keystrokes and brief pauses, which closely resemble variable bot timing when trained only on browsing and checkout tasks.

### Fold 3: `LOTO_TEST_TASK_01` (Zero-Shot Transfer to Catalog Browsing)
- **Test Samples:** 17 (7 Human, 10 Automated)
- **Predictions:** TP = 10, TN = 7, FP = 0, FN = 0
- **Result:** Perfect zero-shot transfer ($F_1 = 1.000$).

---

## 5. Formal Hypothesis Testing Breakdown

| Hypothesis | Evaluation Criterion | Target Threshold | Observed Value | Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **$H_0$ (Null)** | Baseline Performance Equivalence | Balanced Acc $\le 0.50$ | Balanced Acc = 0.9259 | **REJECTED** |
| **$H_1$ Criterion 1** | Balanced Accuracy Superiority | $\text{Balanced Acc} \ge 0.85$ | 0.9259 | **MET** |
| **$H_1$ Criterion 2** | Macro $F_1$ Superiority | $\text{Macro } F_1 \ge 0.90$ | 0.9388 | **MET** |
| **$H_1$ Criterion 3** | Human False Positive Control | $\text{FPR}_{\text{human}} \le 0.05$ | 0.1481 | **NOT MET** |
| **$H_1$ Overall** | All Three Criteria Satisfied | All 3 Met | Criteria 1 & 2 Met, 3 Failed | **PARTIALLY SUPPORTED** |

**Scientific Interpretation:** While the model substantially outperforms random and majority guessing ($H_0$ rejected), it fails strict clinical false-alarm constraints due to the elevated human false positive rate on TASK_02.

---

## 6. Limitations & Threats to Validity

1. **Small Sample Size ($N=53$):**  
   The pilot evaluation cohort consists of 23 human and 30 automated sessions. Clopper-Pearson 95% confidence intervals on individual metrics are broad ($\pm 10\text{--}18\%$).
2. **Participant Overlap Across Tasks:**  
   In Phase 1, the same 5 participants performed multiple tasks. While LOTO holds out task workflows, subject-specific motor styles may have leaked across folds. Phase 2 remedies this with strict Leave-One-Group-Out (LOGO) partitioning.
3. **Synthetic Bot Diversity:**  
   The automated baseline uses scripted linear and quadratic Bézier movements. Real-world adversaries employ browser humanizers (e.g., Ghost-Cursor) and generative replay attacks.
4. **Client-Side Timing Resolution:**  
   High-resolution timers (`performance.now()`) are subject to browser privacy mitigations (jittered to 0.1ms or 1ms), adding noise to micro-dwell keystroke calculations.
5. **Inability to Generalize:**  
   These pilot metrics reflect a controlled research laboratory interface and cannot be extrapolated as a commercial-grade detection rate on arbitrary websites.
