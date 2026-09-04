# Medication Diversion Support Reporting — Data Spec

**Prod target:** `healthcare_ai.med_diversion.medication_activity` (Yutong's starting point) + supporting tables we add
**Workshop build:** `kk_test.med_diversion.*`
**Grounded in:** the detailed `Diversion_Support_Reporting_AI_Project_Request.pdf` (no sample data exists yet, so we design from the documented workflow). **PHI + HR/legal sensitive: synthetic only.**

## The problem (what the AI must do)
The Diversion Support Team runs 1-6 investigations/month, each 3-5 manual days. The manual effort is **comparison**: one employee vs peer exemplars, across shifts, and over time. The solution must:
1. Benchmark a suspected employee's dispensing/administration against a **peer-exemplar cohort** (patients seen, doses dispensed, null/waste transactions).
2. Flag anomalies in **pain-score correlation, medication timing vs provider order, dosage accuracy, and administration patterns** using explicit rules.
3. Produce a **human-readable investigation narrative** (replaces the manual Excel pivot + color-coding).

## Tables
### `medication_activity` (event grain — the anchor table)
Omnicell (dispense/waste/return) + Epic (administration, orders, pain scores) unified:
- `transaction_id` STRING, `event_datetime` TIMESTAMP, `shift` STRING (Day/Eve/Night)
- `employee_id` STRING, `employee_name` STRING (synthetic), `employee_role` STRING (RN/Tech), `department` STRING, `unit` STRING
- `patient_id` STRING (nullable; null on waste/return -> "null transactions")
- `medication` STRING, `med_class` STRING (opioid/benzo), `dea_schedule` STRING (CII/CIII/CIV)
- `event_type` STRING (`dispense`,`administer`,`waste`,`return`)
- `dose_amount` DECIMAL(8,2), `dose_unit` STRING
- `order_id` STRING (nullable), `order_datetime` TIMESTAMP (nullable), `admin_datetime` TIMESTAMP (nullable)
- `pain_score_before` INT (0-10, nullable), `pain_score_after` INT (nullable)
- `witness_id` STRING (nullable; waste should have a witness)
- `off_shift_flag` BOOLEAN (activity outside the employee's scheduled shift)
- `out_of_department_flag` BOOLEAN

### `employee_risk` (IRIS scores from Bluesight ControlCheck)
- `employee_id`, `employee_name`, `role`, `department`, `peer_group_id`, `iris_score` DECIMAL(5,2), `scored_month` DATE

### `peer_group` (defines the exemplar cohorts)
- `peer_group_id`, `role`, `unit`, `description` (e.g. "Med-Surg RN, Night shift")

## Documented anomaly rules (encode as AI Functions / metric-view flags)
- **Waste without witness** on a CII med.
- **Administration without a matching provider order**, or admin **before** the order time.
- **Pain-score gap**: opioid administered with `pain_score_before` low/null (no documented justification).
- **Dose discrepancy**: dispensed dose > administered + wasted (missing amount).
- **Off-shift / out-of-department** dispensing.
- **Peer deviation**: employee's dispense/waste/null rate is N sigma above their peer-group mean.

## Planted signal
- ~40-60 employees across peer groups; **4-5 planted "diverters"** whose combined anomaly counts + IRIS scores make them the clear top of the ranking. Headline: "the 4 flagged employees are the top 4 by composite anomaly score," matching the peer-comparison story.
- Everyone else is a realistic control with occasional benign anomalies (so it is not trivially separable).

## Unstructured component
Synthetic **policy documents** (controlled-substance waste policy, diversion investigation SOP) as PDFs in a Volume, so a Genie Agent / KA can answer "what does policy require for CII waste?" alongside the data. Optional narrative output via `ai_query`.
