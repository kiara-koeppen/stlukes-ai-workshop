-- HTM Data Load (SQL-based)
-- Load medical_assets and work_orders from CSV files in the landing volume

-- Load medical_assets
INSERT INTO kk_test.htm.medical_assets
SELECT
  asset_number,
  asset_description,
  manufacturer,
  model_number,
  serial_number,
  facility,
  department,
  CAST(purchase_date AS DATE),
  CAST(install_date AS DATE),
  CAST(support_end_date AS DATE),
  operating_system,
  ip_address,
  mac_address,
  device_status,
  CAST(replacement_cost AS DECIMAL(12,2)),
  CAST(risk_score AS DECIMAL(5,2))
FROM read_csv('/Volumes/kk_test/htm/landing/medical_assets.csv');

-- Load work_orders
INSERT INTO kk_test.htm.work_orders
SELECT
  work_order_id,
  asset_number,
  work_order_type,
  CAST(request_date AS DATE),
  CAST(completion_date AS DATE),
  technician_id,
  CAST(labor_hours AS DECIMAL(5,2)),
  status
FROM read_csv('/Volumes/kk_test/htm/landing/work_orders.csv');
