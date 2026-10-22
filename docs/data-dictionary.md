# CrossTrace: Behavioral Integrity Verification System — Data Dictionary

**Document Version:** 2.0.0  
**Phase:** Stage 2B Pre-Collection / Baseline Artifact Specification  
**Classification:** Technical Data Dictionary & Schema Specification  

---

## 1. Overview & Data Flow

CrossTrace ingests, processes, and stores data across three core pipeline stages:
1. **Raw Client Interaction Events:** Ephemeral, high-frequency telemetry ingested via `POST /api/behavior/events`.
2. **Application Domain API Records:** Structural and latency telemetry capturing backend API interactions via `POST /api/api-requests`.
3. **Derived Feature Representations:**
   - **Experiment A (Canonical Baseline):** 64 session-level statistical features derived from the 76-feature canonical feature extractor (`ml/features/extractor.py`).
   - **Phase 2 (Windowed Kinematics):** 29 intensive motor kinematics features extracted over fixed-size event windows ($W=30, S=15$) (`ml/features/windowed_extractor.py`).

---

## 2. Ingestion Event Schemas & Privacy Boundaries

### 2.1 Allowed Ingestion Fields (Whitelist)

```
Event Payload Schema (POST /api/behavior/events)
├── session_id: string (UUID / sess_<hex>)
└── events: Array<EventObject>
    ├── event_type: "mouse_move" | "mouse_click" | "scroll" | "key_meta" | "navigation" | "visibility"
    ├── client_timestamp: integer (Epoch ms from browser performance.now / Date.now)
    └── event_data: Object (Strictly whitelisted payload per event_type)
```

| Event Type | Permitted `event_data` Fields | Description & Units |
| :--- | :--- | :--- |
| `mouse_move` | `x`, `y`<br>`distance_px`<br>`time_delta_ms`<br>`velocity_px_s`<br>`acceleration_px_s2`<br>`direction_change_deg` | Viewport $(x, y)$ coordinates in pixels.<br>Euclidean displacement since preceding sample.<br>Time elapsed since preceding sample.<br>Instantaneous speed ($px/s$).<br>Instantaneous acceleration ($px/s^2$).<br>Angular deflection along path ($0^\circ$ to $180^\circ$). |
| `mouse_click` | `x`, `y`<br>`button`<br>`click_type`<br>`time_since_last_click_ms`<br>`target_type` | Viewport click coordinates.<br>Button index: `0` (Left), `1` (Middle), `2` (Right).<br>`"single"` or `"double"`.<br>Inter-click latency in milliseconds.<br>Semantic target category: `"button"`, `"link"`, `"input"`, `"select"`, `"canvas"`, `"other"`. |
| `scroll` | `scroll_x`, `scroll_y`<br>`delta_x`, `delta_y`<br>`velocity_px_s`<br>`direction`<br>`time_since_last_scroll_ms` | Absolute page scroll offset in pixels.<br>Scroll displacement delta in pixels.<br>Scroll velocity ($px/s$).<br>Direction vector: `"up"`, `"down"`, `"left"`, `"right"`, `"none"`.<br>Inter-scroll burst interval in milliseconds. |
| `key_meta` | `dwell_ms` (or `hold_time_ms`)<br>`flight_ms` (or `inter_key_latency_ms`)<br>`inter_key_interval_ms`<br>`is_backspace`<br>`is_paste` | Key down-to-up hold duration in milliseconds.<br>Latency between keyup of key $i-1$ and keydown of key $i$.<br>Latency between successive keydown events ($dwell + flight$).<br>Boolean flag indicating editing/backspace action.<br>Boolean flag indicating clipboard paste shortcut. |
| `navigation` | `path`<br>`referrer`<br>`dwell_time_ms` | Application route pathname (e.g., `"/catalog"`).<br>Sanitized internal referring route.<br>Time spent on the previous view in milliseconds. |
| `visibility` | `state`<br>`duration_away_ms` | Tab visibility state: `"visible"`, `"hidden"`, `"focus"`, `"blur"`.<br>Milliseconds spent away from active application tab. |

### 2.2 Prohibited Raw Input Fields (Strict Blacklist)

The server-side privacy validator (`ml/data/privacy_validator.py::validate_event_privacy`) executes a recursive inspection on all incoming event batches. **Any payload containing the following keys or values is immediately rejected with HTTP 400 Bad Request before in-memory buffering or storage:**

| Prohibited Key / Value | Category | Enforcement Action |
| :--- | :--- | :--- |
| `key`, `code`, `keyCode`, `which`, `char` | Keystroke Character Content | Immediate rejection (`PrivacyViolationError`); payload dropped. |
| `value`, `text`, `inputValue` | Form Field Content | Immediate rejection (`PrivacyViolationError`); payload dropped. |
| `target_type == "password"` | Password Element Interaction | Immediate rejection (`PrivacyViolationError`); payload dropped. |
| Direct PII (names, emails, credit cards) | Personal Direct Identifiers | Never requested in UI forms; zero ingestion pathways. |

