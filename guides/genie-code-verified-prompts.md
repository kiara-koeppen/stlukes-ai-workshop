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

---

## 01 · CKD

### Metric view — `slhs_test1.clinical.ckd_metrics`
- **Status:** ✅ built by Genie Code, independently verified.
- **Verified result:** Patient Count 2000 · Patients With CKD 1524 · Care Gap 500 · High Risk 230 (exact match to the hand-built answer key).
- **Notes:** First pass used a detailed/spec-style prompt (works reliably). Re-testing with a
  natural-language prompt (below) to confirm intent-only phrasing lands the same result — that is
  the workshop-realistic test.
- **Natural prompt (verifying):** "Make a metric view over the CKD patient registry. I want to see
  how many patients actually have CKD, how many are a care gap — they have CKD but it's not
  documented in Epic — and how many are high-risk, meaning advanced stage and not seeing a
  nephrologist. Let me slice it by CKD stage, sex, and age."

### AI function (note extraction) — _pending_
### Genie Agent — _pending_
### AI/BI dashboard — _pending_
### Databricks App — _pending_

## 02 · Medication Diversion — _pending_
## 03 · HTM — _pending_
## 04 · Huddle — _pending_
