# AI Huddle Management: Instructor Cheatsheet

## TL;DR of the Problem

South Clinic's morning triage huddle runs daily. Patients are not pre-assigned to providers; providers choose who to see based on visit complexity, existing relationships, and psychosocial factors. Currently, the assignment is manual, based on a verbal discussion and individual provider memory. The goal: combine Epic demographics, AI-extracted transcript factors, and physician input to optimize assignment and track assignment quality (optimal vs. suboptimal).

## The Solution We Built

An end-to-end huddle board (Databricks App centerpiece) that ingests Teams transcripts, extracts structured complexity factors, lets physicians input relationship/complexity scores and assignments, and surfaces an assignment summary dashboard. The data layer is built for both POC (Delta writeback) and production (Lakebase Postgres with synced analytics).

**Verified assets (kk_test, 2026-09-15):**
- **Tables:** `kk_test.huddle.patient_demographics` (18 patients), `transcript_extractions` (18 rows, 100% parsed from Teams transcripts), `physician_inputs` (34 rows, 3 providers on one South Clinic morning huddle)
- **Metric View:** `kk_test.huddle.huddle_metrics` (dimensions: Huddle Date, Provider, Complexity Band, Relationship Band, Assignment Match; measures: Patient Count, Avg Patient Complexity Score, High Complexity Count, Strong Relationship Count, Optimal Assignment Count)
  - **NOTE:** Patient Count measure currently counts input rows, not distinct patients. This is a known artifact of the workshop table schema; production fix documented below.
- **AI Functions table:** `kk_test.huddle.transcript_ai_extractions` (18 rows, 18/18 transcripts successfully parsed via `ai_query` + `regexp_extract` JSON grab)
- **Genie Agent space_id:** `01f1a88caa171f01b6a7ad343d28dfe3` (verified: "Highest complexity patients today, complexity score 9")
- **AI/BI Dashboard:** `01f1a88db4291b848e5cdd4e4e0fc880` (huddle summary: complexity distribution, provider workload, assignment quality)
- **(Centerpiece) Databricks App:** huddle-board UI (stretch for workshop; full build in production)

## How to Build It (Ordered Steps)

### Step 1: Load Synthetic Huddle Data
Participants run the data-generator notebook (parameterized catalog/schema via `dbutils.widgets`). It creates:
- `patient_demographics`: 18 rows, one realistic South Clinic morning (2026-09-15). Mix of complexity: 2-3 high-complexity, 5-6 moderate, rest low. Age range 18-85, equal gender split, scheduled reasons (follow-up, new symptom, chronic management).
- Synthetic **Teams huddle transcript** (.txt files) in a UC Volume (`/Volumes/kk_test/huddle/transcripts/`). Each transcript named `PAT-{pat_id}_huddle_2026-09-15.txt`, contains verbal discussion of the patient (complexity, psychosocial factors, existing relationships). 18 transcripts, each 200-500 words.

**Verification queries:**
```sql
SELECT COUNT(*) FROM kk_test.huddle.patient_demographics;
-- Expected: 18

SELECT COUNT(*) FROM read_files('/Volumes/kk_test/huddle/transcripts/', format=>'text');
-- Expected: 18 files
```

### Step 2: Extract Structured Factors from Transcripts
Participants run `solutions/04-huddle/02_ai_functions.sql`. This creates `transcript_ai_extractions` table:
- Reads each transcript from the Volume via `read_files(..., format=>'text')`.
- Calls `ai_query` with a prompt: "Extract visit_complexity_projection, psychosocial_complexity_projection, social_determinants_of_health, relationship_context. Respond with ONLY JSON, no prose."
- Parses the JSON response via `from_json` + `regexp_extract('[{][^}]*[}]', 0)` (robust grab of JSON from prose, handles model wrapping).
- Extracts `pat_id` from the filename (regex: `PAT-[A-Z0-9]+`).

**Verification:**
```sql
SELECT COUNT(*) FROM kk_test.huddle.transcript_ai_extractions WHERE pat_id IS NOT NULL;
-- Expected: 18 (all parsed successfully)

SELECT * FROM kk_test.huddle.transcript_ai_extractions WHERE pat_id = 'PAT-001';
-- Expected: one row with complexity_projection (Low/Moderate/High), psychosocial_projection, etc.
```

