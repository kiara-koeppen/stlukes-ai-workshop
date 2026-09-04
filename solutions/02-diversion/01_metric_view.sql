-- Medication Diversion Support -- Peer Benchmarking Metrics
-- Catalog is hardcoded to kk_test for workshop build (swap to healthcare_ai for prod).
-- Verified 2026-09-04 in kk_test.med_diversion: 45k events, 50 employees, top 4 diverters identifiable.

CREATE OR REPLACE VIEW kk_test.med_diversion.diversion_metrics
WITH METRICS LANGUAGE YAML AS $$
version: 1.1
source: kk_test.med_diversion.medication_activity
comment: "Medication diversion anomaly detection via peer benchmarking and explicit rules"
dimensions:
  - name: Employee
    expr: employee_id
  - name: Employee Name
    expr: employee_name
  - name: Role
    expr: employee_role
  - name: Department
    expr: department
  - name: Unit
    expr: unit
  - name: Shift
    expr: shift
  - name: Event Type
    expr: event_type
  - name: Medication Class
    expr: med_class
  - name: DEA Schedule
    expr: dea_schedule
measures:
  - name: Dispense Count
    expr: SUM(CASE WHEN event_type = 'dispense' THEN 1 ELSE 0 END)
  - name: Administer Count
    expr: SUM(CASE WHEN event_type = 'administer' THEN 1 ELSE 0 END)
  - name: Waste Count
    expr: SUM(CASE WHEN event_type = 'waste' THEN 1 ELSE 0 END)
  - name: Return Count
    expr: SUM(CASE WHEN event_type = 'return' THEN 1 ELSE 0 END)
  - name: Null Transaction Count
    expr: SUM(CASE WHEN patient_id IS NULL THEN 1 ELSE 0 END)
  - name: Waste Without Witness CII
    expr: SUM(CASE WHEN event_type = 'waste' AND witness_id IS NULL AND dea_schedule = 'CII' THEN 1 ELSE 0 END)
  - name: Administration Without Order
    expr: SUM(CASE WHEN event_type = 'administer' AND order_id IS NULL THEN 1 ELSE 0 END)
  - name: Admin Before Order
    expr: SUM(CASE WHEN event_type = 'administer' AND order_datetime IS NOT NULL AND admin_datetime < order_datetime THEN 1 ELSE 0 END)
  - name: Opioid Low Pain Score
    expr: SUM(CASE WHEN event_type = 'administer' AND med_class = 'opioid' AND (pain_score_before IS NULL OR pain_score_before < 3) THEN 1 ELSE 0 END)
  - name: Off Shift Activity Count
    expr: SUM(CASE WHEN off_shift_flag THEN 1 ELSE 0 END)
  - name: Out Of Department Activity Count
    expr: SUM(CASE WHEN out_of_department_flag THEN 1 ELSE 0 END)
  - name: Composite Anomaly Score
    expr: SUM(CASE WHEN event_type = 'waste' AND witness_id IS NULL AND dea_schedule = 'CII' THEN 1 ELSE 0 END) + SUM(CASE WHEN event_type = 'administer' AND order_id IS NULL THEN 1 ELSE 0 END) + SUM(CASE WHEN event_type = 'administer' AND med_class = 'opioid' AND (pain_score_before IS NULL OR pain_score_before < 3) THEN 1 ELSE 0 END) + SUM(CASE WHEN off_shift_flag THEN 1 ELSE 0 END) + SUM(CASE WHEN out_of_department_flag THEN 1 ELSE 0 END)
  - name: Total Events
    expr: COUNT(1)
$$;
