# CKD Identification & Risk Flagging — Data Spec

**Prod target:** `healthcare_ai.clinical.ckd_patient_registry` + `healthcare_ai.clinical.clinical_notes`
**Workshop build:** `kk_test.clinical.*` (catalog is a widget; swap `kk_test` -> `healthcare_ai` for prod)
**Grounded in:** real de-identified sample `copy for yutong.xlsx` (Data tab, 5,330 rows x 23 cols) + the KDIGO staging rules on its "Additiona detail" tab. Yutong asked us to use those columns directly.

## The problem (what the AI must do)
CKD stages are often missing or wrong in Epic. Physicians manually review large panels. The solution must:
1. Identify patients whose **lab evidence indicates CKD** but whose **Epic documentation is missing or wrong** (the care gap).
2. Suggest the **likely KDIGO stage** from labs + trend.
3. Flag **high-risk** patients (advanced stage, not seeing nephrology) for clinician review.
4. Cut manual chart-review burden.

## Real source columns -> table columns
Source header (spreadsheet) -> `ckd_patient_registry` column:

| Source header | Column | Type | Notes |
|---|---|---|---|
| ID | `patient_id` | STRING | de-id token, e.g. `ACO-5AT5CX1MM82` |
| Number | `patient_num` | INT | |
| Sex | `sex` | STRING | M/F |
| DOB | `dob` | DATE | |
| Age | `age` | INT | |
| AssignedProviderName | `assigned_provider_name` | STRING | synthetic provider names; some `UNKNOWN` / clinic names (real data has both) |
| ChronicCondition | `chronic_conditions` | STRING | comma list |
| ChronicConditionCount | `chronic_condition_count` | INT | |
| CKD in Prob List or Past medical history? | `ckd_in_problem_list` | BOOLEAN | |
| Documented CKD | `documented_ckd` | STRING | what Epic says: `No`, `None`, `CKD 2`, `CKD 3a`, `CKD3 and CKD3b`, ... (deliberately messy) |
| Prior 3 outpt creat over 3 mo (a/b/c) | `creatinine_1/2/3` | DECIMAL(4,2) | 3 monthly outpatient creatinines |
| Prior 3 outpt GFR over 3 mo (a/b/c) | `gfr_1/2/3` | INT | `>90` stored as 90 (documented) |
| Recent microalb | `microalbumin_value` + `microalbumin_category` | DECIMAL(6,1) + STRING | real cells like `8.2 (A1)`, `276.4 (A2)`; split into value + A1/A2/A3 |
| Recent MicAlb date | `microalbumin_date` | DATE | |
| Has CKD? | `has_ckd` | BOOLEAN | ground truth |
| Actual CKD stage | `actual_ckd_stage` | STRING | ground truth: `None`, `CKD 1`..`CKD 5`, `3a`/`3b` |
| Sees nephro? | `sees_nephrology` | BOOLEAN | ground truth |
| Notes | `notes` | STRING | |
| Key meds | `key_meds` | STRING | SGLT-2 inhibitors / GLP-1 agonists (per rules tab) |

## KDIGO staging logic (from the rules tab, encode in the generator + as the AI's target)
- GFR bands: G1 >=90, G2 60-89, **G3a 45-59, G3b 30-44, G4 15-29, G5 <15**.
- Albuminuria: A1 <30, A2 30-300, A3 >300 mg/g.
- Use the **average** of the 3 outpatient creatinines/GFRs; exclude inpatient (hospitalization) values (they run high); require a sustained low GFR over the 3-month span.
- Nephrology: text search for "nephrolog" in notes; a current (2025/2026) mention = yes.
- Key meds: SGLT-2 inhibitors, GLP-1 agonists.

## Planted signal (so the demo lands)
Target ~2,000 patients:
- **~500 care-gap patients**: labs imply stage >= 3 but `documented_ckd` in (`No`,`None`) -> the headline "undocumented CKD" cohort.
- **~150 high-risk**: actual stage 4/5 AND `sees_nephrology = false` -> referral candidates.
- **~200 mis-staged**: documented stage disagrees with lab-derived stage (e.g. documented 3a, labs say 3b).
- Remainder correctly documented (control group).

## Unstructured component: `clinical_notes` + Volume
`clinical_notes` (`patient_id`, `note_id`, `note_date`, `author`, `note_type`, `note_text`) plus the same notes written as files to a Volume `kk_test.clinical.clinical_notes_files` for **Genie-on-Volumes (Beta)** and `ai_parse_document`/`ai_extract` demos. Notes embed: creatinine trend language, "referred to nephrology" (for the sees-nephro extraction), symptoms, and med mentions. A subset of care-gap patients has a note that *clearly* implies CKD the problem list missed, so `ai_extract` can surface it.
