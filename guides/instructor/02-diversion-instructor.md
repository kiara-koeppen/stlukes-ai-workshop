# Medication Diversion Support: Instructor Cheatsheet

## TL;DR of the Problem

Diversion investigations consume 3-5 manual days per case. Investigators manually build Excel pivots and color-code to compare a suspected employee's medication activity (dispense, administer, waste, return) against peer exemplars, flag anomalies across shifts and over time, and document findings. The Diversion Support Team runs 1-6 investigations per month.

## The Solution We Built

A peer-benchmarked anomaly detection system that ranks employees by composite risk and generates investigation narratives in seconds.

**Verified assets (kk_test, 2026-09-04):**
- **Tables:** `kk_test.med_diversion.medication_activity` (45,000 events), `employee_risk` (50 employees), `peer_group` (10 cohorts)
- **Metric View:** `kk_test.med_diversion.diversion_metrics` (peer-benchmark measures: Dispense Count, Waste Without Witness CII, Administration Without Order, Opioid Low Pain Score, Off-Shift Activity, Composite Anomaly Score, etc.)
- **AI Functions table:** `kk_test.med_diversion.investigation_narratives` (top 5 employees by composite anomaly; the 4 planted diverters occupy the #1-4 spots; narratives generated via `ai_query` peer-benchmarked reasoning)
- **Genie Agent space_id:** `01f1a88ca9ab13638e9123eb9a0edf4b` (verified: "Top 5 are EMP-00001 through EMP-00005; planted diverters dominate the ranking")
- **AI/BI Dashboard:** `01f1a88db3721dc383ea706b9d78854a` (investigation dashboard showing anomaly heatmaps, employee rankings, peer comparisons)

## How to Build It (Ordered Steps)

### Step 1: Load Synthetic Data
Participants run the data-generator notebook (parameterized catalog/schema via `dbutils.widgets`). It creates:
- `medication_activity`: 45k rows of Omnicell (dispense/waste/return) + Epic (administer/orders/pain-scores) unified events, with planted signal: 4-5 employees whose combined anomalies are ~50-60% above peer-group mean.
- `employee_risk`: 50 rows, IRIS scores from ControlCheck (synthetic).
- `peer_group`: 10 cohorts (by role + unit + shift).

**Verification query:**
```sql
SELECT COUNT(*) event_count FROM kk_test.med_diversion.medication_activity;
-- Expected: 45000

SELECT COUNT(*) FROM kk_test.med_diversion.employee_risk;
-- Expected: 50
```

### Step 2: Create the Metric View
Participants create the metric view `diversion_metrics` from `solutions/02-diversion/01_metric_view.sql`. The YAML metric view encodes the anomaly rules as measures:
- `Waste Without Witness CII`: waste transactions on controlled substances with no witness (compliance red flag).
- `Administration Without Order`: administer events with no matching provider order.
- `Opioid Low Pain Score`: opioid administrations when pain_score_before is null or <3 (no documented justification).
- `Off Shift Activity Count`, `Out Of Department Activity Count`: behavioral anomalies.
- **`Composite Anomaly Score`**: sum of the above five flags per employee.

**Verification:**
```sql
SELECT * FROM kk_test.med_diversion.diversion_metrics
WHERE Employee IN ('EMP-00001', 'EMP-00002', 'EMP-00003', 'EMP-00004')
ORDER BY "Composite Anomaly Score" DESC;
-- Expected: top 4 rows are the planted diverters
```

### Step 3: Create AI Functions (Investigation Narratives)
Participants run `solutions/02-diversion/02_ai_functions.sql`. This creates `investigation_narratives` table, which:
- Aggregates each employee's anomaly counts (waste-no-witness, admin-no-order, low-pain-opioid, off-shift, out-of-dept).
- Queries the IRIS score from `employee_risk`.
- Computes peer-group average anomalies.
- Calls `ai_query` with a prompt that generates a 3-sentence narrative, comparing the employee to the peer average, without accusatory language.

**Example output (EMP-00001):**
```
EMP-00001, Sarah Johnson, RN, Oncology
IRIS score: 8.9
Composite anomaly: 47
Narrative: "Sarah Johnson's medication activity in oncology shows 12 waste transactions without witnessed signatures on CII substances, compared to a peer average of 2.1. Additionally, 8 administrations lack matching provider orders, and 6 opioid administrations occurred with no documented pain scores. These patterns, combined with 4 off-shift activities, place her significantly above peer norms and warrant further investigation."
```

**Verification:**
```sql
SELECT employee_name, composite, investigation_narrative
FROM kk_test.med_diversion.investigation_narratives
LIMIT 5;
-- Expected: 5 rows with narratives, top 4 are planted diverters
```

### Step 4: Create a Genie Agent
Participants use the Genie UI or REST API to create a Genie Agent pointing to:
- Tables: `medication_activity`, `employee_risk`, `peer_group`
- Metric view: `diversion_metrics`
- Optional: unstructured Policy volumes (waste policy, investigation SOP)

**Genie Agent creation (REST):**
```bash
POST /api/2.0/data-rooms/
{
  "display_name": "Medication Diversion Support",
  "warehouse_id": "c68a614580fefe22",
  "table_identifiers": [
    "kk_test.med_diversion.medication_activity",
    "kk_test.med_diversion.employee_risk",
    "kk_test.med_diversion.peer_group",
    "kk_test.med_diversion.diversion_metrics"
  ],
  "run_as_type": "VIEWER",
  "description": "Medication diversion anomaly detection: peer benchmarking, rules-based flags, investigation narratives."
}
```

### Step 5: Deploy AI/BI Dashboard
Participants import `solutions/02-diversion/03_dashboard.lvdash.json` into AI/BI. Dashboard includes:
- Employee anomaly ranking (bar chart, Composite Anomaly Score).
- Heatmap of anomaly types by employee.
- Peer-group comparison (this employee vs average).
- Drill-through to investigation narrative.

**Verification:** Open the dashboard, run a filter on a planted diverter, verify the narrative appears.

### Step 6: Create Investigator App (Databricks Apps)
Participants scaffold a Databricks App (apx) with:
- **Backend:** FastAPI endpoints to query the metric view, fetch narratives, and store investigator notes.
- **Frontend:** React UI showing the employee ranking, anomaly breakdown, narrative, and a form for the investigator to document findings.
- **Genie integration:** Conversation API to ask "Is Sarah Johnson's waste pattern typical for her peer group?" and get natural-language reasoning.

This is the art-of-the-possible; the workshop focuses on the data layer (Steps 1-5). Apps are a stretch.

## Genie Code Prompts That Land the Solution

Use these in a Genie Agent to navigate the data:

1. **Find the top anomalies:**
   ```
   Show me the top 10 employees by Composite Anomaly Score, with their Dispense Count, Waste Without Witness CII, and Administration Without Order.
   ```
   Expected: EMP-00001 through EMP-00004 (planted diverters) at the top, plus realistic controls with lower scores.

2. **Peer benchmarking:**
   ```
   For employee EMP-00001, show me their Waste Without Witness CII, Opioid Low Pain Score, and Off Shift Activity Count compared to others in the Oncology department, Night shift.
   ```
   Expected: EMP-00001 is much higher than peer-group mean.

3. **Rules-based drill:**
   ```
   Which employees have Waste Without Witness CII on controlled substances? Order by count descending.
   ```
   Expected: Planted diverters in top 4.

4. **Narrative lookup:**
   ```
   What is the investigation narrative for the top 5 employees by anomaly score?
   ```
   Expected: Genie fetches from `investigation_narratives` table, returns narratives that compare to peer average.

5. **Temporal anomaly:**
   ```
   Which employees have the most Off Shift Activity Count?
   ```
   Expected: Behavioral red flag; planted diverters should rank high here too.

## Facilitator Tips + Tiered Hints

### L1 (Data Loaded)
If a participant is stuck after Step 1:
- Confirm `SELECT COUNT(*) FROM kk_test.med_diversion.medication_activity;` returns 45000.
- Spot-check: `SELECT DISTINCT employee_id FROM employee_risk LIMIT 5;` shows EMP-00001, etc.

### L2 (Metric View Query Works)
If metric view is created but query is slow or returns nulls:
- Check dimensions: `SELECT DISTINCT "Employee" FROM kk_test.med_diversion.diversion_metrics;` should show 50 employees.
- Check for GROUP BY scope: Metric view defaults to grouping by all dimensions; if too granular, drill may be slow. Confirm `"Composite Anomaly Score"` is non-null for a subset.
- **Gotcha:** Metric View `MEASURE()` aggregation requires correct context. If someone writes `SELECT * FROM diversion_metrics` without a dimension, they get all-nulls. Guide them to `SELECT "Employee", "Composite Anomaly Score" FROM diversion_metrics ORDER BY "Composite Anomaly Score" DESC LIMIT 10;`

### L3 (AI Functions Wired)
If `investigation_narratives` table creation fails or narrative is garbled:
- **Gotcha:** `ai_query` concatenates a multi-line prompt; if the prompt has unclosed quotes or CONCAT errors, the function fails. Check the SQL; watch for escaped quotes.
- **JSON parsing gotcha:** The huddle example (Step 3, not this use case, but relevant) uses `regexp_extract('[{][^}]*[}]', 0)` to grab JSON from prose. Diversion uses simple string concatenation, but if a narrative has newlines or special chars, ensure CONCAT properly escapes them.
- Verify: `SELECT COUNT(*) FROM kk_test.med_diversion.investigation_narratives;` should return 5. If it returns 0, the `ai_query` call timed out or errored; check the Genie query_history or re-run with a smaller LIMIT.

### L4 (Genie Agent + Dashboard)
- **Genie Agent tip:** Point only at the metric view + `investigation_narratives` table. Do NOT include raw `medication_activity` (45k rows makes Genie slow; the metric view is already aggregated).
- **Dashboard SQL gotcha:** The dashboard's `03_dashboard.lvdash.json` uses `diversion_metrics` + `investigation_narratives`. If the dashboard filter on "Employee" doesn't refresh, hard-refresh the browser; Lakeview's caching can lag.
- **Genie One stretch (optional):** If a participant wants to roll this up to a business-user surface, the Genie Agent is already the Genie One entry point.

## Gotchas & Compliance Notes

1. **PHI + Controlled Substance Sensitivity:** This is HR/legal territory. The narrative output intentionally avoids accusatory language ("patterns suggest" not "employee is diverting"). Remind participants: investigation_narratives are a *starting point*, not proof.

2. **Metric View `MEASURE()` Scoping:** The Composite Anomaly Score is a SUM across multiple CASE expressions. If someone queries it without dimensions, they get a single global sum. To get per-employee scores, always include `"Employee"` in the SELECT or GROUP BY.

3. **Timestamp Columns in Anomaly Detection:** The "Admin Before Order" measure compares `admin_datetime < order_datetime`. If these columns are mislabeled or NULL, the measure returns 0 even when there are genuine ordering issues. Verify the ETL via spot-checks:
   ```sql
   SELECT order_datetime, admin_datetime 
   FROM kk_test.med_diversion.medication_activity 
   WHERE event_type='administer' 
   LIMIT 10;
   ```

4. **IRIS Score Source:** `employee_risk.iris_score` is synthetic for this workshop. In production, it comes from Bluesight ControlCheck. The narrative prompt includes it as context ("IRIS risk score X"); if missing (NULL), the narrative still generates but with less supporting evidence.

5. **Genie Code responseFormat Constraint:** When using `ai_query` inside a table creation, Genie only handles one top-level result field. If you want narrative + a risk_level classification, nest them: `ai_query(...) AS narrative, EXTRACT(... FROM narrative) AS risk_level` (post-hoc). Do NOT call ai_query twice in one row.

## Expected Outcomes

By the end, participants will have:
- Ranked the 50 employees by composite anomaly in <1 second (metric view aggregation).
- Generated human-readable narratives for the top 5 (5-10 sec, via ai_query).
- Asked Genie Agent natural-language questions about peer benchmarking ("Is this person an outlier?") and gotten SQL reasoning back.
- Seen a dashboard visualization of the findings.
- Understood the link between explicit rules (the CASE expressions in the metric view) and AI reasoning (the ai_query narrative).

The planted signal is designed so the top 4 by composite anomaly score are the 4 intentional diverters. A fifth employee (control) is nearby but with a clearer pattern attribution (e.g., lots of off-shift, less waste-without-witness). The solution demonstrates that **rules-based anomaly flags + AI-generated peer contextualization** replaces 3-5 days of manual Excel work.
