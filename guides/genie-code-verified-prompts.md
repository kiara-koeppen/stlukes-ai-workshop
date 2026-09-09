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
| G6 | **The exact numbers follow how you phrase the definition.** "Patients who *have* CKD" → `has_ckd=true` (518 care gap); "advanced-stage CKD" → stage 3a+ (500). Genie Code faithfully builds what you say. | Not a bug — a teaching point. If a specific clinical definition matters, phrase it; otherwise expect a defensible interpretation. Facilitators should know why a count differs from the slide. |

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
- **Prompt 3 (iterate, add measures):** *"add two more measures to that metric view - care gap patients
  (they have ckd but it's not documented in epic, so documented_ckd is No or None) and high risk
  patients (ckd stage 4 or 5 and not seeing nephrology)"*
  → **Result: ✅** added `care_gap_patients` and `high_risk_patients`. Genie Code first checked the actual
  `documented_ckd` / `sees_nephrology` values before writing DDL (good behavior).
- **Verified independently (SQL):** `care_gap_patients` = **518**, `high_risk_patients` = **230**.
- **✅ CKD metric view COMPLETE** — `patient_count` 2000 · `ckd_patient_count` 1524 · `care_gap_patients`
  518 · `high_risk_patients` 230; dims `actual_ckd_stage`, `sex`, `age_group`. Built entirely through 3
  short natural prompts (one of which was a wrong-turn course-correction).
- **Note (G6):** Care Gap came out **518**, not the answer key's 500, because "they *have* CKD" mapped to
  `has_ckd = true` rather than the stricter "advanced-stage (3a+)". Both are valid; 518 matches the
  original CKD narrative. Instructor point: the exact count follows the definition the attendee phrases.

### AI function (note extraction) — `slhs_test1.clinical.clinical_notes_ckd_extraction`
- **Prompt 1:** *"i have clinical notes in slhs_test1.clinical.clinical_notes. use an ai function to read
  each note and tell me whether it mentions chronic kidney disease and whether the patient is seeing
  nephrology. save the results to a table i can query."*
  → **Result: ✅** created `clinical_notes_ckd_extraction` — all **1,018** notes scored with `mentions_ckd`
  and `seeing_nephrology` (used `ai_query` under the hood). No spec needed; the short prompt worked first try.
- **Verified independently (SQL):** `mentions_ckd` = Yes 770 / No 245 / null 3. **Precision: of 770 notes
  flagging CKD, 764 are for patients with `has_ckd=true` in the registry → 99.2%.**
- **Payoff iterate:** *"now give me a table of the patients whose notes mention ckd but who aren't
  documented as ckd in the registry - documented_ckd is No or None. this is our undocumented ckd worklist"*
  → **Result: ✅ (as analysis).** Genie Code joined the extraction to the registry and returned the
  worklist **inline**: ~500 undocumented CKD patients (CKD 3a 204, 3b 203, CKD 4 93), and flagged the
  most urgent — **93 stage-4 undocumented, 28 not seeing nephrology.** This is the CKD use-case payoff.
- **Note (G7):** "give me a table of…" returns **inline query results, not a saved table.** Genie Code
  offered a "Save this worklist as a table" follow-up. To persist an artifact, say so explicitly.
- **✅ CKD AI function COMPLETE** — extraction table verified (99.2% precision) + undocumented-worklist
  analysis demonstrated. Persisting the worklist is a one-prompt follow-up if a saved table is wanted.

### Genie Agent — `01f1ac630be811fab2a17b766a235f5d` ("CKD Patient Registry")
- **Prompt:** *"create a genie space on the ckd data so clinicians can ask questions about kidney patients
  in plain english. use the ckd patient registry and the ckd_patient_registry_metrics metric view we built"*
  → **Result: ✅ Genie Code created a working Genie space** over the registry + metric view, and even
  proposed sample questions. **Big finding: Genie Code can build the Genie Agent itself**, not just SQL.
- **Verified live (Conversation API):** asked *"how many high risk patients are there?"* → answered
  **230**, generating `SELECT MEASURE(\`high_risk_patients\`) FROM …ckd_patient_registry_metrics`. Correct.
- **✅ CKD Genie Agent COMPLETE** — created + live-verified from one natural prompt.

### AI/BI dashboard — `01f1ac6418471f72859f9b559fac875f` ("CKD Patient Registry Dashboard")
- **Prompt:** *"build an ai/bi dashboard on the ckd_patient_registry_metrics metric view. show total ckd
  patients, care gap patients and high risk patients as big number tiles, plus care gap patients broken
  down by ckd stage and by assigned provider"*
  → **Result: ✅** 5 widgets. Genie Code used the **metric view as a native dataset** for tiles 1–4, and —
  since provider isn't a metric-view dimension — **wrote a supplemental SQL query on the registry** for the
  by-provider chart (nice automatic handling of the missing dimension).
- **Verified visually (browser):** tiles render **1.52K / 518 / 230** (Total CKD / Care Gap / High Risk);
  stage bar chart (3a ~204, 3b ~203); provider chart led by St. Luke's Meridian. Screenshot:
  `guides/assets/ckd-dashboard-genie-code.png`.
- **✅ CKD AI/BI dashboard COMPLETE.**

### Databricks App — _in progress_ (testing whether Genie Code can build a Databricks App)
### AI/BI dashboard — _pending_
### Databricks App — _pending_

## 02 · Medication Diversion — _pending_
## 03 · HTM — _pending_
## 04 · Huddle — _pending_
