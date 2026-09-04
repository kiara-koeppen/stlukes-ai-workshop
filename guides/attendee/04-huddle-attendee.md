# AI Huddle Management: Attendee Guide

## The Problem (TL;DR)

South Clinic runs a morning triage huddle each day. Patients are not pre-assigned to providers; instead, providers choose who they want to see based on the patient's visit complexity, psychosocial factors, existing relationships, and their own capacity. Right now, this assignment is done verbally in the huddle with no written record, no optimization, and no way to track whether assignments were good. St. Luke's wants to: (1) extract assignment factors from Teams transcripts automatically, (2) capture physician assignments in real time, and (3) measure assignment quality (was the patient paired with an optimal provider?).

## What You'll Build + Which Databricks Assets

Over the next 3-4 hours, you'll build an end-to-end huddle-board system. The app is the centerpiece; the data layer uses Databricks assets to power it:

- **Unstructured -> Structured (AI Functions):** Parse Teams huddle transcripts to extract complexity, psychosocial factors, and relationship context (11 factors, AI-driven).
- **Metric Views** (Unity Catalog): Aggregates huddle data by patient/provider/complexity band, measures assignment quality.
- **Genie Agent** (natural-language SQL): Query "Which patients have high psychosocial complexity today?" or "What's the workload per provider?"
- **AI/BI Dashboard** (Lakeview): Huddle summary (complexity distribution, assignment balance, assignment quality).
- **(Centerpiece) Databricks App:** The huddle board UI. Physicians see the patient roster (with AI-extracted complexity + relationships), enter their own complexity + relationship assessments, and click "Assign". The app writes to a database (Delta in workshop, Lakebase in production) and renders an assignment summary.

## Genie Code Prompts to Get Started

These are natural-language queries you'll ask a Genie Agent to explore the huddle data:

### Prompt 1: High-Complexity Patients
```
Show me all patients from today's huddle with high visit complexity or high psychosocial complexity. 
Include their names, complexity projection, and which provider they're assigned to.
```
Genie will find the high-complexity cases so providers can decide who to prioritize.

### Prompt 2: Provider Workload Balance
```
How many patients is each provider assigned to today? Order by count descending to see if the workload is balanced.
```
This helps identify if one provider is overloaded.

### Prompt 3: Assignment Quality
```
How many patients today were assigned to their optimal team member?
```
This measures whether assignments matched the relationship/complexity logic.

### Prompt 4: Psychosocial Drill
```
Which patients today have high psychosocial complexity? Show their names and current assignments.
```
These patients need careful provider matching; psychosocial fit matters as much as clinical fit.

### Prompt 5: Relationship Context
```
Show me patients with strong existing relationships to their assigned providers. 
How many assignments are relationship-optimal?
```
Genie correlates provider-patient relationship scores to see if assignments leverage existing trust.

## From POC to Production

### Architecture: Delta (Workshop) vs. Lakebase (Production)

**Workshop:** Your app writes physician inputs to a Delta table (`physician_inputs`). Delta is fast and sufficient for POC testing.

**Production path:** Move to **Lakebase Provisioned** (Databricks managed PostgreSQL) for the following reasons:

1. **Transactional consistency:** If two providers submit assignments for the same patient at the same time, Lakebase ensures they don't overwrite each other (ACID transactions). Delta can have write conflicts.
2. **HIPAA compliance:** Lakebase is encrypted at rest, has audit trails, and role-based access. It's the compliance-aligned choice for patient data.
3. **Low-latency writes:** Huddle board app needs sub-second write latency. Lakebase direct SQL inserts are faster than Delta writes for real-time app use.
4. **Synced analytics:** Set up a Lakeflow synced table from Lakebase -> Delta, syncing every 5 minutes. The app writes to Lakebase; Genie Agent and AI/BI dashboard query Delta.

**Prod architecture:**
```
Huddle Board App (writes)
    |
    +--> Lakebase Postgres (fast transactional storage, HIPAA-aligned)
         |
         +--> Lakeflow synced table -> Delta (analytics)
              |
              +--> Genie Agent (queries)
              +--> AI/BI Dashboard (queries)
              +--> MLflow evaluation (scores assignments)
```

### Unstructured Data: Teams Transcript Ingestion

**Workshop:** You manually place .txt transcript files in a UC Volume (`/Volumes/.../transcripts/`). The AI extraction job reads them on demand.

**Production path:**

1. **Lakeflow Connect (Beta):** Automatically sync Teams huddle transcripts from OneDrive to a UC Volume on a schedule (e.g., post-huddle).
2. **Genie-on-Volumes (Beta):** Attach the transcript Volume to your Genie Agent. Genie can then answer questions like "What was the main concern raised about patient 123 in the huddle?" and parse transcripts on the fly. Note: This is BETA, so set expectations around file types (currently .pdf, .txt, .docx support) and rate limits.
3. **Daily extraction job:** After Lakeflow syncs new transcripts, a Databricks job runs the AI extraction (`ai_query` on new files), populates `transcript_extractions`, updates the metric view. Physicians get a Slack notification: "Huddle data is ready; open the huddle board."

### Evaluation & Tuning: Are Extractions Helping?

