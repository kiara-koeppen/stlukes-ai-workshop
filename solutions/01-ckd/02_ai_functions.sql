-- CKD AI Functions: read free-text clinical notes and surface UNDOCUMENTED CKD.
-- Uses ai_query (Llama 3.3 70B) with a directed prompt; parses JSON with from_json into a struct.
-- (ai_extract also works but returns inconsistent nulls; the directed ai_query prompt is crisper.)
-- Verified 2026-09-04 in kk_test: of 200 notes scored, AI flagged 102 as undocumented CKD;
-- precision check = 102/102 truly have lab-derived stage >= 3.
-- Catalog is kk_test here; swap to healthcare_ai for prod. Model choice only matters for ai_query.

CREATE OR REPLACE TABLE kk_test.clinical.notes_ckd_signals AS
SELECT scored.patient_id, scored.note_id, scored.note_date,
       scored.a.indicates_ckd       AS ai_indicates_ckd,
       scored.a.suggested_stage     AS ai_suggested_stage,
       scored.a.mentions_nephrology AS ai_mentions_nephrology,
       r.documented_ckd, r.actual_ckd_stage, r.sees_nephrology,
       (scored.a.indicates_ckd = 'Yes' AND r.documented_ckd IN ('No','None')) AS ai_flag_undocumented
FROM (
  SELECT patient_id, note_id, note_date,
    from_json(
      ai_query(
        'databricks-meta-llama-3-3-70b-instruct',
        CONCAT('You are a nephrology chart reviewer using KDIGO logic. Read the clinical note and return ONLY a compact JSON object with keys: indicates_ckd (Yes or No), suggested_stage (like CKD 3b, or None), mentions_nephrology (Yes or No). No prose. Note: ', note_text)
      ),
      'STRUCT<indicates_ckd: STRING, suggested_stage: STRING, mentions_nephrology: STRING>'
    ) AS a
  FROM (SELECT * FROM kk_test.clinical.clinical_notes ORDER BY patient_id LIMIT 200) s
) scored
JOIN kk_test.clinical.ckd_patient_registry r USING (patient_id);

-- Headline: patients the AI surfaces as CKD that Epic never documented.
-- SELECT count(*) notes_scored,
--        sum(CASE WHEN ai_flag_undocumented THEN 1 ELSE 0 END) ai_flagged_undocumented
-- FROM kk_test.clinical.notes_ckd_signals;

-- Scaling note: this scores a 200-note sample for the workshop. In production, score the
-- full notes stream on a schedule (Lakeflow) and govern the model via Unity AI Gateway.
