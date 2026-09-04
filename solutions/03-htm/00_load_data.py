# Databricks notebook source
# MAGIC %md
# MAGIC # HTM Data Load
# MAGIC Load medical_assets and work_orders CSVs from the landing volume into Delta tables

# COMMAND

from pyspark.sql.types import *

# COMMAND

# Read medical_assets
assets_schema = StructType([
    StructField("asset_number", StringType()),
    StructField("asset_description", StringType()),
    StructField("manufacturer", StringType()),
    StructField("model_number", StringType()),
    StructField("serial_number", StringType()),
    StructField("facility", StringType()),
    StructField("department", StringType()),
    StructField("purchase_date", DateType()),
    StructField("install_date", DateType()),
    StructField("support_end_date", DateType()),
    StructField("operating_system", StringType()),
    StructField("ip_address", StringType()),
    StructField("mac_address", StringType()),
    StructField("device_status", StringType()),
    StructField("replacement_cost", DecimalType(12, 2)),
    StructField("risk_score", DecimalType(5, 2))
])

assets_df = spark.read.option("header", "true").schema(assets_schema).csv("/Volumes/kk_test/htm/landing/medical_assets.csv")
assets_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("kk_test.htm.medical_assets")

# COMMAND

# Read work_orders
wo_schema = StructType([
    StructField("work_order_id", StringType()),
    StructField("asset_number", StringType()),
    StructField("work_order_type", StringType()),
    StructField("request_date", DateType()),
    StructField("completion_date", DateType()),
    StructField("technician_id", StringType()),
    StructField("labor_hours", DecimalType(5, 2)),
    StructField("status", StringType())
])

wo_df = spark.read.option("header", "true").schema(wo_schema).csv("/Volumes/kk_test/htm/landing/work_orders.csv")
wo_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("kk_test.htm.work_orders")

# COMMAND

# Verify
print(f"Assets loaded: {spark.table('kk_test.htm.medical_assets').count()}")
print(f"Work Orders loaded: {spark.table('kk_test.htm.work_orders').count()}")
