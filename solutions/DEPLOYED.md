# Deployed Workshop Assets (kk_test)

Live IDs + verification status for the facilitator answer-key build. Rebuildable from the SQL/code in each `solutions/0X-*/` folder. Genie create endpoint = `POST /api/2.0/data-rooms/`; ask/verify via `solutions/_tools/genie_ask.py`. Warehouse: `c68a614580fefe22` (Serverless Starter).

## 01 CKD  (VERIFIED live)
- Tables: `kk_test.clinical.ckd_patient_registry` (2000), `clinical_notes` (1018), `notes_ckd_signals` (200 AI-scored)
- Volumes: `kk_test.clinical.clinical_notes_files` (45 note .txt), `landing`
- Metric view: `kk_test.clinical.ckd_metrics`  (1524 CKD, 500 care-gap, 230 high-risk)
- AI functions: ai_query note extraction (102/102 undocumented-CKD precise)
- **Genie Agent space_id: `01f1a88b5c6613f9ad5a4383a3b81a6b`** (live-verified: "518 patients ... not documented in Epic")
- TODO: AI/BI dashboard, App, guides

## 02 Diversion  (data + metric view VERIFIED)
- Tables: `kk_test.med_diversion.medication_activity` (45000), `employee_risk` (50), `peer_group` (10)
- Metric view: `kk_test.med_diversion.diversion_metrics` (composite anomaly; 4 planted diverters top the ranking)
- TODO: AI functions (risk narrative), Genie Agent, dashboard, App, guides

## 03 HTM  (in progress)
- Tables: `kk_test.htm.medical_assets`, `work_orders` (being built)
- Metric view: `kk_test.htm.htm_metrics`
- TODO: AI functions (ai_forecast), Genie Agent, dashboard, App, guides

## 04 Huddle  (data + metric view VERIFIED)
- Tables: `kk_test.huddle.patient_demographics` (18), `transcript_extractions` (18), `physician_inputs` (34)
- Volume: `kk_test.huddle.transcripts` (18 .txt)
- Metric view: `kk_test.huddle.huddle_metrics` (NOTE: patient-count measure counts input rows, not distinct patients; fix when building app)
- TODO: AI functions (extract from transcripts), Genie Agent, dashboard, **App (centerpiece) + Lakebase prod path**, guides
