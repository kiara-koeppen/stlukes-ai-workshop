#!/usr/bin/env python3
"""
CKD Identification & Risk Flagging — synthetic data generator.

Produces two tables + a folder of clinical-note text files, grounded in the real
de-identified sample (copy for yutong.xlsx: 23 cols) and the KDIGO staging rules.

Outputs (under --out, default synthetic-data/data/ckd/):
  ckd_patient_registry.csv   -> kk_test.clinical.ckd_patient_registry
  clinical_notes.csv         -> kk_test.clinical.clinical_notes
  notes_files/*.txt          -> UC Volume for Genie-on-Volumes / ai_parse_document

Planted signal (defaults, ~2000 patients):
  ~500 care-gap  : lab-evidence CKD (stage >=3) but Epic documented_ckd in (No, None)
  ~150 high-risk : actual stage 4/5 AND not seeing nephrology
  ~200 mis-staged: documented stage disagrees with lab-derived stage
  remainder      : correctly documented (control)

Deterministic (seeded). Local generator; a setup notebook loads the CSVs into Delta.
"""
import argparse, csv, os, random, datetime as dt
from faker import Faker

STAGES = ["None", "CKD 2", "CKD 3a", "CKD 3b", "CKD 4", "CKD 5"]
# GFR band and creatinine band per true stage
GFR_BAND = {"None": (90, 118), "CKD 2": (60, 89), "CKD 3a": (45, 59),
            "CKD 3b": (30, 44), "CKD 4": (15, 29), "CKD 5": (5, 14)}
CREAT_BAND = {"None": (0.6, 1.0), "CKD 2": (0.9, 1.2), "CKD 3a": (1.1, 1.4),
              "CKD 3b": (1.3, 1.8), "CKD 4": (1.8, 3.5), "CKD 5": (3.5, 11.0)}
# adjacency for mis-staging
ADJ = {"CKD 2": ["None", "CKD 3a"], "CKD 3a": ["CKD 2", "CKD 3b"],
       "CKD 3b": ["CKD 3a", "CKD 4"], "CKD 4": ["CKD 3b", "CKD 5"], "CKD 5": ["CKD 4"]}
COMORBID = ["Diabetes Mellitus", "Hypertension", "Atrial Fibrillation",
            "Heart Failure", "COPD", "Hyperlipidemia", "Obesity", "Anemia"]
CLINIC_NAMES = ["UNKNOWN", "ST. LUKE'S CLINIC MAGIC VALLEY", "ST. LUKE'S CLINIC BOISE",
                "ST. LUKE'S CLINIC MERIDIAN", "ST. LUKE'S CLINIC NAMPA"]


def id_token(fake):
    return "ACO-" + "".join(random.choices("0123456789ABCDEFGHJKLMNPQRSTUVWXYZ", k=11))


def three_labs(band, lo_hi):
    # 3 sustained outpatient creatinines: pick a base in-band, add small noise (~10%),
    # floor at 0.3 so values are always physiologically plausible.
    lo, hi = lo_hi
    base = random.uniform(lo, hi)
    noise = max(0.08, base * 0.10)
    vals = [round(max(0.3, min(hi + 0.3, base + random.uniform(-noise, noise))), 2) for _ in range(3)]
    return vals


def three_gfr(band):
    lo, hi = band
    base = random.uniform(lo, hi)
    return [int(round(min(hi + 4, max(1, base + random.uniform(-4, 4))))) for _ in range(3)]


def microalbumin(true_stage):
    # higher stage -> more likely elevated albuminuria (A1<30, A2 30-300, A3>300)
    r = random.random()
    sev = {"None": 0.1, "CKD 2": 0.25, "CKD 3a": 0.45, "CKD 3b": 0.6, "CKD 4": 0.8, "CKD 5": 0.9}[true_stage]
    if r > sev:
        return None, None, None  # not recently measured
    p = random.random()
    if p < 1 - sev:
        val, cat = round(random.uniform(3, 29), 1), "A1"
    elif p < 1 - sev / 3:
        val, cat = round(random.uniform(30, 300), 1), "A2"
    else:
        val, cat = round(random.uniform(300, 900), 1), "A3"
    d = dt.date(2025, 1, 1) + dt.timedelta(days=random.randint(0, 500))
    return val, cat, d.isoformat()


