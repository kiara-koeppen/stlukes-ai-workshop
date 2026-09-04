# Deployed Workshop Assets (kk_test)

Live IDs + verification status for the facilitator answer-key build. Rebuildable from the SQL/code in each `solutions/0X-*/` folder. Genie create endpoint = `POST /api/2.0/data-rooms/`; ask/verify via `solutions/_tools/genie_ask.py`. Warehouse: `c68a614580fefe22` (Serverless Starter).

## 01 CKD  (VERIFIED live)
- Tables: `kk_test.clinical.ckd_patient_registry` (2000), `clinical_notes` (1018), `notes_ckd_signals` (200 AI-scored)
- Volumes: `kk_test.clinical.clinical_notes_files` (45 note .txt), `landing`
- Metric view: `kk_test.clinical.ckd_metrics`  (1524 CKD, 500 care-gap, 230 high-risk)
- AI functions: ai_query note extraction (102/102 undocumented-CKD precise)
- **Genie Agent space_id: `01f1a88b5c6613f9ad5a4383a3b81a6b`** (live-verified: "518 patients ... not documented in Epic")
- TODO: AI/BI dashboard, App, guides

## 02 Diversion  (data + metric view + Genie VERIFIED)
- Tables: `kk_test.med_diversion.medication_activity` (45000), `employee_risk` (50), `peer_group` (10)
- Metric view: `kk_test.med_diversion.diversion_metrics` (composite anomaly; 4 planted diverters top the ranking)
- **Genie Agent space_id: `01f1a88ca9ab13638e9123eb9a0edf4b`** (live-verified: top 5 = EMP-00001..00004 planted diverters + 1 control)
- TODO: AI functions (risk narrative), dashboard, App, guides

## 03 HTM  (data + metric view + Genie VERIFIED)
- Tables: `kk_test.htm.medical_assets` (8000), `work_orders` (52104); Volume `kk_test.htm.landing`
- Metric view: `kk_test.htm.htm_metrics` (1388 EOL-2026 @ avg risk 83.7, 1365 EOL-2027)
- **Genie Agent space_id: `01f1a88ca93e134ca8dec9628062762b`** (live-verified: "171 anesthesia machines need replacement in 2026")
- TODO: AI functions (ai_forecast), dashboard, App, guides

## 04 Huddle  (data + metric view + Genie VERIFIED)
- Tables: `kk_test.huddle.patient_demographics` (18), `transcript_extractions` (18), `physician_inputs` (34)
- Volume: `kk_test.huddle.transcripts` (18 .txt)
- Metric view: `kk_test.huddle.huddle_metrics` (NOTE: patient-count measure counts input rows, not distinct patients; fix when building app)
- **Genie Agent space_id: `01f1a88caa171f01b6a7ad343d28dfe3`** (live-verified: highest-complexity patients today, score 9)
- TODO: AI functions (extract from transcripts), dashboard, **App (centerpiece) + Lakebase prod path**, guides

## Genie build recipe (MCP is broken here; use REST via CLI)
- Create: `POST /api/2.0/data-rooms/` with {display_name, warehouse_id, table_identifiers[], run_as_type:"VIEWER", description}
- Verify live: `uv run --with requests --python 3.11 python solutions/_tools/genie_ask.py <space_id> "<question>"`

## Update (2026-09-04): AI Functions + Dashboards done

AI Functions (all verified on real rows):
- CKD: `kk_test.clinical.notes_ckd_signals` (ai_query note extraction, 102/102 precise)
- HTM: `kk_test.htm.work_order_forecast` (ai_forecast; ~480 corrective WOs/mo, bounds 428-542)
- Diversion: `kk_test.med_diversion.investigation_narratives` (ai_query peer-benchmarked narratives, top 5)
- Huddle: `kk_test.huddle.transcript_ai_extractions` (ai_query from transcripts, 18/18 parsed)

AI/BI Dashboards (deployed + verified live, SQL tested first):
- CKD:       `01f1a88db2fc1a5f843fe617311b5cc2`  (solutions/01-ckd/03_dashboard.lvdash.json)
- Diversion: `01f1a88db3721dc383ea706b9d78854a`  (solutions/02-diversion/03_dashboard.lvdash.json)
- HTM:       `01f1a88db3bd1c3aa3cd2fed66b243b2`  (solutions/03-htm/03_dashboard.lvdash.json)
- Huddle:    `01f1a88db4291b848e5cdd4e4e0fc880`  (solutions/04-huddle/03_dashboard.lvdash.json)

REMAINING: Apps (CKD clinician-review + Huddle huddle-board w/ Lakebase prod path priority); guides x4; Google Doc demo script; final verification; GitHub push.

## Update (2026-09-04): Databricks Apps (deployed + browser-verified)

- **CKD clinician-review** (RUNNING): https://ckd-clinician-review-669602668219382.2.azure.databricksapps.com
  KPI tiles (1,524 / 500 / 230 / 32.8%), 500-patient risk-sorted care-gap worklist w/ filters,
  patient review + AI note signal, **live ai_query "Draft nephrology referral + problem-list update"**
  (browser-verified: real draft generated in 6.6s for ACO-X3B0FQGM9NB), **human-in-the-loop writeback**
  to kk_test.clinical.ckd_review_actions, Ask-Genie box. Screenshots in apps/ckd-clinician-review/.
- **huddle-board** (RUNNING): https://huddle-board-669602668219382.2.azure.databricksapps.com
  18-patient list w/ AI-extracted factors, physician input form -> Delta writeback (physician_inputs),
  huddle board grouped by provider, **AI-suggested provider assignments** (ai_query per patient,
  verified for all 18). Lakebase documented as prod path. Screenshot in apps/huddle-board/.
- Both browser-verified live via the authorized Chrome session (SSO satisfied). HTM + Diversion do not
  have dedicated apps (their Genie Agent + AI/BI dashboard are the interactive surfaces).
