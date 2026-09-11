# Genie Code re-drive with AI metadata (2026-09-11)

Re-driving all 4 use cases through the Genie Code UI in `slhs_test1` AFTER adding
PK/FK + table/column comments to the base tables, to see whether the metadata improves
Genie Code's live behavior. Data-only clean state (metric views + AI tables dropped, base
tables carry 10 PK / 6 FK / comments). Each asset independently verified via SQL / API.

Key question: does the metadata reduce gotchas and let short natural prompts land correctly?

---

## 01 CKD

### Metric view — clinical.ckd_patient_registry_metrics  ✅ FIRST-PROMPT SUCCESS
- Prompt (one natural line): *"build a reusable metric view in unity catalog on the ckd patient
  registry. i want measures for total patients, how many actually have ckd, care gap patients,
  and high risk patients. let me break it down by ckd stage, sex and age"*
- Genie Code explored schema + data ("2,000 patients across 6 CKD stages"), then created +
  validated the metric view in ONE pass. **No G3 dashboard detour; correct definitions first try.**
- **Metadata payoff:** it defined `care_gap_patients` (CKD not documented in Epic = 518) and
  `high_risk_patients` (stage 4/5 not seeing nephrology = 230) WITHOUT me spelling out the SQL —
  the column comments carried those definitions. Previously (pre-metadata) this took 3 prompts
  incl. a wrong-turn dashboard, and care-gap definition had to be clarified.
- Measures still named by raw column (patient_count, etc.) — G4 unchanged.
- **Verified (SQL):** MEASURE(patient_count)=2000, ckd_patient_count=1524, care_gap_patients=518,
  high_risk_patients=230; table_type=METRIC_VIEW. Matches answer key exactly.
- Note: Genie Code also *found a leftover notebook* from the prior build. In a fresh attendee
  workspace that notebook won't exist; here it still explored the live schema/data before building.

### AI function — clinical.clinical_notes_ckd_extraction  ✅ FIRST-PROMPT SUCCESS
- Prompt: *"now i have clinical notes in slhs_test1.clinical.clinical_notes. use an ai function to
  read each note and tell me whether it mentions chronic kidney disease and whether the patient
  is seeing nephrology. save the results to a table i can query"*
- Genie Code read the table (using the comments), confirmed 1,018 notes, built an `ai_extract`
  query (enum types), ran it (~3 min), and validated. Table clinical_notes_ckd_extraction (1,018
  rows; cols patient_id, note_id, note_date, note_type, author, mentions_ckd, seeing_nephrology).
- **Verified (SQL):** mentions_ckd = Yes 759 / No 256 / null 3; precision = 757/759 flagged notes
  are for has_ckd=true patients = **99.7%** (grounded, no fabrication). Matches prior behavior.

### Genie Agent — "CKD Patient Registry" (01f1ae0626f41e31a517eb3aac920de1)  ✅
- Prompt: *"now create a genie space on the ckd data so clinicians can ask questions about kidney
  patients in plain english. use the ckd patient registry and the ckd_patient_registry_metrics
  metric view we built, and add a few good sample questions"*
- Genie Code created the space (no G13 Accept gate this time) over the registry + metric view.
- **Verified live (Conversation API):** "how many high risk patients are there?" -> **230**, via
  `SELECT MEASURE(high_risk_patients) FROM ckd_patient_registry_metrics`. Correct.

### AI/BI dashboard — "CKD Patient Registry Dashboard" (01f1ae0678c51786af5d28272ca942ea)  ✅
- Prompt: *"now build an ai/bi dashboard on the ckd_patient_registry_metrics metric view. show total
  ckd patients, care gap patients and high risk patients as big number tiles, plus care gap patients
  broken down by ckd stage and by assigned provider"*
- **Gotcha (NEW, G18): dashboard name collision.** The build first failed with "There is already a
  dashboard named 'CKD Patient Registry Dashboard'" because the PRIOR session's dashboard still
  existed. Also, Genie Code initially fumbled its dashboard-editing tools (openAsset/editAsset
  handoff). Fix: delete the stale prior-session dashboards + Genie spaces so names are free, then
  it completed. **In a fresh attendee workspace this collision does not occur.**
- **Verified (Lakeview API):** 5 datasets + 5 widgets (3 counter tiles + 2 bar charts) on the metric
  view. Tiles map to 1,524 / 518 / 230.

### Databricks App — ship pre-built (established finding G8-G10)
- Genie Code scaffolds+deploys but the app isn't runnable without developer finishing. Not re-driven;
  use the repo's pre-built answer-key app. (Use-case-independent; same for all 4.)

## NEW ASSET IDs (for doc-link refresh; OLD 01f1ac... assets deleted)
- CKD: Genie space 01f1ae0626f41e31a517eb3aac920de1 | dashboard 01f1ae0678c51786af5d28272ca942ea

---

## 02 Medication Diversion