---

## 3. Domain API Telemetry Schema (`api_request_records.csv`)

Collected via `POST /api/api-requests` and exported alongside behavioral features:

| Field Name | Type | Storage Format | Privacy & Integrity Guarantees |
| :--- | :--- | :--- | :--- |
| `session_id` | string | `VARCHAR(64)` | Binds API call to active browser session token. |
| `task_id` | string | `VARCHAR(32)` | Associated research task (`TASK_01`, `TASK_02`, `TASK_03`). |
| `sequence_number` | integer | `INTEGER` | Monotonically increasing counter ($1, 2, 3\dots$) per session. |
| `http_method` | string | `VARCHAR(10)` | Standard HTTP verb (`GET`, `POST`). |
| `endpoint` | string | `VARCHAR(255)` | Application route (e.g., `"/api/products"`). |
| `status_code` | integer | `SMALLINT` | HTTP response code (e.g., `200`, `404`, `422`). |
| `response_time_ms`| float | `DOUBLE PRECISION` | Client-measured round-trip network latency in milliseconds. |
| `request_size_bytes` | integer | `INTEGER` | Request body length in bytes. |
| `response_size_bytes`| integer | `INTEGER` | Response payload length in bytes. |
| `param_keys` | JSON string | `JSONB` / stringified list | Parameter names present in query string. **Values are stripped.** |
| `payload_keys` | JSON string | `JSONB` / stringified list | Field names present in JSON payload. **Values are stripped.** |
| `headers_fingerprint`| string | `VARCHAR(64)` | SHA-256 hash of normalized HTTP headers. |
| `payload_structure_hash` | string | `VARCHAR(64)` | SHA-256 hash of JSON structure keys. |
| `client_timestamp`| integer | `BIGINT` | Client-side epoch milliseconds when request was dispatched. |
| `server_timestamp`| integer | `BIGINT` | Server-side epoch milliseconds when telemetry was ingested. |

---

## 4. Machine Learning Feature Sets

### 4.1 Canonical Schema (76 Features)
The base feature extractor (`ml/features/extractor.py`) computes 76 numerical features across 7 categories:
- **Group A (Mouse Movements):** 16 features (`mouse_event_count`, `mouse_mean_velocity`, `mouse_std_velocity`, `mouse_path_straightness`, `mouse_mean_acceleration`, etc.).
- **Group B (Clicks):** 11 features (`click_count`, `click_rate`, `mean_click_interval_ms`, `button_click_ratio`, etc.).
- **Group C (Keystrokes):** 14 features (`key_event_count`, `mean_dwell_ms`, `mean_flight_ms`, `mean_inter_key_interval_ms`, `typing_speed`, etc.).
- **Group D (Scrolling):** 10 features (`scroll_event_count`, `mean_scroll_velocity`, `upward_scroll_ratio`, etc.).
- **Group E (Navigation):** 9 features (`navigation_count`, `unique_route_count`, `route_transition_rate`, etc.).
- **Group F (Visibility):** 8 features (`visibility_event_count`, `total_time_away_ms`, `time_away_ratio`, etc.).
- **Group G (Cross-Behavior):** 8 features (`total_behavior_event_count`, `session_duration_ms`, `events_per_second`, `interaction_density`, etc.).

### 4.2 Experiment A: 64-Feature Baseline Configuration
- Defined in `ml/training/feature_config.py`.
- **Selected Features (64):** Retains motor dynamics, interval statistics, ratios, and controlled task-dependent signals.
- **Excluded Features (12):** Excludes unmonitored task artifacts, raw route identifiers, and redundant linear combinations.
- **Dimensionality:** Exactly 64 numeric floats per session.

### 4.3 Phase 2: 29-Feature Intensive Kinematics Configuration
- Defined in `ml/training/phase2_config.py`.
- **Selected Features (29):** Pure motor and timing kinematics (6 mouse velocity/acceleration moments, 3 mouse trajectory geometry metrics, 6 click dynamic ratios, 8 keystroke dwell/flight dynamics, 6 scroll dynamic moments).
- **Excluded Features (47):** All session durations, event counts, tab focus artifacts, route identifiers, and study constants.
- **Modality Sparsity Semantic:** Unexercised modalities produce explicit `0.0` values representing behavioral absence, not missing data imputation.

---

## 5. Export File Formats and Partitions

| Partition Target | Export Path | Contained Files | Security Guard |
| :--- | :--- | :--- | :--- |
| **Protected Phase 1 Baseline** | `ml/data/` | • `features.csv` (53 sessions × 76 features)<br>• `metadata.csv` (53 sessions × 8 metadata fields)<br>• `api_request_records.csv` | **PROTECTED BASELINE (Immutable).** Re-exports strictly forbidden. |
| **Phase 2 Development** | `ml/data/phase2_development/` | • `features.csv`<br>• `metadata.csv`<br>• `api_request_records.csv` | **SANDBOXED.** Path traversal and baseline overwrites prevented via canonical path validation. |
