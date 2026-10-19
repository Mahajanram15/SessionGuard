# CrossTrace Phase 2 — Baseline Metadata Recovery Proposal

**Candidate File**: `ml/metadata_recovery/candidate_metadata_53_sessions.csv`  
**Candidate SHA-256**: `E98184240A8E6C4FC895CE132FE68EBD279420DF572396A9F5B5460E072EF8B9`  
**Original Protected File (Untouched)**: `ml/data/metadata.csv`  
**Original Protected SHA-256**: `E2BAD00643DDE2AC6F1A8889D8B5987AEB957390CAD7E37B3BC13B3A7E9DC3A5`  

---

### 1. Forensic Root Cause
Inspection of git history reveals that in commit `5b1eb5c` (*feat: implement Phase 2 windowed kinematics feature extractor and training configuration*, Oct 19 23:05:51 2026), user prompt text starting with `Revise the CrossTrace Phase 2 implementation plan based on the following review findings...` was accidentally pasted into `ml/data/metadata.csv` from line 54 to line 92, replacing the 53rd data row.

When `pd.read_csv("ml/data/metadata.csv")` parses this file, it parses the 39 markdown lines as rows, resulting in 82 rows total, causing a row mismatch against `features.csv` (53 rows).

---

### 2. Provenance of the Candidate Recovery File
The candidate file was extracted directly from git commit `58c045bcb2b10bbc7711d34f4c8a0890f558cdbc`:
```bash
git show 58c045b:ml/data/metadata.csv > ml/metadata_recovery/candidate_metadata_53_sessions.csv
```
Commit `58c045b` (*feat: add baseline comparison model training pipeline and session features dataset*, Oct 19 22:27:12 2026) was authored immediately prior to commit `5b1eb5c`.

---

### 3. Verification & Alignment Against `features.csv`
1. **Dimensions**: Exactly 53 data rows (54 total lines including header) and 8 columns:
   `session_id,collection_mode,automation_condition,task_id,participant_id,collection_timestamp,label,event_count`
2. **Label Alignment**: All 53 binary labels (`0` = HUMAN, `1` = AUTOMATED) match `features.csv` row-for-row with 100% identity.
3. **Event Count Consistency**: All 53 session event counts match or exceed the corresponding `mouse_event_count` in `features.csv`.
4. **The Missing 53rd Row**: Row 53 is verified as:
   `sess_d0ebf5fe362a42cebe17,HUMAN,NONE,TASK_03,p_01,1792407859896,0,586`
5. **Zero Invented Rows**: 100% of rows are derived from verified git blob history. Zero metadata was invented or estimated.

---

### 4. Recommendation
The candidate file is ready. Per strict project instructions, `ml/data/metadata.csv` has **not** been modified. When authorized by the user in a future step, this candidate file can be copied to replace the corrupted `ml/data/metadata.csv`.
