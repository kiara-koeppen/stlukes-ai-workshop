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
