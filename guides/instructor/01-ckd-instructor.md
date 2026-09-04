# CKD Identification & Risk Flagging: Instructor Cheatsheet

## TL;DR

CKD stages are frequently missing or incorrectly documented in Epic, forcing physicians to manually review large patient cohorts. The solution identifies patients whose lab evidence indicates CKD but whose Epic documentation is missing or wrong (the care gap), suggests the likely KDIGO stage from recent labs and trends, and flags high-risk patients (advanced stage, not seeing nephrology) for urgent clinician review.

## The Solution We Built

All assets are deployed and verified live on kk_test. Swap catalog to `healthcare_ai` when participants deploy to prod.

### Structured Data

- **`kk_test.clinical.ckd_patient_registry`** (2,000 patients): de-identified patient demographics, lab history (prior 3 months creatinine and GFR), albuminuria category, documented CKD stage (often wrong or missing), Epic problem-list status, nephrology referral status, key medications (SGLT-2i, GLP-1 agonist), and ground-truth KDIGO stage derived from lab data.
- **`kk_test.clinical.clinical_notes`** (1,018 notes): free-text clinical progress notes with embedded lab trends, nephrology referral mentions, and medication details.

### Semantic Layer (Metric View)

- **`kk_test.clinical.ckd_metrics`** (verified 2026-09-04): dimensions for actual stage, documented stage, nephrology referral, assigned provider, age band, albuminuria category, key medication use, care-gap status, and stage match. Measures compute:
  - **1,524** patients with CKD (ground truth).
  - **500 care-gap patients** (33% undocumented): lab stage >= 3 but Epic says "No" or "None".
  - **230 high-risk patients**: stage 4 or 5 and NOT seeing nephrology, flagged for referral.
  - Undocumented rate, average GFR/creatinine, nephrology engagement rate.

### AI Functions

- **`kk_test.clinical.notes_ckd_signals`** (200 scored notes, 102 AI-flagged): runs `ai_query` on the clinical-notes text, asking the LLM to extract whether the note indicates CKD per KDIGO logic, suggests the stage, and mentions nephrology. Parse the JSON response with `from_json` into a struct. Joins back to the registry to compute `ai_flag_undocumented`: true if AI says "indicates CKD" AND Epic says "No/None". Precision verified: 102/102 flagged notes truly have lab-derived stage >= 3.

### Genie Agent

- **Space ID `01f1a88b5c6613f9ad5a4383a3b81a6b`** (live-verified): point the agent at the metric view and registry table. The agent answers "How many patients are undocumented for CKD?" (500), "Show me the high-risk patients by provider" (230 patients stratified), "What is the average GFR in the care-gap cohort?" (typically 35-45 ml/min/1.73m2).

### AI/BI Dashboard

- **Dashboard ID `01f1a88db2fc1a5f843fe617311b5cc2`** (verified 2026-09-04): shows care-gap patients by stage, high-risk by facility/provider, KPI tiles for undocumented rate and nephrology engagement, trend of care-gap discovery over time.

## How to Build It

### Step 1: Load Structured Data (Participant Setup Notebook)

Participants run the data-generation notebook (e.g., `generator/01_ckd_generator.py` or the equivalent SQL), which creates:

- `{catalog}.clinical.ckd_patient_registry` with parameterized catalog/schema (widget defaults to `kk_test`).
- `{catalog}.clinical.clinical_notes` (1,018 notes).

**Facilitator check**: Verify counts with SQL:
```sql
SELECT count(*) patient_count FROM {catalog}.clinical.ckd_patient_registry
WHERE has_ckd = true;
```
Should return approximately 1,524.

### Step 2: Build the Metric View

Participants write a metric view over the registry using Genie Code (or direct SQL).

**Genie Code Prompt:**
```
Create a metric view named ckd_metrics over {catalog}.clinical.ckd_patient_registry 
with dimensions: Actual Stage (actual_ckd_stage), Documented CKD (documented_ckd), 
Sees Nephrology (sees_nephrology), Sex, Age Band (case: <55, 55-64, 65-74, 75+), 
Albuminuria (microalbumin_category), Care Gap (true if actual stage >= 3 AND documented 
in No/None), Stage Match (true if documented equals actual).
Add measures: Patient Count, Patients With CKD (sum where has_ckd=true), Care Gap Patients 
(sum where Care Gap=true), High Risk Patients (sum where actual stage in 4/5 AND 
sees_nephrology=false), Undocumented CKD Rate (care gap / patients with ckd).
```

**Facilitator check**: Query the view:
```sql
SELECT Patient_Count, Care_Gap_Patients, High_Risk_Patients, Undocumented_CKD_Rate
FROM {catalog}.clinical.ckd_metrics;
```
Expected: 1,524 total CKD, 500 care-gap (~33%), 230 high-risk, rate ~0.33.

### Step 3: Create the AI Functions (ai_query)

Participants write a table that applies `ai_query` to clinical notes, extracting CKD signals.

