# St. Luke's AI Dev Collaborative Workshop

Facilitator answer key + shareable starter for the St. Luke's Health System (SLHS, Boise) x Databricks
AI Dev Collaborative Workshop, **Sept 16-17 2026**. This repo holds the synthetic data, built Databricks
solutions, and instructor/attendee guides for four healthcare AI use cases, so the Databricks team walks
in with a working solution for every group and can guide participants who get stuck.

> **Synthetic data only. No PHI.** The `source-materials/` folder (real de-identified SLHS briefs and sample
> data) is git-ignored and never committed.

## The four use cases
| # | Use case | What it does | Sensitivity | SLHS owner |
|---|---|---|---|---|
| 1 | **CKD Identification & Risk Flagging** | Find patients with lab-evidence CKD that Epic under-documents; suggest KDIGO stage; flag high-risk for review | PHI-adjacent | Samihah (art-of-the-possible anchor) |
| 2 | **Medication Diversion Support Reporting** | Benchmark a suspected employee vs peer exemplars; flag anomalies; auto-generate the investigation narrative | PHI + HR/legal | Yutong's group |
| 3 | **NextGen HTM Equipment Planning** | NL queries + forecasting over the TMS asset inventory for capital replacement planning | Non-PHI | Group 3 |
| 4 | **AI Huddle Management** | Combine Epic Clarity demographics + Teams huddle transcripts + physician input to support morning patient-to-provider assignment | PHI | Drake's group (trending to prod) |

*(AI Huddle replaced Nursing Position Control, which SLHS deferred to 2027.)*

## Databricks assets used
Databricks Apps, Genie Agents, AI Functions (`ai_query`, `ai_extract`, `ai_forecast`, ...), AI/BI Dashboards,
Unity Catalog Metric Views, Genie Code, Genie-on-Volumes (Beta), and Lakebase (AI Huddle production path).
Current status of each is in [`reference/feature-status-fy27.md`](reference/feature-status-fy27.md).

## Architecture (per use case)
```
Unstructured files (notes/transcripts/manuals)  ─┐
   in UC Volumes ──ai_parse_document/ai_extract──┤
                                                 ├─► Delta tables ─► Metric Views ─┬─► Genie Agent ─► App (Genie Conversation API)
Structured synthetic data (planted signal) ──────┘   (semantic layer)              └─► AI/BI Dashboard
                                                                                    App writeback ─► Delta (prod: Lakebase)
```

## Repo layout
```
reference/           Feature status, master build plan, platform patterns
synthetic-data/
  schemas/           Data spec per use case (grounded in the real SLHS samples)
  generators/        Parameterized generators (Spark+Faker) that create the synthetic data
solutions/           Facilitator answer-key build per use case (01-ckd ... 04-huddle)
guides/
  instructor/        Cheatsheets: problem TL;DR, built solution, how to build, Genie Code prompts
  attendee/          Problem TL;DR, assets to use, Genie Code prompts, POC->production
apps/                Databricks Apps
source-materials/    (git-ignored) real SLHS briefs + de-identified samples
```

## Prerequisites
- Databricks workspace with Unity Catalog, Serverless SQL, Genie, Model Serving / AI Functions enabled.
- Databricks CLI authenticated. Workshop build/test target: profile `kk_test`, warehouse `Serverless Starter Warehouse`.
- A UC catalog for the data. Build uses `kk_test`; participants set catalog `healthcare_ai` via widget.

## How to build / run
1. **Data:** run the generator for a use case (see `synthetic-data/generators/`), setting the `catalog`/`schema` widgets.
   Each generator creates the tables + writes unstructured files to a Volume, then prints verification counts.
2. **Assets:** follow the matching `solutions/0X-*/` build (metric views -> AI functions -> Genie Agent -> dashboard -> app).
3. **Guides:** `guides/` holds the instructor cheatsheet and attendee guide for each use case.

## Status
Foundation in place (schemas + build plan + feature verification). Asset build in progress; see
[`reference/build-plan.md`](reference/build-plan.md) for the current build order and verification standard.
