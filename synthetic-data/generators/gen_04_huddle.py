#!/usr/bin/env python3
"""
AI Huddle Management — synthetic data generator.

Produces three tables + a folder of huddle transcript files, grounded in a realistic
South Clinic morning triage huddle (Nampa location, Sept 15 2026).

Outputs (under --out, default synthetic-data/data/huddle/):
  patient_demographics.csv   -> kk_test.huddle.patient_demographics
  transcript_extractions.csv -> kk_test.huddle.transcript_extractions
  physician_inputs.csv       -> kk_test.huddle.physician_inputs
  transcripts/*.txt          -> UC Volume for Genie-on-Volumes / ai_extract

Planted signal:
  ~15-20 patients in one morning huddle
  ~3-5 providers scoring them
  A few high-complexity / high-psychosocial patients
  A couple with strong existing provider relationships (visible in relationship_score)
  "Optimal vs assigned" mismatch story (some assigned suboptimally, documented in non_optimal_assignment_notes)

Deterministic (seeded). Local generator; a setup notebook loads the CSVs into Delta.
"""
import argparse, csv, os, random, datetime as dt
from faker import Faker

HUDDLE_DATE = "2026-09-15"  # Single morning huddle
CLINIC_NAME = "South Clinic / Nampa"

# Realistic visit reasons for a morning triage huddle
VISIT_REASONS = [
    "Chronic disease management",
    "Hypertension follow-up",
    "Diabetes management",
    "Chest pain evaluation",
    "Abdominal pain",
    "Medication adjustment",
    "New patient intake",
    "Behavioral health concern",
    "Complex social situation",
    "Post-hospitalization follow-up"
]

# Business-named extraction factors (11 total)
COMPLEXITY_LEVELS = ["Low", "Moderate", "High", "Very High"]

def id_token(fake):
    return "PAT-" + "".join(random.choices("0123456789ABCDEFGHJKLMNPQRSTUVWXYZ", k=8))

def provider_id(fake):
    return "PRV-" + "".join(random.choices("0123456789ABCDEFGHJKLMNPQRSTUVWXYZ", k=6))

def generate_extraction_factors(complexity_band):
    """Generate realistic clinical/psychosocial factor descriptions."""

    factors = {}

    if complexity_band == "High" or complexity_band == "Very High":
        # High complexity patients
        factors["visit_complexity_projection"] = random.choice([
            "Multiple comorbidities requiring coordination",
            "Complex medication interactions",
            "Multidisciplinary care needed"
        ])
        factors["provider_identified_issues"] = random.choice([
            "Medication non-compliance, unclear medication list",
            "Frequent ER visits, no clear pathway to care",
            "Advanced chronic disease requiring specialist input"
        ])
        factors["medical_drivers"] = random.choice([
            "Uncontrolled diabetes with complications",
            "Heart failure with recurrent decompensation",
            "CKD Stage 3b with proteinuria"
        ])
        factors["patient_identified_issues"] = random.choice([
            "Difficulty affording medications",
            "Job changes affecting health insurance",
            "Cannot take time off work for appointments"
        ])
        factors["history_of_job_modifications"] = random.choice([
            "Multiple job changes in past 12 months",
            "Currently unemployed, seeking work",
            "Shift work, variable schedule"
        ])
        factors["psychosocial_complexity_projection"] = random.choice([
            "Untreated depression/anxiety, recent loss",
            "Substance use history, recovery supported",
            "Severe stress, family caregiver burden"
        ])
        factors["social_determinants_of_health"] = random.choice([
            "Food insecurity, relies on food bank",
            "Housing instability, recent move",
            "Transportation barrier to clinic"
        ])
        factors["hidden_contextual_factors"] = random.choice([
            "Recent trauma/loss not disclosed initially",
            "Distrust of medical system, ICE concerns",
            "Undisclosed domestic situation"
        ])
        factors["negotiability"] = random.choice([
            "Low: patient rigid on treatment preferences",
            "Moderate: some flexibility but strong beliefs about care",
            "Willing to discuss alternatives"
        ])
        factors["relationship_context"] = random.choice([
            "First time seeing provider, needs trust-building",
            "Longstanding relationship but recent breakdown",
            "Complex history with multiple providers"
        ])
        factors["relationship_equity_with_care_team"] = random.choice([
            "Language barrier, interpreter needed",
            "Cultural factors affecting communication",
            "Past negative experience with healthcare system"
        ])
    else:
        # Moderate/Low complexity patients
        factors["visit_complexity_projection"] = random.choice([
            "Routine follow-up",
            "Single chronic condition management",
            "Preventive care visit"
        ])
        factors["provider_identified_issues"] = random.choice([
            "Good adherence, stable on current regimen",
            "Minor medication adjustment needed",
            "Preventive screening due"
        ])
        factors["medical_drivers"] = random.choice([
            "Well-controlled hypertension",
            "Stable diabetes on current regimen",
            "Annual physical examination"
        ])
        factors["patient_identified_issues"] = random.choice([
            "Interested in lifestyle modifications",
            "No current concerns",
            "Routine check-in"
        ])
        factors["history_of_job_modifications"] = random.choice([
            "Stable employment",
            "No recent job changes",
            "Retired"
        ])
        factors["psychosocial_complexity_projection"] = random.choice([
            "Stable mental health, no acute concerns",
            "Social support system intact",
            "Actively engaged in wellness"
        ])
        factors["social_determinants_of_health"] = random.choice([
            "Stable housing, good support network",
            "Access to transportation",
            "Adequate food security"
        ])
        factors["hidden_contextual_factors"] = random.choice([
            "None identified",
            "Routine social history",
            "Engaged with community resources"
        ])
        factors["negotiability"] = random.choice([
            "High: collaborative, flexible with options",
            "Very high: proactive in own care",
            "Engaged in shared decision-making"
        ])
        factors["relationship_context"] = random.choice([
            "Established relationship, good rapport",
            "Long-standing patient with provider",
            "Trusting relationship"
        ])
        factors["relationship_equity_with_care_team"] = random.choice([
            "Strong communication, no barriers",
            "Engaged, understands care plan",
            "Culturally concordant care"
        ])

    return factors

