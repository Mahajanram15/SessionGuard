# LearnSphere & CrossTrace: End-to-End Demonstration Walkthrough & Operator Guide

**Document Version:** 3.0.0 (Stage 8)  
**System:** CrossTrace Behavioral Integrity Verification System  
**Demonstration Application:** LearnSphere E-Learning Platform  
**Target Milestone:** Live Demonstration Readiness & Evaluator Presentation  

---

## 1. Startup Guide & Environmental Prerequisites

### Prerequisites
- **Python:** 3.10+ with workspace virtual environment installed.
- **Node.js:** v18+ with `npm` installed.
- **Git:** Clean working tree on branch.
- **Frozen ML Model:** `ml/models/experiment_a_xgboost.joblib` (SHA-256: `74ff7cb594ffa953ed51e433e5f059a9fbb19dd8beb650c422d1acec88b70fb0`).

### Terminal 1: Backend API Gateway
From the repository root (`d:\VIT\TY\Web Tech\CP`):
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
- Health Check URL: `http://127.0.0.1:8000/health`
- Model Status URL: `http://127.0.0.1:8000/api/model/status`
- Expected Health JSON:
  ```json
  {
    "status": "healthy",
    "service": "crosstrace-backend",
    "components": {
      "api": "ready",
      "session_manager": "ready",
      "ml_inference": "ready"
    }
  }
  ```

### Terminal 2: LearnSphere & Analyst Frontend
From the `frontend/` directory (`d:\VIT\TY\Web Tech\CP\frontend`):
```powershell
npm run dev -- --host 127.0.0.1 --port 5173
```
- LearnSphere Student Landing Page: `http://127.0.0.1:5173/` (Default tab)
- Analyst Dashboard ("System Matrix"): `http://127.0.0.1:5173/` (Click **System Matrix** tab)
- Telemetry Sandbox: `http://127.0.0.1:5173/` (Click **Telemetry Sandbox** tab)

### Clean Termination
- Press `Ctrl + C` in Terminal 1 (Uvicorn server) and Terminal 2 (Vite dev server) to gracefully shut down both services.

---

## 2. Step-by-Step Operator Demonstration Walkthrough

This 10-step checklist guides the operator through a complete, reproducible demonstration:

| Step | Action | User Interface / Route | Observed System Behavior |
| :--- | :--- | :--- | :--- |
| **1** | **Open LearnSphere** | `http://127.0.0.1:5173/` | The LearnSphere student dashboard renders with greeting, stats banner, search input, and course grid. |
| **2** | **Catalog Browsing & Search** | LearnSphere Search Input | Type `"Systems"` or `"Full-Stack"`. The catalog filters reactively to matching courses via `GET /api/courses/search?q=...`. |
| **3** | **Open Course & Curriculum** | Click "Distributed Systems Design" | Modal opens with syllabus, learning outcomes, and module list. Click **"Start Course"** to load the lesson player. |
| **4** | **Lesson Player & Quiz** | Lesson Player & Quiz Tab | Navigate to Lesson 1: "Microservices Architecture Fundamentals". Select an answer on the knowledge-check quiz. Emitted telemetry records interaction timestamps and selection indices; **zero correct answers or quiz keys are transmitted**. |
| **5** | **Run Operator Manual Session** | Telemetry Sandbox or in-app | Run manual scenario (`TASK_LEARN_MANUAL`). Move mouse organically and click. The SDK batches kinematic telemetry via `POST /api/behavior/events`. Finalize session (`POST /api/session/end`). |
| **6** | **Run Synthetic Bot Session** | Telemetry Sandbox / Simulation | Trigger the deterministic synthetic bot simulation (`TASK_LEARN_AUTOMATION`). Telemetry batches are captured and finalized via the same pipeline. |
| **7** | **Open Analyst Dashboard** | Top Nav: "System Matrix" | Aggregated telemetry, active sessions, risk distributions, and recent flagged sessions are loaded via `GET /api/dashboard/stats`. |
| **8** | **Inspect Both Sessions** | Click session IDs in table | View the Session Inspection modal. Note that both sessions have extracted 64-feature vectors, genuine ML prediction status (`available`), and TreeSHAP feature attributions. |
| **9** | **Explain Identical Model Output** | Session Inspection Modal | Point out that both sessions received $P(\text{Automated}) = 0.9659$ and Risk = $0.387$ (`CHALLENGE`). Explain that the frozen model partitions exclusively on `mouse_event_count < 72`, and both short demonstration sessions had $< 72$ mouse events (15 vs 16). |
| **10** | **Review Model Limitation Notice** | Dashboard Limitation Banner | Direct evaluators to the prominent amber banner stating that the frozen Experiment A model operates on a single active split feature for short sessions, demonstrating transparency and research integrity. |

