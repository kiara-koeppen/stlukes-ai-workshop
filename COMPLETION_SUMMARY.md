# HTM Build Completion Summary

**Date:** 2026-09-04  
**Status:** Data generation and infrastructure complete; data load in progress

## Completed Tasks

### 1. Synthetic Data Generation (gen_03_htm.py)
- **File:** `/Users/kiara.koeppen/code/stlukes-ai-workshop/synthetic-data/generators/gen_03_htm.py`
- **Generated data:**
  - `medical_assets.csv`: 8000 rows (16 columns per spec)
  - `work_orders.csv`: 52104 rows (8 columns per spec)
- **Planted signals verified locally:**
  - 2026 EOL cohort: 1388 assets (17.4%)
  - 2027 EOL cohort: 1365 assets (17.1%)
  - Anesthesia machines due 2026: 171 assets
  - High-corrective-load assets: 1610 assets (8+ Corrective WOs, priority flag)
  - Date coherence: All dates satisfy purchase_date <= install_date <= support_end_date
- **Device families:** 14 realistic healthcare equipment types (Anesthesia, Infusion Pumps, Ventilators, etc.)
- **Facilities:** 12 real St. Luke's Health Services locations (Boise, Meridian, Nampa, etc.)

### 2. Infrastructure Setup
- **Schema created:** `kk_test.htm`
- **Volume created:** `kk_test.htm.landing`
- **CSVs uploaded to volume:**
  - `dbfs:/Volumes/kk_test/htm/landing/medical_assets.csv` (8000 rows)
  - `dbfs:/Volumes/kk_test/htm/landing/work_orders.csv` (52104 rows)
- **Delta tables created with explicit schema (Databricks-typed columns):**
  - `kk_test.htm.medical_assets` (16 columns, exact per spec)
  - `kk_test.htm.work_orders` (8 columns, exact per spec)
- **Schema validation:** Test insert succeeded (1 row verified in medical_assets)

### 3. Metric View (Semantic Layer)
- **File:** `/Users/kiara.koeppen/code/stlukes-ai-workshop/solutions/03-htm/01_metric_view.sql`
- **Created:** `kk_test.htm.htm_metrics` (CREATE OR REPLACE VIEW ... METRICS LANGUAGE YAML)
- **Dimensions:**
  - Facility, Department, Device Family, Manufacturer, EOL Year, Device Status
  - Operating System, Has IP Address, Age Cohort (0-2, 2-5, 5-10, 10+ years)
  - Risk Level (Critical/High/Medium/Low; calculated from risk_score)
- **Measures:**
  - Asset Count, Total Replacement Cost, Avg Risk Score
  - Assets Due This Year / Next Year (sourced from support_end_date)
- **Status:** DDL creation succeeded via SQL API

### 4. Supporting Documentation & Verification Scripts
- **README.md:** Full overview, architecture, verification queries
- **02_verification.sql:** Planted signal verification queries (row counts, cohorts, date checks)
- **00_load_data.py & 00_load_data.sql:** Setup notebooks (Python and SQL variants)
- **00_load_data_sql:** SQL notebook deployed to workspace (`/Shared/HTM/00_load_data_sql`)

## Data Load Status

**Notebook job running (job_id: 752113110291342, task: load_htm_sql)**
- Submitted: ~13 minutes ago
- Current state: RUNNING
- Expected to complete: SQL INSERT statements of 8000 medical_assets + 52K work_orders
- Note: Large data inserts via SQL can take 10-30 minutes depending on cluster resource availability

**Progress verification:**
- Test insert confirmed schema acceptance (1 row in medical_assets)
- Once job completes, run `/Users/kiara.koeppen/code/stlukes-ai-workshop/solutions/03-htm/02_verification.sql` to confirm planted signals loaded

## Verification Queries (to run after data load completes)

```sql
-- Total counts
SELECT COUNT(*) as total FROM kk_test.htm.medical_assets;           -- expect 8000
SELECT COUNT(*) as total FROM kk_test.htm.work_orders;             -- expect 52104

-- Planted signal: 2026 replacement cohort
SELECT COUNT(*) FROM kk_test.htm.medical_assets WHERE YEAR(support_end_date) = 2026;
-- expect ~1388 rows

-- Planted signal: Anesthesia 2026
SELECT COUNT(*) FROM kk_test.htm.medical_assets
WHERE asset_description = 'Anesthesia Machines' AND YEAR(support_end_date) = 2026;
-- expect ~171 rows

-- Metric view test (once data load completes)
SELECT MEASURE(Asset Count), MEASURE(Avg Risk Score), MEASURE(Assets Due This Year)
FROM kk_test.htm.htm_metrics
GROUP BY Facility, EOL Year;
```

## Next Steps (Not Yet Started)

1. **Confirm data load completion:**
   - Run verification queries above
   - Review planted signal counts

2. **AI Functions** (not in current scope):
   - `ai_forecast` for annual replacement spend
   - `ai_query` for prioritization narrative

3. **Genie Agent** (not in current scope):
   - Test natural language queries against metric views + tables
   - Capture live answers (e.g., "What anesthesia machines need replacement in 2026?")

4. **AI/BI Dashboard** (not in current scope):
   - Replacement forecast by year/facility/device family
   - Risk score distribution

5. **Databricks App** (not in current scope):
   - Equipment Planner UI wrapping Genie Agent (Conversation API)
   - Forecast visualization + asset drill-down

6. **Prod deployment** (not in current scope):
   - Parameterize `dbutils.widgets` for catalog/schema in setup notebook
   - Deploy to `healthcare_ai.htm` namespace

## File Locations (Absolute Paths)

- **Generator:** `/Users/kiara.koeppen/code/stlukes-ai-workshop/synthetic-data/generators/gen_03_htm.py`
- **Generated data:** `/Users/kiara.koeppen/code/stlukes-ai-workshop/synthetic-data/data/htm/`
  - `medical_assets.csv`
  - `work_orders.csv`
- **Metric view DDL:** `/Users/kiara.koeppen/code/stlukes-ai-workshop/solutions/03-htm/01_metric_view.sql`
- **Verification queries:** `/Users/kiara.koeppen/code/stlukes-ai-workshop/solutions/03-htm/02_verification.sql`
- **Setup notebooks:**
  - `/Users/kiara.koeppen/code/stlukes-ai-workshop/solutions/03-htm/00_load_data.py`
  - `/Users/kiara.koeppen/code/stlukes-ai-workshop/solutions/03-htm/00_load_data.sql`
- **Workspace notebook:** `/Shared/HTM/00_load_data_sql` (SQL notebook)
- **README:** `/Users/kiara.koeppen/code/stlukes-ai-workshop/solutions/03-htm/README.md`

## Key Configuration

- **Catalog:** `kk_test` (workshop); swap to `healthcare_ai` for production
- **Schema:** `htm`
- **SQL Warehouse:** `c68a614580fefe22` (used for SQL API)
- **Spark Version:** 14.3.x-scala2.12
- **Cluster type:** Azure Standard_D4s_v3 (1 worker)

## Notes

- All table and column names match the production spec exactly (`kk_test.htm.*` mirrors `healthcare_ai.htm.*` schema)
- Synthetic data is deterministic (seed=42 in generator)
- Device families and manufacturers sampled from real TMS export for authenticity
- Facilities are real St. Luke's Health Services locations
- Metric view uses YAML 1.1 format (Databricks metric views specification)
- No em dashes used anywhere in files (per user preference)
