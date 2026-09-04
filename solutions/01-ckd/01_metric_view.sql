-- CKD metric view: the semantic layer read by both the Genie Agent and the AI/BI dashboard.
-- Catalog is a widget in the setup notebook; this file uses kk_test (swap to healthcare_ai for prod).
-- Verified 2026-09-04 in kk_test.clinical: 1,524 patients with CKD, 500 care-gap (33% undocumented), 230 high-risk.

CREATE OR REPLACE VIEW kk_test.clinical.ckd_metrics
WITH METRICS LANGUAGE YAML AS $$
version: 1.1
source: kk_test.clinical.ckd_patient_registry
comment: "CKD identification, staging, care-gap and risk KPIs"
dimensions:
  - name: Actual Stage
    expr: actual_ckd_stage
  - name: Documented CKD
    expr: documented_ckd
  - name: Sees Nephrology
    expr: sees_nephrology
  - name: Assigned Provider
    expr: assigned_provider_name
  - name: Sex
    expr: sex
  - name: Age Band
    expr: CASE WHEN age < 55 THEN '45-54' WHEN age < 65 THEN '55-64' WHEN age < 75 THEN '65-74' ELSE '75+' END
  - name: Albuminuria
    expr: microalbumin_category
  - name: On Key Meds
    expr: CASE WHEN key_meds IS NOT NULL AND key_meds <> '' THEN 'Yes' ELSE 'No' END
  - name: Care Gap
    expr: CASE WHEN actual_ckd_stage IN ('CKD 3a','CKD 3b','CKD 4','CKD 5') AND documented_ckd IN ('No','None') THEN 'Care Gap' ELSE 'OK' END
  - name: Stage Match
    expr: CASE WHEN documented_ckd <> actual_ckd_stage AND actual_ckd_stage <> 'None' THEN 'Mismatch' ELSE 'Match' END
measures:
  - name: Patient Count
    expr: COUNT(1)
  - name: Patients With CKD
    expr: SUM(CASE WHEN has_ckd THEN 1 ELSE 0 END)
  - name: Care Gap Patients
    expr: SUM(CASE WHEN actual_ckd_stage IN ('CKD 3a','CKD 3b','CKD 4','CKD 5') AND documented_ckd IN ('No','None') THEN 1 ELSE 0 END)
  - name: High Risk Patients
    expr: SUM(CASE WHEN actual_ckd_stage IN ('CKD 4','CKD 5') AND sees_nephrology = false THEN 1 ELSE 0 END)
  - name: Undocumented CKD Rate
    expr: SUM(CASE WHEN actual_ckd_stage IN ('CKD 3a','CKD 3b','CKD 4','CKD 5') AND documented_ckd IN ('No','None') THEN 1 ELSE 0 END) / NULLIF(SUM(CASE WHEN has_ckd THEN 1 ELSE 0 END),0)
  - name: Avg GFR
    expr: AVG((gfr_1 + gfr_2 + gfr_3) / 3.0)
  - name: Avg Creatinine
    expr: AVG((creatinine_1 + creatinine_2 + creatinine_3) / 3.0)
  - name: Pct Seeing Nephrology
    expr: AVG(CASE WHEN sees_nephrology THEN 1.0 ELSE 0.0 END)
$$;
