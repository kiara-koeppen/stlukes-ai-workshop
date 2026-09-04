# HTM Equipment Planning - St. Luke's Health Services

**Use case:** Equipment planning and replacement forecasting for HTM (Health Technology Management) at St. Luke's Health Services.

**Problem:** HTM manually filters a 45K-row TMS (Technology Management System) asset file to identify devices nearing end-of-support and plan replacements with Finance.

**Solution:** Databricks semantic layer (metric views) + Genie Agent for natural language queries over equipment lifecycle data.

## Build artifacts

### Data generation
- `synthetic-data/generators/gen_03_htm.py`: Deterministic synthetic data generator
  - Inputs: Real HTM TMS export (source-materials/HTM_TMS_Active_5-5-2025.xlsx)
  - Outputs: 8000 medical assets + 30000 work orders CSV files
  - Planted signal: 2026/2027 replacement cohorts, high-corrective-load assets

### Delta tables (kk_test.htm namespace, prod: healthcare_ai.htm)
- `medical_assets` (8000 rows, 16 cols): asset_number, asset_description, manufacturer, model_number, serial_number, facility, department, purchase_date, install_date, support_end_date, operating_system, ip_address, mac_address, device_status, replacement_cost, risk_score
- `work_orders` (30000+ rows, 8 cols): work_order_id, asset_number, work_order_type, request_date, completion_date, technician_id, labor_hours, status

### Metric view
- `01_metric_view.sql`: Semantic layer for Genie Agent + AI/BI dashboard
  - Dimensions: Facility, Department, Device Family, Manufacturer, EOL Year, Device Status, OS, Network connectivity, Age Cohort, Risk Level
  - Measures: Asset Count, Total Replacement Cost, Avg Risk Score, Assets Due This Year/Next Year

### Setup and verification
- `00_load_data.py`: Python notebook (legacy) to load CSVs with explicit schema casting
- `00_load_data_sql.sql`: SQL notebook to load CSVs (current)
- `02_verification.sql`: Verification queries to check planted signal (2026 cohort, anesthesia 2026, date coherence)

## Key planted signals (verified in synthetic data)

- **2026 EOL cohort:** 1388 assets (17.4%)
- **2027 EOL cohort:** 1365 assets (17.1%)
- **Anesthesia machines due 2026:** 171 assets
- **High corrective load:** 1610 assets (8+ corrective work orders, replacement priority)
- **Date coherence:** All dates satisfy purchase_date <= install_date <= support_end_date

## Verification queries

### Total row counts
```sql
SELECT 'medical_assets' as table_name, COUNT(*) as row_count FROM kk_test.htm.medical_assets
UNION ALL
SELECT 'work_orders' as table_name, COUNT(*) as row_count FROM kk_test.htm.work_orders;
```

### Assets 2026 replacement cohort
```sql
SELECT COUNT(*) as assets_eol_2026
FROM kk_test.htm.medical_assets
WHERE YEAR(support_end_date) = 2026;
```

### Anesthesia machines due 2026
```sql
SELECT COUNT(*) as anesthesia_2026
FROM kk_test.htm.medical_assets
WHERE asset_description = 'Anesthesia Machines'
  AND YEAR(support_end_date) = 2026;
```

### Metric view test
```sql
SELECT MEASURE(Asset Count), MEASURE(Avg Risk Score), MEASURE(Assets Due This Year)
FROM kk_test.htm.htm_metrics
GROUP BY Facility, EOL Year;
```

## Facilities (real SLHS locations)

Boise, Meridian, Nampa, Magic Valley, Twin Falls, McCall, Eagle, Fruitland, Jerome, North Canyon, Wood River, Elmore

## Device families

Anesthesia Machines, Infusion Pumps, Ventilators, Patient Monitors, Ultrasound, CT Scanners, MRI, Defibrillators, Vital Signs Monitors, Cardiac Devices, Dialysis, Surgical Lights, Microscopes, Lighting Systems

## Next steps (AI Functions, Genie Agent, App, Dashboard)

1. AI Functions: `ai_forecast` on annual replacement spend by facility; `ai_query` for prioritization narrative (risk + corrective load)
2. Genie Agent: Natural language queries over metric views: "What anesthesia machines need replacement in 2026?" "Show me high-risk assets by facility"
3. AI/BI Dashboard: Replacement forecast by year / facility / device family
4. App (Equipment Planner UI): Genie Conversation API + forecast visualization + drill-down to asset details

## Prod deployment (healthcare_ai catalog)

1. Parameterize catalog + schema in setup notebook via `dbutils.widgets`
2. Deploy data load notebook to healthcare_ai workspace
3. Deploy metric view DDL
4. Test Genie Agent against prod tables
5. Configure dashboards and apps to point to healthcare_ai.htm
