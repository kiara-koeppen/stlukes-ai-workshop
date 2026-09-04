-- Databricks notebook source
-- MAGIC %md
-- MAGIC # HTM Data Load (SQL Notebook)
-- MAGIC Load medical_assets and work_orders from CSV files using SQL

-- COMMAND

-- Load medical_assets from CSV
INSERT INTO kk_test.htm.medical_assets
SELECT
  _1 as asset_number,
  _2 as asset_description,
  _3 as manufacturer,
  _4 as model_number,
  _5 as serial_number,
  _6 as facility,
  _7 as department,
  CAST(_8 AS DATE) as purchase_date,
  CAST(_9 AS DATE) as install_date,
  CAST(_10 AS DATE) as support_end_date,
  _11 as operating_system,
  _12 as ip_address,
  _13 as mac_address,
  _14 as device_status,
  CAST(_15 AS DECIMAL(12,2)) as replacement_cost,
  CAST(_16 AS DECIMAL(5,2)) as risk_score
FROM csv.`/Volumes/kk_test/htm/landing/medical_assets.csv`
WHERE _1 IS NOT NULL AND _1 <> 'asset_number';

-- COMMAND

-- Load work_orders from CSV
INSERT INTO kk_test.htm.work_orders
SELECT
  _1 as work_order_id,
  _2 as asset_number,
  _3 as work_order_type,
  CAST(_4 AS DATE) as request_date,
  CAST(_5 AS DATE) as completion_date,
  _6 as technician_id,
  CAST(_7 AS DECIMAL(5,2)) as labor_hours,
  _8 as status
FROM csv.`/Volumes/kk_test/htm/landing/work_orders.csv`
WHERE _1 IS NOT NULL AND _1 <> 'work_order_id';

-- COMMAND

SELECT COUNT(*) as assets_loaded FROM kk_test.htm.medical_assets;

-- COMMAND

SELECT COUNT(*) as work_orders_loaded FROM kk_test.htm.work_orders;
