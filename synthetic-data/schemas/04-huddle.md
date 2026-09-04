# AI Huddle Management — Data Spec

**Prod target:** `healthcare_ai.huddle.*` (schema "designed to best support the workflow" per Drake's doc)
**Workshop build:** `kk_test.huddle.*`
**Grounded in:** Drake's `AI Huddle Management.docx`. **NEW use case that replaced Nursing Position Control.** Drake's group; trending toward production. PHI (patient-level). Explicitly names Databricks Apps + AI extraction + Lakebase.

## The problem (what the AI must do)
The South Clinic (Nampa) R&D clinic runs a morning triage huddle. Patients are NOT pre-assigned to providers; providers choose who to see based on visit complexity, existing relationships, and psychosocial factors. The tool combines **Epic Clarity demographics + Teams huddle transcripts + physician input** to support assignment, then organizes results into a table/dashboard. Future: ML auto-assigns patients to providers.

## Tables
### `patient_demographics` (from Epic Clarity `clarity.dbo.patient`)
- `pat_id` STRING, `pat_name` STRING (synthetic), `birth_date` DATE, `home_phone` STRING, `age` INT, `sex` STRING
- `clinic` STRING (South Clinic / Nampa), `huddle_date` DATE, `scheduled_visit_reason` STRING

### `transcript_extractions` (AI-extracted from Teams transcripts — the 11 business-defined factors)
One row per patient per huddle_date, columns exactly as the business named them:
- `visit_complexity_projection`, `provider_identified_issues`, `medical_drivers`, `patient_identified_issues`,
  `history_of_job_modifications`, `psychosocial_complexity_projection`, `social_determinants_of_health`,
  `hidden_contextual_factors`, `negotiability`, `relationship_context`, `relationship_equity_with_care_team`
- plus `pat_id`, `huddle_date`, `source_transcript_file`

### `physician_inputs` (writeback — Delta in the workshop, **Lakebase in production**)
- `pat_id`, `huddle_date`, `provider_id`, `provider_name`
- `provider_patient_relationship_score` INT (-10..10)
- `patient_complexity_score` INT (-10..10)
- `physician_notes` STRING (optional free text)
- `optimal_team_member` STRING, `assigned_team_member` STRING, `non_optimal_assignment_notes` STRING
- `created_at` TIMESTAMP

## Workshop build vs production (per Kiara: Lakebase is the prod path)
- **Workshop:** physician inputs write to a Delta table `kk_test.huddle.physician_inputs`; the app reads/writes it. Fast, no extra infra.
- **Production path (documented, and shown in the CKD/leadership story):** physician inputs write to **Lakebase Postgres** (OLTP, low-latency, transactional) via the App's OAuth managed credentials, with a synced table back to Delta for analytics. This is the "turn POC into production" section for this use case.

## Assets to build
- **Unstructured -> structured:** synthetic **Teams huddle transcripts** (.txt/.vtt) in a Volume; `ai_extract` / `ai_query` populates `transcript_extractions`. Also feeds Genie-on-Volumes.
- **App (the centerpiece):** morning-huddle UI. Shows the day's patient list (demographics + extracted factors), lets a physician enter relationship/complexity scores + assignment, writes to Delta (Lakebase in prod), then renders the organized huddle board / assignment table.
- **Genie Agent:** over demographics + extractions + inputs ("which patients have high psychosocial complexity today?").
- **AI/BI dashboard:** huddle summary (complexity distribution, assignment balance across providers).

## Planted signal
One realistic South Clinic morning: ~15-20 patients for a given `huddle_date`, a few clearly high-complexity / high-psychosocial, a couple with strong existing provider relationships, so the assignment logic + "optimal vs assigned" story is visible. 2-3 providers.