### Step 3: Create the Metric View
Participants create the metric view `huddle_metrics` from `solutions/04-huddle/01_metric_view.sql`. The YAML metric view reads from `physician_inputs` and encodes:
- **Dimensions:** Huddle Date, Assigned Team Member, Optimal Team Member, Provider, Complexity Band (High if score >= 5), Relationship Band (Strong if score >= 5), Assignment Match (Optimal if optimal == assigned).
- **Measures:**
  - `Patient Count`: COUNT(DISTINCT pat_id) [NOTE: workshop schema counts input rows; prod fix below]
  - `Avg Patient Complexity Score`, `Avg Relationship Score`: averages.
  - `High Complexity Count`, `Strong Relationship Count`, `Optimal Assignment Count`: categorical counts.

**Verification:**
```sql
SELECT * FROM kk_test.huddle.huddle_metrics
WHERE "Huddle Date" = '2026-09-15'
ORDER BY "Avg Patient Complexity Score" DESC;
-- Expected: metrics for that day, breakdown by provider/complexity.
```

### Step 4: Create Genie Agent
Participants use the Genie UI or REST API to create a Genie Agent pointing to:
- Tables: `patient_demographics`, `transcript_extractions`
- Metric view: `huddle_metrics`
- Optional: unstructured transcripts in Volumes (Genie-on-Volumes, Beta).

**Genie Agent creation (REST):**
```bash
POST /api/2.0/data-rooms/
{
  "display_name": "AI Huddle Management",
  "warehouse_id": "c68a614580fefe22",
  "table_identifiers": [
    "kk_test.huddle.patient_demographics",
    "kk_test.huddle.transcript_extractions",
    "kk_test.huddle.huddle_metrics"
  ],
  "run_as_type": "VIEWER",
  "description": "Huddle complexity, assignment optimization, and provider workload."
}
```

### Step 5: Deploy AI/BI Dashboard
Participants import `solutions/04-huddle/03_dashboard.lvdash.json` into AI/BI. Dashboard includes:
- Complexity distribution (pie or bar chart).
- Provider workload (number of patients per provider).
- Assignment quality (optimal vs. suboptimal assignment count).
- Drill-through to individual patient (demographics + extracted complexity factors + assigned provider).

**Verification:** Open the dashboard for huddle_date = 2026-09-15, verify you see ~18 patients, 2-3 high-complexity, assignment balance across 3 providers.