### Metric view — med_diversion.medication_activity_metrics  ✅ FIRST-PROMPT SUCCESS
- Prompt: *"build a reusable metric view in unity catalog on slhs_test1.med_diversion.medication_activity
  to help spot possible drug diversion. i want measures for total transactions, off-shift activity,
  and unwitnessed waste events. dimensions for employee, unit and shift"*
- Genie Code built it with 3 measures (total_transactions, off_shift_activity, unwitnessed_waste) +
  11 dimensions. The comments let it define unwitnessed_waste = waste event with null witness.
- **Verified (SQL):** total_transactions=45,000, unwitnessed_waste=326; grouped by employee the 4
  planted diverters top the list (Allison Hill 88, Angie Henderson 87, Noah Rhodes 83, Daniel
  Wagner 68) then a cliff to 0. Correct.

### AI function — med_diversion.employee_risk_summaries  ✅ NO FABRICATION (G11 payoff)
- Prompt: *"now using the medication_activity_metrics view, take the top 10 employees by unwitnessed
  waste events and use an ai function to write a short risk-summary narrative for each one explaining
  why they might be a concern. save it as a table in med_diversion i can review"*
- Genie Code queried the metric view for the top 10 and used `ai_gen()` for narratives, saved to
  employee_risk_summaries (employee_id, employee_name, total_transactions, off_shift_activity,
  unwitnessed_waste, risk_summary).
- **HEADLINE FINDING:** with the column comments + FK + metric-view grounding, a NATURAL prompt used
  **real employees (10/10 match employee_risk; top = the 4 real diverters)** and cited real numbers
  (e.g. Allison Hill: 88 unwitnessed waste, 917 txns, 618 off-shift). **No fabrication** — contrast
  with the pre-metadata run where the first natural attempt invented fake employees (old G11). The
  metadata materially reduced the fabrication risk. (Still: always verify AI output vs source.)

### Genie Agent — "Medication Diversion Monitor" (01f1ae08af291854b6ef6533875dbc4c)  ✅
- Prompt referenced medication_activity + the metric view + employee_risk_summaries.
- **Verified live (API):** "which 5 employees have the most unwitnessed waste events?" -> the 4 real
  diverters (Allison Hill 88, Angie Henderson 87, Noah Rhodes 83, Daniel Wagner 68), cliff to 0. Correct.

### AI/BI dashboard — "Medication Diversion Monitor Dashboard" (01f1ae08ebaa11129ce693930df2c58c)  ✅
- Prompt: tiles for total transactions / off-shift / unwitnessed waste; bar top-10 employees by
  unwitnessed waste; unwitnessed waste by unit.
- **Verified (Lakeview API):** 5 datasets + 5 widgets (3 counters + 2 bars) on the metric view. The
  multi-step build (openAsset/editWidgetsV2/simpleCreateWidget handoff) is slow but completed.

### Databricks App — ship pre-built (G8-G10, use-case-independent).

## Use case 02 COMPLETE. New IDs: Genie 01f1ae08af291854b6ef6533875dbc4c | dashboard 01f1ae08ebaa11129ce693930df2c58c

---

## 03 HTM (Equipment Planning)

### Metric view — htm.medical_assets_metrics  ✅ FIRST-PROMPT SUCCESS
- Prompt named measures (asset count, total replacement cost, avg risk, assets whose support ends
  this year) + dimensions (facility, manufacturer, device status, support-end year). Genie Code
  derived support_end_year from support_end_date on its own (comment helped).
- **Verified (SQL):** MEASURE(asset_count)=8,000, total_replacement_cost=$2.02B, avg_risk=65.6,
  support_ending_this_year(2026)=1,388. Correct.

### AI function (forecast) — htm.corrective_wo_forecast  ✅ (fallback) / G14 stands
- Prompt asked for a 6-month corrective-WO forecast via an AI forecasting function.
- **G14 CONFIRMED: ai_forecast (Predictive AI Functions) is still DISABLED** in this workspace (both
  v1 and v2). NEW behavior vs prior run: Genie Code did NOT silently fall back — it surfaced options
  (retry after enabling / Python fallback / skip). Told to use the Python fallback, it fit
  Holt-Winters (had to pip-install statsmodels + restart kernel), and saved corrective_wo_forecast
  (ds, actual, forecast, forecast_lower/upper).
- **Verified (SQL):** forecast ~461-483 corrective WOs/month (bounds 432-512), grounded in the real
  ~447-502/month history.
- **WORKSHOP IMPLICATION:** this is the slowest/most fragile asset. ENABLE the Predictive AI
  Functions preview before the onsite so ai_forecast runs natively (one clean SQL step instead of a
  multi-minute Python fallback with a package install).

### Genie Agent — "Medical Equipment & Replacement Planning" (01f1ae0af6301d0bac8ece3fabbeeff6)  ✅
- **Verified live (API):** "how many assets have support ending in 2026?" -> **1,388** via
  MEASURE(asset_count) filtered to support_end_year 2026. No G13 gate this time.