def note_text(pid, true_stage, sees_nephro, gfrs, creats, care_gap):
    g = int(sum(gfrs) / 3); c = round(sum(creats) / 3, 2)
    lines = [f"Patient {pid} seen for routine follow-up."]
    if care_gap and true_stage in ("CKD 3a", "CKD 3b", "CKD 4", "CKD 5"):
        lines.append(f"Creatinine has trended up over the past year, averaging {c} mg/dL, "
                     f"with eGFR now in the {g}s range on repeated outpatient draws.")
        lines.append("This is consistent with chronic kidney disease that is not yet captured "
                     "on the problem list. Recommend adding CKD to the problem list and staging.")
        if not sees_nephro:
            lines.append("No nephrology involvement to date; consider referral if progression continues.")
    else:
        lines.append(f"Renal function stable, eGFR approximately {g}, creatinine {c} mg/dL.")
    if sees_nephro:
        lines.append("Patient is followed by nephrology for chronic kidney disease management.")
    return " ".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--care-gap", type=int, default=500)
    ap.add_argument("--high-risk", type=int, default=150)
    ap.add_argument("--mis-staged", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "data", "ckd"))
    ap.add_argument("--note-files", type=int, default=45, help="how many notes to also write as .txt for the Volume")
    args = ap.parse_args()

    random.seed(args.seed)
    fake = Faker(); Faker.seed(args.seed)
    out = os.path.abspath(args.out)
    notes_dir = os.path.join(out, "notes_files")
    os.makedirs(notes_dir, exist_ok=True)

    providers = [f"{fake.last_name().upper()}, {fake.first_name().upper()} {random.choice('ABCDEFGHJKLM')}"
                 for _ in range(45)]

    # assign cohort roles
    roles = (["care_gap"] * args.care_gap + ["high_risk"] * args.high_risk +
             ["mis_staged"] * args.mis_staged)
    roles += ["control"] * (args.n - len(roles))
    random.shuffle(roles)

    reg_rows, note_rows = [], []
    note_file_budget = args.note_files
    for i, role in enumerate(roles, start=1):
        # pick a true stage; care_gap/high_risk force CKD stages
        if role == "care_gap":
            true_stage = random.choices(["CKD 3a", "CKD 3b", "CKD 4"], [0.4, 0.4, 0.2])[0]
        elif role == "high_risk":
            true_stage = random.choices(["CKD 4", "CKD 5"], [0.6, 0.4])[0]
        elif role == "mis_staged":
            true_stage = random.choices(["CKD 2", "CKD 3a", "CKD 3b", "CKD 4"], [0.2, 0.35, 0.3, 0.15])[0]
        else:
            true_stage = random.choices(STAGES, [0.42, 0.13, 0.16, 0.13, 0.11, 0.05])[0]

        gfrs = three_gfr(GFR_BAND[true_stage])
        creats = three_labs(True, CREAT_BAND[true_stage])
        mval, mcat, mdate = microalbumin(true_stage)
        has_ckd = true_stage != "None"

        # nephrology
        if role == "high_risk":
            sees_nephro = False
        else:
            base_p = {"None": 0.02, "CKD 2": 0.05, "CKD 3a": 0.15, "CKD 3b": 0.35, "CKD 4": 0.7, "CKD 5": 0.85}[true_stage]
            sees_nephro = random.random() < base_p

        # documented CKD (Epic) vs actual (truth)
        if role == "care_gap":
            documented = random.choice(["No", "None"])
        elif role == "mis_staged" and true_stage in ADJ:
            documented = random.choice(ADJ[true_stage])
            if documented == "None":
                documented = "No"
        else:  # control / high_risk usually documented
            documented = "No" if true_stage == "None" else true_stage
        ckd_in_problem_list = documented not in ("No", "None")

        # comorbidities
        k = random.randint(1, 5)
        conds = random.sample(COMORBID, k)
        if ckd_in_problem_list:
            conds = ["Chronic Kidney Disease"] + conds
        chronic_conditions = ", ".join(conds)

        # key meds (SGLT2 / GLP-1) more likely if diabetic or CKD
        meds = []
        if "Diabetes Mellitus" in conds or has_ckd:
            if random.random() < 0.4: meds.append("Empagliflozin")   # SGLT-2
            if random.random() < 0.35: meds.append("Semaglutide")     # GLP-1
        key_meds = ", ".join(meds)

        sex = random.choice(["M", "F"])
        age = random.randint(45, 92)
        dob = dt.date(2026 - age, random.randint(1, 12), random.randint(1, 28))
        pid = id_token(fake)
        provider = random.choice(providers) if random.random() > 0.15 else random.choice(CLINIC_NAMES)

        short_note = ""
        if role == "care_gap":
            short_note = "Labs suggest CKD; not on problem list."
        elif role == "high_risk":
            short_note = "Advanced CKD, no nephrology follow-up."

        reg_rows.append([
            pid, i, sex, dob.isoformat(), age, provider, chronic_conditions, len(conds),
            ckd_in_problem_list, documented,
            creats[0], creats[1], creats[2], gfrs[0], gfrs[1], gfrs[2],
            mval if mval is not None else "", mcat or "", mdate or "",
            has_ckd, true_stage, sees_nephro, short_note, key_meds
        ])

        # clinical note for a subset (all care-gap + some others)
        if role == "care_gap" or random.random() < 0.35:
            nid = f"N{i:06d}"
            ndate = dt.date(2025, 6, 1) + dt.timedelta(days=random.randint(0, 400))
            txt = note_text(pid, true_stage, sees_nephro, gfrs, creats, role == "care_gap")
            note_rows.append([pid, nid, ndate.isoformat(), random.choice(providers), "Progress Note", txt])
            # write a subset as files for the Volume (favor care-gap so the demo lands)
            if note_file_budget > 0 and (role == "care_gap" or random.random() < 0.2):
                with open(os.path.join(notes_dir, f"{pid}_{nid}.txt"), "w") as f:
                    f.write(f"PATIENT: {pid}\nDATE: {ndate.isoformat()}\nNOTE TYPE: Progress Note\n\n{txt}\n")
                note_file_budget -= 1

    os.makedirs(out, exist_ok=True)
    reg_header = ["patient_id", "patient_num", "sex", "dob", "age", "assigned_provider_name",
                  "chronic_conditions", "chronic_condition_count", "ckd_in_problem_list", "documented_ckd",
                  "creatinine_1", "creatinine_2", "creatinine_3", "gfr_1", "gfr_2", "gfr_3",
                  "microalbumin_value", "microalbumin_category", "microalbumin_date",
                  "has_ckd", "actual_ckd_stage", "sees_nephrology", "notes", "key_meds"]
    with open(os.path.join(out, "ckd_patient_registry.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(reg_header); w.writerows(reg_rows)
    with open(os.path.join(out, "clinical_notes.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["patient_id", "note_id", "note_date", "author", "note_type", "note_text"])
        w.writerows(note_rows)

    # ---- local verification of planted signal ----
    def stg_num(s):
        return {"None": 0, "CKD 1": 1, "CKD 2": 2, "CKD 3a": 3, "CKD 3b": 3, "CKD 4": 4, "CKD 5": 5}.get(s, 0)
    care_gap = sum(1 for r in reg_rows if stg_num(r[20]) >= 3 and r[9] in ("No", "None"))
    high_risk = sum(1 for r in reg_rows if r[20] in ("CKD 4", "CKD 5") and r[21] is False)
    print(f"registry rows      : {len(reg_rows)}")
    print(f"clinical_notes rows: {len(note_rows)}  (note files written: {args.note_files - note_file_budget})")
    print(f"CARE-GAP (labs>=3, documented No/None): {care_gap}")
    print(f"HIGH-RISK (stage 4/5, no nephro)      : {high_risk}")
    print(f"output dir: {out}")


if __name__ == "__main__":
    main()
