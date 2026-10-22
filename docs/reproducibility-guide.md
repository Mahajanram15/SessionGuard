# CrossTrace: Experiment A Reproducibility Guide

**Document Version:** 2.0.0  
**Baseline Dataset:** 53-Session Restored Verified Baseline  
**Classification:** Scientific Reproducibility & Verification Guide  

---

## 1. System Requirements

- **Operating System:** Windows 10/11, macOS, or Linux (Ubuntu 22.04+).
- **Python Environment:** Python 3.11 or higher (tested on Python 3.14).
- **Node.js Environment:** Node 18.x or 20.x, npm 9+.
- **Virtual Environment:** Dedicated Python `.venv` with project dependencies installed via `requirements.txt`.

---

## 2. Pre-Execution Integrity Verification

Before running any evaluation scripts, verify the SHA-256 cryptographic signatures of the six protected baseline files using PowerShell or bash:

### PowerShell:
```powershell
Get-FileHash -Algorithm SHA256 `
  ml/data/features.csv, `
  ml/data/metadata.csv, `
  ml/data/api_request_records.csv, `
  ml/training/train_experiment_a.py, `
  ml/training/feature_config.py, `
  ml/evaluation/baseline_comparison_53_sessions/metrics_summary.json | Format-List Path, Hash
```

### Expected SHA-256 Hashes:
| File Path | Expected SHA-256 Hash |
| :--- | :--- |
| `ml/data/features.csv` | `7164C4432BFC1D0E93BE0E183639FAA67215E5BB5A2EE6F05565BE85B668319C` |
| `ml/data/metadata.csv` | `E98184240A8E6C4FC895CE132FE68EBD279420DF572396A9F5B5460E072EF8B9` |
| `ml/data/api_request_records.csv` | `2EA9028854C681D02929B12D1C894F27DBEDA92D82AAA2B8E077DA5154FF4D46` |
| `ml/training/train_experiment_a.py` | `925F4AB7DAD47DBDF699CE6498611F20723602C35D325CB7F8EE48723FEAFCED` |
| `ml/training/feature_config.py` | `D50ED367ED3EF965F42CA51BB8FC96873D45C76B363B5F000D3CD3C5D8D1E7EC` |
| `ml/evaluation/baseline_comparison_53_sessions/metrics_summary.json` | `369A4DC49BFFFA790ED938F2D943BFC17BB932C59E0F44AC17F4314441AE05A7` |

---

## 3. Step-by-Step Reproduction Instructions

### Step 1: Activate Environment
```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="."
```

### Step 2: Run Automated Feature Configuration Validation
```powershell
python -m pytest tests/test_feature_config.py -v
```
*Expected Result:* 5 passed in <5 seconds. Validates 64 selected and 12 excluded features against 53 sessions.

### Step 3: Run Reproducible Leave-One-Task-Out Evaluation
```powershell
python -m pytest tests/test_train_experiment_a.py -v
```
*Expected Result:* 5 passed in ~10 seconds. Executes LOTO cross-validation, verifies baseline majority metrics, and checks hypothesis criteria.

### Step 4: Run Evaluation Protocol Verification
```powershell
python -m pytest tests/test_evaluation_protocol.py -v
```
*Expected Result:* 12 passed. Validates leakage prevention, LOTO fold generation, LOGO fold isolation, and per-task slicing.

### Step 5: Run Full Verification Suite
```powershell
python -m pytest tests/ -v
```
*Expected Result:* Exactly 133 passed across all 10 test modules in ~3 minutes.

---

## 4. Key Artifacts Required for Scientific Audit

1. **Features Matrix (`ml/data/features.csv`):** 53 rows × 76 canonical features.
2. **Metadata Register (`ml/data/metadata.csv`):** 53 rows mapping session IDs, participant IDs, task IDs, and labels.
3. **Training Engine (`ml/training/train_experiment_a.py`):** Deterministic LOTO cross-validation with seed 42.
4. **Baseline Comparison Artifact (`ml/evaluation/baseline_comparison_53_sessions/metrics_summary.json`):** Frozen metrics summary.
