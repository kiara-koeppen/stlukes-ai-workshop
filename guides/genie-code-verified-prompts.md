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
| G11 | **Genie Code can FABRICATE data.** Asked for a diversion AI function, it invented employees + evidence instead of using the real table, and saved to the `default` schema. | Ground the prompt in the exact table + columns; **verify every AI output against source rows**; never trust the "done" summary. The single most important workshop guardrail. |
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

### Databricks App — `ckd-undocumented-worklist` (deployed, but NOT working out of the box)
- **Prompt:** *"build a databricks app for the nephrology team - a simple worklist showing the undocumented
  ckd patients (their notes mention ckd but it's not documented in epic) so a coordinator can work through
  them. use the ckd data in slhs_test1.clinical"*
- **Result: ⚠️ PARTIAL — the key honest finding.** Genie Code **did** scaffold a Streamlit app (app.py +
  app.yaml + requirements), create the app, and **deploy it successfully** (compute ACTIVE, deploy
  SUCCEEDED, URL live). But the app **hangs on `load_worklist()` and never renders** — the generated
  output is not data-connected. Fixing it required several manual steps, and one defect blocks it entirely:
  1. **app.yaml bug:** `DATABRICKS_HTTP_PATH: valueFrom: resources` — there's no resource named "resources";
     it must be the resource's name, `sql-warehouse`. Log: *"error resolving resource resources … not found."*
  2. **No warehouse bound** to the app's `sql-warehouse` resource (had to `apps update` with the warehouse id).
  3. **App service principal had no grants** (had to `GRANT USE CATALOG/SCHEMA + SELECT`).
  4. **Even after 1–3, still hangs:** the generated `app.py` calls `dbsql.connect(server_hostname=…,
     http_path=…)` with **no authentication** (no `access_token` / `credentials_provider`), so the SQL
     connection never completes. This needs a real code edit to wire SP OAuth.
- **Workshop implication (important):** For metric view / AI function / Genie Agent / dashboard, Genie Code
  goes **data → working asset** from natural prompts. **The Databricks App is the exception** — Genie Code
  produces a *deployable scaffold* but finishing it (resource wiring + grants + connector auth) is a
  developer task. Recommend: for the workshop, **provide the app pre-built** (the repo's 4 answer-key
  Streamlit apps already work), or frame the app as a guided "Genie Code scaffolds it, we finish the wiring
  together" segment — not a clean one-prompt build.
- **Gotchas G8 (app.yaml valueFrom must name the resource), G9 (Genie Code doesn't bind warehouse/grant SP),
  G10 (generated dbsql.connect lacks auth).**
- **Fix recipe (what to do during the workshop if using Genie Code's app):**
  1. Edit `app.yaml`: `DATABRICKS_HTTP_PATH` → `valueFrom: sql-warehouse` (the resource name, not "resources").
  2. Bind a warehouse to the app's `sql-warehouse` resource (UI: app → Edit → Resources → pick a warehouse;
     or `databricks apps update <app> --json '{"resources":[{"name":"sql-warehouse","sql_warehouse":{"id":"<wh>","permission":"CAN_USE"}}]}'`).
  3. Grant the app's service principal: `GRANT USE CATALOG/USE SCHEMA/SELECT` on the catalog+schema.
  4. Edit `app.py` `dbsql.connect(...)` to add auth: `from databricks.sdk.core import Config`; `_cfg = Config()`;
     `credentials_provider=lambda: _cfg.authenticate`; add `databricks-sdk` to `requirements.txt`.
  5. Redeploy (`databricks apps deploy …`).
- **Outcome after all 4 fixes:** app deployed clean (no config errors in logs) but **still hung on the query with
  no error surfaced** in this workspace — an opaque connection hang. **RECOMMENDATION: for the workshop, ship the
  app PRE-BUILT** (the repo's 4 answer-key Streamlit apps are known-good) rather than relying on Genie Code to
  produce a working app. Genie Code's value for the App asset is *scaffolding the UI/logic*, not a runnable deploy.

## 02 · Medication Diversion

### Metric view — `slhs_test1.med_diversion.diversion_metrics`
- **Prompt (one shot):** *"build a reusable metric view in unity catalog on
  slhs_test1.med_diversion.medication_activity to help spot possible drug diversion. measures for total
  transactions, off-shift activity, and waste events; dimensions for employee, unit and shift"*
  → **Result: ✅ first try** (the G3 lesson applied — "reusable metric view in unity catalog" + "measures/
  dimensions" language got a metric view directly, no dashboard detour, and **friendly names** this time,
  e.g. "Total Transactions"). Genie Code went beyond the ask, adding strong signals: Unwitnessed Waste
  Events, Controlled Substance Txns, Out-of-Dept Events, No-Pain-Improvement Admins, Off-Shift %.
- **Verified (SQL):** Total Transactions 45,000 · Off-Shift 27,045 · Waste 7,472 · Unwitnessed Waste 326.
- **Signal check:** grouped by employee, ordered by Unwitnessed Waste → **the 4 planted diverters top the
  list** (EMP-00001/00003/00002/00004 = 88/87/83/68; next is 0). ✅
- **✅ Diversion metric view COMPLETE.**

### AI function — ⚠️ CRITICAL GOTCHA (G11): Genie Code FABRICATED the data on the first attempt
- **Prompt (attempt 1):** *"for the top 10 employees who look suspicious for drug diversion (high unwitnessed
  waste and off-shift controlled-substance activity), use an ai function to write a short risk-summary
  narrative explaining why each one is a concern. save it as a table i can review"*
  → **Result: ⚠️ HALLUCINATED.** Genie Code built an elaborate pipeline (`gold_diversion_flags`, composite
  risk scores, rule codes like `R10_AFTER_DISCHARGE`) and wrote AI narratives — but about **fabricated
  employees** ("James Carter / E5001", "Sarah Mitchell", "Emily Rodriguez") that **do not exist in the
  data**. The real planted diverters are EMP-00001 Allison Hill, EMP-00002 Noah Rhodes, EMP-00003 Angie
  Henderson, EMP-00004 Daniel Wagner. `SELECT count(*) … WHERE employee_name='James Carter'` = **0**.
  It also silently saved the table to the **`default`** schema, not `med_diversion` (secondary gotcha).
- **Why it matters (headline finding):** the output looked professional and would have passed a glance.
  For a HR/legal-sensitive use case, shipping hallucinated employees + invented evidence is dangerous.
  **The workshop MUST teach: pin the AI function to the real table/columns, and verify every AI output
  against the source data.** Do not trust Genie Code's "done" summary.
- **Prompt (attempt 2 — the fix):** *"using our slhs_test1.med_diversion.diversion_metrics view, take the
  top 10 employees by unwitnessed waste events - keep their real employee_id and employee_name from the
  data, do not invent any. for each, use an ai function to write a 2-3 sentence risk narrative citing their
  actual off-shift and unwitnessed-waste numbers. save it as a table in med_diversion"*
  → **Result: ✅ correct.** Created `med_diversion.employee_risk_narratives` (10 rows: employee_id,
  employee_name, unwitnessed_waste_events, off_shift_events, risk_narrative). Genie Code correctly read the
  metric view (MEASURE/GROUP BY ALL) and used **real** employees.
- **Verified (SQL):** top 4 are the **real planted diverters** — EMP-00001 Allison Hill, EMP-00003 Angie
  Henderson, EMP-00002 Noah Rhodes, EMP-00004 Daniel Wagner — narratives cite their actual numbers; the
  rest are real employees rated low-risk.
- **✅ Diversion AI function COMPLETE (attempt 2).** The lesson (G11): grounding in the real view + "do not
  invent" + naming the real id/name columns is what flips it from fabrication to correct.

### Genie Agent — `01f1ac6ddfb815d48bae4fa7fd6df6b0` ("Medication Diversion Investigation")
- **Prompt:** *"create a genie space for our diversion analysts to ask about suspicious medication activity
  in plain english. use slhs_test1.med_diversion.medication_activity, the diversion_metrics view, and the
  employee_risk_narratives table"*
  → **Result: ✅** created the space over the 3 objects.
- **Verified live (Conversation API):** *"which 5 employees have the most unwitnessed waste events?"* →
  returned **Allison Hill, Angie Henderson, Noah Rhodes, Daniel Wagner** (the real planted diverters), with
  correct SQL (`event_type='waste' AND witness_id IS NULL`). ✅ **Diversion Genie Agent COMPLETE.**

### AI/BI dashboard — `01f1ac6e25fb1675926f2696701b2b56` ("Diversion Metrics Dashboard")
- **Prompt:** *"build an ai/bi dashboard on the diversion_metrics view. tiles for total transactions, waste
  events, and unwitnessed waste events; a bar chart of the top 10 employees by unwitnessed waste events;
  and off-shift events by unit"* (then a follow-up to add the widgets — see gotcha below).
- **Result: ✅** 5 widgets on the real `diversion_metrics` metric view (+ a top-10 employees dataset).
- **Verified visually:** tiles **45K / 7.47K / 326** (total txns / waste / unwitnessed); top-10 chart shows
  the **real diverters** (Allison Hill, Angie Henderson, Daniel Wagner, Noah Rhodes); off-shift by unit.
  Screenshot: `guides/assets/diversion-dashboard-genie-code.png`. ✅ **Diversion dashboard COMPLETE.**
- **Gotcha G12 (my mistake, worth teaching):** the dashboard is *created empty first*, then a second agent
  builds the widgets. **Navigating to the dashboard while that's running interrupts it** (browser
  beforeunload) → empty shell (0 widgets). Wait for the widget build to finish before opening it.

### Databricks App — per the CKD finding (G8–G10), NOT re-run
- The App finding is **use-case-independent** — it's about Genie Code's app-generation capability, not the
  diversion data. Re-running the full scaffold→deploy→debug for each use case reproduces the same result
  (deployable scaffold, not runnable without developer finishing). **Recommendation stands: ship the
  Diversion app pre-built** (repo answer-key app `diversion-investigator` works). Fix recipe: see CKD.

## ✅ 02 · Medication Diversion COMPLETE — metric view, AI function (after grounding fix), Genie Agent,
dashboard all built via Genie Code + verified; app per the established finding.
### AI/BI dashboard — _pending_
### Databricks App — _pending_

## 02 · Medication Diversion — _pending_
## 03 · HTM (Equipment Planning)

### Metric view — `slhs_test1.htm.medical_assets_metrics`
- **Prompt (one shot):** *"build a reusable metric view in unity catalog on slhs_test1.htm.medical_assets
  for capital equipment replacement planning. measures for asset count, total replacement cost, average
  risk score, and assets whose support ends this year; dimensions for facility, manufacturer, device
  status, and support-end year"*
  → **Result: ✅ first try.** Genie Code **derived `support_end_year`** from `support_end_date` on its own.
  Measures: asset_count, total_replacement_cost, avg_risk_score, assets_support_ending_this_year.
- **Verified (SQL):** asset_count **8,000** · total replacement cost **$2.0B** · avg risk **65.6** ·
  support ending this year (2026) **1,388** (matches answer key). ✅ **HTM metric view COMPLETE.**

### AI function (ai_forecast) — _in progress_
### Genie Agent — _pending_
### AI/BI dashboard — _pending_
### Databricks App — _pending (per CKD finding: scaffold only; ship pre-built)_
## 04 · Huddle — _pending_
