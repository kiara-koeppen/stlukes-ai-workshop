#!/usr/bin/env python3
"""
St. Luke's Workshop Smoke Test - Quick Version
Uses direct HTTP calls to Databricks API
"""
import json
import os
import subprocess
import sys
from pathlib import Path

WAREHOUSE_ID = "c68a614580fefe22"
PROFILE = "kk_test"
REPO_ROOT = Path(__file__).parent

EXPECTED_COUNTS = {
    "clinical.ckd_patient_registry": 2000,
    "clinical.clinical_notes": 1018,
    "med_diversion.medication_activity": 45000,
    "med_diversion.employee_risk": 50,
    "med_diversion.peer_group": 10,
    "htm.medical_assets": 8000,
    "htm.work_orders": 52104,
    "huddle.patient_demographics": 18,
    "huddle.transcript_extractions": 18,
    "huddle.physician_inputs": 34,
}

LIVE_ASSETS = {
    "ckd": {
        "genie_space_id": "01f1a88b5c6613f9ad5a4383a3b81a6b",
        "dashboard_id": "01f1a88db2fc1a5f843fe617311b5cc2",
        "app_name": "ckd-clinician-review",
        "ai_output_table": "clinical.notes_ckd_signals",
    },
    "diversion": {
        "genie_space_id": "01f1a88ca9ab13638e9123eb9a0edf4b",
        "dashboard_id": "01f1a88db3721dc383ea706b9d78854a",
        "ai_output_table": "med_diversion.investigation_narratives",
    },
    "htm": {
        "genie_space_id": "01f1a88ca93e134ca8dec9628062762b",
        "dashboard_id": "01f1a88db3bd1c3aa3cd2fed66b243b2",
        "ai_output_table": "htm.work_order_forecast",
    },
    "huddle": {
        "genie_space_id": "01f1a88caa171f01b6a7ad343d28dfe3",
        "dashboard_id": "01f1a88db4291b848e5cdd4e4e0fc880",
        "app_name": "huddle-board",
        "ai_output_table": "huddle.transcript_ai_extractions",
    },
}

def run_sql(sql: str) -> dict:
    """Execute SQL via Databricks CLI."""
    payload = {"warehouse_id": WAREHOUSE_ID, "statement": sql, "wait_timeout": "50s"}
    cmd = ["databricks", "api", "post", "/api/2.0/sql/statements", "--profile", PROFILE, "--json", json.dumps(payload)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}
    except Exception as e:
        print(f"Error: {e}")
        return {}

def get_count(table: str, catalog: str = "kk_test") -> int:
    """Get row count for a table."""
    result = run_sql(f"SELECT COUNT(*) as cnt FROM `{catalog}`.{table}")
    if result.get("status", {}).get("state") == "SUCCEEDED":
        data = result.get("result", {}).get("data_array", [])
        if data:
            return int(data[0][0])
    return -1

def table_exists(table: str, catalog: str = "kk_test") -> bool:
    """Check if table exists."""
    result = run_sql(f"DESCRIBE TABLE `{catalog}`.{table}")
    return result.get("status", {}).get("state") == "SUCCEEDED"

def get_dashboard(dashboard_id: str) -> dict:
    """Get dashboard info."""
    cmd = ["databricks", "api", "get", f"/api/2.0/lakeview/dashboards/{dashboard_id}", "--profile", PROFILE]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}
    except:
        return {}

def get_app(app_name: str) -> dict:
    """Get app info."""
    cmd = ["databricks", "apps", "get", app_name, "--profile", PROFILE]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}
    except:
        return {}

def main():
    print("\n" + "="*70)
    print("ST. LUKE'S WORKSHOP SMOKE TEST")
    print("="*70)

    # PART A: Check if we can access kk_test data (proxy for loader capability)
    print("\n--- PART A: Can data be accessed in kk_test? (Proxy for Loader) ---")
    part_a_pass = True
    for table, expected_count in EXPECTED_COUNTS.items():
        count = get_count(table, "kk_test")
        if count == expected_count:
            print(f"✓ {table}: {count}")
        elif count > 0:
            print(f"✗ {table}: {count} (expected {expected_count})")
            part_a_pass = False
        else:
            print(f"✗ {table}: NOT FOUND")
            part_a_pass = False

    # PART B: Verify live assets
    print("\n" + "="*70)
    print("PART B: LIVE WORKSHOP ASSETS (kk_test)")
    print("="*70)

    summary = {}
    for use_case, assets in LIVE_ASSETS.items():
        print(f"\n--- {use_case.upper()} ---")
        uc_status = {"tables": 0, "metric_view": False, "ai_output": False, "dashboard": False, "app": False}

        # Base tables
        base_tables = {
            "ckd": ["clinical.ckd_patient_registry", "clinical.clinical_notes"],
            "diversion": ["med_diversion.medication_activity", "med_diversion.employee_risk", "med_diversion.peer_group"],
            "htm": ["htm.medical_assets", "htm.work_orders"],
            "huddle": ["huddle.patient_demographics", "huddle.transcript_extractions", "huddle.physician_inputs"],
        }
        for table in base_tables[use_case]:
            if get_count(table, "kk_test") > 0:
                uc_status["tables"] += 1

        # Metric view
        mv_map = {"ckd": "clinical.ckd_metrics", "diversion": "med_diversion.diversion_metrics", "htm": "htm.htm_metrics", "huddle": "huddle.huddle_metrics"}
        if get_count(mv_map[use_case], "kk_test") > 0:
            uc_status["metric_view"] = True

        # AI output table
        ai_table = assets["ai_output_table"]
        if get_count(ai_table, "kk_test") > 0:
            uc_status["ai_output"] = True

        # Dashboard
        dash = get_dashboard(assets["dashboard_id"])
        if dash.get("dashboard", {}).get("lifecycle") == "ACTIVE":
            uc_status["dashboard"] = True

        # App (if exists)
        if "app_name" in assets:
            app = get_app(assets["app_name"])
            if app.get("state") == "RUNNING":
                uc_status["app"] = True

        print(f"  Tables: {uc_status['tables']}/2-3")
        print(f"  Metric View: {'✓' if uc_status['metric_view'] else '✗'}")
        print(f"  AI Output Table: {'✓' if uc_status['ai_output'] else '✗'}")
        print(f"  Dashboard: {'✓' if uc_status['dashboard'] else '✗'}")
        if "app_name" in assets:
            print(f"  App ({assets['app_name']}): {'✓' if uc_status['app'] else '✗'}")

        summary[use_case] = uc_status

    # Final summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\nPart A (Loader test via kk_test access): {'✓ PASS' if part_a_pass else '✗ FAIL'}")
    print(f"\nPart B (Live workshop assets):")
    for use_case, status in summary.items():
        tables_ok = status["tables"] >= (3 if use_case == "ckd" else 2)
        all_ok = tables_ok and status["metric_view"] and status["ai_output"] and status["dashboard"]
        marker = "✓" if all_ok else "✗"
        print(f"  {marker} {use_case}: tables={status['tables']} mv={status['metric_view']} ai={status['ai_output']} dash={status['dashboard']}")

if __name__ == "__main__":
    main()
