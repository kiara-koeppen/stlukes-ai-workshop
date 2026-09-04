# Equipment Lifecycle & Replacement Planning: Participant Guide

## The Problem

HTM (Healthcare Technology Management) manually filters a large equipment database to find devices nearing end-of-support and plan capital replacements. The spreadsheet-and-email workflow is slow and error-prone. Equipment planners struggle to answer questions like:

- "What anesthesia machines need replacement in 2026?"
- "How much will those replacements cost by facility?"
- "Which devices have the highest maintenance burden (corrective work orders) and should be prioritized?"

**What we are solving**: Build a system that lets equipment planners ask natural-language questions over the asset database, automatically forecasts replacement volume and cost by year and facility, and prioritizes based on lifecycle stage and maintenance load.

## What You'll Build

You will construct an end-to-end solution using these Databricks assets:

### 1. Structured Data Layer
- **Assets table**: 8,000 active devices with manufacturer, model, facility, department, end-of-support date, replacement cost, and risk score.
- **Work orders table**: 52,104 maintenance records (corrective, preventive, recall, inspection) so you can compute maintenance burden.

### 2. Semantic Layer (Metric View)
A **metric view** over the assets that defines key business concepts: which devices are due for replacement in 2026 vs. 2027, what is the replacement cost, what is the risk level, how many devices per facility, etc.

**Example measures you will compute**:
- Total assets due in 2026: 1,388 (average risk 83.7, critical category)
- Total assets due in 2027: 1,365
- Replacement cost for 2026: sum of all replacement_cost for EOL-2026 assets
- Corrective WO load per asset (for prioritization)

### 3. AI Functions
- **ai_forecast**: Run a time-series forecast on corrective work orders to predict technician capacity needs over the next 6 months. Forecast approximately 480 corrective WOs/month, with bounds 428-542.

### 4. Genie Agent
A natural-language interface over your metric view and asset tables. Equipment planners ask questions without SQL:

**Example questions the agent will answer**:
- "What anesthesia machines need replacement in 2026?" (returns ~50 machines by facility)
- "Show me the critical-risk assets due in Boise next year." (returns count + details)
- "What is the total replacement cost for 2026?" (returns the sum)

### 5. AI/BI Dashboard
A visual summary: KPIs for assets due by year, replacement cost, average risk; charts showing replacement forecast by facility and year; a table of critical-risk assets requiring urgent planning.

## Genie Code Prompts to Get Started

Genie Code is a conversational interface. Here are opening prompts:

### Build the Metric View
```
I have a table kk_test.htm.medical_assets with columns asset_number, asset_description, 
manufacturer, facility, department, install_date, support_end_date, operating_system, 
device_status, replacement_cost, and risk_score. I need a metric view that breaks down 
assets by facility, department, device type (asset_description), and end-of-life year. 
Include dimensions for device status and risk level (Critical if risk_score >= 80, 
High 60-79, Medium 40-59, Low <40). Add measures for asset count, total replacement cost, 
average risk score, and count of assets due this year vs. next year. Call it htm_metrics.
```

### Forecast Corrective Work Orders
```
I have a table kk_test.htm.work_orders with columns work_order_id, asset_number, 
work_order_type (Corrective, Preventive, Recall, Inspection), request_date, and others. 
I want to forecast corrective work orders for the next 6 months to plan technician staffing. 
Filter for Corrective type, group by month, and use an AI forecasting function to predict 
the next 6 months. Return forecast month, forecasted count, lower bound, and upper bound.
```

### Create a Dashboard
```
I have a metric view kk_test.htm.htm_metrics and a forecast table kk_test.htm.work_order_forecast. 
Build me a dashboard with: KPI tiles for assets due 2026, average risk score, and total 2026 
replacement cost; a bar chart of assets due by year and facility; a line chart showing the 
corrective WO forecast with confidence bounds; a table of the top 20 highest-risk assets due 
in 2026 with facility, department, risk score, and replacement cost. Add filters for facility 
and risk level.
```

## From POC to Production

What you build in the workshop is a proof of concept. Moving to production requires:

### 1. Real Data Ingestion
**Workshop**: Synthetic data in kk_test. **Production**: Consume the real asset database from your TMS (Technology Management System) via **Lakeflow Connect**, pulling a fresh extract daily or weekly.

### 2. Work Order Integration
**Workshop**: Synthetic work orders. **Production**: Ingest from your ServiceNow instance (or CMDB). Note: Yutong mentioned that ServiceNow migration is planned for spring 2027, so this is a wave-2 initiative.

### 3. Forecast Scale-Up
**Workshop**: 6-month horizon for learning. **Production**: Extend to 12 or 24 months for annual and multi-year capital planning. Be aware that forecast accuracy declines for very long horizons, so re-train regularly.

### 4. Access Control & Governance
Equipment lifecycle data is operationally sensitive. Use **Unity Catalog** RBAC to restrict access to Finance, HTM leadership, and procurement only. Audit who runs queries and exports data.

### 5. Alerting & Automation
- Create a **Databricks Alert** that triggers when an asset enters the "critical replacement window" (e.g., EOL date within 90 days or new maintenance complaints spike).
- Automate the replacement recommendation to procurement via reverse-ETL so the handoff is seamless.

### 6. Multi-Year Planning
Once you have 12-24 month forecasts, link replacement costs to the Financial system so Finance can track capital spend vs. budget in real time.

### 7. Unstructured Data (Future)
If you want to attach vendor end-of-life bulletins or device manuals to the Genie Agent for context, use **Genie-on-Volumes** (Beta). This allows equipment planners to ask "What does the vendor say about replacement timelines?" and the agent will cite the bulletin.

## Key Takeaways

- **Metric Views** standardize the definition of "due for replacement in 2026," shared across dashboards and Genie queries.
- **Genie Agents** democratize data: HTM staff can ask questions without knowing SQL or Databricks.
- **ai_forecast** brings predictive capacity planning into SQL. No separate Python pipeline or Jupyter notebook needed.
- **Governance and alerting**: Non-PHI data is still operationally sensitive. Use RBAC and alerts to keep the right people informed.
