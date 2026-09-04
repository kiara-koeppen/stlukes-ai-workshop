# St. Luke's AI Dev Collaborative Workshop — Build Plan

**Onsite:** Sept 16-17 2026, Boise (Day 1 full, Day 2 half + leadership read-out to Molly, Rex, "J"). Prep sync with Yutong + Drake: Fri Sept 11 (9-11 MT).
**Databricks team:** Kiara (lead), Samihah (CKD build), Chad (AI Functions + Genie Code deep-dive), Michael (AE), Mobeen (SA). +Ryan Floyd (DNA) as a group driver, TBD.
**Format:** 3 mixed groups build POCs; Databricks brings a working answer-key for each so nothing stalls. This is an **MVP / art-of-the-possible**, explicitly NOT a security or productionalization review (those come 1-2 weeks later; Lakebase + Lakeflow Connect + Unity AI Gateway governance live in the "path to production" sections).

## Scope decisions (confirmed with Kiara 2026-09-04)
- **New clean repo** (`stlukes-ai-workshop`); old `stlukes-hackathon-*` repos left as archive.
- **Build all 4 use cases end-to-end** as a facilitator answer key (safety net), even the two with SLHS owners:
  - **CKD** = art-of-the-possible anchor, Samihah leads the live build; we build a full independent version too and coordinate.
  - **AI Huddle** = Drake's group, trending to production; full build with **Delta writeback + Lakebase as the documented prod path**.
- **Toolset (what we teach/build with):** Databricks Apps, Genie Agents, AI Functions, AI/BI Dashboards, Metric Views, Genie Code. Genie-on-Volumes (Beta) for unstructured. See `feature-status-fy27.md`.

## Data strategy
- Build + test in **kk_test**; schemas named **exactly** like prod (`clinical`, `med_diversion`, `htm`, `huddle`) so the only prod swap is the catalog token.
- Every generator + setup notebook **parameterizes catalog + schema via `dbutils.widgets`** (Kiara's rule); default catalog `kk_test`, participants set `healthcare_ai`.
- `healthcare_ai` catalog could not be created via API on this metastore (Default Storage needs the UI/managed location); the widget approach makes this a non-issue.
- Synthetic structured data with **planted signal** (see each schema spec) + synthetic **unstructured** docs (CKD notes, diversion policies, HTM manuals, huddle transcripts) in UC Volumes for Genie-on-Volumes + `ai_parse_document`/`ai_extract`.

## Asset matrix (what each use case demonstrates)
| Use case | Data | Metric Views | AI Functions | Genie Agent | AI/BI Dashboard | App | Genie-on-Volumes | Lakebase |
|---|---|---|---|---|---|---|---|---|
| **CKD** | registry + notes | stage/care-gap KPIs | `ai_extract` (notes), `ai_query` (stage suggestion) | yes (+ Genie One stretch) | care-gap + risk | clinician review UI | notes (Beta) | prod path only |
| **Diversion** | activity + IRIS + peer | peer-benchmark measures | `ai_query` (risk narrative), anomaly flags | yes | investigation dashboard | investigator UI | policy PDFs | - |
| **HTM** | assets + work_orders | assets/spend by EOL yr/facility | `ai_forecast`, `ai_query` (prioritization) | yes (NL queries) | replacement forecast | equipment-planner UI | vendor EOL bulletins | - |
| **Huddle** | demographics + extractions + inputs | complexity/assignment | `ai_extract` (transcripts) | yes | huddle summary | **huddle board (centerpiece)** | transcripts | **workshop=Delta, prod=Lakebase** |

## Build order (each step is tested before moving on — TDD/smoke)
For each use case: **1) synthetic data (verify counts + planted signal via SQL) -> 2) Metric Views (query them) -> 3) AI Functions (run on real rows) -> 4) Genie Agent (ask live via API, capture answers) -> 5) AI/BI dashboard -> 6) App -> 7) instructor + attendee guides.**

Sequence across use cases:
1. **CKD** (anchor + safety net; we have exact real columns + KDIGO rules).
2. **HTM** (cleanest, non-PHI, `ai_forecast` showcase).
3. **Diversion** (richest documented rules; metric-view peer benchmarking).
4. **Huddle** (most complex; app + Lakebase prod path).

## Deliverables (per use case)
1. **Synthetic data** (structured + unstructured), generators parameterized + reproducible on serverless.
2. **Databricks assets** built + tested in kk_test (metric views, AI functions, Genie Agent space_ids, dashboard, app).
3. **Instructor guide + cheatsheet** (`guides/instructor/`): TL;DR problem, the built solution, how to build it, and Genie Code prompts that land at the solution.
4. **Attendee guide** (`guides/attendee/`): TL;DR problem, which Databricks assets to use, Genie Code prompts, and "POC -> production" (governance, Lakebase, Lakeflow Connect, Epic write-back, MLflow eval, Unity AI Gateway).
5. Art-of-the-possible **demo script** (CKD) as a Google Doc in Claude Projects (per Kiara's doc rule).

## Verification standard (Kiara's rules)
- Test the **real end-to-end path**, not proxies: run the AI functions on real rows, create the metric views, ask the Genie Agent live and capture answers, launch the app.
- Report real output. If something is design-only (e.g. Genie Code prompts can't be driven headlessly), label it.
- Convert to DABs only once "done" (not during iterative build).

## Open items to close on the Sept 11 prep call
- Diversion: pharmacy team's PowerBI export / real field names (Bob Gregg). Until then, synthetic from the brief.
- Huddle: confirm transcript access reality (Teams -> OneDrive -> Lakeflow Connect is the prod story).
- Re-confirm Genie-on-Volumes Beta limits + Genie One branding before saying them to SLHS.
- Confirm the leadership read-out attendees ("J" = ?) and room/AV.
