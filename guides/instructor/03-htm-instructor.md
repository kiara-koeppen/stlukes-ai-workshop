# Equipment Lifecycle & Replacement Planning: Instructor Cheatsheet

## TL;DR

HTM (Healthcare Technology Management) manually filters asset databases to find devices nearing end-of-support and plan capital replacements with Finance. The solution provides natural-language query access to equipment lifecycle data, forecasts replacement volume and costs by year and facility, and ranks replacement priority by lifecycle stage, risk score, and maintenance burden.

## The Solution We Built

All assets are deployed and verified live on kk_test. Swap catalog to `healthcare_ai` when participants deploy to prod. This is the cleanest use case (non-PHI) and makes a strong Day-1 anchor.

### Structured Data

- **`kk_test.htm.medical_assets`** (8,000 active devices): asset number, description, manufacturer, model, serial number, facility, department (Surgery, ICU, Imaging, Lab, etc.), purchase date, install date, **end-of-support date**, operating system, IP address, MAC address, device status (Active/Retired/Loaner), replacement cost, and risk score (numeric, 0-100; higher = replace sooner).
- **`kk_test.htm.work_orders`** (52,104 total): work order ID, asset number, work order type (Corrective, Preventive, Recall, Inspection), request date, completion date, technician, labor hours, status. Includes planted signal: a subset of assets has high corrective-work-order volume, indicating maintenance burden and replacement urgency.

### Semantic Layer (Metric View)

- **`kk_test.htm.htm_metrics`** (verified 2026-09-04): dimensions for facility, department, device family (asset description), manufacturer, end-of-life (EOL) year, device status, operating system, network connectivity, age cohort (0-2 years, 2-5, 5-10, 10+ years), and risk level (Critical >= 80, High 60-79, Medium 40-59, Low < 40). Measures compute:
  - **1,388 assets due for replacement in 2026** (support_end_date in 2026), with average risk score 83.7 (critical).
  - **1,365 assets due in 2027**.
  - Asset count, total replacement cost, average risk score, assets due this year, assets due next year.
  - Filterable by facility so Equipment Planners can scope capital requests.

### AI Functions

- **`kk_test.htm.work_order_forecast`** (6-month horizon forecast, verified 2026-09-04): `ai_forecast` on the corrective work-order time series. Scores monthly corrective-WO volume for the next 6 months. Forecast: approximately **480 corrective WOs/month**, with bounds 428-542 (confidence interval). This informs technician staffing and parts budgets.

### Genie Agent

- **Space ID `01f1a88ca93e134ca8dec9628062762b`** (live-verified): point the agent at the metric view and tables. The agent answers natural-language questions like "What anesthesia machines need replacement in 2026?" (returns ~50 anesthesia machines in Boise, Meridian, etc.), "What devices in Surgery are due next year?" (returns count + details by facility), "How much will 2026 replacements cost?" (aggregates replacement_cost for all EOL-2026 assets).

### AI/BI Dashboard

- **Dashboard ID `01f1a88db3bd1c3aa3cd2fed66b243b2`** (verified 2026-09-04): shows replacement forecast by year (stacked bar: count by 2026, 2027, etc.), assets due by facility, cost breakdown, corrective-WO forecast trend, and a table of critical-risk assets due in 2026.

## How to Build It

### Step 1: Load Structured Data

Participants run the data-generation notebook, which creates:

- `{catalog}.htm.medical_assets` (8,000 devices).
- `{catalog}.htm.work_orders` (52,104 work orders).

**Facilitator check**: Verify counts and planted signal:
```sql
SELECT 
  count(*) total_assets,
  sum(CASE WHEN year(support_end_date) = 2026 THEN 1 ELSE 0 END) due_2026,
  sum(CASE WHEN year(support_end_date) = 2027 THEN 1 ELSE 0 END) due_2027
FROM {catalog}.htm.medical_assets
WHERE device_status = 'Active';
```
Should return approximately 8,000 total, 1,388 in 2026, 1,365 in 2027.

```sql
SELECT work_order_type, count(*) 
FROM {catalog}.htm.work_orders 
GROUP BY 1;
```
Should show roughly 52,104 total, with a clear Corrective majority (e.g., ~30,000 corrective).

### Step 2: Build the Metric View

Participants write a metric view over the assets table.

**Genie Code Prompt:**
```
Create a metric view named htm_metrics over {catalog}.htm.medical_assets with dimensions:
Facility (facility), Department (department), Device Family (asset_description), 
Manufacturer (manufacturer), EOL Year (year of support_end_date), Device Status, 
Operating System, Has IP Address (Yes/No based on IP column), Age Cohort (case: 0-2 years, 
2-5 years, 5-10 years, 10+ years based on install_date), Risk Level (Critical if risk_score >= 80, 
High 60-79, Medium 40-59, Low <40).
Add measures: Asset Count (count distinct asset_number), Total Replacement Cost (sum 
replacement_cost), Avg Risk Score (avg risk_score), Assets Due This Year (count where 
year(support_end_date) = current year), Assets Due Next Year (count where year = current year + 1).
```