After running 50 huddles (~50 days), measure whether the AI-extracted complexity factors actually match physician judgment:

1. **Evaluation dataset:** Compare extracted `visit_complexity_projection` (Low/Moderate/High) to physician input `patient_complexity_score` (-10 to 10) for all 50 huddles.
2. **Scorer function:** Custom MLflow scorer: "Is extracted complexity correlated with physician complexity?" (target: Spearman correlation >= 0.7).
3. **If correlation is weak:** Retune the extraction prompt (e.g., "Focus on chief complaint and age as proxies for complexity") or experiment with a different AI model for `ai_query`.
4. **Iterate:** Every quarter, re-evaluate and improve the extraction prompts based on physician feedback.

### Expansion: Multi-Clinic Huddles

**Phase 1 (current):** South Clinic, one morning huddle per day.

**Phase 2 (expand):** Add North Clinic, Boise Clinic, etc. Each clinic has its own huddle schedule. The metric view groups by clinic (add `clinic` dimension) so you can ask: "Which clinic has the most suboptimal assignments?" and identify patterns.

**Phase 3 (ML auto-assignment):** Once you have 100+ historical huddles, train an ML model (using PySpark / MLlib) to predict optimal provider for a given patient (input: complexity, psychosocial factors, relationship history, provider capacity). The app can then suggest assignments automatically, which physicians can override.

### Governance & Access Control

**Workshop:** You're building with synthetic patient data (no real PHI). In production, controlled-substance investigations, PHI, and assignment records are sensitive.

**Production access:**
- **Huddle board app:** Only South Clinic physicians + staff (OBO authentication via their Databricks account).
- **Genie Agent:** Only South Clinic team; logged queries for audit.
- **Metric view:** SELECT-only for clinicians; no direct access to raw transcripts (parsed factors only).
- **Lakebase physician_inputs:** Transactional access scoped to the authenticated user + audit trail (created_by, created_at, updated_at).
- **MLflow evaluation:** Data science team only; used to improve extraction prompts.

### Future: Epic Integration & Reverse ETL

**Long term:** After the huddle, the assigned provider opens the patient's Epic chart. Rather than manually copying the assignment, a reverse ETL job (e.g., dbt Cloud + Workato) pushes the assignment back to Epic's "provider assignment" field. This closes the loop: huddle board -> Epic -> chart -> visit.

## Key Assumptions & Constraints

- **Synthetic patient data for the workshop:** Real demographics come from Epic Clarity. The 18 patients here are synthetic with realistic visit reasons, ages, and complexity distribution.
- **Synthetic transcripts:** Real huddles are recorded on Teams. The transcripts here are AI-generated summaries of realistic huddle discussions. In production, ingest real Teams recordings via Lakeflow Connect.
- **Three providers, one morning:** The planted signal is a realistic South Clinic morning with 3 attending physicians, 18 patients, and 2-3 high-complexity cases. This is enough to show assignment optimization.
- **Extraction factors:** The 11 extraction fields (complexity, psychosocial, social determinants, relationship context, etc.) come from Drake's huddle playbook. In production, confirm the fields match your clinic's workflow.
- **Metric view "Patient Count" note:** The metric view currently counts distinct patients in `physician_inputs`. If multiple providers score the same patient, it still counts as 1 patient (not 2 assessments). This is correct for huddle summary analytics.

## Troubleshooting

**Q: My transcript extraction is slow or returns NULL fields.**
A: The `ai_query` + JSON parsing is synchronous. For 18 small transcripts, expect 20-30 seconds. If a transcript fails (NULL fields), the most common cause is:
- **Malformed JSON:** The LLM wrapped the JSON in prose (e.g., "Here is the JSON: {...}"). The parser tries to extract `{...}` via regex; if it fails, that row is NULL.
  - **Fix:** Re-run with a clearer prompt: "Respond with ONLY a JSON object. No prose. No code fences. Example: {...}".
  - **Fallback:** In production, log failures and retry with a different model.

**Q: The metric view seems slow.**
A: The metric view sources from `physician_inputs` (~34 rows). If it's slow, it's likely because Genie is querying the raw `patient_demographics` table (18 rows) instead of the pre-aggregated metric view. Recommend: "Show me Huddle Summary (via the metric view) instead of raw patients."

**Q: Can I see what Genie generated as SQL?**
A: Yes! In Genie, after you ask a question, click "View SQL" to see the translation. Copy it into a SQL notebook to debug or refine.

**Q: What if a patient's extracted complexity doesn't match what the physicians say?**
A: The extraction is driven by the huddle transcript (what was discussed). If physicians disagree, they can override the extracted score with their own `patient_complexity_score` in the app. The metric view will use the physician input. This is by design: AI extraction is a starting point, physician judgment is authoritative.

**Q: How do I productionize the assignment logic?**
A: Phase 1 (current): Manual assignment (physicians choose). Phase 2: Add a "recommend optimal provider" field in the app (deterministic logic based on complexity + relationship + capacity). Phase 3: ML-driven recommendations (train a model on 100+ historical huddles). Start with Phase 1; expand in Q1 2027 if the POC is successful.
