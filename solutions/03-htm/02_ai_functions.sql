-- HTM AI Functions: ai_forecast on the corrective work-order time series.
-- Forecasts monthly corrective work-order volume so HTM can plan technician capacity.
-- NOTE: ai_forecast `horizon` is a TARGET DATE (not a step count). Anchor it to
-- max(request_date)+N months. Output columns are <value_col>_forecast/_lower/_upper.
-- Verified 2026-09-04 in kk_test (horizon 2027-06-01): ~480 corrective WOs/mo forecast, bounds ~428-542.
-- Swap kk_test -> healthcare_ai for prod.

CREATE OR REPLACE TABLE kk_test.htm.work_order_forecast AS
SELECT ds AS forecast_month,
       round(cnt_forecast)     AS forecast_corrective_wos,
       round(cnt_lower)        AS lower_bound,
       round(cnt_upper)        AS upper_bound
FROM ai_forecast(
  TABLE(
    SELECT date_trunc('MONTH', request_date) AS ds, CAST(count(*) AS DOUBLE) AS cnt
    FROM kk_test.htm.work_orders
    WHERE work_order_type = 'Corrective'
    GROUP BY 1
  ),
  horizon   => (SELECT date_format(add_months(date_trunc('MONTH', max(request_date)), 6), 'yyyy-MM-dd')
                FROM kk_test.htm.work_orders WHERE work_order_type='Corrective'),
  time_col  => 'ds',
  value_col => 'cnt'
);

-- Bonus prioritization narrative (ai_query) for the 2026 replacement cohort could be added similarly;
-- the deterministic EOL/risk ranking already lives in htm_metrics.