---

## 3. Demo Data Management & Cache Reset

- **Storage Location:** Active sessions, kinematic events, and domain API requests are stored in memory and synchronized to `ml/data/.active_sessions_cache.json`.
- **Protected Dataset Protection:** Baseline datasets in `data/baseline/` and `data/training/` are strictly isolated and are never overwritten by demonstration sessions.
- **Distinguishing Sessions:** Each session receives a unique timestamped ID `sess_<20-hex>` along with its task ID (`TASK_LEARN_MANUAL` vs `TASK_LEARN_AUTOMATION`).
- **Safe Reset Procedure:**
  1. Terminate the backend server (`Ctrl + C`).
  2. Remove or rename the active sessions cache:
     ```powershell
     Remove-Item "ml/data/.active_sessions_cache.json" -ErrorAction SilentlyContinue
     ```
  3. Restart the backend server. The session matrix will start with a fresh registry.

---

## 4. Presentation Notes & Evaluator Q&A

### 60-Second Elevator Pitch
> *"CrossTrace is a behavioral integrity verification system that monitors human and automated interactions in modern web applications without compromising user privacy. Operating behind our LearnSphere e-learning platform, CrossTrace captures client-side kinematic dynamics—such as mouse velocity, trajectory curvature, and inter-keystroke intervals—while strictly omitting raw keystroke contents or quiz answers. Telemetry is streamed to a FastAPI backend where a 64-dimensional feature extractor feeds a frozen XGBoost model and TreeSHAP explainer, allowing security analysts to inspect real-time risk scores and feature attributions in the System Matrix dashboard."*

### 3–5 Minute Technical Demonstration Script
1. **Introduction & System Health (0:00 – 0:45):**  
   Show the running LearnSphere platform and top navigation. Point out the real-time health indicator connected to FastAPI (`/health`) and the background SDK streaming status.
2. **Privacy-Preserving Telemetry (0:45 – 1:45):**  
   Browse courses, filter by search term, and open the lesson player. Answer a quiz question. Open browser developer tools or the terminal log to show that telemetry payloads contain only timing differentials, coordinate vectors, and parameter keys (`param_keys`), with zero sensitive strings or quiz answer keys.
3. **Dual-Session Evaluation (1:45 – 3:15):**  
   Switch to the Telemetry Sandbox. Run the operator-triggered manual scenario, followed by the synthetic bot simulation. Explain that both sessions stream to the exact same ingestion and feature-extraction pipeline.
4. **Analyst Inspection & Limitation Disclosure (3:15 – 4:30):**  
   Open the System Matrix dashboard. Open each session modal to display the 64-feature vector, the risk score (0.387 `CHALLENGE`), and the TreeSHAP attribution. Explain honestly why both sessions received $P(\text{Automated}) = 0.9659$: the frozen Experiment A XGBoost model decision tree splits exclusively on `mouse_event_count < 72`. Highlight the in-dashboard limitation notice as proof of research transparency.

### Evaluator Q&A Preparation
1. **Q: Why do the manual and synthetic demonstration sessions receive the exact same prediction?**  
   **A:** *"Our diagnostic audit in Stage 5 revealed that across all 35 decision splits in the frozen Experiment A XGBoost model, the trees branch exclusively on `mouse_event_count < 72`. Because our demonstration scenarios are short interactive tasks with 15 and 16 mouse events respectively, both fall into the identical decision leaf. In accordance with strict experimental integrity, we did not hardcode predictions or alter model weights to force a cosmetic demonstration result; instead, we disclose this limitation clearly in the UI."*
2. **Q: How does CrossTrace ensure student privacy during learning activities?**  
   **A:** *"Privacy is enforced at both the client SDK and backend validation boundaries. The SDK captures dwell and flight times without recording characters or strings. In LearnSphere quizzes, correct answers and explanation texts are never ingested into telemetry. Furthermore, the backend privacy validator rejects any payload containing forbidden content keys with an HTTP 400 error."*
3. **Q: Is this system ready for production deployment in enterprise LMS environments?**  
   **A:** *"No. CrossTrace is an academic research prototype evaluated as READY WITH LIMITATIONS. It was developed on a 53-session experimental dataset and relies on a frozen model that exhibits severe feature dominance. It provides an end-to-end architectural demonstration of privacy-preserving behavioral telemetry and SHAP explainability, but requires retraining on broader, multi-modal human datasets before real-world security deployment."*