**Facilitator check**: Query the view:
```sql
SELECT 
  Facility, 
  EOL_Year, 
  Asset_Count, 
  Total_Replacement_Cost, 
  Avg_Risk_Score
FROM {catalog}.htm.htm_metrics
WHERE EOL_Year IN (2026, 2027)
ORDER BY EOL_Year, Facility;
```
Expected: 1,388 assets in 2026 with avg risk 83.7, 1,365 in 2027. Breakdown by facility.

### Step 3: Create the AI Functions (ai_forecast)

Participants write a table that applies `ai_forecast` to the corrective work-order time series.

**Direct SQL or Genie Code Prompt:**
```
Create an ai_forecast table over {catalog}.htm.work_orders:
1. Aggregate corrective work orders by month: group by date_trunc('MONTH', request_date), 
   count the rows.
2. Use ai_forecast to predict the next 6 months. Set horizon to max(request_date) + 6 months 
   (format as a target date, not a step count). Set time_col='ds' (the month), value_col='cnt' (count).
3. Return forecast_month, forecast_corrective_wos (rounded), lower_bound, upper_bound.
Call the table {catalog}.htm.work_order_forecast.
```

**Key note**: `ai_forecast` horizon is a TARGET DATE (end date for the forecast), not a step count. This is a common gotcha.

**Facilitator check**: Query the forecast:
```sql
SELECT 
  forecast_month, 
  forecast_corrective_wos, 
  lower_bound, 
  upper_bound
FROM {catalog}.htm.work_order_forecast
ORDER BY forecast_month;
```
Expected: ~480 WOs/month, bounds ~428-542. The forecast will vary slightly by run due to the stochastic nature of the model.

### Step 4: Create the Genie Agent

Participants use the REST API to create a Genie Agent.

**Steps:**
1. Open a terminal or script.
2. POST to `/api/2.0/data-rooms/` with:
   ```json
   {
     "display_name": "Equipment Lifecycle Planning",
     "warehouse_id": "c68a614580fefe22",
     "table_identifiers": [
       "{catalog}.htm.htm_metrics",
       "{catalog}.htm.medical_assets",
       "{catalog}.htm.work_order_forecast"
     ],
     "run_as_type": "VIEWER",
     "description": "Natural-language queries on equipment lifecycle and replacement forecasting"
   }
   ```
3. Capture the returned `space_id`.

**Facilitator check**: Test the agent:
```bash
uv run --with requests --python 3.11 python solutions/_tools/genie_ask.py <space_id> \
  "What anesthesia machines need replacement in 2026?"
```
Expected response: mentions a count (e.g., 50-100) and lists specific anesthesia machines or the count by facility.

### Step 5: Build the AI/BI Dashboard

Participants create a Lakeview dashboard visualizing the metric view and forecast.

**Genie Code Prompt (or use lvdash.json):**
```
Create a dashboard with these widgets:
- KPI: Total Assets Due 2026
- KPI: Average Risk Score (for 2026 assets)
- KPI: Total Replacement Cost (sum for 2026)
- Bar chart: Assets due by year (2026, 2027, etc.), grouped by facility
- Line chart: Corrective WO forecast (from work_order_forecast) over time with confidence bounds
- Table: Top 20 critical-risk assets due in 2026 (asset description, facility, department, risk score, replacement cost)
Add filters for Facility and Risk Level.
```

## Genie Code Prompts That Land the Solution

### Metric View Prompt

```
Create a metric view named htm_metrics from kk_test.htm.medical_assets (or {catalog}.htm.medical_assets).

Dimensions:
- Facility: facility
- Department: department
- Device Family: asset_description
- Manufacturer: manufacturer
- EOL Year: year(support_end_date)
- Device Status: device_status
- Operating System: operating_system
- Has IP Address: case when ip_address is not null and ip_address <> '' then 'Yes' else 'No'
- Age Cohort: case when year(current_date()) - year(install_date) < 2 then '0-2 years' when < 5 then '2-5 years' when < 10 then '5-10 years' else '10+ years'
- Risk Level: case when risk_score >= 80 then 'Critical' when >= 60 then 'High' when >= 40 then 'Medium' else 'Low'

Measures:
- Asset Count: count(distinct asset_number)
- Total Replacement Cost: sum(replacement_cost)
- Avg Risk Score: avg(risk_score)
- Assets Due This Year: sum(case when year(support_end_date) = year(current_date()) then 1 else 0 end)
- Assets Due Next Year: sum(case when year(support_end_date) = year(current_date()) + 1 then 1 else 0 end)
```