def generate_transcript(pat_id, pat_name, huddle_date, complexity_band, provider_name):
    """Generate a realistic Teams-style huddle excerpt mentioning this patient."""
    lines = [
        f"--- Huddle Discussion: {huddle_date} ---",
        f"[Provider transcript snippet]",
        f"",
        f"Patient: {pat_name} (ID: {pat_id})",
        f"Provider: {provider_name}",
        ""
    ]

    if complexity_band == "Very High":
        lines.extend([
            "\"This patient coming in today has multiple things going on. Seen them before,",
            "significant medication non-compliance, frequent ER utilization. Recent job loss,",
            "currently unemployed. Has some untreated mental health concerns we need to address.",
            "I'm concerned about the psychosocial component - family situation is unstable.",
            "Will need a care coordination touch base to get them set up with resources.\"",
        ])
    elif complexity_band == "High":
        lines.extend([
            "\"Moderate complexity here. Uncontrolled diabetes, also has CKD - lab work",
            "trending in the wrong direction. Family caregiver for parents, working part-time.",
            "Some social determinants at play - housing stable but transportation is challenging.",
            "Patient is motivated but needs some help with medication management and scheduling.\"",
        ])
    else:
        lines.extend([
            "\"Routine follow-up visit. Stable on current medications, doing well with",
            "lifestyle changes we discussed last visit. Annual physical due. Patient is engaged,",
            "no acute concerns. Should be straightforward visit today.\"",
        ])

    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=18, help="number of patients in huddle")
    ap.add_argument("--providers", type=int, default=3, help="number of providers")
    ap.add_argument("--high-complexity", type=int, default=4, help="count of high/very-high complexity")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "data", "huddle"))
    args = ap.parse_args()

    random.seed(args.seed)
    fake = Faker(); Faker.seed(args.seed)
    out = os.path.abspath(args.out)
    transcripts_dir = os.path.join(out, "transcripts")
    os.makedirs(transcripts_dir, exist_ok=True)

    # Generate providers
    providers = [
        {"id": provider_id(fake), "name": f"{fake.last_name().upper()}, {fake.first_name().upper()} {random.choice('MDDO')}"}
        for _ in range(args.providers)
    ]

    # Assign complexity bands
    complexity_bands = (["High"] * (args.high_complexity // 2) +
                        ["Very High"] * (args.high_complexity - args.high_complexity // 2))
    complexity_bands += ["Moderate"] * (args.n - len(complexity_bands) // 2)
    complexity_bands += ["Low"] * (args.n - len(complexity_bands))
    complexity_bands = complexity_bands[:args.n]
    random.shuffle(complexity_bands)

    demo_rows = []
    extract_rows = []
    phys_rows = []
    optimal_assignment_signal = {}  # Track who should see whom based on relationship

    for i in range(args.n):
        pat_id = id_token(fake)
        sex = random.choice(["M", "F"])
        age = random.randint(35, 85)
        dob = dt.date(2026 - age, random.randint(1, 12), random.randint(1, 28))
        pat_name = fake.name()
        complexity_band = complexity_bands[i]

        # patient demographics
        demo_rows.append([
            pat_id,
            pat_name,
            dob.isoformat(),
            fake.phone_number()[:20],  # home_phone
            age,
            sex,
            CLINIC_NAME,
            HUDDLE_DATE,
            random.choice(VISIT_REASONS)
        ])

        # transcript extraction (1 row per patient per huddle_date)
        factors = generate_extraction_factors(complexity_band)
        transcript_filename = f"{pat_id}_{HUDDLE_DATE}.txt"

        extract_rows.append([
            pat_id,
            HUDDLE_DATE,
            transcript_filename,
            factors["visit_complexity_projection"],
            factors["provider_identified_issues"],
            factors["medical_drivers"],
            factors["patient_identified_issues"],
            factors["history_of_job_modifications"],
            factors["psychosocial_complexity_projection"],
            factors["social_determinants_of_health"],
            factors["hidden_contextual_factors"],
            factors["negotiability"],
            factors["relationship_context"],
            factors["relationship_equity_with_care_team"]
        ])

        # write transcript file
        primary_provider = random.choice(providers)
        transcript_text = generate_transcript(pat_id, pat_name, HUDDLE_DATE, complexity_band, primary_provider["name"])
        with open(os.path.join(transcripts_dir, transcript_filename), "w") as f:
            f.write(transcript_text)

        # Store signal for optimal assignment (high-complexity -> less available provider, low -> more available)
        if complexity_band in ("High", "Very High"):
            optimal_assignment_signal[pat_id] = random.choice(providers)
        else:
            optimal_assignment_signal[pat_id] = random.choice(providers)

    # Physician inputs: some patients scored by 1, some by 2-3 providers
    for i, pat_id in enumerate([r[0] for r in demo_rows]):
        complexity_band = complexity_bands[i]

        # Determine how many providers will score this patient
        num_scorers = random.choices([1, 2, 3], [0.4, 0.45, 0.15])[0]
        scorers = random.sample(providers, min(num_scorers, len(providers)))

        optimal_provider = optimal_assignment_signal[pat_id]

        for provider in scorers:
            # Complexity and relationship scores
            if complexity_band == "Very High":
                complexity_score = random.randint(5, 10)
                relationship_score = random.randint(-8, 5)  # Mixed, some new to team
            elif complexity_band == "High":
                complexity_score = random.randint(2, 8)
                relationship_score = random.randint(-5, 5)
            else:
                complexity_score = random.randint(-5, 3)
                relationship_score = random.randint(-2, 8)  # More often good relationships

            # Planted mismatch: sometimes optimal != assigned
            assigned_provider = provider
            if random.random() < 0.2:  # 20% of assignments suboptimal
                assigned_provider = random.choice([p for p in providers if p["id"] != provider["id"]])
                non_optimal_notes = "Provider availability constraint; patient comfortable with assignment"
            else:
                non_optimal_notes = ""

            phys_rows.append([
                pat_id,
                HUDDLE_DATE,
                provider["id"],
                provider["name"],
                relationship_score,
                complexity_score,
                random.choice([
                    "Good engagement, stable on medications",
                    "Needs care coordination support",
                    "Recommend specialist consult",
                    ""
                ]),
                optimal_provider["name"],
                assigned_provider["name"],
                non_optimal_notes,
                dt.datetime(2026, 9, 15, random.randint(7, 10), random.randint(0, 59)).isoformat()
            ])

    # Write CSVs
    os.makedirs(out, exist_ok=True)

    demo_header = ["pat_id", "pat_name", "birth_date", "home_phone", "age", "sex", "clinic", "huddle_date", "scheduled_visit_reason"]
    with open(os.path.join(out, "patient_demographics.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(demo_header); w.writerows(demo_rows)

    extract_header = [
        "pat_id", "huddle_date", "source_transcript_file",
        "visit_complexity_projection", "provider_identified_issues", "medical_drivers",
        "patient_identified_issues", "history_of_job_modifications", "psychosocial_complexity_projection",
        "social_determinants_of_health", "hidden_contextual_factors", "negotiability",
        "relationship_context", "relationship_equity_with_care_team"
    ]
    with open(os.path.join(out, "transcript_extractions.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(extract_header); w.writerows(extract_rows)

    phys_header = [
        "pat_id", "huddle_date", "provider_id", "provider_name",
        "provider_patient_relationship_score", "patient_complexity_score",
        "physician_notes", "optimal_team_member", "assigned_team_member",
        "non_optimal_assignment_notes", "created_at"
    ]
    with open(os.path.join(out, "physician_inputs.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(phys_header); w.writerows(phys_rows)

    # Verification
    print(f"patient_demographics rows    : {len(demo_rows)}")
    print(f"transcript_extractions rows  : {len(extract_rows)}")
    print(f"physician_inputs rows        : {len(phys_rows)}")
    print(f"transcript files written     : {len(os.listdir(transcripts_dir))}")
    print(f"output dir                   : {out}")
    print(f"")
    print(f"Complexity distribution:")
    for band in ["Very High", "High", "Moderate", "Low"]:
        count = complexity_bands.count(band)
        if count > 0:
            print(f"  {band}: {count}")


if __name__ == "__main__":
    main()
