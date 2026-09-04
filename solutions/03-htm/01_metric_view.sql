-- HTM Equipment Planning metric view: semantic layer for Genie Agent and AI/BI dashboard.
-- Catalog is kk_test (workshop); swap to healthcare_ai for production.
-- Covers asset lifecycle, replacement needs by year/facility/device family, corrective work-order load for prioritization.

CREATE OR REPLACE VIEW kk_test.htm.htm_metrics
WITH METRICS LANGUAGE YAML AS $$
version: 1.1
source: kk_test.htm.medical_assets
comment: "HTM equipment planning: lifecycle, replacement forecast, and corrective maintenance load"
dimensions:
  - name: Facility
    expr: facility
  - name: Department
    expr: department
  - name: Device Family
    expr: asset_description
  - name: Manufacturer
    expr: manufacturer
  - name: EOL Year
    expr: YEAR(support_end_date)
  - name: Device Status
    expr: device_status
  - name: Operating System
    expr: operating_system
  - name: Has IP Address
    expr: CASE WHEN ip_address IS NOT NULL AND ip_address <> '' THEN 'Yes' ELSE 'No' END
  - name: Age Cohort
    expr: CASE WHEN YEAR(CURRENT_DATE()) - YEAR(install_date) < 2 THEN '0-2 years' WHEN YEAR(CURRENT_DATE()) - YEAR(install_date) < 5 THEN '2-5 years' WHEN YEAR(CURRENT_DATE()) - YEAR(install_date) < 10 THEN '5-10 years' ELSE '10+ years' END
  - name: Risk Level
    expr: CASE WHEN risk_score >= 80 THEN 'Critical' WHEN risk_score >= 60 THEN 'High' WHEN risk_score >= 40 THEN 'Medium' ELSE 'Low' END
measures:
  - name: Asset Count
    expr: COUNT(DISTINCT asset_number)
  - name: Total Replacement Cost
    expr: SUM(replacement_cost)
  - name: Avg Risk Score
    expr: AVG(risk_score)
  - name: Assets Due This Year
    expr: SUM(CASE WHEN YEAR(support_end_date) = YEAR(CURRENT_DATE()) THEN 1 ELSE 0 END)
  - name: Assets Due Next Year
    expr: SUM(CASE WHEN YEAR(support_end_date) = YEAR(CURRENT_DATE()) + 1 THEN 1 ELSE 0 END)
$$;