### Step 6: Create Huddle Board App (Databricks Apps)
Participants scaffold a Databricks App (apx) with:
- **Backend:** FastAPI endpoints to query patient_demographics + transcript_extractions, fetch existing physician_inputs, and store new inputs (to Delta in workshop, Lakebase in production).
- **Frontend:** React UI with two sections:
  1. **Patient roster** (table): columns pat_name, age, scheduled_visit_reason, visit_complexity_projection, psychosocial_complexity_projection, relationship_context (from extractions).
  2. **Assignment form** (per patient): provider name, relationship_score (-10 to +10), complexity_score (-10 to +10), notes, optimal_team_member (from the app's logic), assigned_team_member (physician input).
- **Genie integration:** Optional Genie Conversation API query: "For this patient, who has the strongest relationship in the clinic?" Genie reasons over the metric view.
- **Writeback:** Submit button saves physician_input row to Delta (`physician_inputs` table) or Lakebase.

This is the art-of-the-possible and workshop stretch; full build is shown in the solution repo, but participants may scaffold the backend/frontend structure.

## Genie Code Prompts That Land the Solution

Use these in a Genie Agent to navigate the data:

1. **Find high-complexity patients:**
   ```
   Show me all patients from the 2026-09-15 huddle with visit_complexity_projection = 'High' 
   or psychosocial_complexity_projection = 'High'. Include their names and assigned providers.
   ```
   Expected: 2-3 rows, showing which patients are high-complexity and who they're assigned to.

2. **Provider workload:**
   ```
   How many patients is each provider assigned to on 2026-09-15? Order by count descending.
   ```
   Expected: 3 providers, roughly balanced (6, 6, 6) or (5, 6, 7) to show real distribution.

3. **Assignment quality:**
   ```
   On 2026-09-15, how many patients were assigned to their optimal team member?
   ```
   Expected: a count; if <75%, suggests suboptimal assignments due to relationship constraints.

4. **Psychosocial drill:**
   ```
   Which patients today have high psychosocial complexity or significant social determinants of health?
   ```
   Expected: Genie returns rows with psychosocial_complexity = High or notes on social drivers.

5. **Relationship context:**
   ```
   Show me patients with strong existing provider relationships. Who should they be assigned to?
   ```
   Expected: Genie correlates relationship_score >= 5 with provider assignment, recommends optimal matches.

## Facilitator Tips + Tiered Hints

### L1 (Data Loaded)
If a participant is stuck after Step 1:
- Confirm `SELECT COUNT(*) FROM kk_test.huddle.patient_demographics;` returns 18.
- Spot-check transcript volume: `SELECT _metadata.file_path FROM read_files('/Volumes/kk_test/huddle/transcripts/', format=>'text') LIMIT 5;` shows PAT-*.txt files.

### L2 (Transcript Extraction Works)
If `transcript_ai_extractions` is created but rows are NULL or JSON parsing fails:
- **Gotcha:** `ai_query` + `regexp_extract` JSON grab is brittle. The model may wrap JSON in prose (e.g., "Here is the JSON: {...}"), so `regexp_extract('[{][^}]*[}]', 0)` pulls the first `{...}` substring. If the model returns `"json": {...}`, the regex may fail.
  - **Fix:** Adjust prompt to emphasize "ONLY a JSON object, no prose, no code fences, no explanation."
  - **Fallback:** If a transcript fails to parse (NULL fields), the metric view will still work (GROUP BY will exclude that row from aggregations). In production, log failed parses and retry with a different model.
- Verify one row: `SELECT * FROM kk_test.huddle.transcript_ai_extractions LIMIT 1;` should show non-null visit_complexity_projection, psychosocial_complexity_projection, etc.

### L3 (Metric View + Physician Input)
If the metric view works but "Patient Count" is wrong:
- **Gotcha:** The huddle_metrics metric view sources from `physician_inputs`, which may have multiple rows per patient (e.g., if a physician re-enters their input or multiple physicians score the same patient). The `Patient Count` measure uses `COUNT(DISTINCT pat_id)` in the YAML, but the workshop table has 34 rows for 18 patients (avg ~1.9 inputs per patient).
  - **Expected behavior:** SELECT "Patient Count" FROM huddle_metrics returns 18 distinct patients, not 34.
  - **Gotcha in production:** If a patient is scored by multiple providers (for second opinion), the metric view will count them once. The Optimal Assignment field may be ambiguous (two different providers, two different optimal_team_members). Document this in the metric view comment for production.

### L4 (Genie Agent + App)
- **Genie Agent scope:** Include `transcript_extractions` and `huddle_metrics` (NO raw `physician_inputs` if it's going to be real PHI; the metric view is already aggregated and HIPAA-friendly).
- **App authentication:** Use OBO (on-behalf-of) with the logged-in user's token so physician_inputs.created_by or created_at can be tracked for audit.
- **Delta vs Lakebase:** In the workshop, writes go to Delta. Emphasize that production uses Lakebase Postgres (next section) for transactional consistency and HIPAA compliance.

## Gotchas & Production Notes

1. **Patient Count Metric (Known Workshop Artifact):**
   The huddle_metrics metric view's "Patient Count" measure is defined as `COUNT(DISTINCT pat_id)`. However, if `physician_inputs` has multiple rows per patient (e.g., two providers score the same patient), the measure will still return the count of distinct patients, not input rows. This is correct for analytics but may confuse participants who see 34 input rows and expect "Patient Count" = 34. Clarify: "Patient Count is the number of unique patients, not the number of physician assessments."

   **Production fix:** Store assessments separately (e.g., `physician_assessments` table with provider_id + pat_id + scores), then join to `physician_inputs` (which holds the final assignment). The metric view would then count distinct patients, not assessments.

2. **Transcript AI Extraction Limitations (Genie-on-Volumes, BETA):**
   The workshop uses `read_files(..., format=>'text')` to ingest transcripts and `ai_query` to parse them. This is synchronous and works for 18 small files. In production:
   - **Lakeflow Connect (beta):** Ingest Teams transcripts directly from OneDrive on a schedule (daily).
   - **Genie-on-Volumes (BETA):** Attach the transcript Volume to the Genie Agent; Genie can query "What was mentioned about patient complexity in the huddle?" and it will parse transcripts on the fly. Note: BETA, so set expectations around rate limits and file-type support.

3. **Lakebase for Physician Input Writeback (Production Path):**
   The workshop writes to Delta (`physician_inputs` Delta table). Production should use **Lakebase Provisioned** for the following reasons:
   - **Transactional consistency:** If two providers submit assignments for the same patient simultaneously, Lakebase ensures serialization (via ACID transactions). Delta can have write conflicts.
   - **HIPAA compliance:** Lakebase is a managed Postgres instance with encryption at rest, audit trails, and role-based access. Delta in UC is secure but Lakebase is the HIPAA-aligned choice for patient data.
   - **Low-latency reads:** The huddle board app needs sub-second response times. Lakebase direct queries are faster than Delta lakehouse queries for OLTP workloads.
   - **Synced analytics:** Set up a Lakeflow synced table from Lakebase -> Delta, syncing daily. Genie Agent and AI/BI dashboard query Delta (analytics), while the app writes to Lakebase (transactional).

   **Prod architecture:**
   ```
   Huddle Board App (FastAPI)
     |
     +-> Lakebase Postgres (physician_inputs, transactional)
     |    |
     |    +-> Lakeflow synced table -> Delta (analytics)
     |
     +-> Genie Agent (queries Delta + metric view)
     |
     +-> AI/BI Dashboard (queries Delta)
   ```

4. **MLflow Evaluation of Transcript Extraction:**
   After running 50 huddles, measure whether the AI-extracted complexity factors are predictive of actual assignment difficulty:
   - **Evaluation dataset:** Huddles 1-50; for each patient, compare extracted `visit_complexity_projection` (Low/Moderate/High) to the physician's input `patient_complexity_score` (-10 to 10).
   - **Scorer:** "Does extracted complexity correlate with physician complexity score?" (Spearman rho or simple agreement %).
   - **Fine-tune:** If correlation is <0.7, retune the extraction prompt or experiment with a different model for ai_query.

5. **Transcript Ingestion Workflow (Future):**
   - **Teams integration:** Huddles are recorded on Teams. After each huddle, the app sends a Teams API call to download the transcript (.vtt or .txt) to the Volumes.
   - **Lakeflow Connect:** Automated sync from Teams OneDrive -> UC Volumes, running post-huddle.
   - **Trigger:** New transcript -> Databricks job runs `ai_extract` on all new transcripts, populates `transcript_extractions`, updates the metric view. Physicians get notified the huddle data is ready.

## Expected Outcomes

By the end, participants will have:
- Extracted complexity factors from 18 unstructured Team transcripts in ~20 seconds (ai_query + JSON parsing).
- Built a metric view that answers "Which patients are high-complexity today?" and "Is the assignment workload balanced?"
- Queried Genie Agent: "Show me high-complexity patients with weak provider relationships" (natural-language drill).
- Seen a dashboard of huddle metrics (complexity distribution, assignment quality, provider workload).
- Understood the architecture: transcript -> AI extraction -> metric view -> Genie Agent + dashboard + app.
- (Stretch) Built the start of a Databricks App for the huddle board, with writeback to Delta (or Lakebase in full prod).

The planted signal: one realistic South Clinic morning with 2-3 high-complexity patients, 2-3 providers, and a mix of strong/neutral/weak relationships. The assignment logic shows: "Optimal assignments improve when psychosocial factors and relationships are considered alongside complexity." The app is the centerpiece, demonstrating a production-ready POC of the full workflow.
