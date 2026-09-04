-- Diversion AI Functions: ai_query generates a peer-benchmarked, objective investigation
-- narrative for each flagged employee (replaces the manual Excel pivot + color-coding).
-- Verified 2026-09-04 in kk_test: narratives generated for the top 5 by composite anomaly;
-- the 4 planted diverters lead. Wording is descriptive, not accusatory (compliance-sensitive).
-- Swap kk_test -> healthcare_ai for prod. Model choice matters only for ai_query.

CREATE OR REPLACE TABLE kk_test.med_diversion.investigation_narratives AS
WITH emp AS (
  SELECT employee_id, max(employee_name) employee_name, max(employee_role) role, max(department) department,
    count(*) total_events,
    sum(CASE WHEN event_type='waste' AND witness_id IS NULL AND dea_schedule='CII' THEN 1 ELSE 0 END) waste_no_witness,
    sum(CASE WHEN event_type='administer' AND (order_id IS NULL OR (admin_datetime IS NOT NULL AND order_datetime IS NOT NULL AND admin_datetime < order_datetime)) THEN 1 ELSE 0 END) admin_no_order,
    sum(CASE WHEN event_type='administer' AND med_class='opioid' AND (pain_score_before IS NULL OR pain_score_before <= 2) THEN 1 ELSE 0 END) low_pain_opioid,
    sum(CASE WHEN off_shift_flag THEN 1 ELSE 0 END) off_shift,
    sum(CASE WHEN out_of_department_flag THEN 1 ELSE 0 END) out_of_dept
  FROM kk_test.med_diversion.medication_activity GROUP BY employee_id
),
scored AS (
  SELECT e.*, r.iris_score,
    (waste_no_witness + admin_no_order + low_pain_opioid + off_shift + out_of_dept) composite,
    round(avg(waste_no_witness + admin_no_order + low_pain_opioid) OVER (), 1) peer_avg_anomalies
  FROM emp e LEFT JOIN kk_test.med_diversion.employee_risk r USING (employee_id)
),
top5 AS (SELECT * FROM scored ORDER BY composite DESC LIMIT 5)
SELECT employee_id, employee_name, role, department, iris_score, composite,
  waste_no_witness, admin_no_order, low_pain_opioid, off_shift, out_of_dept, peer_avg_anomalies,
  ai_query('databricks-meta-llama-3-3-70b-instruct',
    CONCAT('You are a controlled-substance diversion analyst. Write a 3-sentence investigation summary explaining why this employee is flagged, comparing to the peer average. Do not accuse; describe patterns objectively. Employee ', employee_name, ' (', role, ', ', department, '). IRIS risk score ', CAST(iris_score AS STRING),
    '. Anomalies: waste-without-witness=', CAST(waste_no_witness AS STRING), ', administrations-without-matching-order=', CAST(admin_no_order AS STRING),
    ', opioid-administrations-with-low-or-missing-pain-score=', CAST(low_pain_opioid AS STRING), ', off-shift activity=', CAST(off_shift AS STRING), ', out-of-department activity=', CAST(out_of_dept AS STRING),
    '. Peer group averages roughly ', CAST(peer_avg_anomalies AS STRING), ' such anomalies total.')) AS investigation_narrative
FROM top5;
