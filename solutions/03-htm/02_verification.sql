-- HTM Data Verification Queries
-- Run after data load to verify planted signals and data quality

-- Total row counts
SELECT 'medical_assets' as table_name, COUNT(*) as row_count FROM kk_test.htm.medical_assets
UNION ALL
SELECT 'work_orders' as table_name, COUNT(*) as row_count FROM kk_test.htm.work_orders;

-- Assets 2026 replacement cohort
SELECT COUNT(*) as assets_eol_2026
FROM kk_test.htm.medical_assets
WHERE YEAR(support_end_date) = 2026;

-- Assets 2027 replacement cohort
SELECT COUNT(*) as assets_eol_2027
FROM kk_test.htm.medical_assets
WHERE YEAR(support_end_date) = 2027;

-- Anesthesia machines due in 2026
SELECT COUNT(*) as anesthesia_2026
FROM kk_test.htm.medical_assets
WHERE asset_description = 'Anesthesia Machines'
  AND YEAR(support_end_date) = 2026;

-- High corrective load assets (diagnostic query)
SELECT
  asset_number,
  asset_description,
  facility,
  COUNT(CASE WHEN work_order_type = 'Corrective' THEN 1 END) as corrective_count
FROM kk_test.htm.medical_assets ma
LEFT JOIN kk_test.htm.work_orders wo ON ma.asset_number = wo.asset_number
GROUP BY ma.asset_number, ma.asset_description, ma.facility
HAVING corrective_count >= 8
ORDER BY corrective_count DESC
LIMIT 10;

-- Date coherence check (purchase < install < support_end)
SELECT COUNT(*) as incoherent_dates
FROM kk_test.htm.medical_assets
WHERE NOT (purchase_date <= install_date AND install_date <= support_end_date);

-- Replacement cost and risk distribution
SELECT
  CAST(AVG(replacement_cost) AS DECIMAL(12,2)) as avg_replacement_cost,
  CAST(MIN(replacement_cost) AS DECIMAL(12,2)) as min_replacement_cost,
  CAST(MAX(replacement_cost) AS DECIMAL(12,2)) as max_replacement_cost,
  CAST(AVG(risk_score) AS DECIMAL(5,2)) as avg_risk_score,
  MIN(risk_score) as min_risk_score,
  MAX(risk_score) as max_risk_score
FROM kk_test.htm.medical_assets;

-- Metric view test queries (requires metric view to be created first)
-- SELECT MEASURE(Asset Count), MEASURE(Total Replacement Cost), MEASURE(Avg Risk Score)
-- FROM kk_test.htm.htm_metrics
-- GROUP BY Facility, Device Family, EOL Year;
