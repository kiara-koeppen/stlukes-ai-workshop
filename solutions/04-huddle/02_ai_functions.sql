-- Huddle AI Functions: ai_query extracts structured factors from raw Teams huddle
-- transcripts (unstructured -> structured), the exact "AI extraction" step in Drake's brief.
-- Reads transcript .txt files from a UC Volume via read_files(text), extracts a JSON object,
-- and parses it with from_json. Robust JSON grab via regexp_extract('[{][^}]*[}]', 0) since
-- the model occasionally wraps output in prose/fences (avoid backslash-heavy regex: it gets
-- double-escaped through the SQL/JSON layers).
-- Verified 2026-09-04 in kk_test: 18/18 transcripts parsed.
-- Swap kk_test -> healthcare_ai for prod.

CREATE OR REPLACE TABLE kk_test.huddle.transcript_ai_extractions AS
SELECT
  regexp_extract(file_path, '(PAT-[A-Z0-9]+)', 1) AS pat_id,
  file_path AS source_transcript_file,
  x.visit_complexity_projection, x.psychosocial_complexity_projection,
  x.social_determinants_of_health, x.relationship_context
FROM (
  SELECT _metadata.file_path AS file_path,
    from_json(
      regexp_extract(
        ai_query('databricks-meta-llama-3-3-70b-instruct',
          CONCAT('Extract structured fields from this morning-huddle transcript. Respond with ONLY a JSON object, no code fences, no prose, keys exactly: visit_complexity_projection (Low, Moderate, or High), psychosocial_complexity_projection (Low, Moderate, or High), social_determinants_of_health (short phrase), relationship_context (short phrase). Transcript: ', value)),
        '[{][^}]*[}]', 0),
      'STRUCT<visit_complexity_projection: STRING, psychosocial_complexity_projection: STRING, social_determinants_of_health: STRING, relationship_context: STRING>') AS x
  FROM read_files('/Volumes/kk_test/huddle/transcripts/', format=>'text', wholeText=>true)
) s;
