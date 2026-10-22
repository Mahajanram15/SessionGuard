# CrossTrace: End-to-End System Demonstration Script

**Document Version:** 2.0.0  
**Phase:** Demonstration & Presentation Readiness  
**Target Date:** October 28, 2026  
**Classification:** Live Demonstration & Operator Walkthrough Guide  

---

## 1. Prerequisites & Startup Commands

### Terminal 1: Backend API Gateway
```powershell
# Navigate to workspace root
cd "d:\VIT\TY\Web Tech\CP"

# Activate environment and launch FastAPI service
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="."
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Expected Output:*
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Terminal 2: React Security Dashboard
```powershell
# Navigate to frontend directory
cd "d:\VIT\TY\Web Tech\CP\frontend"

# Launch Vite development server
npm run dev
```
*Expected Output:*
```
  VITE v5.4.21  ready in 450 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

## 2. Demonstration Flow: Step-by-Step Operator Script

### Phase A: System Health & Security Baseline (1 Minute)
1. Open Chrome or Firefox to `http://localhost:5173/`.
2. Inspect the **Top Navigation Bar**:
   - System Health badge indicates `HEALTHY` (connected to `http://localhost:8000/api/health`).
   - SDK Streaming badge indicates `STREAMING: INACTIVE` (amber).
3. Switch to the **Security Overview** tab:
   - View the continuous Behavioral Integrity Score, Decision Distribution, and Session History.
   - Note the three-tier decision boundaries: `ALLOW` ($R < 0.35$), `CHALLENGE` ($0.35 \le R < 0.70$), `BLOCK` ($R \ge 0.70$).

---

### Phase B: Interactive Human Behavioral Capture (2 Minutes)
1. Switch to the **Behavioral Sandbox** tab (`/demo/telemetry`).
2. **Configure Session:**
   - Mode: Select `HUMAN [0]`.
   - Task: Select `TASK_01 (Catalog Browsing)`.
   - Participant ID: Enter `p_01` (or test token `H1`).
3. Click **"Start Labeled Session"**:
   - Header badge transitions to `STREAMING: ACTIVE` (green).
   - Session timer begins incrementing.
   - Session metadata is bound to incoming telemetry.
4. **Exercise Modalities in the Interaction Zones:**
   - **Zone 1 (Mouse Dynamics):** Move the pointer organically across the interaction canvas. Notice the live trajectory and click counter update.
   - **Zone 2 (Keyboard Timing):** Type a search query (e.g., `"ultrawide monitor"`) into the search box.
     - *Demonstrate Privacy Guarantee:* Explain that key hold durations (`dwell_ms`) and flight times are captured, but **zero typed characters or text strings are ingested**.
   - **Zone 3 (Scroll Dynamics):** Scroll the vertical product container. Notice scroll deltas, velocity, and direction reversals update.
   - **Zone 4 (Route Navigation & API Calls):** Click `/demo/catalog` or `/demo/products`.
     - Observe the **Domain API Telemetry Log** below the interaction zone: `[GET] /api/products (200) - 24ms`.
5. Click **"Flush Buffer"** to force immediate micro-batch transmission.
6. Click **"Complete & Label Session"**:
   - SDK flushes remaining events and notifies backend of session completion.
   - Backend freezes session status to `COMPLETED`.
   - Feature engineering extracts windowed kinematics.

---

### Phase C: Synthetic Automated Bot Simulation (1.5 Minutes)
1. On the same page, set Collection Mode toggle to `AUTOMATED [1]`.
2. Select Automation Condition: `AUTOMATED_VARIABLE` (seeded Bézier curves with bounded jitter).
3. Select Task: `TASK_02 (Search Querying)`.
4. Click **"Run Automated Simulation"**:
   - The browser automatically executes a seeded automated routine mimicking scripted navigation.
   - Telemetry batches are labeled with `label = 1` and `automation_condition = "AUTOMATED_VARIABLE"`.
   - Notice the distinct velocity profile (rigid acceleration vs. human organic jitter).

---

### Phase D: Privacy Violation Rejection Demonstration (1 Minute)
*Demonstrate that sensitive payload tampering is hard-rejected at the ingestion boundary.*

Execute this curl / PowerShell request targeting the running backend:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/behavior/events" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{
    "session_id": "test_security_audit",
    "events": [{
      "event_type": "key_meta",
      "client_timestamp": 1729000000000,
      "event_data": {
        "key": "P@ssword123",
        "dwell_ms": 65
      }
    }]
  }'
```
*Expected Result:*
- **HTTP 400 Bad Request**
- Detail: `"Privacy violation: Forbidden field 'key' detected in telemetry event payload."`
- The payload is dropped immediately; **sensitive string values are never echoed in logs or responses**.

---

### Phase E: Safe Development Partition Export (30 Seconds)
1. On the Behavioral Sandbox header, click **"Export CSV Dataset"**.
2. Notice the feedback banner:
   ```
   Exported N development sessions to ml/data/phase2_development/features.csv
   ```
3. *Demonstrate Baseline Protection:* Highlight that exports from this page are strictly contained within `ml/data/phase2_development/` and cannot overwrite the protected Phase 1 baseline files (`ml/data/features.csv`).

---

## 3. Fallback Demonstration Mode (Offline / Standalone)

If the backend database or Python service is temporarily offline during a presentation:
- The React frontend gracefully handles offline states.
- Mock telemetry mode automatically provides synthetic visual streams.
- The terminal test suite (`python -m pytest tests/test_train_experiment_a.py -v`) can be executed standalone in 6 seconds to prove machine learning and hypothesis testing results without network dependencies.
