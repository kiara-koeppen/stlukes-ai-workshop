# Databricks Feature Status (verified 2026-09-04)

Status of every feature this workshop leans on. Verified against internal sources + docs on 2026-09-04.
Product names shift quarterly, so re-confirm the two flagged items before the onsite.

| Feature | Status | Notes for the workshop |
|---|---|---|
| **AI Functions** (`ai_query`, `ai_parse_document`, `ai_extract`, `ai_classify`, `ai_summarize`, `ai_gen`, `ai_forecast`, `ai_mask`, `ai_analyze_sentiment`) | **GA** | All GA in SQL. Only `ai_query` lets you pick the model; the rest use managed endpoints. `ai_forecast` does time-series forecasting directly in SQL (used for HTM replacement forecasting). |
| **Unity Catalog Metric Views** | **GA** | Consumed by Genie Agents, AI/BI dashboards, SQL, notebooks, alerts. Requires DBR 17.2+. The shared semantic layer under both Genie and dashboards. |
| **Genie Agents** (fka Genie Spaces) | **GA** | The natural-language-to-SQL surface. Point at metric views + tables. |
| **Genie Agent on Volumes** ("Analyze files in Volumes") | **BETA** ⚠️ | Attach up to ~10 UC Volumes of unstructured files (PDF, Word, images, slides); Genie answers questions over them using `ai_parse_document` under the hood. This is how CKD clinical notes, HTM manuals, and huddle transcripts get into Genie. **Beta**, so frame it as art-of-the-possible, not a production SLA. RE-CONFIRM config + limits at build time. |
| **Genie One** | **GA** (re-confirm branding) | Simplified business-user surface / unified entry point. Relevant to the CKD "expand to Genie One" stretch. Branding claim needs a quick re-confirm before we say it to SLHS. |
| **Databricks Apps** | **GA** | The clean UI wrapper for each solution. Talks to a SQL warehouse and, via the **Genie Conversation API (GA)**, to a Genie Agent. |
| **Genie Conversation API** | **GA** | Lets an App / Slack / Teams query a Genie Agent programmatically. Backbone of the app-to-agent integration. |
| **Lakebase** (managed Postgres) | **GA** | Two forms: **Autoscaling** (scale-to-zero, GA 2026-01-22) and **Provisioned** (GA). Apps connect via OAuth managed credentials. This is the huddle physician-writeback store + the "path to production" story. |
| **Unity AI Gateway** (fka Mosaic AI Gateway) | **GA** (guardrails = Public Preview) | Rate limits, budgets, usage tracking all GA; guardrails (PII, safety) in Public Preview. The governance layer for the PHI-sensitive use cases (CKD, Diversion). Part of the production-path narrative, not the build. |

## Two things to re-confirm before the onsite
1. **Genie Agent on Volumes** exact config, supported file types, and the ~10-volume / size limits (it is Beta).
2. **Genie One** current branding / positioning, so we describe it correctly to SLHS.

## Names to get right in front of the customer (do NOT say "deprecated")
- Genie Agents (formerly Genie Spaces).
- Unity AI Gateway (formerly Mosaic AI Gateway).
- Never tell SLHS that Agent Bricks / Knowledge Assistant / Multi-Agent Supervisor is "deprecated." Those interactive pieces are folding into the Genie family internally, with no customer-communicable EOL. Build on the Genie family + AI Functions instead.