### AI/BI dashboard — "Medical Equipment Capital Planning Dashboard" (01f1ae0b2f8a1d5783e004ed18a123b3)  ✅
- Tiles: total assets / total replacement cost / assets ending support this year; bars: assets ending
  by facility, replacement cost by manufacturer.
- **Verified (Lakeview API):** 5 datasets + 5 widgets (3 counters + 2 bars). Build hit a transient
  "wrong page ID" retry but completed.

### Databricks App — ship pre-built (G8-G10).

## Use case 03 COMPLETE. New IDs: Genie 01f1ae0af6301d0bac8ece3fabbeeff6 | dashboard 01f1ae0b2f8a1d5783e004ed18a123b3

---

## 04 AI Huddle Management

### Metric view — huddle.physician_inputs_metrics  ✅ FIRST-PROMPT SUCCESS
- Prompt named measures (patient count as distinct patients, avg complexity, avg relationship,
  non-optimal assignments where assigned <> optimal) + dims (provider, huddle date, assigned member).
- **Verified (SQL):** MEASURE(patient_count)=18 (distinct - correct), non_optimal_assignments=20,
  avg_complexity=0.76. Matches. (Distinct-patient count right first try - comment + explicit ask.)

### AI function (transcript extraction from Volume) — huddle.transcript_ai_extractions  ✅ grounded
- Prompt: read the transcript text files in the volume slhs_test1.huddle.transcripts, extract barriers
  to care / social needs / recommended follow-up per patient, save to a NEW table
  transcript_ai_extractions (deliberately new name to avoid the G15 overwrite).
- Genie Code used ai_extract over the 18 transcript files (cols file_name, patient_name, patient_id,
  provider, huddle_date, barriers_to_care, social_needs, recommended_follow_up_actions, transcript_text).
- **Verified (SQL):** 18 rows; **18/18 patient_ids real** (join to patient_demographics) - no
  fabrication. The loaded transcript_extractions table stayed intact (G15 avoided via new table name).
- Note: Genie Code "compacted" its own (long) chat mid-run - fine, just a pause.

### Genie Agent — "Care Team Daily Huddle" (01f1ae0d9a7a12cc8de27ca6e5c7ed86)  ✅
- **Verified live (API):** "how many patients were assigned to a team member who was not the optimal
  one?" -> **20** via non_optimal_assignments. (First send was lost after the chat compaction; a
  re-send created it - NEW gotcha G19: after a long Genie Code chat compaction, a queued create can
  drop silently; re-send if the asset doesn't appear.)

### AI/BI dashboard — "Care Team Huddle Dashboard" (01f1ae0df4911a33975000df2239ed85)  ✅
- Tiles: patient count / avg complexity / non-optimal assignments; bars: patient count by provider,
  non-optimal by assigned team member.
- **Verified (Lakeview API):** 5 datasets + 5 widgets (3 counters + 2 bars). (Also needed a re-send - G19.)

### Databricks App — ship pre-built (G8-G10).

## Use case 04 COMPLETE. New IDs: Genie 01f1ae0d9a7a12cc8de27ca6e5c7ed86 | dashboard 01f1ae0df4911a33975000df2239ed85

---

# ALL 4 USE CASES REBUILT VIA GENIE CODE + VERIFIED (2026-09-11)
Metric view + AI function + Genie agent + AI/BI dashboard for every use case, from the data-only
state carrying PK/FK + comments. Apps ship pre-built.

## NEW ASSET IDs (canonical - replaces the deleted 01f1ac... assets in all docs)
| Use case | Genie space | AI/BI dashboard |
|---|---|---|
| CKD | 01f1ae0626f41e31a517eb3aac920de1 | 01f1ae0678c51786af5d28272ca942ea |
| Medication Diversion | 01f1ae08af291854b6ef6533875dbc4c | 01f1ae08ebaa11129ce693930df2c58c |
| HTM | 01f1ae0af6301d0bac8ece3fabbeeff6 | 01f1ae0b2f8a1d5783e004ed18a123b3 |
| AI Huddle | 01f1ae0d9a7a12cc8de27ca6e5c7ed86 | 01f1ae0df4911a33975000df2239ed85 |

## METADATA PAYOFF SUMMARY
- CKD metric view: correct 4 measures in ONE prompt (was 3 prompts + a dashboard wrong-turn).
- Diversion AI function: used REAL employees, NO fabrication (was the headline G11 failure).
- Huddle metric view: distinct-patient count correct first try.
- Metric-view/agent builds lean on the column comments for definitions (care gap, high risk,
  unwitnessed waste, non-optimal assignment) without hand-written SQL.
- Still true: ai_forecast preview disabled (G14); apps not runnable from Genie Code (G8-G10).
- New: G18 dashboard name collisions with stale assets; G19 queued creates can drop after a long-chat compaction.
