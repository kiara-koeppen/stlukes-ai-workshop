# Genie Agent curation: instructions + example SQL (per use case)

Beyond table/column comments and PK/FK constraints, the single biggest lever on Genie
accuracy is **curated space instructions** plus a few **example SQL queries** (trusted
assets). Add these to each agent (Genie space -> Configure -> Instructions, and
-> Example queries). This file is the source of truth; the answer-key agents are
configured from it, and the User/Instructor guides tell attendees to add the same.

Notes on querying metric views: measures must be wrapped in `MEASURE()`. Metric-view
measure/dimension names are the raw ones Genie Code created (see each metric view).

---

## 01 CKD - "CKD Patient Registry"
**General instructions**
- This space is for identifying under-documented and under-managed chronic kidney disease (CKD).
- "Care gap" / "undocumented CKD" = a patient with `has_ckd = true` whose `documented_ckd` is not 'Yes' (it is 'No' or 'None'). These patients truly have CKD but it is not documented in the EHR.
- "High risk" = advanced-stage CKD (stage 4 or 5) AND `sees_nephrology = false`.
- CKD stage lives in `actual_ckd_stage` (values like 1, 2, 3a, 3b, 4, 5). Lab GFR is in gfr_1/2/3 (lower = worse).
- Prefer the metric view `clinical.ckd_patient_registry_metrics` for counts (total patients, CKD patients, care gap, high risk); use `MEASURE(...)`.
- Never invent patients; answer only from the registry and clinical notes.

**Example queries**
- Total patients and patients who have CKD:
  `SELECT MEASURE(patient_count) AS patients, MEASURE(ckd_patient_count) AS with_ckd FROM clinical.ckd_patient_registry_metrics`
- Care-gap and high-risk counts:
  `SELECT MEASURE(care_gap_patients) AS care_gap, MEASURE(high_risk_patients) AS high_risk FROM clinical.ckd_patient_registry_metrics`
- Undocumented-CKD worklist by stage:
  `SELECT actual_ckd_stage, count(*) AS n FROM clinical.ckd_patient_registry WHERE has_ckd = true AND documented_ckd IN ('No','None') GROUP BY actual_ckd_stage ORDER BY actual_ckd_stage`

## 02 Medication Diversion - "Medication Diversion Investigation"
**General instructions**
- This space supports diversion investigators. Findings prioritize employees for human review; they are never an accusation.
- A "diverter" signal = high **unwitnessed waste** (event_type = 'waste' with `witness_id IS NULL`), plus off-shift activity (`off_shift_flag = true`), out-of-department activity, and controlled-substance (CII) handling.
- Rank suspicious staff by unwitnessed waste events. Always keep real `employee_id` / `employee_name` from the data; never invent employees.
- `medication_activity.employee_id` joins to `employee_risk` (peer context) which joins to `peer_group`.

**Example queries**
- Total transactions and unwitnessed waste:
  `SELECT count(*) AS transactions, sum(CASE WHEN event_type='waste' AND witness_id IS NULL THEN 1 ELSE 0 END) AS unwitnessed_waste FROM med_diversion.medication_activity`
- Top employees by unwitnessed waste:
  `SELECT employee_id, employee_name, count(*) AS unwitnessed_waste FROM med_diversion.medication_activity WHERE event_type='waste' AND witness_id IS NULL GROUP BY employee_id, employee_name ORDER BY unwitnessed_waste DESC LIMIT 10`

## 03 HTM - "HTM Medical Equipment & Replacement Planning"
**General instructions**
- This space supports biomed/HTM capital equipment replacement planning.
- "End of life" / "support ending" uses `support_end_date`; "ending in 2026" = year(support_end_date) = 2026.
- Replacement cost is `replacement_cost` (USD); sum it for capital planning. `risk_score` higher = higher replacement priority.
- `work_orders.asset_number` joins to `medical_assets`. Corrective work orders have work_order_type = 'corrective'.
- Prefer the metric view `htm.medical_assets_metrics` for asset counts, total replacement cost, and assets with support ending this year.

**Example queries**
- Assets, total replacement cost, assets ending support in 2026:
  `SELECT count(*) AS assets, round(sum(replacement_cost)/1e9,2) AS replacement_cost_billions, sum(CASE WHEN year(support_end_date)=2026 THEN 1 ELSE 0 END) AS ending_2026 FROM htm.medical_assets`
- Replacement cost by facility for assets ending support this year:
  `SELECT facility, round(sum(replacement_cost),0) AS cost FROM htm.medical_assets WHERE year(support_end_date)=2026 GROUP BY facility ORDER BY cost DESC`

## 04 AI Huddle - "Care Team Daily Patient Huddle"
**General instructions**
- This space supports the care-team daily huddle at the Nampa clinic.
- "Non-optimal assignment" = a row in `physician_inputs` where `assigned_team_member <> optimal_team_member`.
- Patient complexity is `patient_complexity_score` and provider-relationship strength is `provider_patient_relationship_score` (both physician-rated).
- `physician_inputs.pat_id` and `transcript_extractions.pat_id` join to `patient_demographics.pat_id`.
- Prefer the metric view `huddle.physician_inputs_metrics` for patient count, average complexity, and non-optimal assignment count. Count patients as distinct pat_id.

**Example queries**
- Patient count and non-optimal assignments:
  `SELECT count(DISTINCT pat_id) AS patients, sum(CASE WHEN assigned_team_member <> optimal_team_member THEN 1 ELSE 0 END) AS non_optimal FROM huddle.physician_inputs`
- Non-optimal assignments by assigned team member:
  `SELECT assigned_team_member, count(*) AS n FROM huddle.physician_inputs WHERE assigned_team_member <> optimal_team_member GROUP BY assigned_team_member ORDER BY n DESC`
