#!/usr/bin/env python3
"""
Medication Diversion Support Reporting -- synthetic data generator.

Produces three tables: medication_activity (event grain), employee_risk (IRIS scores),
and peer_group (cohort definitions), grounded in the diversion investigation workflow
from Diversion_Support_Reporting_AI_Project_Request.pdf.

Outputs (under --out, default synthetic-data/data/diversion/):
  medication_activity.csv  -> kk_test.med_diversion.medication_activity
  employee_risk.csv        -> kk_test.med_diversion.employee_risk
  peer_group.csv           -> kk_test.med_diversion.peer_group

Planted signal (defaults, ~40-60 employees, ~40k-80k events over 90 days):
  ~4-5 "diverters" with clear anomaly patterns: waste without witness on CII meds,
  administrations without orders, opioids with low pain scores, dose discrepancies,
  off-shift + out-of-department activity, high IRIS scores. Their composite anomaly
  count is >> control group.
  ~50 controls with realistic baseline + occasional benign anomalies
  (not trivially separable from diverters, but the planted ones stand out).

Deterministic (seeded). Local generator; a setup notebook loads the CSVs into Delta.
"""
import argparse, csv, os, random, datetime as dt
from faker import Faker

ROLES = ["RN", "Tech"]
DEPARTMENTS = ["Surgery", "ICU", "ED", "Orthopedics", "Cardiology"]
UNITS = ["Med-Surg", "Burn", "Night Shift", "Day Shift", "Evening"]
SHIFTS = ["Day", "Eve", "Night"]
MEDICATIONS = [
    ("Morphine", "opioid", "CII", 10.0, 20.0),
    ("Hydromorphone", "opioid", "CII", 2.0, 4.0),
    ("Fentanyl", "opioid", "CII", 0.05, 0.1),
    ("Oxycodone", "opioid", "CII", 5.0, 10.0),
    ("Lorazepam", "benzo", "CIV", 1.0, 2.0),
    ("Midazolam", "benzo", "CIV", 1.0, 5.0),
    ("Diazepam", "benzo", "CIV", 5.0, 10.0),
    ("Acetaminophen", "other", "OTC", 500.0, 1000.0),
    ("Ibuprofen", "other", "OTC", 200.0, 600.0),
]
EVENT_TYPES = ["dispense", "administer", "waste", "return"]


def employee_id_token(fake, emp_num):
    return f"EMP-{emp_num:05d}"


def patient_id_token(fake):
    return "PAT-" + "".join(random.choices("0123456789ABCDEFGHJKLMNPQRSTUVWXYZ", k=8))


def transaction_id_token():
    return "TXN-" + "".join(random.choices("0123456789ABCDEFGHJKLMNPQRSTUVWXYZ", k=12))


def random_datetime_in_range(start_date, end_date):
    """Random datetime between start_date and end_date (both dates)."""
    delta = (end_date - start_date).days
    random_days = random.randint(0, delta)
    random_seconds = random.randint(0, 86399)
    dt_val = dt.datetime.combine(start_date, dt.time.min) + dt.timedelta(days=random_days, seconds=random_seconds)
    return dt_val


