# CrossTrace Phase 2 — Participant Information & Informed Consent Brief

**Study Title:** CrossTrace: Controlled Client-Side Behavioral Dynamics & Telemetry Research  
**Protocol Phase:** Phase 2 Stage 2B Development Data Collection  
**Document Version:** 2.1 (Reconciled with Verified Technical Telemetry Inventory)  
**Status:** Pre-Collection Review Document — Not authorized for participant recruitment until all institutional decisions are resolved.

---

## 1. Study Purpose & Research Scope

You are invited to participate in a research study evaluating client-side human-computer interaction dynamics on web applications. The objective of this research is to investigate whether fine-grained behavioral kinematics (such as cursor trajectory curvature, scrolling rhythm, and keystroke timing dynamics) can reliably distinguish genuine human users from automated bot scripts across typical e-commerce workflows.

Participation involves completing five short task sessions (approximately 2–3 minutes each) on a local research e-commerce interface:
- **TASK_01 (Catalog Browsing):** Browsing product listings, inspecting specifications, and filtering categories.
- **TASK_02 (Search Querying):** Performing product searches, filtering results, and navigating listings.
- **TASK_03 (Cart & Checkout):** Adding items to the shopping cart, reviewing the cart summary, and stepping through the checkout verification workflow.

---

## 2. Complete Inventory of Collected & Processed Telemetry

The CrossTrace client software (`@behavioral-integrity/sdk`) and backend services (`/api`) record and process the following specific data elements:

### A. Pointer & Cursor Kinematics
- **Coordinates:** Horizontal $(x)$ and vertical $(y)$ cursor positions in pixels relative to the browser viewport.
- **Motion Dynamics:** Euclidean displacement (`distance_px`), sampling interval (`time_delta_ms`), instantaneous velocity (`velocity_px_s`), acceleration (`acceleration_px_s2`), motion angle (`angle_degrees`), and angular path deviation (`direction_change_deg`).
- **Click Dynamics:** Click coordinates $(x, y)$, mouse button index ($0 = \text{left}, 1 = \text{middle}, 2 = \text{right}$), click type (`single` or `double`), time elapsed since preceding click (`time_since_last_click_ms`), and semantic target element category (`button`, `link`, `input`, `select`, `canvas`, `other`).
- **Timestamps:** Client-side epoch milliseconds (`client_timestamp`) and server receipt timestamp (`server_timestamp`).

### B. Scrolling Dynamics
- **Offsets & Displacements:** Horizontal and vertical scroll positions (`scroll_x`, `scroll_y`), displacements (`delta_x`, `delta_y`), scrolling velocity (`velocity_px_s`), directional vector (`up`, `down`, `left`, `right`, `none`), and elapsed time since preceding scroll event (`time_since_last_scroll_ms`).

### C. Keystroke Timing Metadata (Zero Text Captured)
- **Temporal Dynamics Only:** Key press hold duration / dwell time (`dwell_ms` or `hold_time_ms`), flight time between successive key events (`flight_ms` or `inter_key_latency_ms`), and inter-key interval (`inter_key_interval_ms`).
- **Structural Event Flags:** Boolean flags indicating whether the key pressed was a backspace (`is_backspace`) or a paste shortcut (`is_paste`).
- **No Character Logging:** No key names, character representations, key codes, or typed textual strings are captured.

### D. Navigation & Tab Visibility State
- **Route Tracking:** Application route pathnames (`/catalog`, `/search`, `/checkout`, `/products`), sanitized referrer pathnames, route dwell time (`dwell_time_ms`), and sequential navigation order.
- **Tab State:** Browser tab visibility state (`visible`, `hidden`, `focus`, `blur`) and duration away from the active tab (`duration_away_ms`).

### E. Session Context & Browser Fingerprint Metadata
- **Identifiers:** Ephemeral session identifier (`sess_<20-char-hex>`) and assigned pseudonymous research participant profile identifier (`H1`, `H2`, `H3`, `H4`).
- **Device & Environment:** Browser User-Agent string (browser family, OS version, rendering engine), screen/viewport resolution (e.g., `1920x1080`), and client system timezone string (e.g., `UTC`, `Asia/Kolkata`).
- **Task & Research Labels:** Experimental task tag (`TASK_01`, `TASK_02`, `TASK_03`), collection mode (`HUMAN`), and ground-truth classification label (`0` for human).

### F. Application Domain API Request Metadata
- **Network Traffic Dynamics:** Request endpoint URL path (e.g., `/api/products`), HTTP method (`GET`, `POST`), HTTP response status code, measured round-trip response latency in milliseconds (`response_time_ms`), request body size in bytes, and response body size in bytes.
- **Structural Key Names Only:** Parameter names present in query strings (`param_keys`) and field names present in request JSON bodies (`payload_keys`). **Values associated with parameters or body payloads are stripped before transmission.**

### G. Client IP Address Handling & Web Server Logging
- **Application Layer (Pseudonymized):** The backend receives the connecting IP address from the TCP socket connection and immediately computes a 256-bit cryptographic digest using SHA-256 (`ip_hash`). The database, cache, and exported research datasets store ONLY this one-way hash. The raw IP address is not written to research dataset files.
- **Transport Layer (Network Access Logs):** Standard web server access logging (e.g., Uvicorn transport logs or reverse proxy connection logs) may ephemerally log the raw incoming network IP address in connection stream logs for operational diagnostic purposes.

