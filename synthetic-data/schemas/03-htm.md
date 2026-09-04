# NextGen HTM Equipment Planning — Data Spec

**Prod target:** `healthcare_ai.htm.medical_assets` + `healthcare_ai.htm.work_orders` (schemas from Yutong's email)
**Workshop build:** `kk_test.htm.*`
**Grounded in:** real TMS export `TMS - Active as 5-5-2025.xlsx` (45,356 rows x 37 cols) + Yutong's proposed clean 16-col `medical_assets` + 8-col `work_orders`. **Non-PHI: the cleanest use case, good Day-1 anchor material.**

## The problem (what the AI must do)
HTM manually filters the TMS asset file to find devices nearing end-of-support and plan replacements with Finance. The solution must:
1. Answer natural-language queries: *"What anesthesia machines need replacement in 2026?"*, *"What devices in Boise are due next year?"*
2. Forecast replacement needs by year / facility / clinical area.
3. Recommend replacement prioritization (lifecycle + risk + corrective-work-order load).

## Tables
### `medical_assets` (Yutong's clean schema; distilled from the 37-col TMS export)
- `asset_number` STRING, `asset_description` STRING, `manufacturer` STRING, `model_number` STRING, `serial_number` STRING
- `facility` STRING (real values: Boise, Meridian, Nampa, Magic Valley, Twin Falls, McCall, Eagle, Fruitland, Jerome, North Canyon, Wood River, Elmore, ...)
- `department` STRING (clinical area, e.g. Surgery, ICU, Imaging, Lab)
- `purchase_date` DATE, `install_date` DATE, `support_end_date` DATE (end of vendor/OS support)
- `operating_system` STRING, `ip_address` STRING, `mac_address` STRING
- `device_status` STRING (Active/Retired/Loaner)
- `replacement_cost` DECIMAL(12,2)
- `risk_score` DECIMAL(5,2) (higher = replace sooner)

### `work_orders` (Yutong's schema; "pull work orders and types per asset")
- `work_order_id` STRING, `asset_number` STRING
- `work_order_type` STRING (`Corrective`, `Preventive`, `Recall`, `Inspection`)
- `request_date` DATE, `completion_date` DATE, `technician_id` STRING, `labor_hours` DECIMAL(5,2), `status` STRING

## Planted signal
Target ~8,000 assets + ~30,000 work orders:
- A clear **2026 replacement cohort**: assets with `support_end_date` in 2026 (and 2027) across specific device families (anesthesia machines, infusion pumps, ventilators, imaging) so "what anesthesia machines need replacement in 2026?" returns a crisp list.
- **High-corrective-load** assets: a subset with disproportionate `Corrective` work orders -> replacement-priority story ("most corrective actions and need replacement").
- Replacement cost + risk_score distributions that make a believable capital-planning forecast by year/facility.

## Assets to build on top
- **Metric Views**: assets & replacement cost by EOL year / facility / device family; corrective-WO rate per asset.
- **AI Functions**: `ai_forecast` on annual replacement spend or corrective-WO volume; `ai_query` for prioritization narrative.
- **Genie Agent**: the NL query surface over the metric views + tables.
- **AI/BI dashboard**: replacement forecast by year/facility/clinical area.
- **App**: equipment-planner UI wrapping the Genie Agent (Conversation API) + the forecast.

## Unstructured component
Synthetic **device manuals / vendor end-of-life bulletins** (PDF) in a Volume so the Genie Agent can cite "vendor states end-of-support 2026-06" alongside the structured lifecycle data (Genie-on-Volumes, Beta).