### ai_forecast Prompt

```
Create a table named work_order_forecast that forecasts corrective work order volume.

Steps:
1. Aggregate corrective work orders from {catalog}.htm.work_orders by month: 
   select date_trunc('MONTH', request_date) as ds, count(*) as cnt where work_order_type='Corrective'
2. Use ai_forecast with:
   - horizon: max(request_date) in your data + 6 months (format as 'YYYY-MM-DD')
   - time_col: 'ds'
   - value_col: 'cnt'
3. Return columns: forecast_month (ds), forecast_corrective_wos (rounded cnt_forecast), 
   lower_bound (rounded cnt_lower), upper_bound (rounded cnt_upper)
```

## Facilitator Tips & Tiered Hints

### Group is stuck on the metric view

**L1**: "Dimensions are the grouping columns (facility, department, year). Measures are the aggregations (count, sum). Start simple: count assets, sum replacement cost."

**L2**: "For the age cohort dimension, use CASE WHEN: if the asset is less than 2 years old, put it in '0-2 years', etc."

**L3**: "The risk-level dimension is derived: take the continuous risk_score and bucket it into categories (80+ = critical, 60-79 = high, etc.)."

**L4**: Show the full metric view from `solutions/03-htm/01_metric_view.sql` for cross-checking.

### Group is stuck on ai_forecast

**L1**: "ai_forecast is a built-in function that takes a time series and predicts future values. You need: a time column (dates), a value column (counts), and a horizon (end date you want to forecast to)."

**L2**: "First, build the input table: corrective WOs grouped by month. Then pass that to ai_forecast."

**L3**: "The horizon parameter is a TARGET DATE, not a step count. If your data goes to 2026-09, and you want 6 months of forecast, set horizon='2027-03-01' (not 6)."

**L4**: "The forecast returns three columns: value_forecast (the predicted value), value_lower (lower confidence bound), value_upper (upper bound). Round them to integers since you can't have fractional work orders."

### Group is stuck on creating the Genie Agent

**L1**: "The Genie Agent is a REST API. Use curl or Python to create it with display_name, warehouse_id, and table_identifiers."

**L2**: "Include both the metric view AND the base tables so the agent can drill down if a user asks detailed questions."

**L3**: "If the API call fails, check: (1) Is your auth token valid? (2) Does the warehouse exist? (3) Are the table_identifiers in the right catalog.schema.table format?"

**L4**: "If all three checks pass, copy the curl command from the solutions/_tools/genie_ask.py script and adapt it for your workspace."

### Known Gotchas

1. **ai_forecast horizon is a date, not a step count**: This trips up most participants. Horizon must be a target date string like '2027-03-01', not the integer 6.

2. **Metric view MEASURE() vs aggregate expressions**: You cannot write `expr: count(*)` in a MEASURE. You must use the MEASURE() function. For complex logic, pre-aggregate in a view and then reference it.

3. **Genie Agent on Volumes for device manuals (Beta)**: If you want to attach vendor end-of-life bulletins (PDFs) to the Genie Agent, use Genie-on-Volumes. This is Beta, so test file types and size limits beforehand.

4. **Work order type filtering**: The planted signal is in Corrective work orders. If a participant accidentally includes all work-order types in the forecast, the volume will be much higher (52,000 total vs ~30,000 corrective). Remind them to filter `where work_order_type = 'Corrective'`.

5. **Replacement cost aggregation**: Replacement cost is per asset, not amortized over time. If a participant sums replacement costs across all 2026 assets, the number is the full capital ask for that year. This is the right interpretation for Finance planning.

## Production Path (Attendees Will Ask)

For equipment lifecycle planning, production considerations are:

- **Real data ingestion**: Replace the synthetic medical_assets table with a real export from your TMS (Technology Management System) via **Lakeflow Connect** on a schedule (daily or weekly).

- **Work order integration**: Ingest work orders from your ServiceNow instance. Yutong noted that ServiceNow migration is planned for spring 2027, so this is a wave-2 item.

- **Forecast scale-up**: The workshop forecast is 6 months. In production, extend to 12-24 months for annual and multi-year capital planning. Be aware that ai_forecast accuracy degrades for very long horizons.

- **Governance**: HTM data is not PHI, but it is operationally sensitive (equipment roadmap). Use Unity Catalog RBAC to restrict access to Finance and HTM leadership.

- **Alerting**: Create a Databricks Alert that triggers when an asset moves into the critical-risk bucket or EOL date is within 90 days, notifying HTM and procurement.

- **Dashboard refresh**: Set up a scheduled query to refresh the dashboard nightly so Equipment Planners see the latest asset lifecycle data.

- **Cost tracking**: Integrate replacement costs with the Financial system via reverse-ETL so Finance can track capital vs. budget in real time.