---

## 3. Data Technically Excluded vs. Data Not Requested

To ensure transparency, CrossTrace distinguishes between data prevented from transmission by technical filters and data not requested by the study:

| Category | Specific Data Elements | Protection Mechanism |
| :--- | :--- | :--- |
| **Technically Blocked & Discarded** | Raw typed characters (`key`, `code`, `value`, `text`, `inputValue`, `keyCode`, `which`, `char`). | Server-side automated privacy schema validator recursively inspects all event payloads before buffer append, cache save, or database write. Any forbidden key raises `PrivacyViolationError` and returns HTTP 400 Bad Request. |
| **Technically Blocked & Discarded** | Password element interactions (`target_type == "password"`). | Automated validator rejects any telemetry associated with password input elements. |
| **Technically Blocked & Discarded** | Query parameter values and form-input field values. | API client strips parameter and payload values, transmitting only sorted field keys (`param_keys`, `payload_keys`). |
| **Not Requested by Study** | Personal contact details (real name, physical address, personal email, phone number). | Not requested in any UI form, prompt, or endpoint. |
| **Not Requested by Study** | Financial credentials, credit card numbers, billing information. | Demonstration application uses mock catalog/cart items and mock checkout verification only. |

---

## 4. Nature of Data: Pseudonymity vs. Anonymity

**This research data is PSEUDONYMOUS, NOT ANONYMOUS.**
- Individual participants are identified across sessions by an assigned pseudonymous research token (`H1`, `H2`, `H3`, `H4`).
- While direct personal identifiers are not collected, combinations of device viewport resolution, browser User-Agent string, client timezone, and hashed IP address constitute pseudonymous browser fingerprint data that could theoretically be linked to an individual if combined with external auxiliary datasets.
- Accordingly, the data is treated as pseudonymous research telemetry under standard data protection principles.

---

## 5. Data Storage, Security & Access Restrictions

- **Storage Locations:** Data is stored locally in project development directories (`ml/data/phase2_development/`) and in-memory cache structures (`.active_sessions_cache.json`).
- **Access Control:** Access is strictly restricted to authorized CrossTrace project researchers on secured workstations. Datasets are not distributed to third parties, advertising exchanges, or commercial brokers.
- **Security Boundary:** Phase 2 development datasets are strictly isolated from Phase 1 baseline files and quarantined evaluation sets via canonical path containment safeguards.

---

## 6. Voluntary Participation & Right to Withdraw

- **Voluntary Participation:** Your participation is completely voluntary. You are free to refuse participation or stop interacting with the tasks at any time without penalty.
- **Withdrawal Process:** You may request that all sessions associated with your assigned participant token (`H1`–`H4`) be deleted from the development partition. To request deletion, notify the research team using the contact method below prior to the Stage 2C model freeze. Once the dataset is frozen and cryptographically signed for scientific peer review reproducibility, individual records cannot be selectively excised without invalidating reproducibility verification.

---

## 7. Data Retention & Deletion Policy

- **Current Operational Arrangement:** Development session telemetry will be retained for the duration of the CrossTrace experimental evaluation, baseline comparison analysis, and peer-review publication cycle.
- **Pending Institutional Decision (BLOCKER):** A formal calendar deletion date and long-term institutional archiving schedule have not yet been established. This operational decision is flagged as an unresolved requirement in Section 9 below and must be confirmed prior to recruitment.

---

## 8. Research Contacts

- **Repository Operator & Lead Developer:** Ram Mahajan (`mahajanram1506@gmail.com`)
- **Institutional Ethics / IRB Contact (BLOCKER):** A formal Institutional Review Board (IRB) or human research ethics committee contact point has not yet been designated for this repository workspace. This is flagged as an unresolved requirement in Section 9 below.

---

## 9. Pre-Recruitment Unresolved Operational Decisions (Blockers)

Before human participant recruitment or data collection can be authorized, the project team must formally resolve and record:

1. **Formal Institutional Oversight:** Confirm whether formal institutional IRB/ethics board approval is required for participant recruitment, and record the designated institutional contact or oversight exemption.
2. **Defined Data Retention Cutoff:** Specify the exact calendar retention period (e.g., 12 months post-publication) and the scheduled permanent deletion date for the development partition.
3. **Contact Protocol for Withdrawal:** Confirm that `mahajanram1506@gmail.com` serves as the official withdrawal communication channel, or provide an official institutional study mailbox.

---

## 10. Participant Acknowledgement

*(This acknowledgement must be presented and confirmed by each participant prior to initiating their first task session):*

```
[ ] I confirm that I have read and understood the CrossTrace Phase 2 Participant Information Brief.
[ ] I understand that the system collects cursor coordinates, motion dynamics, scroll behavior,
    keystroke timing intervals (hold duration and inter-key latency), browser fingerprint metadata,
    and API request timing.
[ ] I understand that raw typed characters, form field values, and passwords are NOT collected.
[ ] I understand that my data is pseudonymous (linked to an assigned ID such as H1) and that my
    IP address is cryptographically hashed with SHA-256.
[ ] I understand that my participation is voluntary and that I may withdraw my data prior to
    model freeze by contacting the study lead with my assigned participant ID.
[ ] I freely consent to participate in this research study.
```