**Direct SQL or Genie Code Prompt:**
```
Score the clinical notes with an AI function that extracts whether each note 
indicates CKD per KDIGO staging, suggests a stage, and mentions nephrology. 
Use the model "databricks-meta-llama-3-3-70b-instruct". Return the results as a 
table with columns: patient_id, note_id, note_date, ai_indicates_ckd, ai_suggested_stage, 
ai_mentions_nephrology, and a flag column ai_flag_undocumented (true if AI says 
Yes AND registry documented_ckd is No/None).
```

**Technical note**: Use `ai_query` (not `ai_extract`) because the directed prompt is crisper. Parse the JSON response with `from_json(..., 'STRUCT<indicates_ckd: STRING, suggested_stage: STRING, mentions_nephrology: STRING>')`.

**Facilitator check**: Verify precision on 200 scored notes:
```sql
SELECT count(*) total_scored,
       sum(CASE WHEN ai_flag_undocumented THEN 1 ELSE 0 END) undocumented_flagged,
       sum(CASE WHEN ai_flag_undocumented AND actual_ckd_stage IN ('CKD 3a','CKD 3b','CKD 4','CKD 5') 
           THEN 1 ELSE 0 END) precision_check
FROM {catalog}.clinical.notes_ckd_signals;
```
Expect precision (true positives / flagged) >= 90%.

### Step 4: Create the Genie Agent

Participants use the REST API to create a Genie Agent (formerly Genie Space).

**Steps:**
1. Open a terminal or use the solutions/_tools script.
2. POST to `/api/2.0/data-rooms/` with:
   ```json
   {
     "display_name": "CKD Care Gap Discovery",
     "warehouse_id": "c68a614580fefe22",
     "table_identifiers": [
       "{catalog}.clinical.ckd_metrics",
       "{catalog}.clinical.ckd_patient_registry"
     ],
     "run_as_type": "VIEWER",
     "description": "Identify undocumented CKD, high-risk patients, and care gaps"
   }
   ```
3. Capture the returned `space_id`.

**Facilitator check**: Test the agent with `genie_ask.py`:
```bash
uv run --with requests --python 3.11 python solutions/_tools/genie_ask.py <space_id> \
  "How many patients have undocumented CKD?"
```
Expected response: mentions "500" or "care gap" patients.

### Step 5: Build the AI/BI Dashboard

Participants create a Lakeview dashboard that visualizes the metric view.

**Genie Code Prompt (or use the lvdash.json file):**
```
Create a dashboard with these widgets:
- KPI: Total CKD Patients (from ckd_metrics, filtered has_ckd=true)
- KPI: Care Gap Patients (from ckd_metrics, filtered Care Gap=true)
- KPI: High Risk Patients (from ckd_metrics, filtered High Risk=true)
- Bar chart: Care Gap count by Actual Stage
- Bar chart: High Risk patients by Assigned Provider
- Table: High Risk patients (actual stage, documented stage, nephrology status, age)
Add filters for Sex, Age Band, and Care Gap status.
```

## Genie Code Prompts That Land the Solution

These are the natural-language prompts that generate each major asset. Participants can type these into Genie Code (or ask Chad in the room for guidance).

### Metric View Prompt

```
Create a metric view named ckd_metrics from the table kk_test.clinical.ckd_patient_registry 
(or your parameterized {catalog}.clinical.ckd_patient_registry).

Dimensions:
- Actual Stage: the actual_ckd_stage column
- Documented CKD: the documented_ckd column (what Epic says)
- Sees Nephrology: the sees_nephrology column (boolean)
- Sex: sex
- Age Band: case when age < 55 then '45-54' when age < 65 then '55-64' when age < 75 then '65-74' else '75+'
- Albuminuria: microalbumin_category (A1, A2, or A3)
- Care Gap: case when actual_ckd_stage in ('CKD 3a', 'CKD 3b', 'CKD 4', 'CKD 5') and documented_ckd in ('No', 'None') then 'Care Gap' else 'OK'
- Stage Match: case when documented_ckd != actual_ckd_stage and actual_ckd_stage != 'None' then 'Mismatch' else 'Match'
- On Key Meds: case when key_meds is not null and key_meds <> '' then 'Yes' else 'No'

Measures:
- Patient Count: count(1)
- Patients With CKD: sum(case when has_ckd then 1 else 0 end)
- Care Gap Patients: sum(case when actual_ckd_stage in ('CKD 3a','CKD 3b','CKD 4','CKD 5') and documented_ckd in ('No','None') then 1 else 0 end)
- High Risk Patients: sum(case when actual_ckd_stage in ('CKD 4','CKD 5') and sees_nephrology=false then 1 else 0 end)
- Undocumented CKD Rate: (care gap patients) / (patients with ckd)
- Avg GFR: avg((gfr_1 + gfr_2 + gfr_3) / 3)
- Avg Creatinine: avg((creatinine_1 + creatinine_2 + creatinine_3) / 3)
- Pct Seeing Nephrology: count(case when sees_nephrology then 1 else 0 end) / count(1)
```

### AI Query Prompt

