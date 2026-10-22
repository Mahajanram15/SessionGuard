# CrossTrace: Privacy, Data Lifecycle, and Storage Governance

**Document Version:** 2.0.0  
**Phase:** Stage 2B Pre-Collection / Engineering Readiness  
**Classification:** Data Privacy, Lifecycle & Compliance Specification  

---

## 1. Core Privacy Architecture & Zero-Knowledge Input Principles

CrossTrace is engineered around a strict **privacy-preserving behavioral capture model**:
1. **Zero Text Capture:** Keystroke dynamics capture temporal rhythms ($t_{\text{hold}}$, $t_{\text{flight}}$, $\Delta t_{\text{inter\_key}}$) and binary action flags (`is_backspace`, `is_paste`). **Zero key characters, typed words, or key codes are captured or stored.**
2. **Zero Form Data Capture:** Form input values, query parameter values, and JSON payload values are stripped at the client layer and validated server-side. Only structural field names (`param_keys`, `payload_keys`) are retained.
3. **Password Shield:** Any interaction event targeting a field with `type="password"` or `target_type="password"` is immediately rejected by the server validator and discarded.
4. **Recursive Ingestion Validation:** The ingestion boundary (`ml/data/privacy_validator.py::validate_event_privacy`) executes a recursive tree traversal over incoming JSON payloads, rejecting any forbidden key (`key`, `code`, `value`, `text`, `inputValue`, `keyCode`, `which`, `char`) prior to buffering, caching, or database persistence.

---

## 2. Pseudonymity vs. Anonymity

> [!IMPORTANT]
> **CrossTrace Research Data is PSEUDONYMOUS, NOT ANONYMOUS.**

- **Why It Is Pseudonymous:**
  - Direct identifiers (names, emails, physical addresses) are never collected.
  - Participants are referenced by research tokens (`H1`–`H4`, `p_01`–`p_05`).
  - IP addresses are immediately hashed via SHA-256 (`ip_hash`).
- **Why It Is NOT Fully Anonymous:**
  - High-resolution cursor kinematics, typing rhythms, viewport resolution (`1920x1080`), browser User-Agent strings, and timezone offsets constitute high-entropy behavioral biometric fingerprints.
  - If combined with auxiliary external datasets, behavioral profiles could theoretically be linked to an individual.
  - Accordingly, CrossTrace treats all telemetry as pseudonymous research data subject to rigorous access control and data minimization.

---

## 3. Storage Layer Inventory & Deletion Scope

CrossTrace stores session information across five distinct storage layers:

| Storage Layer | Location / Artifact | Data Content | Retention & Purge Procedure |
| :--- | :--- | :--- | :--- |
| **1. Development Files** | `ml/data/phase2_development/` | Raw JSON session files, event arrays, exported features. | Filesystem deletion (`rm -rf` / purge script) upon project conclusion. |
| **2. Session State Cache** | `.active_sessions_cache.json` | In-memory/disk session cache tracking active session metadata and `ip_hash`. | Removed during dataset purge; cleared on session flush. |
| **3. Relational Database** | PostgreSQL Tables (`sessions`, `behavior_events`, `api_requests`, `behavior_features`, `risk_scores`) | Persistent session records, raw event sequences, API latency records, window features. | `DELETE FROM sessions WHERE session_id IN (...)` with cascading foreign keys to all dependent tables. |
| **4. Server & Proxy Logs** | • Uvicorn runtime `stdout`/`stderr`<br>• Reverse proxy access logs (e.g., Nginx, Traefik) | Raw client IP addresses, HTTP request timestamps, route paths, HTTP status codes. | Log rotation (`logrotate`), log truncation, and clearing container stdout streams. |
| **5. Derived Feature Files** | • Temporary CSV extracts in `ml/data/phase2_development/`<br>• Scratch scripts in `.gemini/.../scratch/` | Windowed feature matrices, sliding-window summaries, diagnostic evaluations. | Purged alongside development dataset files. |

---

## 4. Operational Governance Status (Unresolved Blockers)

In accordance with strict safety rules, the project status remains **NO-GO for human participant recruitment and data collection** until the following three operational items are formally confirmed:

| Blocker ID | Governance Item | Current Status | Required Action / Decision Needed |
| :--- | :--- | :--- | :--- |
| **Blocker A** | **Institutional Ethics / IRB Determination** | **OPEN** | Obtain written confirmation from the faculty supervisor or institutional review board determining whether human telemetry collection qualifies for an academic coursework exemption or requires formal IRB approval. |
| **Blocker B** | **Data Retention & Scheduled Purge Date** | **OPEN** | Formally establish: (1) exact calendar deletion cutoff date, (2) formal milestone trigger (e.g., 14 days post-course evaluation), and (3) designated operator responsible for purging files, cache, DB, and logs. |
| **Blocker C** | **Official Withdrawal Contact** | **OPEN** | Confirm whether `mahajanram1506@gmail.com` is formally designated as the official withdrawal mailbox, or provide an official university institutional email address with a defined response SLA. |

---

## 5. Participant Withdrawal Protocol

### 5.1 Token Verification Procedure (Pre-Freeze)
1. **Intake Token Issuance:** Each participant receives a private withdrawal receipt containing their assigned research token (`H1`–`H4`) and a random verification code (e.g., `H1-VERIFY-9241`).
2. **Withdrawal Request:** The participant emails the designated project contact stating their withdrawal request and providing their verification code.
3. **Record Excised:** Within 5 business days, all sessions associated with that token are permanently deleted from `ml/data/phase2_development/`, `.active_sessions_cache.json`, and database tables.

### 5.2 Scientific Limitations Post-Freeze
- Once a dataset partition is frozen, partitioned into train/test folds, cryptographically signed, and used to train machine learning models:
  - Raw session files can still be deleted from active disks.
  - **Limitation:** In machine learning benchmarks, individual data points are transformed into aggregate population statistics (means, standard deviations, distribution histograms) and model weight vectors. Once frozen into published baselines, individual mathematical contributions cannot be selectively excised without retraining all models and recalculating all experimental benchmarks.
