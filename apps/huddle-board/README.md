# AI Huddle Management board

Centerpiece Databricks App for the St. Luke's **AI Huddle** use case. It supports
the South Clinic (Nampa) morning triage huddle for `huddle_date = 2026-09-15`.

## What it does

1. **Patient List** - the day's patients from `kk_test.huddle.patient_demographics`
   joined with the AI-extracted transcript factors in
   `kk_test.huddle.transcript_ai_extractions` (visit complexity, psychosocial
   complexity, SDOH, relationship context).
2. **Physician Input** - for a selected patient, a physician enters:
   `provider_patient_relationship_score` (-10..10),
   `patient_complexity_score` (-10..10), optional `physician_notes`,
   `optimal_team_member`, `assigned_team_member`, and
   `non_optimal_assignment_notes`. Submitting **writes the row back to the Delta
   table `kk_test.huddle.physician_inputs`** via an `INSERT` on the SQL warehouse.
3. **Huddle Board** - patients grouped by `assigned_team_member` with complexity,
   assignment balance across providers, and optimal-vs-assigned mismatches.
4. **AI-suggested assignments** (future-state) - a "Suggest assignments" action
   on the Huddle Board calls
   `ai_query('databricks-meta-llama-3-3-70b-instruct', ...)` live on the SQL
   warehouse, once per patient. The prompt is built from the patient's
   AI-extracted transcript factors, the provider roster, and any existing
   relationship scores, and the model returns a recommended provider + a
   one-line rationale. These are shown as **suggestions the physician can
   override** - the physician's actual assignment still writes to
   `physician_inputs` on the Physician Input tab. This realizes the "ML/AI picks
   which patients should be seen by which provider" future-state in the huddle
   brief.

## Architecture

```
Streamlit UI (Databricks Apps runtime)
      |
      |  databricks-sql-connector  (service-principal OAuth via SDK Config)
      v
SQL Warehouse  c68a614580fefe22
      |
      |  SELECT (reads)                 INSERT (physician-input writeback)
      v                                          v
kk_test.huddle.patient_demographics      kk_test.huddle.physician_inputs  (Delta)
kk_test.huddle.transcript_ai_extractions
```

### Workshop writeback vs. production path

- **Workshop (implemented here):** physician inputs `INSERT` directly into the
  Delta table `kk_test.huddle.physician_inputs` through the SQL warehouse. Fast,
  no extra infra, good enough for the huddle-board demo.
- **Production (documented target):** physician inputs write to **Lakebase
  Postgres** - a Databricks-managed, low-latency OLTP store - using the App's
  **OAuth managed credentials** (auto-injected `PGHOST`/`PGUSER`/... env vars, no
  static secret). A **synced table** streams Lakebase rows back into Delta for
  analytics and Genie. This is the "turn the POC into production" step for the
  huddle use case: the transactional writes belong in an OLTP database, while the
  lakehouse remains the analytics system of record.

  To move to the production path: add a **Database (Lakebase)** app resource,
  install `psycopg2-binary`, connect with the injected `PG*` env vars + an OAuth
  token from the SDK, and create a Lakebase-to-Delta synced table.

## Configuration

- Catalog/schema (`kk_test.huddle`) and `huddle_date` (`2026-09-15`) are constants
  in `app.py` (workshop scope).
- Warehouse id comes from the `DATABRICKS_WAREHOUSE_ID` env var, bound to the
  `sql-warehouse` app resource in `app.yaml`; it falls back to the workshop
  warehouse id in code if the resource is not attached.

## Service principal grants (required)

The app runs as a service principal. It needs (not admin):

```sql
GRANT USE CATALOG ON CATALOG kk_test TO `<app-sp>`;
GRANT USE SCHEMA  ON SCHEMA  kk_test.huddle TO `<app-sp>`;
GRANT SELECT, MODIFY ON TABLE kk_test.huddle.patient_demographics    TO `<app-sp>`;
GRANT SELECT, MODIFY ON TABLE kk_test.huddle.transcript_ai_extractions TO `<app-sp>`;
GRANT SELECT, MODIFY ON TABLE kk_test.huddle.physician_inputs        TO `<app-sp>`;
-- plus CAN_USE on the SQL warehouse (set via warehouse permissions).
```

## Deploy

```bash
databricks apps create huddle-board --profile kk_test
databricks sync . /Workspace/Users/<you>/apps/huddle-board --profile kk_test
databricks apps deploy huddle-board \
  --source-code-path /Workspace/Users/<you>/apps/huddle-board --profile kk_test
databricks apps get huddle-board --profile kk_test   # wait for RUNNING
```

## Files

- `app.py` - Streamlit app (3 tabs + Delta writeback).
- `app.yaml` - Databricks Apps config (command + warehouse resource binding).
- `requirements.txt` - `databricks-sql-connector`, `databricks-sdk`, `pandas`.
- `.streamlit/config.toml` - headless server config.