```
Create a table that scores the clinical notes (from {catalog}.clinical.clinical_notes) 
using the ai_query function. For each note, use the Llama 3.3 70B model to extract:
1. Whether the note indicates CKD per KDIGO staging rules
2. The suggested KDIGO stage (like CKD 3b, or None)
3. Whether the note mentions a nephrology referral

Return the result as JSON in this format:
{
  "indicates_ckd": "Yes" or "No",
  "suggested_stage": "CKD 3a" or similar,
  "mentions_nephrology": "Yes" or "No"
}

Parse that JSON and join back to the registry table so you can compute a flag: 
ai_flag_undocumented = true if (ai_indicates_ckd='Yes' AND documented_ckd in ('No','None')).

Score a 200-note sample for the workshop. The table should be named {catalog}.clinical.notes_ckd_signals
```

## Facilitator Tips & Tiered Hints

### Group is stuck on the metric view

**L1 (warmup)**: "Use the dimensions from the source table directly. For the Care Gap dimension, write a CASE statement: if actual stage is 3-5 AND documented is No/None, that is a care gap."

**L2 (nudge)**: "The MEASURE() functions count and sum. For high-risk count, use SUM(CASE WHEN ... THEN 1 ELSE 0 END). For rate, divide one measure by another."

**L3 (show structure)**: "Here is the schema:
```yaml
dimensions:
  - name: Actual Stage
    expr: actual_ckd_stage
measures:
  - name: Patient Count
    expr: COUNT(1)
```
Fill in the rest."

**L4 (close to done)**: Show the full metric view SQL file from `solutions/01-ckd/01_metric_view.sql` so they can cross-check their YAML structure.

### Group is stuck on the ai_query function

**L1**: "ai_query lets you ask an LLM a question inside SQL. The result is a string (the LLM's response). If you want structured output, wrap it in from_json()."

**L2**: "Your prompt should be specific: 'Is this note about CKD? What stage? Does it mention nephrology?' The LLM will return a JSON object."

**L3**: "The from_json syntax is `from_json(ai_query(...), 'STRUCT<field1: STRING, field2: STRING, ...>')`. Parse the response into a struct so you can extract individual fields."

**L4**: "If the LLM response is malformed JSON, ai_query can throw an error. If that happens, use ai_extract instead (same model, but returns an array of predictions). See the gotchas section below."

### Group is stuck on creating the Genie Agent

**L1**: "The Genie Agent is a REST API call. Use the CLI or a Python script to POST to `/api/2.0/data-rooms/`."

**L2**: "You need: display_name, warehouse_id (serverless ID from your workspace), table_identifiers (list the metric view and the base table), run_as_type='VIEWER'."

**L3**: "If the API returns 403, check that your token has the right permissions and the warehouse exists. If it returns 400, check the JSON syntax."

**L4**: "Use this curl command to create the space:
```bash
curl -X POST https://<databricks_instance>/api/2.0/data-rooms/ \\
  -H 'Authorization: Bearer <token>' \\
  -d '{\"display_name\": \"CKD Care Gap Discovery\", \"warehouse_id\": \"<id>\", \"table_identifiers\": [...]}' 
```
"

### Known Gotchas

1. **Metric View MEASURE() usage**: Measures MUST use aggregate functions (COUNT, SUM, AVG, etc.). If you write `expr: care_gap` (a dimension), the view creation will fail. Use `SUM(CASE WHEN care_gap = 'Care Gap' THEN 1 ELSE 0 END)`.

2. **ai_query JSON parsing**: If the LLM returns prose instead of JSON, `from_json` will throw an error. Always prefix the prompt with "Return ONLY a JSON object, no prose." If errors persist, switch to `ai_extract` (more forgiving but sometimes returns nulls).

3. **ai_extract inconsistent nulls**: `ai_extract` has known issues with null fields. Use `ai_query` with a directed prompt and `from_json` for the CKD solution.

4. **Genie Agent on Volumes (Beta)**: To attach clinical notes as unstructured files, use Genie Agent on Volumes. This is Beta, so limits may apply (roughly 10 volumes, up to ~100GB total). Reference: see the feature-status file.

5. **Epic write-back question**: Leadership has asked about writing stage recommendations back to Epic via the EHR's ADT interface. This is outside the workshop scope but achievable via a downstream job + FHIR/HL7 adaptor. Mention it as a "production roadmap" item.

6. **Genie Code limitations**: Genie Code can help draft metric views and dashboards, but can't drive headless tests. Always verify the final assets by querying them in SQL or through the UI.

## Production Path (Attendees Will Ask)

For this use case, the production story includes:

- **Unity AI Gateway** (GA): Scope the `ai_query` calls to individual models and set rate limits/budgets. CKD is PHI-adjacent, so governance is critical.
- **RBAC + Audit**: The care-gap cohort identifies vulnerable patients. Use Unity Catalog grants and system tables to audit who runs queries.
- **Lakeflow Connect**: For real ingestion, consume the Epic FHIR feed via Lakeflow Connect (replacing manual synthetic data).
- **MLflow Evaluation**: Log the precision/recall of the AI extraction in MLflow so you can track model quality over time and trigger retraining if needed.
- **Genie-on-Volumes Beta caveat**: If you expand to analyze the full clinical-notes corpus, Genie-on-Volumes is currently Beta, so test it thoroughly before committing to SLA.
