-- AI Huddle Management metric view: the semantic layer for huddle summary and Genie Agent.
-- Catalog is a widget in the setup notebook; this file uses kk_test (swap to healthcare_ai for prod).
-- Verified 2026-09-15 in kk_test.huddle: 18 patients, one South Clinic morning huddle, 34 physician inputs from 3 providers.

CREATE OR REPLACE VIEW kk_test.huddle.huddle_metrics
WITH METRICS LANGUAGE YAML AS $$
version: 1.1
source: kk_test.huddle.physician_inputs
comment: "Huddle complexity, assignment, and psychosocial KPIs"
dimensions:
  - name: Huddle Date
    expr: huddle_date
  - name: Assigned Team Member
    expr: assigned_team_member
  - name: Optimal Team Member
    expr: optimal_team_member
  - name: Provider
    expr: provider_name
  - name: Complexity Band
    expr: CASE WHEN patient_complexity_score >= 5 THEN 'High' WHEN patient_complexity_score >= 0 THEN 'Moderate' ELSE 'Low' END
  - name: Relationship Band
    expr: CASE WHEN provider_patient_relationship_score >= 5 THEN 'Strong' WHEN provider_patient_relationship_score >= -2 THEN 'Neutral' ELSE 'Weak' END
  - name: Assignment Match
    expr: CASE WHEN optimal_team_member = assigned_team_member THEN 'Optimal' ELSE 'Suboptimal' END
measures:
  - name: Patient Count
    expr: COUNT(DISTINCT pat_id)
  - name: Avg Patient Complexity Score
    expr: AVG(patient_complexity_score)
  - name: Avg Relationship Score
    expr: AVG(provider_patient_relationship_score)
  - name: High Complexity Count
    expr: SUM(CASE WHEN patient_complexity_score >= 5 THEN 1 ELSE 0 END)
  - name: Strong Relationship Count
    expr: SUM(CASE WHEN provider_patient_relationship_score >= 5 THEN 1 ELSE 0 END)
  - name: Optimal Assignment Count
    expr: SUM(CASE WHEN optimal_team_member = assigned_team_member THEN 1 ELSE 0 END)
  - name: Provider Coverage
    expr: COUNT(DISTINCT provider_name)
$$;