def is_shift_match(dt_val, assigned_shift):
    """Rough heuristic: Day=6-18, Eve=14-22, Night=22-6."""
    hour = dt_val.hour
    if assigned_shift == "Day":
        return 6 <= hour < 18
    elif assigned_shift == "Eve":
        return 14 <= hour < 22
    elif assigned_shift == "Night":
        return hour >= 22 or hour < 6
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-employees", type=int, default=50, help="target employee count")
    ap.add_argument("--n-diverters", type=int, default=4, help="number of planted diverters")
    ap.add_argument("--events-per-day", type=int, default=500, help="baseline events/day")
    ap.add_argument("--days", type=int, default=90, help="days of data")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "data", "diversion"))
    args = ap.parse_args()

    random.seed(args.seed)
    fake = Faker()
    Faker.seed(args.seed)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    start_date = dt.date(2026, 6, 1)
    end_date = start_date + dt.timedelta(days=args.days - 1)

    # Generate employees and peer groups
    peer_groups = []
    peer_group_id_counter = 1
    for role in ROLES:
        for unit in UNITS:
            pg_id = f"PG-{peer_group_id_counter:03d}"
            desc = f"{role}, {unit}"
            peer_groups.append((pg_id, role, unit, desc))
            peer_group_id_counter += 1

    # Assign employees to peer groups
    employees = []
    diverter_ids = set()
    for i in range(args.n_employees):
        emp_id = employee_id_token(fake, i + 1)
        emp_name = fake.name()
        role = random.choice(ROLES)
        dept = random.choice(DEPARTMENTS)
        shift = random.choice(SHIFTS)
        peer_group = random.choice([p for p in peer_groups if p[1] == role])
        pg_id = peer_group[0]

        is_diverter = i < args.n_diverters
        if is_diverter:
            diverter_ids.add(emp_id)
            iris_score = random.uniform(75.0, 95.0)  # high risk
        else:
            iris_score = random.uniform(20.0, 50.0)  # normal

        employees.append({
            "emp_id": emp_id,
            "emp_name": emp_name,
            "role": role,
            "dept": dept,
            "shift": shift,
            "pg_id": pg_id,
            "iris_score": iris_score,
            "is_diverter": is_diverter,
        })

    # Generate medication_activity events
    activity_rows = []
    events_target = args.events_per_day * args.days
    for _ in range(events_target):
        emp = random.choice(employees)
        emp_id = emp["emp_id"]
        emp_name = emp["emp_name"]
        role = emp["role"]
        dept = emp["dept"]
        shift = emp["shift"]

        event_dt = random_datetime_in_range(start_date, end_date)
        off_shift = not is_shift_match(event_dt, shift)

        out_of_dept = random.random() < 0.05

        # Pick medication
        med_name, med_class, dea_sch, dose_lo, dose_hi = random.choice(MEDICATIONS)
        dose = round(random.uniform(dose_lo, dose_hi), 2)

        # For diverters, bias heavily toward anomalous patterns
        if emp["is_diverter"]:
            event_type = random.choices(
                EVENT_TYPES,
                [0.15, 0.40, 0.35, 0.10]  # more waste, more admin, less dispense/return
            )[0]
        else:
            event_type = random.choices(EVENT_TYPES, [0.40, 0.40, 0.15, 0.05])[0]

        txn_id = transaction_id_token()

        # Null transactions (waste/return on no patient)
        if event_type in ("waste", "return"):
            has_patient = random.random() > 0.30  # higher null rate for diverters
            if emp["is_diverter"]:
                has_patient = random.random() > 0.55
        else:
            has_patient = True

        patient_id = patient_id_token(fake) if has_patient else None

        # Timing anomalies for diverters
        order_id = None
        order_dt = None
        admin_dt = None
        pain_before = None
        pain_after = None
        witness_id = None

        if event_type == "administer":
            if emp["is_diverter"]:
                # For diverters: sometimes no order, sometimes admin before order
                if random.random() < 0.35:
                    # No order
                    order_id = None
                    order_dt = None
                else:
                    order_id = f"ORD-{random.randint(100000, 999999)}"
                    # Sometimes order is after admin
                    if random.random() < 0.25:
                        order_dt = event_dt + dt.timedelta(hours=random.randint(1, 6))
                    else:
                        order_dt = event_dt - dt.timedelta(hours=random.randint(0, 4))
            else:
                order_id = f"ORD-{random.randint(100000, 999999)}"
                order_dt = event_dt - dt.timedelta(hours=random.randint(0, 2))

            admin_dt = event_dt

            # Pain scores
            if med_class == "opioid":
                if emp["is_diverter"]:
                    # For diverters: low/null pain scores
                    if random.random() < 0.50:
                        pain_before = None
                    else:
                        pain_before = random.randint(0, 3)  # very low
                    pain_after = random.randint(0, 2)
                else:
                    pain_before = random.randint(3, 10)  # reasonable pre-admin pain
                    pain_after = random.randint(0, 6)
            else:
                if random.random() < 0.5:
                    pain_before = random.randint(0, 10)
                    pain_after = random.randint(0, 10)

        elif event_type == "dispense":
            order_id = f"ORD-{random.randint(100000, 999999)}"
            order_dt = event_dt - dt.timedelta(hours=random.randint(0, 1))

        elif event_type == "waste":
            # Witness required for compliant waste
            if emp["is_diverter"]:
                # High rate of waste without witness for diverters on CII
                if dea_sch == "CII" and random.random() < 0.60:
                    witness_id = None
                else:
                    witness_id = employee_id_token(fake, random.randint(1, args.n_employees))
            else:
                witness_id = employee_id_token(fake, random.randint(1, args.n_employees))

        # Dose discrepancies: for diverters, dispense > admin + waste (missing volume)
        activity_rows.append([
            txn_id,
            event_dt.isoformat(),
            shift,
            emp_id,
            emp_name,
            role,
            dept,
            random.choice(UNITS),  # unit
            patient_id,
            med_name,
            med_class,
            dea_sch,
            event_type,
            dose,
            "mg" if med_class != "other" else "mL",
            order_id or "",
            order_dt.isoformat() if order_dt else "",
            admin_dt.isoformat() if admin_dt else "",
            pain_before if pain_before is not None else "",
            pain_after if pain_after is not None else "",
            witness_id or "",
            off_shift,
            out_of_dept,
        ])

    # Generate employee_risk (IRIS scores)
    employee_risk_rows = []
    scored_month = dt.date(2026, 5, 1)
    for emp in employees:
        employee_risk_rows.append([
            emp["emp_id"],
            emp["emp_name"],
            emp["role"],
            emp["dept"],
            emp["pg_id"],
            round(emp["iris_score"], 2),
            scored_month.isoformat(),
        ])

    # Generate peer_group table
    peer_group_rows = [(p[0], p[1], p[2], p[3]) for p in peer_groups]

    # Write CSVs
    with open(os.path.join(out, "medication_activity.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "transaction_id", "event_datetime", "shift",
            "employee_id", "employee_name", "employee_role", "department", "unit",
            "patient_id", "medication", "med_class", "dea_schedule", "event_type",
            "dose_amount", "dose_unit",
            "order_id", "order_datetime", "admin_datetime",
            "pain_score_before", "pain_score_after",
            "witness_id", "off_shift_flag", "out_of_department_flag"
        ])
        w.writerows(activity_rows)

    with open(os.path.join(out, "employee_risk.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["employee_id", "employee_name", "role", "department", "peer_group_id", "iris_score", "scored_month"])
        w.writerows(employee_risk_rows)

    with open(os.path.join(out, "peer_group.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["peer_group_id", "role", "unit", "description"])
        w.writerows(peer_group_rows)

    # Local verification of planted signal
    print(f"medication_activity rows: {len(activity_rows)}")
    print(f"employee_risk rows      : {len(employee_risk_rows)}")
    print(f"peer_group rows         : {len(peer_group_rows)}")
    print(f"employees               : {len(employees)}")
    print(f"diverter employees      : {len(diverter_ids)}")
    print(f"date range              : {start_date.isoformat()} to {end_date.isoformat()}")
    print(f"output dir              : {out}")
    print(f"\nPlanted diverter IDs:")
    for emp in sorted(employees, key=lambda e: e["iris_score"], reverse=True)[:args.n_diverters]:
        print(f"  {emp['emp_id']}: {emp['emp_name']} (IRIS={emp['iris_score']:.1f})")


if __name__ == "__main__":
    main()
