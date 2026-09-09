# Genie Code — Verified Prompts & Gotchas

Working record of testing the **Genie Code** UI path end-to-end: starting from **only the
synthetic data** (no metric views, no AI-function tables, no agents/dashboards/apps), can a
workshop attendee build each asset with natural-language prompts?

Tested live in `adb-447340683886633` against the `slhs_test1` catalog (data-only starting
state). Every result is **independently verified by querying the object via SQL** — not by
trusting Genie Code's own "done" message.

**Prompt style:** written the way a real clinician/analyst would type — intent, not a spec.
If a natural prompt underperforms, the gotcha + the minimal prompt that *does* work are recorded.

**What Genie Code is:** an agentic, multi-step assistant in the workspace top nav ("Run multi-step
data and AI tasks"). It reads the table schema, searches Databricks docs, writes + runs SQL,
and self-corrects. `@` references objects, `/` runs commands, model selector defaults to "Auto".

---

## Global gotchas (apply to all use cases)

| # | Gotcha | Workaround |
|---|--------|------------|
| G1 | Genie Code input is a rich-text (Lexical) editor — pasting/scripting text programmatically doesn't register and Submit stays disabled. | (Automation only.) Real keystrokes are needed. Not a concern for humans typing in the room. |
| G2 | Metric-view measures **must** be queried with the `MEASURE()` wrapper; a plain `SELECT measure` fails. | Genie Code hit this itself and self-corrected. When *you* query a metric view, use `SELECT MEASURE(\`Name\`) ...`. Worth calling out to attendees. |
| G3 | **A metric-view ask phrased as "so I can *see* X *broken down by* Y" makes Genie Code build a DASHBOARD** (with an inline/local metric view), not a governed Unity Catalog metric view object. | Say **"reusable metric view in Unity Catalog"** and describe **measures** and **dimensions**. Avoid viz words ("see", "broken down by", "chart"). A one-line course-correction ("not a dashboard — I want a reusable metric view in Unity Catalog") fixes it in the same chat. |
| G4 | Genie Code **names measures/dimensions by raw column** (`patient_count`, `actual_ckd_stage`) even when it shows friendly labels ("Total Patients", "CKD Stage") in chat. | If you want friendly, governed names, ask explicitly ("name the measures Patient Count, Patients With CKD…"). Otherwise query with the raw names. |
| G5 | Metric views do **not** appear in `information_schema.views`. | They show in `information_schema.tables` with `table_type = 'METRIC_VIEW'`. (Verification note.) |

---

## 01 · CKD

### Metric view — `slhs_test1.clinical.ckd_patient_registry_metrics`
Built the way an attendee actually would: a short opener, then reviewing and correcting. This is
the intended asset-by-asset, review-and-iterate loop (not a one-shot spec prompt).

- **Prompt 1 (opener):** *"build me a metric view on the ckd patient registry so i can see how many
  patients have ckd, broken down by stage, sex and age"*
  → **Result: WRONG asset.** Genie Code built a **dashboard** with an inline metric view (see G3). Good
  teachable moment — shows attendees the difference between "I want to see" (dashboard) and "I want a
  reusable metric view" (semantic object).
- **Prompt 2 (course-correct):** *"not a dashboard - i want a reusable metric view in unity catalog.
  create one on the ckd registry with measures for total patients and how many actually have ckd, and
  let me break it down by ckd stage, sex and age"*
  → **Result: ✅ correct.** Created `slhs_test1.clinical.ckd_patient_registry_metrics` (`table_type =
  METRIC_VIEW`). Genie Code opened a notebook, wrote + ran the DDL, and self-verified.
- **Verified independently (SQL):** `MEASURE(patient_count)` = **2000**, `MEASURE(ckd_patient_count)`
  = **1524** (matches answer key). Dimensions: `actual_ckd_stage`, `age_group`, `sex`. Note raw column
  naming (G4).
- **Next iterate step (to reach the full answer key):** review shows it's a *starter* — missing the
  Care Gap and High Risk measures. Planned follow-up prompt: *"add two more measures — care gap (they
  have CKD but it's not documented in Epic — documented_ckd is No or None) and high risk (stage 4 or 5
  and not seeing nephrology)."* Then re-verify expecting 500 / 230.

### AI function (note extraction) — _pending_
### Genie Agent — _pending_
### AI/BI dashboard — _pending_
### Databricks App — _pending_

## 02 · Medication Diversion — _pending_
## 03 · HTM — _pending_
## 04 · Huddle — _pending_
