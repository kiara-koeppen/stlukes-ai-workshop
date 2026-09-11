# AGENTS.md — St. Luke's x Databricks Workshop (context for AI assistants)

You are helping a Databricks facilitator prepare for or run the **St. Luke's Health System (SLHS) x
Databricks AI Dev Collaborative workshop**. Read this file, then help with whatever they ask:
rehearsing prompts, explaining an asset, drafting talking points, troubleshooting, etc. Everything
below is verified (built + tested), not aspirational.

## The workshop
- SLHS (Boise) x Databricks. Onsite **Sept 16-17 2026** (prep sync Sept 11). This is **art of the
  possible / MVP**, explicitly NOT a security or productionalization exercise (that is a follow-on).
- **4 use cases, each owned by a different facilitator/team:** CKD (chronic kidney disease
  identification), Medication Diversion, HTM (healthcare technology management / equipment planning),
  AI Huddle Management.
- **How it runs:** attendees start with ONLY synthetic data in their Unity Catalog and build the
  solution LIVE using **Genie Code** (an agentic natural-language assistant in the Databricks workspace
  top nav). Build order per use case: **Metric View -> AI Function -> Genie Agent -> AI/BI Dashboard ->
  Databricks App**. The loop is: prompt Genie Code -> review what it built -> correct/iterate (via Genie
  Code or by hand) -> verify -> next asset.
- **Assets in scope:** Metric Views, Genie Agents, AI Functions, AI/BI Dashboards, Databricks Apps, with
  Genie Code as the build tool.

## Where everything is (all docs are Google Docs, linked from the Master Index)
- **Master Index (START HERE):** https://docs.google.com/document/d/1E1gFzNvkswDZdYoC_MErBpN__x1SCEA01MehG_1UGk4/edit
  Links to both repos, all 8 guides, the data-load doc, and the reference assets.
- **Per use case:** a **User Guide** (tested Genie Code prompts in copy-paste code blocks, expected
  outputs, a problem->solution diagram, and productionalization + expansion notes) and an **Instructor
  Guide** (facilitator walkthrough + the full gotcha table). Links are in the Master Index.
- **Repos:**
  - Data loader (hand to attendee teams): https://github.com/kiara-koeppen/stlukes-workshop-data
    (loads the synthetic data + files ONLY; notebook + DAB).
  - Answer key / everything else: https://github.com/kiara-koeppen/stlukes-ai-workshop
    (solutions, the verified-prompts engineering record at `guides/genie-code-verified-prompts.md`,
    pre-built app source in `apps/`, data generators, DAB).

## Workspace + reference assets
- **FEVM workspace (facilitator reference):** https://adb-447340683886633.13.azuredatabricks.net
  (catalog `slhs_test1`). All 4 use cases were built here with Genie Code and verified.
- **Genie Agents:** CKD `01f1ae0626f41e31a517eb3aac920de1` · Diversion `01f1ae08af291854b6ef6533875dbc4c`
  · HTM `01f1ae0af6301d0bac8ece3fabbeeff6` · Huddle `01f1ae0d9a7a12cc8de27ca6e5c7ed86`.
- **AI/BI Dashboards:** CKD `01f1ae0678c51786af5d28272ca942ea` · Diversion `01f1ae08ebaa11129ce693930df2c58c`
  · HTM `01f1ae0b2f8a1d5783e004ed18a123b3` · Huddle `01f1ae0df4911a33975000df2239ed85`.
- The polished working **Databricks Apps live in a separate facilitator workspace (kk_test), not FEVM.**

## What each use case builds (verified numbers)
- **CKD:** surface undocumented / under-managed CKD. Metric view: 2000 patients / 1524 with CKD / 518
  care-gap / 230 high-risk. AI function scores 1018 clinical notes (99.2% precision). Genie agent + dashboard.
- **Medication Diversion:** spot possible drug diversion. Metric view over 45000 events (unwitnessed
  waste, off-shift, etc.); the 4 planted diverters (Allison Hill, Noah Rhodes, Angie Henderson, Daniel
  Wagner) top the ranking. AI risk narratives. Genie agent + dashboard. (HR/legal sensitive; findings
  prioritize review, never accuse.)
- **HTM:** capital equipment replacement planning. Metric view: 8000 assets / ~$2.0B replacement cost /
  1388 with support ending 2026. AI forecast ~465-493 corrective work orders/month. Genie agent + dashboard.
- **AI Huddle:** care-team huddle. Metric view: 18 patients / 20 non-optimal assignments. AI extracts
  barriers/social-needs/follow-ups from 18 transcript files. Genie agent + dashboard.

## Key findings / gotchas (the important ones; full list G1-G16 in the guides)
- **G11 (headline): Genie Code CAN fabricate.** For the Diversion AI function it invented fake employees
  and evidence on the first attempt. ALWAYS verify AI output against the source data; ground prompts in
  the real table/columns; never trust a "done" message.
- **G3:** ask for a "reusable metric view in Unity Catalog" with measures/dimensions. Phrasing it as "so
  I can see X broken down by Y" makes Genie Code build a dashboard instead.
- **Apps (G8-G10):** Genie Code scaffolds and deploys a Streamlit app, but it is NOT runnable without
  developer finishing (warehouse binding, service-principal grants, connector auth). For the workshop,
  ship a pre-built app or use the Genie One path.
- **Disabled previews:** Genie-on-Volumes (G16) and Predictive AI Functions / `ai_forecast` (G14) were
  OFF in the test workspace. Enable them under Settings > Previews.

## Required previews to enable before the onsite
Genie Code (for everyone), Predictive AI Functions (`ai_forecast`), Genie-on-Volumes (for document Q&A).

## Genie-on-Volumes mapping (attach once enabled, via each Genie space -> Configure > Sources > Add)
`med_diversion.policy_docs` -> Diversion agent · `htm.vendor_bulletins` -> HTM agent ·
`clinical.clinical_notes_files` -> CKD (optional) · `huddle.transcripts` -> Huddle (optional).

## How to help a coworker prepare
- **Rehearse:** walk them through their use case's User Guide prompts and the review/iterate loop; help
  them anticipate where Genie Code stumbles (see gotchas).
- **Explain:** any asset, the problem->solution flow, or a gotcha.
- **Draft:** a problem-statement intro, talking points, or Q&A for their group.
- **Troubleshoot:** lean on the gotcha table; always verify AI output against source rows.
- **Do NOT tell the customer that Agent Bricks / Knowledge Assistant / Supervisor Agent are
  "deprecated"** — they are GA (current status is in the guides' productionalization sections).
- **Productionalization questions:** the User Guides' "Productionalization and Expansion" sections cover
  the current path (Lakeflow Connect ingest, Unity Catalog ABAC governance, Unity AI Gateway, Lakebase,
  MLflow evaluation/monitoring, Databricks Asset Bundles) and expansion (Knowledge Assistant, Supervisor
  Agent, Databricks AI Search, custom Model Serving). Product names/status there were verified current as
  of late 2026; re-confirm before quoting to the customer.
